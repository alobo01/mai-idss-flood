"""
Linear programming optimizer for fair (max–min) resource allocation with
necessity-aware dispatch.

Key changes vs. the original version:
- Necessity caps: allocations are bounded above by the zone's ideal (fuzzy-derived)
  bundle demand, so the solver does NOT "fill" all capacity by default.
- Optional relevance gating: scores below a threshold are treated as irrelevant
  (demand = 0), forcing x_ij = 0.
- Tie-breaking: add a tiny epsilon penalty on total allocation so that, among
  equally fair solutions, the solver prefers using fewer resources.

References:
- Chen & Hooker (2023): A Guide to Fairness in Optimization
- Kaplan (1974): On a Two-Stage Linear Programming Model with Fixed-Charge Variables
- Luss (1999): On Equitable Resource Allocation Problems: A Lexicographic Minimax Approach
"""

from typing import Dict, List, Tuple, Optional
import logging

import numpy as np
from scipy.optimize import linprog

logger = logging.getLogger(__name__)


def compute_ideal_bundles(
    zones: List[Dict],
    resource_scores: Dict[str, Dict[str, float]],
    nominal_allocations: Dict[str, float],
    *,
    score_threshold: float = 0.0,
) -> Dict[str, Dict[str, float]]:
    """
    Compute ideal (demand) resource bundle for each zone based on priority scores.

    For zone j with nominal allocation R_j, the ideal amount of resource i is:
        a_ij = R_j * (s_ij / sum_h(s_hj)), for resources with s_ij > threshold

    Args:
        zones: List of zone dicts with "zone_id"
        resource_scores: zone_id -> {resource_id: score in [0,1]}
        nominal_allocations: zone_id -> total nominal units R_j
        score_threshold: scores <= threshold are treated as irrelevant (a_ij = 0)

    Returns:
        zone_id -> {resource_id: ideal_amount a_ij}
    """
    ideal_bundles: Dict[str, Dict[str, float]] = {}

    for zone in zones:
        zone_id = zone["zone_id"]
        scores = resource_scores.get(zone_id, {})
        R_j = float(nominal_allocations.get(zone_id, 0.0))

        # Filter relevant scores (strictly > threshold)
        relevant_scores = {k: float(v) for k, v in scores.items() if float(v) > score_threshold}

        if not relevant_scores or R_j <= 0.0:
            ideal_bundles[zone_id] = {}
            continue

        total_score = float(sum(relevant_scores.values()))
        if total_score <= 0.0:
            ideal_bundles[zone_id] = {}
            continue

        # Normalize scores to sum to R_j
        ideal_bundles[zone_id] = {
            resource_id: R_j * (score / total_score)
            for resource_id, score in relevant_scores.items()
        }

    return ideal_bundles


def optimize_fair_allocation(
    zones: List[Dict],
    resource_scores: Dict[str, Dict[str, float]],
    nominal_allocations: Dict[str, float],
    capacities: Dict[str, int],
    resource_types: List[str],
    *,
    score_threshold: float = 0.05,
    epsilon_alloc_penalty: float = 1e-6,
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, float], float]:
    """
    Solve max–min fairness LP for resource allocation with necessity-aware constraints.

    Decision variables:
    - x_ij: amount of resource i allocated to zone j
    - z_j: satisfaction level of zone j (fraction of ideal bundle)
    - t: minimum satisfaction level (fairness level)

    Objective (single-stage tie-broken):
        max  t - eps * sum_{i,j} x_ij
    Implemented as:
        min  -t + eps * sum_{i,j} x_ij

    Constraints:
    1. Fairness coupling: t <= z_j  for all j
    2. Bundle satisfaction: x_ij >= a_ij * z_j  for all (i,j) with a_ij > 0
    3. Necessity caps: 0 <= x_ij <= a_ij, and if a_ij == 0 then x_ij = 0
    4. Capacity: sum_j x_ij <= B_i  for all i
    5. Bounds: 0 <= z_j <= 1, x_ij >= 0, t free

    Args:
        zones: list of zone dictionaries with "zone_id"
        resource_scores: zone_id -> {resource_id: score}
        nominal_allocations: zone_id -> R_j (zone-level total demand from upstream)
        capacities: resource_id -> B_i
        resource_types: list of resource IDs (defines order)
        score_threshold: scores <= threshold are treated as irrelevant (a_ij = 0)
        epsilon_alloc_penalty: tiny tie-breaker weight; set 0 to disable

    Returns:
        (allocations, satisfaction_levels, fairness_level)
        allocations: zone_id -> {resource_id: amount}
        satisfaction_levels: zone_id -> z_j
        fairness_level: t
    """
    # Compute ideal (demand) bundles a_ij
    ideal_bundles = compute_ideal_bundles(
        zones,
        resource_scores,
        nominal_allocations,
        score_threshold=score_threshold,
    )

    zone_ids = [z["zone_id"] for z in zones]
    n_resources = len(resource_types)
    n_zones = len(zone_ids)

    # Variable indexing:
    # x_ij: [0 .. n_resources*n_zones - 1]
    # z_j:  [n_x .. n_x + n_zones - 1]
    # t:    [n_x + n_zones]
    n_x_vars = n_resources * n_zones
    n_z_vars = n_zones
    n_vars = n_x_vars + n_z_vars + 1

    def x_idx(i: int, j: int) -> int:
        return i * n_zones + j

    def z_idx(j: int) -> int:
        return n_x_vars + j

    def t_idx() -> int:
        return n_x_vars + n_z_vars

    # Objective: minimize -t + eps * sum x_ij
    c = np.zeros(n_vars)
    c[t_idx()] = -1.0
    if epsilon_alloc_penalty and epsilon_alloc_penalty > 0.0:
        c[:n_x_vars] = float(epsilon_alloc_penalty)

    # Inequality constraints A_ub @ vars <= b_ub
    A_ub: List[np.ndarray] = []
    b_ub: List[float] = []

    # (1) Fairness coupling: t - z_j <= 0
    for j in range(n_zones):
        row = np.zeros(n_vars)
        row[t_idx()] = 1.0
        row[z_idx(j)] = -1.0
        A_ub.append(row)
        b_ub.append(0.0)

    # (2) Bundle satisfaction: -x_ij + a_ij * z_j <= 0  (only when a_ij > 0)
    for j, zone_id in enumerate(zone_ids):
        ideal = ideal_bundles.get(zone_id, {})
        for i, resource_id in enumerate(resource_types):
            a_ij = float(ideal.get(resource_id, 0.0))
            if a_ij > 0.0:
                row = np.zeros(n_vars)
                row[x_idx(i, j)] = -1.0
                row[z_idx(j)] = a_ij
                A_ub.append(row)
                b_ub.append(0.0)

    # (3) Capacity: sum_j x_ij <= B_i
    for i, resource_id in enumerate(resource_types):
        row = np.zeros(n_vars)
        for j in range(n_zones):
            row[x_idx(i, j)] = 1.0
        A_ub.append(row)
        b_ub.append(float(capacities.get(resource_id, 0)))

    A_ub_arr = np.array(A_ub)
    b_ub_arr = np.array(b_ub)

    # Bounds with necessity caps:
    # If a_ij == 0 -> x_ij = 0 (hard block)
    # else x_ij in [0, a_ij] (cannot exceed "needed" amount)
    bounds: List[Tuple[Optional[float], Optional[float]]] = []
    for i, resource_id in enumerate(resource_types):
        for j, zone_id in enumerate(zone_ids):
            a_ij = float(ideal_bundles.get(zone_id, {}).get(resource_id, 0.0))
            if a_ij <= 1e-12:
                bounds.append((0.0, 0.0))
            else:
                bounds.append((0.0, a_ij))

    # z_j bounds
    for _ in range(n_zones):
        bounds.append((0.0, 1.0))

    # t is free (unbounded); practically it will be <= 1
    bounds.append((None, None))

    # Solve LP
    try:
        result = linprog(
            c,
            A_ub=A_ub_arr,
            b_ub=b_ub_arr,
            bounds=bounds,
            method="highs",
            options={"disp": False},
        )

        if not result.success:
            logger.warning(f"LP optimization failed: {result.message}")
            return _fallback_allocation(
                zones,
                resource_scores,
                nominal_allocations,
                capacities,
                resource_types,
                score_threshold=score_threshold,
            )

        sol = result.x
        fairness_level = float(sol[t_idx()])

        allocations: Dict[str, Dict[str, float]] = {}
        satisfaction_levels: Dict[str, float] = {}

        for j, zone_id in enumerate(zone_ids):
            allocations[zone_id] = {}
            for i, resource_id in enumerate(resource_types):
                amount = float(sol[x_idx(i, j)])
                if amount > 1e-6:
                    allocations[zone_id][resource_id] = round(amount, 2)
            satisfaction_levels[zone_id] = float(sol[z_idx(j)])

        logger.info(f"Optimization successful. Fairness level: {fairness_level:.3f}")
        return allocations, satisfaction_levels, fairness_level

    except Exception as e:
        logger.error(f"LP optimization error: {e}", exc_info=True)
        return _fallback_allocation(
            zones,
            resource_scores,
            nominal_allocations,
            capacities,
            resource_types,
            score_threshold=score_threshold,
        )


def _fallback_allocation(
    zones: List[Dict],
    resource_scores: Dict[str, Dict[str, float]],
    nominal_allocations: Dict[str, float],
    capacities: Dict[str, int],
    resource_types: List[str],
    *,
    score_threshold: float = 0.05,
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, float], float]:
    """
    Fallback proportional allocation if LP fails.

    Uses necessity-aware ideal bundles a_ij, then scales each resource type by
    min(1, capacity / total_demand) and applies that scaling to each zone's demand.

    Returns:
        allocations, satisfaction_levels (min per-zone scaling across demanded resources),
        and min_satisfaction across zones.
    """
    logger.warning("Using fallback proportional allocation")

    ideal_bundles = compute_ideal_bundles(
        zones,
        resource_scores,
        nominal_allocations,
        score_threshold=score_threshold,
    )

    # Total demand per resource
    total_demand = {r: 0.0 for r in resource_types}
    for _, bundle in ideal_bundles.items():
        for resource_id, amount in bundle.items():
            total_demand[resource_id] += float(amount)

    # Scaling per resource to fit capacities
    scaling: Dict[str, float] = {}
    for resource_id in resource_types:
        demand = float(total_demand.get(resource_id, 0.0))
        cap = float(capacities.get(resource_id, 0))
        if demand > 0.0:
            scaling[resource_id] = min(1.0, cap / demand)
        else:
            scaling[resource_id] = 1.0

    allocations: Dict[str, Dict[str, float]] = {}
    satisfaction_levels: Dict[str, float] = {}
    min_satisfaction = 1.0

    for zone in zones:
        zone_id = zone["zone_id"]
        bundle = ideal_bundles.get(zone_id, {})
        allocations[zone_id] = {}

        # zone satisfaction = min scaling among resources it actually demands
        zone_satisfactions: List[float] = []

        for resource_id, ideal_amount in bundle.items():
            ideal_amount = float(ideal_amount)
            if ideal_amount <= 0.0:
                continue
            s = float(scaling[resource_id])
            allocated = ideal_amount * s
            if allocated > 1e-6:
                allocations[zone_id][resource_id] = round(allocated, 2)
            zone_satisfactions.append(s)

        if zone_satisfactions:
            satisfaction_levels[zone_id] = float(min(zone_satisfactions))
        else:
            satisfaction_levels[zone_id] = 0.0

        min_satisfaction = min(min_satisfaction, satisfaction_levels[zone_id])

    return allocations, satisfaction_levels, float(min_satisfaction)

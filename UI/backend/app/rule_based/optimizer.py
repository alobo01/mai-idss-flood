"""
Linear programming optimizer for fair resource allocation.

Implements max-min fairness objective to ensure equitable distribution
of resources across zones while respecting capacity constraints.

References:
- Chen & Hooker (2023): A Guide to Fairness in Optimization
- Kaplan (1974): On a Two-Stage Linear Programming Model with Fixed-Charge Variables
- Luss (1999): On Equitable Resource Allocation Problems: A Lexicographic Minimax Approach
"""

from typing import Dict, List, Tuple
import logging

import numpy as np
from scipy.optimize import linprog

logger = logging.getLogger(__name__)


def compute_ideal_bundles(
    zones: List[Dict],
    resource_scores: Dict[str, Dict[str, float]],
    nominal_allocations: Dict[str, float]
) -> Dict[str, Dict[str, float]]:
    """
    Compute ideal resource bundle for each zone based on priority scores.

    For zone j with nominal allocation R_j, the ideal amount of resource i is:
        a_ij = R_j * (s_ij / sum_h(s_hj))

    Args:
        zones: List of zone dictionaries with zone_id
        resource_scores: Dict mapping zone_id -> {resource_id: score}
        nominal_allocations: Dict mapping zone_id -> total nominal units

    Returns:
        Dict mapping zone_id -> {resource_id: ideal_amount}
    """
    ideal_bundles = {}

    for zone in zones:
        zone_id = zone["zone_id"]
        scores = resource_scores.get(zone_id, {})
        R_j = nominal_allocations.get(zone_id, 0)

        # Filter positive scores
        relevant_scores = {k: v for k, v in scores.items() if v > 0}

        if not relevant_scores or R_j <= 0:
            ideal_bundles[zone_id] = {}
            continue

        # Normalize scores to sum to R_j
        total_score = sum(relevant_scores.values())
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
    resource_types: List[str]
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, float], float]:
    """
    Solve max-min fairness LP for resource allocation.

    Maximizes the minimum satisfaction level across zones while respecting
    capacity constraints and zone-specific resource preferences.

    Decision variables:
    - x_ij: amount of resource i allocated to zone j
    - z_j: satisfaction level of zone j (fraction of ideal bundle)
    - t: minimum satisfaction level (fairness level)

    Objective: max t

    Constraints:
    1. Fairness coupling: t <= z_j for all j
    2. Bundle satisfaction: x_ij >= a_ij * z_j for all i,j where a_ij > 0
    3. Capacity: sum_j x_ij <= B_i for all i
    4. Bounds: 0 <= z_j <= 1, x_ij >= 0

    Args:
        zones: List of zone dictionaries
        resource_scores: Zone-specific resource priority scores
        nominal_allocations: Nominal units per zone from upstream
        capacities: Available capacity for each resource type
        resource_types: List of resource type IDs

    Returns:
        Tuple of (allocations, satisfaction_levels, fairness_level)
        - allocations: Dict[zone_id, Dict[resource_id, amount]]
        - satisfaction_levels: Dict[zone_id, fraction]
        - fairness_level: float (minimum satisfaction across zones)
    """

    # Compute ideal bundles
    ideal_bundles = compute_ideal_bundles(zones, resource_scores, nominal_allocations)

    zone_ids = [z["zone_id"] for z in zones]
    n_resources = len(resource_types)
    n_zones = len(zones)

    # Variable indices:
    # x_ij: indices 0 to (n_resources * n_zones - 1)
    # z_j: indices (n_resources * n_zones) to (n_resources * n_zones + n_zones - 1)
    # t: index (n_resources * n_zones + n_zones)

    n_x_vars = n_resources * n_zones
    n_z_vars = n_zones
    n_vars = n_x_vars + n_z_vars + 1  # x's, z's, and t

    # Helper to get variable index
    def x_idx(i: int, j: int) -> int:
        return i * n_zones + j

    def z_idx(j: int) -> int:
        return n_x_vars + j

    def t_idx() -> int:
        return n_x_vars + n_z_vars

    # Objective: maximize t (minimize -t)
    c = np.zeros(n_vars)
    c[t_idx()] = -1.0

    # Inequality constraints: A_ub @ x <= b_ub
    A_ub = []
    b_ub = []

    # 1. Fairness coupling: t <= z_j  =>  t - z_j <= 0  for all j
    for j in range(n_zones):
        row = np.zeros(n_vars)
        row[t_idx()] = 1.0
        row[z_idx(j)] = -1.0
        A_ub.append(row)
        b_ub.append(0.0)

    # 2. Bundle satisfaction (as inequality): -x_ij + a_ij * z_j <= 0
    #    =>  x_ij >= a_ij * z_j  for all i,j where a_ij > 0
    for j, zone_id in enumerate(zone_ids):
        ideal = ideal_bundles.get(zone_id, {})
        for i, resource_id in enumerate(resource_types):
            a_ij = ideal.get(resource_id, 0.0)
            if a_ij > 0:
                row = np.zeros(n_vars)
                row[x_idx(i, j)] = -1.0
                row[z_idx(j)] = a_ij
                A_ub.append(row)
                b_ub.append(0.0)

    # 3. Capacity constraints: sum_j x_ij <= B_i  for all i
    for i, resource_id in enumerate(resource_types):
        row = np.zeros(n_vars)
        for j in range(n_zones):
            row[x_idx(i, j)] = 1.0
        A_ub.append(row)
        b_ub.append(float(capacities.get(resource_id, 0)))

    A_ub = np.array(A_ub)
    b_ub = np.array(b_ub)

    # Bounds: x_ij >= 0, 0 <= z_j <= 1, t unbounded (but will be <= 1)
    bounds = []
    for i in range(n_resources):
        for j in range(n_zones):
            bounds.append((0, None))  # x_ij >= 0
    for j in range(n_zones):
        bounds.append((0, 1))  # 0 <= z_j <= 1
    bounds.append((None, None))  # t unbounded

    # Solve LP
    try:
        result = linprog(
            c, A_ub=A_ub, b_ub=b_ub, bounds=bounds,
            method='highs',
            options={'disp': False}
        )

        if not result.success:
            logger.warning(f"LP optimization failed: {result.message}")
            # Return fallback: proportional allocation within capacity
            return _fallback_allocation(
                zones,
                resource_scores,
                nominal_allocations,
                capacities,
                resource_types,
            )

        # Extract solution
        x = result.x
        fairness_level = x[t_idx()]

        allocations = {}
        satisfaction_levels = {}

        for j, zone_id in enumerate(zone_ids):
            allocations[zone_id] = {}
            for i, resource_id in enumerate(resource_types):
                amount = x[x_idx(i, j)]
                if amount > 1e-6:  # Filter near-zero allocations
                    allocations[zone_id][resource_id] = round(amount, 2)

            satisfaction_levels[zone_id] = float(x[z_idx(j)])

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
        )


def _fallback_allocation(
    zones: List[Dict],
    resource_scores: Dict[str, Dict[str, float]],
    nominal_allocations: Dict[str, float],
    capacities: Dict[str, int],
    resource_types: List[str]
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, float], float]:
    """
    Fallback proportional allocation if LP fails.
    """
    logger.warning("Using fallback proportional allocation")

    ideal_bundles = compute_ideal_bundles(zones, resource_scores, nominal_allocations)

    # Compute total demand per resource
    total_demand = {r: 0.0 for r in resource_types}
    for zone_id, bundle in ideal_bundles.items():
        for resource_id, amount in bundle.items():
            total_demand[resource_id] += amount

    # Compute scaling factor per resource (capacity / demand)
    scaling = {}
    for resource_id in resource_types:
        demand = total_demand.get(resource_id, 0.0)
        capacity = capacities.get(resource_id, 0)
        if demand > 0:
            scaling[resource_id] = min(1.0, capacity / demand)
        else:
            scaling[resource_id] = 1.0

    # Apply scaling
    allocations = {}
    satisfaction_levels = {}
    min_satisfaction = 1.0

    for zone_id, bundle in ideal_bundles.items():
        allocations[zone_id] = {}
        zone_satisfactions = []

        for resource_id, ideal_amount in bundle.items():
            if ideal_amount > 0:
                allocated = ideal_amount * scaling[resource_id]
                if allocated > 1e-6:
                    allocations[zone_id][resource_id] = round(allocated, 2)
                zone_satisfactions.append(scaling[resource_id])

        if zone_satisfactions:
            satisfaction_levels[zone_id] = min(zone_satisfactions)
        else:
            satisfaction_levels[zone_id] = 0.0

        min_satisfaction = min(min_satisfaction, satisfaction_levels[zone_id])

    return allocations, satisfaction_levels, min_satisfaction

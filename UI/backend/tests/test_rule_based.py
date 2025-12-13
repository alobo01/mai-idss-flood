"""
Tests for rule-based dispatch functionality.
"""
import pytest
from unittest.mock import Mock, patch
import numpy as np

from app.rule_based.zones import (
    compute_vulnerability,
    compute_pf_by_zone_from_global,
    build_zones_from_data,
    _ensure_float,
)
from app.rule_based.allocations import (
    recommend_resources_proportional,
    recommend_resources_crisp,
    recommend_resources_fuzzy,
    classify_impact,
    _crisp_fraction,
    _fuzzy_fraction,
    resource_priority_list,
    fuzzy_resource_scores,
    old_rule_based_resource_scores,
    allocate_resources,
    build_dispatch_plan,
    get_resource_types,
    RESOURCE_TYPES,
)
from app.schemas import Zone, AllocationMode, ImpactLevel


class TestZoneHelpers:
    """Test zone helper functions."""

    def test_ensure_float(self):
        """Test _ensure_float helper function."""
        assert _ensure_float(5.5) == 5.5
        assert _ensure_float("5.5") == 5.5
        assert _ensure_float(None) == 0.0
        assert _ensure_float("invalid") == 0.0

    def test_compute_vulnerability(self):
        """Test vulnerability computation."""
        attrs = {
            "river_proximity": 0.8,
            "elevation_risk": 0.6,
            "pop_density": 0.7,
            "crit_infra_score": 0.9,
        }
        vulnerability = compute_vulnerability(attrs)

        expected = (0.35 * 0.8 + 0.25 * 0.6 + 0.25 * 0.7 + 0.15 * 0.9)
        assert abs(vulnerability - expected) < 1e-6

    def test_compute_vulnerability_missing_attrs(self):
        """Test vulnerability computation with missing attributes."""
        attrs = {
            "river_proximity": 0.5,
            # Missing other attributes
        }
        vulnerability = compute_vulnerability(attrs)

        expected = 0.35 * 0.5  # Only river_proximity contributes
        assert abs(vulnerability - expected) < 1e-6

    def test_compute_pf_by_zone_from_global(self):
        """Test zone flood probability computation."""
        rows = [
            {"zone_id": "ZONE_001", "river_proximity": 0.9},
            {"zone_id": "ZONE_002", "river_proximity": 0.6},
            {"zone_id": "ZONE_003", "river_proximity": 0.3},
        ]
        global_pf = 0.5
        pf_by_zone = compute_pf_by_zone_from_global(rows, global_pf)

        assert pf_by_zone["ZONE_001"] > pf_by_zone["ZONE_002"]
        assert pf_by_zone["ZONE_002"] > pf_by_zone["ZONE_003"]
        assert all(pf <= 1.0 for pf in pf_by_zone.values())

    def test_compute_pf_by_zone_from_global_edge_cases(self):
        """Test zone flood probability with edge cases."""
        # Test with no river proximity data
        rows = [{"zone_id": "ZONE_001", "river_proximity": None}]
        pf_by_zone = compute_pf_by_zone_from_global(rows, 0.5)

        assert pf_by_zone["ZONE_001"] == 0.25  # Base weight

    def test_build_zones_from_data(self, sample_zone_data):
        """Test building Zone objects from data."""
        pf_by_zone = {"ZONE_001": 0.6, "ZONE_002": 0.4, "ZONE_003": 0.2}
        zones = build_zones_from_data(sample_zone_data, pf_by_zone)

        assert len(zones) == 3
        assert isinstance(zones[0], Zone)
        assert zones[0].zone_id == "ZONE_001"
        assert zones[0].pf == 0.6
        assert zones[0].vulnerability > 0
        assert zones[0].is_critical_infra is True  # Has hospitals


class TestImpactClassification:
    """Test impact level classification."""

    def test_classify_impact(self):
        """Test impact level classification."""
        # Test LOW impact
        impact = classify_impact(0.1, 0.1)  # iz = 0.01
        assert impact == ImpactLevel.NORMAL

        # Test ADVISORY impact
        impact = classify_impact(0.3, 0.8)  # iz = 0.24
        assert impact == ImpactLevel.ADVISORY

        # Test WARNING impact
        impact = classify_impact(0.6, 0.8)  # iz = 0.48
        assert impact == ImpactLevel.WARNING

        # Test CRITICAL impact
        impact = classify_impact(0.9, 0.9)  # iz = 0.81
        assert impact == ImpactLevel.CRITICAL

    def test_crisp_fraction(self):
        """Test crisp fraction computation."""
        # Test NORMAL impact
        fraction = _crisp_fraction("NORMAL", False)
        assert fraction == 0.0

        # Test ADVISORY impact
        fraction = _crisp_fraction("ADVISORY", False)
        assert fraction == 0.1

        # Test WARNING impact
        fraction = _crisp_fraction("WARNING", False)
        assert fraction == 0.3

        # Test CRITICAL impact
        fraction = _crisp_fraction("CRITICAL", False)
        assert fraction == 0.5

        # Test CRITICAL impact with critical infrastructure
        fraction = _crisp_fraction("CRITICAL", True)
        assert fraction == 0.6

    def test_fuzzy_fraction(self):
        """Test fuzzy fraction computation."""
        # Test low impact
        fraction = _fuzzy_fraction(0.1, False)
        assert 0.0 <= fraction <= 0.6

        # Test high impact
        fraction = _fuzzy_fraction(0.9, False)
        assert 0.0 <= fraction <= 0.6

        # Test critical infrastructure bonus
        fraction_regular = _fuzzy_fraction(0.85, False)
        fraction_critical = _fuzzy_fraction(0.85, True)
        assert fraction_critical > fraction_regular


class TestResourceAllocation:
    """Test resource allocation functions."""

    def test_recommend_resources_proportional(self, sample_zones):
        """Test proportional resource allocation."""
        zone = sample_zones[0]  # Downtown zone with high impact
        total_units = 100
        iz = zone.pf * zone.vulnerability
        sum_iz = sum(z.pf * z.vulnerability for z in sample_zones)

        recommendation = recommend_resources_proportional(zone, total_units, iz, sum_iz)

        assert recommendation["zone_id"] == zone.id
        assert recommendation["zone_name"] == zone.name
        assert recommendation["allocation_mode"] == "PROPORTIONAL"
        assert isinstance(recommendation["units_allocated"], int)

    def test_recommend_resources_crisp(self, sample_zones):
        """Test crisp resource allocation."""
        zone = sample_zones[0]
        total_units = 100

        recommendation = recommend_resources_crisp(zone, total_units)

        assert recommendation["zone_id"] == zone.id
        assert recommendation["allocation_mode"] == "CRISP"
        assert isinstance(recommendation["units_allocated"], int)
        assert recommendation["units_allocated"] >= 0

    def test_recommend_resources_fuzzy(self, sample_zones):
        """Test fuzzy resource allocation."""
        zone = sample_zones[0]
        total_units = 100

        recommendation = recommend_resources_fuzzy(zone, total_units)

        assert recommendation["zone_id"] == zone.id
        assert recommendation["allocation_mode"] == "FUZZY"
        assert isinstance(recommendation["units_allocated"], int)
        assert recommendation["units_allocated"] >= 0

    def test_recommend_resources_minimum_allocation(self, sample_zones):
        """Test that impacted zones get minimum allocation."""
        zone = sample_zones[0]
        # Ensure zone has significant impact
        zone.pf = 0.8
        zone.vulnerability = 0.8

        recommendation = recommend_resources_crisp(zone, 1)  # Very limited resources

        # Should get at least 1 unit if impact is significant
        assert recommendation["units_allocated"] >= 1

    def test_allocate_resources_crisp_mode(self, sample_zones):
        """Test overall resource allocation in crisp mode."""
        total_units = 50
        allocations = allocate_resources(sample_zones, total_units, mode="crisp")

        assert len(allocations) == len(sample_zones)
        total_allocated = sum(a["units_allocated"] for a in allocations)
        assert total_allocated <= total_units

        # Check that allocations are reasonable
        for allocation in allocations:
            assert allocation["units_allocated"] >= 0

    def test_allocate_resources_fuzzy_mode(self, sample_zones):
        """Test overall resource allocation in fuzzy mode."""
        total_units = 50
        allocations = allocate_resources(sample_zones, total_units, mode="fuzzy")

        assert len(allocations) == len(sample_zones)
        total_allocated = sum(a["units_allocated"] for a in allocations)
        assert total_allocated <= total_units

    def test_allocate_resources_proportional_mode(self, sample_zones):
        """Test overall resource allocation in proportional mode."""
        total_units = 50
        allocations = allocate_resources(sample_zones, total_units, mode="proportional")

        assert len(allocations) == len(sample_zones)
        total_allocated = sum(a["units_allocated"] for a in allocations)
        assert total_allocated <= total_units

    def test_allocate_resources_invalid_mode(self, sample_zones):
        """Test resource allocation with invalid mode."""
        with pytest.raises(ValueError):
            allocate_resources(sample_zones, 50, mode="invalid")

    def test_allocate_resources_max_units_per_zone(self, sample_zones):
        """Test resource allocation with maximum units per zone."""
        total_units = 100
        max_units = 20
        allocations = allocate_resources(
            sample_zones, total_units, mode="fuzzy", max_units_per_zone=max_units
        )

        for allocation in allocations:
            assert allocation["units_allocated"] <= max_units


class TestResourcePriority:
    """Test resource priority calculations."""

    def test_resource_priority_list(self, sample_zones):
        """Test resource priority list generation."""
        zone = sample_zones[0]
        priority_list = resource_priority_list(zone)

        assert "zone_id" in priority_list
        assert "zone_name" in priority_list
        assert "priority_index" in priority_list
        assert "resource_scores" in priority_list
        assert "resource_priority" in priority_list

        assert priority_list["zone_id"] == zone.id
        assert 0.0 <= priority_list["priority_index"] <= 1.0
        assert isinstance(priority_list["resource_scores"], dict)
        assert isinstance(priority_list["resource_priority"], list)

    @patch('app.rule_based.allocations._HAS_SIMPFUL', False)
    def test_fuzzy_resource_scores_fallback(self, sample_zones):
        """Test fuzzy resource scores fallback when simpful unavailable."""
        zone = sample_zones[0]
        scores = fuzzy_resource_scores(zone)

        assert isinstance(scores, dict)
        for resource_type in RESOURCE_TYPES:
            assert resource_type in scores
            assert isinstance(scores[resource_type], float)
            assert scores[resource_type] >= 0.0

    def test_old_rule_based_resource_scores(self, sample_zones):
        """Test old rule-based resource scoring."""
        zone = sample_zones[0]
        # Set high values to trigger scoring
        zone.pf = 0.8
        zone.vulnerability = 0.8

        scores = old_rule_based_resource_scores(zone)

        assert isinstance(scores, dict)
        for resource_type in RESOURCE_TYPES:
            assert resource_type in scores
            assert isinstance(scores[resource_type], (int, float))

        # High PF and vulnerability should trigger some resource allocation
        assert scores["R4_RESCUE"] > 0

    def test_resource_priority_filtering(self, sample_zones):
        """Test resource priority filtering by threshold."""
        zone = sample_zones[0]
        # Use a high threshold to filter most resources
        priority_list = resource_priority_list(zone, threshold=0.9)

        # Should have fewer resources due to filtering
        filtered_count = len(priority_list["resource_priority"])
        total_count = len(RESOURCE_TYPES)
        assert filtered_count <= total_count


class TestDispatchPlan:
    """Test dispatch plan generation."""

    def test_build_dispatch_plan_heuristic(self, sample_zones):
        """Test building dispatch plan with heuristic allocation."""
        total_units = 50
        dispatch_plan = build_dispatch_plan(
            sample_zones, total_units, mode="fuzzy", use_optimizer=False
        )

        assert len(dispatch_plan) == len(sample_zones)
        total_allocated = sum(zone["units_allocated"] for zone in dispatch_plan)
        assert total_allocated <= total_units

        # Check structure of dispatch plan
        for allocation in dispatch_plan:
            assert "zone_id" in allocation
            assert "zone_name" in allocation
            assert "impact_level" in allocation
            assert "allocation_mode" in allocation
            assert "units_allocated" in allocation

    @patch('app.rule_based.allocations.optimize_fair_allocation')
    def test_build_dispatch_plan_optimized(self, mock_optimize, sample_zones, sample_resource_types):
        """Test building dispatch plan with optimizer."""
        # Setup mock optimizer response
        mock_allocations = {
            "ZONE_001": {"R1_UAV": 2, "R2_ENGINEERING": 3},
            "ZONE_002": {"R1_UAV": 1, "R3_PUMPS": 2},
        }
        mock_satisfaction = {"ZONE_001": 0.8, "ZONE_002": 0.6}
        mock_fairness = 0.7
        mock_optimize.return_value = (mock_allocations, mock_satisfaction, mock_fairness)

        # Setup resource capacities
        resource_capacities = {"R1_UAV": 10, "R2_ENGINEERING": 15, "R3_PUMPS": 20}

        dispatch_plan = build_dispatch_plan(
            sample_zones,
            total_units=50,
            use_optimizer=True,
            resource_capacities=resource_capacities
        )

        assert len(dispatch_plan) == len(sample_zones)

        # Check that optimizer was called
        mock_optimize.assert_called_once()

        # Check optimized allocation structure
        for allocation in dispatch_plan:
            assert allocation["allocation_mode"] == "OPTIMIZED"
            assert "satisfaction_level" in allocation
            assert "fairness_level" in allocation

    @patch('app.rule_based.allocations.optimize_fair_allocation')
    def test_build_dispatch_plan_optimizer_fallback(self, mock_optimize, sample_zones, sample_resource_types):
        """Test fallback to heuristic when optimizer fails."""
        # Make optimizer fail
        mock_optimize.side_effect = Exception("Optimization failed")

        resource_capacities = {"R1_UAV": 10, "R2_ENGINEERING": 15}

        dispatch_plan = build_dispatch_plan(
            sample_zones,
            total_units=50,
            use_optimizer=True,
            resource_capacities=resource_capacities
        )

        # Should fallback to heuristic mode
        assert len(dispatch_plan) == len(sample_zones)
        # First allocation should indicate fallback occurred
        # (This depends on implementation details)

    def test_dispatch_plan_resource_aggregation(self, sample_zones):
        """Test resource aggregation in dispatch plan."""
        total_units = 30
        dispatch_plan = build_dispatch_plan(
            sample_zones, total_units, mode="fuzzy", use_optimizer=False
        )

        # Check that resource units are properly distributed
        for allocation in dispatch_plan:
            if allocation["units_allocated"] > 0:
                assert "resource_units" in allocation
                assert "resource_priority" in allocation

                # Should have resource allocations
                total_resource_units = sum(allocation["resource_units"].values())
                assert total_resource_units == allocation["units_allocated"]


class TestIntegration:
    """Integration tests for rule-based dispatch."""

    def test_end_to_end_dispatch_workflow(self, sample_zone_data):
        """Test complete workflow from zone data to dispatch plan."""
        # Build zones from data
        pf_by_zone = {"ZONE_001": 0.7, "ZONE_002": 0.4, "ZONE_003": 0.2}
        zones = build_zones_from_data(sample_zone_data, pf_by_zone)

        # Generate dispatch plan
        total_units = 50
        dispatch_plan = build_dispatch_plan(
            zones, total_units, mode="fuzzy", use_optimizer=False
        )

        # Verify complete workflow
        assert len(dispatch_plan) == 3

        # Check that high-risk zones get more resources
        zone_001_allocation = next(a for a in dispatch_plan if a["zone_id"] == "ZONE_001")
        zone_003_allocation = next(a for a in dispatch_plan if a["zone_id"] == "ZONE_003")

        # Downtown (ZONE_001) should get more resources than North County (ZONE_003)
        assert zone_001_allocation["units_allocated"] >= zone_003_allocation["units_allocated"]

    def test_dispatch_with_critical_infrastructure_priority(self):
        """Test that critical infrastructure gets appropriate priority."""
        # Create zones with different critical infrastructure status
        zone_data = [
            {
                "zone_id": "CRITICAL",
                "name": "Critical Zone",
                "pf": 0.5,
                "vulnerability": 0.5,
                "is_critical_infra": True,
                "hospital_count": 2,
                "river_proximity": 0.7,
                "elevation_risk": 0.4,
                "pop_density": 0.6,
                "crit_infra_score": 0.8,
            },
            {
                "zone_id": "NORMAL",
                "name": "Normal Zone",
                "pf": 0.5,
                "vulnerability": 0.5,
                "is_critical_infra": False,
                "hospital_count": 0,
                "river_proximity": 0.7,
                "elevation_risk": 0.4,
                "pop_density": 0.6,
                "crit_infra_score": 0.2,
            },
        ]

        zones = [Zone(**data) for data in zone_data]
        total_units = 20

        dispatch_plan = build_dispatch_plan(
            zones, total_units, mode="crisp", use_optimizer=False
        )

        critical_zone = next(a for a in dispatch_plan if a["zone_id"] == "CRITICAL")
        normal_zone = next(a for a in dispatch_plan if a["zone_id"] == "NORMAL")

        # Critical zone should get equal or more resources in crisp mode
        assert critical_zone["units_allocated"] >= normal_zone["units_allocated"]
import pandas as pd
import pytest

from pipeline_v2 import schema
from pipeline_v2.business_rules import BusinessRuleError, RuleSet, enforce_rules
from pipeline_v2.provenance import build_provenance
from pipeline_v2.zone_registry import load_zone_file

from pathlib import Path


def test_schema_validation_passes():
    df = pd.DataFrame(
        {
            "timestamp": ["2024-01-01T00:00:00Z"],
            "scenario": ["demo"],
            "zone_id": ["Z1"],
            "river_level_pred": [10.5],
            "global_pf": [0.5],
            "pf_zone": [0.4],
            "vulnerability": [0.7],
            "is_critical_infra": [True],
        }
    )
    assert schema.validate_dataframe("model_input", df, schema.MODEL_INPUT_SCHEMA) == []


def test_business_rules_detects_over_allocation():
    df = pd.DataFrame(
        {
            "timestamp": ["2024-01-01", "2024-01-01"],
            "zone_id": ["Z1", "Z2"],
            "units_allocated": [5, 7],
            "is_critical_infra": [True, False],
        }
    )
    rules = RuleSet(total_units=8, max_units_per_zone=6, min_critical_units=2)
    with pytest.raises(BusinessRuleError):
        enforce_rules(df, {"Z1", "Z2"}, rules)


def test_zone_registry_loads_profiles():
    bundle = load_zone_file("data1", Path("pipeline_v2/zone_configs/data1.yaml"))
    assert "Z1N" in bundle.zones
    assert bundle.zones["Z1N"].is_critical_infra is True


def test_provenance_hash(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("paths: {}\n", encoding="utf-8")
    input_file = tmp_path / "input.csv"
    input_file.write_text("col\n1\n", encoding="utf-8")
    record = build_provenance("demo", config, input_file, Path.cwd())
    assert record.config_hash
    assert record.input_hash

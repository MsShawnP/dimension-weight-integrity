"""Tests for the JSON export script — config loading and schema validation."""

import json
import pathlib

import pytest
import yaml

from scripts.export_frontend_json import DecimalEncoder, load_config

import decimal


def test_config_loads_all_rate_tables():
    config = load_config()
    assert 50 in config["ltl"]["rate_per_cwt"]
    assert 55 in config["ltl"]["rate_per_cwt"]
    assert 1 in config["parcel"]["rate_per_lb"]
    assert config["parcel"]["dim_divisor"] == 139


def test_decimal_encoder_converts_to_float():
    data = {"value": decimal.Decimal("21.50")}
    result = json.loads(json.dumps(data, cls=DecimalEncoder))
    assert result["value"] == 21.5
    assert isinstance(result["value"], float)


def test_hero_json_schema_keys():
    """Verify expected top-level keys in the hero JSON output."""
    hero_path = pathlib.Path(__file__).parent.parent / "frontend" / "src" / "data" / "hero.json"
    hero = json.loads(hero_path.read_text())
    expected_keys = {"hero_sku", "cost", "rate_tables", "paradox"}
    assert set(hero.keys()) == expected_keys


def test_config_rate_tables_match_hero_json_contract():
    """Rate tables embedded in hero.json must come from config."""
    config = load_config()
    ltl_rates = config["ltl"]["rate_per_cwt"]
    parcel_rates = config["parcel"]["rate_per_lb"]

    assert ltl_rates[50] == 18.00
    assert ltl_rates[55] == 19.80
    assert parcel_rates[1] == 9.80
    assert parcel_rates[3] == 11.77


def test_hero_json_annual_cost_formula():
    """annual_cost = per_unit_delta × annual_units for each cost driver."""
    hero_path = pathlib.Path(__file__).parent.parent / "frontend" / "src" / "data" / "hero.json"
    hero = json.loads(hero_path.read_text())
    for name, driver in hero["cost"].items():
        expected = round(driver["per_unit_delta"] * driver["annual_units"], 2)
        assert driver["annual_cost"] == expected, f"{name}: {driver['annual_cost']} != {expected}"

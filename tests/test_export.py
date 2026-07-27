"""Tests for the JSON export script — encoding and hero.json schema."""

import json
import pathlib

from scripts.export_frontend_json import DecimalEncoder

import decimal


def test_decimal_encoder_converts_to_float():
    data = {"value": decimal.Decimal("21.50")}
    result = json.loads(json.dumps(data, cls=DecimalEncoder))
    assert result["value"] == 21.5
    assert isinstance(result["value"], float)


def test_hero_json_schema_keys():
    """Verify expected top-level keys in the hero JSON output."""
    hero_path = pathlib.Path(__file__).parent.parent / "frontend" / "src" / "data" / "hero.json"
    hero = json.loads(hero_path.read_text())
    expected_keys = {"hero_sku", "cost", "paradox"}
    assert set(hero.keys()) == expected_keys


def test_hero_json_annual_cost_formula():
    """annual_cost = per_unit_delta × annual_units for each cost driver."""
    hero_path = pathlib.Path(__file__).parent.parent / "frontend" / "src" / "data" / "hero.json"
    hero = json.loads(hero_path.read_text())
    for name, driver in hero["cost"].items():
        expected = round(driver["per_unit_delta"] * driver["annual_units"], 2)
        assert driver["annual_cost"] == expected, f"{name}: {driver['annual_cost']} != {expected}"

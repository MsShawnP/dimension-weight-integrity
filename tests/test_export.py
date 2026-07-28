"""Tests for the JSON export script — encoding and hero.json schema."""

import json
import pathlib

import pytest

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


ALL_SKUS_PATH = pathlib.Path(__file__).parent.parent / "frontend" / "src" / "data" / "all_skus.json"

# The 18 valid NMFC classes. Membership only — the threshold mapping is
# drift-guarded in test_cost_math.py.
VALID_NMFC_CLASSES = {
    50, 55, 60, 65, 70, 77.5, 85, 92.5, 100, 110,
    125, 150, 175, 200, 250, 300, 400, 500,
}


@pytest.fixture
def all_skus():
    return json.loads(ALL_SKUS_PATH.read_text())


def test_all_skus_aggregate_reconciles_to_sku_totals(all_skus):
    total = sum(s["cost"]["total_annual_cost"] for s in all_skus["skus"])
    assert round(total, 2) == round(all_skus["aggregate"]["total_annual_cost"], 2)
    assert all_skus["aggregate"]["total_skus"] == len(all_skus["skus"])


def test_all_skus_row_totals_equal_sum_of_their_drivers(all_skus):
    for s in all_skus["skus"]:
        drivers = sum(d["annual_cost"] for d in s["cost"]["drivers"].values())
        assert round(drivers, 2) == round(s["cost"]["total_annual_cost"], 2), s["sku"]


def test_all_skus_driver_math_holds(all_skus):
    for s in all_skus["skus"]:
        for name, d in s["cost"]["drivers"].items():
            expected = round(d["per_unit_delta"] * d["annual_units"], 2)
            assert d["annual_cost"] == expected, f"{s['sku']}/{name}"


def test_no_sku_silently_fell_through_to_the_class_500_fallback(all_skus):
    """A zero or null cube yields a null density, which the dbt macro's CASE
    sends to the class-500 fallback — the most expensive class — with no error.
    Every shipped SKU must have a real positive density, so that fallback is
    never the reason a SKU is priced."""
    for s in all_skus["skus"]:
        density = s["density_lb_per_ft3"]
        assert density is not None and density > 0, f"{s['sku']} has no usable density"
        assert s["freight_class"] in VALID_NMFC_CLASSES, s["sku"]


def test_no_negative_costs_anywhere(all_skus):
    for s in all_skus["skus"]:
        assert s["cost"]["total_annual_cost"] >= 0, s["sku"]
        for name, d in s["cost"]["drivers"].items():
            assert d["annual_cost"] >= 0, f"{s['sku']}/{name}"


def test_hero_json_annual_cost_formula():
    """annual_cost = per_unit_delta × annual_units for each cost driver."""
    hero_path = pathlib.Path(__file__).parent.parent / "frontend" / "src" / "data" / "hero.json"
    hero = json.loads(hero_path.read_text())
    for name, driver in hero["cost"].items():
        expected = round(driver["per_unit_delta"] * driver["annual_units"], 2)
        assert driver["annual_cost"] == expected, f"{name}: {driver['annual_cost']} != {expected}"

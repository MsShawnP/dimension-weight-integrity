"""
End-to-end reconciliation: verify hero.json placeholder matches expected
physical constants and cost math.

These are the acceptance-example invariants (AE1-AE4) that must hold
regardless of whether the data comes from the pipeline or placeholders.
"""

import json
import math
from pathlib import Path

import pytest

HERO_JSON = Path(__file__).resolve().parent.parent / "frontend" / "src" / "data" / "hero.json"


@pytest.fixture
def hero():
    with open(HERO_JSON) as f:
        return json.load(f)


# --- AE1: Physical constants ---

class TestPhysicalConstants:
    def test_cube_ft3(self, hero):
        mor = hero["hero_sku"]["measurement_of_record"]
        expected = (mor["case_length_in"] * mor["case_width_in"] * mor["case_height_in"]) / 1728
        assert math.isclose(mor["case_cube_ft3"], expected, rel_tol=1e-3)

    def test_density(self, hero):
        mor = hero["hero_sku"]["measurement_of_record"]
        expected = mor["case_gross_weight_lb"] / mor["case_cube_ft3"]
        assert math.isclose(mor["density_lb_per_ft3"], expected, rel_tol=1e-2)

    def test_mor_freight_class(self, hero):
        assert hero["hero_sku"]["measurement_of_record"]["freight_class"] == 50

    def test_mor_source_is_wms(self, hero):
        assert hero["hero_sku"]["measurement_of_record"]["source"] == "wms"


# --- AE2: GDSN freight class mismatch ---

class TestGdsnMismatch:
    def test_gdsn_class_is_55(self, hero):
        assert hero["hero_sku"]["freight_by_system"]["gdsn"]["freight_class"] == 55

    def test_gdsn_density(self, hero):
        gdsn = hero["hero_sku"]["freight_by_system"]["gdsn"]
        assert math.isclose(gdsn["density"], 37.98, rel_tol=1e-2)


# --- AE3: Cost driver math ---

class TestCostMath:
    def test_ltl_annual_cost(self, hero):
        ltl = hero["cost"]["ltl_reclass"]
        expected = ltl["per_unit_delta"] * ltl["annual_units"]
        assert math.isclose(ltl["annual_cost"], expected, rel_tol=1e-3)

    def test_parcel_annual_cost(self, hero):
        parcel = hero["cost"]["parcel_reweigh"]
        expected = parcel["per_unit_delta"] * parcel["annual_units"]
        assert math.isclose(parcel["annual_cost"], expected, rel_tol=1e-3)

    def test_chargeback_annual_cost(self, hero):
        cb = hero["cost"]["compliance_cb"]
        expected = cb["per_unit_delta"] * cb["annual_units"]
        assert math.isclose(cb["annual_cost"], expected, rel_tol=1e-3)

    def test_total_annual_cost(self, hero):
        total = sum(d["annual_cost"] for d in hero["cost"].values())
        assert math.isclose(total, 1014.28, rel_tol=1e-3)


# --- AE4: Rate tables present ---

class TestRateTables:
    def test_ltl_rates_present(self, hero):
        rates = hero["rate_tables"]["ltl_rate_per_cwt"]
        assert "50" in rates
        assert "55" in rates

    def test_parcel_rates_present(self, hero):
        rates = hero["rate_tables"]["parcel_rate_per_lb"]
        assert len(rates) >= 2

    def test_dim_divisor(self, hero):
        assert hero["rate_tables"]["dim_divisor"] == 139

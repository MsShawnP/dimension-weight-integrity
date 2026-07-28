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
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
HERO_JSON = REPO_ROOT / "frontend" / "src" / "data" / "hero.json"
COST_PARAMS = REPO_ROOT / "config" / "cost_params.yml"


@pytest.fixture
def hero():
    with open(HERO_JSON, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def cost_params():
    with open(COST_PARAMS, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def ltl_rate_per_cwt(cost_params):
    return {float(k): float(v) for k, v in cost_params["ltl"]["rate_per_cwt"].items()}


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
    # The three tests below check that hero.json foots against itself:
    # annual_cost == per_unit_delta x annual_units. They restate the arithmetic
    # the generator already performed, so they hold for ANY per_unit_delta,
    # including a wrong one. They are self-consistency checks, not correctness
    # checks -- see the un-pinned tests at the bottom of this class for the
    # assertion that actually constrains the basis.
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

    # --- The LTL driver must be $/case against an annual CASE count ---
    #
    # These replaced a frozen `total == 654.28`, which had made a unit mismatch
    # a requirement: per_unit_delta is a $/case figure (case cwt x rate delta)
    # but was multiplied by a count of PALLET shipments, understating the
    # driver by roughly a pallet's worth of cases.
    #
    # The earlier framing of this defect -- that the delta should be repriced
    # onto a pallet weight, needing a new ti/hi field -- was wrong. LTL bills
    # per hundredweight, so the penalty falls on tonnage shipped and
    # cases_per_pallet cancels out of the product entirely:
    #
    #   (cases_per_pallet x case_lb/100) x rate_delta x pallets_per_year
    #     == (case_lb/100) x rate_delta x annual_cases
    #
    # So per_unit_delta was already correct and only the multiplier was wrong.
    # These two tests pin that unit contract from both sides.

    def test_ltl_delta_is_priced_per_case(self, hero, ltl_rate_per_cwt):
        """per_unit_delta = case hundredweight x the class rate delta."""
        ltl = hero["cost"]["ltl_reclass"]
        basis = ltl["basis"]
        case_lb = basis["case_weight_lb"]
        delta_per_cwt = (
            ltl_rate_per_cwt[float(basis["gdsn_class"])]
            - ltl_rate_per_cwt[float(basis["mor_class"])]
        )
        expected = max(0.0, (case_lb / 100.0) * delta_per_cwt)
        assert math.isclose(ltl["per_unit_delta"], round(expected, 2), abs_tol=0.01), (
            f"LTL delta {ltl['per_unit_delta']} is not {case_lb} lb / 100 x "
            f"{delta_per_cwt:.2f} $/cwt = {expected:.4f}"
        )

    def test_ltl_annual_units_is_a_case_count_not_a_pallet_count(self, hero, cost_params):
        """The multiplier must be annual CASES, derived from revenue.

        A pallet count here would be a unit mismatch against a $/case delta.
        """
        ltl = hero["cost"]["ltl_reclass"]
        cfg = cost_params["ltl"]
        case_pack = ltl["basis"]["case_pack_qty"]
        expected = round(
            cfg["annual_wholesale_revenue_per_sku"]
            / cfg["wholesale_price_per_unit"]
            / case_pack
        )
        assert ltl["annual_units"] == expected, (
            f"LTL annual_units {ltl['annual_units']} is not the derived annual "
            f"case count {expected} (revenue / unit price / case pack {case_pack})"
        )
        # Guard the specific regression: a weekly-pallet count is ~2 orders of
        # magnitude too small to be a case volume for a $500k/yr SKU.
        assert ltl["annual_units"] > 1000, (
            "annual_units looks like a pallet count, not an annual case count"
        )



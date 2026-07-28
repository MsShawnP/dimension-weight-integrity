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
    with open(HERO_JSON, encoding="utf-8") as f:
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

    # --- Un-pinned: the LTL basis is a case weight against pallet shipments ---
    #
    # test_total_annual_cost used to assert the portfolio total was exactly
    # 654.28 (20.28 LTL + 394.00 parcel + 240.00 chargeback). That constant is
    # downstream of the Critical in dbt/models/marts/fct_dimension_cost.sql:27,
    # where per_unit_delta divides a CASE weight (21.5 lb) by 100 to get
    # hundredweight and is then multiplied by 52 PALLET shipments. The rate
    # delta is priced on 0.215 cwt when the shipped unit is 8.60 cwt --
    # build_spec_dimension_integrity.md:75 gives 1 pallet = 40 x 21.50 lb =
    # 8.60 cwt, delta $15.48/pallet. Freezing 654.28 made the wrong basis a
    # requirement.
    #
    # Both replacements assert the corrected contract under xfail(strict=True):
    # green now, and the marker XPASSes and fails the suite the moment the
    # basis is fixed, so it cannot silently outlive the defect.
    # Tracked in PLAN.md -- "LTL delta is priced on a case, not a pallet".

    @pytest.mark.xfail(
        strict=True,
        reason="fct_dimension_cost.sql:27 prices the rate delta on a case weight",
    )
    def test_ltl_delta_is_priced_on_the_shipped_unit_not_a_case(self, hero):
        ltl = hero["cost"]["ltl_reclass"]
        basis = ltl["basis"]
        # annual_units counts pallet shipments, so the weight the rate delta is
        # applied to has to be a pallet's weight. Today the only weight in the
        # basis is case_weight_lb, which is what makes the figure ~40x light.
        shipped_unit_lb = basis.get("shipped_unit_weight_lb")
        assert shipped_unit_lb is not None, (
            "LTL basis names no shipped-unit weight; it prices on "
            f"case_weight_lb={basis.get('case_weight_lb')} while annual_units "
            f"counts {ltl['annual_units']} pallet shipments"
        )
        assert shipped_unit_lb > basis["case_weight_lb"], (
            "shipped-unit weight is not heavier than one case"
        )

    @pytest.mark.xfail(
        strict=True,
        reason="portfolio total inherits the case-weight LTL basis",
    )
    def test_total_annual_cost_is_not_the_case_weight_figure(self, hero):
        total = sum(d["annual_cost"] for d in hero["cost"].values())
        assert not math.isclose(total, 654.28, rel_tol=1e-3), (
            "portfolio total still carries the case-weight LTL component"
        )



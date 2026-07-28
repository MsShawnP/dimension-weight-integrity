"""Tests for cost parameter loading and physical computation math."""

import json
import math
import pathlib
import re

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "cost_params.yml"


@pytest.fixture
def config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


# --- Config Loading ---


def test_config_loads_successfully(config):
    assert config is not None


def test_config_has_all_required_sections(config):
    for section in ("ltl", "parcel", "chargebacks", "tolerances", "hero_sku"):
        assert section in config, f"Missing config section: {section}"


def test_ltl_rate_table_has_class_50_and_55(config):
    rates = config["ltl"]["rate_per_cwt"]
    assert rates[50] == 18.00
    assert rates[55] == 19.80


def test_parcel_rate_table_has_weight_tiers(config):
    rates = config["parcel"]["rate_per_lb"]
    assert rates[1] == 9.80
    assert rates[2] == 10.96
    assert rates[3] == 11.77
    assert rates[4] == 12.41
    assert rates[5] == 12.97


def test_dim_divisor_is_139(config):
    assert config["parcel"]["dim_divisor"] == 139


# --- Physical Computation Math (Python equivalents of dbt macros) ---


def cube_ft3(length_in, width_in, height_in):
    return (length_in * width_in * height_in) / 1728.0


def density_lb_per_ft3(weight_lb, cube):
    return weight_lb / cube


def density_to_nmfc_class(density):
    # Canonical NMFC density scale. Must match dbt/macros/density_to_nmfc_class.sql
    # exactly -- see test_python_nmfc_table_is_canonical and
    # test_dbt_macro_nmfc_table_matches_canonical. The frontend no longer
    # carries a copy; it renders costs precomputed by the pipeline.
    bands = [
        (50.0, 50), (35.0, 55), (30.0, 60), (22.5, 65),
        (15.0, 70), (13.5, 77.5), (12.0, 85), (10.5, 92.5),
        (9.0, 100), (8.0, 110), (7.0, 125), (6.0, 150),
        (5.0, 175), (4.0, 200), (3.0, 250), (2.0, 300),
        (1.0, 400),
    ]
    for threshold, nmfc_class in bands:
        if density >= threshold:
            return nmfc_class
    return 500


def dim_weight_lb(length_in, width_in, height_in, divisor):
    return (math.ceil(length_in) * math.ceil(width_in) * math.ceil(height_in)) / divisor


def billable_weight_lb(actual_weight, dim_weight):
    return math.ceil(max(actual_weight, dim_weight))


# Hero SKU reconciliation invariants (AE3)


def test_hero_cube():
    result = cube_ft3(11.25, 8.5, 5.25)
    assert round(result, 5) == 0.29053


def test_hero_density():
    cube = cube_ft3(11.25, 8.5, 5.25)
    density = density_lb_per_ft3(21.5, cube)
    assert round(density, 1) == 74.0


def test_hero_freight_class():
    cube = cube_ft3(11.25, 8.5, 5.25)
    density = density_lb_per_ft3(21.5, cube)
    assert density_to_nmfc_class(density) == 50


def test_gdsn_density_class_55():
    cube = cube_ft3(13.0, 11.0, 7.0)
    density = density_lb_per_ft3(22.0, cube)
    assert round(density, 2) == 37.98
    assert density_to_nmfc_class(density) == 55


def test_hero_billable_weight():
    dim_wt = dim_weight_lb(6.0, 6.0, 6.0, 139)
    assert round(dim_wt, 3) == round(216.0 / 139.0, 3)
    bill = billable_weight_lb(2.05, dim_wt)
    assert bill == 3


# NMFC boundary tests


def test_nmfc_exact_boundary_50():
    assert density_to_nmfc_class(50.0) == 50


def test_nmfc_just_below_50():
    assert density_to_nmfc_class(49.99) == 55


def test_nmfc_low_density_250():
    assert density_to_nmfc_class(3.5) == 250


def test_nmfc_class_400():
    assert density_to_nmfc_class(1.5) == 400


def test_nmfc_class_500_below_1():
    # Below 1 pcf is class 500 — the stale table wrongly returned 400 here.
    assert density_to_nmfc_class(0.5) == 500
    assert density_to_nmfc_class(0.3) == 500


# --- NMFC cross-implementation agreement (drift guard) ---
#
# The freight-class table is reimplemented in two places that MUST agree:
# this Python reference and dbt/macros/density_to_nmfc_class.sql. A stale copy
# here once passed green while asserting wrong classes; these tests fail the
# moment either copy drifts.

CANONICAL_NMFC_BANDS = [
    (50.0, 50), (35.0, 55), (30.0, 60), (22.5, 65),
    (15.0, 70), (13.5, 77.5), (12.0, 85), (10.5, 92.5),
    (9.0, 100), (8.0, 110), (7.0, 125), (6.0, 150),
    (5.0, 175), (4.0, 200), (3.0, 250), (2.0, 300),
    (1.0, 400),
]
NMFC_FALLBACK_CLASS = 500


def test_python_nmfc_table_is_canonical():
    for threshold, expected_class in CANONICAL_NMFC_BANDS:
        assert density_to_nmfc_class(threshold) == expected_class
    assert density_to_nmfc_class(0.9) == NMFC_FALLBACK_CLASS


def test_dbt_macro_nmfc_table_matches_canonical():
    """Structural check of the dbt macro, not just a scan for the right numbers.

    Matching the threshold->class pairs alone would still pass if a branch
    compared a different expression, if the branches were reordered (a SQL CASE
    returns the FIRST match, so order is load-bearing), or if an extra branch
    were added that does not use '>='. Assert all four properties.
    """
    macro = (REPO_ROOT / "dbt" / "macros" / "density_to_nmfc_class.sql").read_text()
    # Strip Jinja comments so commented-out bands cannot be counted as branches.
    body = re.sub(r"\{#.*?#\}", "", macro, flags=re.S)

    branches = re.findall(r"when\s+(.+?)\s*>=\s*([0-9.]+)\s*then\s*([0-9.]+)", body)
    pairs = [(float(t), float(c)) for _, t, c in branches]
    expected = [(float(t), float(c)) for t, c in CANONICAL_NMFC_BANDS]

    assert pairs == expected, "dbt macro NMFC table drifted from canonical"

    # Every branch must test the SAME expression — otherwise a branch could
    # compare the wrong column while the numbers still line up.
    compared = {expr.strip() for expr, _, _ in branches}
    assert len(compared) == 1, f"macro compares differing expressions: {compared}"

    # No extra branches beyond the ones we validated (e.g. a '<' or 'is null'
    # branch slipped in above them would change results invisibly).
    assert len(re.findall(r"\bwhen\b", body)) == len(expected), "unvalidated extra when-branch"

    # Thresholds must be strictly descending: a CASE returns the first match.
    thresholds = [t for t, _ in pairs]
    assert thresholds == sorted(thresholds, reverse=True), "macro branches are out of order"

    assert re.search(rf"else\s+{NMFC_FALLBACK_CLASS}\b", body), "dbt macro fallback drifted"


# --- Divergence flagging honors the tolerance rule (shipped-data check) ---


def test_published_class_mismatch_count_is_the_true_count():
    """aggregate.skus_with_class_mismatch must count EVERY SKU whose GDSN class
    differs from the measurement-of-record class — including downward shifts,
    whose LTL cost floors at 0. Counting only costly mismatches undercounts and
    contradicts the "SKUs with freight class mismatch" label the UI shows."""
    import csv

    all_skus = json.loads((REPO_ROOT / "frontend" / "src" / "data" / "all_skus.json").read_text())
    mor_class = {s["sku"]: s["freight_class"] for s in all_skus["skus"]}

    expected = 0
    with open(REPO_ROOT / "data" / "generated" / "gdsn_published.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                cube = cube_ft3(
                    float(row["case_length_in"]),
                    float(row["case_width_in"]),
                    float(row["case_height_in"]),
                )
            except (ValueError, KeyError):
                continue  # no published dims -> no comparable GDSN class
            if cube <= 0 or row["sku"] not in mor_class:
                continue
            gdsn = density_to_nmfc_class(density_lb_per_ft3(float(row["case_gross_weight_lb"]), cube))
            if gdsn != mor_class[row["sku"]]:
                expected += 1

    assert all_skus["aggregate"]["skus_with_class_mismatch"] == expected

    # And it must be strictly greater than the costly-only count, which is the
    # bug this guards against (downward shifts cost $0 but are real mismatches).
    costly = sum(
        1 for s in all_skus["skus"]
        if s["cost"]["drivers"].get("ltl_reclass", {}).get("annual_cost", 0) > 0
    )
    assert expected > costly, "fixture no longer exercises the downward-shift case"


def test_hero_flagged_matches_tolerance_rule(config):
    """Every flagged value in the exported hero data must follow the dbt rule:
    weight fields flag above the lb tolerance, '*_in' fields above the inch
    tolerance, everything else stays unflagged."""
    tol_lb = config["tolerances"]["weight_lb"]
    tol_in = config["tolerances"]["dimension_in"]
    hero = json.loads((REPO_ROOT / "frontend" / "src" / "data" / "hero.json").read_text())

    checked = 0
    for system in hero["hero_sku"]["systems"]:
        for d in system["divergences"]:
            field, abs_delta, flagged = d["field"], d["abs_delta"], d["flagged"]
            if abs_delta is None:
                expected = False
            elif "weight" in field:
                expected = abs_delta > tol_lb
            elif field.endswith("_in"):
                expected = abs_delta > tol_in
            else:
                expected = False
            assert flagged == expected, f"{system['system']}.{field}: flagged={flagged}, expected {expected}"
            checked += 1
    assert checked > 0, "no divergences found to check"


# DIM weight per-dimension rounding


def test_dim_weight_rounds_each_dimension_up():
    result = dim_weight_lb(6.1, 6.2, 6.3, 139)
    expected = (7 * 7 * 7) / 139
    assert round(result, 3) == round(expected, 3)


def test_dim_weight_exact_integers_no_rounding():
    result = dim_weight_lb(6.0, 6.0, 6.0, 139)
    expected = (6 * 6 * 6) / 139
    assert round(result, 3) == round(expected, 3)


# Billable weight edge cases


def test_billable_weight_exact_integer():
    assert billable_weight_lb(3.0, 3.0) == 3


def test_billable_weight_dim_greater_than_actual():
    assert billable_weight_lb(1.0, 2.5) == 3

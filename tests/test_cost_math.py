"""Tests for cost parameter loading and physical computation math."""

import math
import pathlib

import pytest
import yaml

CONFIG_PATH = pathlib.Path(__file__).parent.parent / "config" / "cost_params.yml"


@pytest.fixture
def config():
    with open(CONFIG_PATH) as f:
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


def test_config_missing_key_raises_clear_error():
    bad_config = {"ltl": {}}
    with pytest.raises(KeyError):
        _ = bad_config["ltl"]["rate_per_cwt"]


# --- Physical Computation Math (Python equivalents of dbt macros) ---


def cube_ft3(length_in, width_in, height_in):
    return (length_in * width_in * height_in) / 1728.0


def density_lb_per_ft3(weight_lb, cube):
    return weight_lb / cube


def density_to_nmfc_class(density):
    bands = [
        (50.0, 50), (35.0, 55), (22.5, 60), (15.0, 65),
        (13.5, 70), (12.0, 77.5), (10.5, 85), (9.0, 92.5),
        (8.0, 100), (7.0, 110), (6.0, 125), (5.0, 150),
        (4.0, 175), (3.0, 200), (2.0, 250), (1.0, 300),
        (0.5, 400),
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


def test_nmfc_low_density_200():
    assert density_to_nmfc_class(3.5) == 200


def test_nmfc_class_400():
    assert density_to_nmfc_class(0.5) == 400


def test_nmfc_class_500_below_half():
    assert density_to_nmfc_class(0.3) == 500


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

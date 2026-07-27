"""Enforce that business parameters stay in sync across their two sources.

config/cost_params.yml is the documented source of record; dbt reads a
mirrored copy from dbt/dbt_project.yml (vars:). The two files carry a comment
saying they MUST be kept in sync, but nothing enforced it — a rate changed in
one and not the other would silently produce wrong costs. These tests fail if
the mirror drifts.
"""

import pathlib

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).parent.parent


@pytest.fixture
def cost_params():
    with open(REPO_ROOT / "config" / "cost_params.yml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def dbt_vars():
    with open(REPO_ROOT / "dbt" / "dbt_project.yml") as f:
        return yaml.safe_load(f)["vars"]


def _num_dict(d):
    """Normalize a rate table to {float: float} so int/float key or value
    representations compare equal across the two YAML files."""
    return {float(k): float(v) for k, v in d.items()}


def test_ltl_rate_table_matches(cost_params, dbt_vars):
    assert _num_dict(cost_params["ltl"]["rate_per_cwt"]) == _num_dict(dbt_vars["ltl_rate_per_cwt"])


def test_parcel_rate_table_matches(cost_params, dbt_vars):
    assert _num_dict(cost_params["parcel"]["rate_per_lb"]) == _num_dict(dbt_vars["parcel_rate_per_lb"])


def test_parcel_fallback_is_top_weight_tier(cost_params, dbt_vars):
    # dbt's parcel_rate_fallback has no standalone config key; it must equal
    # the heaviest parcel rate tier in cost_params.
    top_tier = max(cost_params["parcel"]["rate_per_lb"])
    assert dbt_vars["parcel_rate_fallback"] == cost_params["parcel"]["rate_per_lb"][top_tier]


def test_scalar_parameters_match(cost_params, dbt_vars):
    # (cost_params path, dbt var name)
    mirrored = [
        (cost_params["parcel"]["dim_divisor"], dbt_vars["dim_divisor"]),
        (cost_params["parcel"]["dtc_parcel_box_in"], dbt_vars["dtc_parcel_box_in"]),
        (cost_params["ltl"]["annual_pallet_shipments_per_sku"], dbt_vars["annual_pallet_shipments_per_sku"]),
        (cost_params["parcel"]["annual_dtc_orders_per_sku"], dbt_vars["annual_dtc_orders_per_sku"]),
        (cost_params["chargebacks"]["per_event_cost"], dbt_vars["chargeback_per_event_cost"]),
        (cost_params["chargebacks"]["annual_events_per_sku"], dbt_vars["annual_chargeback_events_per_sku"]),
        (cost_params["chargebacks"]["affected_sku_pct"], dbt_vars["chargeback_affected_sku_pct"]),
        (cost_params["tolerances"]["weight_lb"], dbt_vars["divergence_tolerance_lb"]),
        (cost_params["tolerances"]["dimension_in"], dbt_vars["divergence_tolerance_in"]),
    ]
    for config_value, dbt_value in mirrored:
        assert config_value == dbt_value


def test_packaging_offset_matches_hero_parcel_gross(cost_params, dbt_vars):
    # packaging_offset_lb lives only in dbt vars; it must reconcile with the
    # hero reference values (unit net + offset = DTC parcel gross).
    hero = cost_params["hero_sku"]
    expected_offset = round(hero["dtc_parcel_gross_lb"] - hero["unit_net_weight_lb"], 2)
    assert dbt_vars["packaging_offset_lb"] == expected_offset

"""Every published figure in README.md must match the shipped data.

DECISIONS.md forbids hard-coded numbers in published prose precisely because
they drift: the README quoted a $654.28 hero total and a "$0.39/case x 52
pallets/yr" LTL line long after the pipeline stopped producing them. Nothing
read the README, so nothing caught it.

These tests parse the figures back out of the prose and reconcile them against
frontend/src/data/*.json. Editing a number in the README without a matching
pipeline change now fails the suite, and vice versa.
"""

import json
import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).parent.parent
README = REPO_ROOT / "README.md"
DATA_DIR = REPO_ROOT / "frontend" / "src" / "data"


@pytest.fixture(scope="module")
def readme():
    return README.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def hero():
    return json.loads((DATA_DIR / "hero.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def all_skus():
    return json.loads((DATA_DIR / "all_skus.json").read_text(encoding="utf-8"))


def _money(value):
    """Render a number the way the README writes money: $1,234.56 / $394."""
    whole = f"${value:,.0f}"
    return whole if float(value).is_integer() else f"${value:,.2f}"


def _count(value):
    return f"{value:,.0f}" if float(value).is_integer() else f"{value:,}"


@pytest.mark.parametrize("driver_key", ["ltl_reclass", "parcel_reweigh", "compliance_cb"])
def test_driver_annual_cost_appears_in_readme(readme, hero, driver_key):
    driver = hero["cost"][driver_key]
    assert f"{_money(driver['annual_cost'])}/yr" in readme, (
        f"README does not quote {driver_key} annual cost "
        f"{_money(driver['annual_cost'])}/yr"
    )


@pytest.mark.parametrize("driver_key", ["ltl_reclass", "parcel_reweigh", "compliance_cb"])
def test_driver_unit_math_appears_in_readme(readme, hero, driver_key):
    """The 'per-unit x volume' string must use the shipped volume.

    This is the assertion that would have caught the LTL unit mismatch: the
    README said '52 pallets/yr' while the model multiplied by a case count.
    """
    driver = hero["cost"][driver_key]
    per_unit = _money(driver["per_unit_delta"])
    volume = _count(driver["annual_units"])
    pattern = re.escape(per_unit) + r"/\w+ × " + re.escape(volume) + r" "
    assert re.search(pattern, readme), (
        f"README does not show {driver_key} as {per_unit}/unit × {volume} <volume>/yr"
    )


def test_hero_total_matches_sum_of_drivers(readme, hero):
    total = sum(d["annual_cost"] for d in hero["cost"].values())
    assert f"Total annual cost for one SKU: {_money(total)}." in readme


def test_portfolio_total_matches_aggregate(readme, all_skus):
    total = all_skus["aggregate"]["total_annual_cost"]
    assert f"Across the 50-SKU portfolio: {_money(total)}." in readme


def test_readme_does_not_price_ltl_on_pallets(readme):
    """Guards the specific regression, in prose as well as in the model."""
    assert not re.search(r"×\s*[\d,]+\s*pallets?/yr", readme), (
        "README still prices a driver against a pallet count; LTL bills per "
        "hundredweight, so the volume must be annual cases"
    )

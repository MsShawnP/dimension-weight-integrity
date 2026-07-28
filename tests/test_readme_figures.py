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


class TestHeroRangeDisclosure:
    """The hero's range disclosure must match the measured sensitivity band.

    The headline portfolio total is a point estimate resting on an even
    revenue split -- the model's highest-leverage assumption, and an
    allocation rather than a scalar, so it can reorder which SKUs dominate
    rather than just rescale them. The measured band is ~0.31x-2.71x. Stating
    it is accuracy, not hedging; leaving it unstated presents a stronger claim
    than the model supports.

    These figures live in cost_params.yml under
    ltl.revenue_split_sensitivity_portfolio so the copy is testable rather
    than free prose. DECISIONS.md forbids hard-coded numbers in published
    copy; where the pipeline JSON does not carry the value, the rule's escape
    hatch is a test asserting the static copy still matches the data.
    """

    APP = REPO_ROOT / "frontend" / "src" / "App.tsx"
    CONFIG = REPO_ROOT / "config" / "cost_params.yml"

    @staticmethod
    def _compact(value):
        """Mirror formatCurrency's compact notation (3 significant digits)."""
        thousands = value / 1000
        rounded = float(f"{thousands:.3g}")
        text = f"{rounded:g}"
        return f"${text}K"

    @pytest.fixture(scope="class")
    def band(self):
        import yaml
        with open(self.CONFIG, encoding="utf-8") as f:
            return yaml.safe_load(f)["ltl"]["revenue_split_sensitivity_portfolio"]

    def test_even_case_matches_the_shipped_aggregate(self, band, all_skus):
        """The band's centre must be the number the pipeline actually ships."""
        shipped = all_skus["aggregate"]["total_annual_cost"]
        assert abs(band["even"] - shipped) < 1.0, (
            f"sensitivity band centre {band['even']} does not match the shipped "
            f"aggregate {shipped}"
        )

    @pytest.mark.parametrize("key", ["volume_on_divergent", "volume_on_clean"])
    def test_hero_copy_quotes_the_measured_bound(self, band, key):
        copy = self.APP.read_text(encoding="utf-8")
        expected = self._compact(band[key])
        assert expected in copy, (
            f"hero range disclosure does not quote {key} as {expected}; "
            f"copy and config/cost_params.yml have drifted"
        )

    def test_band_is_wide_enough_to_be_worth_stating(self, band):
        """Guards the reason the disclosure exists, not just its wording."""
        spread = band["volume_on_divergent"] / band["volume_on_clean"]
        assert spread > 2.0, (
            f"band has narrowed to {spread:.2f}x -- if the revenue split stops "
            "being load-bearing, revisit whether the disclosure is still needed"
        )

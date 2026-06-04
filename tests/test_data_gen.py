"""Tests for synthetic data generation."""

import csv
import pathlib
import tempfile

import pytest

from data_gen.generate_dimension_mess import (
    apply_hero_overrides,
    fill_missing_fields,
    generate_all,
    generate_erp,
    generate_gdsn,
    generate_shopify,
    generate_wms,
    HERO_MOR,
)
from data_gen.shared import DATA_DIR, HERO_SKU_ID, SEED

import random


def _make_products(n=50):
    """Create a synthetic product_master with n SKUs for testing."""
    rng = random.Random(999)
    products = []
    for i in range(n):
        sku = f"CHP-{i:04d}"
        has_dims = rng.random() > 0.36
        has_case_wt = rng.random() > 0.36
        unit_wt = round(rng.uniform(0.5, 2.0), 2)
        pack_qty = rng.choice([6, 12, 24])

        p = {
            "sku": sku,
            "product_name": f"Test Product {i}",
            "product_line": "Artisan Sauces",
            "case_pack_qty": pack_qty,
            "unit_weight_lbs": unit_wt,
            "case_weight_lbs": round(unit_wt * pack_qty * 1.15, 2) if has_case_wt else None,
            "case_length_in": round(rng.uniform(10, 16), 2) if has_dims else None,
            "case_width_in": round(rng.uniform(8, 12), 2) if has_dims else None,
            "case_height_in": round(rng.uniform(5, 11), 2) if has_dims else None,
        }
        products.append(p)

    hero_idx = next(i for i, p in enumerate(products) if p["sku"] == HERO_SKU_ID)
    products[hero_idx]["product_name"] = "Calabrian Chili Marinara"
    return products


@pytest.fixture
def products():
    return _make_products(50)


@pytest.fixture(autouse=True)
def use_temp_data_dir(monkeypatch, tmp_path):
    """Redirect CSV output to temp directory for test isolation."""
    import data_gen.generate_dimension_mess as gen_mod
    monkeypatch.setattr(gen_mod, "DATA_DIR", tmp_path)
    return tmp_path


def test_generates_four_csv_files(products, use_temp_data_dir):
    result = generate_all(products)
    assert set(result.keys()) == {"wms", "erp", "gdsn", "shopify"}
    for system in ("wms_dimensions", "netsuite_items", "gdsn_published", "shopify_products"):
        assert (use_temp_data_dir / f"{system}.csv").exists()


def test_each_system_has_50_rows(products):
    result = generate_all(products)
    for system, rows in result.items():
        assert len(rows) == 50, f"{system} has {len(rows)} rows, expected 50"


def test_deterministic_output(products, use_temp_data_dir):
    result1 = generate_all(products)
    result2 = generate_all(products)
    for system in result1:
        for r1, r2 in zip(result1[system], result2[system]):
            assert r1 == r2, f"{system} output differs between runs"


def test_hero_wms_matches_mor(products):
    result = generate_all(products)
    hero_wms = next(r for r in result["wms"] if r["sku"] == HERO_SKU_ID)
    assert hero_wms["case_gross_weight_lb"] == HERO_MOR["case_gross_weight_lb"]
    assert hero_wms["case_length_in"] == HERO_MOR["case_length_in"]
    assert hero_wms["case_width_in"] == HERO_MOR["case_width_in"]
    assert hero_wms["case_height_in"] == HERO_MOR["case_height_in"]


def test_hero_erp_biased_low(products):
    result = generate_all(products)
    hero_erp = next(r for r in result["erp"] if r["sku"] == HERO_SKU_ID)
    assert hero_erp["case_gross_weight_lb"] == 20.00
    assert hero_erp["unit_weight_lb"] == 1.00


def test_hero_gdsn_inflated(products):
    result = generate_all(products)
    hero_gdsn = next(r for r in result["gdsn"] if r["sku"] == HERO_SKU_ID)
    assert hero_gdsn["case_gross_weight_lb"] == 22.00
    assert hero_gdsn["case_length_in"] == 13.0
    assert hero_gdsn["case_width_in"] == 11.0
    assert hero_gdsn["case_height_in"] == 7.0


def test_hero_shopify_net_weight(products):
    result = generate_all(products)
    hero_shopify = next(r for r in result["shopify"] if r["sku"] == HERO_SKU_ID)
    assert hero_shopify["ship_weight_lb"] == 1.00
    assert hero_shopify["case_length_in"] == ""
    assert hero_shopify["case_width_in"] == ""


def test_erp_weights_systematically_lower(products):
    rng_fill = random.Random(SEED)
    products = fill_missing_fields(products, rng_fill)
    products = apply_hero_overrides(products)
    rng = random.Random(SEED)
    wms = generate_wms(products, rng)
    erp = generate_erp(products, rng)

    non_hero_erp = [r for r in erp if r["sku"] != HERO_SKU_ID]
    non_hero_wms = {r["sku"]: r for r in wms if r["sku"] != HERO_SKU_ID}

    confused = 0
    lower = 0
    for r in non_hero_erp:
        wms_r = non_hero_wms[r["sku"]]
        if r["case_gross_weight_lb"] == r["unit_weight_lb"]:
            confused += 1
        elif r["case_gross_weight_lb"] < wms_r["case_gross_weight_lb"]:
            lower += 1

    assert confused + lower == len(non_hero_erp)


def test_about_20_pct_unit_case_confusion(products):
    rng_fill = random.Random(SEED)
    products = fill_missing_fields(products, rng_fill)
    products = apply_hero_overrides(products)
    rng = random.Random(SEED)
    _ = generate_wms(products, rng)
    erp = generate_erp(products, rng)

    non_hero = [r for r in erp if r["sku"] != HERO_SKU_ID]
    confused = sum(1 for r in non_hero if r["case_gross_weight_lb"] == r["unit_weight_lb"])

    assert 5 <= confused <= 15, f"Expected ~10 confused, got {confused}"


def test_about_80_pct_shopify_null_dims(products):
    rng_fill = random.Random(SEED)
    products = fill_missing_fields(products, rng_fill)
    products = apply_hero_overrides(products)
    rng = random.Random(SEED)
    _ = generate_wms(products, rng)
    _ = generate_erp(products, rng)
    _ = generate_gdsn(products, rng)
    shopify = generate_shopify(products, rng)

    non_hero = [r for r in shopify if r["sku"] != HERO_SKU_ID]
    null_dims = sum(1 for r in non_hero if r["case_length_in"] == "")

    assert 30 <= null_dims <= 45, f"Expected ~39 null-dim rows, got {null_dims}"


def test_fill_missing_fields_handles_nulls():
    products = [{
        "sku": "CHP-TEST",
        "product_name": "Test",
        "product_line": "Test",
        "case_pack_qty": 12,
        "unit_weight_lbs": 1.0,
        "case_weight_lbs": None,
        "case_length_in": None,
        "case_width_in": None,
        "case_height_in": None,
    }]
    rng = random.Random(42)
    filled = fill_missing_fields(products, rng)
    assert filled[0]["case_weight_lbs"] is not None
    assert filled[0]["case_weight_lbs"] > 0
    assert filled[0]["case_length_in"] is not None
    assert filled[0]["case_length_in"] > 0

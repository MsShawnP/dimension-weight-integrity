"""Dagster Definitions entry point for the dimension & weight integrity pipeline."""

from dagster import Definitions

from assets import (
    generate_source_extracts,
    load_raw,
    dbt_build,
    export_frontend_json,
)

defs = Definitions(
    assets=[generate_source_extracts, load_raw, dbt_build, export_frontend_json],
)

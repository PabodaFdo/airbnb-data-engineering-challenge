"""
Automated data-quality validation for the Amsterdam Airbnb project.

This module validates all seven raw source files and writes one consolidated
report:

    outputs/data_quality/validation_results.csv

Design goals:
- Reusable and repeatable.
- Safe for an 8 GB RAM laptop.
- Pandas for small/medium datasets.
- DuckDB for large detailed calendar and review datasets.
- Raw source files are never modified.
- Validation findings are classified as PASS, WARNING, or FAIL.
"""

from __future__ import annotations

import gc
import json
import logging
from pathlib import Path
from typing import Any, Iterable

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "amsterdam"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "data_quality"
DUCKDB_TEMP_DIR = OUTPUT_DIR / "duckdb_temp"
VALIDATION_RESULTS_PATH = OUTPUT_DIR / "validation_results.csv"

NEIGHBOURHOODS_PATH = RAW_DIR / "neighbourhoods.csv"
SUMMARY_LISTINGS_PATH = RAW_DIR / "listings.csv"
SUMMARY_REVIEWS_PATH = RAW_DIR / "reviews.csv"
DETAILED_LISTINGS_PATH = RAW_DIR / "listings.csv.gz"
NEIGHBOURHOODS_GEOJSON_PATH = RAW_DIR / "neighbourhoods.geojson"
CALENDAR_PATH = RAW_DIR / "calendar.csv.gz"
DETAILED_REVIEWS_PATH = RAW_DIR / "reviews.csv.gz"

EXPECTED_ROOM_TYPES = {
    "Entire home/apt",
    "Private room",
    "Shared room",
    "Hotel room",
}

VALID_GEOJSON_GEOMETRY_TYPES = {"Polygon", "MultiPolygon"}

REQUIRED_COLUMNS = {
    "neighbourhoods.csv": {"neighbourhood"},
    "listings.csv": {
        "id",
        "host_id",
        "neighbourhood",
        "latitude",
        "longitude",
        "room_type",
        "price",
        "minimum_nights",
        "availability_365",
    },
    "reviews.csv": {"listing_id", "date"},
    "listings.csv.gz": {
        "id",
        "host_id",
        "neighbourhood_cleansed",
        "latitude",
        "longitude",
        "room_type",
        "price",
        "minimum_nights",
        "availability_365",
    },
    "calendar.csv.gz": {
        "listing_id",
        "date",
        "available",
        "minimum_nights",
        "maximum_nights",
    },
    "reviews.csv.gz": {
        "listing_id",
        "id",
        "date",
        "reviewer_id",
        "reviewer_name",
        "comments",
    },
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
LOGGER = logging.getLogger(__name__)

VALIDATION_RESULTS: list[dict[str, Any]] = []


def add_result(
    *,
    dataset_name: str,
    rule_id: str,
    rule_description: str,
    checked_column: str,
    invalid_count: int,
    total_rows: int,
    severity: str,
    notes: str = "",
) -> None:
    """Add one validation result to the in-memory report."""
    invalid_count = int(invalid_count)
    total_rows = int(total_rows)
    invalid_percentage = (
        round((invalid_count / total_rows) * 100, 4)
        if total_rows > 0
        else 0.0
    )

    severity = severity.upper()
    if invalid_count == 0:
        status = "PASS"
    elif severity == "ERROR":
        status = "FAIL"
    else:
        status = "WARNING"

    VALIDATION_RESULTS.append(
        {
            "dataset_name": dataset_name,
            "rule_id": rule_id,
            "rule_description": rule_description,
            "checked_column": checked_column,
            "invalid_count": invalid_count,
            "total_rows": total_rows,
            "invalid_percentage": invalid_percentage,
            "status": status,
            "severity": severity,
            "notes": notes,
        }
    )


def require_file(path: Path) -> None:
    """Raise a clear error when a required source file is missing."""
    if not path.exists():
        raise FileNotFoundError(f"Required source file not found: {path}")


def validate_required_columns(
    *,
    dataset_name: str,
    actual_columns: Iterable[str],
    required_columns: set[str],
    total_rows: int,
    rule_prefix: str,
) -> set[str]:
    """Validate required-column presence and return missing columns."""
    actual = set(actual_columns)
    missing = required_columns - actual

    for index, column_name in enumerate(sorted(required_columns), start=1):
        add_result(
            dataset_name=dataset_name,
            rule_id=f"{rule_prefix}_{index:03d}",
            rule_description=f"Required column '{column_name}' must exist",
            checked_column=column_name,
            invalid_count=total_rows if column_name not in actual else 0,
            total_rows=total_rows,
            severity="ERROR",
            notes=(
                "Critical schema validation. Missing required columns can "
                "prevent downstream processing."
            ),
        )

    return missing


def parse_price_series(series: pd.Series) -> pd.Series:
    """Convert values such as '$1,250.00' to numeric without changing raw data."""
    return pd.to_numeric(
        series.astype("string")
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip(),
        errors="coerce",
    )


def count_unparseable_dates(series: pd.Series) -> int:
    """Count non-null date values that cannot be parsed."""
    non_null = series.notna()
    parsed = pd.to_datetime(series, errors="coerce")
    return int((non_null & parsed.isna()).sum())


def quote_identifier(identifier: str) -> str:
    """Safely quote a DuckDB SQL identifier."""
    return '"' + identifier.replace('"', '""') + '"'


def escape_sql_path(path: Path) -> str:
    """Escape a path for use inside a DuckDB SQL string literal."""
    return path.resolve().as_posix().replace("'", "''")


def duckdb_relation(path: Path) -> str:
    """Return a DuckDB relation expression for a CSV or CSV.GZ file."""
    escaped_path = escape_sql_path(path)
    return (
        "read_csv_auto("
        f"'{escaped_path}', "
        "header=true, "
        "sample_size=200000"
        ")"
    )


def create_duckdb_connection() -> duckdb.DuckDBPyConnection:
    """Create a memory-aware DuckDB connection for an 8 GB laptop."""
    DUCKDB_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(database=":memory:")
    con.execute("SET memory_limit = '3GB'")
    con.execute("SET preserve_insertion_order = false")
    con.execute(
        f"SET temp_directory = '{escape_sql_path(DUCKDB_TEMP_DIR)}'"
    )
    return con


def duckdb_schema(
    con: duckdb.DuckDBPyConnection,
    relation: str,
) -> dict[str, str]:
    """Return {column_name: data_type} for a DuckDB relation."""
    rows = con.execute(f"DESCRIBE SELECT * FROM {relation}").fetchall()
    return {row[0]: row[1] for row in rows}


def load_reference_sets() -> dict[str, set[Any]]:
    """Load compact listing-ID and neighbourhood reference sets."""
    LOGGER.info("Loading compact reference sets...")

    summary_listing_ids = set(
        pd.read_csv(SUMMARY_LISTINGS_PATH, usecols=["id"])["id"]
        .dropna()
        .tolist()
    )

    neighbourhood_names = set(
        pd.read_csv(
            NEIGHBOURHOODS_PATH,
            usecols=["neighbourhood"],
        )["neighbourhood"]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )

    return {
        "summary_listing_ids": summary_listing_ids,
        "neighbourhood_names": neighbourhood_names,
    }


def validate_neighbourhoods_csv() -> None:
    """Validate neighbourhoods.csv."""
    dataset_name = "neighbourhoods.csv"
    LOGGER.info("Validating %s...", dataset_name)

    df = pd.read_csv(NEIGHBOURHOODS_PATH)
    total_rows = len(df)

    missing_required = validate_required_columns(
        dataset_name=dataset_name,
        actual_columns=df.columns,
        required_columns=REQUIRED_COLUMNS[dataset_name],
        total_rows=total_rows,
        rule_prefix="N_SCHEMA",
    )

    if "neighbourhood" not in missing_required:
        add_result(
            dataset_name=dataset_name,
            rule_id="N_001",
            rule_description="Neighbourhood name must not be null",
            checked_column="neighbourhood",
            invalid_count=int(df["neighbourhood"].isna().sum()),
            total_rows=total_rows,
            severity="ERROR",
        )

        add_result(
            dataset_name=dataset_name,
            rule_id="N_002",
            rule_description="Neighbourhood name must be unique",
            checked_column="neighbourhood",
            invalid_count=int(df["neighbourhood"].duplicated(keep=False).sum()),
            total_rows=total_rows,
            severity="ERROR",
            notes="Counts all rows participating in duplicate name groups.",
        )

    if "neighbourhood_group" in df.columns:
        add_result(
            dataset_name=dataset_name,
            rule_id="N_003",
            rule_description="Report missing neighbourhood_group values",
            checked_column="neighbourhood_group",
            invalid_count=int(df["neighbourhood_group"].isna().sum()),
            total_rows=total_rows,
            severity="INFO",
            notes=(
                "Known source limitation. The field is fully empty for this "
                "Amsterdam dataset and is not required as a primary key."
            ),
        )

    del df
    gc.collect()


def validate_summary_listings(reference_sets: dict[str, set[Any]]) -> None:
    """Validate the canonical summary listings dataset."""
    dataset_name = "listings.csv"
    LOGGER.info("Validating %s...", dataset_name)

    df = pd.read_csv(SUMMARY_LISTINGS_PATH, low_memory=False)
    total_rows = len(df)

    missing_required = validate_required_columns(
        dataset_name=dataset_name,
        actual_columns=df.columns,
        required_columns=REQUIRED_COLUMNS[dataset_name],
        total_rows=total_rows,
        rule_prefix="SL_SCHEMA",
    )

    if "id" not in missing_required:
        add_result(
            dataset_name=dataset_name,
            rule_id="SL_001",
            rule_description="Listing ID must not be null",
            checked_column="id",
            invalid_count=int(df["id"].isna().sum()),
            total_rows=total_rows,
            severity="ERROR",
        )
        add_result(
            dataset_name=dataset_name,
            rule_id="SL_002",
            rule_description="Listing ID must be unique",
            checked_column="id",
            invalid_count=int(df["id"].duplicated(keep=False).sum()),
            total_rows=total_rows,
            severity="ERROR",
            notes="Counts all rows participating in duplicate ID groups.",
        )

    if "host_id" not in missing_required:
        add_result(
            dataset_name=dataset_name,
            rule_id="SL_003",
            rule_description="Report missing host IDs",
            checked_column="host_id",
            invalid_count=int(df["host_id"].isna().sum()),
            total_rows=total_rows,
            severity="WARNING",
            notes=(
                "Missing host IDs reduce host-level enrichment coverage but do "
                "not invalidate the listing itself."
            ),
        )

    if "latitude" not in missing_required:
        latitude = pd.to_numeric(df["latitude"], errors="coerce")
        invalid = (
            df["latitude"].notna()
            & (latitude.isna() | (latitude < -90) | (latitude > 90))
        ).sum()
        add_result(
            dataset_name=dataset_name,
            rule_id="SL_004",
            rule_description="Latitude must be between -90 and 90",
            checked_column="latitude",
            invalid_count=int(invalid),
            total_rows=total_rows,
            severity="ERROR",
        )

    if "longitude" not in missing_required:
        longitude = pd.to_numeric(df["longitude"], errors="coerce")
        invalid = (
            df["longitude"].notna()
            & (longitude.isna() | (longitude < -180) | (longitude > 180))
        ).sum()
        add_result(
            dataset_name=dataset_name,
            rule_id="SL_005",
            rule_description="Longitude must be between -180 and 180",
            checked_column="longitude",
            invalid_count=int(invalid),
            total_rows=total_rows,
            severity="ERROR",
        )

    if "availability_365" not in missing_required:
        values = pd.to_numeric(df["availability_365"], errors="coerce")
        invalid = (
            df["availability_365"].notna()
            & (values.isna() | (values < 0) | (values > 365))
        ).sum()
        add_result(
            dataset_name=dataset_name,
            rule_id="SL_006",
            rule_description="availability_365 must be between 0 and 365",
            checked_column="availability_365",
            invalid_count=int(invalid),
            total_rows=total_rows,
            severity="ERROR",
        )

    if "minimum_nights" not in missing_required:
        values = pd.to_numeric(df["minimum_nights"], errors="coerce")
        invalid = (
            df["minimum_nights"].notna()
            & (values.isna() | (values < 0))
        ).sum()
        add_result(
            dataset_name=dataset_name,
            rule_id="SL_007",
            rule_description="minimum_nights must not be negative",
            checked_column="minimum_nights",
            invalid_count=int(invalid),
            total_rows=total_rows,
            severity="ERROR",
        )

    if "price" not in missing_required:
        parsed_price = parse_price_series(df["price"])
        negative_prices = (
            df["price"].notna() & parsed_price.notna() & (parsed_price < 0)
        ).sum()
        unparseable_prices = (
            df["price"].notna() & parsed_price.isna()
        ).sum()

        add_result(
            dataset_name=dataset_name,
            rule_id="SL_008",
            rule_description="Price must not be negative after parsing",
            checked_column="price",
            invalid_count=int(negative_prices),
            total_rows=total_rows,
            severity="ERROR",
        )
        add_result(
            dataset_name=dataset_name,
            rule_id="SL_009",
            rule_description="Non-null price values must be parseable",
            checked_column="price",
            invalid_count=int(unparseable_prices),
            total_rows=total_rows,
            severity="ERROR",
        )
        add_result(
            dataset_name=dataset_name,
            rule_id="SL_010",
            rule_description="Report missing price values",
            checked_column="price",
            invalid_count=int(df["price"].isna().sum()),
            total_rows=total_rows,
            severity="WARNING",
            notes=(
                "Missing price does not mean zero price. Preserve nulls unless "
                "a context-specific cleaning decision is justified."
            ),
        )

    if "room_type" not in missing_required:
        room_types = df["room_type"].dropna().astype(str).str.strip()
        unexpected = (~room_types.isin(EXPECTED_ROOM_TYPES)).sum()
        add_result(
            dataset_name=dataset_name,
            rule_id="SL_011",
            rule_description="Room type must be an expected category",
            checked_column="room_type",
            invalid_count=int(unexpected),
            total_rows=total_rows,
            severity="WARNING",
            notes=(
                "Unexpected categories should be reviewed before normalization; "
                "new source values are not automatically errors."
            ),
        )

    if "neighbourhood" not in missing_required:
        values = df["neighbourhood"].dropna().astype(str).str.strip()
        unknown = (~values.isin(reference_sets["neighbourhood_names"])).sum()
        add_result(
            dataset_name=dataset_name,
            rule_id="SL_012",
            rule_description=(
                "Listing neighbourhood must exist in neighbourhoods.csv"
            ),
            checked_column="neighbourhood",
            invalid_count=int(unknown),
            total_rows=total_rows,
            severity="ERROR",
        )

    del df
    gc.collect()


def validate_summary_reviews(reference_sets: dict[str, set[Any]]) -> None:
    """Validate the two-column summary review dataset."""
    dataset_name = "reviews.csv"
    LOGGER.info("Validating %s...", dataset_name)

    df = pd.read_csv(SUMMARY_REVIEWS_PATH, low_memory=False)
    total_rows = len(df)

    missing_required = validate_required_columns(
        dataset_name=dataset_name,
        actual_columns=df.columns,
        required_columns=REQUIRED_COLUMNS[dataset_name],
        total_rows=total_rows,
        rule_prefix="SR_SCHEMA",
    )

    if "listing_id" not in missing_required:
        add_result(
            dataset_name=dataset_name,
            rule_id="SR_001",
            rule_description="Review listing_id must not be null",
            checked_column="listing_id",
            invalid_count=int(df["listing_id"].isna().sum()),
            total_rows=total_rows,
            severity="ERROR",
        )
        orphan_rows = (
            ~df["listing_id"].dropna().isin(reference_sets["summary_listing_ids"])
        ).sum()
        add_result(
            dataset_name=dataset_name,
            rule_id="SR_002",
            rule_description=(
                "Review listing_id should exist in canonical listings.csv"
            ),
            checked_column="listing_id",
            invalid_count=int(orphan_rows),
            total_rows=total_rows,
            severity="ERROR",
        )

    if "date" not in missing_required:
        add_result(
            dataset_name=dataset_name,
            rule_id="SR_003",
            rule_description="Review date must not be null",
            checked_column="date",
            invalid_count=int(df["date"].isna().sum()),
            total_rows=total_rows,
            severity="ERROR",
        )
        add_result(
            dataset_name=dataset_name,
            rule_id="SR_004",
            rule_description="Non-null review dates must be parseable",
            checked_column="date",
            invalid_count=count_unparseable_dates(df["date"]),
            total_rows=total_rows,
            severity="ERROR",
        )

    add_result(
        dataset_name=dataset_name,
        rule_id="SR_005",
        rule_description="Report exact duplicate summary-review rows",
        checked_column="listing_id,date",
        invalid_count=int(df.duplicated().sum()),
        total_rows=total_rows,
        severity="WARNING",
        notes=(
            "Repeated (listing_id, date) rows are expected because multiple "
            "individual reviews can occur for the same listing on the same "
            "date. Do not blindly delete them."
        ),
    )

    del df
    gc.collect()


def validate_detailed_listings(reference_sets: dict[str, set[Any]]) -> None:
    """Validate listings.csv.gz."""
    dataset_name = "listings.csv.gz"
    LOGGER.info("Validating %s...", dataset_name)

    df = pd.read_csv(DETAILED_LISTINGS_PATH, low_memory=False)
    total_rows = len(df)

    missing_required = validate_required_columns(
        dataset_name=dataset_name,
        actual_columns=df.columns,
        required_columns=REQUIRED_COLUMNS[dataset_name],
        total_rows=total_rows,
        rule_prefix="DL_SCHEMA",
    )

    if "id" not in missing_required:
        add_result(
            dataset_name=dataset_name,
            rule_id="DL_001",
            rule_description="Detailed listing ID must not be null",
            checked_column="id",
            invalid_count=int(df["id"].isna().sum()),
            total_rows=total_rows,
            severity="ERROR",
        )
        add_result(
            dataset_name=dataset_name,
            rule_id="DL_002",
            rule_description="Detailed listing ID must be unique",
            checked_column="id",
            invalid_count=int(df["id"].duplicated(keep=False).sum()),
            total_rows=total_rows,
            severity="ERROR",
        )

        detailed_ids = set(df["id"].dropna().tolist())
        detailed_not_in_summary = (
            detailed_ids - reference_sets["summary_listing_ids"]
        )
        add_result(
            dataset_name=dataset_name,
            rule_id="DL_003",
            rule_description=(
                "Detailed listing IDs should exist in canonical listings.csv"
            ),
            checked_column="id",
            invalid_count=len(detailed_not_in_summary),
            total_rows=total_rows,
            severity="ERROR",
        )

        summary_missing_from_detailed = (
            reference_sets["summary_listing_ids"] - detailed_ids
        )
        add_result(
            dataset_name=dataset_name,
            rule_id="DL_004",
            rule_description=(
                "Report canonical summary listings absent from detailed listings"
            ),
            checked_column="id",
            invalid_count=len(summary_missing_from_detailed),
            total_rows=len(reference_sets["summary_listing_ids"]),
            severity="WARNING",
            notes=(
                "Known source-coverage difference. Do not silently discard "
                "summary-only listings during enrichment."
            ),
        )

    if "host_id" not in missing_required:
        add_result(
            dataset_name=dataset_name,
            rule_id="DL_005",
            rule_description="Report missing host IDs",
            checked_column="host_id",
            invalid_count=int(df["host_id"].isna().sum()),
            total_rows=total_rows,
            severity="WARNING",
        )

    if "latitude" not in missing_required:
        values = pd.to_numeric(df["latitude"], errors="coerce")
        invalid = (
            df["latitude"].notna()
            & (values.isna() | (values < -90) | (values > 90))
        ).sum()
        add_result(
            dataset_name=dataset_name,
            rule_id="DL_006",
            rule_description="Latitude must be between -90 and 90",
            checked_column="latitude",
            invalid_count=int(invalid),
            total_rows=total_rows,
            severity="ERROR",
        )

    if "longitude" not in missing_required:
        values = pd.to_numeric(df["longitude"], errors="coerce")
        invalid = (
            df["longitude"].notna()
            & (values.isna() | (values < -180) | (values > 180))
        ).sum()
        add_result(
            dataset_name=dataset_name,
            rule_id="DL_007",
            rule_description="Longitude must be between -180 and 180",
            checked_column="longitude",
            invalid_count=int(invalid),
            total_rows=total_rows,
            severity="ERROR",
        )

    if "price" not in missing_required:
        parsed_price = parse_price_series(df["price"])
        negative_prices = (
            df["price"].notna() & parsed_price.notna() & (parsed_price < 0)
        ).sum()
        unparseable_prices = (
            df["price"].notna() & parsed_price.isna()
        ).sum()
        add_result(
            dataset_name=dataset_name,
            rule_id="DL_008",
            rule_description="Price must not be negative after parsing",
            checked_column="price",
            invalid_count=int(negative_prices),
            total_rows=total_rows,
            severity="ERROR",
        )
        add_result(
            dataset_name=dataset_name,
            rule_id="DL_009",
            rule_description="Non-null price values must be parseable",
            checked_column="price",
            invalid_count=int(unparseable_prices),
            total_rows=total_rows,
            severity="ERROR",
        )
        add_result(
            dataset_name=dataset_name,
            rule_id="DL_010",
            rule_description="Report missing price values",
            checked_column="price",
            invalid_count=int(df["price"].isna().sum()),
            total_rows=total_rows,
            severity="WARNING",
            notes="Missing price values must not be interpreted as zero.",
        )

    if "minimum_nights" not in missing_required:
        values = pd.to_numeric(df["minimum_nights"], errors="coerce")
        invalid = (
            df["minimum_nights"].notna()
            & (values.isna() | (values < 0))
        ).sum()
        add_result(
            dataset_name=dataset_name,
            rule_id="DL_011",
            rule_description="minimum_nights must not be negative",
            checked_column="minimum_nights",
            invalid_count=int(invalid),
            total_rows=total_rows,
            severity="ERROR",
        )

    if "availability_365" not in missing_required:
        values = pd.to_numeric(df["availability_365"], errors="coerce")
        invalid = (
            df["availability_365"].notna()
            & (values.isna() | (values < 0) | (values > 365))
        ).sum()
        add_result(
            dataset_name=dataset_name,
            rule_id="DL_012",
            rule_description="availability_365 must be between 0 and 365",
            checked_column="availability_365",
            invalid_count=int(invalid),
            total_rows=total_rows,
            severity="ERROR",
        )

    if "room_type" not in missing_required:
        room_types = df["room_type"].dropna().astype(str).str.strip()
        unexpected = (~room_types.isin(EXPECTED_ROOM_TYPES)).sum()
        add_result(
            dataset_name=dataset_name,
            rule_id="DL_013",
            rule_description="Room type must be an expected category",
            checked_column="room_type",
            invalid_count=int(unexpected),
            total_rows=total_rows,
            severity="WARNING",
        )

    if "neighbourhood_cleansed" not in missing_required:
        values = (
            df["neighbourhood_cleansed"].dropna().astype(str).str.strip()
        )
        unknown = (~values.isin(reference_sets["neighbourhood_names"])).sum()
        add_result(
            dataset_name=dataset_name,
            rule_id="DL_014",
            rule_description=(
                "neighbourhood_cleansed must exist in neighbourhoods.csv"
            ),
            checked_column="neighbourhood_cleansed",
            invalid_count=int(unknown),
            total_rows=total_rows,
            severity="ERROR",
        )

    del df
    gc.collect()


def validate_geojson(reference_sets: dict[str, set[Any]]) -> None:
    """Validate neighbourhoods.geojson."""
    dataset_name = "neighbourhoods.geojson"
    LOGGER.info("Validating %s...", dataset_name)

    with NEIGHBOURHOODS_GEOJSON_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    features = data.get("features", [])
    total_rows = len(features)
    neighbourhood_values: list[Any] = []
    geometry_types: list[Any] = []
    missing_geometry_count = 0

    for feature in features:
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry")
        neighbourhood_values.append(properties.get("neighbourhood"))

        if not geometry:
            missing_geometry_count += 1
            geometry_types.append(None)
        else:
            geometry_types.append(geometry.get("type"))

    neighbourhood_series = pd.Series(neighbourhood_values, dtype="object")

    add_result(
        dataset_name=dataset_name,
        rule_id="GJ_001",
        rule_description="GeoJSON neighbourhood name must not be null",
        checked_column="properties.neighbourhood",
        invalid_count=int(neighbourhood_series.isna().sum()),
        total_rows=total_rows,
        severity="ERROR",
    )
    add_result(
        dataset_name=dataset_name,
        rule_id="GJ_002",
        rule_description="GeoJSON neighbourhood name must be unique",
        checked_column="properties.neighbourhood",
        invalid_count=int(neighbourhood_series.duplicated(keep=False).sum()),
        total_rows=total_rows,
        severity="ERROR",
    )

    normalized_names = set(
        neighbourhood_series.dropna().astype(str).str.strip().tolist()
    )
    add_result(
        dataset_name=dataset_name,
        rule_id="GJ_003",
        rule_description=(
            "GeoJSON neighbourhoods must exist in neighbourhoods.csv"
        ),
        checked_column="properties.neighbourhood",
        invalid_count=len(
            normalized_names - reference_sets["neighbourhood_names"]
        ),
        total_rows=total_rows,
        severity="ERROR",
    )
    add_result(
        dataset_name=dataset_name,
        rule_id="GJ_004",
        rule_description=(
            "All reference neighbourhoods should have GeoJSON boundaries"
        ),
        checked_column="properties.neighbourhood",
        invalid_count=len(
            reference_sets["neighbourhood_names"] - normalized_names
        ),
        total_rows=len(reference_sets["neighbourhood_names"]),
        severity="ERROR",
    )
    add_result(
        dataset_name=dataset_name,
        rule_id="GJ_005",
        rule_description="GeoJSON geometry must not be missing",
        checked_column="geometry",
        invalid_count=missing_geometry_count,
        total_rows=total_rows,
        severity="ERROR",
    )

    invalid_geometry_types = sum(
        1
        for geometry_type in geometry_types
        if (
            geometry_type is not None
            and geometry_type not in VALID_GEOJSON_GEOMETRY_TYPES
        )
    )
    add_result(
        dataset_name=dataset_name,
        rule_id="GJ_006",
        rule_description="Geometry type must be Polygon or MultiPolygon",
        checked_column="geometry.type",
        invalid_count=invalid_geometry_types,
        total_rows=total_rows,
        severity="ERROR",
    )

    del data, features, neighbourhood_series
    gc.collect()


def validate_calendar() -> None:
    """Validate calendar.csv.gz with DuckDB."""
    dataset_name = "calendar.csv.gz"
    LOGGER.info("Validating %s with DuckDB...", dataset_name)

    con = create_duckdb_connection()
    try:
        relation = duckdb_relation(CALENDAR_PATH)
        schema = duckdb_schema(con, relation)
        total_rows = int(
            con.execute(f"SELECT COUNT(*) FROM {relation}").fetchone()[0]
        )

        missing_required = validate_required_columns(
            dataset_name=dataset_name,
            actual_columns=schema.keys(),
            required_columns=REQUIRED_COLUMNS[dataset_name],
            total_rows=total_rows,
            rule_prefix="CAL_SCHEMA",
        )

        if "listing_id" not in missing_required:
            add_result(
                dataset_name=dataset_name,
                rule_id="CAL_001",
                rule_description="Calendar listing_id must not be null",
                checked_column="listing_id",
                invalid_count=int(
                    con.execute(
                        f"SELECT COUNT(*) FROM {relation} WHERE listing_id IS NULL"
                    ).fetchone()[0]
                ),
                total_rows=total_rows,
                severity="ERROR",
            )

            summary_relation = duckdb_relation(SUMMARY_LISTINGS_PATH)
            orphan_rows = int(
                con.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM {relation} c
                    ANTI JOIN {summary_relation} l
                    ON c.listing_id = l.id
                    """
                ).fetchone()[0]
            )
            add_result(
                dataset_name=dataset_name,
                rule_id="CAL_002",
                rule_description=(
                    "Calendar listing_id must exist in canonical listings.csv"
                ),
                checked_column="listing_id",
                invalid_count=orphan_rows,
                total_rows=total_rows,
                severity="ERROR",
            )

        if "date" not in missing_required:
            add_result(
                dataset_name=dataset_name,
                rule_id="CAL_003",
                rule_description="Calendar date must not be null",
                checked_column="date",
                invalid_count=int(
                    con.execute(
                        f"SELECT COUNT(*) FROM {relation} WHERE date IS NULL"
                    ).fetchone()[0]
                ),
                total_rows=total_rows,
                severity="ERROR",
            )
            add_result(
                dataset_name=dataset_name,
                rule_id="CAL_004",
                rule_description="Non-null calendar dates must be parseable",
                checked_column="date",
                invalid_count=int(
                    con.execute(
                        f"""
                        SELECT COUNT(*)
                        FROM {relation}
                        WHERE date IS NOT NULL
                          AND TRY_CAST(date AS DATE) IS NULL
                        """
                    ).fetchone()[0]
                ),
                total_rows=total_rows,
                severity="ERROR",
            )

        if "listing_id" not in missing_required and "date" not in missing_required:
            duplicate_pairs = int(
                con.execute(
                    f"""
                    SELECT COUNT(*) - COUNT(DISTINCT hash(listing_id, date))
                    FROM {relation}
                    """
                ).fetchone()[0]
            )
            add_result(
                dataset_name=dataset_name,
                rule_id="CAL_005",
                rule_description="(listing_id, date) must be unique",
                checked_column="listing_id,date",
                invalid_count=duplicate_pairs,
                total_rows=total_rows,
                severity="ERROR",
                notes=(
                    "Uses DuckDB hash-based full-pair distinct counting for "
                    "memory-aware duplicate detection."
                ),
            )

        if "available" not in missing_required:
            unexpected = int(
                con.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM {relation}
                    WHERE available IS NULL
                       OR LOWER(TRIM(CAST(available AS VARCHAR)))
                          NOT IN ('t', 'f', 'true', 'false')
                    """
                ).fetchone()[0]
            )

            add_result(
                dataset_name=dataset_name,
                rule_id="CAL_006",
                rule_description=(
                    "available must represent a valid Boolean availability value"
                ),
                checked_column="available",
                invalid_count=unexpected,
                total_rows=total_rows,
                severity="ERROR",
                notes=(
                    "Accepts raw CSV values t/f and Boolean values true/false "
                    "because DuckDB may automatically infer the source column "
                    "as BOOLEAN during CSV ingestion."
                ),
            )

        if "minimum_nights" not in missing_required:
            invalid = int(
                con.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM {relation}
                    WHERE minimum_nights IS NOT NULL
                      AND (
                          TRY_CAST(minimum_nights AS DOUBLE) IS NULL
                          OR TRY_CAST(minimum_nights AS DOUBLE) < 0
                      )
                    """
                ).fetchone()[0]
            )
            add_result(
                dataset_name=dataset_name,
                rule_id="CAL_007",
                rule_description="minimum_nights must not be negative",
                checked_column="minimum_nights",
                invalid_count=invalid,
                total_rows=total_rows,
                severity="ERROR",
            )

        if "maximum_nights" not in missing_required:
            invalid = int(
                con.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM {relation}
                    WHERE maximum_nights IS NOT NULL
                      AND (
                          TRY_CAST(maximum_nights AS DOUBLE) IS NULL
                          OR TRY_CAST(maximum_nights AS DOUBLE) < 0
                      )
                    """
                ).fetchone()[0]
            )
            add_result(
                dataset_name=dataset_name,
                rule_id="CAL_008",
                rule_description="maximum_nights must not be negative",
                checked_column="maximum_nights",
                invalid_count=invalid,
                total_rows=total_rows,
                severity="ERROR",
            )

        if "minimum_nights" not in missing_required and "maximum_nights" not in missing_required:
            inconsistent = int(
                con.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM {relation}
                    WHERE TRY_CAST(minimum_nights AS DOUBLE) IS NOT NULL
                      AND TRY_CAST(maximum_nights AS DOUBLE) IS NOT NULL
                      AND TRY_CAST(maximum_nights AS DOUBLE)
                          < TRY_CAST(minimum_nights AS DOUBLE)
                    """
                ).fetchone()[0]
            )
            add_result(
                dataset_name=dataset_name,
                rule_id="CAL_009",
                rule_description=(
                    "maximum_nights should not be less than minimum_nights"
                ),
                checked_column="minimum_nights,maximum_nights",
                invalid_count=inconsistent,
                total_rows=total_rows,
                severity="ERROR",
            )
    finally:
        con.close()
        gc.collect()


def validate_detailed_reviews() -> None:
    """Validate reviews.csv.gz with DuckDB."""
    dataset_name = "reviews.csv.gz"
    LOGGER.info("Validating %s with DuckDB...", dataset_name)

    con = create_duckdb_connection()
    try:
        relation = duckdb_relation(DETAILED_REVIEWS_PATH)
        schema = duckdb_schema(con, relation)
        total_rows = int(
            con.execute(f"SELECT COUNT(*) FROM {relation}").fetchone()[0]
        )

        missing_required = validate_required_columns(
            dataset_name=dataset_name,
            actual_columns=schema.keys(),
            required_columns=REQUIRED_COLUMNS[dataset_name],
            total_rows=total_rows,
            rule_prefix="DR_SCHEMA",
        )

        if "id" not in missing_required:
            add_result(
                dataset_name=dataset_name,
                rule_id="DR_001",
                rule_description="Review ID must not be null",
                checked_column="id",
                invalid_count=int(
                    con.execute(
                        f"SELECT COUNT(*) FROM {relation} WHERE id IS NULL"
                    ).fetchone()[0]
                ),
                total_rows=total_rows,
                severity="ERROR",
            )
            add_result(
                dataset_name=dataset_name,
                rule_id="DR_002",
                rule_description="Review ID must be unique",
                checked_column="id",
                invalid_count=int(
                    con.execute(
                        f"""
                        SELECT COUNT(*) - COUNT(DISTINCT id)
                        FROM {relation}
                        WHERE id IS NOT NULL
                        """
                    ).fetchone()[0]
                ),
                total_rows=total_rows,
                severity="ERROR",
            )

        if "listing_id" not in missing_required:
            add_result(
                dataset_name=dataset_name,
                rule_id="DR_003",
                rule_description="Detailed review listing_id must not be null",
                checked_column="listing_id",
                invalid_count=int(
                    con.execute(
                        f"SELECT COUNT(*) FROM {relation} WHERE listing_id IS NULL"
                    ).fetchone()[0]
                ),
                total_rows=total_rows,
                severity="ERROR",
            )

            summary_relation = duckdb_relation(SUMMARY_LISTINGS_PATH)
            orphan_rows = int(
                con.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM {relation} r
                    ANTI JOIN {summary_relation} l
                    ON r.listing_id = l.id
                    """
                ).fetchone()[0]
            )
            add_result(
                dataset_name=dataset_name,
                rule_id="DR_004",
                rule_description=(
                    "Detailed review listing_id should exist in canonical "
                    "listings.csv"
                ),
                checked_column="listing_id",
                invalid_count=orphan_rows,
                total_rows=total_rows,
                severity="ERROR",
            )

        if "date" not in missing_required:
            add_result(
                dataset_name=dataset_name,
                rule_id="DR_005",
                rule_description="Detailed review date must not be null",
                checked_column="date",
                invalid_count=int(
                    con.execute(
                        f"SELECT COUNT(*) FROM {relation} WHERE date IS NULL"
                    ).fetchone()[0]
                ),
                total_rows=total_rows,
                severity="ERROR",
            )
            add_result(
                dataset_name=dataset_name,
                rule_id="DR_006",
                rule_description="Non-null review dates must be parseable",
                checked_column="date",
                invalid_count=int(
                    con.execute(
                        f"""
                        SELECT COUNT(*)
                        FROM {relation}
                        WHERE date IS NOT NULL
                          AND TRY_CAST(date AS DATE) IS NULL
                        """
                    ).fetchone()[0]
                ),
                total_rows=total_rows,
                severity="ERROR",
            )

        if "reviewer_id" not in missing_required:
            add_result(
                dataset_name=dataset_name,
                rule_id="DR_007",
                rule_description="Report missing reviewer IDs",
                checked_column="reviewer_id",
                invalid_count=int(
                    con.execute(
                        f"SELECT COUNT(*) FROM {relation} WHERE reviewer_id IS NULL"
                    ).fetchone()[0]
                ),
                total_rows=total_rows,
                severity="WARNING",
            )

        if "reviewer_name" not in missing_required:
            missing_names = int(
                con.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM {relation}
                    WHERE reviewer_name IS NULL
                       OR TRIM(CAST(reviewer_name AS VARCHAR)) = ''
                    """
                ).fetchone()[0]
            )
            add_result(
                dataset_name=dataset_name,
                rule_id="DR_008",
                rule_description="Report missing reviewer names",
                checked_column="reviewer_name",
                invalid_count=missing_names,
                total_rows=total_rows,
                severity="WARNING",
                notes=(
                    "Reviewer-name missingness is non-critical metadata and "
                    "does not invalidate the review event."
                ),
            )

        if "comments" not in missing_required:
            missing_comments = int(
                con.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM {relation}
                    WHERE comments IS NULL
                       OR TRIM(CAST(comments AS VARCHAR)) = ''
                    """
                ).fetchone()[0]
            )
            add_result(
                dataset_name=dataset_name,
                rule_id="DR_009",
                rule_description="Report missing or empty review comments",
                checked_column="comments",
                invalid_count=missing_comments,
                total_rows=total_rows,
                severity="INFO",
                notes=(
                    "Missing review text may matter for optional NLP analysis "
                    "but does not invalidate the core review event."
                ),
            )
    finally:
        con.close()
        gc.collect()


def main() -> None:
    """Run all validation suites and save one consolidated CSV report."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_RESULTS.clear()

    LOGGER.info("Starting automated data-quality validation.")
    LOGGER.info("Raw data directory: %s", RAW_DIR)
    LOGGER.info("Output directory: %s", OUTPUT_DIR)

    required_files = [
        NEIGHBOURHOODS_PATH,
        SUMMARY_LISTINGS_PATH,
        SUMMARY_REVIEWS_PATH,
        DETAILED_LISTINGS_PATH,
        NEIGHBOURHOODS_GEOJSON_PATH,
        CALENDAR_PATH,
        DETAILED_REVIEWS_PATH,
    ]
    for path in required_files:
        require_file(path)

    reference_sets = load_reference_sets()

    validate_neighbourhoods_csv()
    validate_summary_listings(reference_sets)
    validate_summary_reviews(reference_sets)
    validate_detailed_listings(reference_sets)
    validate_geojson(reference_sets)
    validate_calendar()
    validate_detailed_reviews()

    results_df = pd.DataFrame(VALIDATION_RESULTS)
    status_rank = {"FAIL": 0, "WARNING": 1, "PASS": 2}
    results_df["_status_rank"] = results_df["status"].map(status_rank)
    results_df = (
        results_df
        .sort_values(["_status_rank", "dataset_name", "rule_id"])
        .drop(columns="_status_rank")
        .reset_index(drop=True)
    )

    results_df.to_csv(
        VALIDATION_RESULTS_PATH,
        index=False,
        encoding="utf-8",
    )

    status_counts = (
        results_df["status"]
        .value_counts()
        .reindex(["PASS", "WARNING", "FAIL"], fill_value=0)
    )

    LOGGER.info("Saved: %s", VALIDATION_RESULTS_PATH)
    LOGGER.info(
        "Validation finished: %s PASS, %s WARNING, %s FAIL.",
        status_counts["PASS"],
        status_counts["WARNING"],
        status_counts["FAIL"],
    )

    if int(status_counts["FAIL"]) > 0:
        LOGGER.warning(
            "%s critical validation rule(s) failed. Review the generated "
            "report before cleaning.",
            status_counts["FAIL"],
        )
    else:
        LOGGER.info(
            "No critical validation rules failed. Review warnings before "
            "continuing to cleaning and standardization."
        )


if __name__ == "__main__":
    main()

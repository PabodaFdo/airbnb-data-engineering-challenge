"""
Listing-level enrichment for the Amsterdam Airbnb project.

This module builds one analysis-ready master dataset with exactly one row per
canonical listing:

    data/processed/enriched_listing_master.parquet

It also creates compact listing-level aggregates:

    data/processed/review_listing_aggregates.parquet
    data/processed/calendar_listing_aggregates.parquet

and an audit summary:

    outputs/data_quality/enrichment_summary.csv

Design principles:
- Preserve the canonical 10,465-listing population from listings.csv.
- Never directly join raw one-to-many review or calendar rows to listings.
- Aggregate large review and calendar datasets with DuckDB first.
- Keep all 96 summary-only listings even when detailed attributes are missing.
- Avoid calling unavailability true occupancy.
- Remain safe for an 8 GB RAM laptop.
"""

from __future__ import annotations

import gc
import logging
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "amsterdam"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
QUALITY_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "data_quality"
DUCKDB_TEMP_DIR = QUALITY_OUTPUT_DIR / "duckdb_temp"

CLEANED_LISTINGS_PATH = PROCESSED_DIR / "cleaned_listings.parquet"
CLEANED_DETAILED_LISTINGS_PATH = (
    PROCESSED_DIR / "cleaned_detailed_listings.parquet"
)

RAW_REVIEWS_PATH = RAW_DIR / "reviews.csv.gz"
RAW_CALENDAR_PATH = RAW_DIR / "calendar.csv.gz"

REVIEW_AGGREGATES_PATH = (
    PROCESSED_DIR / "review_listing_aggregates.parquet"
)
CALENDAR_AGGREGATES_PATH = (
    PROCESSED_DIR / "calendar_listing_aggregates.parquet"
)
ENRICHED_MASTER_PATH = (
    PROCESSED_DIR / "enriched_listing_master.parquet"
)

ENRICHMENT_SUMMARY_PATH = (
    QUALITY_OUTPUT_DIR / "enrichment_summary.csv"
)


# ---------------------------------------------------------------------------
# Expected canonical grain
# ---------------------------------------------------------------------------

EXPECTED_CANONICAL_LISTING_COUNT = 10_465


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Audit collector
# ---------------------------------------------------------------------------

ENRICHMENT_SUMMARY: list[dict[str, Any]] = []


def record_metric(
    *,
    metric: str,
    value: Any,
    notes: str,
) -> None:
    """Record one enrichment audit metric."""
    ENRICHMENT_SUMMARY.append(
        {
            "metric": metric,
            "value": value,
            "notes": notes,
        }
    )


# ---------------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------------

def require_file(path: Path) -> None:
    """Raise a clear error if a required file does not exist."""
    if not path.exists():
        raise FileNotFoundError(
            f"Required file was not found: {path}"
        )


def escape_sql_path(path: Path) -> str:
    """Escape a filesystem path for use inside a DuckDB SQL literal."""
    return path.resolve().as_posix().replace("'", "''")


def duckdb_csv_relation(path: Path) -> str:
    """Return a DuckDB relation expression for CSV/CSV.GZ input."""
    escaped_path = escape_sql_path(path)

    return (
        "read_csv_auto("
        f"'{escaped_path}', "
        "header=true, "
        "sample_size=200000"
        ")"
    )


def create_duckdb_connection() -> duckdb.DuckDBPyConnection:
    """
    Create an in-memory, 8 GB RAM-aware DuckDB connection.

    DuckDB is limited to 3 GB and can spill temporary work to disk.
    """
    DUCKDB_TEMP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    con = duckdb.connect(database=":memory:")

    con.execute("SET memory_limit = '3GB'")
    con.execute("SET preserve_insertion_order = false")

    temp_directory = escape_sql_path(DUCKDB_TEMP_DIR)

    con.execute(
        f"SET temp_directory = '{temp_directory}'"
    )

    return con


def ensure_unique_key(
    df: pd.DataFrame,
    *,
    dataset_name: str,
    key_column: str,
) -> None:
    """Fail fast if a supposedly one-row-per-key dataset is not unique."""
    if key_column not in df.columns:
        raise ValueError(
            f"{dataset_name}: required key column '{key_column}' is missing."
        )

    null_count = int(df[key_column].isna().sum())

    duplicate_count = int(
        df[key_column].duplicated(keep=False).sum()
    )

    if null_count > 0:
        raise ValueError(
            f"{dataset_name}: found {null_count:,} null values in "
            f"'{key_column}'."
        )

    if duplicate_count > 0:
        raise ValueError(
            f"{dataset_name}: found {duplicate_count:,} rows participating "
            f"in duplicate '{key_column}' groups."
        )


# ---------------------------------------------------------------------------
# Detailed listing attributes
# ---------------------------------------------------------------------------

def prepare_detailed_listing_attributes() -> pd.DataFrame:
    """
    Select only analytically useful detailed-listing attributes.

    Columns are selected dynamically so the code remains robust to harmless
    source-schema variation.
    """
    LOGGER.info(
        "Preparing detailed listing attributes..."
    )

    detailed = pd.read_parquet(
        CLEANED_DETAILED_LISTINGS_PATH
    )

    ensure_unique_key(
        detailed,
        dataset_name="cleaned_detailed_listings.parquet",
        key_column="id",
    )

    desired_columns = [
        "id",
        "property_type",
        "accommodates",
        "bathrooms",
        "bedrooms",
        "beds",
        "amenities",
        "price",
        "price_raw",
        "maximum_nights",
        "host_is_superhost",
        "host_has_profile_pic",
        "host_identity_verified",
        "host_listings_count",
        "has_availability",
        "availability_30",
        "availability_60",
        "availability_90",
        "review_scores_rating",
        "review_scores_accuracy",
        "review_scores_cleanliness",
        "review_scores_checkin",
        "review_scores_communication",
        "review_scores_location",
        "review_scores_value",
        "calculated_host_listings_count_entire_homes",
        "calculated_host_listings_count_private_rooms",
        "calculated_host_listings_count_shared_rooms",
    ]

    available_columns = [
        column
        for column in desired_columns
        if column in detailed.columns
    ]

    selected = detailed[available_columns].copy()

    rename_map = {
        "id": "listing_id",
        "price": "detailed_price",
        "price_raw": "detailed_price_raw",
        "property_type": "detailed_property_type",
    }

    selected = selected.rename(
        columns=rename_map
    )

    selected["detailed_source_available"] = True

    ensure_unique_key(
        selected,
        dataset_name="prepared detailed listing attributes",
        key_column="listing_id",
    )

    record_metric(
        metric="detailed_listing_rows",
        value=len(selected),
        notes=(
            "Number of one-row-per-listing records available from the "
            "cleaned detailed listing source."
        ),
    )

    record_metric(
        metric="detailed_listing_selected_columns",
        value=len(selected.columns),
        notes=(
            "Number of detailed attributes retained for listing enrichment, "
            "including the source-availability flag."
        ),
    )

    del detailed
    gc.collect()

    return selected


# ---------------------------------------------------------------------------
# Review aggregation
# ---------------------------------------------------------------------------

def build_review_aggregates() -> pd.DataFrame:
    """
    Aggregate detailed reviews to exactly one row per reviewed listing.

    Raw comments are never loaded into Pandas.
    """
    LOGGER.info(
        "Aggregating detailed reviews with DuckDB..."
    )

    con = create_duckdb_connection()

    try:
        relation = duckdb_csv_relation(
            RAW_REVIEWS_PATH
        )

        query = f"""
        SELECT
            listing_id,

            COUNT(*)::BIGINT AS detailed_review_count,

            MIN(TRY_CAST(date AS DATE))
                AS first_detailed_review_date,

            MAX(TRY_CAST(date AS DATE))
                AS last_detailed_review_date,

            DATE_DIFF(
                'day',
                MIN(TRY_CAST(date AS DATE)),
                MAX(TRY_CAST(date AS DATE))
            )::BIGINT AS review_span_days,

            COUNT(DISTINCT reviewer_id)::BIGINT
                AS unique_reviewer_count,

            SUM(
                CASE
                    WHEN reviewer_name IS NULL
                      OR TRIM(CAST(reviewer_name AS VARCHAR)) = ''
                    THEN 1
                    ELSE 0
                END
            )::BIGINT AS missing_reviewer_name_count,

            SUM(
                CASE
                    WHEN comments IS NULL
                      OR TRIM(CAST(comments AS VARCHAR)) = ''
                    THEN 1
                    ELSE 0
                END
            )::BIGINT AS missing_comment_count

        FROM {relation}

        GROUP BY listing_id

        ORDER BY listing_id
        """

        review_aggregates = con.execute(
            query
        ).fetch_df()

    finally:
        con.close()
        gc.collect()

    ensure_unique_key(
        review_aggregates,
        dataset_name="review listing aggregates",
        key_column="listing_id",
    )

    review_aggregates[
        "review_events_per_active_year"
    ] = np.where(
        review_aggregates["review_span_days"] >= 30,
        (
            review_aggregates["detailed_review_count"]
            * 365.25
            / review_aggregates["review_span_days"]
        ),
        np.nan,
    )

    review_aggregates[
        "review_events_per_active_year"
    ] = pd.to_numeric(
        review_aggregates[
            "review_events_per_active_year"
        ],
        errors="coerce",
    ).round(4)

    review_aggregates.to_parquet(
        REVIEW_AGGREGATES_PATH,
        index=False,
        engine="pyarrow",
    )

    LOGGER.info(
        "Saved: %s",
        REVIEW_AGGREGATES_PATH,
    )

    record_metric(
        metric="review_aggregate_rows",
        value=len(review_aggregates),
        notes=(
            "Number of listings with at least one detailed review."
        ),
    )

    record_metric(
        metric="total_detailed_reviews_aggregated",
        value=int(
            review_aggregates[
                "detailed_review_count"
            ].sum()
        ),
        notes=(
            "Total detailed review events represented in the "
            "listing-level aggregate."
        ),
    )

    return review_aggregates


# ---------------------------------------------------------------------------
# Calendar aggregation
# ---------------------------------------------------------------------------

def build_calendar_aggregates() -> pd.DataFrame:
    """
    Aggregate 3.8M+ calendar rows to one row per listing with DuckDB.

    Availability is interpreted cautiously. The derived
    `unavailability_rate_proxy` is not true occupancy.
    """
    LOGGER.info(
        "Aggregating calendar data with DuckDB..."
    )

    con = create_duckdb_connection()

    try:
        relation = duckdb_csv_relation(
            RAW_CALENDAR_PATH
        )

        query = f"""
        WITH normalized AS (
            SELECT
                listing_id,
                TRY_CAST(date AS DATE) AS calendar_date,
                TRY_CAST(available AS BOOLEAN) AS is_available,
                TRY_CAST(minimum_nights AS DOUBLE)
                    AS minimum_nights_numeric,
                TRY_CAST(maximum_nights AS DOUBLE)
                    AS maximum_nights_numeric
            FROM {relation}
        )

        SELECT
            listing_id,

            COUNT(*)::BIGINT AS calendar_days_observed,

            SUM(
                CASE
                    WHEN is_available IS TRUE
                    THEN 1
                    ELSE 0
                END
            )::BIGINT AS available_days,

            SUM(
                CASE
                    WHEN is_available IS FALSE
                    THEN 1
                    ELSE 0
                END
            )::BIGINT AS unavailable_days,

            ROUND(
                SUM(
                    CASE
                        WHEN is_available IS TRUE
                        THEN 1.0
                        ELSE 0.0
                    END
                )
                / NULLIF(COUNT(*), 0),
                6
            ) AS availability_rate_observed,

            ROUND(
                SUM(
                    CASE
                        WHEN is_available IS FALSE
                        THEN 1.0
                        ELSE 0.0
                    END
                )
                / NULLIF(COUNT(*), 0),
                6
            ) AS unavailability_rate_proxy,

            MIN(calendar_date)
                AS calendar_start_date,

            MAX(calendar_date)
                AS calendar_end_date,

            SUM(
                CASE
                    WHEN EXTRACT(DOW FROM calendar_date) IN (0, 6)
                    THEN 1
                    ELSE 0
                END
            )::BIGINT AS weekend_days_observed,

            SUM(
                CASE
                    WHEN EXTRACT(DOW FROM calendar_date) IN (0, 6)
                     AND is_available IS TRUE
                    THEN 1
                    ELSE 0
                END
            )::BIGINT AS available_weekend_days,

            ROUND(
                SUM(
                    CASE
                        WHEN EXTRACT(DOW FROM calendar_date) IN (0, 6)
                         AND is_available IS TRUE
                        THEN 1.0
                        ELSE 0.0
                    END
                )
                / NULLIF(
                    SUM(
                        CASE
                            WHEN EXTRACT(DOW FROM calendar_date) IN (0, 6)
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ),
                6
            ) AS weekend_availability_rate,

            SUM(
                CASE
                    WHEN EXTRACT(DOW FROM calendar_date) NOT IN (0, 6)
                    THEN 1
                    ELSE 0
                END
            )::BIGINT AS weekday_days_observed,

            SUM(
                CASE
                    WHEN EXTRACT(DOW FROM calendar_date) NOT IN (0, 6)
                     AND is_available IS TRUE
                    THEN 1
                    ELSE 0
                END
            )::BIGINT AS available_weekday_days,

            ROUND(
                SUM(
                    CASE
                        WHEN EXTRACT(DOW FROM calendar_date) NOT IN (0, 6)
                         AND is_available IS TRUE
                        THEN 1.0
                        ELSE 0.0
                    END
                )
                / NULLIF(
                    SUM(
                        CASE
                            WHEN EXTRACT(DOW FROM calendar_date) NOT IN (0, 6)
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ),
                6
            ) AS weekday_availability_rate,

            ROUND(
                AVG(minimum_nights_numeric),
                4
            ) AS calendar_avg_minimum_nights,

            MIN(minimum_nights_numeric)
                AS calendar_minimum_nights_min,

            MAX(minimum_nights_numeric)
                AS calendar_minimum_nights_max,

            ROUND(
                AVG(maximum_nights_numeric),
                4
            ) AS calendar_avg_maximum_nights

        FROM normalized

        GROUP BY listing_id

        ORDER BY listing_id
        """

        calendar_aggregates = con.execute(
            query
        ).fetch_df()

    finally:
        con.close()
        gc.collect()

    ensure_unique_key(
        calendar_aggregates,
        dataset_name="calendar listing aggregates",
        key_column="listing_id",
    )

    calendar_aggregates[
        "calendar_complete_365_day_window"
    ] = (
        calendar_aggregates[
            "calendar_days_observed"
        ]
        .eq(365)
        .astype("boolean")
    )

    calendar_aggregates.to_parquet(
        CALENDAR_AGGREGATES_PATH,
        index=False,
        engine="pyarrow",
    )

    LOGGER.info(
        "Saved: %s",
        CALENDAR_AGGREGATES_PATH,
    )

    record_metric(
        metric="calendar_aggregate_rows",
        value=len(calendar_aggregates),
        notes=(
            "Number of listings represented in the one-row-per-listing "
            "calendar aggregate."
        ),
    )

    record_metric(
        metric="total_calendar_rows_aggregated",
        value=int(
            calendar_aggregates[
                "calendar_days_observed"
            ].sum()
        ),
        notes=(
            "Total daily calendar rows represented in the aggregate."
        ),
    )

    record_metric(
        metric="listings_with_complete_365_day_calendar",
        value=int(
            calendar_aggregates[
                "calendar_complete_365_day_window"
            ].sum()
        ),
        notes=(
            "Listings with exactly 365 observed calendar rows."
        ),
    )

    return calendar_aggregates


# ---------------------------------------------------------------------------
# Derived features
# ---------------------------------------------------------------------------

def add_derived_features(
    master: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add transparent, business-useful listing-level derived features.

    No causal or verified occupancy claims are made.
    """
    LOGGER.info(
        "Creating derived listing-level features..."
    )

    # ---------------------------------------------------------------
    # Detailed-source coverage
    # ---------------------------------------------------------------

    if "detailed_source_available" in master.columns:
        master[
            "detailed_source_available"
        ] = (
            master[
                "detailed_source_available"
            ]
            .fillna(False)
            .astype("boolean")
        )

    # ---------------------------------------------------------------
    # Best available price while preserving both sources
    # ---------------------------------------------------------------

    if (
        "price" in master.columns
        and "detailed_price" in master.columns
    ):
        master[
            "price_best_available"
        ] = master["price"].combine_first(
            master["detailed_price"]
        )

        master["price_source"] = pd.Series(
            np.select(
                [
                    master["price"].notna(),
                    master["detailed_price"].notna(),
                ],
                [
                    "summary_listings",
                    "detailed_listings",
                ],
                default="missing",
            ),
            index=master.index,
            dtype="string",
        )

    elif "price" in master.columns:
        master[
            "price_best_available"
        ] = master["price"]

        master["price_source"] = pd.Series(
            np.where(
                master["price"].notna(),
                "summary_listings",
                "missing",
            ),
            index=master.index,
            dtype="string",
        )

    # ---------------------------------------------------------------
    # Price efficiency features
    # ---------------------------------------------------------------

    if (
        "price_best_available" in master.columns
        and "bedrooms" in master.columns
    ):
        valid_bedrooms = (
            master["bedrooms"].notna()
            & master["bedrooms"].gt(0)
        )

        master["price_per_bedroom"] = pd.Series(
            np.nan,
            index=master.index,
            dtype="Float64",
        )

        master.loc[
            valid_bedrooms,
            "price_per_bedroom",
        ] = (
            master.loc[
                valid_bedrooms,
                "price_best_available",
            ]
            / master.loc[
                valid_bedrooms,
                "bedrooms",
            ]
        )

    if (
        "price_best_available" in master.columns
        and "accommodates" in master.columns
    ):
        valid_guests = (
            master["accommodates"].notna()
            & master["accommodates"].gt(0)
        )

        master["price_per_guest"] = pd.Series(
            np.nan,
            index=master.index,
            dtype="Float64",
        )

        master.loc[
            valid_guests,
            "price_per_guest",
        ] = (
            master.loc[
                valid_guests,
                "price_best_available",
            ]
            / master.loc[
                valid_guests,
                "accommodates",
            ]
        )

    # ---------------------------------------------------------------
    # Host portfolio segmentation
    # ---------------------------------------------------------------

    if "calculated_host_listings_count" in master.columns:
        portfolio_size = pd.to_numeric(
            master[
                "calculated_host_listings_count"
            ],
            errors="coerce",
        )

        master[
            "host_portfolio_size"
        ] = portfolio_size.astype("Float64")

        portfolio_segment = np.select(
            [
                portfolio_size.eq(1)
                .fillna(False)
                .to_numpy(dtype=bool),

                portfolio_size.between(
                    2,
                    5,
                    inclusive="both",
                )
                .fillna(False)
                .to_numpy(dtype=bool),

                portfolio_size.ge(6)
                .fillna(False)
                .to_numpy(dtype=bool),
            ],
            [
                "Single-listing host",
                "Small multi-listing host (2-5)",
                "Large/professional host (6+)",
            ],
            default=None,
        )

        master[
            "host_portfolio_segment"
        ] = pd.Series(
            portfolio_segment,
            index=master.index,
            dtype="string",
        )

    # ---------------------------------------------------------------
    # Review-derived features
    # ---------------------------------------------------------------

    if "detailed_review_count" in master.columns:
        master[
            "detailed_review_count"
        ] = (
            master[
                "detailed_review_count"
            ]
            .fillna(0)
            .astype("Int64")
        )

        master[
            "has_review_history"
        ] = (
            master[
                "detailed_review_count"
            ]
            .gt(0)
            .astype("boolean")
        )

    # ---------------------------------------------------------------
    # Calendar-derived coverage features
    # ---------------------------------------------------------------

    if "calendar_days_observed" in master.columns:
        master[
            "calendar_data_available"
        ] = (
            master[
                "calendar_days_observed"
            ]
            .notna()
            .astype("boolean")
        )

    # Round business-facing ratio features for readability.
    ratio_columns = [
        "price_per_bedroom",
        "price_per_guest",
        "review_events_per_active_year",
    ]

    for column in ratio_columns:
        if column in master.columns:
            master[column] = pd.to_numeric(
                master[column],
                errors="coerce",
            ).round(4)

    return master


# ---------------------------------------------------------------------------
# Master dataset construction
# ---------------------------------------------------------------------------

def build_enriched_listing_master(
    *,
    detailed_attributes: pd.DataFrame,
    review_aggregates: pd.DataFrame,
    calendar_aggregates: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build the final one-row-per-canonical-listing master dataset.
    """
    LOGGER.info(
        "Building enriched listing master..."
    )

    canonical = pd.read_parquet(
        CLEANED_LISTINGS_PATH
    )

    ensure_unique_key(
        canonical,
        dataset_name="cleaned_listings.parquet",
        key_column="id",
    )

    if len(canonical) != EXPECTED_CANONICAL_LISTING_COUNT:
        raise ValueError(
            "Canonical input row-count mismatch: expected "
            f"{EXPECTED_CANONICAL_LISTING_COUNT:,}, "
            f"found {len(canonical):,}."
        )

    canonical_ids = set(
        canonical["id"].dropna().tolist()
    )

    record_metric(
        metric="canonical_input_rows",
        value=len(canonical),
        notes=(
            "Canonical listing population before enrichment."
        ),
    )

    # ---------------------------------------------------------------
    # Join detailed attributes
    # ---------------------------------------------------------------

    master = canonical.merge(
        detailed_attributes,
        how="left",
        left_on="id",
        right_on="listing_id",
        validate="one_to_one",
    )

    detailed_match_count = int(
        master[
            "detailed_source_available"
        ]
        .fillna(False)
        .sum()
    )

    summary_only_count = (
        len(master) - detailed_match_count
    )

    record_metric(
        metric="detailed_listing_matches",
        value=detailed_match_count,
        notes=(
            "Canonical listings matched to the cleaned detailed source."
        ),
    )

    record_metric(
        metric="summary_only_listings_preserved",
        value=summary_only_count,
        notes=(
            "Canonical listings without a detailed-source match. "
            "These rows remain in the enriched master."
        ),
    )

    master = master.drop(
        columns=["listing_id"],
        errors="ignore",
    )

    # ---------------------------------------------------------------
    # Join review aggregates
    # ---------------------------------------------------------------

    review_ids = set(
        review_aggregates[
            "listing_id"
        ].dropna().tolist()
    )

    orphan_review_aggregate_ids = (
        review_ids - canonical_ids
    )

    if orphan_review_aggregate_ids:
        raise ValueError(
            "Review aggregates contain listing IDs outside the canonical "
            f"population: {len(orphan_review_aggregate_ids):,} IDs."
        )

    master = master.merge(
        review_aggregates,
        how="left",
        left_on="id",
        right_on="listing_id",
        validate="one_to_one",
    )

    master = master.drop(
        columns=["listing_id"],
        errors="ignore",
    )

    # ---------------------------------------------------------------
    # Join calendar aggregates
    # ---------------------------------------------------------------

    calendar_ids = set(
        calendar_aggregates[
            "listing_id"
        ].dropna().tolist()
    )

    orphan_calendar_aggregate_ids = (
        calendar_ids - canonical_ids
    )

    if orphan_calendar_aggregate_ids:
        raise ValueError(
            "Calendar aggregates contain listing IDs outside the canonical "
            f"population: {len(orphan_calendar_aggregate_ids):,} IDs."
        )

    master = master.merge(
        calendar_aggregates,
        how="left",
        left_on="id",
        right_on="listing_id",
        validate="one_to_one",
    )

    master = master.drop(
        columns=["listing_id"],
        errors="ignore",
    )

    # ---------------------------------------------------------------
    # Derived features
    # ---------------------------------------------------------------

    master = add_derived_features(
        master
    )

    # ---------------------------------------------------------------
    # Final integrity checks
    # ---------------------------------------------------------------

    ensure_unique_key(
        master,
        dataset_name="enriched_listing_master.parquet",
        key_column="id",
    )

    if len(master) != EXPECTED_CANONICAL_LISTING_COUNT:
        raise ValueError(
            "Final enrichment changed the canonical grain: expected "
            f"{EXPECTED_CANONICAL_LISTING_COUNT:,} rows, "
            f"found {len(master):,}."
        )

    record_metric(
        metric="final_enriched_rows",
        value=len(master),
        notes=(
            "Final listing-level master row count. Must equal the canonical "
            "input population."
        ),
    )

    record_metric(
        metric="final_enriched_columns",
        value=len(master.columns),
        notes=(
            "Number of analysis-ready fields in the enriched listing master."
        ),
    )

    if "price_best_available" in master.columns:
        record_metric(
            metric="price_best_available_non_null",
            value=int(
                master[
                    "price_best_available"
                ].notna().sum()
            ),
            notes=(
                "Listings with a usable price from the summary source first, "
                "falling back to the detailed source when summary price is "
                "missing."
            ),
        )

    if "has_review_history" in master.columns:
        record_metric(
            metric="listings_with_review_history",
            value=int(
                master[
                    "has_review_history"
                ].sum()
            ),
            notes=(
                "Listings with at least one detailed review event."
            ),
        )

    if "calendar_data_available" in master.columns:
        record_metric(
            metric="listings_with_calendar_data",
            value=int(
                master[
                    "calendar_data_available"
                ].sum()
            ),
            notes=(
                "Canonical listings with listing-level calendar aggregates."
            ),
        )

    return master


# ---------------------------------------------------------------------------
# Final output verification
# ---------------------------------------------------------------------------

def verify_enriched_output() -> None:
    """
    Re-read the final Parquet output and verify canonical listing integrity.
    """
    LOGGER.info(
        "Verifying final enriched Parquet output..."
    )

    if not ENRICHED_MASTER_PATH.exists():
        raise FileNotFoundError(
            f"Expected enriched output was not created: "
            f"{ENRICHED_MASTER_PATH}"
        )

    check = pd.read_parquet(
        ENRICHED_MASTER_PATH,
        columns=["id"],
    )

    if len(check) != EXPECTED_CANONICAL_LISTING_COUNT:
        raise ValueError(
            "Final Parquet verification failed: expected "
            f"{EXPECTED_CANONICAL_LISTING_COUNT:,} rows, "
            f"found {len(check):,}."
        )

    ensure_unique_key(
        check,
        dataset_name="saved enriched_listing_master.parquet",
        key_column="id",
    )

    LOGGER.info(
        "Verified enriched_listing_master.parquet: %s rows, "
        "unique non-null listing IDs.",
        f"{len(check):,}",
    )

    del check
    gc.collect()


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the full listing-level enrichment pipeline."""
    required_files = [
        CLEANED_LISTINGS_PATH,
        CLEANED_DETAILED_LISTINGS_PATH,
        RAW_REVIEWS_PATH,
        RAW_CALENDAR_PATH,
    ]

    for path in required_files:
        require_file(path)

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    QUALITY_OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ENRICHMENT_SUMMARY.clear()

    LOGGER.info(
        "Starting listing-level enrichment."
    )

    LOGGER.info(
        "Canonical grain target: one row per listing (%s rows).",
        f"{EXPECTED_CANONICAL_LISTING_COUNT:,}",
    )

    # ---------------------------------------------------------------
    # 1. Prepare detailed listing attributes
    # ---------------------------------------------------------------

    detailed_attributes = (
        prepare_detailed_listing_attributes()
    )

    # ---------------------------------------------------------------
    # 2. Aggregate detailed reviews
    # ---------------------------------------------------------------

    review_aggregates = (
        build_review_aggregates()
    )

    # ---------------------------------------------------------------
    # 3. Aggregate calendar rows
    # ---------------------------------------------------------------

    calendar_aggregates = (
        build_calendar_aggregates()
    )

    # ---------------------------------------------------------------
    # 4. Build final enriched listing master
    # ---------------------------------------------------------------

    enriched_master = (
        build_enriched_listing_master(
            detailed_attributes=detailed_attributes,
            review_aggregates=review_aggregates,
            calendar_aggregates=calendar_aggregates,
        )
    )

    enriched_master.to_parquet(
        ENRICHED_MASTER_PATH,
        index=False,
        engine="pyarrow",
    )

    LOGGER.info(
        "Saved: %s",
        ENRICHED_MASTER_PATH,
    )

    # ---------------------------------------------------------------
    # 5. Save enrichment audit summary
    # ---------------------------------------------------------------

    enrichment_summary_df = pd.DataFrame(
        ENRICHMENT_SUMMARY
    )

    enrichment_summary_df.to_csv(
        ENRICHMENT_SUMMARY_PATH,
        index=False,
        encoding="utf-8",
    )

    LOGGER.info(
        "Saved: %s",
        ENRICHMENT_SUMMARY_PATH,
    )

    # ---------------------------------------------------------------
    # 6. Final verification
    # ---------------------------------------------------------------

    verify_enriched_output()

    LOGGER.info(
        "Enrichment completed successfully."
    )

    LOGGER.info(
        "Canonical listings preserved: %s rows.",
        f"{EXPECTED_CANONICAL_LISTING_COUNT:,}",
    )

    if "detailed_source_available" in enriched_master.columns:
        LOGGER.info(
            "Detailed-source matches: %s.",
            f"{int(enriched_master['detailed_source_available'].sum()):,}",
        )

        LOGGER.info(
            "Summary-only listings preserved: %s.",
            f"{int((~enriched_master['detailed_source_available']).sum()):,}",
        )

    LOGGER.info(
        "Calendar unavailability is stored only as an "
        "'unavailability_rate_proxy' and is not claimed as true occupancy."
    )

    del (
        detailed_attributes,
        review_aggregates,
        calendar_aggregates,
        enriched_master,
        enrichment_summary_df,
    )

    gc.collect()


if __name__ == "__main__":
    main()

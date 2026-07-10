
from __future__ import annotations

import gc
import logging
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
WAREHOUSE_DIR = PROJECT_ROOT / "data" / "warehouse"
QUALITY_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "data_quality"
DUCKDB_TEMP_DIR = QUALITY_OUTPUT_DIR / "duckdb_temp"

ENRICHED_MASTER_PATH = PROCESSED_DIR / "enriched_listing_master.parquet"
REVIEW_AGGREGATES_PATH = PROCESSED_DIR / "review_listing_aggregates.parquet"
CALENDAR_AGGREGATES_PATH = PROCESSED_DIR / "calendar_listing_aggregates.parquet"

WAREHOUSE_PATH = WAREHOUSE_DIR / "airbnb_analytics.duckdb"
WAREHOUSE_SUMMARY_PATH = QUALITY_OUTPUT_DIR / "warehouse_summary.csv"


# ---------------------------------------------------------------------------
# Expected validated counts
# ---------------------------------------------------------------------------

EXPECTED_CANONICAL_LISTING_COUNT = 10_465
EXPECTED_REVIEWED_LISTING_COUNT = 9_432
EXPECTED_CALENDAR_LISTING_COUNT = 10_465
EXPECTED_TOTAL_REVIEW_EVENTS = 545_162
EXPECTED_TOTAL_CALENDAR_ROWS = 3_819_725
EXPECTED_NEIGHBOURHOOD_COUNT = 22


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

WAREHOUSE_SUMMARY: list[dict[str, Any]] = []


def record_metric(
    *,
    object_name: str,
    metric: str,
    value: Any,
    expected_value: Any,
    status: str,
    notes: str,
) -> None:
    WAREHOUSE_SUMMARY.append(
        {
            "object_name": object_name,
            "metric": metric,
            "value": value,
            "expected_value": expected_value,
            "status": status,
            "notes": notes,
        }
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"Required processed input was not found: {path}"
        )


def escape_sql_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def create_duckdb_connection() -> duckdb.DuckDBPyConnection:
    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    DUCKDB_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(database=str(WAREHOUSE_PATH))

    con.execute("SET memory_limit = '3GB'")
    con.execute("SET preserve_insertion_order = false")

    temp_directory = escape_sql_path(DUCKDB_TEMP_DIR)
    con.execute(f"SET temp_directory = '{temp_directory}'")

    return con


def get_row_count(
    con: duckdb.DuckDBPyConnection,
    object_name: str,
) -> int:
    return int(
        con.execute(
            f'SELECT COUNT(*) FROM "{object_name}"'
        ).fetchone()[0]
    )


def get_distinct_count(
    con: duckdb.DuckDBPyConnection,
    object_name: str,
    column_name: str,
) -> int:
    return int(
        con.execute(
            f'''
            SELECT COUNT(DISTINCT "{column_name}")
            FROM "{object_name}"
            WHERE "{column_name}" IS NOT NULL
            '''
        ).fetchone()[0]
    )


def get_null_count(
    con: duckdb.DuckDBPyConnection,
    object_name: str,
    column_name: str,
) -> int:
    return int(
        con.execute(
            f'''
            SELECT COUNT(*)
            FROM "{object_name}"
            WHERE "{column_name}" IS NULL
            '''
        ).fetchone()[0]
    )


def get_duplicate_key_rows(
    con: duckdb.DuckDBPyConnection,
    object_name: str,
    key_column: str,
) -> int:
    return int(
        con.execute(
            f'''
            SELECT COALESCE(SUM(group_size), 0)
            FROM (
                SELECT
                    "{key_column}",
                    COUNT(*) AS group_size
                FROM "{object_name}"
                WHERE "{key_column}" IS NOT NULL
                GROUP BY "{key_column}"
                HAVING COUNT(*) > 1
            )
            '''
        ).fetchone()[0]
    )


def validate_equal(
    *,
    object_name: str,
    metric: str,
    actual: int,
    expected: int,
    notes: str,
) -> None:
    status = "PASS" if actual == expected else "FAIL"

    record_metric(
        object_name=object_name,
        metric=metric,
        value=actual,
        expected_value=expected,
        status=status,
        notes=notes,
    )

    if actual != expected:
        raise ValueError(
            f"{object_name}: validation failed for '{metric}'. "
            f"Expected {expected:,}, found {actual:,}."
        )


# ---------------------------------------------------------------------------
# Build physical tables
# ---------------------------------------------------------------------------

def build_enriched_master_table(
    con: duckdb.DuckDBPyConnection,
) -> None:
    LOGGER.info("Creating enriched_listing_master table...")

    path = escape_sql_path(ENRICHED_MASTER_PATH)

    con.execute(
        f'''
        CREATE OR REPLACE TABLE enriched_listing_master AS
        SELECT *
        FROM read_parquet('{path}')
        '''
    )


def build_dim_listings(
    con: duckdb.DuckDBPyConnection,
) -> None:
    LOGGER.info("Creating dim_listings table...")

    con.execute(
        '''
        CREATE OR REPLACE TABLE dim_listings AS
        SELECT
            id AS listing_id,
            name,
            host_id,
            host_name,
            neighbourhood_group,
            neighbourhood,
            latitude,
            longitude,
            room_type,
            detailed_property_type AS property_type,
            accommodates,
            bathrooms,
            bedrooms,
            beds,
            minimum_nights,
            maximum_nights,
            availability_365,
            calculated_host_listings_count,
            host_portfolio_size,
            host_portfolio_segment,
            host_is_superhost,
            host_has_profile_pic,
            host_identity_verified,
            detailed_source_available,
            price,
            detailed_price,
            price_best_available,
            price_source,
            price_per_bedroom,
            price_per_guest,
            review_scores_rating,
            review_scores_cleanliness,
            review_scores_location,
            has_review_history,
            calendar_data_available
        FROM enriched_listing_master
        '''
    )


def build_dim_neighbourhoods(
    con: duckdb.DuckDBPyConnection,
) -> None:
    LOGGER.info("Creating dim_neighbourhoods table...")

    con.execute(
        '''
        CREATE OR REPLACE TABLE dim_neighbourhoods AS
        SELECT
            ROW_NUMBER() OVER (
                ORDER BY neighbourhood
            )::INTEGER AS neighbourhood_key,

            neighbourhood,

            COUNT(*)::BIGINT AS listing_count,

            COUNT(price_best_available)::BIGINT
                AS listings_with_price,

            ROUND(
                AVG(price_best_available),
                2
            ) AS avg_price_best_available,

            ROUND(
                MEDIAN(price_best_available),
                2
            ) AS median_price_best_available

        FROM enriched_listing_master

        WHERE neighbourhood IS NOT NULL

        GROUP BY neighbourhood

        ORDER BY neighbourhood
        '''
    )


def build_fact_review_activity(
    con: duckdb.DuckDBPyConnection,
) -> None:
    LOGGER.info("Creating fact_review_activity table...")

    path = escape_sql_path(REVIEW_AGGREGATES_PATH)

    con.execute(
        f'''
        CREATE OR REPLACE TABLE fact_review_activity AS
        SELECT *
        FROM read_parquet('{path}')
        '''
    )


def build_fact_calendar_activity(
    con: duckdb.DuckDBPyConnection,
) -> None:
    LOGGER.info("Creating fact_calendar_activity table...")

    path = escape_sql_path(CALENDAR_AGGREGATES_PATH)

    con.execute(
        f'''
        CREATE OR REPLACE TABLE fact_calendar_activity AS
        SELECT *
        FROM read_parquet('{path}')
        '''
    )


# ---------------------------------------------------------------------------
# Analytical views
# ---------------------------------------------------------------------------

def build_analytical_views(
    con: duckdb.DuckDBPyConnection,
) -> None:
    LOGGER.info("Creating analytical views...")

    con.execute(
        '''
        CREATE OR REPLACE VIEW vw_neighbourhood_performance AS
        SELECT
            neighbourhood,

            COUNT(*)::BIGINT AS listing_count,

            COUNT(price_best_available)::BIGINT
                AS listings_with_price,

            ROUND(
                AVG(price_best_available),
                2
            ) AS avg_price,

            ROUND(
                MEDIAN(price_best_available),
                2
            ) AS median_price,

            ROUND(
                AVG(review_scores_rating),
                3
            ) AS avg_review_score,

            SUM(detailed_review_count)::BIGINT
                AS total_review_events,

            ROUND(
                AVG(detailed_review_count),
                2
            ) AS avg_reviews_per_listing,

            ROUND(
                AVG(availability_rate_observed),
                4
            ) AS avg_availability_rate,

            ROUND(
                AVG(unavailability_rate_proxy),
                4
            ) AS avg_unavailability_rate_proxy

        FROM enriched_listing_master

        WHERE neighbourhood IS NOT NULL

        GROUP BY neighbourhood
        '''
    )

    con.execute(
        '''
        CREATE OR REPLACE VIEW vw_room_type_performance AS
        SELECT
            room_type,

            COUNT(*)::BIGINT AS listing_count,

            COUNT(price_best_available)::BIGINT
                AS listings_with_price,

            ROUND(
                AVG(price_best_available),
                2
            ) AS avg_price,

            ROUND(
                MEDIAN(price_best_available),
                2
            ) AS median_price,

            ROUND(
                AVG(review_scores_rating),
                3
            ) AS avg_review_score,

            SUM(detailed_review_count)::BIGINT
                AS total_review_events,

            ROUND(
                AVG(unavailability_rate_proxy),
                4
            ) AS avg_unavailability_rate_proxy

        FROM enriched_listing_master

        WHERE room_type IS NOT NULL

        GROUP BY room_type
        '''
    )

    con.execute(
        '''
        CREATE OR REPLACE VIEW vw_host_portfolio_performance AS
        SELECT
            host_portfolio_segment,

            COUNT(*)::BIGINT AS listing_count,

            COUNT(price_best_available)::BIGINT
                AS listings_with_price,

            ROUND(
                AVG(price_best_available),
                2
            ) AS avg_price,

            ROUND(
                MEDIAN(price_best_available),
                2
            ) AS median_price,

            ROUND(
                AVG(review_scores_rating),
                3
            ) AS avg_review_score,

            ROUND(
                AVG(detailed_review_count),
                2
            ) AS avg_reviews_per_listing,

            ROUND(
                AVG(unavailability_rate_proxy),
                4
            ) AS avg_unavailability_rate_proxy

        FROM enriched_listing_master

        WHERE host_portfolio_segment IS NOT NULL

        GROUP BY host_portfolio_segment
        '''
    )


# ---------------------------------------------------------------------------
# Warehouse metadata
# ---------------------------------------------------------------------------

def build_metadata_table(
    con: duckdb.DuckDBPyConnection,
) -> None:
    LOGGER.info("Creating warehouse_metadata table...")

    con.execute(
        '''
        CREATE OR REPLACE TABLE warehouse_metadata (
            object_name VARCHAR,
            object_type VARCHAR,
            grain VARCHAR,
            description VARCHAR
        )
        '''
    )

    rows = [
        (
            "enriched_listing_master",
            "TABLE",
            "one row per canonical listing",
            "Full analysis-ready listing master.",
        ),
        (
            "dim_listings",
            "TABLE",
            "one row per canonical listing",
            "Compact listing dimension for analytical SQL.",
        ),
        (
            "dim_neighbourhoods",
            "TABLE",
            "one row per neighbourhood",
            "Neighbourhood-level dimension and summary metrics.",
        ),
        (
            "fact_review_activity",
            "TABLE",
            "one row per listing with review history",
            "Listing-level detailed review aggregates.",
        ),
        (
            "fact_calendar_activity",
            "TABLE",
            "one row per canonical listing",
            "Listing-level calendar aggregates; unavailability is a proxy, not verified occupancy.",
        ),
        (
            "vw_neighbourhood_performance",
            "VIEW",
            "one row per neighbourhood",
            "Reusable neighbourhood-level analytical view.",
        ),
        (
            "vw_room_type_performance",
            "VIEW",
            "one row per room type",
            "Reusable room-type analytical view.",
        ),
        (
            "vw_host_portfolio_performance",
            "VIEW",
            "one row per host portfolio segment",
            "Reusable host-segment analytical view.",
        ),
    ]

    con.executemany(
        '''
        INSERT INTO warehouse_metadata
        VALUES (?, ?, ?, ?)
        ''',
        rows,
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_warehouse(
    con: duckdb.DuckDBPyConnection,
) -> None:
    LOGGER.info("Validating warehouse tables and views...")

    master_rows = get_row_count(
        con,
        "enriched_listing_master",
    )

    validate_equal(
        object_name="enriched_listing_master",
        metric="row_count",
        actual=master_rows,
        expected=EXPECTED_CANONICAL_LISTING_COUNT,
        notes="Final master must preserve all canonical listings.",
    )

    master_unique_ids = get_distinct_count(
        con,
        "enriched_listing_master",
        "id",
    )

    validate_equal(
        object_name="enriched_listing_master",
        metric="unique_listing_ids",
        actual=master_unique_ids,
        expected=EXPECTED_CANONICAL_LISTING_COUNT,
        notes="Each canonical listing ID must appear exactly once.",
    )

    master_null_ids = get_null_count(
        con,
        "enriched_listing_master",
        "id",
    )

    validate_equal(
        object_name="enriched_listing_master",
        metric="null_listing_ids",
        actual=master_null_ids,
        expected=0,
        notes="Listing IDs must never be null.",
    )

    master_duplicate_rows = get_duplicate_key_rows(
        con,
        "enriched_listing_master",
        "id",
    )

    validate_equal(
        object_name="enriched_listing_master",
        metric="duplicate_listing_id_rows",
        actual=master_duplicate_rows,
        expected=0,
        notes="The final master must remain one row per listing.",
    )

    dim_listing_rows = get_row_count(
        con,
        "dim_listings",
    )

    validate_equal(
        object_name="dim_listings",
        metric="row_count",
        actual=dim_listing_rows,
        expected=EXPECTED_CANONICAL_LISTING_COUNT,
        notes="Listing dimension must preserve canonical grain.",
    )

    dim_unique_ids = get_distinct_count(
        con,
        "dim_listings",
        "listing_id",
    )

    validate_equal(
        object_name="dim_listings",
        metric="unique_listing_ids",
        actual=dim_unique_ids,
        expected=EXPECTED_CANONICAL_LISTING_COUNT,
        notes="Listing dimension key must be unique.",
    )

    neighbourhood_rows = get_row_count(
        con,
        "dim_neighbourhoods",
    )

    validate_equal(
        object_name="dim_neighbourhoods",
        metric="row_count",
        actual=neighbourhood_rows,
        expected=EXPECTED_NEIGHBOURHOOD_COUNT,
        notes="Amsterdam neighbourhood dimension should contain 22 rows.",
    )

    review_rows = get_row_count(
        con,
        "fact_review_activity",
    )

    validate_equal(
        object_name="fact_review_activity",
        metric="row_count",
        actual=review_rows,
        expected=EXPECTED_REVIEWED_LISTING_COUNT,
        notes="One row per listing with at least one detailed review.",
    )

    review_total_events = int(
        con.execute(
            '''
            SELECT
                COALESCE(
                    SUM(detailed_review_count),
                    0
                )
            FROM fact_review_activity
            '''
        ).fetchone()[0]
    )

    validate_equal(
        object_name="fact_review_activity",
        metric="total_detailed_review_events",
        actual=review_total_events,
        expected=EXPECTED_TOTAL_REVIEW_EVENTS,
        notes="All detailed review events must reconcile to the source total.",
    )

    review_duplicate_rows = get_duplicate_key_rows(
        con,
        "fact_review_activity",
        "listing_id",
    )

    validate_equal(
        object_name="fact_review_activity",
        metric="duplicate_listing_id_rows",
        actual=review_duplicate_rows,
        expected=0,
        notes="Review fact table must remain one row per reviewed listing.",
    )

    calendar_rows = get_row_count(
        con,
        "fact_calendar_activity",
    )

    validate_equal(
        object_name="fact_calendar_activity",
        metric="row_count",
        actual=calendar_rows,
        expected=EXPECTED_CALENDAR_LISTING_COUNT,
        notes="Calendar fact table should contain one row per canonical listing.",
    )

    calendar_total_rows = int(
        con.execute(
            '''
            SELECT
                COALESCE(
                    SUM(calendar_days_observed),
                    0
                )
            FROM fact_calendar_activity
            '''
        ).fetchone()[0]
    )

    validate_equal(
        object_name="fact_calendar_activity",
        metric="total_calendar_rows_represented",
        actual=calendar_total_rows,
        expected=EXPECTED_TOTAL_CALENDAR_ROWS,
        notes="All source calendar rows must be represented.",
    )

    complete_calendar_windows = int(
        con.execute(
            '''
            SELECT COUNT(*)
            FROM fact_calendar_activity
            WHERE calendar_complete_365_day_window IS TRUE
            '''
        ).fetchone()[0]
    )

    validate_equal(
        object_name="fact_calendar_activity",
        metric="complete_365_day_windows",
        actual=complete_calendar_windows,
        expected=EXPECTED_CALENDAR_LISTING_COUNT,
        notes="Each canonical listing should have a complete 365-day calendar window.",
    )

    calendar_duplicate_rows = get_duplicate_key_rows(
        con,
        "fact_calendar_activity",
        "listing_id",
    )

    validate_equal(
        object_name="fact_calendar_activity",
        metric="duplicate_listing_id_rows",
        actual=calendar_duplicate_rows,
        expected=0,
        notes="Calendar fact table must remain one row per listing.",
    )

    view_names = [
        "vw_neighbourhood_performance",
        "vw_room_type_performance",
        "vw_host_portfolio_performance",
    ]

    for view_name in view_names:
        row_count = get_row_count(
            con,
            view_name,
        )

        status = "PASS" if row_count > 0 else "FAIL"

        record_metric(
            object_name=view_name,
            metric="row_count",
            value=row_count,
            expected_value="> 0",
            status=status,
            notes="Reusable analytical view must return at least one row.",
        )

        if row_count <= 0:
            raise ValueError(
                f"{view_name}: analytical view returned no rows."
            )


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    required_inputs = [
        ENRICHED_MASTER_PATH,
        REVIEW_AGGREGATES_PATH,
        CALENDAR_AGGREGATES_PATH,
    ]

    for path in required_inputs:
        require_file(path)

    WAREHOUSE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    QUALITY_OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    WAREHOUSE_SUMMARY.clear()

    LOGGER.info("Starting DuckDB analytical warehouse build.")
    LOGGER.info("Warehouse path: %s", WAREHOUSE_PATH)

    con = create_duckdb_connection()

    try:
        build_enriched_master_table(con)
        build_dim_listings(con)
        build_dim_neighbourhoods(con)
        build_fact_review_activity(con)
        build_fact_calendar_activity(con)

        build_analytical_views(con)
        build_metadata_table(con)

        validate_warehouse(con)

        con.execute("CHECKPOINT")

    finally:
        con.close()
        gc.collect()

    summary_df = pd.DataFrame(
        WAREHOUSE_SUMMARY
    )

    summary_df.to_csv(
        WAREHOUSE_SUMMARY_PATH,
        index=False,
        encoding="utf-8",
    )

    LOGGER.info(
        "Saved: %s",
        WAREHOUSE_SUMMARY_PATH,
    )

    fail_count = int(
        (summary_df["status"] == "FAIL").sum()
    )

    pass_count = int(
        (summary_df["status"] == "PASS").sum()
    )

    LOGGER.info(
        "Warehouse validation finished: %s PASS, %s FAIL.",
        pass_count,
        fail_count,
    )

    if fail_count > 0:
        raise RuntimeError(
            "Warehouse build completed with failed validation checks. "
            "Review warehouse_summary.csv."
        )

    LOGGER.info(
        "DuckDB analytical warehouse built successfully."
    )

    LOGGER.info(
        "Canonical listing grain preserved: %s rows.",
        f"{EXPECTED_CANONICAL_LISTING_COUNT:,}",
    )

    LOGGER.info(
        "Review events reconciled: %s.",
        f"{EXPECTED_TOTAL_REVIEW_EVENTS:,}",
    )

    LOGGER.info(
        "Calendar rows reconciled: %s.",
        f"{EXPECTED_TOTAL_CALENDAR_ROWS:,}",
    )

    LOGGER.info(
        "Calendar unavailability remains labeled only as a proxy and is not "
        "treated as verified occupancy."
    )


if __name__ == "__main__":
    main()

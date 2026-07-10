"""
Cleaning and standardization for the Amsterdam Airbnb project.

This module cleans the two listing-level source datasets:

    data/raw/amsterdam/listings.csv
        -> data/processed/cleaned_listings.parquet

    data/raw/amsterdam/listings.csv.gz
        -> data/processed/cleaned_detailed_listings.parquet

It also creates:

    outputs/data_quality/cleaning_summary.csv

Design principles:
- Preserve raw source files unchanged.
- Preserve the canonical 10,465-row summary listing population.
- Do not replace missing prices with zero.
- Use context-aware, conservative missing-value handling.
- Standardize prices, dates, booleans, numerics, and categories.
- Keep the cleaning stage separate from enrichment.
- Remain safe for an 8 GB RAM laptop.
"""

from __future__ import annotations

import gc
import logging
from pathlib import Path
from typing import Any

import pandas as pd


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "amsterdam"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
QUALITY_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "data_quality"

SUMMARY_LISTINGS_PATH = RAW_DIR / "listings.csv"
DETAILED_LISTINGS_PATH = RAW_DIR / "listings.csv.gz"

CLEANED_LISTINGS_PATH = PROCESSED_DIR / "cleaned_listings.parquet"
CLEANED_DETAILED_LISTINGS_PATH = (
    PROCESSED_DIR / "cleaned_detailed_listings.parquet"
)

CLEANING_SUMMARY_PATH = QUALITY_OUTPUT_DIR / "cleaning_summary.csv"


# ---------------------------------------------------------------------------
# Expected structural facts from validated familiarization
# ---------------------------------------------------------------------------

EXPECTED_SUMMARY_ROW_COUNT = 10_465
EXPECTED_DETAILED_ROW_COUNT = 10_369


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cleaning configuration
# ---------------------------------------------------------------------------

SUMMARY_DATE_COLUMNS = {
    "last_review",
}

DETAILED_DATE_COLUMNS = {
    "last_scraped",
    "host_since",
    "calendar_last_scraped",
    "first_review",
    "last_review",
}

CATEGORY_COLUMNS = {
    "room_type",
    "property_type",
    "neighbourhood",
    "neighbourhood_cleansed",
    "neighbourhood_group",
    "host_response_time",
}

BOOLEAN_COLUMNS = {
    "host_is_superhost",
    "host_has_profile_pic",
    "host_identity_verified",
    "has_availability",
    "instant_bookable",
}

PERCENTAGE_COLUMNS = {
    "host_response_rate",
    "host_acceptance_rate",
}

SUMMARY_INTEGER_COLUMNS = {
    "id",
    "host_id",
    "minimum_nights",
    "number_of_reviews",
    "calculated_host_listings_count",
    "availability_365",
    "number_of_reviews_ltm",
    "number_of_reviews_l30d",
}

DETAILED_INTEGER_COLUMNS = {
    "id",
    "scrape_id",
    "host_id",
    "host_listings_count",
    "host_total_listings_count",
    "accommodates",
    "bedrooms",
    "beds",
    "minimum_nights",
    "maximum_nights",
    "minimum_minimum_nights",
    "maximum_minimum_nights",
    "minimum_maximum_nights",
    "maximum_maximum_nights",
    "number_of_reviews",
    "number_of_reviews_ltm",
    "number_of_reviews_l30d",
    "calculated_host_listings_count",
    "calculated_host_listings_count_entire_homes",
    "calculated_host_listings_count_private_rooms",
    "calculated_host_listings_count_shared_rooms",
    "availability_30",
    "availability_60",
    "availability_90",
    "availability_365",
}

FLOAT_COLUMNS = {
    "latitude",
    "longitude",
    "bathrooms",
    "reviews_per_month",
    "review_scores_rating",
    "review_scores_accuracy",
    "review_scores_cleanliness",
    "review_scores_checkin",
    "review_scores_communication",
    "review_scores_location",
    "review_scores_value",
}


# ---------------------------------------------------------------------------
# Cleaning summary collector
# ---------------------------------------------------------------------------

CLEANING_SUMMARY: list[dict[str, Any]] = []


def record_cleaning_action(
    *,
    dataset_name: str,
    column_name: str,
    action: str,
    affected_rows: int,
    notes: str,
) -> None:
    """Append one auditable cleaning action to the summary report."""
    CLEANING_SUMMARY.append(
        {
            "dataset_name": dataset_name,
            "column_name": column_name,
            "action": action,
            "affected_rows": int(affected_rows),
            "notes": notes,
        }
    )


# ---------------------------------------------------------------------------
# General helper functions
# ---------------------------------------------------------------------------

def require_file(path: Path) -> None:
    """Raise a clear error if a required raw source file is missing."""
    if not path.exists():
        raise FileNotFoundError(
            f"Required raw source file was not found: {path}"
        )


def normalize_blank_strings(
    df: pd.DataFrame,
    *,
    dataset_name: str,
) -> pd.DataFrame:
    """
    Convert whitespace-only strings to missing values.

    Meaningful text is preserved. Raw source data remains unchanged.
    """
    string_like_columns = [
        column
        for column in df.columns
        if (
            pd.api.types.is_object_dtype(df[column])
            or pd.api.types.is_string_dtype(df[column])
        )
    ]

    for column in string_like_columns:
        series = df[column]

        blank_mask = (
            series.notna()
            & series.astype("string").str.strip().eq("")
        )

        affected_rows = int(blank_mask.sum())

        if affected_rows > 0:
            df.loc[blank_mask, column] = pd.NA

            record_cleaning_action(
                dataset_name=dataset_name,
                column_name=column,
                action="blank_string_to_null",
                affected_rows=affected_rows,
                notes=(
                    "Whitespace-only strings were converted to null. "
                    "Non-empty text was preserved."
                ),
            )

    return df


def clean_price_column(
    df: pd.DataFrame,
    *,
    dataset_name: str,
    column_name: str = "price",
) -> pd.DataFrame:
    """
    Parse a currency-formatted price column into numeric form.

    Example:
        "$1,250.00" -> 1250.00

    The original raw representation is retained in `<column>_raw`.
    Missing values remain missing and are never converted to zero.
    """
    if column_name not in df.columns:
        return df

    raw_column_name = f"{column_name}_raw"

    if raw_column_name not in df.columns:
        insert_position = df.columns.get_loc(column_name)
        df.insert(
            insert_position,
            raw_column_name,
            df[column_name].copy(),
        )

    original_non_null = int(df[column_name].notna().sum())

    parsed = pd.to_numeric(
        df[column_name]
        .astype("string")
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip(),
        errors="coerce",
    )

    parse_failures = int(
        (
            df[column_name].notna()
            & parsed.isna()
        ).sum()
    )

    df[column_name] = parsed.astype("Float64")

    record_cleaning_action(
        dataset_name=dataset_name,
        column_name=column_name,
        action="currency_to_numeric",
        affected_rows=original_non_null - parse_failures,
        notes=(
            "Currency symbols and thousands separators were removed. "
            "Missing prices remain null. Original values are preserved in "
            f"'{raw_column_name}'."
        ),
    )

    if parse_failures > 0:
        record_cleaning_action(
            dataset_name=dataset_name,
            column_name=column_name,
            action="unparseable_price_to_null",
            affected_rows=parse_failures,
            notes=(
                "Non-null price strings that could not be parsed were "
                "converted to null for review."
            ),
        )

    return df


def standardize_dates(
    df: pd.DataFrame,
    *,
    dataset_name: str,
    date_columns: set[str],
) -> pd.DataFrame:
    """
    Parse configured date columns using Pandas datetime.

    Invalid non-null values become NaT and are recorded.
    """
    for column in sorted(date_columns):
        if column not in df.columns:
            continue

        original_non_null = df[column].notna()

        parsed = pd.to_datetime(
            df[column],
            errors="coerce",
        )

        invalid_count = int(
            (
                original_non_null
                & parsed.isna()
            ).sum()
        )

        parsed_count = int(
            (
                original_non_null
                & parsed.notna()
            ).sum()
        )

        df[column] = parsed

        record_cleaning_action(
            dataset_name=dataset_name,
            column_name=column,
            action="parse_datetime",
            affected_rows=parsed_count,
            notes=(
                "Non-null parseable date values were converted to "
                "datetime64[ns]."
            ),
        )

        if invalid_count > 0:
            record_cleaning_action(
                dataset_name=dataset_name,
                column_name=column,
                action="invalid_date_to_nat",
                affected_rows=invalid_count,
                notes=(
                    "Non-null values that could not be parsed were converted "
                    "to NaT for review."
                ),
            )

    return df


def standardize_categories(
    df: pd.DataFrame,
    *,
    dataset_name: str,
) -> pd.DataFrame:
    """
    Trim surrounding whitespace from selected categorical fields.

    Category labels are not arbitrarily remapped because current validation
    already confirmed expected room-type values.
    """
    for column in sorted(CATEGORY_COLUMNS):
        if column not in df.columns:
            continue

        original = df[column].astype("string")
        cleaned = original.str.strip()

        changed = int(
            (
                original.notna()
                & cleaned.notna()
                & original.ne(cleaned)
            ).sum()
        )

        df[column] = cleaned

        record_cleaning_action(
            dataset_name=dataset_name,
            column_name=column,
            action="trim_category_whitespace",
            affected_rows=changed,
            notes=(
                "Leading and trailing whitespace was removed. "
                "Category meanings were otherwise preserved."
            ),
        )

    return df


def standardize_boolean_columns(
    df: pd.DataFrame,
    *,
    dataset_name: str,
) -> pd.DataFrame:
    """
    Convert common Airbnb Boolean representations into Pandas nullable Boolean.

    Accepted true values:
        t, true, 1, yes, y

    Accepted false values:
        f, false, 0, no, n

    Unknown non-null values become null and are recorded.
    """
    true_values = {"t", "true", "1", "yes", "y"}
    false_values = {"f", "false", "0", "no", "n"}

    for column in sorted(BOOLEAN_COLUMNS):
        if column not in df.columns:
            continue

        original = df[column]

        normalized = (
            original.astype("string")
            .str.strip()
            .str.lower()
        )

        result = pd.Series(
            pd.NA,
            index=df.index,
            dtype="boolean",
        )

        true_mask = normalized.isin(true_values)
        false_mask = normalized.isin(false_values)

        result.loc[true_mask] = True
        result.loc[false_mask] = False

        invalid_mask = (
            original.notna()
            & ~true_mask
            & ~false_mask
        )

        invalid_count = int(invalid_mask.sum())
        converted_count = int((true_mask | false_mask).sum())

        df[column] = result

        record_cleaning_action(
            dataset_name=dataset_name,
            column_name=column,
            action="normalize_boolean",
            affected_rows=converted_count,
            notes=(
                "Common Airbnb Boolean representations were converted to "
                "Pandas nullable Boolean values."
            ),
        )

        if invalid_count > 0:
            record_cleaning_action(
                dataset_name=dataset_name,
                column_name=column,
                action="unknown_boolean_to_null",
                affected_rows=invalid_count,
                notes=(
                    "Unknown non-null Boolean representations were converted "
                    "to null for review."
                ),
            )

    return df


def standardize_percentage_columns(
    df: pd.DataFrame,
    *,
    dataset_name: str,
) -> pd.DataFrame:
    """
    Convert percentage strings such as '95%' into numeric percentage points.

    Example:
        '95%' -> 95.0

    Missing values remain null.
    """
    for column in sorted(PERCENTAGE_COLUMNS):
        if column not in df.columns:
            continue

        original = df[column]

        parsed = pd.to_numeric(
            original.astype("string")
            .str.replace("%", "", regex=False)
            .str.strip(),
            errors="coerce",
        ).astype("Float64")

        parse_failures = int(
            (
                original.notna()
                & parsed.isna()
            ).sum()
        )

        converted_count = int(
            (
                original.notna()
                & parsed.notna()
            ).sum()
        )

        df[column] = parsed

        record_cleaning_action(
            dataset_name=dataset_name,
            column_name=column,
            action="percentage_to_numeric",
            affected_rows=converted_count,
            notes=(
                "Percentage strings were converted to numeric percentage "
                "points on a 0-100 scale."
            ),
        )

        if parse_failures > 0:
            record_cleaning_action(
                dataset_name=dataset_name,
                column_name=column,
                action="unparseable_percentage_to_null",
                affected_rows=parse_failures,
                notes=(
                    "Non-null percentage values that could not be parsed were "
                    "converted to null for review."
                ),
            )

    return df


def standardize_numeric_columns(
    df: pd.DataFrame,
    *,
    dataset_name: str,
    integer_columns: set[str],
) -> pd.DataFrame:
    """
    Convert configured integer and floating-point fields into nullable numerics.

    Non-null unparseable values become null and are recorded.
    """
    for column in sorted(integer_columns):
        if column not in df.columns:
            continue

        original = df[column]

        parsed = pd.to_numeric(
            original,
            errors="coerce",
        )

        parse_failures = int(
            (
                original.notna()
                & parsed.isna()
            ).sum()
        )

        # Use nullable Float64 when decimals are present; otherwise Int64.
        non_null_parsed = parsed.dropna()

        if (
            not non_null_parsed.empty
            and (non_null_parsed % 1 == 0).all()
        ):
            df[column] = parsed.astype("Int64")
            target_type = "Int64"
        else:
            df[column] = parsed.astype("Float64")
            target_type = "Float64"

        record_cleaning_action(
            dataset_name=dataset_name,
            column_name=column,
            action="convert_numeric",
            affected_rows=int(parsed.notna().sum()),
            notes=f"Converted to nullable {target_type}.",
        )

        if parse_failures > 0:
            record_cleaning_action(
                dataset_name=dataset_name,
                column_name=column,
                action="unparseable_numeric_to_null",
                affected_rows=parse_failures,
                notes=(
                    "Non-null values that could not be parsed numerically "
                    "were converted to null for review."
                ),
            )

    for column in sorted(FLOAT_COLUMNS):
        if column not in df.columns:
            continue

        original = df[column]

        parsed = pd.to_numeric(
            original,
            errors="coerce",
        ).astype("Float64")

        parse_failures = int(
            (
                original.notna()
                & parsed.isna()
            ).sum()
        )

        df[column] = parsed

        record_cleaning_action(
            dataset_name=dataset_name,
            column_name=column,
            action="convert_numeric",
            affected_rows=int(parsed.notna().sum()),
            notes="Converted to nullable Float64.",
        )

        if parse_failures > 0:
            record_cleaning_action(
                dataset_name=dataset_name,
                column_name=column,
                action="unparseable_numeric_to_null",
                affected_rows=parse_failures,
                notes=(
                    "Non-null values that could not be parsed numerically "
                    "were converted to null for review."
                ),
            )

    return df


def verify_listing_integrity(
    df: pd.DataFrame,
    *,
    dataset_name: str,
    expected_row_count: int,
) -> None:
    """
    Stop the pipeline if cleaning accidentally changes listing grain or key quality.
    """
    actual_row_count = len(df)

    if actual_row_count != expected_row_count:
        raise ValueError(
            f"{dataset_name}: expected {expected_row_count:,} rows after "
            f"cleaning, but found {actual_row_count:,}."
        )

    if "id" not in df.columns:
        raise ValueError(
            f"{dataset_name}: required primary-key candidate 'id' is missing."
        )

    null_ids = int(df["id"].isna().sum())
    duplicate_ids = int(df["id"].duplicated(keep=False).sum())

    if null_ids > 0:
        raise ValueError(
            f"{dataset_name}: found {null_ids:,} null listing IDs after "
            "cleaning."
        )

    if duplicate_ids > 0:
        raise ValueError(
            f"{dataset_name}: found {duplicate_ids:,} rows participating in "
            "duplicate listing-ID groups after cleaning."
        )


# ---------------------------------------------------------------------------
# Summary listings cleaning
# ---------------------------------------------------------------------------

def clean_summary_listings() -> pd.DataFrame:
    """
    Clean listings.csv while preserving all 10,465 canonical listings.
    """
    dataset_name = "listings.csv"

    LOGGER.info("Cleaning %s...", dataset_name)

    df = pd.read_csv(
        SUMMARY_LISTINGS_PATH,
        low_memory=False,
    )

    original_row_count = len(df)
    original_column_count = len(df.columns)

    df = normalize_blank_strings(
        df,
        dataset_name=dataset_name,
    )

    df = clean_price_column(
        df,
        dataset_name=dataset_name,
    )

    df = standardize_dates(
        df,
        dataset_name=dataset_name,
        date_columns=SUMMARY_DATE_COLUMNS,
    )

    df = standardize_categories(
        df,
        dataset_name=dataset_name,
    )

    df = standardize_numeric_columns(
        df,
        dataset_name=dataset_name,
        integer_columns=SUMMARY_INTEGER_COLUMNS,
    )

    verify_listing_integrity(
        df,
        dataset_name=dataset_name,
        expected_row_count=EXPECTED_SUMMARY_ROW_COUNT,
    )

    record_cleaning_action(
        dataset_name=dataset_name,
        column_name="*",
        action="row_count_preservation_check",
        affected_rows=0,
        notes=(
            f"Row count preserved at {original_row_count:,}. "
            "No canonical listings were dropped."
        ),
    )

    record_cleaning_action(
        dataset_name=dataset_name,
        column_name="*",
        action="column_count_report",
        affected_rows=len(df.columns) - original_column_count,
        notes=(
            f"Input columns: {original_column_count}. "
            f"Output columns: {len(df.columns)}. "
            "The additional column is the preserved raw price field when "
            "price exists."
        ),
    )

    return df


# ---------------------------------------------------------------------------
# Detailed listings cleaning
# ---------------------------------------------------------------------------

def clean_detailed_listings() -> pd.DataFrame:
    """
    Clean listings.csv.gz while preserving all 10,369 detailed listing rows.
    """
    dataset_name = "listings.csv.gz"

    LOGGER.info("Cleaning %s...", dataset_name)

    df = pd.read_csv(
        DETAILED_LISTINGS_PATH,
        low_memory=False,
    )

    original_row_count = len(df)
    original_column_count = len(df.columns)

    df = normalize_blank_strings(
        df,
        dataset_name=dataset_name,
    )

    df = clean_price_column(
        df,
        dataset_name=dataset_name,
    )

    df = standardize_dates(
        df,
        dataset_name=dataset_name,
        date_columns=DETAILED_DATE_COLUMNS,
    )

    df = standardize_categories(
        df,
        dataset_name=dataset_name,
    )

    df = standardize_boolean_columns(
        df,
        dataset_name=dataset_name,
    )

    df = standardize_percentage_columns(
        df,
        dataset_name=dataset_name,
    )

    df = standardize_numeric_columns(
        df,
        dataset_name=dataset_name,
        integer_columns=DETAILED_INTEGER_COLUMNS,
    )

    verify_listing_integrity(
        df,
        dataset_name=dataset_name,
        expected_row_count=EXPECTED_DETAILED_ROW_COUNT,
    )

    record_cleaning_action(
        dataset_name=dataset_name,
        column_name="*",
        action="row_count_preservation_check",
        affected_rows=0,
        notes=(
            f"Row count preserved at {original_row_count:,}. "
            "No detailed listing records were dropped."
        ),
    )

    record_cleaning_action(
        dataset_name=dataset_name,
        column_name="*",
        action="column_count_report",
        affected_rows=len(df.columns) - original_column_count,
        notes=(
            f"Input columns: {original_column_count}. "
            f"Output columns: {len(df.columns)}. "
            "The additional column is the preserved raw price field when "
            "price exists."
        ),
    )

    return df


# ---------------------------------------------------------------------------
# Output validation
# ---------------------------------------------------------------------------

def validate_output_files() -> None:
    """
    Re-read the generated Parquet outputs and verify row counts and unique IDs.
    """
    LOGGER.info("Validating generated Parquet outputs...")

    output_expectations = [
        (
            CLEANED_LISTINGS_PATH,
            "cleaned_listings.parquet",
            EXPECTED_SUMMARY_ROW_COUNT,
        ),
        (
            CLEANED_DETAILED_LISTINGS_PATH,
            "cleaned_detailed_listings.parquet",
            EXPECTED_DETAILED_ROW_COUNT,
        ),
    ]

    for path, dataset_name, expected_rows in output_expectations:
        if not path.exists():
            raise FileNotFoundError(
                f"Expected processed output was not created: {path}"
            )

        df = pd.read_parquet(
            path,
            columns=["id"],
        )

        if len(df) != expected_rows:
            raise ValueError(
                f"{dataset_name}: expected {expected_rows:,} rows, "
                f"but found {len(df):,}."
            )

        if df["id"].isna().any():
            raise ValueError(
                f"{dataset_name}: null listing IDs found after writing."
            )

        if df["id"].duplicated().any():
            raise ValueError(
                f"{dataset_name}: duplicate listing IDs found after writing."
            )

        LOGGER.info(
            "Verified %s: %s rows, unique non-null IDs.",
            dataset_name,
            f"{len(df):,}",
        )

        del df
        gc.collect()


# ---------------------------------------------------------------------------
# Main cleaning pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    """Run listing-level cleaning and save processed Parquet outputs."""
    require_file(SUMMARY_LISTINGS_PATH)
    require_file(DETAILED_LISTINGS_PATH)

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    QUALITY_OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    CLEANING_SUMMARY.clear()

    LOGGER.info("Starting cleaning and standardization.")
    LOGGER.info("Raw data directory: %s", RAW_DIR)
    LOGGER.info("Processed data directory: %s", PROCESSED_DIR)

    # ------------------------------------------------------------------
    # 1. Clean canonical summary listings
    # ------------------------------------------------------------------

    cleaned_summary = clean_summary_listings()

    cleaned_summary.to_parquet(
        CLEANED_LISTINGS_PATH,
        index=False,
        engine="pyarrow",
    )

    LOGGER.info(
        "Saved: %s",
        CLEANED_LISTINGS_PATH,
    )

    del cleaned_summary
    gc.collect()

    # ------------------------------------------------------------------
    # 2. Clean detailed listings
    # ------------------------------------------------------------------

    cleaned_detailed = clean_detailed_listings()

    cleaned_detailed.to_parquet(
        CLEANED_DETAILED_LISTINGS_PATH,
        index=False,
        engine="pyarrow",
    )

    LOGGER.info(
        "Saved: %s",
        CLEANED_DETAILED_LISTINGS_PATH,
    )

    del cleaned_detailed
    gc.collect()

    # ------------------------------------------------------------------
    # 3. Save cleaning audit summary
    # ------------------------------------------------------------------

    cleaning_summary_df = pd.DataFrame(CLEANING_SUMMARY)

    cleaning_summary_df.to_csv(
        CLEANING_SUMMARY_PATH,
        index=False,
        encoding="utf-8",
    )

    LOGGER.info(
        "Saved: %s",
        CLEANING_SUMMARY_PATH,
    )

    # ------------------------------------------------------------------
    # 4. Validate generated outputs
    # ------------------------------------------------------------------

    validate_output_files()

    LOGGER.info(
        "Cleaning completed successfully."
    )

    LOGGER.info(
        "Canonical summary listings preserved: %s rows.",
        f"{EXPECTED_SUMMARY_ROW_COUNT:,}",
    )

    LOGGER.info(
        "Detailed listings preserved: %s rows.",
        f"{EXPECTED_DETAILED_ROW_COUNT:,}",
    )

    LOGGER.info(
        "Missing prices were preserved as null; no zero-price imputation "
        "was performed."
    )


if __name__ == "__main__":
    main()

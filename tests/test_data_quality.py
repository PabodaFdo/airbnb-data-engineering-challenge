"""
High-value unit and integrity tests for the Amsterdam Airbnb
Data Engineering Challenge.

These tests focus on the most important engineering guarantees:

1. Price values are parsed correctly without inventing zero prices.
2. Raw price representations are preserved.
3. Dates are parsed safely.
4. Boolean fields are standardized consistently.
5. Listing-level primary keys remain unique and non-null.
6. Duplicate keys are rejected.
7. Enrichment-derived features are calculated correctly.
8. The saved enriched master preserves the canonical listing grain,
   when the local processed output is available.

Run from the project root with:

    python -m pytest tests/ -v
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.clean import (
    clean_price_column,
    standardize_boolean_columns,
    standardize_dates,
    verify_listing_integrity,
)
from src.enrich import (
    EXPECTED_CANONICAL_LISTING_COUNT,
    add_derived_features,
    ensure_unique_key,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

ENRICHED_MASTER_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "enriched_listing_master.parquet"
)


# ============================================================================
# Price cleaning tests
# ============================================================================


def test_clean_price_column_parses_currency_values() -> None:
    """
    Currency-formatted prices should become numeric values.

    Examples:
        "$1,250.00" -> 1250.00
        "$99.50"    -> 99.50
    """

    df = pd.DataFrame(
        {
            "price": [
                "$1,250.00",
                "$99.50",
                "$0.00",
            ]
        }
    )

    result = clean_price_column(
        df,
        dataset_name="test_prices",
    )

    assert result["price"].tolist() == [
        1250.0,
        99.5,
        0.0,
    ]


def test_clean_price_column_preserves_raw_values() -> None:
    """
    The original source representation should be preserved in price_raw.
    """

    df = pd.DataFrame(
        {
            "price": [
                "$1,250.00",
                "$99.50",
            ]
        }
    )

    result = clean_price_column(
        df,
        dataset_name="test_prices",
    )

    assert "price_raw" in result.columns

    assert result["price_raw"].tolist() == [
        "$1,250.00",
        "$99.50",
    ]


def test_clean_price_column_preserves_missing_as_null() -> None:
    """
    Missing prices must remain null rather than being incorrectly
    replaced with zero.
    """

    df = pd.DataFrame(
        {
            "price": [
                "$100.00",
                None,
            ]
        }
    )

    result = clean_price_column(
        df,
        dataset_name="test_prices",
    )

    assert result.loc[0, "price"] == 100.0

    assert pd.isna(
        result.loc[1, "price"]
    )


# ============================================================================
# Date standardization tests
# ============================================================================


def test_standardize_dates_parses_valid_dates() -> None:
    """
    Valid Airbnb date strings should become Pandas datetime values.
    """

    df = pd.DataFrame(
        {
            "last_review": [
                "2025-01-15",
                "2025-06-30",
            ]
        }
    )

    result = standardize_dates(
        df,
        dataset_name="test_dates",
        date_columns={"last_review"},
    )

    assert pd.api.types.is_datetime64_any_dtype(
        result["last_review"]
    )

    assert result.loc[
        0,
        "last_review",
    ] == pd.Timestamp("2025-01-15")


def test_standardize_dates_converts_invalid_values_to_nat() -> None:
    """
    Invalid non-null date strings should become NaT rather than
    crashing the pipeline or remaining misleading strings.
    """

    df = pd.DataFrame(
        {
            "last_review": [
                "2025-01-15",
                "not-a-valid-date",
            ]
        }
    )

    result = standardize_dates(
        df,
        dataset_name="test_dates",
        date_columns={"last_review"},
    )

    assert pd.isna(
        result.loc[1, "last_review"]
    )


# ============================================================================
# Boolean normalization tests
# ============================================================================


def test_standardize_boolean_columns_handles_common_airbnb_values() -> None:
    """
    Common true/false representations should become nullable Boolean values.
    """

    df = pd.DataFrame(
        {
            "host_is_superhost": [
                "t",
                "f",
                "true",
                "false",
                "yes",
                "no",
                None,
            ]
        }
    )

    result = standardize_boolean_columns(
        df,
        dataset_name="test_booleans",
    )

    expected = [
        True,
        False,
        True,
        False,
        True,
        False,
        pd.NA,
    ]

    assert result["host_is_superhost"].tolist() == expected

    assert str(
        result["host_is_superhost"].dtype
    ) == "boolean"


def test_unknown_boolean_value_becomes_null() -> None:
    """
    Unknown Boolean representations must not be guessed.
    """

    df = pd.DataFrame(
        {
            "host_is_superhost": [
                "t",
                "unknown-value",
            ]
        }
    )

    result = standardize_boolean_columns(
        df,
        dataset_name="test_booleans",
    )

    assert result.loc[
        0,
        "host_is_superhost",
    ] == True

    assert pd.isna(
        result.loc[
            1,
            "host_is_superhost",
        ]
    )


# ============================================================================
# Listing-grain integrity tests
# ============================================================================


def test_verify_listing_integrity_accepts_unique_non_null_ids() -> None:
    """
    A one-row-per-listing dataset with unique, non-null IDs should pass.
    """

    df = pd.DataFrame(
        {
            "id": [
                101,
                102,
                103,
            ]
        }
    )

    verify_listing_integrity(
        df,
        dataset_name="test_listings",
        expected_row_count=3,
    )


def test_verify_listing_integrity_rejects_duplicate_listing_ids() -> None:
    """
    Duplicate listing IDs should fail fast because they violate
    the intended listing-level grain.
    """

    df = pd.DataFrame(
        {
            "id": [
                101,
                101,
                103,
            ]
        }
    )

    with pytest.raises(
        ValueError,
        match="duplicate listing-ID",
    ):
        verify_listing_integrity(
            df,
            dataset_name="test_listings",
            expected_row_count=3,
        )


def test_verify_listing_integrity_rejects_null_listing_ids() -> None:
    """
    Null listing IDs should fail because the listing identifier
    is the primary-key candidate for the listing-level dataset.
    """

    df = pd.DataFrame(
        {
            "id": [
                101,
                None,
                103,
            ]
        }
    )

    with pytest.raises(
        ValueError,
        match="null listing IDs",
    ):
        verify_listing_integrity(
            df,
            dataset_name="test_listings",
            expected_row_count=3,
        )


def test_ensure_unique_key_rejects_duplicate_keys() -> None:
    """
    Enrichment inputs with duplicate listing keys must be rejected
    before one-to-one joins are attempted.
    """

    df = pd.DataFrame(
        {
            "listing_id": [
                1,
                1,
                2,
            ]
        }
    )

    with pytest.raises(
        ValueError,
        match="duplicate 'listing_id'",
    ):
        ensure_unique_key(
            df,
            dataset_name="test_aggregates",
            key_column="listing_id",
        )


# ============================================================================
# Derived-feature tests
# ============================================================================


def test_add_derived_features_creates_expected_business_features() -> None:
    """
    Verify several important enrichment rules:

    - Summary price is preferred when available.
    - Detailed price is used as fallback.
    - Price per bedroom is calculated only for positive bedroom counts.
    - Price per guest is calculated only for positive guest capacity.
    - Host portfolio segments are created correctly.
    - Missing review counts become zero.
    """

    df = pd.DataFrame(
        {
            "price": [
                200.0,
                pd.NA,
                150.0,
            ],
            "detailed_price": [
                190.0,
                120.0,
                145.0,
            ],
            "bedrooms": [
                2,
                1,
                0,
            ],
            "accommodates": [
                4,
                2,
                0,
            ],
            "calculated_host_listings_count": [
                1,
                3,
                10,
            ],
            "detailed_review_count": [
                5,
                pd.NA,
                20,
            ],
            "calendar_days_observed": [
                365,
                365,
                pd.NA,
            ],
        }
    )

    result = add_derived_features(df)

    # Summary price takes priority.
    assert result.loc[
        0,
        "price_best_available",
    ] == 200.0

    # Detailed price provides fallback.
    assert result.loc[
        1,
        "price_best_available",
    ] == 120.0

    assert result.loc[
        0,
        "price_source",
    ] == "summary_listings"

    assert result.loc[
        1,
        "price_source",
    ] == "detailed_listings"

    # Price efficiency.
    assert result.loc[
        0,
        "price_per_bedroom",
    ] == 100.0

    assert result.loc[
        0,
        "price_per_guest",
    ] == 50.0

    # Zero bedroom/capacity values must not create misleading ratios.
    assert pd.isna(
        result.loc[
            2,
            "price_per_bedroom",
        ]
    )

    assert pd.isna(
        result.loc[
            2,
            "price_per_guest",
        ]
    )

    # Host segmentation.
    assert result.loc[
        0,
        "host_portfolio_segment",
    ] == "Single-listing host"

    assert result.loc[
        1,
        "host_portfolio_segment",
    ] == "Small multi-listing host (2-5)"

    assert result.loc[
        2,
        "host_portfolio_segment",
    ] == "Large/professional host (6+)"

    # Missing review count becomes zero.
    assert result.loc[
        1,
        "detailed_review_count",
    ] == 0

    assert result.loc[
        1,
        "has_review_history",
    ] == False


# ============================================================================
# Processed-output integrity test
# ============================================================================


@pytest.mark.skipif(
    not ENRICHED_MASTER_PATH.exists(),
    reason=(
        "Local enriched_listing_master.parquet is not available. "
        "Run the pipeline first."
    ),
)
def test_saved_enriched_master_preserves_canonical_listing_grain() -> None:
    """
    Integration-style integrity check for the locally generated enriched master.

    The final dataset must contain exactly one row for every canonical listing.
    """

    df = pd.read_parquet(
        ENRICHED_MASTER_PATH,
        columns=["id"],
    )

    assert len(df) == EXPECTED_CANONICAL_LISTING_COUNT

    assert df["id"].notna().all()

    assert df["id"].is_unique
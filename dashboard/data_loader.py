from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]

ENRICHED_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "enriched_listing_master.parquet"
)

MODEL_RESULTS_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "modeling"
    / "price_model_results.csv"
)

FEATURE_IMPORTANCE_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "modeling"
    / "random_forest_feature_importance.csv"
)

MODEL_PREDICTIONS_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "modeling"
    / "price_model_predictions.csv"
)

STATISTICAL_RESULTS_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "statistics"
    / "tables"
    / "statistical_test_results.csv"
)


def _validate_file_exists(file_path: Path) -> None:
    """
    Raise a clear error when a required dashboard data file is missing.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Required dashboard file was not found:\n{file_path}\n\n"
            "Run the relevant pipeline or experiment first."
        )


@st.cache_data(show_spinner=False)
def load_enriched_listings() -> pd.DataFrame:
    """
    Load the enriched one-row-per-listing analytical dataset.
    """
    _validate_file_exists(ENRICHED_DATA_PATH)

    df = pd.read_parquet(ENRICHED_DATA_PATH)

    if "id" not in df.columns:
        raise ValueError(
            "Expected listing identifier column 'id' "
            "was not found in enriched_listing_master.parquet."
        )

    if df["id"].isna().any():
        raise ValueError(
            "The enriched listing dataset contains missing listing IDs."
        )

    if df["id"].duplicated().any():
        raise ValueError(
            "The enriched listing dataset does not preserve "
            "one row per canonical listing."
        )

    return df


@st.cache_data(show_spinner=False)
def load_model_results() -> pd.DataFrame:
    """
    Load model-comparison metrics.
    """
    _validate_file_exists(MODEL_RESULTS_PATH)
    return pd.read_csv(MODEL_RESULTS_PATH)


@st.cache_data(show_spinner=False)
def load_feature_importance() -> pd.DataFrame:
    """
    Load Random Forest feature-importance results.
    """
    _validate_file_exists(FEATURE_IMPORTANCE_PATH)
    return pd.read_csv(FEATURE_IMPORTANCE_PATH)


@st.cache_data(show_spinner=False)
def load_model_predictions() -> pd.DataFrame:
    """
    Load actual and predicted test-set prices.
    """
    _validate_file_exists(MODEL_PREDICTIONS_PATH)
    return pd.read_csv(MODEL_PREDICTIONS_PATH)


@st.cache_data(show_spinner=False)
def load_statistical_results() -> pd.DataFrame:
    """
    Load statistical hypothesis-test results.
    """
    _validate_file_exists(STATISTICAL_RESULTS_PATH)
    return pd.read_csv(STATISTICAL_RESULTS_PATH)


def get_available_data_sources() -> dict[str, bool]:
    """
    Return availability status for each dashboard data source.

    This is useful because the dashboard should still be able to show
    a clear message when an optional output file has not yet been generated.
    """
    return {
        "enriched_listings": ENRICHED_DATA_PATH.exists(),
        "model_results": MODEL_RESULTS_PATH.exists(),
        "feature_importance": FEATURE_IMPORTANCE_PATH.exists(),
        "model_predictions": MODEL_PREDICTIONS_PATH.exists(),
        "statistical_results": STATISTICAL_RESULTS_PATH.exists(),
    }
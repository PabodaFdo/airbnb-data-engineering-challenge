from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st


# ---------------------------------------------------------------------------
# Project path setup
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Local imports
# ---------------------------------------------------------------------------

from dashboard.charts import (  # noqa: E402
    create_actual_vs_predicted_chart,
    create_feature_importance_chart,
    create_listings_by_neighbourhood_chart,
    create_median_price_by_capacity_chart,
    create_median_price_by_neighbourhood_chart,
    create_median_price_by_room_type_chart,
    create_model_comparison_chart,
    create_price_distribution_chart,
    create_review_activity_by_neighbourhood_chart,
    create_unavailability_proxy_chart,
)

from dashboard.components import (  # noqa: E402
    render_data_quality_metrics,
    render_filter_summary,
    render_footer,
    render_hypothesis_card,
    render_market_overview_metrics,
    render_ml_caveat,
    render_ml_summary_metrics,
    render_page_header,
    render_price_caveat,
    render_project_status,
    render_review_caveat,
    render_secondary_market_metrics,
    render_section_header,
    render_unavailability_caveat,
    render_visualization_limit_caveat,
)

from dashboard.data_loader import (  # noqa: E402
    get_available_data_sources,
    load_enriched_listings,
    load_feature_importance,
    load_model_predictions,
    load_model_results,
    load_statistical_results,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ARCHITECTURE_IMAGE_PATH = (
    PROJECT_ROOT
    / "docs"
    / "architecture_diagram.png"
)

PRICE_COLUMN = "price_best_available"


# ---------------------------------------------------------------------------
# Streamlit page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Amsterdam Airbnb Market Explorer",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def normalize_boolean_label(value: object) -> str:
    """
    Convert common Boolean representations into readable dashboard labels.
    """
    if pd.isna(value):
        return "Missing"

    normalized = str(value).strip().lower()

    if normalized in {"true", "t", "1", "yes"}:
        return "Yes"

    if normalized in {"false", "f", "0", "no"}:
        return "No"

    return str(value)


def create_filter_options(
    df: pd.DataFrame,
    column_name: str,
) -> list[str]:
    """
    Return sorted unique non-null values for a sidebar filter.
    """
    if column_name not in df.columns:
        return []

    return (
        df[column_name]
        .dropna()
        .astype(str)
        .sort_values()
        .unique()
        .tolist()
    )


def apply_dashboard_filters(
    df: pd.DataFrame,
    selected_neighbourhoods: list[str],
    selected_room_types: list[str],
    selected_host_segments: list[str],
    selected_superhost_statuses: list[str],
    minimum_price: float | None,
    maximum_price: float | None,
    minimum_capacity: int | None,
    maximum_capacity: int | None,
) -> pd.DataFrame:
    """
    Apply all interactive sidebar filters.
    """
    filtered_df = df.copy()

    if (
        selected_neighbourhoods
        and "neighbourhood" in filtered_df.columns
    ):
        filtered_df = filtered_df[
            filtered_df["neighbourhood"]
            .astype(str)
            .isin(selected_neighbourhoods)
        ]

    if (
        selected_room_types
        and "room_type" in filtered_df.columns
    ):
        filtered_df = filtered_df[
            filtered_df["room_type"]
            .astype(str)
            .isin(selected_room_types)
        ]

    if (
        selected_host_segments
        and "host_portfolio_segment" in filtered_df.columns
    ):
        filtered_df = filtered_df[
            filtered_df["host_portfolio_segment"]
            .astype(str)
            .isin(selected_host_segments)
        ]

    if (
        selected_superhost_statuses
        and "host_is_superhost" in filtered_df.columns
    ):
        readable_superhost_status = (
            filtered_df["host_is_superhost"]
            .map(normalize_boolean_label)
        )

        filtered_df = filtered_df[
            readable_superhost_status.isin(
                selected_superhost_statuses
            )
        ]

    if PRICE_COLUMN in filtered_df.columns:
        numeric_price = pd.to_numeric(
            filtered_df[PRICE_COLUMN],
            errors="coerce",
        )

        if minimum_price is not None:
            filtered_df = filtered_df[
                numeric_price.isna()
                | (numeric_price >= minimum_price)
            ]

        if maximum_price is not None:
            numeric_price = pd.to_numeric(
                filtered_df[PRICE_COLUMN],
                errors="coerce",
            )

            filtered_df = filtered_df[
                numeric_price.isna()
                | (numeric_price <= maximum_price)
            ]

    if "accommodates" in filtered_df.columns:
        numeric_capacity = pd.to_numeric(
            filtered_df["accommodates"],
            errors="coerce",
        )

        if minimum_capacity is not None:
            filtered_df = filtered_df[
                numeric_capacity.isna()
                | (numeric_capacity >= minimum_capacity)
            ]

        if maximum_capacity is not None:
            numeric_capacity = pd.to_numeric(
                filtered_df["accommodates"],
                errors="coerce",
            )

            filtered_df = filtered_df[
                numeric_capacity.isna()
                | (numeric_capacity <= maximum_capacity)
            ]

    return filtered_df


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------


def render_sidebar_filters(
    df: pd.DataFrame,
) -> dict[str, object]:
    """
    Render all interactive dashboard filters in the sidebar.
    """
    st.sidebar.header("Market Filters")

    st.sidebar.caption(
        "Use these filters to explore subsets of the Amsterdam "
        "Airbnb listing market."
    )

    neighbourhood_options = create_filter_options(
        df,
        "neighbourhood",
    )

    room_type_options = create_filter_options(
        df,
        "room_type",
    )

    host_segment_options = create_filter_options(
        df,
        "host_portfolio_segment",
    )

    selected_neighbourhoods = st.sidebar.multiselect(
        "Neighbourhood",
        options=neighbourhood_options,
        default=[],
        placeholder="All neighbourhoods",
    )

    selected_room_types = st.sidebar.multiselect(
        "Room Type",
        options=room_type_options,
        default=[],
        placeholder="All room types",
    )

    selected_host_segments = st.sidebar.multiselect(
        "Host Portfolio Segment",
        options=host_segment_options,
        default=[],
        placeholder="All host segments",
    )

    selected_superhost_statuses: list[str] = []

    if "host_is_superhost" in df.columns:
        superhost_options = sorted(
            df["host_is_superhost"]
            .map(normalize_boolean_label)
            .dropna()
            .unique()
            .tolist()
        )

        selected_superhost_statuses = st.sidebar.multiselect(
            "Superhost Status",
            options=superhost_options,
            default=[],
            placeholder="All statuses",
        )

    minimum_price = None
    maximum_price = None

    if PRICE_COLUMN in df.columns:
        valid_prices = pd.to_numeric(
            df[PRICE_COLUMN],
            errors="coerce",
        )

        valid_prices = valid_prices[
            valid_prices.notna()
            & (valid_prices > 0)
        ]

        if not valid_prices.empty:
            observed_minimum = float(valid_prices.min())
            observed_maximum = float(valid_prices.max())

            selected_price_range = st.sidebar.slider(
                "Available Price Range (€)",
                min_value=observed_minimum,
                max_value=observed_maximum,
                value=(
                    observed_minimum,
                    observed_maximum,
                ),
                step=10.0,
            )

            minimum_price = selected_price_range[0]
            maximum_price = selected_price_range[1]

            st.sidebar.caption(
                "Missing prices remain null and are not treated as zero."
            )

    minimum_capacity = None
    maximum_capacity = None

    if "accommodates" in df.columns:
        capacity_values = pd.to_numeric(
            df["accommodates"],
            errors="coerce",
        )

        capacity_values = capacity_values[
            capacity_values.notna()
            & (capacity_values > 0)
        ]

        if not capacity_values.empty:
            observed_minimum_capacity = int(
                capacity_values.min()
            )

            observed_maximum_capacity = min(
                int(capacity_values.max()),
                16,
            )

            selected_capacity_range = st.sidebar.slider(
                "Guest Capacity",
                min_value=observed_minimum_capacity,
                max_value=observed_maximum_capacity,
                value=(
                    observed_minimum_capacity,
                    observed_maximum_capacity,
                ),
                step=1,
            )

            minimum_capacity = selected_capacity_range[0]
            maximum_capacity = selected_capacity_range[1]

    st.sidebar.divider()

    st.sidebar.caption(
        "Empty multi-select filters mean that all values are included."
    )

    return {
        "selected_neighbourhoods": selected_neighbourhoods,
        "selected_room_types": selected_room_types,
        "selected_host_segments": selected_host_segments,
        "selected_superhost_statuses": selected_superhost_statuses,
        "minimum_price": minimum_price,
        "maximum_price": maximum_price,
        "minimum_capacity": minimum_capacity,
        "maximum_capacity": maximum_capacity,
    }


# ---------------------------------------------------------------------------
# Optional data loading
# ---------------------------------------------------------------------------


def load_optional_dashboard_data(
    availability: dict[str, bool],
) -> dict[str, pd.DataFrame | None]:
    """
    Load optional dashboard outputs only when files exist.
    """
    optional_data: dict[str, pd.DataFrame | None] = {
        "model_results": None,
        "feature_importance": None,
        "model_predictions": None,
        "statistical_results": None,
    }

    if availability.get("model_results"):
        try:
            optional_data["model_results"] = (
                load_model_results()
            )
        except Exception as error:
            st.warning(
                "Model results could not be loaded: "
                f"{error}"
            )

    if availability.get("feature_importance"):
        try:
            optional_data["feature_importance"] = (
                load_feature_importance()
            )
        except Exception as error:
            st.warning(
                "Feature importance could not be loaded: "
                f"{error}"
            )

    if availability.get("model_predictions"):
        try:
            optional_data["model_predictions"] = (
                load_model_predictions()
            )
        except Exception as error:
            st.warning(
                "Model predictions could not be loaded: "
                f"{error}"
            )

    if availability.get("statistical_results"):
        try:
            optional_data["statistical_results"] = (
                load_statistical_results()
            )
        except Exception as error:
            st.warning(
                "Statistical results could not be loaded: "
                f"{error}"
            )

    return optional_data


# ---------------------------------------------------------------------------
# Overview tab
# ---------------------------------------------------------------------------


def render_overview_tab(
    original_df: pd.DataFrame,
    filtered_df: pd.DataFrame,
) -> None:
    """
    Render the market overview section.
    """
    render_section_header(
        "Market Overview",
        (
            "High-level indicators for the filtered Amsterdam "
            "Airbnb listing market."
        ),
    )

    render_filter_summary(
        original_df,
        filtered_df,
    )

    render_market_overview_metrics(filtered_df)

    st.write("")

    render_secondary_market_metrics(filtered_df)

    st.divider()

    left_column, right_column = st.columns(2)

    with left_column:
        st.plotly_chart(
            create_listings_by_neighbourhood_chart(
                filtered_df,
                top_n=15,
            ),
            width="stretch",
            key="overview_listings_by_neighbourhood",
        )

    with right_column:
        st.plotly_chart(
            create_median_price_by_room_type_chart(
                filtered_df,
            ),
            width="stretch",
            key="overview_median_price_by_room_type",
        )

    render_price_caveat()


# ---------------------------------------------------------------------------
# Market explorer tab
# ---------------------------------------------------------------------------


def render_market_explorer_tab(
    original_df: pd.DataFrame,
    filtered_df: pd.DataFrame,
) -> None:
    """
    Render interactive market exploration charts.
    """
    render_section_header(
        "Market Explorer",
        (
            "Explore neighbourhood supply, room types, capacity, "
            "and price patterns using the sidebar filters."
        ),
    )

    render_filter_summary(
        original_df,
        filtered_df,
    )

    first_column, second_column = st.columns(2)

    with first_column:
        st.plotly_chart(
            create_listings_by_neighbourhood_chart(
                filtered_df,
                top_n=15,
            ),
            width="stretch",
            key="explorer_listings_by_neighbourhood",
        )

    with second_column:
        st.plotly_chart(
            create_median_price_by_neighbourhood_chart(
                filtered_df,
                top_n=15,
                minimum_listings=20,
            ),
            width="stretch",
            key="explorer_median_price_by_neighbourhood",
        )

    third_column, fourth_column = st.columns(2)

    with third_column:
        st.plotly_chart(
            create_median_price_by_room_type_chart(
                filtered_df,
            ),
            width="stretch",
            key="explorer_median_price_by_room_type",
        )

    with fourth_column:
        st.plotly_chart(
            create_median_price_by_capacity_chart(
                filtered_df,
                maximum_capacity=10,
            ),
            width="stretch",
            key="explorer_median_price_by_capacity",
        )

    render_price_caveat()


# ---------------------------------------------------------------------------
# Pricing tab
# ---------------------------------------------------------------------------


def render_pricing_tab(
    filtered_df: pd.DataFrame,
) -> None:
    """
    Render focused pricing analysis.
    """
    render_section_header(
        "Pricing Analysis",
        (
            "Explore price distributions and pricing differences "
            "across neighbourhoods, room types, and capacity."
        ),
    )

    render_market_overview_metrics(filtered_df)

    st.plotly_chart(
        create_price_distribution_chart(
            filtered_df,
            use_99th_percentile_limit=True,
        ),
        width="stretch",
        key="pricing_price_distribution",
    )

    first_column, second_column = st.columns(2)

    with first_column:
        st.plotly_chart(
            create_median_price_by_neighbourhood_chart(
                filtered_df,
                top_n=15,
                minimum_listings=20,
            ),
            width="stretch",
            key="pricing_median_price_by_neighbourhood",
        )

    with second_column:
        st.plotly_chart(
            create_median_price_by_room_type_chart(
                filtered_df,
            ),
            width="stretch",
            key="pricing_median_price_by_room_type",
        )

    st.plotly_chart(
        create_median_price_by_capacity_chart(
            filtered_df,
            maximum_capacity=10,
        ),
        width="stretch",
        key="pricing_median_price_by_capacity",
    )

    render_price_caveat()
    render_visualization_limit_caveat()


# ---------------------------------------------------------------------------
# Reviews and availability tab
# ---------------------------------------------------------------------------


def render_reviews_and_availability_tab(
    filtered_df: pd.DataFrame,
) -> None:
    """
    Render review activity and availability-proxy analysis.
    """
    render_section_header(
        "Reviews & Availability",
        (
            "Explore review activity and calendar-based "
            "unavailability patterns."
        ),
    )

    first_column, second_column = st.columns(2)

    with first_column:
        st.plotly_chart(
            create_review_activity_by_neighbourhood_chart(
                filtered_df,
                top_n=15,
            ),
            width="stretch",
            key="reviews_review_activity_by_neighbourhood",
        )

    with second_column:
        st.plotly_chart(
            create_unavailability_proxy_chart(
                filtered_df,
                top_n=15,
                minimum_listings=20,
            ),
            width="stretch",
            key="reviews_unavailability_proxy",
        )

    render_review_caveat()
    render_unavailability_caveat()


# ---------------------------------------------------------------------------
# Statistics tab
# ---------------------------------------------------------------------------


def render_statistical_findings_tab(
    statistical_results: pd.DataFrame | None,
) -> None:
    """
    Render the two completed statistical hypothesis findings.
    """
    render_section_header(
        "Statistical Findings",
        (
            "Two focused hypothesis tests examining pricing and "
            "review-score differences."
        ),
    )

    first_column, second_column = st.columns(2)

    with first_column:
        render_hypothesis_card(
            title="Hypothesis 1 — Entire Homes vs Private Rooms",
            question=(
                "Do entire-home listings command higher prices "
                "than private-room listings?"
            ),
            result=(
                "Entire home/apt median: €331 · "
                "Private room median: €171 · "
                "p < 0.001 · "
                "Rank-biserial effect size: 0.697"
            ),
            interpretation=(
                "Entire homes show a statistically significant "
                "and practically large price premium over "
                "private rooms."
            ),
        )

    with second_column:
        render_hypothesis_card(
            title="Hypothesis 2 — Superhosts vs Non-Superhosts",
            question=(
                "Do superhost listings achieve different review "
                "scores than non-superhost listings?"
            ),
            result=(
                "Superhost median: 4.90 · "
                "Non-superhost median: 4.94 · "
                "p = 3.19 × 10⁻²⁵ · "
                "Rank-biserial effect size: -0.158"
            ),
            interpretation=(
                "The difference is statistically significant but "
                "small in practical terms."
            ),
        )

    st.info(
        "**Interpretation principle:** Statistical significance is "
        "not treated as automatic practical importance, and these "
        "observational findings do not prove causation."
    )

    if (
        statistical_results is not None
        and not statistical_results.empty
    ):
        with st.expander(
            "View statistical result output table"
        ):
            st.dataframe(
                statistical_results,
                width="stretch",
                hide_index=True,
            )


# ---------------------------------------------------------------------------
# Machine learning tab
# ---------------------------------------------------------------------------


def render_ml_results_tab(
    model_results: pd.DataFrame | None,
    feature_importance: pd.DataFrame | None,
    model_predictions: pd.DataFrame | None,
) -> None:
    """
    Render machine-learning experiment results.
    """
    render_section_header(
        "Machine Learning Results",
        (
            "A focused price-prediction experiment comparing "
            "Dummy Regressor, Ridge Regression, and Random Forest."
        ),
    )

    if model_results is None or model_results.empty:
        st.warning(
            "Machine-learning model results are not available. "
            "Run `python experiments/price_prediction.py` first."
        )
        return

    render_ml_summary_metrics(model_results)

    st.write("")

    st.plotly_chart(
        create_model_comparison_chart(model_results),
        width="stretch",
        key="ml_model_comparison",
    )

    with st.expander("View full model comparison table"):
        st.dataframe(
            model_results,
            width="stretch",
            hide_index=True,
        )

    if (
        feature_importance is not None
        and not feature_importance.empty
    ):
        st.divider()

        st.plotly_chart(
            create_feature_importance_chart(
                feature_importance,
                top_n=15,
            ),
            width="stretch",
            key="ml_feature_importance",
        )

        st.caption(
            "Impurity-based feature importance indicates how "
            "features contributed to the fitted Random Forest model. "
            "It does not establish causation."
        )

    if (
        model_predictions is not None
        and not model_predictions.empty
    ):
        st.divider()

        st.plotly_chart(
            create_actual_vs_predicted_chart(
                model_predictions,
                percentile_limit=0.99,
            ),
            width="stretch",
            key="ml_actual_vs_predicted",
        )

        render_visualization_limit_caveat()

    render_ml_caveat()


# ---------------------------------------------------------------------------
# Data engineering tab
# ---------------------------------------------------------------------------


def render_engineering_tab() -> None:
    """
    Render project engineering and data-quality status.
    """
    render_section_header(
        "Data Quality & Engineering",
        (
            "Engineering validation, reproducibility, testing, "
            "continuous integration, and architecture."
        ),
    )

    render_data_quality_metrics()

    st.divider()

    first_column, second_column = st.columns(2)

    with first_column:
        st.markdown("### Pipeline Summary")

        st.markdown(
            """
```text
Raw Source Files
        ↓
Raw Input Verification
        ↓
Automated Profiling
        ↓
Data-Quality Validation
        ↓
Critical Validation Gate
        ↓
Cleaning & Standardization
        ↓
Listing-Level Enrichment
        ↓
Processed Parquet Layer
        ↓
DuckDB Analytical Warehouse
        ↓
SQL + EDA + Statistics + ML
        ↓
Interactive Dashboard
```
            """
        )

    with second_column:
        st.markdown("### Project Status")
        render_project_status()

    st.divider()

    st.markdown("### Verified Engineering Results")

    engineering_results = pd.DataFrame(
        {
            "Metric": [
                "Canonical listings preserved",
                "Detailed listings matched",
                "Summary-only listings preserved",
                "Review events reconciled",
                "Calendar rows reconciled",
                "Datasets profiled",
                "Data-quality checks",
                "Warehouse validation",
                "Automated tests",
                "GitHub Actions CI",
            ],
            "Result": [
                "10,465",
                "10,369",
                "96",
                "545,162",
                "3,819,725",
                "7 / 7",
                "83 PASS / 7 WARNING / 0 FAIL",
                "17 PASS / 0 FAIL",
                "13 passed / 0 failed",
                "Passing",
            ],
        }
    )

    st.dataframe(
        engineering_results,
        width="stretch",
        hide_index=True,
    )

    if ARCHITECTURE_IMAGE_PATH.exists():
        st.divider()

        st.markdown("### Project Architecture")

        st.image(
            str(ARCHITECTURE_IMAGE_PATH),
            caption="Amsterdam Airbnb Data Engineering Architecture",
            width="stretch",
        )


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------


def main() -> None:
    """
    Run the Amsterdam Airbnb interactive dashboard.
    """
    render_page_header(
        title="🏠 Amsterdam Airbnb Market Explorer",
        subtitle=(
            "Interactive market analysis built on the validated "
            "Amsterdam Airbnb data engineering pipeline."
        ),
    )

    try:
        listings_df = load_enriched_listings()

    except FileNotFoundError as error:
        st.error(str(error))

        st.code(
            "python run_pipeline.py --city amsterdam",
            language="bash",
        )

        st.stop()

    except Exception as error:
        st.error(
            "The enriched listing dataset could not be loaded."
        )

        st.exception(error)
        st.stop()

    data_availability = get_available_data_sources()

    optional_data = load_optional_dashboard_data(
        data_availability
    )

    filters = render_sidebar_filters(listings_df)

    filtered_df = apply_dashboard_filters(
        df=listings_df,
        selected_neighbourhoods=filters[
            "selected_neighbourhoods"
        ],
        selected_room_types=filters[
            "selected_room_types"
        ],
        selected_host_segments=filters[
            "selected_host_segments"
        ],
        selected_superhost_statuses=filters[
            "selected_superhost_statuses"
        ],
        minimum_price=filters["minimum_price"],
        maximum_price=filters["maximum_price"],
        minimum_capacity=filters["minimum_capacity"],
        maximum_capacity=filters["maximum_capacity"],
    )

    if filtered_df.empty:
        st.warning(
            "No listings match the selected filters. "
            "Adjust the sidebar filters and try again."
        )

        render_footer()
        st.stop()

    (
        overview_tab,
        market_explorer_tab,
        pricing_tab,
        reviews_tab,
        statistics_tab,
        ml_tab,
        engineering_tab,
    ) = st.tabs(
        [
            "🏠 Overview",
            "🔍 Market Explorer",
            "💶 Pricing",
            "⭐ Reviews & Availability",
            "📊 Statistics",
            "🤖 Machine Learning",
            "🛠️ Data Engineering",
        ]
    )

    with overview_tab:
        render_overview_tab(
            original_df=listings_df,
            filtered_df=filtered_df,
        )

    with market_explorer_tab:
        render_market_explorer_tab(
            original_df=listings_df,
            filtered_df=filtered_df,
        )

    with pricing_tab:
        render_pricing_tab(filtered_df)

    with reviews_tab:
        render_reviews_and_availability_tab(
            filtered_df
        )

    with statistics_tab:
        render_statistical_findings_tab(
            optional_data["statistical_results"]
        )

    with ml_tab:
        render_ml_results_tab(
            model_results=optional_data[
                "model_results"
            ],
            feature_importance=optional_data[
                "feature_importance"
            ],
            model_predictions=optional_data[
                "model_predictions"
            ],
        )

    with engineering_tab:
        render_engineering_tab()

    render_footer()


if __name__ == "__main__":
    main()
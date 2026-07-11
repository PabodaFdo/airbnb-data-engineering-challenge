from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


PRICE_COLUMN = "price_best_available"


def format_integer(value: Any) -> str:
    """
    Format a numeric value as a comma-separated integer.

    Example:
        10465 -> "10,465"
    """
    if pd.isna(value):
        return "N/A"

    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "N/A"


def format_euro(
    value: Any,
    decimal_places: int = 0,
) -> str:
    """
    Format a numeric value as a euro amount.

    Examples:
        287 -> "€287"
        78.61 -> "€78.61"
    """
    if pd.isna(value):
        return "N/A"

    try:
        numeric_value = float(value)

        if decimal_places == 0:
            return f"€{numeric_value:,.0f}"

        return f"€{numeric_value:,.{decimal_places}f}"

    except (TypeError, ValueError):
        return "N/A"


def format_percentage(
    value: Any,
    decimal_places: int = 1,
) -> str:
    """
    Format a decimal value as a percentage.

    Example:
        0.5884 -> "58.8%"
    """
    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value) * 100:.{decimal_places}f}%"
    except (TypeError, ValueError):
        return "N/A"


def render_page_header(
    title: str,
    subtitle: str,
) -> None:
    """
    Render the main dashboard title and subtitle.
    """
    st.title(title)

    st.markdown(
        f"""
        <p style="
            font-size: 1.05rem;
            color: #6b7280;
            margin-top: -0.5rem;
            margin-bottom: 1.5rem;
        ">
            {subtitle}
        </p>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(
    title: str,
    description: str | None = None,
) -> None:
    """
    Render a dashboard section heading with an optional description.
    """
    st.subheader(title)

    if description:
        st.caption(description)


def render_market_overview_metrics(
    df: pd.DataFrame,
) -> None:
    """
    Render primary Amsterdam Airbnb market KPI cards.
    """
    required_columns = [
        "id",
        PRICE_COLUMN,
        "neighbourhood",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        st.error(
            "Market overview metrics cannot be displayed because "
            f"these columns are missing: {missing_columns}"
        )
        return

    total_listings = int(df["id"].nunique())

    valid_price_mask = (
        df[PRICE_COLUMN].notna()
        & (df[PRICE_COLUMN] > 0)
    )

    valid_price_count = int(
        df.loc[valid_price_mask, "id"].nunique()
    )

    median_price = (
        df.loc[valid_price_mask, PRICE_COLUMN].median()
        if valid_price_mask.any()
        else None
    )

    neighbourhood_count = int(
        df["neighbourhood"].dropna().nunique()
    )

    column_1, column_2, column_3, column_4 = st.columns(4)

    with column_1:
        st.metric(
            label="Total Listings",
            value=format_integer(total_listings),
        )

    with column_2:
        st.metric(
            label="Listings With Valid Price",
            value=format_integer(valid_price_count),
        )

    with column_3:
        st.metric(
            label="Median Available Price",
            value=format_euro(median_price),
        )

    with column_4:
        st.metric(
            label="Neighbourhoods",
            value=format_integer(neighbourhood_count),
        )


def render_secondary_market_metrics(
    df: pd.DataFrame,
) -> None:
    """
    Render additional market KPI cards where source columns are available.
    """
    total_reviews = None
    median_unavailability = None
    median_accommodates = None
    superhost_count = None

    if "detailed_review_count" in df.columns:
        review_values = pd.to_numeric(
            df["detailed_review_count"],
            errors="coerce",
        )

        total_reviews = review_values.sum(min_count=1)

    if "unavailability_rate_proxy" in df.columns:
        proxy_values = pd.to_numeric(
            df["unavailability_rate_proxy"],
            errors="coerce",
        )

        median_unavailability = proxy_values.median()

    if "accommodates" in df.columns:
        capacity_values = pd.to_numeric(
            df["accommodates"],
            errors="coerce",
        )

        median_accommodates = capacity_values.median()

    if "host_is_superhost" in df.columns:
        normalized_superhost = (
            df["host_is_superhost"]
            .astype("string")
            .str.strip()
            .str.lower()
        )

        superhost_count = int(
            normalized_superhost.isin(
                [
                    "true",
                    "t",
                    "1",
                    "yes",
                ]
            ).sum()
        )

    column_1, column_2, column_3, column_4 = st.columns(4)

    with column_1:
        st.metric(
            label="Detailed Review Events",
            value=format_integer(total_reviews),
        )

    with column_2:
        st.metric(
            label="Median Unavailability Proxy",
            value=format_percentage(
                median_unavailability,
            ),
        )

    with column_3:
        st.metric(
            label="Median Guest Capacity",
            value=(
                format_integer(median_accommodates)
                if median_accommodates is not None
                else "N/A"
            ),
        )

    with column_4:
        st.metric(
            label="Superhost Listings",
            value=format_integer(superhost_count),
        )


def render_data_quality_metrics() -> None:
    """
    Render verified project data-quality and engineering metrics.
    """
    column_1, column_2, column_3, column_4 = st.columns(4)

    with column_1:
        st.metric(
            label="Datasets Profiled",
            value="7 / 7",
        )

    with column_2:
        st.metric(
            label="Data Quality",
            value="83 PASS",
        )

        st.caption("7 WARNING · 0 FAIL")

    with column_3:
        st.metric(
            label="Warehouse Validation",
            value="17 PASS",
        )

        st.caption("0 FAIL")

    with column_4:
        st.metric(
            label="Automated Tests",
            value="13 Passed",
        )

        st.caption("0 Failed")


def render_ml_summary_metrics(
    model_results: pd.DataFrame,
) -> None:
    """
    Render best-model machine-learning metrics.

    The function attempts to recognize common model and metric
    column naming conventions.
    """
    if model_results.empty:
        st.info("No machine-learning model results are available.")
        return

    model_column = _find_column(
        model_results,
        [
            "model",
            "Model",
            "model_name",
        ],
    )

    mae_column = _find_column(
        model_results,
        [
            "mae_eur",
            "mae",
            "MAE",
        ],
    )

    rmse_column = _find_column(
    model_results,
        [
            "rmse_eur",
            "rmse",
            "RMSE",
        ],
    )

    r2_column = _find_column(
        model_results,
        [
            "r2",
            "R2",
            "r_squared",
            "R²",
        ],
    )

    if model_column is None or mae_column is None:
        st.warning(
            "The model results file does not contain the required "
            "model-name and MAE columns."
        )
        return

    numeric_mae = pd.to_numeric(
        model_results[mae_column],
        errors="coerce",
    )

    if numeric_mae.dropna().empty:
        st.warning(
            "No valid MAE values were found in the model results."
        )
        return

    best_index = numeric_mae.idxmin()
    best_row = model_results.loc[best_index]

    best_model = str(best_row[model_column])

    best_mae = pd.to_numeric(
        pd.Series([best_row[mae_column]]),
        errors="coerce",
    ).iloc[0]

    best_rmse = (
        pd.to_numeric(
            pd.Series([best_row[rmse_column]]),
            errors="coerce",
        ).iloc[0]
        if rmse_column is not None
        else None
    )

    best_r2 = (
        pd.to_numeric(
            pd.Series([best_row[r2_column]]),
            errors="coerce",
        ).iloc[0]
        if r2_column is not None
        else None
    )

    column_1, column_2, column_3, column_4 = st.columns(4)

    with column_1:
        st.metric(
            label="Best Model",
            value=best_model,
        )

    with column_2:
        st.metric(
            label="MAE",
            value=format_euro(
                best_mae,
                decimal_places=2,
            ),
        )

    with column_3:
        st.metric(
            label="RMSE",
            value=format_euro(
                best_rmse,
                decimal_places=2,
            ),
        )

    with column_4:
        st.metric(
            label="R²",
            value=(
                f"{float(best_r2):.4f}"
                if best_r2 is not None
                and not pd.isna(best_r2)
                else "N/A"
            ),
        )


def render_filter_summary(
    original_df: pd.DataFrame,
    filtered_df: pd.DataFrame,
) -> None:
    """
    Show how many listings remain after dashboard filters are applied.
    """
    original_count = len(original_df)
    filtered_count = len(filtered_df)

    if original_count == 0:
        percentage = 0.0
    else:
        percentage = (
            filtered_count / original_count
        ) * 100

    st.info(
        f"Showing **{filtered_count:,} of "
        f"{original_count:,} listings** "
        f"({percentage:.1f}% of the canonical dataset)."
    )


def render_price_caveat() -> None:
    """
    Render the missing-price interpretation warning.
    """
    st.info(
        "**Price interpretation:** Missing prices are preserved as null "
        "and are not treated as zero. Price-based analysis uses only "
        "valid positive price observations."
    )


def render_unavailability_caveat() -> None:
    """
    Render the calendar unavailability interpretation warning.
    """
    st.warning(
        "**Important limitation:** Calendar unavailability is used only "
        "as an `unavailability_rate_proxy`. It is not verified occupancy, "
        "confirmed booking activity, or actual revenue."
    )


def render_review_caveat() -> None:
    """
    Render the review activity interpretation warning.
    """
    st.info(
        "**Review interpretation:** Review activity is not equivalent to "
        "verified booking volume because not every guest necessarily "
        "leaves a review."
    )


def render_ml_caveat() -> None:
    """
    Render the machine-learning interpretation warning.
    """
    st.warning(
        "**Model limitation:** The machine-learning experiment predicts "
        "available listing prices, not confirmed transaction prices, "
        "revenue, profitability, or causal effects. Feature importance "
        "does not establish causation."
    )


def render_visualization_limit_caveat() -> None:
    """
    Explain that chart truncation does not remove underlying records.
    """
    st.caption(
        "Some visualizations use percentile-based display limits for "
        "readability. These limits affect only the displayed chart and "
        "do not remove records from model evaluation or source datasets."
    )


def render_hypothesis_card(
    title: str,
    question: str,
    result: str,
    interpretation: str,
) -> None:
    """
    Render a compact statistical-hypothesis summary.
    """
    with st.container(border=True):
        st.markdown(f"### {title}")
        st.markdown(f"**Question:** {question}")
        st.markdown(f"**Result:** {result}")
        st.markdown(
            f"**Interpretation:** {interpretation}"
        )


def render_project_status() -> None:
    """
    Render key current project completion indicators.
    """
    st.markdown(
        """
        ✅ Dataset familiarization  
        ✅ Automated profiling  
        ✅ Data-quality validation  
        ✅ Cleaning and standardization  
        ✅ Listing-level enrichment  
        ✅ DuckDB analytical warehouse  
        ✅ Exploratory data analysis  
        ✅ Statistical hypothesis testing  
        ✅ Focused price-prediction experiment  
        ✅ 13 automated tests  
        ✅ GitHub Actions continuous integration  
        ✅ Interactive Streamlit dashboard
        """
    )


def render_footer() -> None:
    """
    Render a compact dashboard footer.
    """
    st.divider()

    st.caption(
        "Amsterdam Airbnb Data Engineering & Analytics Challenge · "
        "Built by Paboda Sathsarani Fernando · "
        "Data sourced from Inside Airbnb"
    )


def _find_column(
    df: pd.DataFrame,
    candidates: list[str],
) -> str | None:
    """
    Return the first matching column name from a list of candidates.
    """
    return next(
        (
            column
            for column in candidates
            if column in df.columns
        ),
        None,
    )
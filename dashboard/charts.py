from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


PRICE_COLUMN = "price_best_available"


def _require_columns(
    df: pd.DataFrame,
    required_columns: list[str],
    chart_name: str,
) -> None:
    """
    Validate that all columns required by a chart exist.
    """
    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{chart_name} cannot be created because these columns "
            f"are missing: {missing_columns}"
        )


def create_listings_by_neighbourhood_chart(
    df: pd.DataFrame,
    top_n: int = 15,
) -> go.Figure:
    """
    Create a horizontal bar chart showing listing counts by neighbourhood.
    """
    _require_columns(
        df,
        ["neighbourhood", "id"],
        "Listings by neighbourhood chart",
    )

    chart_data = (
        df.dropna(subset=["neighbourhood"])
        .groupby("neighbourhood", as_index=False)
        .agg(listing_count=("id", "nunique"))
        .sort_values("listing_count", ascending=False)
        .head(top_n)
        .sort_values("listing_count", ascending=True)
    )

    fig = px.bar(
        chart_data,
        x="listing_count",
        y="neighbourhood",
        orientation="h",
        labels={
            "listing_count": "Listings",
            "neighbourhood": "Neighbourhood",
        },
        title=f"Top {top_n} Neighbourhoods by Listing Count",
    )

    fig.update_layout(
        xaxis_title="Number of Listings",
        yaxis_title="",
        height=max(450, top_n * 32),
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig


def create_median_price_by_neighbourhood_chart(
    df: pd.DataFrame,
    top_n: int = 15,
    minimum_listings: int = 20,
) -> go.Figure:
    """
    Create a horizontal bar chart showing median price by neighbourhood.

    Only neighbourhoods meeting the minimum valid-price sample threshold
    are included.
    """
    _require_columns(
        df,
        ["neighbourhood", PRICE_COLUMN, "id"],
        "Median price by neighbourhood chart",
    )

    valid_df = df[
        df[PRICE_COLUMN].notna()
        & (df[PRICE_COLUMN] > 0)
        & df["neighbourhood"].notna()
    ].copy()

    chart_data = (
        valid_df.groupby("neighbourhood", as_index=False)
        .agg(
            median_price=(PRICE_COLUMN, "median"),
            valid_price_listings=("id", "nunique"),
        )
    )

    chart_data = chart_data[
        chart_data["valid_price_listings"] >= minimum_listings
    ]

    chart_data = (
        chart_data.sort_values(
            "median_price",
            ascending=False,
        )
        .head(top_n)
        .sort_values(
            "median_price",
            ascending=True,
        )
    )

    fig = px.bar(
        chart_data,
        x="median_price",
        y="neighbourhood",
        orientation="h",
        custom_data=["valid_price_listings"],
        labels={
            "median_price": "Median Price (€)",
            "neighbourhood": "Neighbourhood",
        },
        title=(
            f"Top {top_n} Neighbourhoods by Median Available Price"
        ),
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Median price: €%{x:,.2f}<br>"
            "Valid-price listings: %{customdata[0]:,}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        xaxis_title="Median Price (€)",
        yaxis_title="",
        height=max(450, top_n * 32),
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig


def create_median_price_by_room_type_chart(
    df: pd.DataFrame,
) -> go.Figure:
    """
    Create a bar chart showing median available price by room type.
    """
    _require_columns(
        df,
        ["room_type", PRICE_COLUMN, "id"],
        "Median price by room type chart",
    )

    valid_df = df[
        df[PRICE_COLUMN].notna()
        & (df[PRICE_COLUMN] > 0)
        & df["room_type"].notna()
    ].copy()

    chart_data = (
        valid_df.groupby("room_type", as_index=False)
        .agg(
            median_price=(PRICE_COLUMN, "median"),
            valid_price_listings=("id", "nunique"),
        )
        .sort_values("median_price", ascending=False)
    )

    fig = px.bar(
        chart_data,
        x="room_type",
        y="median_price",
        custom_data=["valid_price_listings"],
        labels={
            "room_type": "Room Type",
            "median_price": "Median Price (€)",
        },
        title="Median Available Price by Room Type",
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Median price: €%{y:,.2f}<br>"
            "Valid-price listings: %{customdata[0]:,}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        xaxis_title="Room Type",
        yaxis_title="Median Price (€)",
        height=500,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig


def create_price_distribution_chart(
    df: pd.DataFrame,
    use_99th_percentile_limit: bool = True,
) -> go.Figure:
    """
    Create a histogram of valid available listing prices.

    By default, the chart is visually limited to the 99th percentile.
    This affects visualization only and does not modify the underlying data.
    """
    _require_columns(
        df,
        [PRICE_COLUMN],
        "Price distribution chart",
    )

    valid_prices = df.loc[
        df[PRICE_COLUMN].notna()
        & (df[PRICE_COLUMN] > 0),
        PRICE_COLUMN,
    ].copy()

    if valid_prices.empty:
        return go.Figure()

    if use_99th_percentile_limit:
        upper_limit = float(valid_prices.quantile(0.99))
        chart_prices = valid_prices[
            valid_prices <= upper_limit
        ]
    else:
        upper_limit = float(valid_prices.max())
        chart_prices = valid_prices

    chart_data = pd.DataFrame(
        {
            PRICE_COLUMN: chart_prices,
        }
    )

    fig = px.histogram(
        chart_data,
        x=PRICE_COLUMN,
        nbins=50,
        labels={
            PRICE_COLUMN: "Available Listing Price (€)",
        },
        title="Distribution of Available Listing Prices",
    )

    fig.update_layout(
        xaxis_title="Available Listing Price (€)",
        yaxis_title="Number of Listings",
        height=500,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    if use_99th_percentile_limit:
        fig.add_annotation(
            text=(
                "Visualization limited to the 99th percentile "
                f"(€{upper_limit:,.0f}) for readability."
            ),
            xref="paper",
            yref="paper",
            x=0,
            y=1.08,
            showarrow=False,
            align="left",
        )

    return fig


def create_median_price_by_capacity_chart(
    df: pd.DataFrame,
    maximum_capacity: int = 10,
) -> go.Figure:
    """
    Create a line chart showing median price by accommodation capacity.
    """
    _require_columns(
        df,
        ["accommodates", PRICE_COLUMN, "id"],
        "Median price by capacity chart",
    )

    valid_df = df[
        df[PRICE_COLUMN].notna()
        & (df[PRICE_COLUMN] > 0)
        & df["accommodates"].notna()
        & (df["accommodates"] > 0)
        & (df["accommodates"] <= maximum_capacity)
    ].copy()

    chart_data = (
        valid_df.groupby("accommodates", as_index=False)
        .agg(
            median_price=(PRICE_COLUMN, "median"),
            listing_count=("id", "nunique"),
        )
        .sort_values("accommodates")
    )

    fig = px.line(
        chart_data,
        x="accommodates",
        y="median_price",
        markers=True,
        custom_data=["listing_count"],
        labels={
            "accommodates": "Accommodation Capacity",
            "median_price": "Median Price (€)",
        },
        title="Median Available Price by Accommodation Capacity",
    )

    fig.update_traces(
        hovertemplate=(
            "Capacity: %{x}<br>"
            "Median price: €%{y:,.2f}<br>"
            "Listings: %{customdata[0]:,}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        xaxis_title="Guests Accommodated",
        yaxis_title="Median Price (€)",
        height=500,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig


def create_review_activity_by_neighbourhood_chart(
    df: pd.DataFrame,
    top_n: int = 15,
) -> go.Figure:
    """
    Create a horizontal bar chart showing total detailed review activity
    by neighbourhood.
    """
    _require_columns(
        df,
        [
            "neighbourhood",
            "detailed_review_count",
        ],
        "Review activity by neighbourhood chart",
    )

    valid_df = df[
        df["neighbourhood"].notna()
        & df["detailed_review_count"].notna()
    ].copy()

    chart_data = (
        valid_df.groupby("neighbourhood", as_index=False)
        .agg(
            total_review_events=(
                "detailed_review_count",
                "sum",
            )
        )
        .sort_values(
            "total_review_events",
            ascending=False,
        )
        .head(top_n)
        .sort_values(
            "total_review_events",
            ascending=True,
        )
    )

    fig = px.bar(
        chart_data,
        x="total_review_events",
        y="neighbourhood",
        orientation="h",
        labels={
            "total_review_events": "Review Events",
            "neighbourhood": "Neighbourhood",
        },
        title=f"Top {top_n} Neighbourhoods by Review Activity",
    )

    fig.update_layout(
        xaxis_title="Detailed Review Events",
        yaxis_title="",
        height=max(450, top_n * 32),
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig


def create_unavailability_proxy_chart(
    df: pd.DataFrame,
    top_n: int = 15,
    minimum_listings: int = 20,
) -> go.Figure:
    """
    Create a horizontal bar chart showing median unavailability proxy
    by neighbourhood.
    """
    _require_columns(
        df,
        [
            "neighbourhood",
            "unavailability_rate_proxy",
            "id",
        ],
        "Unavailability proxy chart",
    )

    valid_df = df[
        df["neighbourhood"].notna()
        & df["unavailability_rate_proxy"].notna()
    ].copy()

    chart_data = (
        valid_df.groupby("neighbourhood", as_index=False)
        .agg(
            median_unavailability_proxy=(
                "unavailability_rate_proxy",
                "median",
            ),
            listing_count=("id", "nunique"),
        )
    )

    chart_data = chart_data[
        chart_data["listing_count"] >= minimum_listings
    ]

    chart_data = (
        chart_data.sort_values(
            "median_unavailability_proxy",
            ascending=False,
        )
        .head(top_n)
        .sort_values(
            "median_unavailability_proxy",
            ascending=True,
        )
    )

    fig = px.bar(
        chart_data,
        x="median_unavailability_proxy",
        y="neighbourhood",
        orientation="h",
        custom_data=["listing_count"],
        labels={
            "median_unavailability_proxy": (
                "Median Unavailability Proxy"
            ),
            "neighbourhood": "Neighbourhood",
        },
        title=(
            f"Top {top_n} Neighbourhoods by "
            "Median Unavailability Proxy"
        ),
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Median unavailability proxy: %{x:.2%}<br>"
            "Listings: %{customdata[0]:,}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        xaxis_title="Median Unavailability Proxy",
        yaxis_title="",
        xaxis_tickformat=".0%",
        height=max(450, top_n * 32),
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig


def create_model_comparison_chart(
    model_results: pd.DataFrame,
) -> go.Figure:
    """
    Create a model-comparison chart using MAE values.
    """
    possible_model_columns = [
        "model",
        "Model",
        "model_name",
    ]

    model_column = next(
        (
            column
            for column in possible_model_columns
            if column in model_results.columns
        ),
        None,
    )

    possible_mae_columns = [
        "mae_eur",
        "mae",
        "MAE",
    ]

    mae_column = next(
        (
            column
            for column in possible_mae_columns
            if column in model_results.columns
        ),
        None,
    )

    if model_column is None or mae_column is None:
        raise ValueError(
            "Model results must contain a model-name column "
            "and an MAE column."
        )

    chart_data = model_results.copy()

    chart_data[mae_column] = pd.to_numeric(
        chart_data[mae_column],
        errors="coerce",
    )

    chart_data = chart_data.dropna(
        subset=[model_column, mae_column]
    )

    chart_data = chart_data.sort_values(
        mae_column,
        ascending=True,
    )

    fig = px.bar(
        chart_data,
        x=model_column,
        y=mae_column,
        text=mae_column,
        labels={
            model_column: "Model",
            mae_column: "MAE (€)",
        },
        title="Price-Prediction Model Comparison",
    )

    fig.update_traces(
        texttemplate="€%{text:.2f}",
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "MAE: €%{y:,.2f}"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        xaxis_title="Model",
        yaxis_title="Mean Absolute Error (€)",
        height=500,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig


def create_feature_importance_chart(
    feature_importance: pd.DataFrame,
    top_n: int = 15,
) -> go.Figure:
    """
    Create a horizontal bar chart of Random Forest feature importance.
    """
    _require_columns(
        feature_importance,
        ["feature", "importance"],
        "Feature importance chart",
    )

    chart_data = (
        feature_importance.nlargest(top_n, "importance")
        .sort_values("importance", ascending=True)
    )

    fig = px.bar(
        chart_data,
        x="importance",
        y="feature",
        orientation="h",
        labels={
            "importance": "Importance",
            "feature": "Feature",
        },
        title=f"Top {top_n} Random Forest Encoded Features",
    )

    fig.update_layout(
        xaxis_title="Impurity-Based Feature Importance",
        yaxis_title="",
        height=max(500, top_n * 32),
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig


def create_actual_vs_predicted_chart(
    predictions: pd.DataFrame,
    percentile_limit: float = 0.99,
) -> go.Figure:
    """
    Create an actual-vs-predicted diagnostic chart using
    Random Forest predictions.

    The percentile limit affects visualization only.
    All observations remain part of model evaluation.
    """
    actual_candidates = [
        "actual_price",
        "actual",
        "y_true",
    ]

    predicted_candidates = [
        "random_forest_regressor_prediction",
        "predicted_price",
        "predicted",
        "y_pred",
    ]

    actual_column = next(
        (
            column
            for column in actual_candidates
            if column in predictions.columns
        ),
        None,
    )

    predicted_column = next(
        (
            column
            for column in predicted_candidates
            if column in predictions.columns
        ),
        None,
    )

    if actual_column is None or predicted_column is None:
        raise ValueError(
            "Prediction data must contain actual-price and "
            "Random Forest predicted-price columns."
        )

    chart_data = predictions[
        predictions[actual_column].notna()
        & predictions[predicted_column].notna()
    ].copy()

    chart_data[actual_column] = pd.to_numeric(
        chart_data[actual_column],
        errors="coerce",
    )

    chart_data[predicted_column] = pd.to_numeric(
        chart_data[predicted_column],
        errors="coerce",
    )

    chart_data = chart_data.dropna(
        subset=[
            actual_column,
            predicted_column,
        ]
    )

    if chart_data.empty:
        return go.Figure()

    actual_limit = float(
        chart_data[actual_column].quantile(
            percentile_limit
        )
    )

    visible_data = chart_data[
        chart_data[actual_column] <= actual_limit
    ].copy()

    fig = px.scatter(
        visible_data,
        x=actual_column,
        y=predicted_column,
        opacity=0.55,
        labels={
            actual_column: "Actual Price (€)",
            predicted_column: (
                "Random Forest Predicted Price (€)"
            ),
        },
        title="Actual vs Predicted Listing Prices",
    )

    maximum_visible_value = max(
        float(visible_data[actual_column].max()),
        float(visible_data[predicted_column].max()),
    )

    fig.add_trace(
        go.Scatter(
            x=[0, maximum_visible_value],
            y=[0, maximum_visible_value],
            mode="lines",
            name="Perfect prediction",
            hoverinfo="skip",
        )
    )

    fig.update_layout(
        xaxis_title="Actual Price (€)",
        yaxis_title=(
            "Random Forest Predicted Price (€)"
        ),
        height=550,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    fig.add_annotation(
        text=(
            f"Visualization limited to the "
            f"{percentile_limit:.0%} percentile of actual prices "
            f"(€{actual_limit:,.0f}) for readability."
        ),
        xref="paper",
        yref="paper",
        x=0,
        y=1.08,
        showarrow=False,
        align="left",
    )

    return fig
"""
Focused Airbnb price-prediction experiment.

Research question:
    Can listing characteristics predict the available listing price
    for Amsterdam Airbnb listings?

Models compared:
1. Dummy Regressor
2. Ridge Regression
3. Random Forest Regressor

Evaluation metrics:
- MAE
- RMSE
- R²

Important design decisions:
- Price-derived columns are excluded to prevent target leakage.
- Missing target prices are not imputed.
- Only listings with a valid positive target price are used.
- Pandas nullable values are converted into scikit-learn-compatible
  representations before model preprocessing.
- A log1p target transformation is used because Airbnb prices are
  strongly right-skewed.
- Model interpretation includes Random Forest feature importance and
  an actual-vs-predicted diagnostic figure.
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.compose import (
    ColumnTransformer,
    TransformedTargetRegressor,
)
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler,
)


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "enriched_listing_master.parquet"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "modeling"
)

RESULTS_PATH = (
    OUTPUT_DIR
    / "price_model_results.csv"
)

PREDICTIONS_PATH = (
    OUTPUT_DIR
    / "price_model_predictions.csv"
)

MODEL_COMPARISON_FIGURE_PATH = (
    OUTPUT_DIR
    / "price_model_comparison.png"
)

FEATURE_IMPORTANCE_PATH = (
    OUTPUT_DIR
    / "random_forest_feature_importance.csv"
)

FEATURE_IMPORTANCE_FIGURE_PATH = (
    OUTPUT_DIR
    / "random_forest_feature_importance.png"
)

ACTUAL_VS_PREDICTED_FIGURE_PATH = (
    OUTPUT_DIR
    / "actual_vs_predicted_price.png"
)


# ---------------------------------------------------------------------------
# Experiment configuration
# ---------------------------------------------------------------------------

TARGET_COLUMN = "price_best_available"

RANDOM_STATE = 42

TEST_SIZE = 0.20


# ---------------------------------------------------------------------------
# Selected features
# ---------------------------------------------------------------------------

CATEGORICAL_FEATURES = [
    "neighbourhood",
    "room_type",
    "detailed_property_type",
    "host_is_superhost",
    "host_identity_verified",
    "host_portfolio_segment",
]


NUMERICAL_FEATURES = [
    "latitude",
    "longitude",
    "accommodates",
    "bathrooms",
    "bedrooms",
    "beds",
    "minimum_nights",
    "maximum_nights",
    "availability_365",
    "number_of_reviews",
    "reviews_per_month",
    "number_of_reviews_ltm",
    "review_scores_rating",
    "calculated_host_listings_count",
    "detailed_review_count",
    "review_events_per_active_year",
    "unavailability_rate_proxy",
]


# ---------------------------------------------------------------------------
# Target-leakage protection
# ---------------------------------------------------------------------------

LEAKAGE_COLUMNS = {
    "price_raw",
    "price",
    "detailed_price",
    "detailed_price_raw",
    "price_best_available",
    "price_source",
    "price_per_bedroom",
    "price_per_guest",
}


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data loading and validation
# ---------------------------------------------------------------------------

def load_modeling_data() -> pd.DataFrame:
    """
    Load the enriched listing-level dataset and prepare it for modeling.

    Processing rules:
    - Preserve the original source data unchanged.
    - Keep only rows with a valid positive target price.
    - Never impute missing target prices.
    - Convert numerical features to float64 with np.nan for missing values.
    - Convert categorical features to plain Python strings with np.nan
      for missing values.

    Returns
    -------
    pd.DataFrame
        Modeling-ready listing-level DataFrame.
    """

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            "Processed modeling dataset was not found: "
            f"{DATA_PATH}. "
            "Run the data pipeline first."
        )

    LOGGER.info(
        "Loading enriched listing master: %s",
        DATA_PATH,
    )

    df = pd.read_parquet(DATA_PATH)

    required_columns = (
        set(CATEGORICAL_FEATURES)
        | set(NUMERICAL_FEATURES)
        | {TARGET_COLUMN}
    )

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            "Required modeling columns are missing: "
            f"{sorted(missing_columns)}"
        )

    feature_columns = (
        CATEGORICAL_FEATURES
        + NUMERICAL_FEATURES
    )

    accidental_leakage = (
        set(feature_columns)
        & LEAKAGE_COLUMNS
    )

    if accidental_leakage:
        raise ValueError(
            "Target leakage detected in feature list: "
            f"{sorted(accidental_leakage)}"
        )

    original_rows = len(df)

    modeling_df = df.loc[
        df[TARGET_COLUMN].notna(),
        feature_columns + [TARGET_COLUMN],
    ].copy()

    # ------------------------------------------------------------------
    # Normalize target
    # ------------------------------------------------------------------

    modeling_df[TARGET_COLUMN] = pd.to_numeric(
        modeling_df[TARGET_COLUMN],
        errors="coerce",
    ).astype("float64")

    modeling_df = modeling_df.loc[
        modeling_df[TARGET_COLUMN].notna()
        & (modeling_df[TARGET_COLUMN] > 0)
    ].copy()

    # ------------------------------------------------------------------
    # Normalize numerical features
    #
    # Convert Pandas nullable numeric types to standard float64 values.
    # Missing values become np.nan, which SimpleImputer can handle.
    # ------------------------------------------------------------------

    for column in NUMERICAL_FEATURES:
        modeling_df[column] = pd.to_numeric(
            modeling_df[column],
            errors="coerce",
        ).astype("float64")

    # ------------------------------------------------------------------
    # Normalize categorical features
    #
    # Valid values become strings.
    # Missing values become np.nan.
    #
    # This prevents:
    #
    # TypeError: boolean value of NA is ambiguous
    #
    # during scikit-learn preprocessing.
    # ------------------------------------------------------------------

    for column in CATEGORICAL_FEATURES:
        modeling_df[column] = modeling_df[column].map(
            lambda value: (
                str(value)
                if pd.notna(value)
                else np.nan
            )
        )

        modeling_df[column] = modeling_df[column].astype(
            "object"
        )

    LOGGER.info(
        "Original listing rows: %s",
        f"{original_rows:,}",
    )

    LOGGER.info(
        "Usable rows with positive target price: %s",
        f"{len(modeling_df):,}",
    )

    LOGGER.info(
        "Rows excluded because target price is missing or invalid: %s",
        f"{original_rows - len(modeling_df):,}",
    )

    LOGGER.info(
        "Modeling feature dtypes normalized successfully."
    )

    return modeling_df


# ---------------------------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------------------------

def build_preprocessor() -> ColumnTransformer:
    """
    Build preprocessing pipelines for numerical and categorical features.

    Numerical features:
    - Missing values imputed with the median.
    - Features standardized.

    Categorical features:
    - Missing values replaced with "Missing".
    - One-hot encoded.
    - Rare categories grouped using min_frequency=10.

    Returns
    -------
    ColumnTransformer
        Configured reusable feature preprocessor.
    """

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median",
                ),
            ),
            (
                "scaler",
                StandardScaler(),
            ),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="constant",
                    fill_value="Missing",
                ),
            ),
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore",
                    min_frequency=10,
                ),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                NUMERICAL_FEATURES,
            ),
            (
                "categorical",
                categorical_pipeline,
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )


# ---------------------------------------------------------------------------
# Model definitions
# ---------------------------------------------------------------------------

def build_models() -> dict[str, object]:
    """
    Build the regression models used in the experiment.

    Models
    ------
    Dummy Regressor:
        Provides a simple baseline.

    Ridge Regression:
        Provides a regularized linear benchmark.

    Random Forest Regressor:
        Captures nonlinear relationships and feature interactions.

    A log1p target transformation is applied because Airbnb prices are
    strongly right-skewed. Predictions are automatically converted back
    to the original euro scale.

    Returns
    -------
    dict[str, object]
        Mapping of model names to configured estimators.
    """

    dummy_pipeline = Pipeline(
        steps=[
            (
                "preprocessor",
                build_preprocessor(),
            ),
            (
                "model",
                DummyRegressor(
                    strategy="median",
                ),
            ),
        ]
    )

    ridge_pipeline = Pipeline(
        steps=[
            (
                "preprocessor",
                build_preprocessor(),
            ),
            (
                "model",
                Ridge(
                    alpha=1.0,
                ),
            ),
        ]
    )

    random_forest_pipeline = Pipeline(
        steps=[
            (
                "preprocessor",
                build_preprocessor(),
            ),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=200,
                    max_depth=18,
                    min_samples_leaf=3,
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    return {
        "Dummy Regressor": TransformedTargetRegressor(
            regressor=dummy_pipeline,
            func=np.log1p,
            inverse_func=np.expm1,
        ),

        "Ridge Regression": TransformedTargetRegressor(
            regressor=ridge_pipeline,
            func=np.log1p,
            inverse_func=np.expm1,
        ),

        "Random Forest Regressor": TransformedTargetRegressor(
            regressor=random_forest_pipeline,
            func=np.log1p,
            inverse_func=np.expm1,
        ),
    }


# ---------------------------------------------------------------------------
# Model evaluation
# ---------------------------------------------------------------------------

def evaluate_model(
    model_name: str,
    model: object,
    x_train: pd.DataFrame,
    x_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
) -> tuple[dict[str, float | str], np.ndarray]:
    """
    Train and evaluate one regression model.

    Parameters
    ----------
    model_name:
        Human-readable model name.

    model:
        Configured scikit-learn estimator.

    x_train:
        Training feature data.

    x_test:
        Test feature data.

    y_train:
        Training target values.

    y_test:
        Test target values.

    Returns
    -------
    tuple
        Evaluation result dictionary and prediction array.
    """

    LOGGER.info(
        "Training model: %s",
        model_name,
    )

    model.fit(
        x_train,
        y_train,
    )

    predictions = model.predict(
        x_test
    )

    # Prevent impossible negative nightly price predictions.
    predictions = np.maximum(
        predictions,
        0,
    )

    mae = mean_absolute_error(
        y_test,
        predictions,
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_test,
            predictions,
        )
    )

    r2 = r2_score(
        y_test,
        predictions,
    )

    LOGGER.info(
        "%s | MAE: %.2f | RMSE: %.2f | R²: %.4f",
        model_name,
        mae,
        rmse,
        r2,
    )

    result = {
        "model": model_name,

        "mae_eur": round(
            float(mae),
            2,
        ),

        "rmse_eur": round(
            float(rmse),
            2,
        ),

        "r2": round(
            float(r2),
            4,
        ),
    }

    return result, predictions


# ---------------------------------------------------------------------------
# Model comparison visualization
# ---------------------------------------------------------------------------

def save_model_comparison_figure(
    results_df: pd.DataFrame,
) -> None:
    """
    Save a model-comparison chart using Mean Absolute Error.

    Lower MAE indicates better average predictive performance.
    """

    figure_df = results_df.sort_values(
        "mae_eur",
        ascending=True,
    ).copy()

    plt.figure(
        figsize=(10, 6),
    )

    bars = plt.bar(
        figure_df["model"],
        figure_df["mae_eur"],
    )

    plt.title(
        "Amsterdam Airbnb Price Prediction Model Comparison"
    )

    plt.xlabel(
        "Model"
    )

    plt.ylabel(
        "Mean Absolute Error (€)"
    )

    plt.xticks(
        rotation=15,
        ha="right",
    )

    for bar, value in zip(
        bars,
        figure_df["mae_eur"],
        strict=True,
    ):
        plt.text(
            bar.get_x()
            + bar.get_width() / 2,
            bar.get_height(),
            f"€{value:,.2f}",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()

    plt.savefig(
        MODEL_COMPARISON_FIGURE_PATH,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    LOGGER.info(
        "Saved model comparison figure: %s",
        MODEL_COMPARISON_FIGURE_PATH,
    )


# ---------------------------------------------------------------------------
# Random Forest feature importance
# ---------------------------------------------------------------------------

def save_random_forest_feature_importance(
    fitted_model: object,
    top_n: int = 20,
) -> pd.DataFrame:
    """
    Extract and save Random Forest feature importances.

    Parameters
    ----------
    fitted_model:
        Fitted TransformedTargetRegressor containing the Random Forest
        preprocessing and model pipeline.

    top_n:
        Number of highest-ranked encoded features shown in the figure.

    Returns
    -------
    pd.DataFrame
        Complete feature-importance table sorted from highest to lowest.
    """

    regression_pipeline = fitted_model.regressor_

    preprocessor = regression_pipeline.named_steps[
        "preprocessor"
    ]

    random_forest = regression_pipeline.named_steps[
        "model"
    ]

    feature_names = (
        preprocessor.get_feature_names_out()
    )

    feature_importances = (
        random_forest.feature_importances_
    )

    if len(feature_names) != len(feature_importances):
        raise ValueError(
            "Feature-name count does not match "
            "Random Forest importance count."
        )

    importance_df = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": feature_importances,
        }
    )

    # Remove sklearn transformer prefixes for readability.
    importance_df["feature"] = (
        importance_df["feature"]
        .str.replace(
            "numeric__",
            "",
            regex=False,
        )
        .str.replace(
            "categorical__",
            "",
            regex=False,
        )
    )

    importance_df = (
        importance_df
        .sort_values(
            "importance",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    importance_df["rank"] = (
        importance_df.index + 1
    )

    importance_df = importance_df[
        [
            "rank",
            "feature",
            "importance",
        ]
    ]

    importance_df.to_csv(
        FEATURE_IMPORTANCE_PATH,
        index=False,
    )

    top_features = (
        importance_df
        .head(top_n)
        .sort_values(
            "importance",
            ascending=True,
        )
    )

    plt.figure(
        figsize=(11, 8),
    )

    bars = plt.barh(
        top_features["feature"],
        top_features["importance"],
    )

    plt.title(
        "Top Random Forest Feature Importances"
    )

    plt.xlabel(
        "Feature Importance"
    )

    plt.ylabel(
        "Feature"
    )

    for bar, value in zip(
        bars,
        top_features["importance"],
        strict=True,
    ):
        plt.text(
            bar.get_width(),
            bar.get_y()
            + bar.get_height() / 2,
            f"{value:.3f}",
            va="center",
            ha="left",
        )

    plt.tight_layout()

    plt.savefig(
        FEATURE_IMPORTANCE_FIGURE_PATH,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    LOGGER.info(
        "Saved Random Forest feature importance table: %s",
        FEATURE_IMPORTANCE_PATH,
    )

    LOGGER.info(
        "Saved Random Forest feature importance figure: %s",
        FEATURE_IMPORTANCE_FIGURE_PATH,
    )

    return importance_df


# ---------------------------------------------------------------------------
# Actual vs predicted diagnostic figure
# ---------------------------------------------------------------------------

def save_actual_vs_predicted_figure(
    actual_prices: pd.Series,
    predicted_prices: np.ndarray,
) -> None:
    """
    Save an actual-versus-predicted price diagnostic figure.

    For visual readability, only rows with actual prices at or below the
    99th percentile of the test-set actual-price distribution are plotted.

    No rows are removed from:
    - training,
    - model evaluation,
    - MAE,
    - RMSE,
    - R²,
    - saved prediction outputs.
    """

    diagnostic_df = pd.DataFrame(
        {
            "actual_price": (
                actual_prices
                .reset_index(drop=True)
                .astype(float)
            ),

            "predicted_price": np.asarray(
                predicted_prices,
                dtype=float,
            ),
        }
    )

    upper_limit = float(
        diagnostic_df[
            "actual_price"
        ].quantile(0.99)
    )

    plot_df = diagnostic_df.loc[
        diagnostic_df["actual_price"]
        <= upper_limit
    ].copy()

    if plot_df.empty:
        raise ValueError(
            "No observations were available for the "
            "actual-vs-predicted diagnostic figure."
        )

    max_axis_value = max(
        float(
            plot_df["actual_price"].max()
        ),
        float(
            plot_df["predicted_price"].max()
        ),
    )

    plt.figure(
        figsize=(8, 8),
    )

    plt.scatter(
        plot_df["actual_price"],
        plot_df["predicted_price"],
        alpha=0.45,
        s=25,
    )

    # Perfect-prediction reference line.
    plt.plot(
        [0, max_axis_value],
        [0, max_axis_value],
        linestyle="--",
        linewidth=1.5,
        label="Perfect prediction",
    )

    plt.title(
        "Actual vs Predicted Amsterdam Airbnb Prices\n"
        "Random Forest Regressor"
    )

    plt.xlabel(
        "Actual Price (€)"
    )

    plt.ylabel(
        "Predicted Price (€)"
    )

    plt.xlim(
        0,
        max_axis_value,
    )

    plt.ylim(
        0,
        max_axis_value,
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        ACTUAL_VS_PREDICTED_FIGURE_PATH,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    LOGGER.info(
        "Saved actual-vs-predicted figure: %s",
        ACTUAL_VS_PREDICTED_FIGURE_PATH,
    )

    LOGGER.info(
        "Diagnostic visualization limit: "
        "99th percentile of actual test price = €%.2f",
        upper_limit,
    )

    LOGGER.info(
        "Rows shown in diagnostic figure: %s / %s",
        f"{len(plot_df):,}",
        f"{len(diagnostic_df):,}",
    )


# ---------------------------------------------------------------------------
# Experiment summary
# ---------------------------------------------------------------------------

def log_experiment_summary(
    results_df: pd.DataFrame,
    feature_importance_df: pd.DataFrame,
) -> None:
    """
    Log the final model-comparison and interpretation summary.
    """

    LOGGER.info("")

    LOGGER.info(
        "=" * 72
    )

    LOGGER.info(
        "PRICE-PREDICTION EXPERIMENT COMPLETED"
    )

    LOGGER.info(
        "=" * 72
    )

    LOGGER.info(
        "\n%s",
        results_df.to_string(
            index=False,
        ),
    )

    best_model_row = results_df.iloc[0]

    LOGGER.info("")

    LOGGER.info(
        "Best model by MAE: %s",
        best_model_row["model"],
    )

    LOGGER.info(
        "Best MAE: €%.2f",
        best_model_row["mae_eur"],
    )

    LOGGER.info(
        "Best RMSE: €%.2f",
        best_model_row["rmse_eur"],
    )

    LOGGER.info(
        "Best R²: %.4f",
        best_model_row["r2"],
    )

    LOGGER.info("")

    LOGGER.info(
        "Top 10 Random Forest encoded features:"
    )

    LOGGER.info(
        "\n%s",
        feature_importance_df
        .head(10)
        .to_string(index=False),
    )


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Run the complete focused price-prediction experiment.

    Workflow:
    1. Load and validate data.
    2. Prepare train/test split.
    3. Train three regression models.
    4. Evaluate MAE, RMSE, and R².
    5. Save predictions and model comparison results.
    6. Extract Random Forest feature importance.
    7. Generate actual-vs-predicted diagnostic figure.
    8. Print final experiment summary.
    """

    LOGGER.info(
        "Starting Amsterdam Airbnb price-prediction experiment."
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ------------------------------------------------------------------
    # Load modeling data
    # ------------------------------------------------------------------

    modeling_df = load_modeling_data()

    feature_columns = (
        CATEGORICAL_FEATURES
        + NUMERICAL_FEATURES
    )

    x = modeling_df[
        feature_columns
    ].copy()

    y = modeling_df[
        TARGET_COLUMN
    ].astype("float64")

    # ------------------------------------------------------------------
    # Train/test split
    # ------------------------------------------------------------------

    (
        x_train,
        x_test,
        y_train,
        y_test,
    ) = train_test_split(
        x,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )

    LOGGER.info(
        "Training rows: %s",
        f"{len(x_train):,}",
    )

    LOGGER.info(
        "Test rows: %s",
        f"{len(x_test):,}",
    )

    # ------------------------------------------------------------------
    # Build models
    # ------------------------------------------------------------------

    models = build_models()

    results: list[
        dict[str, float | str]
    ] = []

    predictions_df = pd.DataFrame(
        {
            "actual_price": (
                y_test
                .reset_index(drop=True)
            ),
        }
    )

    random_forest_model = None

    random_forest_predictions = None

    # ------------------------------------------------------------------
    # Train and evaluate all models
    # ------------------------------------------------------------------

    for model_name, model in models.items():

        result, predictions = evaluate_model(
            model_name=model_name,
            model=model,
            x_train=x_train,
            x_test=x_test,
            y_train=y_train,
            y_test=y_test,
        )

        results.append(
            result
        )

        safe_column_name = (
            model_name
            .lower()
            .replace(" ", "_")
        )

        predictions_df[
            f"{safe_column_name}_prediction"
        ] = predictions

        if model_name == "Random Forest Regressor":
            random_forest_model = model

            random_forest_predictions = predictions

    # ------------------------------------------------------------------
    # Build final result table
    # ------------------------------------------------------------------

    results_df = pd.DataFrame(
        results
    ).sort_values(
        "mae_eur",
        ascending=True,
    ).reset_index(
        drop=True
    )

    # ------------------------------------------------------------------
    # Save experiment result files
    # ------------------------------------------------------------------

    results_df.to_csv(
        RESULTS_PATH,
        index=False,
    )

    predictions_df.to_csv(
        PREDICTIONS_PATH,
        index=False,
    )

    # ------------------------------------------------------------------
    # Save model comparison visualization
    # ------------------------------------------------------------------

    save_model_comparison_figure(
        results_df
    )

    # ------------------------------------------------------------------
    # Validate Random Forest outputs
    # ------------------------------------------------------------------

    if (
        random_forest_model is None
        or random_forest_predictions is None
    ):
        raise RuntimeError(
            "The fitted Random Forest model or predictions "
            "were not available for interpretation."
        )

    # ------------------------------------------------------------------
    # Save Random Forest feature importance
    # ------------------------------------------------------------------

    feature_importance_df = (
        save_random_forest_feature_importance(
            fitted_model=random_forest_model,
            top_n=20,
        )
    )

    # ------------------------------------------------------------------
    # Save actual-vs-predicted diagnostic
    # ------------------------------------------------------------------

    save_actual_vs_predicted_figure(
        actual_prices=y_test,
        predicted_prices=random_forest_predictions,
    )

    # ------------------------------------------------------------------
    # Log final experiment summary
    # ------------------------------------------------------------------

    log_experiment_summary(
        results_df=results_df,
        feature_importance_df=feature_importance_df,
    )

    # ------------------------------------------------------------------
    # Log output locations
    # ------------------------------------------------------------------

    LOGGER.info("")

    LOGGER.info(
        "Saved results: %s",
        RESULTS_PATH,
    )

    LOGGER.info(
        "Saved predictions: %s",
        PREDICTIONS_PATH,
    )

    LOGGER.info(
        "Saved model comparison figure: %s",
        MODEL_COMPARISON_FIGURE_PATH,
    )

    LOGGER.info(
        "Saved feature importance table: %s",
        FEATURE_IMPORTANCE_PATH,
    )

    LOGGER.info(
        "Saved feature importance figure: %s",
        FEATURE_IMPORTANCE_FIGURE_PATH,
    )

    LOGGER.info(
        "Saved actual-vs-predicted figure: %s",
        ACTUAL_VS_PREDICTED_FIGURE_PATH,
    )


# ---------------------------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
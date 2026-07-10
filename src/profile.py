"""
Automated dataset profiling for the Amsterdam Airbnb project.

This module profiles all seven raw source files and generates two consolidated
data-quality reports:

    outputs/data_quality/dataset_summary.csv
    outputs/data_quality/column_profile.csv

Design goals:
- Reusable and repeatable.
- Safe for an 8 GB RAM laptop.
- Pandas for small/medium datasets.
- DuckDB for large detailed calendar and review datasets.
- Raw source files are never modified.
"""

from __future__ import annotations

import gc
import json
import logging
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "amsterdam"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "data_quality"
DUCKDB_TEMP_DIR = OUTPUT_DIR / "duckdb_temp"

DATASET_SUMMARY_PATH = OUTPUT_DIR / "dataset_summary.csv"
COLUMN_PROFILE_PATH = OUTPUT_DIR / "column_profile.csv"


# ---------------------------------------------------------------------------
# Profiling configuration
# ---------------------------------------------------------------------------

SAMPLE_VALUE_LIMIT = 3
MAX_SAMPLE_LENGTH = 120

# Exact distinct counts on large free-text columns can be expensive and add
# little analytical value. Missingness and sample values are still recorded.
SKIP_EXACT_UNIQUE_COLUMNS = {"comments"}

DATASETS = [
    {
        "dataset_name": "neighbourhoods",
        "file_name": "neighbourhoods.csv",
        "file_type": "csv",
        "engine": "pandas",
    },
    {
        "dataset_name": "summary_listings",
        "file_name": "listings.csv",
        "file_type": "csv",
        "engine": "pandas",
    },
    {
        "dataset_name": "summary_reviews",
        "file_name": "reviews.csv",
        "file_type": "csv",
        "engine": "pandas",
    },
    {
        "dataset_name": "detailed_listings",
        "file_name": "listings.csv.gz",
        "file_type": "csv.gz",
        "engine": "pandas",
    },
    {
        "dataset_name": "neighbourhoods_geojson",
        "file_name": "neighbourhoods.geojson",
        "file_type": "geojson",
        "engine": "geojson",
    },
    {
        "dataset_name": "calendar",
        "file_name": "calendar.csv.gz",
        "file_type": "csv.gz",
        "engine": "duckdb",
    },
    {
        "dataset_name": "detailed_reviews",
        "file_name": "reviews.csv.gz",
        "file_type": "csv.gz",
        "engine": "duckdb",
    },
]


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# General helper functions
# ---------------------------------------------------------------------------

def _file_size_mb(path: Path) -> float:
    """Return file size in megabytes."""
    return round(path.stat().st_size / (1024 * 1024), 3)


def _clean_sample_value(value: Any) -> str:
    """
    Convert a sample value to a compact single-line string.

    Long text is truncated so column_profile.csv remains readable.
    """
    text = str(value).replace("\r", " ").replace("\n", " ")
    text = " ".join(text.split())

    if len(text) > MAX_SAMPLE_LENGTH:
        return text[: MAX_SAMPLE_LENGTH - 3] + "..."

    return text


def _sample_values_from_series(
    series: pd.Series,
    limit: int = SAMPLE_VALUE_LIMIT,
) -> str:
    """Return up to `limit` distinct non-null sample values."""
    values = series.dropna().drop_duplicates().head(limit).tolist()
    return " | ".join(_clean_sample_value(value) for value in values)


def _safe_pandas_min_max(series: pd.Series) -> tuple[Any, Any]:
    """
    Return minimum and maximum only for meaningful ordered Pandas dtypes.

    Raw text columns are intentionally not assigned lexical min/max values.
    """
    if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_datetime64_any_dtype(series):
        non_null = series.dropna()

        if non_null.empty:
            return None, None

        return non_null.min(), non_null.max()

    return None, None


def _quote_identifier(identifier: str) -> str:
    """Safely quote a SQL identifier for DuckDB."""
    return '"' + identifier.replace('"', '""') + '"'


def _escape_sql_path(path: Path) -> str:
    """Escape a filesystem path for use inside a SQL string literal."""
    return path.resolve().as_posix().replace("'", "''")


def _is_duckdb_range_type(data_type: str) -> bool:
    """Return True when min/max values are meaningful for the DuckDB type."""
    data_type = data_type.upper()

    prefixes = (
        "TINYINT",
        "SMALLINT",
        "INTEGER",
        "BIGINT",
        "HUGEINT",
        "UTINYINT",
        "USMALLINT",
        "UINTEGER",
        "UBIGINT",
        "FLOAT",
        "REAL",
        "DOUBLE",
        "DECIMAL",
        "DATE",
        "TIMESTAMP",
        "TIME",
    )

    return data_type.startswith(prefixes)


# ---------------------------------------------------------------------------
# Pandas profiler
# ---------------------------------------------------------------------------

def profile_with_pandas(
    dataset_name: str,
    file_name: str,
    file_type: str,
    path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """
    Profile a small or medium CSV/CSV.GZ file with Pandas.

    The full DataFrame exists only while the current dataset is being profiled.
    """
    LOGGER.info("Profiling %s with Pandas...", file_name)

    df = pd.read_csv(path, low_memory=False)

    row_count = len(df)
    column_count = len(df.columns)
    duplicate_count = int(df.duplicated().sum())

    dataset_summary = {
        "dataset_name": dataset_name,
        "file_name": file_name,
        "file_type": file_type,
        "file_size_mb": _file_size_mb(path),
        "row_count": row_count,
        "column_count": column_count,
        "duplicate_count": duplicate_count,
        "duplicate_method": "exact_pandas",
        "processing_engine": "pandas",
        "status": "SUCCESS",
        "error_message": None,
    }

    column_profiles: list[dict[str, Any]] = []

    for column_name in df.columns:
        series = df[column_name]

        missing_count = int(series.isna().sum())
        missing_percentage = (
            round((missing_count / row_count) * 100, 4)
            if row_count > 0
            else 0.0
        )

        unique_count = int(series.nunique(dropna=True))
        minimum, maximum = _safe_pandas_min_max(series)

        column_profiles.append(
            {
                "dataset_name": dataset_name,
                "file_name": file_name,
                "column_name": column_name,
                "data_type": str(series.dtype),
                "missing_count": missing_count,
                "missing_percentage": missing_percentage,
                "unique_count": unique_count,
                "minimum": minimum,
                "maximum": maximum,
                "sample_values": _sample_values_from_series(series),
                "profile_note": None,
            }
        )

    # Explicitly release the current DataFrame before moving to the next file.
    del df
    gc.collect()

    return dataset_summary, column_profiles


# ---------------------------------------------------------------------------
# GeoJSON profiler
# ---------------------------------------------------------------------------

def profile_geojson(
    dataset_name: str,
    file_name: str,
    file_type: str,
    path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Profile GeoJSON feature properties plus geometry type."""
    LOGGER.info("Profiling %s with Python JSON + Pandas...", file_name)

    with path.open("r", encoding="utf-8") as file:
        geojson_data = json.load(file)

    features = geojson_data.get("features", [])

    property_names = sorted(
        {
            property_name
            for feature in features
            for property_name in feature.get("properties", {}).keys()
        }
    )

    rows = []

    for feature in features:
        properties = feature.get("properties", {})
        geometry = feature.get("geometry") or {}

        row = {
            property_name: properties.get(property_name)
            for property_name in property_names
        }
        row["geometry_type"] = geometry.get("type")
        rows.append(row)

    df = pd.DataFrame(rows)

    # Exact full-feature duplicate check, including geometry and properties.
    serialized_features = [
        json.dumps(feature, sort_keys=True, ensure_ascii=False)
        for feature in features
    ]
    duplicate_count = len(serialized_features) - len(set(serialized_features))

    dataset_summary = {
        "dataset_name": dataset_name,
        "file_name": file_name,
        "file_type": file_type,
        "file_size_mb": _file_size_mb(path),
        "row_count": len(features),
        "column_count": len(df.columns),
        "duplicate_count": duplicate_count,
        "duplicate_method": "exact_full_feature_json",
        "processing_engine": "python_json+pandas",
        "status": "SUCCESS",
        "error_message": None,
    }

    column_profiles: list[dict[str, Any]] = []

    for column_name in df.columns:
        series = df[column_name]
        row_count = len(df)

        missing_count = int(series.isna().sum())
        missing_percentage = (
            round((missing_count / row_count) * 100, 4)
            if row_count > 0
            else 0.0
        )

        column_profiles.append(
            {
                "dataset_name": dataset_name,
                "file_name": file_name,
                "column_name": column_name,
                "data_type": str(series.dtype),
                "missing_count": missing_count,
                "missing_percentage": missing_percentage,
                "unique_count": int(series.nunique(dropna=True)),
                "minimum": None,
                "maximum": None,
                "sample_values": _sample_values_from_series(series),
                "profile_note": (
                    "GeoJSON property or derived geometry type; "
                    "lexical min/max not reported."
                ),
            }
        )

    del df, geojson_data, features, serialized_features
    gc.collect()

    return dataset_summary, column_profiles


# ---------------------------------------------------------------------------
# DuckDB profiler for large datasets
# ---------------------------------------------------------------------------

def profile_with_duckdb(
    dataset_name: str,
    file_name: str,
    file_type: str,
    path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """
    Profile a large CSV.GZ file with DuckDB without loading it into Pandas.

    A conservative DuckDB memory limit is used, and temporary disk spilling is
    enabled through a dedicated temporary directory.
    """
    LOGGER.info("Profiling %s with DuckDB...", file_name)

    DUCKDB_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(database=":memory:")

    try:
        con.execute("SET memory_limit = '3GB'")
        con.execute("SET preserve_insertion_order = false")

        temp_path_sql = _escape_sql_path(DUCKDB_TEMP_DIR)
        con.execute(f"SET temp_directory = '{temp_path_sql}'")

        source_path_sql = _escape_sql_path(path)

        relation = (
            f"read_csv_auto("
            f"'{source_path_sql}', "
            f"header=true, "
            f"sample_size=200000"
            f")"
        )

        schema_rows = con.execute(
            f"DESCRIBE SELECT * FROM {relation}"
        ).fetchall()

        columns = [
            {
                "column_name": row[0],
                "data_type": row[1],
            }
            for row in schema_rows
        ]

        row_count = int(
            con.execute(
                f"SELECT COUNT(*) FROM {relation}"
            ).fetchone()[0]
        )

        # Memory-aware full-row duplicate check.
        #
        # Hashing all columns avoids materializing a huge full-width GROUP BY
        # key. Equal rows produce equal hashes. A hash collision is theoretically
        # possible but extremely unlikely; the method is recorded transparently.
        hash_arguments = ", ".join(
            _quote_identifier(column["column_name"])
            for column in columns
        )

        duplicate_count = int(
            con.execute(
                f"""
                SELECT
                    COUNT(*) - COUNT(DISTINCT hash({hash_arguments}))
                FROM {relation}
                """
            ).fetchone()[0]
        )

        dataset_summary = {
            "dataset_name": dataset_name,
            "file_name": file_name,
            "file_type": file_type,
            "file_size_mb": _file_size_mb(path),
            "row_count": row_count,
            "column_count": len(columns),
            "duplicate_count": duplicate_count,
            "duplicate_method": "duckdb_full_row_hash",
            "processing_engine": "duckdb",
            "status": "SUCCESS",
            "error_message": None,
        }

        # Build one aggregate query for missingness, exact distinct counts
        # (except deliberately skipped free-text fields), and useful min/max.
        aggregate_expressions: list[str] = []
        metric_positions: dict[str, dict[str, int | None]] = {}
        current_position = 0

        for index, column in enumerate(columns):
            column_name = column["column_name"]
            data_type = column["data_type"]
            quoted_column = _quote_identifier(column_name)

            positions: dict[str, int | None] = {
                "missing_count": None,
                "unique_count": None,
                "minimum": None,
                "maximum": None,
            }

            aggregate_expressions.append(
                f"SUM(CASE WHEN {quoted_column} IS NULL THEN 1 ELSE 0 END)"
            )
            positions["missing_count"] = current_position
            current_position += 1

            if column_name.lower() not in SKIP_EXACT_UNIQUE_COLUMNS:
                aggregate_expressions.append(
                    f"COUNT(DISTINCT {quoted_column})"
                )
                positions["unique_count"] = current_position
                current_position += 1

            if _is_duckdb_range_type(data_type):
                aggregate_expressions.append(
                    f"CAST(MIN({quoted_column}) AS VARCHAR)"
                )
                positions["minimum"] = current_position
                current_position += 1

                aggregate_expressions.append(
                    f"CAST(MAX({quoted_column}) AS VARCHAR)"
                )
                positions["maximum"] = current_position
                current_position += 1

            metric_positions[column_name] = positions

        aggregate_row = con.execute(
            f"""
            SELECT {", ".join(aggregate_expressions)}
            FROM {relation}
            """
        ).fetchone()

        column_profiles: list[dict[str, Any]] = []

        for column in columns:
            column_name = column["column_name"]
            data_type = column["data_type"]
            quoted_column = _quote_identifier(column_name)

            positions = metric_positions[column_name]

            missing_count = int(
                aggregate_row[positions["missing_count"]]
            )
            missing_percentage = (
                round((missing_count / row_count) * 100, 4)
                if row_count > 0
                else 0.0
            )

            unique_position = positions["unique_count"]

            if unique_position is None:
                unique_count = None
                profile_note = (
                    "Exact distinct count skipped for high-cardinality "
                    "free-text column."
                )
            else:
                unique_count = int(aggregate_row[unique_position])
                profile_note = None

            minimum_position = positions["minimum"]
            maximum_position = positions["maximum"]

            minimum = (
                aggregate_row[minimum_position]
                if minimum_position is not None
                else None
            )
            maximum = (
                aggregate_row[maximum_position]
                if maximum_position is not None
                else None
            )

            sample_rows = con.execute(
                f"""
                SELECT DISTINCT {quoted_column}
                FROM {relation}
                WHERE {quoted_column} IS NOT NULL
                LIMIT {SAMPLE_VALUE_LIMIT}
                """
            ).fetchall()

            sample_values = " | ".join(
                _clean_sample_value(row[0])
                for row in sample_rows
            )

            column_profiles.append(
                {
                    "dataset_name": dataset_name,
                    "file_name": file_name,
                    "column_name": column_name,
                    "data_type": data_type,
                    "missing_count": missing_count,
                    "missing_percentage": missing_percentage,
                    "unique_count": unique_count,
                    "minimum": minimum,
                    "maximum": maximum,
                    "sample_values": sample_values,
                    "profile_note": profile_note,
                }
            )

        return dataset_summary, column_profiles

    finally:
        con.close()
        gc.collect()


# ---------------------------------------------------------------------------
# Dataset dispatcher
# ---------------------------------------------------------------------------

def profile_dataset(
    dataset_config: dict[str, str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Route a dataset to the correct profiling engine."""
    dataset_name = dataset_config["dataset_name"]
    file_name = dataset_config["file_name"]
    file_type = dataset_config["file_type"]
    engine = dataset_config["engine"]

    path = RAW_DIR / file_name

    if not path.exists():
        raise FileNotFoundError(
            f"Required source file was not found: {path}"
        )

    if engine == "pandas":
        return profile_with_pandas(
            dataset_name=dataset_name,
            file_name=file_name,
            file_type=file_type,
            path=path,
        )

    if engine == "duckdb":
        return profile_with_duckdb(
            dataset_name=dataset_name,
            file_name=file_name,
            file_type=file_type,
            path=path,
        )

    if engine == "geojson":
        return profile_geojson(
            dataset_name=dataset_name,
            file_name=file_name,
            file_type=file_type,
            path=path,
        )

    raise ValueError(
        f"Unsupported profiling engine '{engine}' for {file_name}"
    )


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    """Profile all seven datasets and write consolidated CSV reports."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Starting automated dataset profiling.")
    LOGGER.info("Raw data directory: %s", RAW_DIR)
    LOGGER.info("Output directory: %s", OUTPUT_DIR)

    dataset_summaries: list[dict[str, Any]] = []
    all_column_profiles: list[dict[str, Any]] = []
    failed_datasets: list[str] = []

    for dataset_config in DATASETS:
        dataset_name = dataset_config["dataset_name"]
        file_name = dataset_config["file_name"]
        file_type = dataset_config["file_type"]
        engine = dataset_config["engine"]
        path = RAW_DIR / file_name

        try:
            summary, column_profiles = profile_dataset(dataset_config)

            dataset_summaries.append(summary)
            all_column_profiles.extend(column_profiles)

            LOGGER.info(
                "Completed %s: %s rows, %s columns.",
                file_name,
                f"{summary['row_count']:,}",
                summary["column_count"],
            )

        except Exception as error:
            LOGGER.exception("Failed to profile %s", file_name)

            failed_datasets.append(file_name)

            dataset_summaries.append(
                {
                    "dataset_name": dataset_name,
                    "file_name": file_name,
                    "file_type": file_type,
                    "file_size_mb": (
                        _file_size_mb(path)
                        if path.exists()
                        else None
                    ),
                    "row_count": None,
                    "column_count": None,
                    "duplicate_count": None,
                    "duplicate_method": None,
                    "processing_engine": engine,
                    "status": "FAILED",
                    "error_message": str(error),
                }
            )

        finally:
            gc.collect()

    dataset_summary_df = pd.DataFrame(dataset_summaries)
    column_profile_df = pd.DataFrame(all_column_profiles)

    dataset_summary_df.to_csv(
        DATASET_SUMMARY_PATH,
        index=False,
        encoding="utf-8",
    )

    column_profile_df.to_csv(
        COLUMN_PROFILE_PATH,
        index=False,
        encoding="utf-8",
    )

    LOGGER.info("Saved: %s", DATASET_SUMMARY_PATH)
    LOGGER.info("Saved: %s", COLUMN_PROFILE_PATH)
    LOGGER.info(
        "Profiling finished: %s/%s datasets succeeded.",
        len(DATASETS) - len(failed_datasets),
        len(DATASETS),
    )

    if failed_datasets:
        LOGGER.error(
            "Failed datasets: %s",
            ", ".join(failed_datasets),
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()

"""
Raw-source ingestion and verification utilities.

This module provides:

- The canonical Amsterdam source-file manifest
- Raw input verification
- Safe Pandas loading for small and medium datasets
- DuckDB access helpers for larger detailed datasets
- Compact source inventory generation

Raw source files are treated as immutable inputs and are never modified.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from src.utils import (
    PROJECT_ROOT,
    RAW_DATA_DIR,
    escape_sql_path,
    file_size_mb,
    get_logger,
)


LOGGER = get_logger(__name__)


# ---------------------------------------------------------------------------
# Source configuration
# ---------------------------------------------------------------------------

SUPPORTED_CITIES = {"amsterdam"}

REQUIRED_RAW_FILES = (
    "listings.csv.gz",
    "listings.csv",
    "calendar.csv.gz",
    "reviews.csv.gz",
    "reviews.csv",
    "neighbourhoods.csv",
    "neighbourhoods.geojson",
)


DATASET_MANIFEST: dict[str, dict[str, str]] = {
    "summary_listings": {
        "file_name": "listings.csv",
        "engine": "pandas",
        "description": "Canonical summary listing population.",
    },
    "detailed_listings": {
        "file_name": "listings.csv.gz",
        "engine": "pandas",
        "description": "Detailed listing attributes.",
    },
    "summary_reviews": {
        "file_name": "reviews.csv",
        "engine": "pandas",
        "description": "Summary review events by listing and date.",
    },
    "detailed_reviews": {
        "file_name": "reviews.csv.gz",
        "engine": "duckdb",
        "description": "Detailed individual review events.",
    },
    "calendar": {
        "file_name": "calendar.csv.gz",
        "engine": "duckdb",
        "description": "Daily listing availability and price observations.",
    },
    "neighbourhoods": {
        "file_name": "neighbourhoods.csv",
        "engine": "pandas",
        "description": "Neighbourhood reference metadata.",
    },
    "neighbourhood_geojson": {
        "file_name": "neighbourhoods.geojson",
        "engine": "geojson",
        "description": "Neighbourhood geographic boundaries.",
    },
}


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def get_city_raw_dir(city: str = "amsterdam") -> Path:
    """
    Return the raw-data directory for a supported city.
    """
    normalized_city = city.strip().lower()

    if normalized_city not in SUPPORTED_CITIES:
        raise ValueError(
            f"Unsupported city: {city!r}. "
            f"Supported cities: {sorted(SUPPORTED_CITIES)}"
        )

    return RAW_DATA_DIR / normalized_city


def get_dataset_path(
    dataset_name: str,
    city: str = "amsterdam",
) -> Path:
    """
    Return the filesystem path for a named source dataset.
    """
    if dataset_name not in DATASET_MANIFEST:
        raise KeyError(
            f"Unknown dataset: {dataset_name!r}. "
            f"Available datasets: {sorted(DATASET_MANIFEST)}"
        )

    file_name = DATASET_MANIFEST[dataset_name]["file_name"]
    return get_city_raw_dir(city) / file_name


# ---------------------------------------------------------------------------
# Raw input verification
# ---------------------------------------------------------------------------

def verify_raw_inputs(city: str = "amsterdam") -> dict[str, Path]:
    """
    Verify that all required raw source files exist.

    Parameters
    ----------
    city:
        Supported city name.

    Returns
    -------
    dict[str, Path]
        Mapping of required file names to verified filesystem paths.

    Raises
    ------
    FileNotFoundError
        If the city directory or one or more required files are missing.
    """
    city_raw_dir = get_city_raw_dir(city)

    LOGGER.info("Verifying raw source files...")
    LOGGER.info("Raw data directory: %s", city_raw_dir)

    if not city_raw_dir.exists():
        raise FileNotFoundError(
            f"Raw data directory does not exist: {city_raw_dir}"
        )

    verified_files: dict[str, Path] = {}
    missing_files: list[str] = []

    for file_name in REQUIRED_RAW_FILES:
        path = city_raw_dir / file_name

        if path.exists() and path.is_file():
            verified_files[file_name] = path
        else:
            missing_files.append(file_name)

    if missing_files:
        raise FileNotFoundError(
            "The following required raw source files are missing: "
            + ", ".join(missing_files)
        )

    LOGGER.info(
        "Raw input verification passed: %s/%s required files found.",
        len(verified_files),
        len(REQUIRED_RAW_FILES),
    )

    return verified_files


# ---------------------------------------------------------------------------
# Pandas ingestion
# ---------------------------------------------------------------------------

def load_pandas_dataset(
    dataset_name: str,
    city: str = "amsterdam",
    *,
    usecols: list[str] | None = None,
    nrows: int | None = None,
    low_memory: bool = False,
    **read_csv_kwargs: Any,
) -> pd.DataFrame:
    """
    Load a CSV or compressed CSV source using Pandas.

    Intended primarily for small and medium source files.

    Parameters
    ----------
    dataset_name:
        Key from DATASET_MANIFEST.
    city:
        Supported city.
    usecols:
        Optional subset of columns.
    nrows:
        Optional row limit.
    low_memory:
        Forwarded to pandas.read_csv.
    **read_csv_kwargs:
        Additional keyword arguments forwarded to pandas.read_csv.
    """
    dataset = DATASET_MANIFEST.get(dataset_name)

    if dataset is None:
        raise KeyError(f"Unknown dataset: {dataset_name!r}")

    if dataset["engine"] not in {"pandas"}:
        raise ValueError(
            f"Dataset {dataset_name!r} is configured for "
            f"{dataset['engine']!r}, not Pandas."
        )

    path = get_dataset_path(dataset_name, city)

    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    LOGGER.info(
        "Loading dataset with Pandas: %s | %.3f MB",
        dataset_name,
        file_size_mb(path),
    )

    return pd.read_csv(
        path,
        usecols=usecols,
        nrows=nrows,
        low_memory=low_memory,
        **read_csv_kwargs,
    )


# ---------------------------------------------------------------------------
# DuckDB ingestion helpers
# ---------------------------------------------------------------------------

def create_raw_duckdb_connection(
    memory_limit: str = "3GB",
) -> duckdb.DuckDBPyConnection:
    """
    Create an in-memory DuckDB connection for large-file processing.

    The conservative default memory limit supports the project's
    8 GB RAM-aware architecture.
    """
    connection = duckdb.connect(database=":memory:")
    connection.execute(f"SET memory_limit = '{memory_limit}'")
    connection.execute("SET preserve_insertion_order = false")

    return connection


def raw_csv_relation_sql(
    dataset_name: str,
    city: str = "amsterdam",
) -> str:
    """
    Return a DuckDB read_csv_auto expression for a source dataset.
    """
    dataset = DATASET_MANIFEST.get(dataset_name)

    if dataset is None:
        raise KeyError(f"Unknown dataset: {dataset_name!r}")

    path = get_dataset_path(dataset_name, city)

    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    escaped_path = escape_sql_path(path)

    return (
        f"read_csv_auto("
        f"'{escaped_path}', "
        f"header=true, "
        f"sample_size=-1, "
        f"all_varchar=false"
        f")"
    )


# ---------------------------------------------------------------------------
# Source inventory
# ---------------------------------------------------------------------------

def build_source_inventory(
    city: str = "amsterdam",
) -> pd.DataFrame:
    """
    Build a compact inventory of all configured raw source datasets.
    """
    verify_raw_inputs(city)

    rows: list[dict[str, Any]] = []

    for dataset_name, metadata in DATASET_MANIFEST.items():
        path = get_dataset_path(dataset_name, city)

        rows.append(
            {
                "dataset_name": dataset_name,
                "file_name": metadata["file_name"],
                "engine": metadata["engine"],
                "description": metadata["description"],
                "file_size_mb": file_size_mb(path),
                "path": str(path.relative_to(PROJECT_ROOT)),
            }
        )

    return pd.DataFrame(rows).sort_values(
        "dataset_name"
    ).reset_index(drop=True)


if __name__ == "__main__":
    inventory = build_source_inventory("amsterdam")
    print(inventory.to_string(index=False))
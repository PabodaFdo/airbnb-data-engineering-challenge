"""
Shared utility helpers for the Amsterdam Airbnb data engineering project.

This module contains lightweight helpers that can be reused across pipeline
stages without introducing business logic or dataset-specific transformations.
"""

from __future__ import annotations

import gc
import logging
from pathlib import Path


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
WAREHOUSE_DIR = DATA_DIR / "warehouse"

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
DATA_QUALITY_OUTPUT_DIR = OUTPUTS_DIR / "data_quality"
EDA_OUTPUT_DIR = OUTPUTS_DIR / "eda"
STATISTICS_OUTPUT_DIR = OUTPUTS_DIR / "statistics"

DOCS_DIR = PROJECT_ROOT / "docs"
SQL_DIR = PROJECT_ROOT / "sql"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"


def get_logger(name: str) -> logging.Logger:
    """
    Return a consistently configured project logger.

    Parameters
    ----------
    name:
        Usually ``__name__`` from the calling module.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format=DEFAULT_LOG_FORMAT,
        )

    return logger


# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------

def ensure_directory(path: Path) -> Path:
    """
    Create a directory and its parents when they do not already exist.

    Returns the same Path object for convenient inline use.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def require_file(path: Path) -> Path:
    """
    Verify that a required file exists.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Required file was not found: {path}")

    if not path.is_file():
        raise FileNotFoundError(f"Expected a file but found another object: {path}")

    return path


def file_size_mb(path: Path) -> float:
    """Return file size in megabytes."""
    require_file(path)
    return round(path.stat().st_size / (1024 * 1024), 3)


def escape_sql_path(path: Path) -> str:
    """
    Escape a filesystem path for safe use inside a DuckDB SQL string literal.
    """
    return path.resolve().as_posix().replace("'", "''")


# ---------------------------------------------------------------------------
# Memory helpers
# ---------------------------------------------------------------------------

def release_memory() -> None:
    """
    Request garbage collection between memory-intensive pipeline stages.

    This is useful for the project's 8 GB RAM-aware processing strategy.
    """
    gc.collect()


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_count(value: int | float) -> str:
    """Format a numeric count with thousands separators."""
    return f"{int(value):,}"


def percentage(
    numerator: int | float,
    denominator: int | float,
    decimals: int = 2,
) -> float:
    """
    Calculate a percentage safely.

    Returns 0.0 when the denominator is zero.
    """
    if denominator == 0:
        return 0.0

    return round((numerator / denominator) * 100, decimals)
"""
Read-only analytical database access utilities.

Warehouse creation is implemented separately in:

    src/build_warehouse.py

This module provides lightweight helpers for:

- Opening the DuckDB analytical warehouse
- Running read-only SQL queries
- Listing warehouse tables and views
- Previewing analytical objects
- Inspecting schemas

The separation keeps warehouse construction and analytical consumption
as distinct responsibilities.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from src.utils import WAREHOUSE_DIR, get_logger


LOGGER = get_logger(__name__)


WAREHOUSE_PATH = WAREHOUSE_DIR / "airbnb_analytics.duckdb"


# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------

def get_warehouse_connection(
    *,
    read_only: bool = True,
) -> duckdb.DuckDBPyConnection:
    """
    Open the analytical DuckDB warehouse.

    Parameters
    ----------
    read_only:
        Open the database in read-only mode by default to protect
        analytical tables from accidental modification.
    """
    if not WAREHOUSE_PATH.exists():
        raise FileNotFoundError(
            "DuckDB analytical warehouse was not found: "
            f"{WAREHOUSE_PATH}. "
            "Run `python run_pipeline.py --city amsterdam` first."
        )

    LOGGER.info(
        "Opening DuckDB warehouse: %s | read_only=%s",
        WAREHOUSE_PATH,
        read_only,
    )

    return duckdb.connect(
        database=str(WAREHOUSE_PATH),
        read_only=read_only,
    )


# ---------------------------------------------------------------------------
# Read-only query execution
# ---------------------------------------------------------------------------

def _validate_read_only_query(query: str) -> None:
    """
    Reject common write operations from analytical query helpers.

    This is a lightweight safety guard and is not intended to replace
    database permissions.
    """
    normalized = " ".join(query.strip().lower().split())

    blocked_prefixes = (
        "insert ",
        "update ",
        "delete ",
        "drop ",
        "alter ",
        "truncate ",
        "create ",
        "replace ",
        "copy ",
        "attach ",
        "detach ",
    )

    if normalized.startswith(blocked_prefixes):
        raise ValueError(
            "Only read-only analytical queries are allowed by this helper."
        )


def run_query(
    query: str,
    *,
    parameters: list | tuple | None = None,
) -> pd.DataFrame:
    """
    Execute a read-only SQL query and return the result as a DataFrame.
    """
    if not query.strip():
        raise ValueError("SQL query must not be empty.")

    _validate_read_only_query(query)

    connection = get_warehouse_connection(read_only=True)

    try:
        if parameters is None:
            result = connection.execute(query).fetchdf()
        else:
            result = connection.execute(query, parameters).fetchdf()

        return result

    finally:
        connection.close()


# ---------------------------------------------------------------------------
# Warehouse inspection
# ---------------------------------------------------------------------------

def list_warehouse_objects() -> pd.DataFrame:
    """
    Return warehouse tables and views.
    """
    query = """
        SELECT
            table_schema,
            table_name,
            table_type
        FROM information_schema.tables
        WHERE table_schema NOT IN (
            'information_schema',
            'pg_catalog'
        )
        ORDER BY table_type, table_name
    """

    return run_query(query)


def preview_table(
    object_name: str,
    limit: int = 10,
) -> pd.DataFrame:
    """
    Preview rows from a warehouse table or view.

    The object name is validated against information_schema before use.
    """
    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    available_objects = list_warehouse_objects()

    valid_names = set(
        available_objects["table_name"]
        .dropna()
        .astype(str)
        .tolist()
    )

    if object_name not in valid_names:
        raise ValueError(
            f"Unknown warehouse object: {object_name!r}. "
            f"Available objects: {sorted(valid_names)}"
        )

    safe_name = object_name.replace('"', '""')

    return run_query(
        f'SELECT * FROM "{safe_name}" LIMIT {int(limit)}'
    )


def describe_table(object_name: str) -> pd.DataFrame:
    """
    Return column metadata for a validated warehouse table or view.
    """
    available_objects = list_warehouse_objects()

    valid_names = set(
        available_objects["table_name"]
        .dropna()
        .astype(str)
        .tolist()
    )

    if object_name not in valid_names:
        raise ValueError(
            f"Unknown warehouse object: {object_name!r}"
        )

    return run_query(
        """
        SELECT
            column_name,
            data_type,
            is_nullable,
            ordinal_position
        FROM information_schema.columns
        WHERE table_name = ?
        ORDER BY ordinal_position
        """,
        parameters=[object_name],
    )


if __name__ == "__main__":
    print("Warehouse objects:")
    print(list_warehouse_objects().to_string(index=False))
"""
End-to-end pipeline entry point for the Amsterdam Airbnb
Data Engineering Challenge.

Pipeline stages:
1. Verify raw source files
2. Automated dataset profiling
3. Data-quality validation
4. Stop on critical validation failures
5. Cleaning and standardization
6. Data enrichment
7. DuckDB analytical warehouse creation

Example:
    python run_pipeline.py --city amsterdam
"""

from __future__ import annotations

import argparse
import gc
import logging
import time
from collections.abc import Callable
from pathlib import Path

import pandas as pd

from src import build_warehouse
from src import clean
from src import enrich
from src import ingest
from src import profile
from src import validate


# ---------------------------------------------------------------------------
# Project configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent

VALIDATION_RESULTS_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "data_quality"
    / "validation_results.csv"
)

# Reuse the supported-city configuration from src/ingest.py
SUPPORTED_CITIES = ingest.SUPPORTED_CITIES


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    force=True,
)

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Validation gate
# ---------------------------------------------------------------------------

def enforce_validation_gate() -> None:
    """
    Stop the pipeline when validation_results.csv contains critical FAIL rows.

    WARNING findings are allowed to continue because they may represent
    genuine source-data limitations that have already been documented.

    FAIL findings indicate critical structural or domain problems that should
    be investigated before cleaning and downstream processing.
    """

    LOGGER.info("Checking validation gate...")

    if not VALIDATION_RESULTS_PATH.exists():
        raise FileNotFoundError(
            "Validation results were not generated: "
            f"{VALIDATION_RESULTS_PATH}"
        )

    results = pd.read_csv(VALIDATION_RESULTS_PATH)

    required_columns = {
        "dataset_name",
        "rule_id",
        "rule_description",
        "status",
    }

    missing_columns = required_columns - set(results.columns)

    if missing_columns:
        raise ValueError(
            "Validation results are missing required columns: "
            f"{sorted(missing_columns)}"
        )

    statuses = (
        results["status"]
        .astype("string")
        .str.upper()
        .str.strip()
    )

    failed_results = results.loc[statuses == "FAIL"].copy()

    if not failed_results.empty:
        LOGGER.error(
            "Validation gate FAILED: %s critical rule(s) failed.",
            len(failed_results),
        )

        for _, row in failed_results.head(10).iterrows():
            LOGGER.error(
                "[%s] %s | %s | %s",
                row["rule_id"],
                row["dataset_name"],
                row["rule_description"],
                row.get(
                    "invalid_count",
                    "unknown invalid count",
                ),
            )

        if len(failed_results) > 10:
            LOGGER.error(
                "%s additional failed rule(s) are available in %s.",
                len(failed_results) - 10,
                VALIDATION_RESULTS_PATH,
            )

        raise RuntimeError(
            "Critical data-quality validation failures were found. "
            "Review outputs/data_quality/validation_results.csv "
            "before continuing."
        )

    warning_count = int((statuses == "WARNING").sum())
    pass_count = int((statuses == "PASS").sum())

    LOGGER.info(
        "Validation gate passed: %s PASS, %s WARNING, 0 FAIL.",
        pass_count,
        warning_count,
    )

    LOGGER.info(
        "Warnings are preserved as documented source-data limitations "
        "and do not automatically block downstream processing."
    )

    del results
    del statuses
    del failed_results

    gc.collect()


# ---------------------------------------------------------------------------
# Stage runner
# ---------------------------------------------------------------------------

def run_stage(
    stage_number: int,
    total_stages: int,
    stage_name: str,
    stage_function: Callable[[], object],
) -> float:
    """
    Execute one pipeline stage with timing, logging, memory cleanup,
    and clear failure handling.

    Parameters
    ----------
    stage_number:
        Current pipeline stage number.

    total_stages:
        Total number of pipeline stages.

    stage_name:
        Human-readable stage name.

    stage_function:
        Callable that performs the stage work.

    Returns
    -------
    float
        Elapsed execution time in seconds.
    """

    LOGGER.info("")
    LOGGER.info("=" * 72)

    LOGGER.info(
        "STAGE %s/%s: %s",
        stage_number,
        total_stages,
        stage_name,
    )

    LOGGER.info("=" * 72)

    start_time = time.perf_counter()

    try:
        stage_function()

    except SystemExit as error:
        # Some existing modules intentionally use SystemExit(1)
        # when an unrecoverable stage failure occurs.
        exit_code = error.code

        if exit_code not in (None, 0):
            raise RuntimeError(
                f"Stage '{stage_name}' exited with code {exit_code}."
            ) from error

    except Exception:
        LOGGER.exception(
            "Pipeline stage failed: %s",
            stage_name,
        )

        raise

    finally:
        # Help release temporary Python objects between
        # memory-intensive pipeline stages.
        gc.collect()

    elapsed_seconds = time.perf_counter() - start_time

    LOGGER.info(
        "Completed stage: %s | %.2f seconds",
        stage_name,
        elapsed_seconds,
    )

    return elapsed_seconds


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(city: str) -> None:
    """
    Run the complete Airbnb Data Engineering pipeline.

    Current supported scope:
        Amsterdam, Netherlands

    Parameters
    ----------
    city:
        City dataset to process.
    """

    normalized_city = city.lower().strip()

    if normalized_city not in SUPPORTED_CITIES:
        raise ValueError(
            f"Unsupported city: {city!r}. "
            f"Supported cities: {sorted(SUPPORTED_CITIES)}"
        )

    LOGGER.info("")
    LOGGER.info("=" * 72)
    LOGGER.info("AMSTERDAM AIRBNB DATA ENGINEERING PIPELINE")
    LOGGER.info("=" * 72)

    LOGGER.info(
        "Selected city: %s",
        normalized_city.title(),
    )

    LOGGER.info(
        "Execution strategy: 8 GB RAM-aware, one stage at a time."
    )

    pipeline_start = time.perf_counter()

    stage_results: list[tuple[str, float]] = []

    total_stages = 7

    # ------------------------------------------------------------------
    # Stage 1: Verify raw inputs
    # ------------------------------------------------------------------

    elapsed = run_stage(
        stage_number=1,
        total_stages=total_stages,
        stage_name="Verify Raw Source Files",
        stage_function=lambda: ingest.verify_raw_inputs(
            normalized_city
        ),
    )

    stage_results.append(
        ("Verify Raw Source Files", elapsed)
    )

    # ------------------------------------------------------------------
    # Stage 2: Automated profiling
    # ------------------------------------------------------------------

    elapsed = run_stage(
        stage_number=2,
        total_stages=total_stages,
        stage_name="Automated Dataset Profiling",
        stage_function=profile.main,
    )

    stage_results.append(
        ("Automated Dataset Profiling", elapsed)
    )

    # ------------------------------------------------------------------
    # Stage 3: Data-quality validation
    # ------------------------------------------------------------------

    elapsed = run_stage(
        stage_number=3,
        total_stages=total_stages,
        stage_name="Data-Quality Validation",
        stage_function=validate.main,
    )

    stage_results.append(
        ("Data-Quality Validation", elapsed)
    )

    # ------------------------------------------------------------------
    # Stage 4: Validation gate
    # ------------------------------------------------------------------

    elapsed = run_stage(
        stage_number=4,
        total_stages=total_stages,
        stage_name="Critical Validation Gate",
        stage_function=enforce_validation_gate,
    )

    stage_results.append(
        ("Critical Validation Gate", elapsed)
    )

    # ------------------------------------------------------------------
    # Stage 5: Cleaning and standardization
    # ------------------------------------------------------------------

    elapsed = run_stage(
        stage_number=5,
        total_stages=total_stages,
        stage_name="Cleaning and Standardization",
        stage_function=clean.main,
    )

    stage_results.append(
        ("Cleaning and Standardization", elapsed)
    )

    # ------------------------------------------------------------------
    # Stage 6: Data enrichment
    # ------------------------------------------------------------------

    elapsed = run_stage(
        stage_number=6,
        total_stages=total_stages,
        stage_name="Data Enrichment",
        stage_function=enrich.main,
    )

    stage_results.append(
        ("Data Enrichment", elapsed)
    )

    # ------------------------------------------------------------------
    # Stage 7: DuckDB analytical warehouse
    # ------------------------------------------------------------------

    elapsed = run_stage(
        stage_number=7,
        total_stages=total_stages,
        stage_name="DuckDB Analytical Warehouse",
        stage_function=build_warehouse.main,
    )

    stage_results.append(
        ("DuckDB Analytical Warehouse", elapsed)
    )

    # ------------------------------------------------------------------
    # Final summary
    # ------------------------------------------------------------------

    total_elapsed = time.perf_counter() - pipeline_start

    LOGGER.info("")
    LOGGER.info("=" * 72)
    LOGGER.info("PIPELINE COMPLETED SUCCESSFULLY")
    LOGGER.info("=" * 72)

    for stage_name, elapsed_seconds in stage_results:
        LOGGER.info(
            "%-35s %10.2f seconds",
            stage_name,
            elapsed_seconds,
        )

    LOGGER.info("-" * 72)

    LOGGER.info(
        "%-35s %10.2f seconds",
        "Total pipeline execution time",
        total_elapsed,
    )

    LOGGER.info("")
    LOGGER.info(
        "Core engineering workflow completed:"
    )

    LOGGER.info(
        "Raw verification -> Profiling -> Validation -> "
        "Cleaning -> Enrichment -> DuckDB warehouse"
    )

    LOGGER.info(
        "Raw source files were preserved unchanged."
    )

    LOGGER.info(
        "Calendar unavailability remains labelled only as a proxy "
        "and is not treated as verified occupancy."
    )


# ---------------------------------------------------------------------------
# Command-line interface
# ---------------------------------------------------------------------------

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns
    -------
    argparse.Namespace
        Parsed command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Run the Amsterdam Airbnb Data Engineering pipeline."
        )
    )

    parser.add_argument(
        "--city",
        default="amsterdam",
        choices=sorted(SUPPORTED_CITIES),
        help=(
            "City dataset to process. "
            "Currently supported: amsterdam."
        ),
    )

    return parser.parse_args()


def main() -> int:
    """
    Command-line entry point.

    Returns
    -------
    int
        Process exit code.
    """

    args = parse_arguments()

    try:
        run_pipeline(args.city)

    except KeyboardInterrupt:
        LOGGER.warning(
            "Pipeline execution was interrupted by the user."
        )

        return 130

    except Exception:
        LOGGER.exception(
            "Pipeline execution FAILED."
        )

        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
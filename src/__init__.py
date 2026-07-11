"""
Core package for the Amsterdam Airbnb Data Engineering & Analytics Challenge.

The package contains reusable modules for:

- Raw source ingestion and verification
- Automated dataset profiling
- Data-quality validation
- Cleaning and standardization
- Listing-level enrichment
- DuckDB analytical warehouse construction
- Shared project utilities

The project follows a one-city, depth-first strategy for Amsterdam,
Netherlands, with memory-aware processing designed for an 8 GB RAM laptop.
"""

from __future__ import annotations

__author__ = "Paboda Sathsarani Fernando"
__version__ = "1.0.0"

__all__ = [
    "ingest",
    "profile",
    "validate",
    "clean",
    "enrich",
    "build_warehouse",
    "database",
    "utils",
]
# AI Usage Disclosure

## Purpose

This document explains how generative AI was used during the Amsterdam Airbnb Data Engineering Challenge.

AI was used as a support tool for planning, code review, debugging, statistical guidance, testing, and documentation. All important outputs were validated against the actual code, datasets, pipeline results, and generated reports.

---

## AI Tool Used

**ChatGPT — GPT-5.5 Thinking**

---

## Areas Where AI Was Used

AI assistance was used for:

- Project scope and prioritization.
- 8 GB RAM-aware architecture planning.
- Dataset familiarization guidance.
- Data-quality reasoning.
- Cleaning and missing-value decisions.
- Enrichment and join strategy.
- DuckDB warehouse design.
- SQL query planning.
- EDA topic selection.
- Statistical methodology guidance.
- Debugging and code review.
- End-to-end pipeline orchestration.
- Automated test design.
- Documentation structure and editing.

---

## Examples of AI-Assisted Work

Examples include:

- Choosing a one-city, depth-first strategy.
- Using Pandas for smaller datasets and DuckDB for large files.
- Preserving missing prices as null instead of zero.
- Preserving 96 summary-only listings during enrichment.
- Aggregating reviews and calendar data before joining to the listing master.
- Treating calendar unavailability only as a proxy, not true occupancy.
- Designing the final pipeline flow.
- Suggesting high-value unit and integrity tests.

---

## How AI Outputs Were Validated

AI suggestions were not accepted automatically.

Validation included:

- Running the full pipeline locally.
- Checking row counts and unique keys.
- Reviewing missing values and warnings.
- Verifying processed Parquet outputs.
- Reconciling DuckDB warehouse counts.
- Reviewing statistical results.
- Running automated tests.

Final verified results include:

```text
10,465 canonical listings
545,162 review events
3,819,725 calendar rows

83 PASS
7 WARNING
0 FAIL

17 warehouse checks passed

13 automated tests passed
0 failed
Representative Prompts

Examples of prompts used:

Review the assignment requirements and create a realistic one-city implementation plan for an 8 GB RAM laptop.

Help me inspect the Airbnb datasets for missing values, duplicates, keys, relationships, and limitations.

Review these validation results and help classify them as PASS, WARNING, or FAIL.

Help design a safe enrichment strategy that preserves one row per listing.

Help connect the existing project modules into one end-to-end pipeline.

Suggest focused tests for cleaning, key integrity, joins, and derived features.

Modifications Made

AI suggestions were changed when they did not match the actual data.

Examples:

Missing prices were preserved as null.
Unavailable host fields were not fabricated.
96 summary-only listings were preserved.
Repeated review dates were not blindly deleted.
Calendar unavailability was not called occupancy.
Optional machine learning and multi-city analysis were deferred.
Final Disclosure Statement

Generative AI was used as a planning, review, debugging, testing, and documentation assistant.

All important technical outputs and analytical results were validated using actual project data, local execution, generated reports, warehouse reconciliation, statistical outputs, and automated tests.

Final responsibility for the implementation, analysis, documentation, and conclusions remains with the project author.


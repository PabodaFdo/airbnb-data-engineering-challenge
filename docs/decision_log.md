# Engineering Decision Log

## Purpose

This document records the major engineering, data-quality, analytical, and scope decisions made during the Amsterdam Airbnb Data Engineering Challenge.

The purpose of this log is to make important trade-offs explicit and reproducible.

Each decision documents:

- The problem or context.
- Options considered.
- Final choice.
- Reasoning.
- Trade-offs and limitations.

The project was intentionally developed using a depth-first strategy, with emphasis on data understanding, reproducibility, validation, efficient processing on an 8 GB RAM laptop, and transparent analytical reasoning.

---

# Decision Summary

| ID | Decision | Final Choice |
|---|---|---|
| D01 | Number of cities | Amsterdam only |
| D02 | Project strategy | Depth over breadth |
| D03 | Canonical listing source | `listings.csv` |
| D04 | Large-file processing | DuckDB |
| D05 | Small/medium-file processing | Pandas |
| D06 | 8 GB RAM strategy | Sequential memory-aware processing |
| D07 | Processed storage format | Parquet |
| D08 | Missing prices | Preserve as null |
| D09 | Listing enrichment join strategy | Preserve canonical listing population |
| D10 | Review/calendar join strategy | Aggregate before joining |
| D11 | Calendar availability interpretation | Unavailability proxy only |
| D12 | Repeated review-date rows | Preserve unless true duplicates are proven |
| D13 | Data-quality validation | PASS/WARNING/FAIL framework |
| D14 | Pipeline failure behavior | Stop on critical FAIL results |
| D15 | Analytical database | DuckDB |
| D16 | Warehouse design | Lightweight analytical dimensional model |
| D17 | Statistical analysis | Two rigorous hypotheses |
| D18 | Outlier handling | Preserve by default |
| D19 | Neighbourhood analysis | Minimum sample thresholds |
| D20 | Machine learning | Not prioritized |
| D21 | Testing strategy | High-value unit and integrity tests |
| D22 | Raw-data handling | Immutable raw layer |
| D23 | Scope differences across source files | Preserve and document |
| D24 | AI assistance | Disclose and independently validate |
| D25 | Public repository content | Exclude confidential assignment and large raw data |

---

# D01 — Select One City Only

## Context

The assignment allows different levels of scope, including single-city and multi-city analysis.

The available execution time was limited, and expanding to multiple cities would introduce:

- Additional downloads.
- Schema comparison.
- Cross-city harmonization.
- Currency considerations.
- Different data-quality conditions.
- Additional validation requirements.
- More complex reporting.

## Options Considered

1. One city.
2. Two to three cities.
3. Four or more cities.

## Decision

**Use Amsterdam, Netherlands only.**

## Reason

A one-city scope enables deeper work in:

- Dataset familiarization.
- Data-quality analysis.
- Reusable pipeline development.
- Cleaning.
- Enrichment.
- SQL.
- Statistical analysis.
- EDA.
- Documentation.
- Business interpretation.

## Trade-off

The project does not provide cross-city benchmarking or generalize findings to other Airbnb markets.

---

# D02 — Prioritize Depth Over Breadth

## Context

The assignment contains many possible engineering, analytics, statistical, dashboard, and machine-learning tasks.

Attempting every optional feature would risk producing incomplete or poorly validated work.

## Options Considered

1. Attempt many tasks superficially.
2. Complete a focused set deeply and professionally.

## Decision

**Prioritize depth, quality, reproducibility, and clear reasoning.**

## Reason

The selected scope focuses on:

- Complete dataset familiarization.
- Automated profiling.
- Data-quality validation.
- Cleaning.
- Enrichment.
- DuckDB warehouse construction.
- SQL analysis.
- EDA.
- Statistical testing.
- Automated tests.
- Professional documentation.

## Trade-off

Some optional features, including machine learning and a production dashboard, were not prioritized.

---

# D03 — Use `listings.csv` as the Canonical Listing Population

## Context

The two listing datasets do not contain exactly the same number of listings.

Observed counts:

- `listings.csv`: 10,465 listings.
- `listings.csv.gz`: 10,369 listings.

There are 96 canonical summary listings that do not appear in the detailed listings source.

## Options Considered

1. Use detailed listings only.
2. Use the intersection of both sources.
3. Treat the summary listings file as the canonical population and preserve unmatched records.

## Decision

**Use `listings.csv` as the canonical listing population.**

## Reason

This preserves all 10,465 listing records instead of silently discarding 96 summary-only listings.

## Trade-off

The 96 unmatched listings have reduced detailed attribute coverage.

Their unavailable detailed attributes remain null rather than being fabricated.

---

# D04 — Use DuckDB for Large Detailed Files

## Context

The project must process:

- 3,819,725 calendar rows.
- 545,162 detailed review rows.

The development machine has 8 GB of RAM.

Loading all large raw files simultaneously into Pandas would increase memory pressure and risk crashes.

## Options Considered

1. Pandas only.
2. Chunked Pandas.
3. PostgreSQL.
4. PySpark.
5. DuckDB.

## Decision

**Use DuckDB for large-file profiling, validation, aggregation, and analytical processing where appropriate.**

## Reason

DuckDB provides:

- Direct CSV and Parquet querying.
- Efficient analytical SQL.
- No external database server requirement.
- Disk spilling support.
- Strong compatibility with Python.
- Low setup overhead.

## Trade-off

The project uses more than one data-processing interface: Pandas and SQL through DuckDB.

---

# D05 — Use Pandas for Small and Medium Datasets

## Context

Not every dataset requires a database-oriented processing strategy.

Files such as:

- Summary listings.
- Detailed listings.
- Neighbourhood CSV.
- Compact processed outputs.

are manageable in memory.

## Options Considered

1. Use DuckDB for everything.
2. Use Pandas for everything.
3. Use the appropriate tool according to dataset size and operation.

## Decision

**Use Pandas for small and medium datasets and DuckDB for larger datasets and analytical aggregations.**

## Reason

This balances:

- Simplicity.
- Readability.
- Developer productivity.
- Memory efficiency.
- Performance.

## Trade-off

Developers must understand both Pandas and DuckDB SQL.

---

# D06 — Design the Pipeline for an 8 GB RAM Laptop

## Context

The project is developed locally on a Windows laptop with 8 GB RAM.

The raw calendar dataset alone contains approximately 3.82 million rows.

## Options Considered

1. Load all datasets into memory simultaneously.
2. Downsample the source data.
3. Use sequential memory-aware processing.
4. Move the entire project to cloud infrastructure.

## Decision

**Process one major stage at a time and avoid retaining unnecessary large DataFrames.**

The implementation uses:

- DuckDB for large datasets.
- Compact aggregations.
- Parquet intermediate outputs.
- Listing-level joins.
- Garbage collection between pipeline stages.
- A conservative DuckDB memory configuration.

## Reason

This allows full-data processing without sacrificing source coverage.

## Trade-off

Some operations may be slower than using significantly larger hardware, but the pipeline remains reliable and reproducible on the target environment.

---

# D07 — Use Parquet for Processed Data

## Context

Processed datasets are repeatedly consumed by:

- Enrichment.
- Warehouse construction.
- EDA.
- Statistics.
- Testing.

## Options Considered

1. CSV.
2. JSON.
3. Parquet.

## Decision

**Use Parquet for cleaned, aggregated, and enriched datasets.**

Examples include:

- `cleaned_listings.parquet`
- `cleaned_detailed_listings.parquet`
- `review_listing_aggregates.parquet`
- `calendar_listing_aggregates.parquet`
- `enriched_listing_master.parquet`

## Reason

Parquet provides:

- Columnar storage.
- Smaller disk footprint.
- Faster analytical reads.
- Data-type preservation.
- Efficient interoperability with Pandas and DuckDB.

## Trade-off

Parquet is less directly human-readable than CSV.

---

# D08 — Preserve Missing Prices as Null

## Context

Observed missing prices:

- Summary listings: 3,994 missing values.
- Detailed listings: 3,992 missing values.

## Options Considered

1. Replace missing prices with zero.
2. Replace with mean.
3. Replace with median.
4. Drop affected listings.
5. Preserve as null and use a legitimate fallback when available.

## Decision

**Preserve missing prices as null.**

The best-available price logic is:

1. Use summary-listing price when available.
2. Otherwise use detailed-listing price when available.
3. Otherwise preserve null.

## Reason

A missing price does not mean:

- Free accommodation.
- Zero revenue.
- Average market price.

Artificial imputation could distort pricing analysis.

## Trade-off

Some price-based analyses use fewer than the full 10,465 canonical listings.

---

# D09 — Preserve the Canonical Population During Enrichment

## Context

A naive inner join between summary and detailed listings would remove 96 canonical listings.

## Options Considered

1. Inner join.
2. Right join.
3. Left-preserving enrichment from the canonical summary population.

## Decision

**Use a left-preserving enrichment strategy based on the canonical listing population.**

## Reason

This prevents silent source-data loss.

Final enriched result:

**10,465 rows with unique, non-null listing IDs.**

## Trade-off

Some rows contain null values for attributes available only from unmatched detailed records.

---

# D10 — Aggregate Reviews and Calendar Data Before Joining

## Context

The source relationships are one-to-many:

```text
Listing
   ├── many Calendar rows
   └── many Review rows

Joining raw reviews and raw calendar rows directly to listings could create:

Massive intermediate datasets.
Row multiplication.
Memory pressure.
Incorrect metrics.
Options Considered
Join all raw rows directly.
Aggregate to listing level first.
Decision

Aggregate both review and calendar data to one row per listing before joining to the listing master.

Reason

This protects the intended final grain:

One row per listing.

It also improves:

Memory efficiency.
Join safety.
Metric clarity.
Reproducibility.
Trade-off

The enriched master does not contain every individual review comment or daily calendar row.

Those raw events remain available separately when detailed analysis is required.

---

# D11 — Treat Calendar Unavailability as a Proxy, Not True Occupancy
## Context

The calendar dataset shows whether dates are available or unavailable.

However, an unavailable date could mean:

A confirmed booking.
Host blocking.
Maintenance.
Personal use.
Regulation.
Other unknown reasons.
Options Considered
Call unavailable dates occupied.
Estimate occupancy without qualification.
Use explicit proxy terminology.
Decision

Use unavailability_rate_proxy and never describe it as verified occupancy.

Reason

The source data does not prove why a date is unavailable.

Trade-off

The project cannot calculate true occupancy without confirmed booking data.

---

# D12 — Preserve Repeated Review-Date Rows Unless True Duplicate Events Are Proven
## Context

The summary reviews dataset contains 22,541 repeated (listing_id, date) rows.

Because the summary file contains only listing ID and date, multiple legitimate reviews on the same day may appear identical at this reduced grain.

Options Considered
Drop all repeated (listing_id, date) rows.
Preserve repeated rows unless duplicate review-event identity is established.
Decision

Preserve repeated review-date rows.

Reason

Blind deletion could remove legitimate review events.

The detailed reviews file contains review-level identifiers and is more appropriate for true event-level duplicate validation.

Trade-off

The summary reviews file should not be interpreted as having a unique (listing_id, date) key.

---

# D13 — Use PASS, WARNING, and FAIL Validation Statuses
## Context

Not every data-quality condition should have the same severity.

Examples:

Duplicate primary key → critical.
Missing price → important limitation but not necessarily fatal.
Missing reviewer name → non-critical metadata issue.
Options Considered
Binary valid/invalid framework.
Multi-level severity classification.
Decision

Use three validation statuses:

PASS
WARNING
FAIL
Reason

This distinguishes between:

Valid data.
Known limitations requiring interpretation.
Critical structural failures.

Observed validation result:

83 PASS.
7 WARNING.
0 FAIL.
Trade-off

Warnings require human interpretation and documentation.

---

# D14 — Stop the Pipeline on Critical Validation Failures
## Context

Continuing a data pipeline after critical structural failures could create invalid downstream outputs.

Options Considered
Always continue.
Stop on any warning.
Stop only on critical FAIL results.
Decision

Introduce a validation gate after the validation stage.

Pipeline behavior:

Validation
    │
    ├── FAIL exists → STOP
    │
    └── No FAIL → Continue

Warnings are allowed when they represent understood and documented source limitations.

Reason

This balances safety with practical robustness.

Trade-off

Correct severity classification is important because inappropriate FAIL classifications could stop valid processing.

---

# D15 — Use DuckDB as the Analytical Warehouse Engine
## Context

The project requires analytical SQL and structured downstream querying.

Options Considered
SQLite.
PostgreSQL.
MySQL.
DuckDB.
Decision

Use DuckDB.

Reason

DuckDB provides:

Embedded deployment.
No database server.
Strong analytical SQL.
Direct Parquet support.
Window functions.
Aggregations.
Good compatibility with the 8 GB RAM environment.
Trade-off

DuckDB is not being used as a transactional production database.

---

# D16 — Build a Lightweight Analytical Dimensional Model
## Context

A complex enterprise warehouse would add implementation overhead without clear value for a one-city take-home assignment.

Options Considered
One denormalized table only.
Highly complex multi-layer warehouse.
Simple analytical dimensional model.
Decision

Create a lightweight warehouse containing analytical entities such as:

enriched_listing_master
dim_listings
dim_neighbourhoods
fact_review_activity
fact_calendar_activity

and analytical views such as:

vw_neighbourhood_performance
vw_room_type_performance
vw_host_portfolio_performance
Reason

This provides sufficient structure for:

SQL analysis.
Business questions.
Reusable metrics.
Demonstration of data-modeling understanding.

Trade-off

The model is intentionally simpler than a production enterprise data warehouse.

---

# D17 — Complete Two Statistical Hypotheses Deeply
## Context

The statistical-analysis section could contain many possible tests.

However, more tests do not necessarily mean better statistical reasoning.

Options Considered
No statistical testing.
Many shallow tests.
Two carefully selected and fully documented hypotheses.
Decision

Complete two focused statistical hypotheses.

The selected topics compare:

Entire-home and private-room pricing.
Superhost and non-superhost review-score performance.
Reason

This allows proper attention to:

Hypothesis definition.
Assumption checking.
Test selection.
P-values.
Effect sizes.
Practical significance.
Business interpretation.
Trade-off

Additional hypotheses were not prioritized.

---

# D18 — Preserve Outliers by Default
## Context

Airbnb datasets can contain extreme values in:

Price.
Review counts.
Availability.
Capacity.

Extreme values may be genuine rather than erroneous.

Options Considered
Delete all statistical outliers.
Winsorize automatically.
Preserve by default and exclude only for justified analytical purposes.
Decision

Do not automatically delete outliers.

Reason

Being statistically unusual is not proof of being invalid.

Where necessary, visualizations may show:

Full data.
A restricted view without extreme upper outliers.

The original records remain preserved.

Trade-off

Some raw visualizations are heavily skewed and require careful presentation.

---

# D19 — Apply Minimum Sample Thresholds to Neighbourhood Rankings
## Context

Neighbourhood rankings can be misleading when a neighbourhood contains only a few listings.

Options Considered
Rank all neighbourhoods regardless of size.
Apply an explicitly documented minimum listing threshold.
Decision

Apply minimum sample thresholds where appropriate.

For example, selected SQL analyses use:

WHERE listing_count >= 100
Reason

This reduces unstable comparisons based on tiny samples.

Trade-off

Smaller neighbourhoods may be excluded from selected comparative rankings.

---

# D20 — Do Not Prioritize Machine Learning
## Context

Machine learning was optional but could require substantial additional time for:

Feature engineering.
Leakage prevention.
Train/test design.
Model comparison.
Evaluation.
Interpretation.
Options Considered
Build a rushed predictive model.
Complete the engineering and analytical core first.
Decision

Do not prioritize machine learning in the core submission.

Reason

The available time provides greater value when invested in:

Data quality.
Reproducible pipelines.
Warehouse design.
Testing.
EDA.
Statistics.
Documentation.
Business storytelling.
Trade-off

No predictive model is included in the current project.

---

# D21 — Add High-Value Automated Tests
## Context

The pipeline contains important transformations and integrity requirements.

Options Considered
No automated tests.
Very large test suite.
Focused tests covering high-risk engineering logic.
Decision

Implement 13 focused automated tests.

The tests cover:

Price parsing.
Raw-price preservation.
Missing-price preservation.
Date parsing.
Invalid-date handling.
Boolean normalization.
Unknown Boolean handling.
Unique listing keys.
Duplicate ID rejection.
Null ID rejection.
Duplicate join-key rejection.
Derived-feature calculations.
Final canonical listing-grain preservation.
Result

13 tests passed successfully.

Trade-off

The suite is intentionally focused rather than exhaustive.

---

# D22 — Keep the Raw Layer Immutable
## Context

Overwriting raw source data reduces reproducibility and makes debugging more difficult.

Options Considered
Modify raw files directly.
Preserve raw files and write processed outputs separately.
Decision

Treat all raw source files as immutable.

Reason

This supports:

Reproducibility.
Traceability.
Debugging.
Auditing.
Reprocessing.
Trade-off

Additional disk space is required for processed outputs.

---

# D23 — Preserve Source Differences Instead of Forcing Equality
## Context

The summary and detailed datasets differ in:

Row counts.
Missingness.
Attribute coverage.
Listing coverage.
Options Considered
Force sources into identical populations.
Discard unmatched records.
Preserve and document genuine source differences.
Decision

Preserve source differences and make them explicit.

Reason

Forcing artificial equality could hide legitimate source limitations or silently delete records.

Trade-off

Some final fields have partial coverage.

---

# D24 — Disclose and Independently Validate AI Assistance
## Context

AI tools assisted with parts of:

Planning.
Code review.
Debugging.
Statistical methodology.
Documentation structuring.
Options Considered
Hide AI usage.
Copy AI-generated outputs without verification.
Disclose AI usage and independently validate all material outputs.
Decision

Use transparent AI disclosure and validate generated suggestions against actual code and data.

Validation methods include:

Executing code locally.
Running the complete pipeline.
Inspecting intermediate outputs.
Checking row counts.
Verifying uniqueness.
Reviewing null rates.
Running automated tests.
Verifying statistical outputs.
Rejecting unsupported suggestions.
Trade-off

AI-assisted work still requires manual validation and ownership by the author.

---

# D25 — Exclude Confidential and Unnecessary Large Files from Public GitHub
## Context

The assignment materials are confidential, and raw datasets may be unnecessarily large for version control.

Options Considered
Commit everything.
Exclude confidential and reproducible large files.
Decision

Do not publicly commit:

Confidential assignment PDF.
Secrets.
Environment files.
Large raw datasets when they can be downloaded from the source.
Local database files where unnecessary.
Reason

This protects confidentiality and keeps the repository clean.

Trade-off

Users may need to download source datasets separately before running the complete pipeline.

Final Reflection on Engineering Decisions

The central engineering strategy of this project was to prefer:

Explicit decisions over hidden assumptions.
Data preservation over silent deletion.
Context-aware null handling over blanket imputation.
Aggregation before one-to-many joins.
Reproducibility over notebook-only experimentation.
Memory-aware processing over unnecessary infrastructure.
Clear warnings over artificially perfect data-quality reports.
Statistical depth over excessive test quantity.
Business interpretation over disconnected charts.
Transparent limitations over unsupported claims.

The resulting pipeline successfully:

Profiles all seven Amsterdam datasets.
Validates source quality.
Preserves 10,465 canonical listings.
Aggregates 545,162 detailed review events.
Processes 3,819,725 calendar rows.
Produces cleaned and enriched Parquet datasets.
Builds a validated DuckDB analytical warehouse.
Stops on critical validation failures.
Completes with 83 PASS, 7 WARNING, and 0 FAIL validation outcomes.
Passes 17 warehouse validation checks.
Passes 13 automated tests.

These decisions reflect the project's primary objective: build a defensible, reproducible, memory-aware, and professionally documented data engineering workflow rather than maximizing feature count.
---
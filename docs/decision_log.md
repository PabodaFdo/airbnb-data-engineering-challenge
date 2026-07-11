# Engineering Decision Log

> **Project:** Amsterdam Airbnb Data Engineering & Analytics Challenge  
> **City:** Amsterdam, Netherlands  
> **Strategy:** One-city, depth-first, 8 GB RAM-aware implementation  
> **Primary Development Branch:** `dev`

---

## Purpose

This document records the major engineering, data-quality, analytical, statistical, machine-learning, testing, and scope decisions made during the Amsterdam Airbnb Data Engineering & Analytics Challenge.

The purpose of this log is to make important trade-offs explicit, reproducible, and reviewable.

Each decision documents:

- Context
- Options considered
- Final choice
- Reasoning
- Trade-offs and limitations

The project was intentionally developed using a depth-first strategy, with emphasis on:

- Data understanding
- Reproducibility
- Validation
- Memory-aware processing
- Analytical usefulness
- Statistical rigor
- Focused machine-learning experimentation
- Automated testing
- Continuous integration
- Transparent limitations
- Clear business interpretation

The project initially deferred several optional extensions until the engineering core was stable. After the core pipeline, warehouse, EDA, statistical analysis, tests, and documentation were completed, selected optional additions were implemented carefully rather than rushed.

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
| D19 | Neighbourhood analysis | Minimum sample thresholds where appropriate |
| D20 | Machine-learning timing | Stabilize engineering core first, then add one focused experiment |
| D21 | Testing strategy | High-value unit and integrity tests |
| D22 | Raw-data handling | Immutable raw layer |
| D23 | Scope differences across source files | Preserve and document |
| D24 | AI assistance | Disclose and independently validate |
| D25 | Public repository content | Exclude confidential assignment material and large raw data |
| D26 | Continuous integration | GitHub Actions |
| D27 | ML experiment target | Predict `price_best_available` |
| D28 | ML leakage prevention | Explicitly exclude price-derived features |
| D29 | ML model comparison | Dummy + Ridge + Random Forest |
| D30 | Skew handling for ML target | `log1p` target transformation |
| D31 | ML evaluation | Held-out test set with MAE, RMSE, and R² |
| D32 | ML interpretation | Feature importance + actual-vs-predicted diagnostics |
| D33 | Interactive dashboard technology | Streamlit planned as next extension |
| D34 | Dashboard data source | Processed Parquet and DuckDB outputs, not raw large files |
| D35 | Architecture communication | Maintain a visual architecture diagram in repository documentation |

---

# D01 — Select One City Only

## Context

The assignment allows different levels of scope, including single-city and multi-city analysis.

Expanding to multiple cities would introduce:

- Additional downloads
- Schema comparison
- Cross-city harmonization
- Market-specific interpretation
- Currency considerations
- Different data-quality conditions
- Additional validation requirements
- More complex reporting

## Options Considered

1. One city
2. Two to three cities
3. Four or more cities

## Decision

**Use Amsterdam, Netherlands only.**

## Reason

A one-city scope enables deeper work in:

- Dataset familiarization
- Data-quality analysis
- Reusable pipeline development
- Cleaning
- Enrichment
- SQL
- Statistical analysis
- EDA
- Machine-learning experimentation
- Testing
- Documentation
- Business interpretation

## Trade-off

The project does not provide cross-city benchmarking and findings should not be generalized automatically to other Airbnb markets.

---

# D02 — Prioritize Depth Over Breadth

## Context

The assignment contains many possible engineering, analytics, statistical, dashboard, cloud, and machine-learning tasks.

Attempting every optional feature immediately would risk producing incomplete or poorly validated work.

## Options Considered

1. Attempt many tasks superficially
2. Complete a focused set deeply and professionally
3. Build the engineering core first, then add selected optional extensions only if time remains

## Decision

**Prioritize depth, quality, reproducibility, and clear reasoning.**

The project follows a staged approach:

```text
Engineering Core
      ↓
Validation
      ↓
Warehouse
      ↓
EDA + Statistics
      ↓
Automated Tests
      ↓
Documentation
      ↓
Selected Optional Extensions
```

## Reason

The selected scope focuses on:

- Complete dataset familiarization
- Automated profiling
- Data-quality validation
- Cleaning
- Enrichment
- DuckDB warehouse construction
- SQL analysis
- EDA
- Statistical testing
- Automated tests
- Continuous integration
- Focused machine-learning experimentation
- Professional documentation

## Trade-off

Some optional features remain deferred, including multi-city analysis, cloud deployment, orchestration, Dockerization, and advanced production infrastructure.

---

# D03 — Use `listings.csv` as the Canonical Listing Population

## Context

The two listing datasets do not contain exactly the same number of listings.

Observed counts:

- `listings.csv`: **10,465 listings**
- `listings.csv.gz`: **10,369 listings**

There are **96 canonical summary listings** that do not appear in the detailed listings source.

## Options Considered

1. Use detailed listings only
2. Use the intersection of both sources
3. Treat the summary listings file as the canonical population and preserve unmatched records

## Decision

**Use `listings.csv` as the canonical listing population.**

## Reason

This preserves all **10,465 listing records** instead of silently discarding 96 summary-only listings.

## Trade-off

The 96 unmatched listings have reduced detailed-attribute coverage.

Unavailable detailed attributes remain null rather than being fabricated.

---

# D04 — Use DuckDB for Large Detailed Files

## Context

The project must process:

- **3,819,725 calendar rows**
- **545,162 detailed review rows**

The development machine has **8 GB RAM**.

Loading all large raw files simultaneously into Pandas would increase memory pressure and risk instability.

## Options Considered

1. Pandas only
2. Chunked Pandas
3. PostgreSQL
4. PySpark
5. DuckDB

## Decision

**Use DuckDB for large-file profiling, validation, aggregation, and analytical processing where appropriate.**

## Reason

DuckDB provides:

- Direct CSV and Parquet querying
- Efficient analytical SQL
- No external database server requirement
- Disk-spilling support
- Strong compatibility with Python
- Low setup overhead
- Good fit for local analytical workloads

## Trade-off

The project uses more than one data-processing interface: Pandas and DuckDB SQL.

---

# D05 — Use Pandas for Small and Medium Datasets

## Context

Not every dataset requires a database-oriented processing strategy.

Files such as:

- Summary listings
- Detailed listings
- Neighbourhood CSV
- Compact processed outputs

are manageable in memory.

## Options Considered

1. Use DuckDB for everything
2. Use Pandas for everything
3. Use the appropriate tool according to dataset size and operation

## Decision

**Use Pandas for small and medium datasets and DuckDB for larger datasets and analytical aggregations.**

## Reason

This balances:

- Simplicity
- Readability
- Developer productivity
- Memory efficiency
- Performance

## Trade-off

Developers must understand both Pandas and DuckDB SQL.

---

# D06 — Design the Pipeline for an 8 GB RAM Laptop

## Context

The project is developed locally on a Windows laptop with 8 GB RAM.

The raw calendar dataset alone contains approximately 3.82 million rows.

## Options Considered

1. Load all datasets into memory simultaneously
2. Downsample the source data
3. Use sequential memory-aware processing
4. Move the entire project to cloud infrastructure

## Decision

**Process one major stage at a time and avoid retaining unnecessary large DataFrames.**

The implementation uses:

- DuckDB for large datasets
- Compact aggregations
- Parquet intermediate outputs
- Listing-level joins
- Memory cleanup between stages where appropriate
- Conservative processing choices

## Reason

This allows full-data processing without sacrificing source coverage.

## Trade-off

Some operations may be slower than on significantly larger hardware, but the pipeline remains reliable and reproducible on the target environment.

---

# D07 — Use Parquet for Processed Data

## Context

Processed datasets are repeatedly consumed by:

- Enrichment
- Warehouse construction
- EDA
- Statistics
- Machine learning
- Testing
- Dashboarding

## Options Considered

1. CSV
2. JSON
3. Parquet

## Decision

**Use Parquet for cleaned, aggregated, and enriched datasets.**

Examples include:

```text
cleaned_listings.parquet
cleaned_detailed_listings.parquet
review_listing_aggregates.parquet
calendar_listing_aggregates.parquet
enriched_listing_master.parquet
```

## Reason

Parquet provides:

- Columnar storage
- Smaller disk footprint
- Faster analytical reads
- Data-type preservation
- Efficient interoperability with Pandas and DuckDB

## Trade-off

Parquet is less directly human-readable than CSV.

---

# D08 — Preserve Missing Prices as Null

## Context

Observed missing prices:

- Summary listings: **3,994 missing values**
- Detailed listings: **3,992 missing values**

## Options Considered

1. Replace missing prices with zero
2. Replace with mean
3. Replace with median
4. Drop affected listings
5. Preserve as null and use a legitimate fallback when available

## Decision

**Preserve missing prices as null.**

Best-available price logic:

1. Use summary-listing price when available.
2. Otherwise use detailed-listing price when available.
3. Otherwise preserve null.

## Reason

A missing price does not mean:

- Free accommodation
- Zero revenue
- Average market price

Artificial imputation could distort pricing analysis.

## Trade-off

Some price-based analyses use fewer than the full **10,465 canonical listings**.

---

# D09 — Preserve the Canonical Population During Enrichment

## Context

A naive inner join between summary and detailed listings would remove 96 canonical listings.

## Options Considered

1. Inner join
2. Right join
3. Left-preserving enrichment from the canonical summary population

## Decision

**Use a left-preserving enrichment strategy based on the canonical listing population.**

## Reason

This prevents silent source-data loss.

Final enriched result:

> **10,465 rows with unique, non-null listing IDs.**

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
```

Joining raw reviews and raw calendar rows directly to listings could create:

- Massive intermediate datasets
- Row multiplication
- Memory pressure
- Incorrect metrics

## Options Considered

1. Join all raw rows directly
2. Aggregate to listing level first

## Decision

**Aggregate review and calendar data to one row per listing before joining to the listing master.**

## Reason

This protects the intended final grain:

> **One row per listing**

It also improves:

- Memory efficiency
- Join safety
- Metric clarity
- Reproducibility

## Trade-off

The enriched master does not contain every individual review comment or daily calendar row.

Those detailed records remain available separately when needed.

---

# D11 — Treat Calendar Unavailability as a Proxy, Not True Occupancy

## Context

The calendar dataset shows whether dates are available or unavailable.

However, an unavailable date could mean:

- A confirmed booking
- Host blocking
- Maintenance
- Personal use
- Regulation
- Other unknown reasons

## Options Considered

1. Call unavailable dates occupied
2. Estimate occupancy without qualification
3. Use explicit proxy terminology

## Decision

**Use `unavailability_rate_proxy` and never describe it as verified occupancy.**

## Reason

The source data does not prove why a date is unavailable.

## Trade-off

The project cannot calculate true occupancy without confirmed booking data.

---

# D12 — Preserve Repeated Review-Date Rows Unless True Duplicate Events Are Proven

## Context

The summary reviews dataset contains **22,541 repeated `(listing_id, date)` rows beyond first occurrences**.

Because the summary file contains only listing ID and date, multiple legitimate reviews on the same date are possible.

## Options Considered

1. Drop all repeated `(listing_id, date)` rows
2. Preserve repeated rows unless duplicate review-event identity is established

## Decision

**Preserve repeated review-date rows.**

## Reason

Blind deletion could remove legitimate review events.

The detailed reviews file contains review-level identifiers and is more appropriate for true event-level duplicate validation.

## Trade-off

The summary reviews file should not be interpreted as having a unique `(listing_id, date)` key.

---

# D13 — Use PASS, WARNING, and FAIL Validation Statuses

## Context

Not every data-quality condition should have the same severity.

Examples:

- Duplicate primary key → critical
- Missing price → important limitation but not necessarily fatal
- Missing reviewer name → non-critical metadata issue

## Options Considered

1. Binary valid/invalid framework
2. Multi-level severity classification

## Decision

**Use three validation statuses:**

```text
PASS
WARNING
FAIL
```

## Reason

This distinguishes between:

- Valid data
- Known limitations requiring interpretation
- Critical structural failures

Observed result:

| Status | Count |
|---|---:|
| PASS | **83** |
| WARNING | **7** |
| FAIL | **0** |

## Trade-off

Warnings require human interpretation and documentation.

---

# D14 — Stop the Pipeline on Critical Validation Failures

## Context

Continuing a pipeline after critical structural failures could create invalid downstream outputs.

## Options Considered

1. Always continue
2. Stop on any warning
3. Stop only on critical FAIL results

## Decision

**Introduce a validation gate after the validation stage.**

Pipeline behavior:

```text
Validation
    │
    ├── FAIL exists → STOP
    │
    └── No FAIL → Continue
```

Warnings are allowed when they represent understood and documented source limitations.

## Reason

This balances safety with practical robustness.

## Trade-off

Correct severity classification is important because inappropriate FAIL classifications could stop otherwise valid processing.

---

# D15 — Use DuckDB as the Analytical Warehouse Engine

## Context

The project requires analytical SQL and structured downstream querying.

## Options Considered

1. SQLite
2. PostgreSQL
3. MySQL
4. DuckDB

## Decision

**Use DuckDB.**

## Reason

DuckDB provides:

- Embedded deployment
- No database server requirement
- Strong analytical SQL
- Direct Parquet support
- Window functions
- Aggregations
- Good compatibility with the 8 GB RAM environment

## Trade-off

DuckDB is not being used as a transactional production database.

---

# D16 — Build a Lightweight Analytical Dimensional Model

## Context

A complex enterprise warehouse would add implementation overhead without clear value for a one-city take-home assignment.

## Options Considered

1. One denormalized table only
2. Highly complex multi-layer warehouse
3. Simple analytical dimensional model

## Decision

**Create a lightweight warehouse containing analytical entities such as:**

```text
enriched_listing_master
dim_listings
dim_neighbourhoods
fact_review_activity
fact_calendar_activity
```

and analytical views such as:

```text
vw_neighbourhood_performance
vw_room_type_performance
vw_host_portfolio_performance
```

## Reason

This provides sufficient structure for:

- SQL analysis
- Business questions
- Reusable metrics
- Dashboard consumption
- Demonstration of data-modeling understanding

## Trade-off

The model is intentionally simpler than a production enterprise data warehouse.

---

# D17 — Complete Two Statistical Hypotheses Deeply

## Context

The statistical-analysis section could contain many possible tests.

However, more tests do not necessarily mean better statistical reasoning.

## Options Considered

1. No statistical testing
2. Many shallow tests
3. Two carefully selected and fully documented hypotheses

## Decision

**Complete two focused statistical hypotheses.**

Selected topics:

1. Entire-home versus private-room pricing
2. Superhost versus non-superhost review-score performance

## Reason

This allows proper attention to:

- Hypothesis definition
- Assumption checking
- Test selection
- P-values
- Effect sizes
- Practical significance
- Business interpretation

## Trade-off

Additional hypotheses were not prioritized.

---

# D18 — Preserve Outliers by Default

## Context

Airbnb datasets can contain extreme values in:

- Price
- Review counts
- Availability
- Capacity

Extreme values may be genuine rather than erroneous.

## Options Considered

1. Delete all statistical outliers
2. Winsorize automatically
3. Preserve by default and exclude only for justified analytical purposes

## Decision

**Do not automatically delete outliers.**

## Reason

Being statistically unusual is not proof of being invalid.

Where necessary, visualizations may show:

- Full data
- A restricted view without extreme upper outliers

The original records remain preserved.

## Trade-off

Some visualizations are heavily skewed and require careful presentation.

---

# D19 — Apply Minimum Sample Thresholds to Neighbourhood Rankings

## Context

Neighbourhood rankings can be misleading when a neighbourhood contains only a few listings.

## Options Considered

1. Rank all neighbourhoods regardless of size
2. Apply an explicitly documented minimum listing threshold

## Decision

**Apply minimum sample thresholds where appropriate.**

For example, selected SQL analyses use:

```sql
WHERE listing_count >= 100
```

## Reason

This reduces unstable comparisons based on tiny samples.

## Trade-off

Smaller neighbourhoods may be excluded from selected comparative rankings.

---

# D20 — Stabilize the Engineering Core Before Adding Machine Learning

## Context

Machine learning was initially optional and could have consumed substantial time for:

- Feature selection
- Leakage prevention
- Train/test design
- Model comparison
- Evaluation
- Interpretation
- Limitation analysis

Early in the project, the engineering and analytical core was not yet complete.

Later, after the pipeline, warehouse, EDA, statistical testing, automated tests, CI, and documentation had stabilized, additional time became available.

## Options Considered

1. Build a rushed predictive model early
2. Exclude machine learning completely
3. Stabilize the engineering core first, then add one focused experiment if time remained

## Decision

**Stabilize the core first, then add one focused machine-learning experiment.**

## Reason

This preserved the depth-first strategy while still allowing a defensible predictive extension.

The final experiment compares:

- Dummy Regressor
- Ridge Regression
- Random Forest Regressor

## Result

The Random Forest Regressor achieved:

| Metric | Result |
|---|---:|
| MAE | **€78.61** |
| RMSE | **€133.76** |
| R² | **0.5884** |

Compared with the Dummy Regressor baseline, MAE was reduced by approximately **41.7%**.

## Trade-off

The experiment remains intentionally focused and does not include extensive hyperparameter tuning, cross-validation, model serving, or production monitoring.

---

# D21 — Add High-Value Automated Tests

## Context

The pipeline contains important transformations and integrity requirements.

## Options Considered

1. No automated tests
2. Very large test suite
3. Focused tests covering high-risk engineering logic

## Decision

**Implement 13 focused automated tests.**

The tests cover:

- Price parsing
- Raw-price preservation
- Missing-price preservation
- Date parsing
- Invalid-date handling
- Boolean normalization
- Unknown Boolean handling
- Unique listing keys
- Duplicate ID rejection
- Null ID rejection
- Duplicate join-key rejection
- Derived-feature calculations
- Final canonical listing-grain preservation

## Result

```text
13 passed
0 failed
```

Latest local test runtime:

```text
1.32 seconds
```

## Trade-off

The suite is intentionally focused rather than exhaustive.

---

# D22 — Keep the Raw Layer Immutable

## Context

Overwriting raw source data reduces reproducibility and makes debugging more difficult.

## Options Considered

1. Modify raw files directly
2. Preserve raw files and write processed outputs separately

## Decision

**Treat all raw source files as immutable.**

## Reason

This supports:

- Reproducibility
- Traceability
- Debugging
- Auditing
- Reprocessing

## Trade-off

Additional disk space is required for processed outputs.

---

# D23 — Preserve Source Differences Instead of Forcing Equality

## Context

The summary and detailed datasets differ in:

- Row counts
- Missingness
- Attribute coverage
- Listing coverage

## Options Considered

1. Force sources into identical populations
2. Discard unmatched records
3. Preserve and document genuine source differences

## Decision

**Preserve source differences and make them explicit.**

## Reason

Forcing artificial equality could hide legitimate source limitations or silently delete records.

## Trade-off

Some final fields have partial coverage.

---

# D24 — Disclose and Independently Validate AI Assistance

## Context

AI tools assisted with parts of:

- Planning
- Architecture thinking
- Dataset-familiarization guidance
- Code review
- Debugging
- Statistical methodology
- Machine-learning experiment design
- Testing guidance
- Documentation structuring

## Options Considered

1. Hide AI usage
2. Copy AI-generated outputs without verification
3. Disclose AI usage and independently validate all material outputs

## Decision

**Use transparent AI disclosure and validate generated suggestions against actual code and data.**

## Validation Methods

- Executing code locally
- Running the complete pipeline
- Inspecting intermediate outputs
- Checking row counts
- Verifying uniqueness
- Reviewing null rates
- Running automated tests
- Running Python compilation checks
- Verifying statistical outputs
- Comparing model performance against a baseline
- Reviewing feature-importance outputs
- Verifying GitHub Actions CI
- Rejecting unsupported suggestions

## Trade-off

AI-assisted work still requires manual validation and ownership by the author.

---

# D25 — Exclude Confidential and Unnecessary Large Files from Public GitHub

## Context

The assignment material is confidential, and raw datasets may be unnecessarily large for version control.

## Options Considered

1. Commit everything
2. Exclude confidential and reproducible large files

## Decision

**Do not publicly commit:**

- Confidential assignment PDF
- Secrets
- Environment files
- Large raw datasets when they can be downloaded from the source
- Local database files where unnecessary

## Reason

This protects confidentiality and keeps the repository clean.

## Trade-off

Users may need to download source datasets separately before running the complete pipeline.

---

# D26 — Use GitHub Actions for Continuous Integration

## Context

Local automated tests provide confidence, but failures introduced through future code changes should also be detected automatically.

## Options Considered

1. Local testing only
2. GitHub Actions
3. A larger external CI platform

## Decision

**Use GitHub Actions for continuous integration.**

Workflow:

```text
.github/workflows/ci.yml
```

The workflow:

1. Checks out the repository
2. Sets up Python 3.13
3. Installs dependencies
4. Compiles Python modules
5. Runs automated tests

## Reason

GitHub Actions:

- Integrates directly with the repository
- Adds little infrastructure overhead
- Automatically validates code changes
- Improves confidence before merging

## Result

The workflow has completed successfully on the `dev` branch.

## Trade-off

The CI workflow intentionally avoids running the full large-data pipeline because raw data and large generated artifacts are not part of the repository.

---

# D27 — Use `price_best_available` as the ML Target

## Context

The enriched listing master contains several price-related fields.

A supervised regression target must be clearly defined and reproducible.

## Options Considered

1. Summary `price`
2. Detailed `detailed_price`
3. Derived `price_best_available`

## Decision

**Use `price_best_available` as the target variable.**

## Reason

The project's enrichment logic already defines a documented best-available price:

1. Use summary price when available
2. Otherwise use detailed price when available
3. Otherwise preserve null

This maximizes valid target coverage without fabricating prices.

## Result

| Metric | Count |
|---|---:|
| Canonical listings | **10,465** |
| Valid positive target prices | **6,471** |
| Missing or invalid target prices excluded | **3,994** |

## Trade-off

The target is an available listing price, not a confirmed booked transaction price, actual revenue, or profitability measure.

---

# D28 — Explicitly Prevent Target Leakage

## Context

Several fields are directly derived from price and would reveal part or all of the target.

Using them as predictors would produce misleadingly strong model performance.

## Decision

**Explicitly exclude price-derived columns from the feature set.**

Excluded fields include:

```text
price_raw
price
detailed_price
detailed_price_raw
price_best_available
price_source
price_per_bedroom
price_per_guest
```

## Reason

This prevents the model from learning the answer directly from target-derived variables.

## Trade-off

Some highly predictive price-related information is intentionally excluded to protect validity.

---

# D29 — Compare Dummy, Ridge, and Random Forest Models

## Context

A focused experiment should include:

- A baseline
- A simple interpretable benchmark
- A nonlinear model

## Options Considered

1. One model only
2. Many models with extensive tuning
3. Three carefully selected models

## Decision

**Compare:**

1. Dummy Regressor
2. Ridge Regression
3. Random Forest Regressor

## Reason

This creates a clear progression:

```text
Simple Baseline
      ↓
Linear Benchmark
      ↓
Nonlinear Ensemble
```

## Result

| Model | MAE | RMSE | R² |
|---|---:|---:|---:|
| **Random Forest Regressor** | **€78.61** | **€133.76** | **0.5884** |
| Ridge Regression | €85.63 | €152.33 | 0.4662 |
| Dummy Regressor | €134.91 | €213.50 | -0.0486 |

## Trade-off

The experiment does not attempt a broad leaderboard of many algorithms.

---

# D30 — Use a `log1p` Transformation for the ML Target

## Context

The available listing-price distribution is strongly right-skewed and includes extreme premium listings.

Observed target summary:

- Median: approximately **€287**
- Mean: approximately **€344**
- Maximum: **€11,412**

## Options Considered

1. Model raw prices directly
2. Delete all upper outliers
3. Apply a log transformation to the target

## Decision

**Use `log1p` for target transformation and `expm1` to return predictions to euro scale.**

## Reason

This reduces the influence of extreme price skew while preserving valid listings.

## Trade-off

Model errors are optimized in transformed target space, but final metrics are reported after predictions are converted back to euros.

---

# D31 — Evaluate Models on a Held-Out Test Set

## Context

Training performance alone is not sufficient evidence of predictive value.

## Decision

**Use an 80/20 train-test split with `random_state=42`.**

Final split:

| Partition | Rows |
|---|---:|
| Training | **5,176** |
| Test | **1,295** |

## Metrics

- MAE
- RMSE
- R²

## Reason

This provides reproducible out-of-sample evaluation.

## Trade-off

A single holdout split does not provide the same robustness as repeated cross-validation.

Cross-validation is left as a possible future improvement.

---

# D32 — Add Model Interpretation and Diagnostic Outputs

## Context

Reporting only model scores would not explain:

- Which features matter
- Whether the model follows actual-price patterns
- Where prediction errors remain

## Decision

**Add:**

1. Random Forest feature importance
2. Actual-vs-predicted diagnostic visualization

## Top Encoded Features

| Rank | Feature | Importance |
|---|---|---:|
| 1 | Bedrooms | 0.2714 |
| 2 | Room type: Entire home/apt | 0.1597 |
| 3 | Longitude | 0.0837 |
| 4 | Minimum nights | 0.0636 |
| 5 | Latitude | 0.0623 |
| 6 | Accommodates | 0.0553 |
| 7 | Reviews per month | 0.0351 |
| 8 | Bathrooms | 0.0331 |
| 9 | Availability 365 | 0.0275 |
| 10 | Unavailability-rate proxy | 0.0268 |

## Diagnostic Visualization Decision

For readability, the actual-vs-predicted chart displays observations up to the **99th percentile of actual test prices (€1,141)**.

Rows displayed:

```text
1,283 / 1,295
```

All 1,295 test rows remain included in:

- MAE
- RMSE
- R²
- Saved predictions

## Trade-off

Impurity-based feature importance does not establish causation and may distribute importance across encoded categorical levels.

---

# D33 — Use Streamlit for the Planned Interactive Dashboard

## Status

**Planned next — not yet implemented.**

## Context

The assignment includes an optional interactive dashboard for market analysis.

Possible technologies include:

- Streamlit
- Dash
- Observable
- Power BI

## Decision

**Use Streamlit for the planned interactive dashboard.**

## Reason

Streamlit is the strongest fit for the current project because it:

- Uses Python
- Integrates directly with Pandas
- Reads Parquet easily
- Can query DuckDB
- Supports interactive filters
- Requires relatively low setup overhead
- Fits the current project stack
- Is suitable for a focused internship submission

## Trade-off

Streamlit offers less front-end control than a fully custom web application.

## Important Note

This decision records the intended implementation approach.

The dashboard should not be listed as completed until it is actually implemented, tested, and verified.

---

# D34 — Feed the Dashboard from Processed Outputs, Not Raw Large Files

## Status

**Planned decision for dashboard implementation.**

## Context

The project already produces clean, compact, validated outputs.

Reading raw large files directly inside a dashboard would:

- Increase startup time
- Duplicate transformation logic
- Increase memory pressure
- Risk inconsistent calculations

## Decision

**Use processed Parquet and DuckDB outputs as dashboard data sources.**

Preferred sources include:

```text
data/processed/enriched_listing_master.parquet
data/warehouse/airbnb_analytics.duckdb
outputs/modeling/price_model_results.csv
outputs/modeling/random_forest_feature_importance.csv
```

## Reason

This keeps the dashboard aligned with the validated engineering pipeline.

## Trade-off

The dashboard depends on processed outputs being generated first.

---

# D35 — Maintain a Visual Architecture Diagram

## Context

The project contains multiple stages, tools, datasets, and outputs.

A reviewer should be able to understand the overall architecture quickly.

## Decision

**Maintain a visual architecture diagram in repository documentation.**

Recommended path:

```text
docs/images/amsterdam_airbnb_data_pipeline_architecture.png
```

## Reason

The diagram communicates:

1. Public source data
2. Raw layer
3. Input verification
4. Profiling
5. Data-quality validation
6. Critical validation gate
7. Cleaning
8. Enrichment
9. Processed Parquet layer
10. DuckDB warehouse
11. SQL, EDA, statistics, and machine learning
12. Business findings and final reporting

## Trade-off

The diagram must be kept synchronized with major architectural changes.

---

# Final Reflection on Engineering Decisions

The central engineering strategy of this project was to prefer:

- Explicit decisions over hidden assumptions
- Data preservation over silent deletion
- Context-aware null handling over blanket imputation
- Aggregation before one-to-many joins
- Reproducibility over notebook-only experimentation
- Memory-aware processing over unnecessary infrastructure
- Clear warnings over artificially perfect data-quality reports
- Statistical depth over excessive test quantity
- A focused ML experiment over an oversized model leaderboard
- Baseline comparison over unsupported performance claims
- Leakage prevention over inflated metrics
- Automated testing over manual-only verification
- Continuous integration over local-only confidence
- Business interpretation over disconnected charts
- Transparent limitations over unsupported claims

The resulting project successfully:

- Profiles all seven Amsterdam datasets
- Validates source quality
- Preserves **10,465 canonical listings**
- Aggregates **545,162 detailed review events**
- Processes **3,819,725 calendar rows**
- Produces cleaned and enriched Parquet datasets
- Builds a validated DuckDB analytical warehouse
- Stops on critical validation failures
- Completes with **83 PASS, 7 WARNING, and 0 FAIL**
- Passes **17 warehouse validation checks**
- Passes **13 automated tests**
- Uses GitHub Actions for continuous integration
- Completes two statistical hypothesis tests
- Compares three regression models
- Achieves best ML performance of **MAE €78.61, RMSE €133.76, R² 0.5884**
- Generates feature-importance outputs
- Generates actual-vs-predicted diagnostics
- Documents the full architecture
- Plans the next optional extension as a Streamlit dashboard

These decisions reflect the project's primary objective:

> **Build a defensible, reproducible, memory-aware, validated, testable, analytically useful, and professionally documented data engineering workflow rather than maximizing feature count.**

---

# Current Decision Status

```text
✅ D01–D32 implemented and documented
✅ D35 architecture decision implemented
⬜ D33 Streamlit dashboard implementation planned next
⬜ D34 Dashboard processed-output integration planned next
```

The next major optional implementation step is the **interactive Streamlit market-analysis dashboard**.
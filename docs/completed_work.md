# Completed Work Summary

> **Project:** Amsterdam Airbnb Data Engineering & Analytics Challenge  
> **City:** Amsterdam, Netherlands  
> **Strategy:** One-city, depth-first, 8 GB RAM-aware implementation  
> **Primary Development Branch:** `dev`

---

## Project Overview

This document summarizes the work completed for the Amsterdam Airbnb Data Engineering & Analytics Challenge.

The project follows a one-city, depth-first strategy focused on:

- Dataset understanding
- Automated profiling
- Data-quality validation
- Cleaning and standardization
- Listing-level data enrichment
- Memory-aware large-file processing
- DuckDB analytical warehouse construction
- SQL analysis
- Exploratory data analysis
- Statistical hypothesis testing
- Focused machine-learning experimentation
- Automated testing
- Continuous integration
- Reproducibility
- Professional documentation

The selected city is:

**Amsterdam, Netherlands**

The complete engineering workflow can be executed using:

```bash
python run_pipeline.py --city amsterdam
```

The focused price-prediction experiment can be executed using:

```bash
python experiments/price_prediction.py
```

---

## 1. Project Setup and Repository Structure

A modular project structure was created to separate:

- Raw data
- Processed data
- Warehouse data
- Source code
- Machine-learning experiments
- SQL queries
- Notebooks
- Data-quality outputs
- EDA outputs
- Statistical outputs
- Modeling outputs
- Documentation
- Tests
- Continuous-integration workflows

Key project components include:

```text
airbnb-data-engineering-challenge/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── README.md
├── requirements.txt
├── .gitignore
├── run_pipeline.py
│
├── config/
│   └── city_config.yaml
│
├── data/
│   ├── raw/
│   │   └── amsterdam/
│   ├── processed/
│   └── warehouse/
│
├── src/
│   ├── __init__.py
│   ├── ingest.py
│   ├── profile.py
│   ├── validate.py
│   ├── clean.py
│   ├── enrich.py
│   ├── build_warehouse.py
│   ├── database.py
│   └── utils.py
│
├── experiments/
│   └── price_prediction.py
│
├── sql/
│   └── analytical_queries.sql
│
├── notebooks/
│   ├── 01_dataset_familiarization.ipynb
│   └── 02_eda_and_statistics.ipynb
│
├── outputs/
│   ├── data_quality/
│   ├── eda/
│   ├── statistics/
│   └── modeling/
│
├── docs/
│   ├── images/
│   ├── assumptions.md
│   ├── decision_log.md
│   ├── completed_work.md
│   ├── incomplete_work.md
│   └── ai_usage_disclosure.md
│
└── tests/
    └── test_data_quality.py
```

---

## 2. Dataset Collection

Seven Amsterdam Airbnb source datasets were included in the project:

1. `listings.csv`
2. `listings.csv.gz`
3. `calendar.csv.gz`
4. `reviews.csv`
5. `reviews.csv.gz`
6. `neighbourhoods.csv`
7. `neighbourhoods.geojson`

The raw files are preserved unchanged.

Raw source datasets are intentionally excluded from the public Git repository because of their size and data-handling considerations.

---

## 3. Dataset Familiarization

Dataset familiarization was completed for all seven source datasets.

The analysis included:

- File inventory
- Row counts
- Column counts
- Column names
- Data types
- Missing-value analysis
- Missing percentages
- Unique-value counts
- Sample values
- Minimum and maximum values where appropriate
- Duplicate-row analysis
- Candidate primary-key investigation
- Foreign-key relationship investigation
- Dataset-grain identification
- Business-domain interpretation
- Source limitations and caveats

Verified source sizes include:

| Dataset | Rows / Features | Columns / Properties |
|---|---:|---:|
| `neighbourhoods.csv` | 22 rows | 2 columns |
| `listings.csv` | 10,465 rows | 19 columns |
| `reviews.csv` | 545,162 rows | 2 columns |
| `listings.csv.gz` | 10,369 rows | 90 columns |
| `neighbourhoods.geojson` | 22 features | Geographic properties + geometry |
| `calendar.csv.gz` | 3,819,725 rows | 5 columns |
| `reviews.csv.gz` | 545,162 rows | 6 columns |

---

## 4. Dataset Relationship Analysis

The main entity relationships were identified as:

```text
Host
  │
  │ host_id
  ▼
Listing
  │
  ├──────────────► Calendar
  │                 listing_id
  │
  ├──────────────► Reviews
  │                 listing_id
  │
  └──────────────► Neighbourhood
                    neighbourhood
```

Key candidate identifiers examined included:

- `listings.id`
- `listings.host_id`
- `calendar.listing_id`
- `reviews.listing_id`
- Detailed review identifiers

Potential keys were validated rather than assumed.

---

## 5. Automated Dataset Profiling

A reusable profiling module was implemented in:

```text
src/profile.py
```

The profiler successfully processed all seven datasets.

Processing strategy:

- **Pandas** for small and medium datasets
- **DuckDB** for large detailed datasets

Large datasets processed without loading everything simultaneously into Pandas include:

```text
calendar.csv.gz: 3,819,725 rows
reviews.csv.gz:    545,162 rows
```

Generated profiling outputs:

```text
outputs/data_quality/dataset_summary.csv
outputs/data_quality/column_profile.csv
```

Final profiling result:

```text
7 / 7 datasets profiled successfully
```

---

## 6. Automated Data-Quality Validation

A reusable validation module was implemented in:

```text
src/validate.py
```

The validation framework checks areas including:

- Required columns
- Missing identifiers
- Unique-key expectations
- Duplicate IDs
- Missing prices
- Negative prices
- Coordinate validity
- Availability ranges
- Room-type categories
- Date parsing
- Foreign-key coverage
- Source-coverage differences
- Missing metadata
- Review-row repetition

Final validation result:

| Status | Count |
|---|---:|
| PASS | **83** |
| WARNING | **7** |
| FAIL | **0** |

All seven warnings were reviewed individually and classified as known source limitations or non-critical structural conditions.

No critical validation failures were present.

---

## 7. Critical Validation Gate

A critical validation gate was added to the end-to-end pipeline.

Behavior:

```text
Validation results
      │
      ├── One or more FAIL results
      │            ↓
      │           STOP
      │
      └── No FAIL results
                   ↓
                Continue
```

Warnings do not automatically block downstream processing when:

- The limitation is understood.
- The affected data remains valid for appropriate uses.
- The condition is documented.

The latest successful validation result was:

| Status | Count |
|---|---:|
| PASS | **83** |
| WARNING | **7** |
| FAIL | **0** |

Therefore, the pipeline correctly continued to downstream processing.

---

## 8. Data Cleaning and Standardization

A reusable cleaning module was implemented in:

```text
src/clean.py
```

Major cleaning work included:

- Currency-formatted price parsing
- Raw-price preservation
- Missing-price preservation
- Date parsing
- Boolean standardization
- Listing-key integrity validation
- Preservation of raw source files

Generated outputs:

```text
data/processed/cleaned_listings.parquet
data/processed/cleaned_detailed_listings.parquet
outputs/data_quality/cleaning_summary.csv
```

Verified cleaned outputs:

| Output | Rows | Listing ID Integrity |
|---|---:|---|
| `cleaned_listings.parquet` | **10,465** | Unique and non-null |
| `cleaned_detailed_listings.parquet` | **10,369** | Unique and non-null |

Missing prices were preserved as null.

No zero-price imputation was performed.

---

## 9. Canonical Listing Population

The project established:

```text
10,465 canonical listings
```

from the summary listings source.

The detailed listings source contained:

```text
10,369 listings
```

Therefore:

```text
96 canonical summary listings
```

were not represented in the detailed listings source.

These 96 records were preserved rather than discarded.

---

## 10. Review Data Investigation

The detailed review dataset contains:

```text
545,162 review events
```

Review-level investigations included:

- Full duplicate-row checking
- Review-identifier validation
- Repeated `(listing_id, date)` analysis
- Missing reviewer metadata

The summary reviews dataset contains repeated:

```text
(listing_id, date)
```

combinations.

Observed repeated-row count beyond first occurrences:

```text
22,541 rows
```

These were not blindly deleted because multiple legitimate review events may occur for the same listing on the same date.

---

## 11. Listing-Level Data Enrichment

A reusable enrichment module was implemented in:

```text
src/enrich.py
```

The final enriched master dataset was designed at the grain:

> **One row per canonical listing**

The enrichment process:

1. Starts with the **10,465 canonical listings**.
2. Adds matching detailed-listing attributes.
3. Aggregates detailed review data to listing level.
4. Aggregates calendar data to listing level.
5. Joins compact listing-level aggregates.
6. Creates derived analytical features.
7. Validates the final one-row-per-listing grain.

Generated outputs:

```text
data/processed/review_listing_aggregates.parquet
data/processed/calendar_listing_aggregates.parquet
data/processed/enriched_listing_master.parquet
outputs/data_quality/enrichment_summary.csv
```

Final verified enrichment result:

| Metric | Result |
|---|---:|
| Canonical listings preserved | **10,465** |
| Detailed-source matches | **10,369** |
| Summary-only listings preserved | **96** |
| Unique non-null listing IDs | **Yes** |

---

## 12. Derived Features

Useful analytical features were created during enrichment.

Examples include:

- Best-available price
- Price source
- Price per bedroom
- Price per guest
- Review-event counts
- Review-frequency measures
- Host portfolio segmentation
- Availability rate
- Unavailability-rate proxy
- Review-history indicators

No derived feature was used to make claims beyond what the underlying source data can support.

---

## 13. Host Portfolio Segmentation

Hosts were segmented into analytical categories:

- **Single-listing host**
- **Small multi-listing host:** 2–5 listings
- **Large/professional host:** 6+ listings

This segmentation supports analysis of host concentration and market-supply structure.

The term `large/professional host` is treated as an analytical label based on listing count, not proof of legal or commercial business status.

---

## 14. Calendar Data Processing

The calendar dataset contains:

```text
3,819,725 rows
```

To remain compatible with the 8 GB RAM development environment:

- The raw calendar dataset was not retained as a full Pandas DataFrame.
- DuckDB was used for aggregation.
- Data was reduced to compact listing-level metrics before enrichment.

Calendar unavailability is stored only as:

```text
unavailability_rate_proxy
```

It is not described as:

- True occupancy
- Confirmed booking rate
- Verified reservation activity

---

## 15. 8 GB RAM-Aware Processing

The project was intentionally designed to run on an 8 GB RAM Windows laptop.

The engineering strategy includes:

- Pandas for smaller datasets
- DuckDB for larger datasets
- One major stage at a time
- Listing-level aggregation before joins
- Parquet intermediate outputs
- Avoiding simultaneous loading of all seven raw datasets
- Memory cleanup between pipeline stages where appropriate
- Conservative memory-aware processing

The full pipeline successfully processed all available Amsterdam data without downsampling the core datasets.

---

## 16. DuckDB Analytical Warehouse

A DuckDB analytical warehouse was implemented through:

```text
src/build_warehouse.py
```

Warehouse location:

```text
data/warehouse/airbnb_analytics.duckdb
```

The warehouse contains analytical structures including:

- `enriched_listing_master`
- `dim_listings`
- `dim_neighbourhoods`
- `fact_review_activity`
- `fact_calendar_activity`

Analytical views include:

- `vw_neighbourhood_performance`
- `vw_room_type_performance`
- `vw_host_portfolio_performance`

The warehouse successfully reconciled:

| Metric | Result |
|---|---:|
| Canonical listings | **10,465** |
| Review events | **545,162** |
| Calendar rows | **3,819,725** |

Warehouse validation result:

| Warehouse Check | Count |
|---|---:|
| PASS | **17** |
| FAIL | **0** |

Generated warehouse validation output:

```text
outputs/data_quality/warehouse_summary.csv
```

---

## 17. Analytical SQL Queries

A dedicated analytical SQL file was created:

```text
sql/analytical_queries.sql
```

The SQL analysis addresses business questions including:

1. Pricing and performance by room type
2. Neighbourhood pricing and market activity
3. Host portfolio concentration
4. Superhost versus non-superhost performance
5. Neighbourhood review activity
6. Frequently reviewed but lower-rated listings
7. Availability-based proxy patterns
8. Pricing by accommodation capacity

The query set is designed for business-oriented analytical consumption through the DuckDB warehouse.

---

## 18. Exploratory Data Analysis

Focused exploratory data analysis was completed.

Ten visualizations were generated:

1. `01_listings_by_neighbourhood.png`
2. `02_median_price_by_neighbourhood.png`
3. `03_median_price_by_room_type.png`
4. `04_median_price_by_host_segment.png`
5. `05_review_activity_by_neighbourhood.png`
6. `06_unavailability_proxy_by_neighbourhood.png`
7. `07_median_price_by_capacity.png`
8. `08_price_distribution_full.png`
9. `09_price_distribution_without_iqr_upper_outliers.png`
10. `10_correlation_matrix.png`

The analyses cover:

- Listing distribution
- Neighbourhood pricing
- Room-type pricing
- Host concentration
- Review activity
- Availability patterns
- Accommodation capacity
- Price distribution
- Outliers
- Feature correlations

Important EDA findings include:

- Supply is concentrated in a relatively small group of neighbourhoods.
- Entire-home listings command substantially higher prices than private rooms.
- Prices are strongly right-skewed and include extreme premium listings.
- Property size and accommodation capacity are materially related to price.
- Calendar unavailability is treated only as a proxy, not verified occupancy.
- Review activity is not treated as verified booking demand.

---

## 19. Statistical Hypothesis Testing

Two focused statistical hypotheses were completed.

### Hypothesis 1 — Entire Homes vs Private Rooms

**Question:**

Do entire-home listings command higher prices than private-room listings?

Key results:

| Metric | Entire Home/Apt | Private Room |
|---|---:|---:|
| Sample size | **4,771** | **1,653** |
| Median price | **€331** | **€171** |

Additional result details:

- Mann-Whitney U statistic: **6,692,891.0**
- **p < 0.001**
- Rank-biserial effect size: **0.697**

**Conclusion:** Entire homes have a statistically significant and practically large price premium over private rooms.

### Hypothesis 2 — Superhosts vs Non-Superhosts

**Question:**

Do superhost listings achieve different review scores than non-superhost listings?

Key results:

| Metric | Superhost | Non-Superhost |
|---|---:|---:|
| Sample size | **1,661** | **7,566** |
| Median review score | **4.90** | **4.94** |

Additional result details:

- Mann-Whitney U statistic: **5,293,896.5**
- **p = 3.19 × 10⁻²⁵**
- Rank-biserial effect size: **-0.158**

**Conclusion:** The difference is statistically significant but small in practical terms.

The project does not rely only on statistical significance.

Effect size and practical importance are also considered.

---

## 20. End-to-End Pipeline

The pipeline entry point was implemented in:

```text
run_pipeline.py
```

Execution command:

```bash
python run_pipeline.py --city amsterdam
```

The complete workflow contains seven stages:

1. Verify Raw Source Files
2. Automated Dataset Profiling
3. Data-Quality Validation
4. Critical Validation Gate
5. Cleaning and Standardization
6. Data Enrichment
7. DuckDB Analytical Warehouse

The latest verified full run completed successfully.

Because runtime can vary with system conditions and disk caching, the most defensible summary is:

> **Approximately 1–2 minutes on the local 8 GB RAM Windows environment.**

All seven stages completed successfully.

---

## 21. Automated Tests

A focused automated test suite was implemented in:

```text
tests/test_data_quality.py
```

The suite contains:

```text
13 automated tests
```

Test coverage includes:

- Currency-price parsing
- Raw-price preservation
- Missing-price preservation
- Valid-date parsing
- Invalid-date handling
- Boolean normalization
- Unknown Boolean handling
- Unique listing IDs
- Duplicate listing-ID rejection
- Null listing-ID rejection
- Duplicate enrichment-key rejection
- Derived-feature calculations
- Final canonical listing-grain preservation

Latest local verification:

```text
Python compilation: PASS
Automated tests collected: 13
Passed: 13
Failed: 0
Test runtime: 1.32 seconds
```

Verification commands:

```bash
python -m compileall -q run_pipeline.py src tests experiments
```

```bash
python -m pytest tests/ -v
```

Both completed successfully.

---

## 22. GitHub Actions Continuous Integration

A GitHub Actions workflow was implemented in:

```text
.github/workflows/ci.yml
```

The CI workflow automatically:

1. Checks out the repository.
2. Sets up Python 3.13.
3. Installs project dependencies.
4. Compiles Python modules.
5. Runs automated tests.

The workflow is configured for the relevant development and integration branches and has completed successfully on the `dev` branch.

This adds automated verification beyond local execution and helps detect regressions before integration.

---

## 23. Focused Price-Prediction Experiment

After the engineering core, warehouse, EDA, statistical analysis, testing, CI, and documentation were stabilized, a focused machine-learning experiment was added.

Implementation:

```text
experiments/price_prediction.py
```

Research question:

> **Can listing characteristics predict the available Airbnb listing price for Amsterdam listings?**

### Modeling Dataset

The experiment uses:

```text
data/processed/enriched_listing_master.parquet
```

Dataset usage:

| Metric | Count |
|---|---:|
| Total canonical listings | **10,465** |
| Listings with valid positive target price | **6,471** |
| Listings excluded because target price was missing or invalid | **3,994** |
| Training observations | **5,176** |
| Test observations | **1,295** |

Missing target prices were not imputed or fabricated.

### Target Variable

```text
price_best_available
```

### Leakage Prevention

Price-derived fields were excluded from model features, including:

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

### Preprocessing

The workflow includes:

- Median imputation for missing numerical features
- Explicit missing-category handling for categorical features
- One-hot encoding with unknown-category protection
- Numerical feature standardization
- `log1p` target transformation
- Fixed `random_state=42`
- 80/20 train-test split

### Models Compared

Three models were evaluated:

1. **Dummy Regressor**
2. **Ridge Regression**
3. **Random Forest Regressor**

### Evaluation Metrics

- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- R² Score

### Final Results

| Model | MAE | RMSE | R² |
|---|---:|---:|---:|
| **Random Forest Regressor** | **€78.61** | **€133.76** | **0.5884** |
| Ridge Regression | €85.63 | €152.33 | 0.4662 |
| Dummy Regressor | €134.91 | €213.50 | -0.0486 |

The Random Forest Regressor achieved the strongest test-set performance.

Compared with the Dummy Regressor baseline, it reduced Mean Absolute Error from **€134.91 to €78.61**, an improvement of approximately **41.7%**.

The Random Forest achieved an R² of **0.5884**, meaning that approximately **58.8% of the variation in held-out listing prices was explained by the selected features within this experiment**.

The considerably higher RMSE relative to MAE indicates that extreme premium-priced listings still generate some larger prediction errors.

### Top Random Forest Encoded Features

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

Feature importance does not establish causation.

Because categorical features such as neighbourhood are one-hot encoded, their total influence may be distributed across multiple encoded categories rather than appearing as one single feature.

### Diagnostic Visualization

The actual-vs-predicted visualization displays:

```text
1,283 of 1,295 test observations
```

using the:

```text
99th percentile of actual test prices = €1,141
```

as a visualization limit.

This limit is applied only to the chart for readability.

All 1,295 test observations remain included in:

- MAE
- RMSE
- R²
- Model evaluation
- Saved prediction outputs

### Generated Modeling Outputs

```text
outputs/modeling/
├── price_model_results.csv
├── price_model_predictions.csv
├── price_model_comparison.png
├── random_forest_feature_importance.csv
├── random_forest_feature_importance.png
└── actual_vs_predicted_price.png
```

The experiment is treated as a focused analytical extension, not a production pricing system.

---

## 24. Validation Warning Review

All seven validation warnings were manually reviewed.

They covered:

1. 96 missing summary-listing host IDs.
2. 3,994 missing summary-listing prices.
3. 96 canonical summary listings absent from detailed listings.
4. 3,992 missing detailed-listing prices.
5. Fully empty `neighbourhood_group`.
6. 22,541 repeated `(listing_id, date)` summary-review rows.
7. One missing reviewer name.

No warning required blind deletion or fabricated imputation.

Each was handled according to source meaning and analytical context.

---

## 25. Assumptions and Caveats Documentation

A dedicated assumptions document was created:

```text
docs/assumptions.md
```

It documents topics including:

- City scope
- Canonical population
- Missing prices
- Missing host metadata
- Source-coverage differences
- Calendar-proxy limitations
- Review-count limitations
- Outlier treatment
- Statistical interpretation
- Machine-learning interpretation
- One-row-per-listing grain
- 8 GB RAM strategy
- Non-causal interpretation

---

## 26. Engineering Decision Log

A dedicated engineering decision log was created:

```text
docs/decision_log.md
```

It records major decisions including:

- One city instead of multiple cities
- Depth over breadth
- Pandas versus DuckDB responsibilities
- Parquet outputs
- Canonical-source choice
- Left-preserving enrichment
- Aggregate-before-join strategy
- Null-price preservation
- Validation-severity framework
- Validation-gate behavior
- Warehouse design
- Statistical scope
- Outlier strategy
- Automated testing
- Continuous integration
- Focused machine-learning experiment
- Target-leakage prevention
- AI disclosure
- Confidential-data handling

---

## 27. Architecture Diagram

A project architecture diagram was created to show the full engineering flow from raw source data to analytical outputs and reporting.

Recommended repository path:

```text
docs/images/amsterdam_airbnb_data_pipeline_architecture.png
```

The architecture communicates:

1. Public source data
2. Raw data layer
3. Raw input verification
4. Automated profiling
5. Data-quality validation
6. Critical validation gate
7. Cleaning and standardization
8. Listing-level enrichment
9. Processed Parquet layer
10. DuckDB analytical warehouse
11. SQL, EDA, statistics, and machine learning
12. Business findings and final reporting

---

## 28. Reproducibility

The project supports reproducibility through:

- Modular Python source code
- A single end-to-end pipeline entry point
- A separate reproducible machine-learning experiment
- `requirements.txt`
- Separate raw and processed layers
- Deterministic output paths
- Data-quality reports
- Automated tests
- GitHub Actions CI
- Documented assumptions
- Documented engineering decisions
- Git version control

Core execution command:

```bash
python run_pipeline.py --city amsterdam
```

Machine-learning experiment command:

```bash
python experiments/price_prediction.py
```

Test execution command:

```bash
python -m pytest tests/ -v
```

Compilation verification command:

```bash
python -m compileall -q run_pipeline.py src tests experiments
```

---

## 29. Current Interactive Dashboard Status

A live interactive market-analysis dashboard is **planned next** but is not yet counted as completed work.

The intended purpose is to provide exploratory access to:

- Market overview
- Neighbourhood comparison
- Room-type analysis
- Pricing distributions
- Review activity
- Availability proxy patterns
- Statistical findings
- Machine-learning results

This work should be documented as completed only after the dashboard has been implemented, tested, and verified.

---

# Final Completed Work Summary

The project currently delivers:

- One-city Amsterdam scope
- Seven source datasets processed
- Complete dataset familiarization
- Automated profiling
- Automated data-quality validation
- Critical validation gate
- Cleaning and standardization
- Canonical population preservation
- Listing-level enrichment
- Review aggregation
- Calendar aggregation
- Derived analytical features
- Parquet processed layer
- 8 GB RAM-aware processing
- DuckDB analytical warehouse
- Warehouse reconciliation
- Eight analytical SQL queries
- Ten EDA visualizations
- Two statistical hypotheses
- End-to-end pipeline execution
- Thirteen automated tests
- GitHub Actions continuous integration
- Focused price-prediction experiment
- Three regression models compared
- Random Forest feature-importance analysis
- Actual-vs-predicted diagnostic analysis
- Architecture diagram
- Assumptions documentation
- Engineering decision documentation
- AI usage disclosure

## Key Final Engineering Results

| Metric | Result |
|---|---:|
| Canonical listings preserved | **10,465** |
| Detailed listings matched | **10,369** |
| Summary-only listings preserved | **96** |
| Review events reconciled | **545,162** |
| Calendar rows reconciled | **3,819,725** |
| Source datasets profiled | **7 / 7** |
| Data-quality validation | **83 PASS / 7 WARNING / 0 FAIL** |
| Warehouse validation | **17 PASS / 0 FAIL** |
| Automated tests | **13 passed / 0 failed** |
| GitHub Actions CI | **Passing** |
| Analytical SQL queries | **8** |
| EDA visualizations | **10** |
| Statistical hypotheses | **2** |
| Price-prediction models compared | **3** |
| Best predictive model | **Random Forest Regressor** |
| Best model MAE | **€78.61** |
| Best model RMSE | **€133.76** |
| Best model R² | **0.5884** |

## Current Completion Status

```text
✅ Dataset Familiarization
✅ Automated Profiling
✅ Data-Quality Validation
✅ Critical Validation Gate
✅ Cleaning and Standardization
✅ Listing-Level Enrichment
✅ Review and Calendar Aggregation
✅ Processed Parquet Layer
✅ DuckDB Analytical Warehouse
✅ 8 Analytical SQL Queries
✅ 10 EDA Visualizations
✅ 2 Statistical Hypothesis Tests
✅ End-to-End Pipeline
✅ 13 Automated Tests
✅ GitHub Actions Continuous Integration
✅ Focused Price-Prediction Experiment
✅ Random Forest Feature Importance
✅ Actual-vs-Predicted Diagnostic Analysis
✅ Architecture Diagram
✅ Assumptions Documentation
✅ Engineering Decision Log
✅ AI Usage Disclosure

⬜ Interactive Dashboard
⬜ Final Report Update
⬜ Submission Details File
⬜ Final Repository QA
⬜ Merge dev → main
⬜ Submit
```

The completed work demonstrates a reproducible, memory-aware, validated, statistically reasoned, testable, and analytically useful data-engineering workflow for the Amsterdam Airbnb market.

The next planned analytical extension is an **interactive Streamlit dashboard for live market exploration**.
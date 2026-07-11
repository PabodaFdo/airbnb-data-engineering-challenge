<h1 align="center">Amsterdam Airbnb Data Engineering & Analytics Challenge</h1>

<p align="center">
  <a href="https://git.io/typing-svg">
    <img
      src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&pause=1200&color=006466&center=true&vCenter=true&width=950&lines=End-to-End+Data+Engineering+Pipeline;Automated+Profiling+%26+Data+Quality+Validation;DuckDB+Analytical+Warehouse+%26+Parquet+Layer;EDA+%2B+Statistical+Hypothesis+Testing;Focused+Machine+Learning+Price+Prediction;Built+for+an+8+GB+RAM+Windows+Environment"
      alt="Typing SVG"
    />
  </a>
</p>

<p align="center">
  <strong>
    A reproducible, memory-aware Data Engineering, Analytics, Statistics,
    and focused Machine Learning project using Amsterdam Inside Airbnb data.
  </strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Data%20Quality-83%20PASS%20%7C%207%20WARNING%20%7C%200%20FAIL-006466?style=for-the-badge" alt="Data Quality">
  <img src="https://img.shields.io/badge/Warehouse%20Validation-17%20PASS%20%7C%200%20FAIL-006466?style=for-the-badge" alt="Warehouse Validation">
  <img src="https://img.shields.io/badge/Tests-13%20Passed-006466?style=for-the-badge" alt="Tests">
</p>

<p align="center">
  <a href="https://github.com/PabodaFdo/airbnb-data-engineering-challenge/actions/workflows/ci.yml">
    <img src="https://github.com/PabodaFdo/airbnb-data-engineering-challenge/actions/workflows/ci.yml/badge.svg?branch=dev" alt="CI">
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/DuckDB-Analytics-FFF000?style=flat-square&logo=duckdb&logoColor=black" alt="DuckDB">
  <img src="https://img.shields.io/badge/Pandas-Data%20Processing-150458?style=flat-square&logo=pandas&logoColor=white" alt="Pandas">
  <img src="https://img.shields.io/badge/scikit--learn-ML-F7931E?style=flat-square&logo=scikitlearn&logoColor=white" alt="Scikit-learn">
  <img src="https://img.shields.io/badge/GitHub%20Actions-CI-2088FF?style=flat-square&logo=githubactions&logoColor=white" alt="GitHub Actions">
</p>

---

## Project Overview

This project transforms raw Airbnb source data into reliable, analysis-ready datasets through a complete, validated, and reproducible workflow.

```text
Raw Source Files
        ↓
Raw Input Verification
        ↓
Automated Dataset Profiling
        ↓
Data-Quality Validation
        ↓
Critical Validation Gate
        ↓
Cleaning & Standardization
        ↓
Listing-Level Enrichment
        ↓
Processed Parquet Outputs
        ↓
DuckDB Analytical Warehouse
        ↓
SQL Analysis + EDA + Statistical Testing
        ↓
Focused Price-Prediction Experiment
        ↓
Business Findings & Recommendations
```

The project follows a **one-city, depth-first strategy** and prioritizes data quality, reproducibility, memory-aware processing, analytical depth, statistical reasoning, focused predictive experimentation, automated testing, continuous integration, and clear business interpretation.

---

## Architecture

<p align="center">
  <img src="docs/images/amsterdam_airbnb_data_pipeline_architecture.png" alt="Amsterdam Airbnb Data Engineering Architecture" width="900">
</p>

<p align="center">
  <em>Figure 1. Amsterdam Airbnb Data Engineering Architecture</em>
</p>

The architecture follows a staged data-engineering workflow:

```text
Inside Airbnb Public Data
        ↓
Raw Data Layer
        ↓
Raw Input Verification
        ↓
Automated Profiling
        ↓
Data-Quality Validation
        ↓
Critical Validation Gate
        ↓
Cleaning & Standardization
        ↓
Listing-Level Enrichment
        ↓
Processed Parquet Layer
        ↓
DuckDB Analytical Warehouse
        ↓
SQL + EDA + Statistics + Machine Learning
        ↓
Business Findings & Final Report
```

---

## Key Engineering Results

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
| Full pipeline runtime | **Approximately 1–2 minutes on the local 8 GB RAM Windows environment** |

---

## Project Objectives

The main objectives are to:

- Understand and document all seven Amsterdam Airbnb source files.
- Validate candidate primary keys and cross-dataset relationships.
- Build a repeatable end-to-end data pipeline.
- Automate dataset profiling and data-quality reporting.
- Detect missing values, duplicates, source-coverage differences, and invalid domain values.
- Clean and standardize listing data using context-aware rules.
- Aggregate large review and calendar datasets safely.
- Build an enriched one-row-per-listing analytical dataset.
- Store processed outputs efficiently in Parquet.
- Build a lightweight DuckDB analytical warehouse.
- Write business-oriented analytical SQL queries.
- Perform focused exploratory data analysis.
- Complete two statistically rigorous hypothesis tests.
- Conduct a focused price-prediction experiment using the enriched listing-level dataset.
- Compare a Dummy Regressor baseline, Ridge Regression, and Random Forest Regressor.
- Evaluate predictive performance using MAE, RMSE, and R².
- Interpret Random Forest feature importance and actual-vs-predicted behavior.
- Translate technical results into business insights and recommendations.

---

## Selected Scope

### City

**Amsterdam, Netherlands**

The project intentionally focuses on one city to prioritize depth over breadth.

This choice allows greater attention to:

- Dataset familiarization
- Data-quality validation
- Reproducibility
- Pipeline reliability
- Analytical modeling
- Statistical rigor
- Business storytelling
- Professional documentation

> Findings should be interpreted within the Amsterdam market context and not automatically generalized to other cities.

---

## Dataset Overview

All data comes from the publicly available **Inside Airbnb** dataset.

| File | Rows / Features | Columns / Properties | Grain |
|---|---:|---:|---|
| `neighbourhoods.csv` | 22 rows | 2 columns | One row per neighbourhood |
| `listings.csv` | 10,465 rows | 19 columns | One row per canonical listing |
| `reviews.csv` | 545,162 rows | 2 columns | Review event by listing and date |
| `listings.csv.gz` | 10,369 rows | 90 columns | One row per detailed listing |
| `neighbourhoods.geojson` | 22 features | Geographic properties + geometry | One feature per neighbourhood |
| `calendar.csv.gz` | 3,819,725 rows | 5 columns | One row per listing per calendar date |
| `reviews.csv.gz` | 545,162 rows | 6 columns | One row per individual review |

> Raw datasets are intentionally excluded from the Git repository because of size and reproducibility considerations.

---

## Important Dataset Findings

### 1. Canonical Listing Population

`listings.csv` is treated as the canonical listing population.

- `listings.csv`: **10,465 listings**
- `listings.csv.gz`: **10,369 listings**
- Summary-only listings preserved: **96**

The enrichment process uses a left-preserving strategy so these 96 canonical listings are not silently lost.

### 2. One Row per Listing

The final enriched master dataset is designed at the grain:

> **One row per canonical listing**

The final dataset contains **10,465 rows with unique, non-null listing IDs**.

Review and calendar datasets are aggregated to listing level before joining to prevent row multiplication.

### 3. Missing Prices Are Preserved as Null

Observed missing prices:

- Summary listings: **3,994**
- Detailed listings: **3,992**

A missing price does **not** mean zero. Missing prices remain `null`, zero-value imputation is not used, and price-based analyses use only valid observations.

### 4. Repeated Review Dates Are Not Automatically Duplicates

The summary reviews dataset contains:

- **12,942 repeated `(listing_id, date)` groups**
- **22,541 extra rows beyond the first occurrence**

These rows are preserved because multiple legitimate reviews may occur for the same listing on the same date.

### 5. Calendar Unavailability Is Not True Occupancy

An unavailable date may represent a booking, host blocking, maintenance, personal use, regulation, or another unknown reason.

Therefore, the project uses:

```text
unavailability_rate_proxy
```

and does **not** describe it as verified occupancy.

### 6. Review Count Is Not Booking Count

Not every guest leaves a review. Review counts may be used as an imperfect proxy for guest activity, but not as verified booking volume.

---

## Cross-Dataset Relationships

```text
                         Host
                          │
                          │ host_id
                          ▼
                    ┌─────────────┐
                    │   Listing   │
                    └─────────────┘
                     │     │     │
          listing_id │     │     │ neighbourhood
                     │     │     ▼
                     │     │  ┌──────────────────┐
                     │     │  │  Neighbourhood   │
                     │     │  └──────────────────┘
                     │     │           │
                     │     │           ▼
                     │     │  ┌──────────────────┐
                     │     │  │ GeoJSON Boundary │
                     │     │  └──────────────────┘
                     │     │
                     │     └───────────────────────┐
                     ▼                             ▼
              ┌───────────┐                ┌────────────┐
              │  Reviews  │                │  Calendar  │
              └───────────┘                └────────────┘
               many rows                    many rows
               per listing                  per listing
```

Validated relationship examples:

- `listings.csv.id` → canonical listing identifier
- `listings.csv.gz.id` → detailed listing subset
- `calendar.csv.gz.listing_id` → `listings.csv.id`
- `reviews.csv.gz.listing_id` → `listings.csv.id`
- `reviews.csv.listing_id` → `listings.csv.id`

---

## End-to-End Pipeline

Run the complete workflow using:

```bash
python run_pipeline.py --city amsterdam
```

The pipeline executes seven stages:

```text
1. Verify Raw Source Files
2. Automated Dataset Profiling
3. Data-Quality Validation
4. Critical Validation Gate
5. Cleaning and Standardization
6. Data Enrichment
7. DuckDB Analytical Warehouse
```

The complete workflow has successfully run on the target **8 GB RAM Windows environment** in approximately **1–2 minutes**, depending on system conditions and disk caching.

---

## Automated Dataset Profiling

Reusable profiling logic is implemented in:

```text
src/profile.py
```

Generated outputs include:

```text
outputs/data_quality/dataset_summary.csv
outputs/data_quality/column_profile.csv
```

Profiling covers row counts, column counts, duplicates, data types, missing values, cardinality, ranges, and sample values.

### Result

**7 / 7 datasets profiled successfully**

---

## Data-Quality Validation

Reusable validation logic is implemented in:

```text
src/validate.py
```

Validation areas include:

- Required columns
- Missing identifiers
- Unique-key expectations
- Duplicate IDs
- Missing and negative prices
- Coordinate validity
- Availability ranges
- Room-type categories
- Date parsing
- Foreign-key coverage
- Source-coverage differences
- Missing metadata
- Repeated review rows

### Final Validation Result

| Status | Count |
|---|---:|
| PASS | **83** |
| WARNING | **7** |
| FAIL | **0** |

All seven warnings were manually reviewed and treated as documented source limitations or non-critical structural conditions.

---

## Critical Validation Gate

```text
Validation Results
      │
      ├── FAIL exists → STOP
      │
      └── No FAIL → Continue
```

Warnings do not automatically block downstream processing when the limitation is understood, valid data is preserved, and the condition is documented.

---

## Cleaning and Standardization

Reusable cleaning logic is implemented in:

```text
src/clean.py
```

Major transformations include:

- Currency-formatted price parsing
- Raw-price preservation
- Missing-price preservation
- Date parsing
- Boolean normalization
- Listing-key integrity validation
- Raw-data preservation

Generated outputs:

```text
data/processed/cleaned_listings.parquet
data/processed/cleaned_detailed_listings.parquet
outputs/data_quality/cleaning_summary.csv
```

| Output | Rows | Listing ID Integrity |
|---|---:|---|
| `cleaned_listings.parquet` | 10,465 | Unique and non-null |
| `cleaned_detailed_listings.parquet` | 10,369 | Unique and non-null |

---

## Listing-Level Data Enrichment

Reusable enrichment logic is implemented in:

```text
src/enrich.py
```

The enrichment process:

1. Starts with the **10,465 canonical listings**.
2. Adds matching detailed-listing attributes.
3. Aggregates detailed reviews to listing level.
4. Aggregates calendar data to listing level.
5. Joins compact listing-level aggregates.
6. Creates derived analytical features.
7. Validates one-row-per-listing grain.

Generated outputs:

```text
data/processed/review_listing_aggregates.parquet
data/processed/calendar_listing_aggregates.parquet
data/processed/enriched_listing_master.parquet
outputs/data_quality/enrichment_summary.csv
```

| Metric | Result |
|---|---:|
| Canonical listings preserved | **10,465** |
| Detailed-source matches | **10,369** |
| Summary-only listings preserved | **96** |
| Unique non-null listing IDs | **Yes** |

---

## 8 GB RAM-Aware Processing Strategy

The project was intentionally designed for an **8 GB RAM Windows laptop**.

> Never keep all seven raw datasets as full Pandas DataFrames in memory at the same time.

The strategy includes:

- Pandas for small and medium datasets
- DuckDB for large detailed files
- One major processing stage at a time
- Listing-level aggregation before joins
- Parquet intermediate outputs
- Compact analytical extracts for EDA
- Memory cleanup between major stages

| Dataset | Recommended Access |
|---|---|
| `neighbourhoods.csv` | Pandas |
| `listings.csv` | Pandas |
| `reviews.csv` | Pandas |
| `listings.csv.gz` | Pandas |
| `neighbourhoods.geojson` | JSON / optional geospatial processing |
| `calendar.csv.gz` | DuckDB |
| `reviews.csv.gz` | DuckDB |

---

## DuckDB Analytical Warehouse

The warehouse is built by:

```text
src/build_warehouse.py
```

Warehouse path:

```text
data/warehouse/airbnb_analytics.duckdb
```

### Main Analytical Structures

```text
enriched_listing_master
dim_listings
dim_neighbourhoods
fact_review_activity
fact_calendar_activity
```

### Analytical Views

```text
vw_neighbourhood_performance
vw_room_type_performance
vw_host_portfolio_performance
```

### Warehouse Reconciliation

| Metric | Result |
|---|---:|
| Canonical listings | **10,465** |
| Review events | **545,162** |
| Calendar rows | **3,819,725** |

### Warehouse Validation

| Status | Count |
|---|---:|
| PASS | **17** |
| FAIL | **0** |

---

## Analytical SQL Queries

Business-oriented SQL is stored in:

```text
sql/analytical_queries.sql
```

The query set covers:

1. Pricing and performance by room type
2. Neighbourhood pricing and market activity
3. Host portfolio concentration
4. Superhost versus non-superhost performance
5. Neighbourhood review activity
6. Highly reviewed but relatively low-rated listings
7. Availability-based proxy patterns
8. Pricing by accommodation capacity

---

## Exploratory Data Analysis

The project generated **10 EDA visualizations**:

```text
01_listings_by_neighbourhood.png
02_median_price_by_neighbourhood.png
03_median_price_by_room_type.png
04_median_price_by_host_segment.png
05_review_activity_by_neighbourhood.png
06_unavailability_proxy_by_neighbourhood.png
07_median_price_by_capacity.png
08_price_distribution_full.png
09_price_distribution_without_iqr_upper_outliers.png
10_correlation_matrix.png
```

The final report prioritizes the strongest figures using:

```text
Finding → Business Meaning → Recommended Action
```

### Important EDA Findings

- Supply is concentrated in a relatively small group of neighbourhoods.
- Entire-home listings command substantially higher prices than private rooms.
- Prices are strongly right-skewed and include extreme premium listings.
- Property size and accommodation capacity are materially related to price.
- Calendar unavailability is useful only as a proxy and is not treated as verified occupancy.
- Review activity is not treated as verified booking demand.

---

## Statistical Analysis

Two focused statistical hypotheses were completed.

### Hypothesis 1 — Entire Homes vs Private Rooms

**Question:** Do entire-home listings command higher prices than private-room listings?

Key results:

- Entire home/apt: **n = 4,771**, median price **€331**
- Private room: **n = 1,653**, median price **€171**
- Mann-Whitney U statistic: **6,692,891.0**
- **p < 0.001**
- Rank-biserial effect size: **0.697**

**Conclusion:** Entire homes have a statistically significant and practically large price premium over private rooms.

### Hypothesis 2 — Superhosts vs Non-Superhosts

**Question:** Do superhost listings achieve different review scores than non-superhost listings?

Key results:

- Superhost: **n = 1,661**, median review score **4.90**
- Non-superhost: **n = 7,566**, median review score **4.94**
- Mann-Whitney U statistic: **5,293,896.5**
- **p = 3.19 × 10⁻²⁵**
- Rank-biserial effect size: **-0.158**

**Conclusion:** The difference is statistically significant but small in practical terms.

> Statistical significance is not treated as automatic practical importance, and observational results are not presented as proof of causation.

---

## Focused Price-Prediction Experiment

After completing the core data engineering, EDA, statistical analysis, automated testing, and documentation work, a focused optional machine-learning experiment was added using the enriched listing-level dataset.

### Research Question

> **Can listing characteristics predict the available Airbnb listing price for Amsterdam listings?**

### Modeling Dataset

The experiment uses:

```text
data/processed/enriched_listing_master.parquet
```

The canonical enriched dataset contains **10,465 listings**.

| Metric | Count |
|---|---:|
| Total canonical listings | **10,465** |
| Listings with valid positive target price | **6,471** |
| Listings excluded because target price was missing or invalid | **3,994** |
| Training observations | **5,176** |
| Test observations | **1,295** |

Missing target prices were **not imputed or fabricated**.

### Target Variable

```text
price_best_available
```

The target uses the best available valid listing price according to the project's documented enrichment rules.

To prevent target leakage, price-derived fields were excluded from model features:

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

### Selected Predictors

The experiment uses a focused combination of:

- Neighbourhood
- Room type
- Detailed property type
- Host superhost status
- Host identity verification
- Host portfolio segment
- Latitude
- Longitude
- Accommodation capacity
- Bathrooms
- Bedrooms
- Beds
- Minimum and maximum nights
- Availability
- Review activity
- Review scores
- Host listing count
- Review-event frequency
- Unavailability-rate proxy

### Preprocessing

The modeling workflow includes:

- Median imputation for missing numerical features
- Explicit missing-category handling for categorical features
- One-hot encoding with unknown-category protection
- Numerical feature standardization
- `log1p` target transformation to reduce the influence of strong right skew
- Fixed `random_state=42` for reproducibility
- 80/20 train-test split

### Models Compared

Three models were evaluated:

1. **Dummy Regressor** — baseline
2. **Ridge Regression** — regularized linear benchmark
3. **Random Forest Regressor** — nonlinear ensemble model

### Evaluation Metrics

The models were evaluated using:

- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- R² Score

### Final Model Results

| Model | MAE | RMSE | R² |
|---|---:|---:|---:|
| **Random Forest Regressor** | **€78.61** | **€133.76** | **0.5884** |
| Ridge Regression | €85.63 | €152.33 | 0.4662 |
| Dummy Regressor | €134.91 | €213.50 | -0.0486 |

### Main Finding

The **Random Forest Regressor** achieved the strongest test-set performance.

Compared with the Dummy Regressor baseline, it reduced Mean Absolute Error from **€134.91 to €78.61**, an improvement of approximately **41.7%**.

The model achieved an R² of **0.5884**, meaning that approximately **58.8% of the variation in held-out listing prices was explained by the selected features within this experiment**.

The considerably higher RMSE relative to MAE indicates that extreme premium-priced listings still produce some substantially larger prediction errors.

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

The feature-importance results suggest that property size, accommodation type, geographic position, minimum-stay requirements, review activity, and availability characteristics contributed meaningful predictive information.

> **Feature importance does not establish causation.** It indicates how strongly features contributed to predictions within this fitted Random Forest model.

Because categorical features such as neighbourhood are one-hot encoded, their total influence may be distributed across multiple encoded categories rather than appearing as one single feature.

### Diagnostic Visualization

The actual-vs-predicted visualization displays **1,283 of 1,295 test observations**, using the **99th percentile of actual test prices (€1,141)** as a visualization limit.

This limit is applied **only to the chart for readability**.

All **1,295 test observations** remain included in:

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

### Reproduce the Experiment

Run:

```bash
python experiments/price_prediction.py
```

### Limitations

- Only listings with valid positive target prices were used.
- **3,994 canonical listings had missing or invalid target prices and were excluded rather than imputed.**
- The target represents an available listing price, not a confirmed booked transaction price.
- The model does not estimate verified revenue, profitability, or causal effects.
- Extreme premium listings remain difficult to predict.
- No extensive hyperparameter optimization or cross-city validation was performed.
- Feature importance should not be interpreted as causal evidence.

The experiment should therefore be treated as a focused analytical extension rather than a production pricing system.

---

## Automated Tests

Automated tests are implemented in:

```text
tests/test_data_quality.py
```

The suite covers cleaning, date parsing, Boolean normalization, key integrity, derived features, and final canonical-grain preservation.

Run tests with:

```bash
python -m pytest tests/ -v
```

| Test Result | Count |
|---|---:|
| Passed | **13** |
| Failed | **0** |

### Latest Local Verification

```text
Python compilation: PASS
Automated tests collected: 13
Passed: 13
Failed: 0
Test runtime: 1.32 seconds
```

The project was also verified using:

```bash
python -m compileall -q run_pipeline.py src tests experiments
```

and:

```bash
python -m pytest tests/ -v
```

Both completed successfully.

---

## Continuous Integration

GitHub Actions automatically verifies the Python project on pushes and pull requests.

Workflow:

```text
.github/workflows/ci.yml
```

The CI process performs:

```text
Checkout repository
        ↓
Set up Python 3.13
        ↓
Install dependencies
        ↓
Compile Python modules
        ↓
Run automated tests
        ↓
PASS / FAIL
```

The GitHub Actions workflow has completed successfully on the `dev` branch.

---

## Project Structure

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
├── docs/
│   ├── images/
│   │   └── amsterdam_airbnb_data_pipeline_architecture.png
│   ├── assumptions.md
│   ├── decision_log.md
│   ├── completed_work.md
│   ├── incomplete_work.md
│   └── ai_usage_disclosure.md
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
└── tests/
    └── test_data_quality.py
```

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/PabodaFdo/airbnb-data-engineering-challenge.git
cd airbnb-data-engineering-challenge
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Git Bash:

```bash
source .venv/Scripts/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Add the Amsterdam Source Files

Place the seven source files inside:

```text
data/raw/amsterdam/
```

Expected files:

```text
listings.csv.gz
listings.csv
calendar.csv.gz
reviews.csv.gz
reviews.csv
neighbourhoods.csv
neighbourhoods.geojson
```

### 5. Run the Complete Pipeline

```bash
python run_pipeline.py --city amsterdam
```

### 6. Run Automated Tests

```bash
python -m pytest tests/ -v
```

### 7. Run the Focused Price-Prediction Experiment

After the processed enriched dataset has been generated:

```bash
python experiments/price_prediction.py
```

This trains and compares the Dummy Regressor, Ridge Regression, and Random Forest Regressor and generates model evaluation, prediction, feature-importance, and diagnostic outputs.

---

## Documentation

Detailed documentation is available under:

```text
docs/
```

- `assumptions.md` — assumptions, limitations, and interpretation rules
- `decision_log.md` — major engineering decisions and trade-offs
- `completed_work.md` — evidence-based summary of completed work
- `incomplete_work.md` — optional work intentionally deferred
- `ai_usage_disclosure.md` — transparent AI assistance disclosure

---

## Assumptions and Limitations

Important limitations include:

- Airbnb source data may contain scraping inconsistencies.
- Missing price does not mean zero price.
- Calendar unavailability is not verified occupancy.
- Review count is not booking count.
- Detailed listings do not contain every canonical listing.
- Repeated review dates are not automatically duplicates.
- A single-city analysis cannot be generalized automatically to all markets.
- Statistical findings do not prove causation.
- Machine-learning feature importance does not prove causal influence.
- The price-prediction experiment does not estimate verified booking prices, revenue, or profitability.

See:

```text
docs/assumptions.md
```

for the full set of assumptions and analytical caveats.

---

## AI Usage Disclosure

Generative AI was used as a support tool for planning, code review, debugging, statistical methodology guidance, machine-learning experiment design, testing, and documentation.

AI-generated suggestions were not accepted automatically. Validation included:

- Running the full pipeline locally
- Checking row counts and unique keys
- Reviewing missing values and warnings
- Verifying processed Parquet outputs
- Reconciling DuckDB warehouse counts
- Reviewing statistical outputs
- Running the price-prediction experiment locally
- Comparing model metrics against a baseline
- Reviewing feature-importance outputs
- Running automated tests
- Running Python compilation checks
- Verifying GitHub Actions CI

Full disclosure:

```text
docs/ai_usage_disclosure.md
```

---

## Future Improvements

Potential future improvements include:

- Multi-city pipeline support
- Automated cross-city schema harmonization
- Incremental data processing
- More advanced data-quality frameworks
- Additional statistical hypotheses
- Cross-validation and formal hyperparameter optimization
- Additional carefully selected predictive models
- Grouped or permutation-based feature importance
- Streamlit analytical dashboard
- Workflow orchestration
- Docker containerization
- Cloud deployment
- Advanced geospatial analysis
- Model monitoring and drift detection for a production scenario

These improvements were intentionally deferred to protect the reliability, documentation quality, reproducibility, and interpretability of the completed engineering and analytical work.

---

## Project Status

### Completed

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
✅ Focused Price-Prediction Experiment
✅ 3 Regression Models Compared
✅ Random Forest Feature Importance
✅ Actual-vs-Predicted Diagnostic Analysis
✅ End-to-End Pipeline
✅ 13 Automated Tests
✅ GitHub Actions Continuous Integration
✅ Assumptions Documentation
✅ Engineering Decision Log
✅ Completed Work Summary
✅ Incomplete Work Summary
✅ AI Usage Disclosure
✅ Architecture Diagram
```

### Remaining Submission Work

```text
⬜ Update final report with the completed price-prediction experiment
⬜ Add final candidate submission details
⬜ Final repository QA
⬜ Merge dev → main
⬜ Submit
```

---

## Author

**Paboda Sathsarani Fernando**  
GitHub: **PabodaFdo**

BSc (Hons) Information Technology Undergraduate  
Specialization in Data Science  
Sri Lanka Institute of Information Technology (SLIIT)

---

## Data Attribution

The Airbnb datasets used in this project are sourced from **Inside Airbnb**, an independent public-data initiative.

Raw dataset files are not included in this repository.

---

## Final Note

This project demonstrates a reproducible, memory-aware, validated, statistically reasoned, and analytically useful data engineering workflow for the Amsterdam Airbnb market.

> **The goal was not to maximize feature count, but to build a defensible submission with clear assumptions, reliable data processing, strong validation, transparent engineering decisions, reproducible outputs, focused analysis, honest limitations, and careful interpretation of both statistical and machine-learning results.**

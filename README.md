# Amsterdam Airbnb Data Engineering & Analytics Challenge

> **End-to-end Data Engineering and Analytics project using Inside Airbnb data for Amsterdam, Netherlands.**  
> Built with **Python, Pandas, DuckDB, Parquet, SciPy, Matplotlib, Seaborn, Pytest, and Jupyter**.

---

## Project Overview

This project transforms raw Airbnb data into reliable, analysis-ready datasets through a complete and reproducible workflow:

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
Business Findings & Recommendations
```

The project follows a **one-city, depth-first strategy** and prioritizes data quality, reproducibility, memory-aware processing, analytical depth, statistical reasoning, and clear business interpretation.

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
| EDA visualizations | **10** |
| Statistical hypotheses | **2** |
| Latest full pipeline runtime | **45.49 seconds** |

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
- Complete two statistical hypothesis tests.
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

### Latest successful pipeline run

| Stage | Time |
|---|---:|
| Verify Raw Source Files | 0.01 s |
| Automated Dataset Profiling | 18.75 s |
| Data-Quality Validation | 21.98 s |
| Critical Validation Gate | 0.13 s |
| Cleaning and Standardization | 1.56 s |
| Data Enrichment | 2.65 s |
| DuckDB Analytical Warehouse | 0.41 s |
| **Total** | **45.49 s** |

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

### Final validation result

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
| `neighbourhoods.geojson` | JSON / optional GeoPandas |
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

### Main analytical structures

```text
enriched_listing_master
dim_listings
dim_neighbourhoods
fact_review_activity
fact_calendar_activity
```

### Analytical views

```text
vw_neighbourhood_performance
vw_room_type_performance
vw_host_portfolio_performance
```

### Warehouse reconciliation

| Metric | Result |
|---|---:|
| Canonical listings | **10,465** |
| Review events | **545,162** |
| Calendar rows | **3,819,725** |

### Warehouse validation

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

---

## Statistical Analysis

Two focused statistical hypotheses were completed.

### Hypothesis 1

**Do entire-home listings have significantly different or higher prices than private-room listings?**

### Hypothesis 2

**Do superhost listings achieve different or higher review scores than non-superhost listings?**

The statistical workflow includes:

- Null and alternative hypotheses
- Sample-size review
- Distribution assessment
- Assumption considerations
- Test selection
- Test statistic
- P-value
- Effect size
- Practical significance
- Business interpretation
- Limitations

> Statistical significance is not treated as automatic practical importance, and observational results are not presented as proof of causation.

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

---

## Project Structure

```text
airbnb-data-engineering-challenge/
│
├── README.md
├── requirements.txt
├── .gitignore
├── run_pipeline.py
│
├── data/
│   ├── raw/
│   │   └── amsterdam/
│   ├── processed/
│   └── warehouse/
│
├── src/
│   ├── __init__.py
│   ├── profile.py
│   ├── validate.py
│   ├── clean.py
│   ├── enrich.py
│   └── build_warehouse.py
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
│   └── statistics/
│
├── docs/
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

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/PabodaFdo/airbnb-data-engineering-challenge.git
cd airbnb-data-engineering-challenge
```

### 2. Create a virtual environment

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

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add the Amsterdam source files

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

### 5. Run the complete pipeline

```bash
python run_pipeline.py --city amsterdam
```

### 6. Run automated tests

```bash
python -m pytest tests/ -v
```

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

See:

```text
docs/assumptions.md
```

for the full set of assumptions and analytical caveats.

---

## AI Usage Disclosure

Generative AI was used as a support tool for planning, code review, debugging, statistical methodology guidance, testing, and documentation.

AI-generated suggestions were not accepted automatically. Validation included:

- Running the full pipeline locally
- Checking row counts and unique keys
- Reviewing missing values and warnings
- Verifying processed Parquet outputs
- Reconciling DuckDB warehouse counts
- Reviewing statistical outputs
- Running automated tests

Full disclosure:

```text
docs/ai_usage_disclosure.md
```

---

## Future Improvements

Potential future improvements include:

- Multi-city pipeline support
- Automated schema harmonization
- Incremental processing
- Advanced data-quality frameworks
- Additional statistical hypotheses
- Price prediction models
- Streamlit dashboard
- Workflow orchestration
- Docker containerization
- Cloud deployment
- CI/CD
- Advanced geospatial analysis

These were intentionally deferred to protect the quality of the completed engineering core.

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
✅ End-to-End Pipeline
✅ 13 Automated Tests
✅ Assumptions Documentation
✅ Engineering Decision Log
✅ Completed Work Summary
✅ Incomplete Work Summary
✅ AI Usage Disclosure
```

### Remaining Submission Work

```text
⬜ Final Architecture Diagram
⬜ Professional 20+ Page PDF Report
⬜ Final Repository QA
⬜ Merge dev → main
⬜ Submit
```

---

## Author

**PabodaFdo**

BSc (Hons) Information Technology Undergraduate  
Specialization in Information Systems Engineering  
Sri Lanka Institute of Information Technology (SLIIT)

---

## Data Attribution

The Airbnb datasets used in this project are sourced from **Inside Airbnb**, an independent public-data initiative.

Raw dataset files are not included in this repository.

---

## Final Note

This project demonstrates a reproducible, memory-aware, validated, and analytically useful data engineering workflow for the Amsterdam Airbnb market.

> **The goal was not to maximize feature count, but to build a defensible submission with clear assumptions, reliable data processing, strong validation, transparent engineering decisions, reproducible outputs, focused analysis, and honest limitations.**

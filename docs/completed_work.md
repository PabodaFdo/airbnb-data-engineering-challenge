# Completed Work Summary

> **Project:** Amsterdam Airbnb Data Engineering Challenge  
> **City:** Amsterdam, Netherlands  
> **Strategy:** One-city, depth-first, 8 GB RAM-aware implementation

## Project Overview

This document summarizes the work completed for the Amsterdam Airbnb Data Engineering Challenge.

The project follows a one-city, depth-first strategy focused on:

- Dataset understanding.
- Automated profiling.
- Data-quality validation.
- Cleaning and standardization.
- Listing-level data enrichment.
- Memory-aware large-file processing.
- DuckDB analytical warehouse construction.
- SQL analysis.
- Exploratory data analysis.
- Statistical hypothesis testing.
- Automated testing.
- Reproducibility.
- Professional documentation.

The selected city is:

**Amsterdam, Netherlands**

The complete engineering workflow can be executed using:

```bash
python run_pipeline.py --city amsterdam
```

---

## 1. Project Setup and Repository Structure

A modular project structure was created to separate:

- Raw data
- Processed data
- Source code
- SQL queries
- Notebooks
- Data-quality outputs
- EDA outputs
- Statistical outputs
- Documentation
- Tests

Key project components include:

```text
airbnb-data-challenge/
│
├── run_pipeline.py
├── requirements.txt
├── README.md
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── warehouse/
│
├── src/
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
- Dataset grain identification
- Business-domain interpretation
- Source limitations and caveats
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
  └──────────────► Reviews
                    listing_id
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

`src/profile.py`

The profiler successfully processed all seven datasets.

Processing strategy:

- **Pandas** for small and medium datasets
- **DuckDB** for large detailed datasets

The following large datasets were processed without loading everything simultaneously into Pandas:

calendar.csv.gz: 3,819,725 rows
reviews.csv.gz: 545,162 rows

Generated profiling outputs:

`outputs/data_quality/dataset_summary.csv`
`outputs/data_quality/column_profile.csv`

The profiling stage completed successfully for:

7 / 7 datasets
---

## 6. Automated Data-Quality Validation

A reusable validation module was implemented in:

`src/validate.py`

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
- Source coverage differences
- Missing metadata
- Review-row repetition

The final validation result was:

| Status | Count |
|---|---:|
| PASS | 83 |
| WARNING | 7 |
| FAIL | 0 |

All seven warnings were reviewed individually and classified as known source limitations or non-critical structural conditions.

No critical validation failures were present.

---

## 7. Validation Gate

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

The limitation is understood.
The affected data remains valid for appropriate uses.
The condition is documented.

The latest successful pipeline execution produced:

| Status | Count |
|---|---:|
| PASS | 83 |
| WARNING | 7 |
| FAIL | 0 |

Therefore, the pipeline correctly continued to downstream processing.

---

## 8. Data Cleaning and Standardization

A reusable cleaning module was implemented in:

`src/clean.py`

Major cleaning work included:

- Currency-formatted price parsing
- Raw-price preservation
- Missing-price preservation
- Date parsing
- Boolean standardization
- Listing-key integrity validation
- Preservation of raw source files

Generated outputs:

`data/processed/cleaned_listings.parquet`
`data/processed/cleaned_detailed_listings.parquet`
`outputs/data_quality/cleaning_summary.csv`

Verified cleaned outputs:

cleaned_listings.parquet
10,465 rows
Unique non-null listing IDs

cleaned_detailed_listings.parquet
10,369 rows
Unique non-null listing IDs

Missing prices were preserved as null.

No zero-price imputation was performed.

---

## 9. Canonical Listing Population

The project established:

10,465 canonical listings

from the summary listings source.

The detailed listings source contained:

10,369 listings

Therefore:

96 canonical summary listings

were not represented in the detailed listings source.

These 96 records were preserved rather than discarded.

---

## 10. Review Data Investigation

The detailed review dataset contains:

545,162 review events

Review-level investigations included:

- Full duplicate-row checking
- Review identifier validation
- Repeated (listing_id, date) analysis
- Missing reviewer metadata

The summary reviews dataset contains repeated:

`(listing_id, date)`

combinations.

Observed repeated-row count:

22,541 rows

These were not blindly deleted because multiple legitimate review events may occur for the same listing on the same date.

---

## 11. Listing-Level Data Enrichment

A reusable enrichment module was implemented in:

`src/enrich.py`

The final enriched master dataset was designed at the grain:

One row per canonical listing

The enrichment process:

Starts with the 10,465 canonical listings.
Adds matching detailed listing attributes.
Aggregates detailed review data to listing level.
Aggregates calendar data to listing level.
Joins compact listing-level aggregates.
Creates derived analytical features.
Validates the final one-row-per-listing grain.

Generated outputs:

`data/processed/review_listing_aggregates.parquet`
`data/processed/calendar_listing_aggregates.parquet`
`data/processed/enriched_listing_master.parquet`
`outputs/data_quality/enrichment_summary.csv`

Final verified enrichment result:

Canonical listings preserved:       10,465
Detailed-source matches:            10,369
Summary-only listings preserved:        96
Unique non-null listing IDs:           Yes
---

## 12. Derived Features

Useful analytical features were created during enrichment.

Examples include:

- Best-available price
- Price source
- Price per bedroom
- Price per guest
- Review-event counts
- Review frequency measures
- Host portfolio segmentation
- Availability rate
- Unavailability rate proxy
- Review-history indicators

No derived feature was used to make claims beyond what the underlying source data can support.

---

## 13. Host Portfolio Segmentation

Hosts were segmented into analytical categories:

- **Single-listing host**
- **Small multi-listing host:** 2–5 listings
- **Large/professional host:** 6+ listings

This segmentation supports analysis of host concentration and market-supply structure.

The term large/professional host is treated as an analytical label based on listing count, not proof of legal or commercial business status.

---

## 14. Calendar Data Processing

The calendar dataset contains:

3,819,725 rows

To remain compatible with the 8 GB RAM development environment:

- The raw calendar dataset was not retained as a full Pandas DataFrame.
- DuckDB was used for aggregation.
- Data was reduced to compact listing-level metrics before enrichment.

Calendar unavailability is stored only as:

`unavailability_rate_proxy`

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
- Conservative DuckDB memory usage

The full pipeline successfully processed all available Amsterdam data without downsampling the core datasets.

---

## 16. DuckDB Analytical Warehouse

A DuckDB analytical warehouse was implemented through:

`src/build_warehouse.py`

Warehouse location:

`data/warehouse/airbnb_analytics.duckdb`

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

Canonical listings:  10,465
Review events:       545,162
Calendar rows:     3,819,725

Warehouse validation result:

| Warehouse Check | Count |
|---|---:|
| PASS | 17 |
| FAIL | 0 |

Generated warehouse validation output:

`outputs/data_quality/warehouse_summary.csv`
---

## 17. Analytical SQL Queries

A dedicated analytical SQL file was created:

`sql/analytical_queries.sql`

The SQL analysis addresses business questions including:

1. Pricing and performance by room type
2. Neighbourhood pricing and market activity
3. Host portfolio concentration
4. Superhost versus non-superhost performance
5. Neighbourhood review activity
6. Frequently reviewed but lower-rated listings
7. Availability-based proxy patterns
8. Pricing by accommodation capacity

The queries use the DuckDB analytical warehouse and documented thresholds where appropriate.

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

The final report will prioritize the strongest 6–8 visualizations rather than presenting every graph without interpretation.

---

## 19. Statistical Hypothesis Testing

Two focused statistical hypotheses were completed.

### Hypothesis 1

**Question:**

Do entire-home listings have significantly different or higher prices than private-room listings?

The statistical workflow includes:

- Null hypothesis
- Alternative hypothesis
- Sample-size review
- Distribution analysis
- Outlier considerations
- Test selection
- Test statistic
- P-value
- Effect size
- Business interpretation
### Hypothesis 2

**Question:**

Do superhost listings achieve different or higher review scores than non-superhost listings?

The analysis similarly includes:

- Null hypothesis
- Alternative hypothesis
- Assumption considerations
- Test selection
- Statistical result
- Effect size
- Practical interpretation
- Business interpretation

The project does not rely only on statistical significance.

Effect size and practical importance are also considered.

---

## 20. End-to-End Pipeline

The pipeline entry point was implemented in:

run_pipeline.py

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

Latest successful execution:

| Pipeline Stage | Time |
|---|---:|
| Verify Raw Source Files | 0.01 seconds |
| Automated Dataset Profiling | 18.75 seconds |
| Data-Quality Validation | 21.98 seconds |
| Critical Validation Gate | 0.13 seconds |
| Cleaning and Standardization | 1.56 seconds |
| Data Enrichment | 2.65 seconds |
| DuckDB Analytical Warehouse | 0.41 seconds |

Total execution time:

**45.49 seconds**

The complete pipeline finished successfully.

---

## 21. Automated Tests

A focused automated test suite was implemented in:

`tests/test_data_quality.py`

The suite contains:

13 automated tests

Test coverage includes:

- Currency price parsing
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

Latest test result:

| Test Result | Count |
|---|---:|
| Passed | 13 |
| Failed | 0 |

The test suite completed successfully.

---

## 22. Validation Warning Review

All seven validation warnings were manually reviewed.

They covered:

1. 96 missing summary-listing host IDs.
2. 3,994 missing summary-listing prices.
3. 96 canonical summary listings absent from detailed listings.
4. 3,992 missing detailed-listing prices.
5. Fully empty neighbourhood_group.
6. 22,541 repeated (listing_id, date) summary-review rows.
7. One missing reviewer name.

No warning required blind deletion or fabricated imputation.

Each was handled according to source meaning and analytical context.

---

## 23. Assumptions and Caveats Documentation

A dedicated assumptions document was created:

`docs/assumptions.md`

It documents topics including:

- City scope
- Canonical population
- Missing prices
- Missing host metadata
- Source coverage differences
- Calendar proxy limitations
- Review-count limitations
- Outlier treatment
- Statistical interpretation
- One-row-per-listing grain
- 8 GB RAM strategy
- Non-causal interpretation
---

## 24. Engineering Decision Log

A dedicated engineering decision log was created:

`docs/decision_log.md`

It records major decisions including:

- One city instead of multiple cities
- Depth over breadth
- Pandas versus DuckDB responsibilities
- Parquet outputs
- Canonical-source choice
- Left-preserving enrichment
- Aggregate-before-join strategy
- Null-price preservation
- Validation severity framework
- Validation gate behavior
- Warehouse design
- Statistical scope
- Outlier strategy
- Automated testing
- AI disclosure
- Confidential-data handling
---

## 25. Reproducibility

The project supports reproducibility through:

- Modular Python source code
- A single end-to-end pipeline entry point
- requirements.txt
- Separate raw and processed layers
- Deterministic output paths
- Data-quality reports
- Automated tests
- Documented assumptions
- Documented engineering decisions
- Git version control

Core execution command:

python run_pipeline.py --city amsterdam

Test execution command:

python -m pytest tests/ -v
---

# Final Completed Work Summary

The project successfully delivers:

- One-city Amsterdam scope
- Seven source datasets processed
- Complete dataset familiarization
- Automated profiling
- Automated data-quality validation
- Validation gate
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
- Analytical SQL queries
- Ten EDA visualizations
- Two statistical hypotheses
- End-to-end pipeline execution
- Thirteen automated tests
- Assumptions documentation
- Engineering decision documentation

Key final engineering results:

| Metric | Result |
|---|---:|
| Canonical listings preserved | 10,465 |
| Detailed listings matched | 10,369 |
| Summary-only listings preserved | 96 |
| Review events reconciled | 545,162 |
| Calendar rows reconciled | 3,819,725 |

Data-quality validation:
| Status | Count |
|---|---:|
| PASS | 83 |
| WARNING | 7 |
| FAIL | 0 |

Warehouse validation:
| Warehouse Check | Count |
|---|---:|
| PASS | 17 |
| FAIL | 0 |

Automated tests:
| Test Result | Count |
|---|---:|
| Passed | 13 |
| Failed | 0 |

Full pipeline execution:
Successful

Latest measured pipeline runtime:
**45.49 seconds**

The completed work demonstrates a reproducible, memory-aware, validated, and analytically useful data engineering workflow for the Amsterdam Airbnb market.
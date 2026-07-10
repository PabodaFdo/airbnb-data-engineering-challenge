# Amsterdam Airbnb Data Engineering & Analytics Challenge

An end-to-end **Data Engineering and Analytics project** built using publicly available data from **Inside Airbnb** for **Amsterdam, Netherlands**.

The project focuses on transforming raw Airbnb data into reliable, analysis-ready datasets through structured dataset familiarization, automated profiling, validation, cleaning, enrichment, analytical modeling, exploratory data analysis, and statistical testing.

The project follows a **depth-first approach**, prioritizing data quality, reproducibility, engineering decisions, analytical storytelling, and clear business interpretation.

---

## Project Objectives

The main objectives of this project are to:

- Understand and document the structure of all seven Inside Airbnb source files.
- Identify candidate primary keys, composite keys, and cross-dataset relationships.
- Build a repeatable data ingestion pipeline.
- Automate dataset profiling and data-quality reporting.
- Detect missing values, duplicates, outliers, and invalid domain values.
- Clean and standardize raw listing, review, calendar, and neighbourhood data.
- Build an enriched listing-level analytical dataset.
- Store processed analytical data efficiently using Parquet.
- Create a simple analytical data model using DuckDB.
- Execute meaningful SQL queries for business analysis.
- Perform focused exploratory data analysis.
- Conduct statistical hypothesis testing.
- Translate technical findings into clear business insights and recommendations.

---

## Selected City

**Amsterdam, North Holland, Netherlands**

The project intentionally focuses on one city to prioritize:

- Analytical depth
- Data quality
- Reproducibility
- Clean engineering practices
- Memory-aware processing
- Clear business storytelling

The pipeline is designed with future extensibility in mind and can later be generalized to support additional cities.

---

## Dataset

All data used in this project comes from the publicly available **Inside Airbnb** dataset.

Seven Amsterdam source files are used:

| File | Rows / Features | Columns / Properties | Grain |
|---|---:|---:|---|
| `neighbourhoods.csv` | 22 rows | 2 columns | One row per neighbourhood |
| `listings.csv` | 10,465 rows | 19 columns | One row per listing |
| `reviews.csv` | 545,162 rows | 2 columns | Review event by listing and date |
| `listings.csv.gz` | 10,369 rows | 90 columns | One row per detailed listing |
| `neighbourhoods.geojson` | 22 features | Geographic properties + geometry | One geographic feature per neighbourhood |
| `calendar.csv.gz` | 3,819,725 rows | 5 columns | One row per listing per calendar date |
| `reviews.csv.gz` | 545,162 rows | 6 columns | One row per individual review |

The raw datasets are intentionally excluded from the Git repository because of file size and reproducibility considerations.

They can be downloaded directly from the official Inside Airbnb data portal.

---

## Dataset Familiarization — Completed

Dataset Familiarization has been completed for all seven source files.

For every dataset, the project reviewed or validated:

- File shape
- Column names
- Data types
- Sample records
- Missing values and missing percentages
- Unique values and cardinality
- Minimum and maximum values where meaningful
- Duplicate rows
- Candidate primary keys
- Composite keys
- Cross-dataset relationships
- Business meaning
- Data-quality limitations
- Downstream processing strategy

The completed notebook is:

```text
notebooks/01_dataset_familiarization.ipynb
```

---

## Key Dataset Findings

### 1. Canonical listing population

`listings.csv` contains **10,465 listings** and is used as the canonical listing population.

`listings.csv.gz` contains **10,369 detailed listings**, meaning **96 listings from the summary dataset are absent from the detailed listing source**.

These 96 listings should not be silently discarded during enrichment.

---

### 2. Calendar coverage is structurally strong

`calendar.csv.gz` contains:

- **3,819,725 rows**
- **10,465 unique listing IDs**
- Exactly **365 calendar rows per listing**

The validated composite key is:

```text
(listing_id, date)
```

Because the calendar dataset is large, it should be aggregated before being joined to listing-level data.

---

### 3. Detailed reviews are preferred for review-level analysis

Both review datasets contain **545,162 rows**.

`reviews.csv` contains only:

```text
listing_id
date
```

and does not have a unique review identifier.

`reviews.csv.gz` contains:

```text
listing_id
id
date
reviewer_id
reviewer_name
comments
```

The `id` column is the preferred candidate primary key for individual reviews.

The summary reviews file is retained mainly for validation and lightweight reference, while detailed reviews are preferred for enrichment.

---

### 4. Summary reviews contain repeated listing-date combinations

The summary review dataset contains repeated `(listing_id, date)` combinations because multiple individual reviews can occur for the same listing on the same date.

Observed results:

- **12,942 repeated `(listing_id, date)` groups**
- **22,541 extra rows beyond the first occurrence**

Therefore:

```text
(listing_id, date)
```

is **not** a unique key for `reviews.csv`.

---

### 5. Neighbourhood relationships are highly consistent

All **22 Amsterdam neighbourhoods** align across:

- `neighbourhoods.csv`
- `listings.csv`
- `listings.csv.gz`
- `neighbourhoods.geojson`

This provides a strong foundation for neighbourhood-level enrichment and optional geographic analysis.

---

### 6. Missing values require context-aware treatment

Missing values will not be handled with a universal strategy such as filling every null with zero.

Examples:

- Missing price does not mean zero price.
- Missing review scores do not mean zero quality.
- Missing review fields may indicate no review history.
- Fully empty fields may be excluded from processed analytical outputs while remaining untouched in raw source data.

---

### 7. Availability is not true occupancy

Calendar availability does not prove whether an unavailable date was booked.

Therefore, any derived metric based on unavailable dates will be described as an:

```text
availability-based proxy
```

rather than true occupancy.

---

### 8. Review count is not booking count

Not every guest leaves a review.

Review count or review frequency may be used as a proxy for guest activity, but not as an exact measure of reservations.

---

## Cross-Dataset Relationships

The primary relationship structure is:

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
                     │     │           │ neighbourhood
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

Important validated relationships include:

- `listings.csv.id` → canonical listing identifier.
- `listings.csv.gz.id` → detailed listing subset.
- `calendar.csv.gz.listing_id` → `listings.csv.id`.
- `reviews.csv.gz.listing_id` → `listings.csv.id`.
- `reviews.csv.listing_id` → `listings.csv.id`.
- `neighbourhoods.csv.neighbourhood` → listing neighbourhood fields.
- `neighbourhoods.geojson.neighbourhood` → neighbourhood reference data.

---

## Data Quality Outputs

The Dataset Familiarization notebook currently generates compact outputs such as:

```text
outputs/data_quality/
├── calendar_availability_distribution.csv
├── calendar_csv_gz_column_profile.csv
├── calendar_window_distribution.csv
├── detailed_listings_column_profile.csv
├── neighbourhoods_column_profile.csv
├── neighbourhoods_geojson_geometry_validation.csv
├── neighbourhoods_geojson_property_profile.csv
├── reviews_csv_gz_column_profile.csv
├── reviews_csv_gz_repeated_listing_date_groups.csv
├── reviews_csv_gz_top_listings_by_review_count.csv
├── summary_listings_column_profile.csv
└── summary_reviews_column_profile.csv
```

These files provide reproducible evidence of profiling, validation, and structural checks performed during familiarization.

---

## 8 GB RAM-Aware Processing Strategy

The project is intentionally designed for an **8 GB RAM laptop**.

The core memory rule is:

> Never keep all seven raw datasets as full Pandas DataFrames in memory at the same time.

Processing strategy:

- Use **Pandas** for small and medium datasets.
- Use **DuckDB** or chunked processing for large datasets.
- Read only required columns where possible.
- Aggregate large review and calendar datasets before joins.
- Save compact intermediate outputs to Parquet.
- Use listing-level or aggregated datasets for most visualizations.
- Release large temporary DataFrames after use.

Recommended access pattern:

| Dataset | Recommended Access |
|---|---|
| `neighbourhoods.csv` | Pandas |
| `listings.csv` | Pandas |
| `reviews.csv` | Pandas |
| `listings.csv.gz` | Pandas |
| `neighbourhoods.geojson` | JSON / GeoPandas if needed |
| `calendar.csv.gz` | DuckDB / chunked processing |
| `reviews.csv.gz` | DuckDB / chunked processing |

---

## Project Architecture

The planned end-to-end data flow is:

```text
Inside Airbnb
      ↓
Raw CSV / CSV.GZ / GeoJSON Files
      ↓
Dataset Familiarization
      ↓
Data Ingestion
      ↓
Automated Profiling
      ↓
Data Quality Validation
      ↓
Cleaning & Standardization
      ↓
Data Enrichment
      ↓
Processed Parquet Files
      ↓
DuckDB Analytical Model
      ↓
SQL Analysis
      ↓
Exploratory Data Analysis
      ↓
Statistical Testing
      ↓
Business Findings & Recommendations
```

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
├── config/
│   └── city_config.yaml
│
├── data/
│   ├── raw/
│   │   └── amsterdam/
│   └── processed/
│
├── src/
│   ├── __init__.py
│   ├── ingest.py
│   ├── profile.py
│   ├── validate.py
│   ├── clean.py
│   ├── enrich.py
│   ├── database.py
│   └── utils.py
│
├── notebooks/
│   ├── 01_dataset_familiarization.ipynb
│   └── 02_eda_and_statistics.ipynb
│
├── sql/
│   └── analytical_queries.sql
│
├── outputs/
│   ├── figures/
│   ├── tables/
│   ├── data_quality/
│   └── database/
│
├── docs/
│   ├── assumptions.md
│   ├── decision_log.md
│   ├── completed_work.md
│   ├── incomplete_work.md
│   └── ai_usage_disclosure.md
│
└── tests/
```

---

## Data Engineering Workflow

### 1. Dataset Familiarization ✅ Completed

Completed for all seven source files.

The project now has:

- File inventory
- Schema documentation
- Missing-value summaries
- Duplicate analysis
- Candidate-key validation
- Cross-dataset relationship validation
- Business-domain interpretation
- Dataset limitations
- Overall seven-dataset summary
- Memory-aware processing decisions

---

### 2. Automated Data Profiling — Next Stage

The next phase is to create a reusable profiling module:

```text
src/profile.py
```

The profiler will generate structured reports containing:

- Dataset name
- Row count
- Column count
- Duplicate count
- Column names
- Data types
- Missing counts
- Missing percentages
- Unique counts
- Minimum and maximum values
- Sample values

Planned outputs:

```text
outputs/data_quality/dataset_summary.csv
outputs/data_quality/column_profile.csv
```

For large text-heavy columns, exact high-cardinality calculations may be avoided when they add significant cost without analytical value.

---

### 3. Data Quality Validation

The validation phase will introduce reusable rules for areas such as:

- Negative or invalid prices
- Invalid latitude and longitude values
- Unexpected availability ranges
- Duplicate listing identifiers
- Missing required join keys
- Invalid date values
- Unexpected room-type categories
- Referential-integrity issues

Planned output:

```text
outputs/data_quality/validation_results.csv
```

---

### 4. Cleaning and Standardization

The cleaning stage will include:

- Cleaning currency-formatted price fields
- Converting appropriate columns to numeric types
- Parsing date columns
- Handling missing values using context-aware strategies
- Normalizing categorical values
- Preserving raw data
- Writing separate processed outputs

---

### 5. Data Enrichment

An enriched listing-level master dataset will be created.

Potential fields include:

- Listing ID
- Host ID
- Neighbourhood
- Latitude and longitude
- Room type
- Property type
- Clean price
- Bedrooms
- Beds
- Minimum nights
- Availability
- Number of reviews
- Review score
- Superhost status
- Host tenure
- Price per bedroom
- Review frequency
- Host portfolio size

Optional calendar-derived values may include:

- Average calendar price, if supported by the source data
- Weekday and weekend prices, if supported by the source data
- Availability-based proxy metrics

Any occupancy-related metric will be clearly described as a **proxy**, not verified occupancy.

---

### 6. Analytical Data Modeling

The project will use **DuckDB** as the analytical database engine.

Planned analytical tables include:

- `dim_listing`
- `dim_host`
- `dim_neighbourhood`
- `fact_listing_performance`

An optional daily calendar fact table may be included if justified by analytical needs, time, and storage constraints.

---

## Exploratory Data Analysis

The project aims to investigate several key areas:

1. Price distribution and premium listing outliers
2. Price differences by room type
3. Neighbourhood-level pricing patterns
4. Host portfolio concentration
5. Availability patterns
6. Reviews and listing performance
7. Temporal pricing trends, if supported by the source data
8. Geographic patterns, if time permits

Each major analytical result will follow:

```text
Finding → Business Meaning → Recommended Action
```

---

## Statistical Analysis

Two focused hypotheses are planned.

### Hypothesis 1

**Do entire-home listings have significantly higher prices than private rooms?**

### Hypothesis 2

**Do superhost listings receive different or higher review scores than non-superhost listings?**

The statistical workflow will include:

- Null and alternative hypotheses
- Sample-size review
- Distribution assessment
- Assumption checking
- Statistical test selection
- Test statistic
- P-value
- Effect size
- Practical significance
- Business interpretation
- Limitations

---

## Technology Stack

| Area | Technology |
|---|---|
| Programming Language | Python |
| Data Processing | Pandas, NumPy |
| Large-File Analytics | DuckDB |
| Data Storage | Parquet |
| Statistical Testing | SciPy |
| Visualization | Matplotlib, Seaborn |
| Notebook Environment | Jupyter Notebook |
| Configuration | YAML |
| Version Control | Git & GitHub |

---

## Getting Started

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd airbnb-data-engineering-challenge
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Download the Amsterdam dataset

Download the seven Amsterdam source files from the Inside Airbnb data portal and place them inside:

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

The `.csv.gz` files should remain compressed.

---

## Running the Pipeline

The planned final execution command is:

```bash
python run_pipeline.py --city amsterdam
```

The pipeline implementation is still in progress and this section will be updated as reusable engineering modules are completed.

---

## Project Status

### Current Stage

- [x] Project scope defined
- [x] Amsterdam selected as the primary city
- [x] Seven Inside Airbnb datasets downloaded
- [x] Initial repository structure created
- [x] Dataset familiarization completed for all seven source files
- [x] Missing-value analysis completed
- [x] Duplicate analysis completed
- [x] Candidate keys validated
- [x] Cross-dataset relationships verified
- [x] Dataset limitations documented
- [x] Overall seven-dataset summary completed
- [ ] Automated profiling module
- [ ] Data quality validation
- [ ] Data cleaning and standardization
- [ ] Data enrichment
- [ ] DuckDB analytical model
- [ ] SQL analysis
- [ ] Exploratory data analysis
- [ ] Statistical hypothesis testing
- [ ] Professional analytical report

### Current Checkpoint

```text
✅ Dataset Familiarization Complete
              ↓
NEXT: Automated Data Profiling
              ↓
      Data Quality Validation
              ↓
     Cleaning & Standardization
              ↓
          Data Enrichment
```

---

## Engineering Decisions

Important architectural and analytical decisions are documented in:

```text
docs/decision_log.md
```

Key decisions include:

- Why one city was selected
- Why Pandas is used for smaller datasets
- Why DuckDB is preferred for large-file analytics
- Why Parquet is used for processed data
- Why large raw tables are aggregated before joins
- Why missing values require context-aware handling
- Why availability is not treated as true occupancy
- Why review count is not treated as exact booking count
- Why the project is designed around an 8 GB RAM constraint
- Why optional work is deferred until the core pipeline is complete

---

## Assumptions and Limitations

The project explicitly recognizes the following limitations:

- Airbnb data is obtained through web scraping and may contain inconsistencies.
- Availability does not necessarily represent true vacancy or verified occupancy.
- Review count is an imperfect proxy for booking demand.
- Revenue estimates do not represent actual host earnings unless directly supported.
- Historical review activity may not perfectly align with current listing attributes.
- Historical coverage may be incomplete.
- Some listing fields contain substantial missingness.
- The detailed listing dataset does not contain every listing from the summary population.
- A single-city analysis cannot automatically be generalized to all Airbnb markets.
- Statistical findings do not necessarily imply causation.

---

## AI Usage Disclosure

AI-assisted work used during this project is transparently documented in:

```text
docs/ai_usage_disclosure.md
```

The disclosure will include:

- AI tools used
- Areas where AI assistance was used
- Important prompts
- Validation methods
- Modifications made to AI-generated suggestions

All code, analytical outputs, statistical results, and interpretations will be validated against the actual project data.

---

## Future Improvements

Potential future improvements include:

- Multi-city pipeline support
- Automated schema harmonization
- Incremental processing
- More comprehensive automated data-quality testing
- Additional statistical analyses
- Price prediction models
- Streamlit dashboard
- Workflow orchestration
- Docker containerization
- Cloud deployment
- CI/CD

---

## Author

**PabodaFdo**

BSc (Hons) Information Technology Undergraduate  
Specialization in Information Systems Engineering  
Sri Lanka Institute of Information Technology (SLIIT)

---

## License and Data Attribution

This repository contains original project code, engineering logic, documentation, and analysis.

The Airbnb datasets used in this project are sourced from **Inside Airbnb**, an independent public-data initiative.

Raw dataset files are not included in this repository.

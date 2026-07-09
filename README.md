# Amsterdam Airbnb Data Engineering & Analytics Challenge

An end-to-end **Data Engineering and Analytics project** built using publicly available data from **Inside Airbnb** for **Amsterdam, Netherlands**.

The project focuses on transforming raw Airbnb data into reliable, analysis-ready datasets through automated data ingestion, profiling, validation, cleaning, enrichment, analytical modeling, exploratory data analysis, and statistical testing.

The project follows a **depth-first approach**, prioritizing data quality, reproducibility, engineering decisions, analytical storytelling, and clear business interpretation.

---

## Project Objectives

The main objectives of this project are to:

* Understand and document the structure of the Inside Airbnb datasets.
* Build a repeatable data ingestion pipeline.
* Automate dataset profiling and data quality analysis.
* Detect missing values, duplicates, outliers, and invalid domain values.
* Clean and standardize raw listing, review, calendar, and neighbourhood data.
* Build an enriched listing-level analytical dataset.
* Store processed analytical data efficiently using Parquet.
* Create a simple analytical data model using DuckDB.
* Execute meaningful SQL queries for business analysis.
* Perform focused exploratory data analysis.
* Conduct statistical hypothesis testing.
* Translate technical findings into clear business insights and recommendations.

---

## Selected City

**Amsterdam, North Holland, Netherlands**

The project currently focuses on one city to prioritize:

* Analytical depth
* Data quality
* Reproducibility
* Clean engineering practices
* Clear business storytelling

The pipeline is designed with future extensibility in mind and can later be generalized to support additional cities.

---

## Dataset

All data used in this project comes from the publicly available **Inside Airbnb** dataset.

The following seven files are used:

| File                     | Description                                          |
| ------------------------ | ---------------------------------------------------- |
| `listings.csv.gz`        | Detailed information about Airbnb listings and hosts |
| `listings.csv`           | Summary listing-level information                    |
| `calendar.csv.gz`        | Daily listing availability and pricing information   |
| `reviews.csv.gz`         | Detailed guest review data                           |
| `reviews.csv`            | Summary review information                           |
| `neighbourhoods.csv`     | Neighbourhood names and geographical groupings       |
| `neighbourhoods.geojson` | Geographic neighbourhood boundary data               |

The raw datasets are intentionally excluded from the Git repository because of file size and reproducibility considerations.

They can be downloaded directly from the official Inside Airbnb data portal.

---

## Project Architecture

The planned data flow is:

```text
Inside Airbnb
      ↓
Raw CSV / CSV.GZ / GeoJSON Files
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

## Planned Data Engineering Workflow

### 1. Dataset Familiarization

The first stage focuses on understanding all available datasets by examining:

* File names
* Number of rows and columns
* Column names
* Data types
* Missing values
* Missing percentages
* Unique values and cardinality
* Minimum and maximum values
* Sample values
* Duplicate records
* Relationships between datasets

---

### 2. Automated Data Profiling

A reusable profiling module will generate structured reports containing:

* Dataset name
* Row count
* Column count
* Duplicate count
* Column data types
* Missing counts
* Missing percentages
* Unique counts
* Minimum and maximum values
* Sample values

Generated profiling results will be stored under:

```text
outputs/data_quality/
```

---

### 3. Data Quality Validation

Validation rules will be introduced for areas such as:

* Negative or invalid prices
* Invalid latitude and longitude values
* Unexpected availability ranges
* Duplicate listing identifiers
* Missing required join keys
* Invalid date values
* Unexpected room type categories

Validation results will be exported for review and documentation.

---

### 4. Cleaning and Standardization

The cleaning stage will include:

* Cleaning currency-formatted price fields
* Converting appropriate columns into numerical types
* Parsing dates into standard datetime formats
* Handling missing values using context-aware strategies
* Normalizing categorical values
* Preserving raw data and creating separate processed outputs

---

### 5. Data Enrichment

An enriched listing-level master dataset will be created.

Potential derived features include:

* Host tenure
* Price per bedroom
* Review frequency
* Host portfolio size
* Average calendar price
* Weekday and weekend prices
* Availability-based analytical indicators

Any calculated occupancy-related measure will be clearly described as a **proxy** rather than actual occupancy unless supported directly by the data.

---

### 6. Analytical Data Modeling

The project will use **DuckDB** as the analytical database engine.

Planned analytical tables include:

* `dim_listing`
* `dim_host`
* `dim_neighbourhood`
* `fact_listing_performance`

An optional daily calendar fact table may also be included if time permits.

---

## Exploratory Data Analysis

The project aims to investigate several key areas:

1. Price distribution and premium listing outliers
2. Price differences by room type
3. Neighbourhood-level pricing patterns
4. Host portfolio concentration
5. Availability patterns
6. Reviews and listing performance
7. Temporal pricing trends, if time permits
8. Geographic patterns, if time permits

Each major analytical result will follow the format:

```text
Finding → Business Meaning → Recommended Action
```

---

## Statistical Analysis

The planned hypothesis tests include:

### Hypothesis 1

**Do entire-home listings have significantly higher prices than private rooms?**

### Hypothesis 2

**Do superhost listings receive different or higher review scores than non-superhost listings?**

The statistical analysis will consider:

* Null and alternative hypotheses
* Distribution characteristics
* Assumption checking
* Statistical test selection
* Test statistics
* P-values
* Effect sizes
* Practical significance
* Business interpretation

---

## Technology Stack

| Area                 | Technology          |
| -------------------- | ------------------- |
| Programming Language | Python              |
| Data Processing      | Pandas, NumPy       |
| Data Storage         | Parquet             |
| Analytical Database  | DuckDB              |
| Statistical Testing  | SciPy               |
| Visualization        | Matplotlib, Seaborn |
| Notebook Environment | Jupyter Notebook    |
| Configuration        | YAML                |
| Version Control      | Git & GitHub        |

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

Download the seven available Amsterdam files from the Inside Airbnb data portal and place them inside:

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

The `.csv.gz` files should remain compressed. Pandas can read them directly.

---

## Running the Pipeline

The planned pipeline execution command is:

```bash
python run_pipeline.py --city amsterdam
```

This section will be updated as the implementation progresses.

---

## Project Status

### Current Stage

* [x] Project scope defined
* [x] Amsterdam selected as the primary city
* [x] Seven Inside Airbnb datasets downloaded
* [x] Initial repository structure created
* [ ] Dataset familiarization
* [ ] Automated profiling
* [ ] Data quality validation
* [ ] Data cleaning and standardization
* [ ] Data enrichment
* [ ] DuckDB analytical model
* [ ] SQL analysis
* [ ] Exploratory data analysis
* [ ] Statistical hypothesis testing
* [ ] Professional analytical report

---

## Engineering Decisions

Important architectural and analytical decisions will be documented in:

```text
docs/decision_log.md
```

Key decisions include:

* Why one city was selected
* Why Pandas was selected for data processing
* Why DuckDB was selected as the analytical engine
* Why Parquet is used for processed data
* Missing-value handling strategies
* Outlier treatment decisions
* Statistical test selection
* Scope and prioritization decisions

---

## Assumptions and Limitations

The project will explicitly document assumptions and limitations, including:

* Airbnb data is obtained through web scraping and may contain inconsistencies.
* Availability does not necessarily represent true vacancy.
* Review count is an imperfect proxy for booking demand.
* Revenue estimates do not represent actual host earnings.
* Historical coverage may be incomplete.
* A single-city analysis cannot automatically be generalized to all Airbnb markets.
* Statistical findings do not necessarily imply causation.

---

## AI Usage Disclosure

AI-assisted work used during this project will be transparently documented in:

```text
docs/ai_usage_disclosure.md
```

The disclosure will include:

* AI tools used
* Areas where AI assistance was used
* Important prompts
* Validation methods
* Modifications made to AI-generated suggestions

All code, analytical outputs, statistical results, and interpretations will be validated against the actual project data.

---

## Future Improvements

Potential future improvements include:

* Multi-city pipeline support
* Automated schema harmonization
* Incremental processing
* Additional statistical analyses
* Price prediction models
* Streamlit dashboard
* Workflow orchestration
* Docker containerization
* Cloud deployment
* CI/CD
* Extended data quality testing

---

## Author

**PabodaFdo**

BSc (Hons) Information Technology Undergraduate
Specialization in Information Systems Engineering
Sri Lanka Institute of Information Technology (SLIIT)

---

## License and Data Attribution

This repository contains original project code and analysis.

The Airbnb datasets used in this project are sourced from **Inside Airbnb**, an independent public-data initiative.

Raw dataset files are not included in this repository.

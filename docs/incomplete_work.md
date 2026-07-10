# Incomplete Work Summary

## Purpose

This document records the work that was intentionally not completed within the available execution window for the Amsterdam Airbnb Data Engineering Challenge.

The project followed a depth-first strategy. Priority was given to completing the core engineering and analytical workflow with strong validation, reproducibility, testing, and documentation rather than attempting too many optional features superficially.

The completed core includes:

- Dataset familiarization.
- Automated profiling.
- Data-quality validation.
- Cleaning and standardization.
- Listing-level enrichment.
- Review and calendar aggregation.
- DuckDB analytical warehouse construction.
- Analytical SQL queries.
- Exploratory data analysis.
- Statistical hypothesis testing.
- End-to-end pipeline execution.
- Automated tests.
- Assumptions documentation.
- Engineering decision documentation.

The following areas were not prioritized.

---

## 1. Multi-City Analysis

### Status

Not implemented.

### Reason

The project intentionally focuses on one city:

**Amsterdam, Netherlands**

The goal was to achieve greater depth in:

- Data understanding.
- Data-quality validation.
- Pipeline reliability.
- Analytical modeling.
- Statistical testing.
- Business interpretation.
- Documentation.

Adding additional cities would have required:

- Additional downloads.
- Schema harmonization.
- Cross-city validation.
- Currency considerations.
- More complex comparison logic.
- Additional report content.
- More opportunities for inconsistent processing.

### Future improvement

The current pipeline could be generalized further using configuration-driven city selection and repeated execution across multiple markets.

---

## 2. Machine Learning

### Status

Not implemented.

### Reason

Machine learning was treated as optional and was not prioritized over the core data-engineering requirements.

A reliable predictive model would require additional work in:

- Feature selection.
- Leakage prevention.
- Train/test design.
- Cross-validation.
- Model comparison.
- Evaluation metrics.
- Interpretation.
- Bias and limitation analysis.

The available time was better invested in:

- Data quality.
- Reproducibility.
- Warehouse design.
- EDA.
- Statistical rigor.
- Testing.
- Documentation.

### Future improvement

A future extension could explore:

- Price prediction.
- Listing-segment classification.
- Demand-proxy modeling.
- Review-score prediction.

Any predictive model should be built only after careful feature validation and evaluation design.

---

## 3. Interactive Dashboard

### Status

Not implemented.

### Reason

A Streamlit or similar dashboard was considered optional.

The project already includes:

- Analytical SQL.
- EDA visualizations.
- Statistical outputs.
- Structured reporting.

A dashboard was not prioritized ahead of the core engineering workflow and required submission documentation.

### Future improvement

A future dashboard could include:

- KPI cards.
- Room-type filters.
- Neighbourhood filters.
- Price distributions.
- Host portfolio segmentation.
- Review activity.
- Availability-based proxy analysis.
- Key business insights.

The dashboard should read from compact Parquet or DuckDB outputs rather than raw large files.

---

## 4. Cloud Deployment

### Status

Not implemented.

### Reason

The project was designed and validated for local execution on an 8 GB RAM Windows laptop.

Cloud deployment was not required for the core submission and would add extra infrastructure work without improving the fundamental data-engineering quality of the current deliverable.

### Future improvement

Possible future deployment options include:

- AWS.
- Azure.
- Google Cloud.
- Managed container platforms.
- Scheduled cloud execution.

---

## 5. Workflow Orchestration

### Status

Not implemented.

### Reason

The project currently uses:

```bash
python run_pipeline.py --city amsterdam

to execute the complete engineering workflow.

A separate orchestration framework such as Airflow, Prefect, or Dagster was not added because the project has a focused single-city scope and the existing pipeline already provides ordered, reproducible stage execution.

Future improvement

A future production-oriented version could use orchestration for:

Scheduling.
Retries.
Dependency management.
Monitoring.
Failure alerts.
Incremental execution.
6. Incremental Data Processing
Status

Not implemented.

Reason

The current pipeline performs full-batch processing of the selected Amsterdam datasets.

Incremental processing would require reliable change-detection logic, stable source update behavior, and additional metadata management.

Future improvement

Possible improvements include:

Incremental ingestion.
Watermark tracking.
Change-data capture.
Partition-based updates.
Merge/upsert logic.
Historical snapshots.
7. CI/CD Pipeline
Status

Not implemented.

Reason

The project includes local automated tests, but a full continuous integration and deployment workflow was not added.

Future improvement

A GitHub Actions workflow could automatically:

Install dependencies.
Run unit tests.
Validate code quality.
Execute selected lightweight pipeline checks.
Prevent merges when tests fail.
8. Dockerization
Status

Not implemented.

Reason

The project is currently reproducible through:

Python virtual environment.
requirements.txt.
Modular source code.
A single pipeline entry point.

Docker was not prioritized ahead of core engineering and documentation deliverables.

Future improvement

A Docker image could improve portability and environment consistency.

9. Advanced Data-Quality Framework
Status

Not implemented.

Reason

The project already includes a custom validation framework with:

PASS.
WARNING.
FAIL.

It also includes a critical validation gate.

External frameworks such as Great Expectations, Soda, or Deequ were not added because the current custom validation system already covers the most important source-quality checks for the assignment.

Future improvement

A larger production system could integrate:

Great Expectations.
Soda.
Data contracts.
Schema evolution checks.
Trend-based anomaly detection.
10. Full Historical Snapshot Tracking
Status

Not implemented.

Reason

The project uses the available Amsterdam dataset snapshot and does not maintain a full historical slowly changing dimension model.

Future improvement

A production version could support:

Snapshot dates.
Historical listing changes.
Host changes.
Price changes.
Availability changes.
Slowly changing dimensions.
11. Real Occupancy and Revenue Calculation
Status

Not implemented.

Reason

The source data does not provide verified reservation records.

Therefore, the project does not claim to calculate:

True occupancy.
Confirmed booked nights.
Actual host revenue.
Verified reservation volume.

Calendar unavailability is treated only as:

unavailability_rate_proxy

and is not interpreted as true occupancy.

Future improvement

Accurate occupancy or revenue analysis would require trusted reservation and transaction data.

12. Causal Analysis
Status

Not implemented.

Reason

The project uses observational Airbnb data.

Therefore, the statistical analyses identify associations or differences but do not prove causation.

Future improvement

Causal questions would require stronger study design, additional variables, experiments, quasi-experimental methods, or causal-inference techniques.

13. Additional Statistical Hypotheses
Status

Not prioritized.

Reason

The project completed two focused statistical hypotheses deeply rather than many shallow tests.

The selected analyses were:

Entire-home versus private-room pricing.
Superhost versus non-superhost review-score performance.

The emphasis was on:

Proper hypotheses.
Appropriate test selection.
Statistical significance.
Effect size.
Practical significance.
Business interpretation.
Future improvement

Possible future tests include:

Neighbourhood price differences.
Weekend versus weekday pricing.
High-review versus low-review listing performance.
Availability-proxy differences across room types.
14. Advanced Geographic Visualization
Status

Not prioritized.

Reason

The project includes neighbourhood-level analysis but did not prioritize advanced interactive geospatial mapping.

Future improvement

Possible additions include:

Choropleth maps.
Listing-density maps.
Price heatmaps.
Interactive neighbourhood exploration.
Final Prioritization Rationale

The following principle guided the project:

Complete the core work deeply before adding optional breadth.

The project therefore prioritized:

Reliable data ingestion.
Complete dataset familiarization.
Automated profiling.
Data-quality validation.
Cleaning.
Enrichment.
Listing-grain preservation.
DuckDB analytical modeling.
SQL.
EDA.
Statistical testing.
Automated tests.
Documentation.
Reproducibility.

The following optional areas were intentionally deferred:

Multiple cities.
Machine learning.
Dashboarding.
Cloud deployment.
Orchestration.
Incremental processing.
CI/CD.
Docker.
Advanced geospatial analysis.

This was a deliberate engineering trade-off rather than an accidental omission.

The goal was to submit a smaller number of complete, validated, reproducible, and well-documented components instead of a larger number of unfinished features.
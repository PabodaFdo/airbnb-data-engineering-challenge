# Incomplete Work Summary

> **Project:** Amsterdam Airbnb Data Engineering & Analytics Challenge  
> **City:** Amsterdam, Netherlands  
> **Strategy:** Depth-first prioritization of core engineering quality over optional breadth  
> **Primary Development Branch:** `dev`

---

## Purpose

This document records work that remains intentionally incomplete, deferred, out of scope, or dependent on unavailable source data.

The project followed a depth-first strategy. Priority was given to completing a reliable engineering and analytical core before adding optional breadth.

The completed core now includes:

- Dataset familiarization
- Automated profiling
- Data-quality validation
- Critical validation gate
- Cleaning and standardization
- Listing-level enrichment
- Review and calendar aggregation
- Processed Parquet outputs
- DuckDB analytical warehouse
- Eight analytical SQL queries
- Ten EDA visualizations
- Two statistical hypothesis tests
- End-to-end pipeline execution
- Thirteen automated tests
- GitHub Actions continuous integration
- Focused machine-learning price-prediction experiment
- Random Forest feature-importance analysis
- Actual-vs-predicted diagnostic analysis
- Architecture documentation
- Assumptions documentation
- Engineering decision documentation
- AI usage disclosure

The following areas remain incomplete, deferred, planned, or out of scope.

---

## Recently Completed Optional Extensions

Some work that was originally deferred has now been completed after the engineering core was stabilized.

### Focused Machine Learning

**Previous status:** Deferred  
**Current status:** **Completed**

A focused price-prediction experiment was implemented in:

```text
experiments/price_prediction.py
```

Three models were compared:

1. Dummy Regressor
2. Ridge Regression
3. Random Forest Regressor

Best result:

| Model | MAE | RMSE | R² |
|---|---:|---:|---:|
| **Random Forest Regressor** | **€78.61** | **€133.76** | **0.5884** |

The experiment also includes:

- Target-leakage prevention
- 80/20 train-test split
- Reproducible random state
- Missing-feature preprocessing
- Log target transformation
- Feature-importance analysis
- Actual-vs-predicted diagnostic visualization

Therefore, machine learning is no longer listed as incomplete work.

### GitHub Actions Continuous Integration

**Previous status:** Deferred  
**Current status:** **Completed**

A GitHub Actions workflow was implemented in:

```text
.github/workflows/ci.yml
```

The workflow:

- Checks out the repository
- Sets up Python 3.13
- Installs dependencies
- Compiles Python modules
- Runs automated tests

The workflow has completed successfully on the `dev` branch.

Therefore, continuous integration is no longer listed as incomplete work.

---

## 1. Interactive Dashboard

### Status

**Planned next — not yet implemented.**

### Purpose

The next planned analytical extension is a live interactive dashboard for exploratory market analysis.

The preferred implementation is:

```text
Streamlit
```

The dashboard should read from compact processed outputs such as:

```text
data/processed/enriched_listing_master.parquet
```

and, where useful:

```text
data/warehouse/airbnb_analytics.duckdb
```

rather than loading all raw source files directly.

### Planned dashboard areas

The intended dashboard may include:

- Market overview KPI cards
- Neighbourhood filters
- Room-type filters
- Price-range filters
- Listing-count analysis
- Median-price comparisons
- Price distributions
- Host portfolio segmentation
- Review activity
- Availability-proxy patterns
- Accommodation-capacity analysis
- Statistical findings
- Machine-learning model comparison
- Random Forest feature importance
- Actual-vs-predicted diagnostic results
- Key business insights and caveats

### Completion rule

The dashboard should be moved to completed work only after it has been:

1. Implemented
2. Tested locally
3. Verified against processed project outputs
4. Documented in the README
5. Added to the final report where relevant

---

## 2. Multi-City Analysis

### Status

**Not implemented.**

### Reason

The project intentionally focuses on one city:

**Amsterdam, Netherlands**

The goal was to achieve greater depth in:

- Data understanding
- Data-quality validation
- Pipeline reliability
- Analytical modeling
- Statistical testing
- Business interpretation
- Machine-learning experimentation
- Testing
- Documentation

Adding additional cities would require:

- Additional data acquisition
- Schema harmonization
- Cross-city validation
- Market-specific interpretation
- Currency considerations
- More complex comparison logic
- Additional report content
- More opportunities for inconsistent processing

### Future improvement

The current pipeline could be generalized further using configuration-driven city selection and repeated execution across multiple markets.

Possible future work includes:

- Reusable city configuration
- Cross-city schema contracts
- Standardized common features
- City-level benchmark tables
- Cross-city visual comparisons
- Cross-city model evaluation

---

## 3. Cloud Deployment

### Status

**Not implemented.**

### Reason

The project was designed and validated for local execution on an 8 GB RAM Windows laptop.

Cloud deployment was not required for the core submission and would add infrastructure complexity without materially improving the fundamental quality of the completed engineering workflow.

### Future improvement

Possible deployment options include:

- AWS
- Microsoft Azure
- Google Cloud
- Managed container platforms
- Scheduled cloud execution
- Hosted Streamlit deployment

Any cloud deployment should preserve:

- Reproducibility
- Secure configuration
- Cost awareness
- Data-access controls
- Clear environment documentation

---

## 4. Workflow Orchestration

### Status

**Not implemented.**

### Reason

The project currently uses:

```bash
python run_pipeline.py --city amsterdam
```

to execute the complete seven-stage engineering workflow.

A separate orchestration framework such as Airflow, Prefect, or Dagster was not added because the project has a focused single-city scope and the current pipeline already provides ordered, reproducible stage execution.

### Future improvement

A production-oriented version could use orchestration for:

- Scheduling
- Retries
- Dependency management
- Monitoring
- Failure alerts
- Incremental execution
- Backfills
- Operational dashboards

---

## 5. Incremental Data Processing

### Status

**Not implemented.**

### Reason

The current pipeline performs full-batch processing of the selected Amsterdam datasets.

Incremental processing would require:

- Reliable source-update behavior
- Stable record identifiers
- Change-detection logic
- Watermark tracking
- Additional metadata management
- Upsert and merge rules
- Historical-state decisions

### Future improvement

Possible improvements include:

- Incremental ingestion
- Watermark tracking
- Change-data capture
- Partition-based updates
- Merge/upsert logic
- Historical snapshots
- Late-arriving-data handling

---

## 6. Dockerization

### Status

**Not implemented.**

### Reason

The project is currently reproducible through:

- Python virtual environment
- `requirements.txt`
- Modular source code
- A single pipeline entry point
- A separate machine-learning experiment entry point
- Automated tests
- GitHub Actions CI

Docker was not prioritized ahead of core engineering, analytical, testing, and documentation deliverables.

### Future improvement

A Docker image could improve:

- Portability
- Environment consistency
- Dependency isolation
- Deployment readiness
- Reproducibility across operating systems

---

## 7. Advanced Data-Quality Framework

### Status

**Not implemented.**

### Reason

The project already includes a custom validation framework with:

- `PASS`
- `WARNING`
- `FAIL`

It also includes a critical validation gate.

The current validation result is:

| Status | Count |
|---|---:|
| PASS | **83** |
| WARNING | **7** |
| FAIL | **0** |

External frameworks such as Great Expectations, Soda, or Deequ were not added because the current custom validation system already covers the most important source-quality checks for this assignment.

### Future improvement

A larger production system could integrate:

- Great Expectations
- Soda
- Data contracts
- Schema evolution checks
- Trend-based anomaly detection
- Data-quality observability
- Historical validation trends

---

## 8. Full Historical Snapshot Tracking

### Status

**Not implemented.**

### Reason

The project uses the available Amsterdam dataset snapshot and does not maintain a full historical slowly changing dimension model.

### Future improvement

A production version could support:

- Snapshot dates
- Historical listing changes
- Host changes
- Price changes
- Availability changes
- Slowly changing dimensions
- Point-in-time analytical views

---

## 9. Real Occupancy and Revenue Calculation

### Status

**Not implemented because the required source data is unavailable.**

### Reason

The source data does not provide verified reservation or transaction records.

Therefore, the project does not claim to calculate:

- True occupancy
- Confirmed booked nights
- Actual host revenue
- Verified reservation volume
- Confirmed transaction prices
- Verified profitability

Calendar unavailability is treated only as:

```text
unavailability_rate_proxy
```

and is not interpreted as true occupancy.

### Future improvement

Accurate occupancy or revenue analysis would require trusted reservation and transaction data.

This is primarily a **data-availability limitation**, not an implementation failure.

---

## 10. Causal Analysis

### Status

**Not implemented.**

### Reason

The project uses observational Airbnb data.

Therefore, statistical and machine-learning analyses identify:

- Associations
- Differences
- Predictive patterns

but do not prove causation.

For example:

- Entire-home listings have higher prices than private rooms.
- Bedrooms and room type are important predictive features in the fitted Random Forest model.

These findings do not prove that changing a feature would causally produce the observed price change.

### Future improvement

Causal questions would require stronger study design, additional variables, experiments, quasi-experimental methods, or causal-inference techniques.

Possible approaches could include:

- Matching
- Difference-in-differences
- Instrumental variables
- Regression discontinuity
- Causal forests

Only where supported by suitable data and assumptions.

---

## 11. Additional Statistical Hypotheses

### Status

**Not prioritized.**

### Reason

The project completed two focused statistical hypotheses deeply rather than many shallow tests.

The selected analyses were:

1. Entire-home versus private-room pricing
2. Superhost versus non-superhost review-score performance

The emphasis was on:

- Proper null and alternative hypotheses
- Sample-size review
- Distribution assessment
- Appropriate test selection
- Statistical significance
- Effect size
- Practical significance
- Business interpretation
- Honest limitations

### Future improvement

Possible future tests include:

- Neighbourhood price differences
- Weekend versus weekday pricing
- High-review versus low-review listing performance
- Availability-proxy differences across room types
- Host-portfolio segment comparisons

Any additional testing should include multiple-comparison considerations where appropriate.

---

## 12. Advanced Geographic Visualization

### Status

**Not prioritized.**

### Reason

The project includes neighbourhood-level analysis but did not prioritize advanced interactive geospatial mapping.

### Future improvement

Possible additions include:

- Choropleth maps
- Listing-density maps
- Price heatmaps
- Interactive neighbourhood exploration
- Geospatial clustering
- Map-based dashboard filtering

This could later be integrated into the planned Streamlit dashboard.

---

## 13. Advanced Machine-Learning Evaluation

### Status

**Not implemented beyond the focused baseline experiment.**

### Completed scope

The current machine-learning experiment already includes:

- Dummy Regressor baseline
- Ridge Regression
- Random Forest Regressor
- MAE
- RMSE
- R²
- Explicit leakage prevention
- Reproducible train-test split
- Feature importance
- Actual-vs-predicted diagnostics

### Deferred scope

The following were intentionally not added:

- Extensive hyperparameter tuning
- Cross-validation
- Nested cross-validation
- Additional boosting models
- Model calibration
- SHAP analysis
- Permutation importance
- Model persistence and serving
- Production inference API
- Drift monitoring

### Reason

The goal was to add one focused, defensible experiment without turning a Data Engineering internship assignment into an oversized machine-learning project.

### Future improvement

Potential next steps include:

- K-fold cross-validation
- Randomized hyperparameter search
- Permutation importance
- Grouped feature importance
- SHAP explanations
- Cross-city external validation

---

## 14. Production Model Serving

### Status

**Not implemented.**

### Reason

The Random Forest model is used only for a focused analytical experiment.

It is not deployed as:

- An API
- A batch-scoring service
- A real-time pricing service
- A production recommendation engine

### Future improvement

A production-oriented version would require:

- Model serialization
- Versioning
- Reproducible preprocessing
- Inference validation
- API or batch interface
- Monitoring
- Drift detection
- Retraining policy
- Security controls

The current model should not be treated as a production pricing system.

---

## 15. Full Production Observability

### Status

**Not implemented.**

### Reason

The project includes logging, validation outputs, automated tests, and CI, but does not include a complete production observability stack.

### Future improvement

Possible additions include:

- Centralized logs
- Pipeline metrics
- Data-quality trends
- Runtime monitoring
- Failure alerts
- Model-performance monitoring
- Data-drift detection
- Dashboard-based operational health checks

---

## 16. Final Report Update

### Status

**Pending.**

### Reason

The final report must be updated to reflect recently completed work, including:

- GitHub Actions continuous integration
- Focused price-prediction experiment
- Model results
- Feature importance
- Actual-vs-predicted diagnostics
- Architecture diagram
- Final completion status

After the interactive dashboard is completed, the report should also include the dashboard in the appropriate section.

### Completion rule

The report should not be considered final until:

1. All completed features are accurately documented.
2. No completed feature is still described as deferred.
3. No incomplete feature is falsely described as completed.
4. Figures and tables are visually verified.
5. The PDF is professionally formatted and reviewed.

---

## 17. Submission Details File

### Status

**Pending.**

The repository should include:

```text
SUBMISSION_DETAILS.md
```

with:

- Candidate name
- GitHub username
- Degree programme
- Specialization
- Institution
- Current GPA
- Latest academic results
- Notice period
- Earliest available start date
- Onsite flexibility
- Repository information
- Submission date

Sensitive personal information should not be added unnecessarily to a public repository.

---

## Final Prioritization Rationale

The following principle guided the project:

> **Complete the core work deeply before adding optional breadth.**

The project prioritized:

1. Reliable data ingestion
2. Complete dataset familiarization
3. Automated profiling
4. Data-quality validation
5. Cleaning
6. Enrichment
7. Listing-grain preservation
8. DuckDB analytical modeling
9. SQL analysis
10. EDA
11. Statistical testing
12. Automated tests
13. Continuous integration
14. Focused machine-learning experimentation
15. Architecture documentation
16. Reproducibility
17. Professional documentation

The following areas remain deferred or planned:

- Interactive Streamlit dashboard — **planned next**
- Multiple cities
- Cloud deployment
- Workflow orchestration
- Incremental processing
- Dockerization
- Advanced external data-quality frameworks
- Historical snapshot tracking
- Verified occupancy and revenue analysis
- Causal analysis
- Additional statistical hypotheses
- Advanced geospatial analysis
- Advanced machine-learning evaluation
- Production model serving
- Full production observability
- Final report update
- Submission details file

This is a deliberate engineering trade-off rather than an accidental omission.

The goal is to deliver complete, validated, reproducible, and well-documented components rather than a larger number of unfinished features.

---

# Current Status Summary

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

⬜ Interactive Streamlit Dashboard
⬜ Final Report Update
⬜ SUBMISSION_DETAILS.md
⬜ Final Repository QA
⬜ Merge dev → main
⬜ Submit
```
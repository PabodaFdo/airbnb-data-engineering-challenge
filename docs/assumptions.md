# Assumptions and Analytical Caveats

> **Project:** Amsterdam Airbnb Data Engineering Challenge  
> **Scope:** Amsterdam, Netherlands  
> **Purpose:** Transparent documentation of assumptions, limitations, and interpretation rules.

## Purpose

This document records the key assumptions, interpretation rules, and analytical caveats used throughout the Amsterdam Airbnb Data Engineering Challenge.

The objective is to make all important data-handling decisions explicit and reproducible. These assumptions prevent unsupported interpretations, avoid silent data loss, and clarify where source-data limitations affect downstream engineering and analysis.

---

## 1. City Scope

This project focuses exclusively on:

**Amsterdam, Netherlands**

A one-city, depth-first approach was intentionally selected to prioritize:

- Data understanding.
- Pipeline reliability.
- Data-quality validation.
- Reproducibility.
- Analytical depth.
- Statistical rigor.
- Clear business interpretation.

No assumption is made that findings from Amsterdam automatically generalize to other Airbnb markets.

---

## 2. Canonical Listing Population

The summary listings dataset, `listings.csv`, is treated as the canonical source for the Amsterdam listing population.

Observed canonical listing count:

**10,465 listings**

The detailed listings dataset, `listings.csv.gz`, contains:

**10,369 listings**

Therefore:

**96 listings exist in the canonical summary source but are absent from the detailed listings source.**

The enrichment process preserves all 10,465 canonical listings rather than using an inner join that would silently remove the 96 summary-only records.

### Implication

Some canonical listings may have limited detailed attributes because matching records are unavailable in the detailed listings source.

These missing detailed attributes are preserved as null rather than being fabricated.

---

## 3. One Row per Listing

The final enriched listing master dataset is designed at the following grain:

**One row per canonical listing**

The expected final row count is:

**10,465 rows**

Listing IDs must remain:

- Non-null.
- Unique.

The pipeline validates this requirement after cleaning and enrichment.

Any accidental row multiplication caused by review, calendar, or other one-to-many joins is considered a data-engineering failure.

For this reason, detailed review and calendar datasets are aggregated to listing level before being joined to the enriched master dataset.

---

## 4. Missing Host IDs

The summary listings dataset contains:

**96 listings with missing `host_id` values**

A missing host ID does not automatically invalidate the listing itself.

Therefore:

- Listings with missing host IDs are preserved.
- They may be excluded only from analyses that specifically require a valid host identifier.
- Missing host IDs limit host-level enrichment and portfolio analysis coverage.
- No artificial host identifier is created.

No assumption is made that the 96 missing-host-ID records are necessarily identical to the 96 summary-only listings unless separately verified through listing-level comparison.

---

## 5. Missing Price Values

Price missingness is substantial in both listing sources.

Observed missing values:

- Summary listings: **3,994 of 10,465 listings**
- Detailed listings: **3,992 of 10,369 listings**

A missing price is not interpreted as a zero price.

Therefore:

- Missing prices remain null.
- Zero-value imputation is not performed.
- Listings with missing prices are preserved in the canonical population.
- Price-based analyses use only listings with valid price observations.

Where available, the enrichment process creates a best-available price using legitimate source values.

The source priority is:

1. Use the summary listing price when available.
2. Otherwise use the detailed listing price when available.
3. Otherwise preserve the final price as null.

No price value is fabricated.

---

## 6. Raw Data Preservation

Raw source files are treated as immutable inputs.

The pipeline does not overwrite or modify the original raw datasets.

Cleaned, aggregated, and enriched outputs are written separately under processed-data and output directories.

This separation supports:

- Traceability.
- Reproducibility.
- Debugging.
- Comparison between raw and processed data.

---

## 7. Price Cleaning

Currency-formatted price values are converted to numeric representations for analysis.

For example:

```text
"$1,250.00" → 1250.00
```

The original price representation is preserved where appropriate so that transformations remain traceable.

Invalid or missing price values are not automatically converted to zero.

## 8. Calendar Availability Is Not True Occupancy

The Airbnb calendar dataset indicates whether a date is marked as available or unavailable.

An unavailable date does not necessarily prove that the property was booked.

A date may be unavailable because of:

- A confirmed booking
- Host blocking
- Maintenance
- Personal use
- Regulatory restrictions
- Calendar-management decisions
- Other unknown causes

Therefore, the derived field:

```text
unavailability_rate_proxy
```

is explicitly treated only as an availability-based proxy.

It must not be described as:

- True occupancy
- Verified booked nights
- Confirmed demand
- Actual reservation rate

No actual occupancy claim is made from calendar availability alone.

## 9. Review Counts Are Not Booking Counts

The review datasets contain review events, not complete reservation records.

Not every guest necessarily leaves a review.

Therefore:

- Review count is not treated as actual booking count.
- Review frequency is not treated as verified booking frequency.
- High review activity may suggest stronger guest activity, but it remains an imperfect proxy.

No revenue or booking conclusions are derived solely from review counts.

## 10. Repeated Review Dates Are Not Automatically Duplicates

The summary reviews dataset contains repeated:

```text
(listing_id, date)
```

combinations.

Observed repeated-row count:

22,541 rows

This does not automatically mean the records are erroneous duplicates.

Multiple individual reviews can legitimately occur for the same listing on the same date.

Because the summary review dataset contains only listing ID and review date, separate legitimate review events may appear identical at this reduced grain.

Therefore:

- Repeated `(listing_id, date)` rows are not blindly deleted.
- The detailed reviews dataset is used when individual review-event identity is required.
- Only true duplicate review-event identifiers should be treated as duplicate events.
## 11. Missing Reviewer Names

The detailed reviews dataset contains:

1 missing reviewer name among 545,162 review events

Reviewer name is treated as non-critical descriptive metadata.

A missing reviewer name does not invalidate the review event when the review itself remains otherwise structurally valid.

Therefore, the review event is preserved.

## 12. Empty neighbourhood_group Field

The Amsterdam neighbourhood metadata contains:

22 of 22 missing values for neighbourhood_group

The field is therefore considered unavailable for meaningful analysis in this dataset.

The project does not:

- Fabricate neighbourhood groups
- Replace missing values with invented classifications
- Use the empty field for analytical conclusions

Neighbourhood-level analysis instead uses the available neighbourhood identifiers and names.

## 13. Geographic Validation

Latitude and longitude fields are treated as geographic coordinates and validated against valid geographic ranges.

The project assumes that syntactically valid coordinates are suitable for listing-level geographic analysis unless additional city-boundary validation demonstrates otherwise.

A valid coordinate does not independently guarantee perfect physical-location accuracy because source data may contain rounding, privacy adjustments, or scraping inconsistencies.

## 14. Summary and Detailed Source Differences

Summary and detailed Airbnb files are treated as related but distinct source extracts.

Differences in:

- Row counts
- Missingness
- Attribute coverage
- Listing coverage

are not automatically treated as pipeline errors.

The pipeline preserves these differences and documents them rather than forcing artificial equality between source files.

## 15. Missing Values Are Handled Contextually

The project does not apply a universal rule such as:

```python
df.fillna(0)
```

to all missing values.

Missing values are handled based on business meaning and source context.

Examples:

Missing price → preserve as null.
Missing review score → preserve as null; do not interpret as zero.
Missing host ID → preserve listing but limit host-level analysis.
Missing review activity after a valid left join may be represented as zero only when the absence of matching review events supports that interpretation.
Completely unavailable source fields are documented rather than artificially populated.
## 16. Host Portfolio Segmentation

Host portfolio segments are derived from the available host listing-count information.

The categories used are:

Single-listing host.
Small multi-listing host (2–5 listings).
Large/professional host (6+ listings).

These categories are analytical segments created for this project.

The term large/professional host is a descriptive analytical label based on listing count and does not independently prove that a host operates as a legally registered business or professional company.

## 17. Statistical Significance Does Not Equal Practical Importance

Statistical hypothesis tests are interpreted using:

- Test statistic
- P-value
- Effect size
- Sample size
- Distribution characteristics
- Business context

A statistically significant result is not automatically considered practically important.

Effect sizes and observed group differences are considered before making business interpretations.

## 18. Statistical Results Do Not Prove Causation

The analyses use observational Airbnb data.

Therefore, statistical associations or group differences do not establish causal relationships.

For example, a difference between superhost and non-superhost review scores does not independently prove that superhost status caused the difference.

Other factors may contribute, including:

- Property type
- Location
- Price
- Host experience
- Listing quality
- Guest expectations
- Review-selection behavior

All statistical findings are interpreted as associations or observed differences unless causal evidence exists.

## 19. Neighbourhood Comparisons Require Adequate Sample Size

Neighbourhood rankings can become misleading when based on very small numbers of listings.

Therefore, minimum listing-count thresholds may be applied to neighbourhood comparisons.

Any threshold used must be explicitly stated in the relevant SQL query, chart, notebook, or report section.

A neighbourhood with very few listings should not automatically be presented as the city's highest-priced or best-performing market.

## 20. Outliers Are Not Automatically Removed

Extreme prices, availability values, review counts, or other unusual observations are first treated as potential genuine source observations.

Outliers are not removed solely because they are statistically extreme.

When exclusion is required for a particular visualization or statistical method:

- The rule must be stated.
- The original data must remain preserved.
- The analytical reason must be documented.

For example, a price distribution may be visualized both with and without extreme upper outliers to improve interpretability without deleting those records from the source or processed datasets.

## 21. 8 GB RAM Constraint

The project is intentionally designed to run on an 8 GB RAM Windows laptop.

The following processing strategy is therefore assumed:

- Pandas for small and medium datasets
- DuckDB for larger calendar and detailed review datasets
- One large processing stage at a time
- Listing-level aggregation before joins
- Parquet for efficient processed outputs
- Compact analytical extracts for visualization
- Memory cleanup between major stages where appropriate

This hardware constraint is treated as an engineering design consideration rather than a reason to reduce data-quality standards.

## 22. Warehouse Grain and Reconciliation

The DuckDB analytical warehouse preserves the canonical listing grain of:

**10,465 listings**

The warehouse also reconciles:

- **545,162 review events**
- **3,819,725 calendar rows**

Warehouse validation is used to verify row-level reconciliation and structural integrity.

The analytical warehouse is designed for analysis and reporting rather than transactional workloads.

## 23. Validation Warnings Do Not Automatically Block Processing

The automated validation stage produced:

| Status | Count |
|---|---:|
| PASS | 83 |
| WARNING | 7 |
| FAIL | 0 |

Warnings represent source-data limitations, coverage differences, or conditions requiring interpretation.

A warning is allowed to continue through the pipeline when:

- The issue does not invalidate the record.
- The limitation is understood.
- The affected data is preserved appropriately.
- The condition is documented.

Critical FAIL results would block downstream processing through the validation gate.

## 24. Business Recommendations Must Be Evidence-Based

Business recommendations are derived only from actual:

- EDA findings
- SQL analysis
- Statistical results
- Validated source data

Recommendations are not created before examining the underlying analytical results.

The project avoids presenting unsupported assumptions as established facts.

## 25. No Cross-City Generalization

Because the project analyzes Amsterdam only:

Results should be interpreted within the Amsterdam market context.
No direct assumptions are made about pricing, host behavior, availability, review activity, or neighbourhood patterns in other cities.
Multi-city comparison is considered a future extension rather than an implicit feature of the current analysis.
## 26. No Machine Learning Assumption

No machine-learning model is required for the core analytical conclusions in this project.

The project prioritizes:

- Data engineering
- Data quality
- Reproducibility
- SQL analytics
- EDA
- Statistical testing
- Business interpretation

Any future predictive model would require additional feature validation, evaluation design, leakage checks, and appropriate performance metrics.

# Summary

The central principles used throughout this project are:

1. Preserve the full canonical listing population whenever possible.
2. Never fabricate missing values without evidence.
3. Never interpret missing price as zero.
4. Never describe calendar unavailability as verified occupancy.
5. Never treat reviews as complete booking records.
6. Never blindly delete repeated rows without understanding dataset grain.
7. Aggregate one-to-many datasets before joining to the listing master.
8. Preserve raw source data unchanged.
9. Treat statistical significance and practical importance separately.
10. Avoid causal claims from observational data.
11. Document source limitations transparently.
Prefer reproducible and defensible engineering decisions over artificial completeness.
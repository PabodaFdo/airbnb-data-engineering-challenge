-- ============================================================================
-- Amsterdam Airbnb Data Engineering Challenge
-- Analytical SQL Queries
--
-- Analytical engine: DuckDB
-- Primary database: data/warehouse/airbnb_analytics.duckdb
--
-- Purpose:
-- Answer meaningful business questions using the analytical warehouse created
-- by src/build_warehouse.py.
--
-- Important caveats:
-- 1. Calendar unavailability is treated only as an availability-based proxy.
--    It must not be interpreted as verified occupancy.
-- 2. Review activity is not equivalent to booking activity because not every
--    guest leaves a review.
-- 3. Price calculations exclude listings without a usable price.
-- ============================================================================


-- ============================================================================
-- Query 1: Pricing and performance by room type
-- Business question:
-- Which accommodation segments command the highest typical prices, and how do
-- their review activity and availability-based patterns differ?
-- ============================================================================

SELECT
    room_type,
    listing_count,
    listings_with_price,
    avg_price,
    median_price,
    avg_review_score,
    total_review_events,
    avg_unavailability_rate_proxy
FROM vw_room_type_performance
ORDER BY median_price DESC NULLS LAST;


-- ============================================================================
-- Query 2: Neighbourhood pricing and market activity
-- Business question:
-- Which neighbourhoods combine meaningful listing supply with relatively high
-- typical prices and review activity?
--
-- Minimum listing threshold:
-- Neighbourhoods with at least 100 listings are retained to avoid highlighting
-- extremely small markets based on unstable sample sizes.
-- ============================================================================

SELECT
    neighbourhood,
    listing_count,
    listings_with_price,
    avg_price,
    median_price,
    avg_review_score,
    total_review_events,
    avg_reviews_per_listing,
    avg_availability_rate,
    avg_unavailability_rate_proxy
FROM vw_neighbourhood_performance
WHERE listing_count >= 100
ORDER BY median_price DESC NULLS LAST;


-- ============================================================================
-- Query 3: Host portfolio concentration and performance
-- Business question:
-- How do single-listing, small multi-listing, and large/professional hosts
-- differ in listing supply, typical price, review score, and review activity?
-- ============================================================================

SELECT
    host_portfolio_segment,
    listing_count,
    listings_with_price,
    avg_price,
    median_price,
    avg_review_score,
    avg_reviews_per_listing,
    avg_unavailability_rate_proxy,
    ROUND(
        100.0 * listing_count
        / SUM(listing_count) OVER (),
        2
    ) AS market_supply_percentage
FROM vw_host_portfolio_performance
ORDER BY listing_count DESC;


-- ============================================================================
-- Query 4: Superhost versus non-superhost performance
-- Business question:
-- Do superhost listings show meaningful differences in price, review scores,
-- review activity, and availability-based proxy metrics?
--
-- Null superhost values are excluded because their status is unknown.
-- ============================================================================

SELECT
    CASE
        WHEN host_is_superhost = TRUE THEN 'Superhost'
        WHEN host_is_superhost = FALSE THEN 'Non-superhost'
    END AS superhost_status,

    COUNT(*) AS listing_count,

    COUNT(price_best_available) AS listings_with_price,

    ROUND(
        AVG(price_best_available),
        2
    ) AS average_price,

    ROUND(
        MEDIAN(price_best_available),
        2
    ) AS median_price,

    COUNT(review_scores_rating) AS listings_with_review_score,

    ROUND(
        AVG(review_scores_rating),
        3
    ) AS average_review_score,

    SUM(detailed_review_count) AS total_review_events,

    ROUND(
        AVG(detailed_review_count),
        2
    ) AS average_reviews_per_listing,

    ROUND(
        AVG(unavailability_rate_proxy),
        4
    ) AS average_unavailability_rate_proxy

FROM enriched_listing_master

WHERE host_is_superhost IS NOT NULL

GROUP BY host_is_superhost

ORDER BY host_is_superhost DESC;


-- ============================================================================
-- Query 5: Neighbourhood review activity
-- Business question:
-- Which neighbourhoods generate the strongest review activity while having a
-- sufficiently large listing population?
--
-- Reminder:
-- Review count is only a proxy for guest activity and is not verified booking
-- volume.
-- ============================================================================

SELECT
    neighbourhood,
    listing_count,
    total_review_events,
    avg_reviews_per_listing,
    median_price,
    avg_review_score
FROM vw_neighbourhood_performance
WHERE listing_count >= 100
ORDER BY total_review_events DESC;


-- ============================================================================
-- Query 6: Listings with high review activity but relatively low ratings
-- Business question:
-- Which frequently reviewed listings may warrant quality investigation because
-- their review scores are relatively low despite substantial review history?
--
-- Thresholds used:
-- At least 50 detailed review events.
-- Review score below 4.5.
--
-- These are analytical screening rules, not universal quality standards.
-- ============================================================================

SELECT
    id AS listing_id,
    name,
    neighbourhood,
    room_type,
    price_best_available,
    review_scores_rating,
    detailed_review_count,
    review_events_per_active_year,
    host_is_superhost,
    host_portfolio_segment
FROM enriched_listing_master
WHERE detailed_review_count >= 50
  AND review_scores_rating < 4.5
ORDER BY
    detailed_review_count DESC,
    review_scores_rating ASC;


-- ============================================================================
-- Query 7: Availability-based proxy patterns by neighbourhood
-- Business question:
-- Which established neighbourhood markets show relatively high or low
-- availability-based unavailability proxy values?
--
-- Important:
-- unavailability_rate_proxy is not true occupancy. Dates may be unavailable
-- because of bookings, host blocking, maintenance, regulation, or other causes.
-- ============================================================================

SELECT
    neighbourhood,
    listing_count,
    avg_availability_rate,
    avg_unavailability_rate_proxy,
    median_price,
    total_review_events
FROM vw_neighbourhood_performance
WHERE listing_count >= 100
ORDER BY avg_unavailability_rate_proxy DESC NULLS LAST;


-- ============================================================================
-- Query 8: Price distribution summary by accommodation capacity
-- Business question:
-- How does typical price change as listing accommodation capacity increases?
--
-- Only capacities represented by at least 30 priced listings are included.
-- ============================================================================

SELECT
    accommodates,
    COUNT(*) AS listing_count,
    COUNT(price_best_available) AS listings_with_price,

    ROUND(
        AVG(price_best_available),
        2
    ) AS average_price,

    ROUND(
        MEDIAN(price_best_available),
        2
    ) AS median_price,

    ROUND(
        QUANTILE_CONT(price_best_available, 0.25),
        2
    ) AS price_q1,

    ROUND(
        QUANTILE_CONT(price_best_available, 0.75),
        2
    ) AS price_q3

FROM enriched_listing_master

WHERE accommodates IS NOT NULL
  AND accommodates > 0
  AND price_best_available IS NOT NULL

GROUP BY accommodates

HAVING COUNT(price_best_available) >= 30

ORDER BY accommodates;
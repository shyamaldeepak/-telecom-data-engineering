-- Telecom 360° Analytical Query: Revenue, Billing & ARPU Analytics
-- Computes financial performance, collection efficiency, and ARPU metrics.

SELECT
    calculated_at,
    total_revenue,
    collected_revenue,
    unique_billed_customers,
    arpu AS average_revenue_per_user,
    collection_rate_pct,
    ROUND(total_revenue - collected_revenue, 2) AS outstanding_uncollected_revenue
FROM read_parquet('data/gold/revenue_summary.parquet');

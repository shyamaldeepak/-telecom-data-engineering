-- Telecom 360° Analytical Query: Customer 360 & Behavioral Profile
-- Combines demographic information, active subscription, monthly spend,
-- data usage, call volumes, quality exposure, and churn risk tier.

SELECT
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.city,
    c.country,
    c.customer_status,
    c.plan_name,
    c.contract_type,
    c.monthly_price,
    c.total_data_gb,
    c.total_calls,
    c.dropped_calls,
    ROUND(CAST(c.dropped_calls AS DOUBLE) / NULLIF(c.total_calls, 0), 3) AS dropped_call_rate,
    c.invoices_count,
    c.lifetime_billed,
    c.failed_payments,
    p.churn_probability,
    p.risk_tier AS churn_risk_tier
FROM read_parquet('data/gold/customer_360.parquet') c
LEFT JOIN read_parquet('data/gold/customer_churn_predictions.parquet') p
    ON c.customer_id = p.customer_id
ORDER BY p.churn_probability DESC NULLS LAST;

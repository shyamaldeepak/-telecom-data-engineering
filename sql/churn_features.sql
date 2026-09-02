-- Telecom 360° Analytical Query: Churn Feature Store Distribution
-- Summarizes behavioral feature distributions segmented by contract type.

SELECT
    contract_type,
    COUNT(*) AS total_subscribers,
    ROUND(AVG(tenure_days), 1) AS avg_tenure_days,
    ROUND(AVG(monthly_price), 2) AS avg_monthly_price,
    ROUND(AVG(total_data_gb), 2) AS avg_data_gb,
    ROUND(AVG(dropped_call_ratio) * 100, 2) AS avg_dropped_call_pct,
    ROUND(AVG(failed_payments), 2) AS avg_failed_payments,
    ROUND(AVG(churn_label) * 100, 1) AS actual_churn_rate_pct
FROM read_parquet('data/gold/churn_features.parquet')
GROUP BY contract_type
ORDER BY actual_churn_rate_pct DESC;

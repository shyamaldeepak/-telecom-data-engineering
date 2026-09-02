-- Telecom 360° Analytical Query: Network Health & Incident Analysis
-- Aggregates cell tower performance KPIs by region and technology,
-- identifies towers breaching SLA thresholds, and counts critical incidents.

WITH tower_summary AS (
    SELECT
        cell_id,
        region,
        technology,
        avg_download_speed,
        avg_upload_speed,
        avg_latency_ms,
        avg_packet_loss,
        avg_availability,
        peak_users,
        health_score
    FROM read_parquet('data/gold/network_health.parquet')
),
incident_summary AS (
    SELECT
        cell_id,
        COUNT(*) AS total_incidents,
        SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_incidents,
        SUM(affected_users_estimate) AS total_affected_users
    FROM read_parquet('data/gold/network_incidents.parquet')
    GROUP BY cell_id
)
SELECT
    t.cell_id,
    t.region,
    t.technology,
    t.avg_download_speed,
    t.avg_latency_ms,
    t.avg_packet_loss,
    t.avg_availability,
    t.health_score,
    COALESCE(i.total_incidents, 0) AS incident_count,
    COALESCE(i.critical_incidents, 0) AS critical_incidents,
    COALESCE(i.total_affected_users, 0) AS affected_users
FROM tower_summary t
LEFT JOIN incident_summary i
    ON t.cell_id = i.cell_id
ORDER BY t.health_score ASC, incident_count DESC;

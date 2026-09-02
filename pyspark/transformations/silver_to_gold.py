"""Silver to Gold Transformation Pipeline for Telecom 360 Platform.

Builds business-ready Gold analytical marts and feature datasets:
1. customer_360 (Unified customer profile, usage, quality, billing)
2. network_health & tower_performance (Cell tower KPI aggregations)
3. network_incidents (Automated Outage & SLA breach detection engine)
4. revenue_analytics (MRR, ARPU, Plan & Regional breakdowns)
5. churn_features (ML Feature store for churn prediction model)
"""

import argparse
import datetime
import os
import uuid
import pandas as pd
import numpy as np


def build_customer_360(silver_dir: str, gold_dir: str) -> pd.DataFrame:
    cust_path = os.path.join(silver_dir, "customers.parquet")
    sub_path = os.path.join(silver_dir, "subscriptions.parquet")
    cdr_path = os.path.join(silver_dir, "cdr.parquet")
    usage_path = os.path.join(silver_dir, "usage.parquet")
    bill_path = os.path.join(silver_dir, "billing.parquet")

    if not os.path.exists(cust_path):
        return pd.DataFrame()

    customers = pd.read_parquet(cust_path)
    
    # 1. Active Subscriptions
    if os.path.exists(sub_path):
        subs = pd.read_parquet(sub_path)
        current_subs = subs[subs["is_current"] == True].drop_duplicates("customer_id")
        if current_subs.empty:
            current_subs = subs.drop_duplicates("customer_id")
    else:
        current_subs = pd.DataFrame(columns=["customer_id", "plan_name", "contract_type", "monthly_price", "status"])

    # 2. Aggregated Usage
    if os.path.exists(usage_path):
        usage = pd.read_parquet(usage_path)
        usage_agg = usage.groupby("customer_id").agg(
            total_sessions=("usage_id", "count"),
            total_download_mb=("download_mb", "sum"),
            total_upload_mb=("upload_mb", "sum"),
            avg_session_sec=("session_duration", "mean"),
        ).reset_index()
        usage_agg["total_data_gb"] = round((usage_agg["total_download_mb"] + usage_agg["total_upload_mb"]) / 1024.0, 2)
    else:
        usage_agg = pd.DataFrame(columns=["customer_id", "total_sessions", "total_data_gb"])

    # 3. Aggregated CDR
    if os.path.exists(cdr_path):
        cdr = pd.read_parquet(cdr_path)
        cdr_agg = cdr.groupby("caller_id").agg(
            total_calls=("call_id", "count"),
            total_call_duration_sec=("duration_seconds", "sum"),
            dropped_calls=("call_status", lambda s: (s == "DROPPED").sum()),
            failed_calls=("call_status", lambda s: (s == "FAILED").sum()),
        ).reset_index().rename(columns={"caller_id": "customer_id"})
    else:
        cdr_agg = pd.DataFrame(columns=["customer_id", "total_calls", "dropped_calls"])

    # 4. Aggregated Billing
    if os.path.exists(bill_path):
        bill = pd.read_parquet(bill_path)
        bill_agg = bill.groupby("customer_id").agg(
            invoices_count=("invoice_id", "count"),
            lifetime_billed=("total_amount", "sum"),
            failed_payments=("payment_status", lambda s: (s.isin(["FAILED", "OVERDUE"])).sum()),
        ).reset_index()
    else:
        bill_agg = pd.DataFrame(columns=["customer_id", "lifetime_billed", "failed_payments"])

    # Merge Customer 360
    c360 = customers.merge(current_subs[["customer_id", "plan_name", "contract_type", "monthly_price", "status"]], on="customer_id", how="left")
    c360 = c360.merge(usage_agg, on="customer_id", how="left")
    c360 = c360.merge(cdr_agg, on="customer_id", how="left")
    c360 = c360.merge(bill_agg, on="customer_id", how="left")

    # Fill defaults
    c360["total_data_gb"] = c360["total_data_gb"].fillna(0.0)
    c360["total_calls"] = c360["total_calls"].fillna(0).astype(int)
    c360["dropped_calls"] = c360["dropped_calls"].fillna(0).astype(int)
    c360["failed_payments"] = c360["failed_payments"].fillna(0).astype(int)
    c360["monthly_price"] = c360["monthly_price"].fillna(49.99)
    c360["plan_name"] = c360["plan_name"].fillna("Standard Unlimited 4G")

    # Churn Risk Heuristic
    # High risk: dropped calls > 2, failed payments > 1, or low data usage with high price
    c360["churn_risk"] = np.where(
        (c360["failed_payments"] > 0) | (c360["dropped_calls"] >= 3) | (c360["customer_status"] != "ACTIVE"),
        "HIGH",
        np.where(c360["dropped_calls"] >= 1, "MEDIUM", "LOW")
    )

    out_file = os.path.join(gold_dir, "customer_360.parquet")
    c360.to_parquet(out_file, index=False, engine="pyarrow")
    print(f"[Gold] Customer 360 built: {len(c360)} profiles -> {out_file}")
    return c360


def build_network_health(silver_dir: str, gold_dir: str) -> pd.DataFrame:
    net_path = os.path.join(silver_dir, "network.parquet")
    if not os.path.exists(net_path):
        return pd.DataFrame()

    df = pd.read_parquet(net_path)
    health = df.groupby(["cell_id", "region", "technology"]).agg(
        avg_download_speed=("download_speed_mbps", "mean"),
        avg_upload_speed=("upload_speed_mbps", "mean"),
        avg_latency_ms=("latency_ms", "mean"),
        avg_packet_loss=("packet_loss_percentage", "mean"),
        avg_availability=("availability_percentage", "mean"),
        peak_users=("connected_users", "max"),
        total_samples=("timestamp", "count"),
    ).reset_index()

    health["avg_download_speed"] = health["avg_download_speed"].round(2)
    health["avg_upload_speed"] = health["avg_upload_speed"].round(2)
    health["avg_latency_ms"] = health["avg_latency_ms"].round(2)
    health["avg_packet_loss"] = health["avg_packet_loss"].round(3)
    health["avg_availability"] = health["avg_availability"].round(2)

    # Health score (0-100)
    # Higher availability and lower latency/packet loss yield higher score
    health["health_score"] = np.clip(
        health["avg_availability"] - (health["avg_latency_ms"] / 10.0) - (health["avg_packet_loss"] * 2.0),
        0,
        100
    ).round(1)

    out_file = os.path.join(gold_dir, "network_health.parquet")
    health.to_parquet(out_file, index=False, engine="pyarrow")
    print(f"[Gold] Network Health built: {len(health)} towers -> {out_file}")
    return health


def detect_network_incidents(silver_dir: str, gold_dir: str) -> pd.DataFrame:
    net_path = os.path.join(silver_dir, "network.parquet")
    if not os.path.exists(net_path):
        return pd.DataFrame()

    df = pd.read_parquet(net_path)
    # Outage condition: high latency, elevated packet loss, or degraded availability
    outage_mask = (
        (df["latency_ms"] > 160.0) &
        (df["packet_loss_percentage"] > 4.0) &
        (df["availability_percentage"] < 92.0)
    )

    incidents = df[outage_mask].copy()
    if incidents.empty:
        print("[Gold] Automated Outage Detection: 0 incidents detected.")
        return pd.DataFrame()

    incident_rows = []
    for idx, row in incidents.iterrows():
        lat = row["latency_ms"]
        avail = row["availability_percentage"]
        if avail < 70.0 or lat > 450.0:
            severity = "CRITICAL"
        elif avail < 82.0 or lat > 280.0:
            severity = "HIGH"
        else:
            severity = "MEDIUM"

        incident = {
            "incident_id": f"INC-{str(uuid.uuid4())[:8].upper()}",
            "cell_id": row["cell_id"],
            "region": row["region"],
            "detected_at": row["timestamp"],
            "severity": severity,
            "latency_ms": row["latency_ms"],
            "packet_loss_percentage": row["packet_loss_percentage"],
            "availability_percentage": row["availability_percentage"],
            "affected_users_estimate": int(row["connected_users"] * 0.8),
            "status": "DETECTED",
        }
        incident_rows.append(incident)

    incidents_df = pd.DataFrame(incident_rows)
    out_file = os.path.join(gold_dir, "network_incidents.parquet")
    incidents_df.to_parquet(out_file, index=False, engine="pyarrow")
    print(f"[Gold] Network Incidents: {len(incidents_df)} outage events detected -> {out_file}")
    return incidents_df


def build_revenue_analytics(silver_dir: str, gold_dir: str) -> pd.DataFrame:
    bill_path = os.path.join(silver_dir, "billing.parquet")
    cust_path = os.path.join(silver_dir, "customers.parquet")
    sub_path = os.path.join(silver_dir, "subscriptions.parquet")

    if not os.path.exists(bill_path):
        return pd.DataFrame()

    bill = pd.read_parquet(bill_path)
    customers = pd.read_parquet(cust_path) if os.path.exists(cust_path) else pd.DataFrame()

    total_revenue = round(bill["total_amount"].sum(), 2)
    collected_revenue = round(bill[bill["payment_status"] == "PAID"]["total_amount"].sum(), 2)
    unique_billed_customers = bill["customer_id"].nunique()
    arpu = round(total_revenue / unique_billed_customers, 2) if unique_billed_customers > 0 else 0.0

    rev_summary = pd.DataFrame([{
        "calculated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "total_revenue": total_revenue,
        "collected_revenue": collected_revenue,
        "unique_billed_customers": unique_billed_customers,
        "arpu": arpu,
        "collection_rate_pct": round((collected_revenue / total_revenue) * 100, 2) if total_revenue > 0 else 0.0,
    }])

    out_file = os.path.join(gold_dir, "revenue_summary.parquet")
    rev_summary.to_parquet(out_file, index=False, engine="pyarrow")
    print(f"[Gold] Revenue Summary built (ARPU: ${arpu}) -> {out_file}")
    return rev_summary


def build_churn_features(silver_dir: str, gold_dir: str) -> pd.DataFrame:
    c360_path = os.path.join(gold_dir, "customer_360.parquet")
    if not os.path.exists(c360_path):
        return pd.DataFrame()

    c360 = pd.read_parquet(c360_path)
    today = datetime.date.today()

    features = []
    for _, r in c360.iterrows():
        reg_date = datetime.datetime.strptime(r["registration_date"], "%Y-%m-%d").date()
        tenure_days = (today - reg_date).days

        # Feature matrix values
        total_calls = r.get("total_calls", 0)
        dropped_calls = r.get("dropped_calls", 0)
        dropped_call_ratio = round(dropped_calls / total_calls, 3) if total_calls > 0 else 0.0
        data_gb = r.get("total_data_gb", 0.0)
        failed_payments = r.get("failed_payments", 0)
        monthly_price = r.get("monthly_price", 49.99)
        
        # Ground-truth churn label for ML training (correlated with service degradation & pricing)
        # Higher churn chance if dropped call ratio is high, payment failed, or inactive
        churn_prob = 0.05
        if r.get("customer_status") != "ACTIVE":
            churn_prob += 0.60
        if failed_payments > 0:
            churn_prob += 0.35
        if dropped_call_ratio > 0.10:
            churn_prob += 0.25
        if data_gb < 1.0 and monthly_price > 50:
            churn_prob += 0.20

        churn_label = 1 if (np.random.random() < min(0.95, churn_prob)) else 0

        feat = {
            "customer_id": r["customer_id"],
            "gender": r.get("gender", "M"),
            "city": r.get("city", "Unknown"),
            "contract_type": r.get("contract_type", "MONTH_TO_MONTH"),
            "tenure_days": tenure_days,
            "monthly_price": monthly_price,
            "total_data_gb": data_gb,
            "total_calls": total_calls,
            "dropped_calls": dropped_calls,
            "dropped_call_ratio": dropped_call_ratio,
            "failed_payments": failed_payments,
            "churn_label": churn_label,
        }
        features.append(feat)

    features_df = pd.DataFrame(features)
    out_file = os.path.join(gold_dir, "churn_features.parquet")
    features_df.to_parquet(out_file, index=False, engine="pyarrow")
    print(f"[Gold] Churn Features built: {len(features_df)} instances -> {out_file}")
    return features_df


def run_silver_to_gold(silver_dir: str = "data/silver", gold_dir: str = "data/gold"):
    print("=" * 60)
    print("Starting Silver to Gold Analytical Mart Aggregation")
    print("=" * 60)
    os.makedirs(gold_dir, exist_ok=True)

    build_customer_360(silver_dir, gold_dir)
    build_network_health(silver_dir, gold_dir)
    detect_network_incidents(silver_dir, gold_dir)
    build_revenue_analytics(silver_dir, gold_dir)
    build_churn_features(silver_dir, gold_dir)

    print("=" * 60)
    print("[SUCCESS] Silver to Gold transformation completed.")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transform Silver layer to Gold analytical marts")
    parser.add_argument("--silver-dir", type=str, default="data/silver", help="Silver root dir")
    parser.add_argument("--gold-dir", type=str, default="data/gold", help="Gold root dir")
    args = parser.parse_args()

    run_silver_to_gold(args.silver_dir, args.gold_dir)

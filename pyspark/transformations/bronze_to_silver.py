"""Bronze to Silver Pipeline for Telecom 360 Platform.

Performs:
1. Schema validation & business rule verification.
2. Quarantine routing for non-compliant records.
3. Deduplication on natural primary keys.
4. Timestamp standardization & type casting.
5. SCD Type 2 dimension processing for customer subscriptions.
"""

import argparse
import datetime
import os
import sys
from typing import List, Dict, Any, Tuple
import pandas as pd

# Local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pyspark.quality.rules import (
    validate_customer_record,
    validate_cdr_record,
    validate_network_record,
    validate_usage_record,
    validate_billing_record,
)


def load_bronze_table(bronze_dir: str, table_name: str) -> pd.DataFrame:
    tbl_path = os.path.join(bronze_dir, table_name)
    if not os.path.exists(tbl_path):
        return pd.DataFrame()
    dfs = []
    for root, _, files in os.walk(tbl_path):
        for f in files:
            if f.endswith(".parquet"):
                dfs.append(pd.read_parquet(os.path.join(root, f)))
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)


def route_quarantine(
    df: pd.DataFrame,
    validator_func,
    table_name: str,
    quarantine_dir: str = "data/quarantine"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    valid_rows = []
    quarantined_rows = []

    for _, row in df.iterrows():
        rec = row.to_dict()
        is_valid, errors = validator_func(rec)
        if is_valid:
            valid_rows.append(rec)
        else:
            rec["_quarantine_reason"] = "; ".join(errors)
            rec["_quarantined_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            quarantined_rows.append(rec)

    valid_df = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame(columns=df.columns)
    quarantine_df = pd.DataFrame(quarantined_rows) if quarantined_rows else pd.DataFrame()

    if not quarantine_df.empty:
        q_dir = os.path.join(quarantine_dir, table_name)
        os.makedirs(q_dir, exist_ok=True)
        q_file = os.path.join(q_dir, f"{table_name}_quarantined_{int(datetime.datetime.now().timestamp())}.parquet")
        quarantine_df.to_parquet(q_file, index=False, engine="pyarrow")
        print(f"[Silver Pipeline] Diverted {len(quarantine_df)} invalid records to quarantine: {q_file}")

    return valid_df, quarantine_df


def process_scd2_subscriptions(df: pd.DataFrame) -> pd.DataFrame:
    """Implement Slowly Changing Dimensions (SCD Type 2) on subscription history."""
    if df.empty:
        return df

    # Sort chronologically by customer and start date
    df = df.sort_values(by=["customer_id", "start_date"]).reset_index(drop=True)
    scd_rows = []

    for cust_id, group in df.groupby("customer_id"):
        group_records = group.to_dict("records")
        num_records = len(group_records)
        for idx, rec in enumerate(group_records):
            is_last = (idx == num_records - 1)
            rec["valid_from"] = rec["start_date"]
            if is_last and rec["status"] == "ACTIVE":
                rec["valid_to"] = None
                rec["is_current"] = True
            else:
                next_start = group_records[idx + 1]["start_date"] if idx + 1 < num_records else rec.get("end_date")
                rec["valid_to"] = next_start or rec.get("end_date") or rec["start_date"]
                rec["is_current"] = False
            scd_rows.append(rec)

    return pd.DataFrame(scd_rows)


def run_bronze_to_silver(
    bronze_dir: str = "data/bronze",
    silver_dir: str = "data/silver",
    quarantine_dir: str = "data/quarantine"
):
    print("=" * 60)
    print("Starting Bronze to Silver Medallion Transformation")
    print("=" * 60)
    os.makedirs(silver_dir, exist_ok=True)

    # 1. Customers
    cust_df = load_bronze_table(bronze_dir, "customers")
    if not cust_df.empty:
        valid_cust, _ = route_quarantine(cust_df, validate_customer_record, "customers", quarantine_dir)
        valid_cust = valid_cust.sort_values("_ingested_at").drop_duplicates(subset=["customer_id"], keep="last")
        valid_cust.to_parquet(os.path.join(silver_dir, "customers.parquet"), index=False, engine="pyarrow")
        print(f"[Silver] Cleaned customers: {len(valid_cust)} records")

    # 2. Subscriptions (with SCD Type 2)
    sub_df = load_bronze_table(bronze_dir, "subscriptions")
    if not sub_df.empty:
        sub_df = sub_df.drop_duplicates(subset=["subscription_id"], keep="last")
        scd2_sub = process_scd2_subscriptions(sub_df)
        scd2_sub.to_parquet(os.path.join(silver_dir, "subscriptions.parquet"), index=False, engine="pyarrow")
        print(f"[Silver] Cleaned subscriptions with SCD2: {len(scd2_sub)} records")

    # 3. CDR
    cdr_df = load_bronze_table(bronze_dir, "cdr")
    if not cdr_df.empty:
        valid_cdr, _ = route_quarantine(cdr_df, validate_cdr_record, "cdr", quarantine_dir)
        valid_cdr = valid_cdr.drop_duplicates(subset=["call_id"], keep="last")
        valid_cdr["duration_seconds"] = pd.to_numeric(valid_cdr["duration_seconds"], errors="coerce").fillna(0).astype(int)
        valid_cdr.to_parquet(os.path.join(silver_dir, "cdr.parquet"), index=False, engine="pyarrow")
        print(f"[Silver] Cleaned CDR: {len(valid_cdr)} records")

    # 4. Network KPIs
    net_df = load_bronze_table(bronze_dir, "network")
    if not net_df.empty:
        valid_net, _ = route_quarantine(net_df, validate_network_record, "network", quarantine_dir)
        valid_net = valid_net.drop_duplicates(subset=["cell_id", "timestamp"], keep="last")
        valid_net.to_parquet(os.path.join(silver_dir, "network.parquet"), index=False, engine="pyarrow")
        print(f"[Silver] Cleaned Network KPIs: {len(valid_net)} records")

    # 5. Billing
    bill_df = load_bronze_table(bronze_dir, "billing")
    if not bill_df.empty:
        valid_bill, _ = route_quarantine(bill_df, validate_billing_record, "billing", quarantine_dir)
        valid_bill = valid_bill.drop_duplicates(subset=["invoice_id"], keep="last")
        valid_bill.to_parquet(os.path.join(silver_dir, "billing.parquet"), index=False, engine="pyarrow")
        print(f"[Silver] Cleaned Billing: {len(valid_bill)} records")

    # 6. Usage
    usage_df = load_bronze_table(bronze_dir, "usage")
    if not usage_df.empty:
        valid_usage, _ = route_quarantine(usage_df, validate_usage_record, "usage", quarantine_dir)
        valid_usage = valid_usage.drop_duplicates(subset=["usage_id"], keep="last")
        valid_usage.to_parquet(os.path.join(silver_dir, "usage.parquet"), index=False, engine="pyarrow")
        print(f"[Silver] Cleaned Usage: {len(valid_usage)} records")

    print("=" * 60)
    print("[SUCCESS] Bronze to Silver transformation complete.")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transform Bronze layer to Silver layer")
    parser.add_argument("--bronze-dir", type=str, default="data/bronze", help="Bronze root dir")
    parser.add_argument("--silver-dir", type=str, default="data/silver", help="Silver root dir")
    parser.add_argument("--quarantine-dir", type=str, default="data/quarantine", help="Quarantine root dir")
    args = parser.parse_args()

    run_bronze_to_silver(args.bronze_dir, args.silver_dir, args.quarantine_dir)

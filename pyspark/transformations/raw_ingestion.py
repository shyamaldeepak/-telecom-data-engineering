"""Bronze Layer Ingestion for Telecom 360 Platform.

Loads raw landing files from `data/raw/` into standardized Bronze storage tables
with ingestion metadata columns (_ingested_at, _source_file, _batch_id).
Preserves raw fidelity for auditing, schema evolution, and replayability.
"""

import argparse
import datetime
import json
import os
import uuid
from typing import List, Dict, Any
import pandas as pd


TABLES = ["customers", "subscriptions", "cdr", "network", "billing", "usage"]


def ingest_table_to_bronze(
    table_name: str,
    raw_dir: str = "data/raw",
    bronze_dir: str = "data/bronze"
) -> int:
    source_folder = os.path.join(raw_dir, table_name)
    if not os.path.exists(source_folder):
        print(f"[Bronze Ingestion] Source path does not exist: {source_folder}")
        return 0

    records: List[Dict[str, Any]] = []
    batch_id = str(uuid.uuid4())[:8]
    ingested_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for root, _, files in os.walk(source_folder):
        for f in files:
            if f.endswith(".jsonl") or f.endswith(".json"):
                fpath = os.path.join(root, f)
                with open(fpath, "r", encoding="utf-8") as fin:
                    for line in fin:
                        line = line.strip()
                        if line:
                            rec = json.loads(line)
                            rec["_ingested_at"] = ingested_time
                            rec["_source_file"] = f
                            rec["_batch_id"] = batch_id
                            records.append(rec)

    if not records:
        print(f"[Bronze Ingestion] No records found for table: {table_name}")
        return 0

    df = pd.DataFrame(records)
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    out_table_dir = os.path.join(bronze_dir, table_name, f"date={today_str}")
    os.makedirs(out_table_dir, exist_ok=True)

    out_file = os.path.join(out_table_dir, f"{table_name}_batch_{batch_id}.parquet")
    df.to_parquet(out_file, index=False, engine="pyarrow")
    print(f"[Bronze Ingestion] {table_name}: Ingested {len(records)} records into {out_file}")
    return len(records)


def run_bronze_ingestion(raw_dir: str = "data/raw", bronze_dir: str = "data/bronze"):
    print("=" * 60)
    print("Starting Bronze Layer Raw Ingestion")
    print("=" * 60)
    total = 0
    for tbl in TABLES:
        total += ingest_table_to_bronze(tbl, raw_dir, bronze_dir)
    print("=" * 60)
    print(f"[SUCCESS] Bronze Ingestion completed. Total records ingested: {total}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest raw data to Bronze lakehouse layer")
    parser.add_argument("--raw-dir", type=str, default="data/raw", help="Raw input folder")
    parser.add_argument("--bronze-dir", type=str, default="data/bronze", help="Bronze storage folder")
    args = parser.parse_args()

    run_bronze_ingestion(args.raw_dir, args.bronze_dir)

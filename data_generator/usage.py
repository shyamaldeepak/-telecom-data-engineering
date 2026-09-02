"""Internet / Mobile Data Usage Generator for Telecom 360 Platform.

Generates high-frequency data usage sessions including download/upload volume,
network technologies (3G/4G/5G), and session durations.
"""

import argparse
import datetime
import json
import os
import random
from typing import List, Dict, Any

NETWORK_TYPES = ["4G", "5G", "4G", "5G", "3G"]


def generate_usage_sessions(
    num_records: int = 5000,
    start_usage_id: int = 700001,
    num_customers: int = 1000,
    start_customer_id: int = 10001,
    num_cells: int = 50
) -> List[Dict[str, Any]]:
    records = []
    base_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)

    for i in range(num_records):
        usage_id = f"USG-{start_usage_id + i}"
        cust_idx = random.randint(0, num_customers - 1)
        cust_id = f"C{start_customer_id + cust_idx}"
        dev_id = f"DEV-{cust_idx % 300:04d}"
        cell_id = f"CELL-{random.randint(1, num_cells):03d}"
        
        offset_seconds = random.randint(0, 7 * 86400)
        timestamp = base_time + datetime.timedelta(seconds=offset_seconds)
        
        net_type = random.choice(NETWORK_TYPES)
        session_duration = random.randint(30, 7200)  # 30s to 2 hours
        
        # Data volume scaled by session length and network type
        if net_type == "5G":
            dl_mb = round(random.uniform(20.0, 1500.0), 2)
            ul_mb = round(random.uniform(5.0, 250.0), 2)
        elif net_type == "4G":
            dl_mb = round(random.uniform(10.0, 600.0), 2)
            ul_mb = round(random.uniform(2.0, 90.0), 2)
        else:  # 3G
            dl_mb = round(random.uniform(1.0, 50.0), 2)
            ul_mb = round(random.uniform(0.5, 10.0), 2)

        record = {
            "usage_id": usage_id,
            "customer_id": cust_id,
            "device_id": dev_id,
            "cell_id": cell_id,
            "timestamp": timestamp.isoformat(),
            "download_mb": dl_mb,
            "upload_mb": ul_mb,
            "network_type": net_type,
            "session_duration": session_duration,
        }
        records.append(record)

    return records


def save_usage(records: List[Dict[str, Any]], output_path: str):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"[Usage] Saved {len(records)} records to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic mobile data usage records")
    parser.add_argument("--num-records", type=int, default=5000, help="Number of records to generate")
    parser.add_argument("--output", type=str, default="data/raw/usage/usage.jsonl", help="Output filepath")
    args = parser.parse_args()

    data = generate_usage_sessions(num_records=args.num_records)
    save_usage(data, args.output)

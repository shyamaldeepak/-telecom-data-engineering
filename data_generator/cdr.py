"""Call Detail Records (CDR) Data Generator for Telecom 360 Platform.

Generates voice and telecom call session events with call types, durations, and cell tower mappings.
"""

import argparse
import datetime
import json
import os
import random
from typing import List, Dict, Any

CALL_TYPES = ["LOCAL", "LOCAL", "NATIONAL", "INTERNATIONAL", "ROAMING", "VOIP"]
CALL_STATUSES = ["COMPLETED", "COMPLETED", "COMPLETED", "DROPPED", "FAILED", "BUSY"]


def generate_cdr(
    num_records: int = 5000,
    start_call_id: int = 100001,
    num_customers: int = 1000,
    start_customer_id: int = 10001,
    num_cells: int = 50
) -> List[Dict[str, Any]]:
    records = []
    base_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)

    for i in range(num_records):
        call_id = f"CALL-{start_call_id + i}"
        caller_idx = random.randint(0, num_customers - 1)
        caller_id = f"C{start_customer_id + caller_idx}"
        
        # 75% internal customer receiver, 25% external number
        if random.random() < 0.75:
            rec_idx = random.randint(0, num_customers - 1)
            while rec_idx == caller_idx and num_customers > 1:
                rec_idx = random.randint(0, num_customers - 1)
            receiver_id = f"C{start_customer_id + rec_idx}"
        else:
            receiver_id = f"+1{random.randint(2000000000, 9999999999)}"

        cell_id = f"CELL-{random.randint(1, num_cells):03d}"
        
        # Timestamp distribution across past 7 days
        offset_seconds = random.randint(0, 7 * 86400)
        start_time = base_time + datetime.timedelta(seconds=offset_seconds)
        
        call_status = random.choice(CALL_STATUSES)
        call_type = random.choice(CALL_TYPES)

        if call_status == "COMPLETED":
            # Normal distribution of call durations around 180s
            duration = max(10, int(random.gauss(180, 90)))
        elif call_status == "DROPPED":
            # Dropped mid-call
            duration = random.randint(5, 60)
        else: # FAILED, BUSY
            duration = 0

        end_time = start_time + datetime.timedelta(seconds=duration)

        record = {
            "call_id": call_id,
            "caller_id": caller_id,
            "receiver_id": receiver_id,
            "cell_id": cell_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "call_type": call_type,
            "call_status": call_status,
        }
        records.append(record)

    return records


def save_cdr(records: List[Dict[str, Any]], output_path: str):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"[CDR] Saved {len(records)} records to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic CDR records")
    parser.add_argument("--num-records", type=int, default=5000, help="Number of records to generate")
    parser.add_argument("--output", type=str, default="data/raw/cdr/cdr.jsonl", help="Output filepath")
    args = parser.parse_args()

    data = generate_cdr(num_records=args.num_records)
    save_cdr(data, args.output)

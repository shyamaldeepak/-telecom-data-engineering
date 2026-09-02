"""Subscription Data Generator for Telecom 360 Platform.

Generates subscription tiers, contract periods, and status history for customers.
"""

import argparse
import datetime
import json
import os
import random
from typing import List, Dict, Any

PLANS = [
    {"plan_id": "PLAN_BASIC", "plan_name": "Basic Voice & 5GB", "monthly_price": 29.99},
    {"plan_id": "PLAN_STANDARD", "plan_name": "Standard Unlimited 4G", "monthly_price": 49.99},
    {"plan_id": "PLAN_PREMIUM", "plan_name": "Premium Unlimited 5G Max", "monthly_price": 79.99},
    {"plan_id": "PLAN_BUSINESS", "plan_name": "Enterprise Business Pro", "monthly_price": 119.99},
]

CONTRACT_TYPES = ["MONTH_TO_MONTH", "ONE_YEAR", "TWO_YEAR"]
STATUSES = ["ACTIVE", "ACTIVE", "ACTIVE", "EXPIRED", "CANCELLED"]


def generate_subscriptions(
    num_records: int = 1000, 
    start_customer_id: int = 10001,
    start_sub_id: int = 50001
) -> List[Dict[str, Any]]:
    subscriptions = []
    base_date = datetime.date(2023, 1, 1)

    for i in range(num_records):
        sub_id = f"SUB-{start_sub_id + i}"
        customer_id = f"C{start_customer_id + (i % num_records)}"
        plan = random.choice(PLANS)
        contract = random.choice(CONTRACT_TYPES)
        
        start_offset = random.randint(0, 900)
        start_date = base_date + datetime.timedelta(days=start_offset)
        
        status = random.choice(STATUSES)
        if status in ("EXPIRED", "CANCELLED"):
            duration = 30 if contract == "MONTH_TO_MONTH" else (365 if contract == "ONE_YEAR" else 730)
            end_date = start_date + datetime.timedelta(days=random.randint(15, duration))
            end_date_str = end_date.strftime("%Y-%m-%d")
        else:
            end_date_str = None

        sub = {
            "subscription_id": sub_id,
            "customer_id": customer_id,
            "plan_id": plan["plan_id"],
            "plan_name": plan["plan_name"],
            "contract_type": contract,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date_str,
            "monthly_price": plan["monthly_price"],
            "status": status,
        }
        subscriptions.append(sub)

    return subscriptions


def save_subscriptions(subscriptions: List[Dict[str, Any]], output_path: str):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for sub in subscriptions:
            f.write(json.dumps(sub) + "\n")
    print(f"[Subscriptions] Saved {len(subscriptions)} records to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic subscription records")
    parser.add_argument("--num-records", type=int, default=1000, help="Number of records to generate")
    parser.add_argument("--output", type=str, default="data/raw/subscriptions/subscriptions.jsonl", help="Output filepath")
    args = parser.parse_args()

    data = generate_subscriptions(num_records=args.num_records)
    save_subscriptions(data, args.output)

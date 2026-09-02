"""Billing & Payment Data Generator for Telecom 360 Platform.

Generates recurring monthly invoices, payment amounts, taxes, and status records.
"""

import argparse
import datetime
import json
import os
import random
from typing import List, Dict, Any

PAYMENT_STATUSES = ["PAID", "PAID", "PAID", "PAID", "PENDING", "FAILED", "OVERDUE"]
PAYMENT_METHODS = ["CREDIT_CARD", "AUTO_DEBIT", "BANK_TRANSFER", "PAYPAL"]
BASE_PRICES = [29.99, 49.99, 79.99, 119.99]


def generate_billing_records(
    num_records: int = 2000,
    start_invoice_id: int = 800001,
    num_customers: int = 1000,
    start_customer_id: int = 10001
) -> List[Dict[str, Any]]:
    records = []
    base_date = datetime.date(2024, 1, 1)

    for i in range(num_records):
        inv_id = f"INV-{start_invoice_id + i}"
        cust_idx = i % num_customers
        cust_id = f"C{start_customer_id + cust_idx}"
        sub_id = f"SUB-{50001 + cust_idx}"
        
        # Monthly billing offset
        month_offset = (i // num_customers) * 30 + random.randint(1, 28)
        billing_date = base_date + datetime.timedelta(days=month_offset)

        base_amount = random.choice(BASE_PRICES)
        # 15% probability of data overage or roaming charge
        overage = round(random.uniform(5.0, 35.0), 2) if random.random() < 0.15 else 0.0
        amount = round(base_amount + overage, 2)
        tax = round(amount * 0.0825, 2)
        total_amount = round(amount + tax, 2)

        status = random.choice(PAYMENT_STATUSES)
        method = random.choice(PAYMENT_METHODS)

        record = {
            "invoice_id": inv_id,
            "customer_id": cust_id,
            "subscription_id": sub_id,
            "billing_date": billing_date.strftime("%Y-%m-%d"),
            "amount": amount,
            "tax": tax,
            "total_amount": total_amount,
            "payment_status": status,
            "payment_method": method,
        }
        records.append(record)

    return records


def save_billing(records: List[Dict[str, Any]], output_path: str):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"[Billing] Saved {len(records)} records to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic Billing records")
    parser.add_argument("--num-records", type=int, default=2000, help="Number of records to generate")
    parser.add_argument("--output", type=str, default="data/raw/billing/billing.jsonl", help="Output filepath")
    args = parser.parse_args()

    data = generate_billing_records(num_records=args.num_records)
    save_billing(data, args.output)

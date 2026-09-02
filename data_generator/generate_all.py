"""Master Data Generator Orchestrator for Telecom 360 Platform.

Generates complete relational & streaming datasets for customers, subscriptions,
CDRs, cell tower network KPIs, billing, and internet usage sessions.
"""

import argparse
import os
import sys

# Ensure local imports work cleanly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_generator.customers import generate_customers, save_customers
from data_generator.subscriptions import generate_subscriptions, save_subscriptions
from data_generator.cdr import generate_cdr, save_cdr
from data_generator.network import generate_network_kpis, save_network_kpis
from data_generator.billing import generate_billing_records, save_billing
from data_generator.usage import generate_usage_sessions, save_usage


def generate_all(
    data_dir: str = "data/raw",
    scale_factor: float = 1.0,
    seed: int = 42
):
    import random
    random.seed(seed)

    print("=" * 60)
    print(f"Generating synthetic telecom datasets (Scale factor: {scale_factor})")
    print(f"Target directory: {os.path.abspath(data_dir)}")
    print("=" * 60)

    num_customers = int(1000 * scale_factor)
    num_subs = int(1200 * scale_factor)
    num_cdr = int(5000 * scale_factor)
    num_network = int(3000 * scale_factor)
    num_billing = int(2000 * scale_factor)
    num_usage = int(6000 * scale_factor)

    # 1. Customers
    customers = generate_customers(num_records=num_customers)
    save_customers(customers, os.path.join(data_dir, "customers", "customers.jsonl"))

    # 2. Subscriptions
    subscriptions = generate_subscriptions(num_records=num_subs, start_customer_id=10001)
    save_subscriptions(subscriptions, os.path.join(data_dir, "subscriptions", "subscriptions.jsonl"))

    # 3. CDR
    cdr_data = generate_cdr(num_records=num_cdr, num_customers=num_customers)
    save_cdr(cdr_data, os.path.join(data_dir, "cdr", "cdr.jsonl"))

    # 4. Network KPIs
    network_data = generate_network_kpis(num_records=num_network, num_cells=50)
    save_network_kpis(network_data, os.path.join(data_dir, "network", "network.jsonl"))

    # 5. Billing
    billing_data = generate_billing_records(num_records=num_billing, num_customers=num_customers)
    save_billing(billing_data, os.path.join(data_dir, "billing", "billing.jsonl"))

    # 6. Usage
    usage_data = generate_usage_sessions(num_records=num_usage, num_customers=num_customers)
    save_usage(usage_data, os.path.join(data_dir, "usage", "usage.jsonl"))

    print("=" * 60)
    print("[SUCCESS] All synthetic datasets generated successfully.")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate all telecom datasets")
    parser.add_argument("--data-dir", type=str, default="data/raw", help="Target root data directory")
    parser.add_argument("--scale", type=float, default=1.0, help="Scale factor multiplier")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    generate_all(data_dir=args.data_dir, scale_factor=args.scale, seed=args.seed)

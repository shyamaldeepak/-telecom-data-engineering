"""Customer Data Generator for Telecom 360 Platform.

Generates realistic customer demographic profiles and registration data.
"""

import argparse
import datetime
import json
import os
import random
from typing import List, Dict, Any

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
]

CITIES_WITH_REGIONS = [
    ("New York", "East"),
    ("Boston", "East"),
    ("Philadelphia", "East"),
    ("Chicago", "Central"),
    ("Dallas", "Central"),
    ("Houston", "Central"),
    ("Denver", "Central"),
    ("Los Angeles", "West"),
    ("San Francisco", "West"),
    ("Seattle", "West"),
    ("Atlanta", "South"),
    ("Miami", "South"),
    ("Charlotte", "South"),
    ("Minneapolis", "North"),
    ("Detroit", "North"),
]

GENDERS = ["M", "F", "Other"]
STATUSES = ["ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE", "INACTIVE", "SUSPENDED"]


def generate_customers(num_records: int = 1000, start_id: int = 10001) -> List[Dict[str, Any]]:
    customers = []
    base_date = datetime.date(2023, 1, 1)

    for i in range(num_records):
        cust_id = f"C{start_id + i}"
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        
        # Age between 18 and 75
        age_days = random.randint(18 * 365, 75 * 365)
        dob = datetime.date.today() - datetime.timedelta(days=age_days)
        
        gender = random.choice(GENDERS)
        city, _ = random.choice(CITIES_WITH_REGIONS)
        country = "United States"
        
        # Registration within last 3 years
        reg_offset = random.randint(0, 1000)
        reg_date = base_date + datetime.timedelta(days=reg_offset)
        
        status = random.choice(STATUSES)

        customer = {
            "customer_id": cust_id,
            "first_name": first_name,
            "last_name": last_name,
            "date_of_birth": dob.strftime("%Y-%m-%d"),
            "gender": gender,
            "city": city,
            "country": country,
            "registration_date": reg_date.strftime("%Y-%m-%d"),
            "customer_status": status,
        }
        customers.append(customer)

    return customers


def save_customers(customers: List[Dict[str, Any]], output_path: str):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for cust in customers:
            f.write(json.dumps(cust) + "\n")
    print(f"[Customers] Saved {len(customers)} records to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic telecom customer records")
    parser.add_argument("--num-records", type=int, default=1000, help="Number of records to generate")
    parser.add_argument("--output", type=str, default="data/raw/customers/customers.jsonl", help="Output filepath")
    args = parser.parse_args()

    data = generate_customers(num_records=args.num_records)
    save_customers(data, args.output)

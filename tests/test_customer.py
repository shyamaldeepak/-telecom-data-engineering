"""Tests for Customer Data Generation and Quality Rules."""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_generator.customers import generate_customers
from pyspark.quality.rules import validate_customer_record


def test_generate_customers():
    customers = generate_customers(num_records=50)
    assert len(customers) == 50
    for c in customers:
        assert c["customer_id"].startswith("C")
        assert len(c["first_name"]) > 0
        assert len(c["last_name"]) > 0
        assert c["customer_status"] in ("ACTIVE", "INACTIVE", "SUSPENDED")


def test_validate_customer_record_valid():
    rec = {
        "customer_id": "C1001",
        "first_name": "Alice",
        "last_name": "Smith",
        "customer_status": "ACTIVE"
    }
    is_valid, errors = validate_customer_record(rec)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_customer_record_invalid():
    rec = {
        "customer_id": None,
        "first_name": "",
        "last_name": "Smith",
        "customer_status": "UNKNOWN"
    }
    is_valid, errors = validate_customer_record(rec)
    assert is_valid is False
    assert len(errors) >= 2

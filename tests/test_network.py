"""Tests for Network Telemetry and Quality Validation."""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_generator.network import generate_network_kpis
from pyspark.quality.rules import validate_network_record


def test_generate_network_kpis():
    records = generate_network_kpis(num_records=40, num_cells=10)
    assert len(records) == 40
    for r in records:
        assert r["cell_id"].startswith("CELL-")
        assert r["latency_ms"] >= 0
        assert 0 <= r["packet_loss_percentage"] <= 100
        assert 0 <= r["availability_percentage"] <= 100


def test_validate_network_record_valid():
    rec = {
        "cell_id": "CELL-010",
        "latency_ms": 25.4,
        "packet_loss_percentage": 0.5,
        "availability_percentage": 99.8
    }
    is_valid, errors = validate_network_record(rec)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_network_record_out_of_bounds():
    rec = {
        "cell_id": "CELL-010",
        "latency_ms": -5.0,
        "packet_loss_percentage": 150.0,
        "availability_percentage": 105.0
    }
    is_valid, errors = validate_network_record(rec)
    assert is_valid is False
    assert len(errors) >= 3

"""Tests for Call Detail Records (CDR) Generation and Quality Rules."""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_generator.cdr import generate_cdr
from pyspark.quality.rules import validate_cdr_record


def test_generate_cdr():
    cdrs = generate_cdr(num_records=50)
    assert len(cdrs) == 50
    for r in cdrs:
        assert r["call_id"].startswith("CALL-")
        assert r["duration_seconds"] >= 0
        assert r["call_status"] in ("COMPLETED", "DROPPED", "FAILED", "BUSY")


def test_validate_cdr_record_valid():
    rec = {
        "call_id": "CALL-12345",
        "caller_id": "C1001",
        "receiver_id": "C1002",
        "cell_id": "CELL-001",
        "duration_seconds": 120,
        "call_status": "COMPLETED"
    }
    is_valid, errors = validate_cdr_record(rec)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_cdr_record_negative_duration():
    rec = {
        "call_id": "CALL-12345",
        "caller_id": "C1001",
        "cell_id": "CELL-001",
        "duration_seconds": -10,
        "call_status": "COMPLETED"
    }
    is_valid, errors = validate_cdr_record(rec)
    assert is_valid is False
    assert any("duration_seconds" in e for e in errors)

"""Data Quality Rules and Quarantine Framework for Telecom 360 Platform.

Validates incoming records against business constraints and schema rules,
diverting invalid rows to quarantine zone.
"""

from typing import Dict, Any, List, Tuple


def validate_customer_record(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors = []
    if not record.get("customer_id"):
        errors.append("customer_id is null or empty")
    if not record.get("first_name") or not record.get("last_name"):
        errors.append("first_name or last_name missing")
    if record.get("customer_status") not in ("ACTIVE", "INACTIVE", "SUSPENDED"):
        errors.append(f"invalid customer_status: {record.get('customer_status')}")
    return len(errors) == 0, errors


def validate_cdr_record(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors = []
    if not record.get("call_id"):
        errors.append("call_id is null")
    if not record.get("caller_id"):
        errors.append("caller_id is null")
    if not record.get("cell_id"):
        errors.append("cell_id is null")
    
    duration = record.get("duration_seconds", 0)
    if duration is None or duration < 0:
        errors.append(f"invalid duration_seconds: {duration}")
        
    status = record.get("call_status")
    if status not in ("COMPLETED", "DROPPED", "FAILED", "BUSY"):
        errors.append(f"invalid call_status: {status}")
        
    return len(errors) == 0, errors


def validate_network_record(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors = []
    if not record.get("cell_id"):
        errors.append("cell_id is null")
        
    latency = record.get("latency_ms", 0)
    if latency is None or latency < 0 or latency > 2000:
        errors.append(f"unrealistic latency_ms: {latency}")
        
    pkt_loss = record.get("packet_loss_percentage", 0)
    if pkt_loss is None or pkt_loss < 0 or pkt_loss > 100:
        errors.append(f"invalid packet_loss_percentage: {pkt_loss}")
        
    avail = record.get("availability_percentage", 100)
    if avail is None or avail < 0 or avail > 100:
        errors.append(f"availability_percentage out of bounds: {avail}")
        
    return len(errors) == 0, errors


def validate_usage_record(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors = []
    if not record.get("usage_id"):
        errors.append("usage_id is null")
    if not record.get("customer_id"):
        errors.append("customer_id is null")
        
    dl_mb = record.get("download_mb", 0)
    ul_mb = record.get("upload_mb", 0)
    if dl_mb is None or dl_mb < 0:
        errors.append(f"invalid download_mb: {dl_mb}")
    if ul_mb is None or ul_mb < 0:
        errors.append(f"invalid upload_mb: {ul_mb}")
        
    return len(errors) == 0, errors


def validate_billing_record(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors = []
    if not record.get("invoice_id"):
        errors.append("invoice_id is null")
    if not record.get("customer_id"):
        errors.append("customer_id is null")
        
    amount = record.get("amount", 0)
    total = record.get("total_amount", 0)
    if amount is None or amount < 0 or total is None or total < 0:
        errors.append(f"negative invoice amount: amount={amount}, total={total}")
        
    return len(errors) == 0, errors

"""Kafka Stream Consumer & Bronze Ingestion Lander for Telecom 360 Platform.

Consumes real-time events from Kafka topics and persists micro-batches into
the Bronze storage layer with ingestion timestamps and metadata.
"""

import argparse
import datetime
import json
import os
import time
from typing import List, Dict, Any


import socket

def is_broker_online(host_port: str) -> bool:
    try:
        parts = host_port.split(":")
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 9092
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def consume_and_land(
    topic: str = "telecom.cdr",
    bootstrap_servers: str = "localhost:9092",
    bronze_dir: str = "data/bronze",
    batch_size: int = 50,
    poll_timeout_s: float = 2.0,
    max_batches: int = 5
):
    source_name = topic.replace("telecom.", "")
    target_dir = os.path.join(bronze_dir, source_name)
    os.makedirs(target_dir, exist_ok=True)

    consumer = None
    first_broker = bootstrap_servers.split(",")[0]
    if is_broker_online(first_broker):
        try:
            from kafka import KafkaConsumer
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers.split(","),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                group_id=f"telecom-bronze-{source_name}-group",
                value_deserializer=lambda x: json.loads(x.decode("utf-8")),
                consumer_timeout_ms=int(poll_timeout_s * 1000),
                request_timeout_ms=3000
            )
            print(f"[Bronze Lander] Connected to Kafka. Consuming topic: {topic}")
        except Exception as e:
            print(f"[Bronze Lander] Kafka unreachable ({e}). Scanning local streaming buffer...")
            consumer = None
    else:
        print(f"[Bronze Lander] Kafka broker {first_broker} not online. Scanning local streaming buffer...")

    batch_count = 0
    total_records = 0

    if consumer:
        batch = []
        for message in consumer:
            record = message.value
            record["_ingested_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            record["_source_topic"] = topic
            batch.append(record)

            if len(batch) >= batch_size:
                batch_count += 1
                total_records += len(batch)
                _save_bronze_batch(batch, target_dir, source_name, batch_count)
                batch = []
                if max_batches and batch_count >= max_batches:
                    break

        if batch:
            batch_count += 1
            total_records += len(batch)
            _save_bronze_batch(batch, target_dir, source_name, batch_count)
    else:
        # Fallback to landing existing streaming buffers
        buffer_dir = os.path.join("data/bronze/streaming", source_name)
        if os.path.exists(buffer_dir):
            for fname in os.listdir(buffer_dir):
                if fname.endswith(".jsonl"):
                    fpath = os.path.join(buffer_dir, fname)
                    records = []
                    with open(fpath, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                r = json.loads(line)
                                r["_ingested_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                                r["_source_topic"] = topic
                                records.append(r)
                    if records:
                        batch_count += 1
                        total_records += len(records)
                        _save_bronze_batch(records, target_dir, source_name, batch_count)
                        os.remove(fpath)

    print(f"[Bronze Lander] Completed landing for {source_name}. Total records: {total_records} in {batch_count} batches.")


def _save_bronze_batch(batch: List[Dict[str, Any]], target_dir: str, source_name: str, batch_num: int):
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    out_dir = os.path.join(target_dir, f"date={today_str}")
    os.makedirs(out_dir, exist_ok=True)
    
    filename = f"{source_name}_batch_{int(time.time())}_{batch_num}.jsonl"
    filepath = os.path.join(out_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        for r in batch:
            f.write(json.dumps(r) + "\n")
    print(f"[Bronze Lander] Landed {len(batch)} records to {filepath}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Consume streaming events into Bronze layer")
    parser.add_argument("--topic", type=str, default="telecom.cdr", help="Topic to consume")
    parser.add_argument("--bootstrap-servers", type=str, default="localhost:9092", help="Kafka broker")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size")
    args = parser.parse_args()

    consume_and_land(topic=args.topic, bootstrap_servers=args.bootstrap_servers, batch_size=args.batch_size)

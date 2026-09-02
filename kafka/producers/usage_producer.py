"""Kafka Mobile Internet Usage Producer for Telecom 360 Platform.

Publishes real-time session packets and data volumes to the 'telecom.usage' topic.
"""

import argparse
import json
import os
import sys
import time
from typing import Optional

# Local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from data_generator.usage import generate_usage_sessions


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


def create_producer(bootstrap_servers: str):
    first_broker = bootstrap_servers.split(",")[0]
    if not is_broker_online(first_broker):
        print(f"[Kafka Usage Producer] Kafka broker {first_broker} offline. Running in file-buffer mode.")
        return None
    try:
        from kafka import KafkaProducer
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers.split(","),
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            acks="all",
            retries=2,
            request_timeout_ms=3000,
        )
        print(f"[Kafka Usage Producer] Connected to broker: {bootstrap_servers}")
        return producer
    except Exception as e:
        print(f"[Kafka Usage Producer] Warning: Could not connect to Kafka ({e}). Running in file-buffer mode.")
        return None


def run_producer(
    topic: str = "telecom.usage",
    bootstrap_servers: str = "localhost:9092",
    rate_eps: float = 10.0,
    max_records: Optional[int] = 100,
    buffer_dir: str = "data/bronze/streaming/usage"
):
    producer = create_producer(bootstrap_servers)
    delay = 1.0 / rate_eps if rate_eps > 0 else 0.1
    count = 0

    if not producer:
        os.makedirs(buffer_dir, exist_ok=True)
        buffer_file = os.path.join(buffer_dir, f"usage_stream_{int(time.time())}.jsonl")
        print(f"[Kafka Usage Producer] Buffering stream events to: {buffer_file}")

    print(f"[Kafka Usage Producer] Starting stream to '{topic}' at ~{rate_eps} events/sec...")

    try:
        while True:
            records = generate_usage_sessions(num_records=1, num_customers=1000)
            record = records[0]

            if producer:
                producer.send(topic, value=record)
            else:
                with open(buffer_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record) + "\n")

            count += 1
            if count % 25 == 0 or (max_records and count == max_records):
                print(f"[Kafka Usage Producer] Published {count} events...")

            if max_records and count >= max_records:
                break

            time.sleep(delay)

    except KeyboardInterrupt:
        print("\n[Kafka Usage Producer] Stopping producer gracefully...")
    finally:
        if producer:
            producer.flush()
            producer.close()
        print(f"[Kafka Usage Producer] Completed session. Total events: {count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Telecom Mobile Usage Kafka Producer")
    parser.add_argument("--topic", type=str, default="telecom.usage", help="Target Kafka topic")
    parser.add_argument("--bootstrap-servers", type=str, default="localhost:9092", help="Kafka broker address")
    parser.add_argument("--rate", type=float, default=20.0, help="Events per second")
    parser.add_argument("--count", type=int, default=100, help="Total events to publish (0 for continuous)")
    args = parser.parse_args()

    run_producer(
        topic=args.topic,
        bootstrap_servers=args.bootstrap_servers,
        rate_eps=args.rate,
        max_records=args.count if args.count > 0 else None
    )

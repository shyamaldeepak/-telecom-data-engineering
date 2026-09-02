"""Network KPI Data Generator for Telecom 360 Platform.

Generates continuous telemetry metrics for cell towers including connected users,
speed, latency, packet loss, availability, and simulated network outage anomalies.
"""

import argparse
import datetime
import json
import os
import random
from typing import List, Dict, Any

REGIONS = ["North", "South", "East", "West", "Central"]
TECHNOLOGIES = ["4G", "5G", "4G", "5G", "3G"]


def generate_network_kpis(
    num_records: int = 3000,
    num_cells: int = 50,
    anomaly_rate: float = 0.08
) -> List[Dict[str, Any]]:
    records = []
    base_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)

    # Assign static properties per cell tower
    cell_metadata = {}
    for c in range(1, num_cells + 1):
        cell_id = f"CELL-{c:03d}"
        cell_metadata[cell_id] = {
            "region": REGIONS[(c - 1) % len(REGIONS)],
            "technology": TECHNOLOGIES[(c - 1) % len(TECHNOLOGIES)],
        }

    for i in range(num_records):
        cell_id = f"CELL-{random.randint(1, num_cells):03d}"
        meta = cell_metadata[cell_id]
        
        offset_seconds = random.randint(0, 7 * 86400)
        timestamp = base_time + datetime.timedelta(seconds=offset_seconds)
        
        tech = meta["technology"]
        is_anomaly = random.random() < anomaly_rate

        if not is_anomaly:
            # Normal operating parameters
            if tech == "5G":
                dl_speed = round(random.uniform(150.0, 450.0), 2)
                ul_speed = round(random.uniform(30.0, 95.0), 2)
                latency = round(random.uniform(12.0, 35.0), 2)
                packet_loss = round(random.uniform(0.0, 0.8), 3)
                signal = round(random.uniform(-85.0, -65.0), 1)
                avail = round(random.uniform(99.0, 100.0), 2)
                users = random.randint(300, 3500)
            elif tech == "4G":
                dl_speed = round(random.uniform(25.0, 120.0), 2)
                ul_speed = round(random.uniform(8.0, 35.0), 2)
                latency = round(random.uniform(28.0, 65.0), 2)
                packet_loss = round(random.uniform(0.1, 1.8), 3)
                signal = round(random.uniform(-95.0, -75.0), 1)
                avail = round(random.uniform(98.5, 99.9), 2)
                users = random.randint(200, 2200)
            else:  # 3G
                dl_speed = round(random.uniform(3.0, 15.0), 2)
                ul_speed = round(random.uniform(1.0, 5.0), 2)
                latency = round(random.uniform(65.0, 140.0), 2)
                packet_loss = round(random.uniform(0.5, 3.5), 3)
                signal = round(random.uniform(-105.0, -85.0), 1)
                avail = round(random.uniform(97.0, 99.5), 2)
                users = random.randint(50, 600)
        else:
            # Simulated network incident / degradation
            dl_speed = round(random.uniform(0.5, 8.0), 2)
            ul_speed = round(random.uniform(0.1, 2.0), 2)
            latency = round(random.uniform(220.0, 650.0), 2)
            packet_loss = round(random.uniform(8.0, 32.0), 3)
            signal = round(random.uniform(-120.0, -108.0), 1)
            avail = round(random.uniform(55.0, 88.0), 2)
            users = random.randint(800, 4500)

        record = {
            "cell_id": cell_id,
            "timestamp": timestamp.isoformat(),
            "region": meta["region"],
            "technology": tech,
            "connected_users": users,
            "download_speed_mbps": dl_speed,
            "upload_speed_mbps": ul_speed,
            "latency_ms": latency,
            "packet_loss_percentage": packet_loss,
            "signal_strength": signal,
            "availability_percentage": avail,
        }
        records.append(record)

    return records


def save_network_kpis(records: List[Dict[str, Any]], output_path: str):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"[Network] Saved {len(records)} records to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic Network KPI records")
    parser.add_argument("--num-records", type=int, default=3000, help="Number of records to generate")
    parser.add_argument("--num-cells", type=int, default=50, help="Number of cell towers")
    parser.add_argument("--output", type=str, default="data/raw/network/network.jsonl", help="Output filepath")
    args = parser.parse_args()

    data = generate_network_kpis(num_records=args.num_records, num_cells=args.num_cells)
    save_network_kpis(data, args.output)

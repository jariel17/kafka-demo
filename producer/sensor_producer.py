import json
import random
import time
import threading
from datetime import datetime, timezone
from confluent_kafka import Producer

BOOTSTRAP_SERVERS = "localhost:9092,localhost:9094,localhost:9096"
TOPIC = "sensor-readings"

SENSORS = [
    {"sensor_id": "sensor-1", "location": "Greenhouse A"},
    {"sensor_id": "sensor-2", "location": "Greenhouse B"},
    {"sensor_id": "sensor-3", "location": "Open Field"},
]


def make_reading(sensor: dict) -> dict:
    # ~8% chance of a temperature spike above 38°C to trigger alerts
    if random.random() < 0.08:
        temperature = round(random.uniform(38.1, 42.0), 1)
    else:
        temperature = round(random.uniform(18.0, 37.9), 1)

    humidity = round(random.uniform(40.0, 90.0), 1)

    return {
        "sensor_id": sensor["sensor_id"],
        "location": sensor["location"],
        "temperature_c": temperature,
        "humidity_pct": humidity,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def delivery_report(err, msg):
    if err:
        print(f"[ERROR] Delivery failed for {msg.key()}: {err}")
    else:
        print(
            f"[OK] {msg.key().decode()} → partition {msg.partition()} "
            f"offset {msg.offset()}"
        )


def sensor_loop(producer: Producer, sensor: dict):
    print(f"[START] {sensor['sensor_id']} ({sensor['location']}) sending...")
    while True:
        reading = make_reading(sensor)
        producer.produce(
            topic=TOPIC,
            key=sensor["sensor_id"],
            value=json.dumps(reading),
            callback=delivery_report,
        )
        producer.poll(0)
        time.sleep(random.uniform(1.0, 2.0))


def main():
    producer = Producer(
        {
            "bootstrap.servers": BOOTSTRAP_SERVERS,
            "acks": "all",
        }
    )

    threads = [
        threading.Thread(target=sensor_loop, args=(producer, sensor), daemon=True)
        for sensor in SENSORS
    ]

    for t in threads:
        t.start()

    print(f"Producing to topic '{TOPIC}'. Press Ctrl+C to stop.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping producer...")
        producer.flush()


if __name__ == "__main__":
    main()

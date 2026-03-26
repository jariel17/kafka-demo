import json
from datetime import datetime, timezone
from confluent_kafka import Consumer, KafkaError

BOOTSTRAP_SERVERS = "localhost:9092,localhost:9094,localhost:9096"
TOPIC             = "sensor-readings"
GROUP_ID          = "alerter-group"
ALERT_THRESHOLD   = 38.0


def format_time(iso_timestamp: str) -> str:
    dt = datetime.fromisoformat(iso_timestamp)
    return dt.astimezone().strftime("%H:%M:%S")


def main():
    consumer = Consumer(
        {
            "bootstrap.servers": BOOTSTRAP_SERVERS,
            "group.id": GROUP_ID,
            "auto.offset.reset": "latest",
        }
    )
    consumer.subscribe([TOPIC])

    print(f"Alerter listening on '{TOPIC}' (group: {GROUP_ID})")
    print(f"Will alert when temperature exceeds {ALERT_THRESHOLD}°C\n")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    print(f"[ERROR] {msg.error()}")
                continue

            data = json.loads(msg.value())
            temp = data["temperature_c"]

            if temp >= ALERT_THRESHOLD:
                time_str = format_time(data["timestamp"])
                print(
                    f"[ALERT] {time_str}  {data['sensor_id']:<10} "
                    f"{data['location']:<15}  {temp}°C"
                )

    except KeyboardInterrupt:
        print("\nAlerter stopped.")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()

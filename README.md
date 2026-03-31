# Kafka Demo — IoT Sensor Dashboard

A self-contained demo of Apache Kafka running in Docker, simulating an IoT sensor network with a real-time web dashboard.

## What it does

Three virtual IoT sensors publish data to a 3-broker Kafka cluster (KRaft mode, no ZooKeeper). Two Python applications consume that data in parallel:

```
Sensors (producer)
    │
    ├──► topic: sensor-readings  ──► Web Dashboard  (live stream + partition map)
    │                            ──► Alerter         (prints high-temperature alerts)
    │
    └──► topic: sensor-health    ──► Web Dashboard  (heartbeat / online status)
```

### Components

| Component | Path | Description |
|---|---|---|
| **Kafka cluster** | `docker-compose.yml` | 3 brokers (KRaft), topics created automatically on first start |
| **Producer** | `producer/sensor_producer.py` | Publishes temperature + humidity readings and heartbeats for 3 sensors |
| **Alerter** | `consumer-alerter/alerter.py` | Prints a terminal alert whenever temperature exceeds 38 °C |
| **Web Dashboard** | `web-dashboard/` | FastAPI + WebSocket backend; animated browser UI showing live messages, cluster topology, and partition leadership |

### Key Kafka configuration

- 3 brokers, each acting as both broker and KRaft controller
- Replication factor 3, min in-sync replicas 2
- Topics: `sensor-readings` and `sensor-health`, each with 3 partitions
- The dashboard can stop/start individual brokers to demonstrate fault tolerance

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with the Compose plugin (`docker compose`)
- [uv](https://docs.astral.sh/uv/) (Python package manager)

---

## Quick start

### 1. Start the Kafka cluster

```bash
docker compose up -d
```

This starts brokers 1–3 and waits for them to be healthy before creating the topics. Check status with:

```bash
docker compose ps
```

Topics are ready when the `kafka-init` container exits with code 0.

### 2. Start the web dashboard

```bash
uv run uvicorn web-dashboard.app:app --reload
```

Open **http://localhost:8000** in your browser.

### 3. Start the producer

In a separate terminal:

```bash
uv run python producer/sensor_producer.py
```

Sensor data will start flowing into the dashboard immediately.

### 4. (Optional) Start the alerter

In another terminal:

```bash
uv run python consumer-alerter/alerter.py
```

The alerter prints a line to the terminal whenever any sensor reports a temperature above 38 °C.

---

## Stopping everything

```bash
# Stop Python processes with Ctrl-C in each terminal, then:
docker compose down
```

To also delete the broker data volumes:

```bash
docker compose down -v
```

---

## Fault tolerance demo

The dashboard has **Stop / Start** buttons for each broker. Stopping one broker leaves the cluster fully functional (replication factor 3, min ISR 2). Stopping two brokers will make the cluster unavailable for writes. Use this to observe Kafka's leader election and ISR behaviour live in the partition map.

import asyncio
import json
import threading
from pathlib import Path

from confluent_kafka import Consumer
from confluent_kafka.admin import AdminClient
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

BOOTSTRAP_SERVERS = "localhost:9092,localhost:9094,localhost:9096"
TOPIC = "sensor-readings"
HERE = Path(__file__).parent

app = FastAPI()

# All browser clients currently connected via WebSocket
clients: set[WebSocket] = set()
clients_lock = threading.Lock()
main_loop: asyncio.AbstractEventLoop | None = None


@app.on_event("startup")
async def startup():
    global main_loop
    main_loop = asyncio.get_event_loop()
    threading.Thread(target=kafka_consumer_loop, daemon=True).start()


def kafka_consumer_loop():
    """Runs in a background thread. Reads from Kafka and pushes to all WebSocket clients."""
    consumer = Consumer(
        {
            "bootstrap.servers": BOOTSTRAP_SERVERS,
            "group.id": "web-dashboard-group",
            "auto.offset.reset": "latest",
        }
    )
    consumer.subscribe([TOPIC])
    while True:
        msg = consumer.poll(1.0)
        if msg is None or msg.error():
            continue
        data = json.loads(msg.value())
        data["partition"] = msg.partition()
        broadcast(data)


def broadcast(data: dict):
    """Send a message to every connected browser client."""
    with clients_lock:
        snapshot = set(clients)
    for ws in snapshot:
        asyncio.run_coroutine_threadsafe(ws.send_json(data), main_loop)


@app.get("/")
async def index():
    return HTMLResponse((HERE / "dashboard.html").read_text())


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    with clients_lock:
        clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        with clients_lock:
            clients.discard(ws)


@app.get("/api/cluster")
async def cluster_info():
    admin = AdminClient({"bootstrap.servers": BOOTSTRAP_SERVERS})
    metadata = admin.list_topics(timeout=5)

    brokers = [
        {"id": b.id, "host": b.host, "port": b.port}
        for b in metadata.brokers.values()
    ]

    topic = metadata.topics.get(TOPIC)
    partitions = []
    if topic:
        for p in topic.partitions.values():
            partitions.append(
                {
                    "id": p.id,
                    "leader": p.leader,
                    "replicas": list(p.replicas),
                    "isrs": list(p.isrs),
                }
            )

    return {
        "brokers": sorted(brokers, key=lambda b: b["id"]),
        "partitions": sorted(partitions, key=lambda p: p["id"]),
        "controller_id": metadata.controller_id,
    }

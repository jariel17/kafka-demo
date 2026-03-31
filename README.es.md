# Kafka Demo — Panel de sensores IoT

Demo de Apache Kafka corriendo en Docker, que simula una red de sensores IoT con un panel web en tiempo real.

## Qué hace

Tres sensores IoT virtuales publican datos en un clúster Kafka de 3 brokers (modo KRaft, sin ZooKeeper). Dos aplicaciones Python consumen esos datos en paralelo:

```
Sensores (productor)
    │
    ├──► topic: sensor-readings  ──► Panel web   (stream en vivo + mapa de particiones)
    │                            ──► Alertador    (imprime alertas de temperatura alta)
    │
    └──► topic: sensor-health    ──► Panel web   (estado de heartbeat / en línea)
```

### Componentes

| Componente | Ruta | Descripción |
|---|---|---|
| **Clúster Kafka** | `docker-compose.yml` | 3 brokers (KRaft), topics creados automáticamente al primer inicio |
| **Productor** | `producer/sensor_producer.py` | Publica lecturas de temperatura + humedad y heartbeats de 3 sensores |
| **Alertador** | `consumer-alerter/alerter.py` | Imprime una alerta en terminal cuando la temperatura supera los 38 °C |
| **Panel web** | `web-dashboard/` | Backend FastAPI + WebSocket; UI animada en el navegador con mensajes en vivo, topología del clúster y liderazgo de particiones |

### Configuración clave de Kafka

- 3 brokers, cada uno actuando como broker y controlador KRaft
- Factor de replicación 3, mínimo de réplicas sincronizadas (ISR) 2
- Topics: `sensor-readings` y `sensor-health`, cada uno con 3 particiones
- El panel permite detener/iniciar brokers individuales para demostrar tolerancia a fallos

---

## Requisitos previos

- [Docker](https://docs.docker.com/get-docker/) con el plugin Compose (`docker compose`)
- [uv](https://docs.astral.sh/uv/) (gestor de paquetes Python)

---

## Inicio rápido

### 1. Iniciar el clúster Kafka

```bash
docker compose up -d
```

Esto levanta los brokers 1–3 y espera a que estén sanos antes de crear los topics. Verificá el estado con:

```bash
docker compose ps
```

Los topics están listos cuando el contenedor `kafka-init` termina con código 0.

### 2. Iniciar el panel web

```bash
uv run uvicorn web-dashboard.app:app --reload
```

Abre **http://localhost:8000** en el navegador.

### 3. Iniciar el productor

En otra terminal:

```bash
uv run python producer/sensor_producer.py
```

Los datos de los sensores comenzarán a fluir al panel de inmediato.

### 4. (Opcional) Iniciar el alertador

En otra terminal:

```bash
uv run python consumer-alerter/alerter.py
```

El alertador imprime una línea en la terminal cada vez que un sensor reporta una temperatura superior a 38 °C.

---

## Detener todo

```bash
# Detener los procesos Python con Ctrl-C en cada terminal, luego:
docker compose down
```

Para eliminar también los volúmenes de datos de los brokers:

```bash
docker compose down -v
```

---

## Demo de tolerancia a fallos

El panel tiene botones **Detener / Iniciar** para cada broker. Detener un broker deja el clúster completamente funcional (factor de replicación 3, ISR mínimo 2). Detener dos brokers hará que el clúster deje de aceptar escrituras.

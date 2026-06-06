# iot-server

IoT device backend server project.

## Target Services

- `docker/web-backend`: Web admin backend and database-facing service.
- `docker/mqtt-server`: MQTT broker service configuration for IoT device messaging.
- `docker/streaming-server`: Nginx-based streaming service for pull-stream access.
- `docker`: Local Docker Compose orchestration for development services.
- `docs`: Learning docs for building the server, cloud services, certificates,
  and service boundaries.

## Core Requirements

- Devices must establish mutual TLS authentication before accessing services.
- The platform must include a mature traffic surge mitigation design.
- Each service is developed independently in its own folder.
- Documentation focuses on learning how to build each service, not only how to
  start containers.

## Initial Mature Stack

- Web backend database: PostgreSQL.
- MQTT server: EMQX with TLS/mTLS support.
- Streaming server: Nginx with RTMP module.
- Surge mitigation: Nginx rate limiting, EMQX rate limiting, Redis/Kafka buffering plan.

Start with `docs/index.html` for the learning path and service build guide.

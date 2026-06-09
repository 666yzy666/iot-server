# MQTT Server

This folder contains MQTT broker configuration and service-specific assets.

## Recommended Broker

Use EMQX because it is open source, mature, supports MQTT 3.1.1/5.0, and has
TLS/mTLS, authentication, authorization, clustering, rate limits, and rule
engine integrations.

## Responsibilities

- Accept device MQTT connections over TLS with client certificate validation.
- Enforce topic authorization per device identity.
- Apply broker-side rate limits and connection limits.
- Forward telemetry to the backend through Kafka, RabbitMQ, webhook, or rule
engine integrations.

## Ports

- `1883`: local plain MQTT for development only, bound to `127.0.0.1`.
- `8883`: MQTT over TLS/mTLS for devices.
- `18083`: EMQX dashboard/API, bound to `127.0.0.1`.

Do not publish the EMQX dashboard directly to the public internet. Logs such as
`unexpected_api_access` with paths like `/.git/config` are usually scanners
probing the dashboard/API endpoint through a public reverse proxy.

## Run This Service

Run MQTT only from this directory:

```bash
docker compose up -d
docker compose logs -f mqtt
```

The root `docker/docker-compose.yml` can also orchestrate this service together
with the web backend, PostgreSQL, and streaming service.

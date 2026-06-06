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

- `1883`: local plain MQTT for development only.
- `8883`: MQTT over TLS/mTLS for devices.
- `18083`: EMQX dashboard.

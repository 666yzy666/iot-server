# Web Backend

This folder contains the web admin backend and database-facing service.

## Responsibilities

- Provide web admin APIs.
- Store device, user, certificate, stream, and audit metadata.
- Validate device identity after mutual TLS termination.
- Write high-volume device events through a buffering layer when traffic spikes.

## Planned Components

- API service.
- PostgreSQL schema and migrations.
- Redis cache.
- Kafka or RabbitMQ event buffer for surge absorption.

## Security

Device-facing APIs must only be exposed through a gateway that enforces mutual
TLS. Backend services should trust forwarded identity headers only from the
gateway network.

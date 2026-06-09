# Streaming Server

This folder contains Nginx-based streaming service configuration.

## Responsibilities

- Provide pull-stream endpoints.
- Terminate or pass through TLS according to deployment design.
- Apply Nginx connection and request rate limits.
- Keep stream service configuration independent from MQTT and web backend
  development.

## Initial Protocol

The initial config uses Nginx RTMP and exposes HTTP-FLV style pull paths through
Nginx. HLS can be added later if browser playback is required.

## Run This Service

Run streaming only from this directory:

```bash
docker compose up -d --build
docker compose logs -f streaming
```

The root `docker/docker-compose.yml` can also orchestrate this service together
with the web backend, PostgreSQL, and MQTT service.

# MQTT Rate Limiting

## Broker-Level Protection

Use EMQX built-in controls for:

- Maximum concurrent connections.
- Per-client publish rate.
- Message size limits.
- Topic authorization.
- Slow subscriber protection.

## Recommended Flow

1. Device connects to `8883` with a client certificate.
2. EMQX validates the certificate against `ca.crt`.
3. EMQX applies client and topic limits.
4. Telemetry is forwarded into Kafka or RabbitMQ.
5. Backend consumers write to PostgreSQL in controlled batches.

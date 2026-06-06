# Web Backend Surge Mitigation

## Strategy

- Keep device-facing traffic behind an mTLS gateway.
- Use Redis for hot device metadata, throttling state, and idempotency keys.
- Use Kafka or RabbitMQ to buffer telemetry writes.
- Use bounded database connection pools.
- Prefer batch writes for high-volume telemetry.

## Database Protection

- Set a strict max connection pool size per service instance.
- Reject or queue non-critical writes when the queue is saturated.
- Use idempotency keys for repeated device submissions.
- Keep audit and telemetry writes asynchronous when possible.

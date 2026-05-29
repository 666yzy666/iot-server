# Streaming Rate Limiting

## Nginx Protection

Use Nginx `limit_conn` and `limit_req` to reduce pull-stream surge impact.

Current base config:

- `limit_conn_zone $binary_remote_addr zone=stream_conn:10m`
- `limit_req_zone $binary_remote_addr zone=stream_req:10m rate=20r/s`
- `limit_conn stream_conn 10`
- `limit_req zone=stream_req burst=40 nodelay`

## Scaling Plan

- Put streaming nodes behind a load balancer.
- Keep private streams behind mTLS.
- Use short-lived signed stream URLs when browser playback is introduced.
- Monitor active sessions and reject excessive pulls before origin overload.

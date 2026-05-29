# Certificates

This folder is reserved for local development certificates.

Do not commit production private keys.

## Required Files for Local mTLS

- `ca.crt`: platform CA certificate.
- `server.crt`: server certificate for EMQX or Nginx.
- `server.key`: server private key.
- `device001.crt`: example device client certificate.
- `device001.key`: example device private key.

## Local CA Tooling

Use `certs/ca/` to generate a local CA and sign server or ESP32 device
certificates. Generated CA artifacts are written under `certs/ca/output/`.

Start here:

```bash
python -m certs.ca.ca_tool create-ca
python -m certs.ca.ca_tool sign-server --common-name localhost --dns-name localhost --ip-address 127.0.0.1
python -m certs.ca.ca_tool sign-device --device-id device001
python -m certs.ca.ca_tool install-server
```

## Mutual TLS Rule

Device-facing services must verify client certificates before accepting device
requests. Certificate subject or SAN must map to a device record managed by the
web backend.

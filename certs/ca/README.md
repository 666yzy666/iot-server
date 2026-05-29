# Local CA

This directory contains local development tooling for creating a CA and signing
server or ESP32 device certificates.

Do not commit generated private keys.

## Layout

- `ca_tool.py`: Python CA tool for creating a CA and signing certificates.

Generated output is written under `certs/ca/output/` and ignored by Git.

## Generate Local CA

Run from the repository root:

```bash
python -m certs.ca.ca_tool create-ca
```

Output:

- `certs/ca/output/ca/ca.crt`
- `certs/ca/output/ca/private/ca.key`

## Sign Server Certificate

```bash
python -m certs.ca.ca_tool sign-server --common-name localhost --dns-name localhost --ip-address 127.0.0.1
```

Output:

- `certs/ca/output/issued/server.crt`
- `certs/ca/output/private/server.key`

Copy or mount these as:

- `certs/ca/output/ca/ca.crt` -> `certs/ca.crt`
- `certs/ca/output/issued/server.crt` -> `certs/server.crt`
- `certs/ca/output/private/server.key` -> `certs/server.key`

Or run:

```bash
python -m certs.ca.ca_tool install-server
```

## Sign ESP32 Device Certificate

```bash
python -m certs.ca.ca_tool sign-device --device-id device001
```

Output:

- `certs/ca/output/issued/device001.crt`
- `certs/ca/output/private/device001.key`

Burn the following into the ESP32 firmware or secure storage:

- `ca.crt`
- `device001.crt`
- `device001.key`

Each ESP32 should use a unique device certificate.

## Python Dependency

The Python tool uses `cryptography`.

```bash
python -m pip install cryptography
```

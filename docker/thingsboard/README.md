# ThingsBoard CE

This folder contains an independent ThingsBoard Community Edition + PostgreSQL
Docker Compose stack.

It is intentionally separate from `docker/docker-compose.yml` because
ThingsBoard exposes MQTT, HTTP, and CoAP ports that overlap with the learning
stack's EMQX and Nginx services.

## Ports

- `18080`: ThingsBoard Web UI, mapped to container `8080`.
- `17070`: ThingsBoard Edge RPC, mapped to container `7070`.
- `11883`: ThingsBoard MQTT, mapped to container `1883`.
- `18884`: ThingsBoard MQTT over SSL, mapped to container `8883`.
- `15683-15688/udp`: CoAP and LwM2M, mapped to container `5683-5688/udp`.
- `15432`: PostgreSQL, mapped to container `5432`.

## First Run

Run from this directory:

```bash
docker compose run --rm -e INSTALL_TB=true -e LOAD_DEMO=true thingsboard-ce
docker compose up -d
docker compose logs -f thingsboard-ce
```

Open:

```text
http://localhost:18080
```

Default demo credentials loaded by `LOAD_DEMO=true`:

- System Administrator: `sysadmin@thingsboard.org` / `sysadmin`
- Tenant Administrator: `tenant@thingsboard.org` / `tenant`
- Customer User: `customer@thingsboard.org` / `customer`

## Stop

```bash
docker compose down
```

To remove PostgreSQL data as well:

```bash
docker compose down -v
```

## Notes

- This stack uses ThingsBoard's built-in in-memory queue, suitable for learning
  and local development.
- Use Kafka for production or clustered deployments.
- Do not expose this local demo stack directly to the public internet.

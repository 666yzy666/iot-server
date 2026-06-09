#!/usr/bin/env sh
set -eu

if [ ! -f .env ]; then
    echo "missing .env; copy .env.example to .env and set the real MySQL password" >&2
    exit 1
fi

docker compose --env-file .env build
docker compose --env-file .env up -d --build

#!/usr/bin/env sh
set -eu

retries="${DB_INIT_RETRIES:-10}"
sleep_seconds="${DB_INIT_RETRY_SECONDS:-3}"
attempt=1

while :; do
    if python -m src.init_db; then
        break
    fi

    if [ "$attempt" -ge "$retries" ]; then
        echo "database initialization failed after ${retries} attempts" >&2
        exit 1
    fi

    echo "database initialization failed, retrying in ${sleep_seconds}s (${attempt}/${retries})" >&2
    attempt=$((attempt + 1))
    sleep "$sleep_seconds"
done

exec "$@"

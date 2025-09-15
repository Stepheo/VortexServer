#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] VortexServer start"

: "${DB_MAX_RETRIES:=30}"
: "${DB_RETRY_DELAY:=2}"
: "${RUN_MIGRATIONS:=1}"
: "${WAIT_REDIS:=1}"

wait_for_postgres() {
  if [[ -z "${DATABASE_URL:-}" ]]; then
    echo "[entrypoint] DATABASE_URL not set, skipping Postgres wait"
    return 0
  fi
  if [[ "$DATABASE_URL" != postgresql* ]]; then
    echo "[entrypoint] Non-Postgres DATABASE_URL, skip Postgres wait"
    return 0
  fi
  echo "[entrypoint] Waiting for Postgres..."
  local attempt=0
  python - <<'PY'
import os,sys,asyncio,asyncpg
url=os.environ.get('DATABASE_URL')
if not url: sys.exit(0)
async def ping():
    for i in range(int(os.environ.get('DB_MAX_RETRIES','30'))):
        try:
            conn=await asyncpg.connect(dsn=url)
            await conn.close();print('[entrypoint] Postgres OK');return
        except Exception as e:
            print(f'[entrypoint] Postgres not ready ({i+1}) {e}');await asyncio.sleep(float(os.environ.get('DB_RETRY_DELAY','2')))
    print('[entrypoint] Postgres not reachable, abort');sys.exit(1)
asyncio.run(ping())
PY
}

wait_for_redis() {
  if [[ "${WAIT_REDIS}" != "1" ]]; then
    echo "[entrypoint] Redis wait disabled"
    return 0
  fi
  local url="${REDIS_URL:-redis://redis:6379/0}"
  if ! command -v python >/dev/null; then
    echo "[entrypoint] Python missing for Redis wait"; return 0
  fi
  python - <<PY
import os,asyncio,sys
import redis.asyncio as redis
url=os.environ.get('REDIS_URL','redis://redis:6379/0')
async def ping():
    r=redis.from_url(url)
    for i in range(30):
        try:
            await r.ping();print('[entrypoint] Redis OK');return
        except Exception as e:
            print(f'[entrypoint] Redis not ready ({i+1}) {e}')
            await asyncio.sleep(1)
    print('[entrypoint] Redis not reachable (continuing fail-open)')
asyncio.run(ping())
PY
}

run_migrations() {
  if [[ "${RUN_MIGRATIONS}" != "1" ]]; then
    echo "[entrypoint] RUN_MIGRATIONS=0 skip Alembic"
    return 0
  fi
  echo "[entrypoint] Running alembic upgrade head"
  alembic upgrade head || { echo "[entrypoint] Alembic failed"; exit 1; }
}

wait_for_postgres
wait_for_redis
run_migrations

echo "[entrypoint] Launching app"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers

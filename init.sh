#!/bin/bash
set -euo pipefail

echo "🚀 Iniciando Airflow en Docker..."

if ! docker info >/dev/null 2>&1; then
  echo "❌ Docker no está corriendo."
  exit 1
fi

export AIRFLOW_UID=${AIRFLOW_UID:-$(id -u)}

docker compose -f docker/docker-compose.yml up -d

echo "⏳ Esperando al webserver..."
for i in {1..40}; do
  if curl -s -I http://localhost:8080 | head -n1 | grep -qE '200|302'; then
    echo "✅ Airflow levantado en http://localhost:8080 (admin/admin)"
    exit 0
  fi
  sleep 3
done

echo "⚠️  No respondió a tiempo. Logs webserver:"
docker logs $(docker ps --format '{{.Names}}' | grep airflow-webserver | head -n1) --tail 200 || true
exit 1

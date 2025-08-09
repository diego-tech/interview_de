#!/bin/bash
set -e

echo "🚀 Iniciando Airflow en Docker..."

# Comprobar que Docker está corriendo
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker no está corriendo. Inicia Docker Desktop o el servicio de Docker."
    exit 1
fi

# Exportar UID para permisos
export AIRFLOW_UID=$(id -u)

# Levantar servicios
docker compose -f docker/docker-compose.yml up -d

echo "✅ Airflow levantado en http://localhost:8080 (usuario: admin, pass: admin)"
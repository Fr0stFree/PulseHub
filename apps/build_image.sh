#!/usr/bin/env bash

set -euo pipefail

PROJECT_NAME="pulse-hub"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_ROOT="${PROJECT_ROOT}/apps"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <service-name>"
  exit 1
fi

SERVICE_NAME="$1"
case "${SERVICE_NAME}" in
  service-api)
    SERVICE_DIR="${APP_ROOT}/service_api"
    ;;
  service-crawler)
    SERVICE_DIR="${APP_ROOT}/service_crawler"
    ;;
  service-analyzer)
    SERVICE_DIR="${APP_ROOT}/service_analyzer"
    ;;
  *)
    echo "[build][error] Unknown service name: ${SERVICE_NAME}"
    exit 1
    ;;
esac

echo "[build] Starting build for service: ${SERVICE_NAME}..."
DOCKERFILE_PATH="${SERVICE_DIR}/Dockerfile"

if [[ ! -f "${DOCKERFILE_PATH}" ]]; then
    echo "[build][error] Dockerfile not found for service '${SERVICE_NAME}' at path: ${DOCKERFILE_PATH}"
    exit 1
fi

eval $(minikube -p minikube docker-env)
echo "[build] Building Docker image for service '${SERVICE_NAME}' using Dockerfile at: ${DOCKERFILE_PATH}"
docker build -t "${PROJECT_NAME}/${SERVICE_NAME}:latest" -f "${DOCKERFILE_PATH}" "${APP_ROOT}"
echo "[build] Successfully built image '${PROJECT_NAME}/${SERVICE_NAME}:latest'"

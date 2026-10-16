#!/usr/bin/env bash
# One-command launcher for the CCPIP platform.
#
#   ./run.sh          start everything, wait for the pipeline, print the URL
#   ./run.sh down     stop and remove containers + data
#   ./run.sh logs     follow the web + pipeline logs
set -euo pipefail

cd "$(dirname "$0")"
CMD="${1:-up}"

case "$CMD" in
  down)
    echo "Stopping CCPIP ..."
    docker compose down -v
    echo "Done."
    ;;
  logs)
    docker compose logs -f web pipeline
    ;;
  up|*)
    if ! command -v docker >/dev/null 2>&1; then
      echo "ERROR: docker is not installed." >&2; exit 1
    fi
    if ! docker info >/dev/null 2>&1; then
      echo "ERROR: docker daemon is not running." >&2; exit 1
    fi

    [ -f .env ] || cp .env.example .env
    WEB_PORT="$(grep -E '^WEB_PORT=' .env | cut -d= -f2)"
    WEB_PORT="${WEB_PORT:-8080}"

    echo "Building image (first run takes a few minutes) ..."
    # Use the docker CLI directly with host networking: Docker's embedded DNS
    # fails on some hosts, and BuildKit (via compose) refuses network:host.
    docker build --network=host -t platform-app:latest . >/dev/null

    echo "Starting database, API and web UI ..."
    docker compose up -d db ingestion web

    echo "Waiting for the database ..."
    for _ in $(seq 1 60); do
      docker compose exec -T db pg_isready -U ccpip >/dev/null 2>&1 && break
      sleep 1
    done

    echo "Running the data pipeline (generate -> ingest -> EVM -> train -> score) ..."
    docker compose up -d pipeline
    # 'ps -aq' includes exited containers; 'ps -q' would go empty once it exits.
    for _ in $(seq 1 300); do
      cid=$(docker compose ps -aq pipeline 2>/dev/null)
      state=$(docker inspect -f '{{.State.Status}}' "$cid" 2>/dev/null || echo unknown)
      [ "$state" = "exited" ] && break
      sleep 2
    done

    echo ""
    echo "==================================================================="
    echo "  CCPIP is running. Open the dashboard:"
    echo ""
    echo "      http://localhost:${WEB_PORT}"
    echo ""
    echo "  Stop:  ./run.sh down"
    echo "  Logs:  ./run.sh logs"
    echo "==================================================================="
    ;;
esac

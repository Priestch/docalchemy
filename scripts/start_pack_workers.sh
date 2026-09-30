#!/bin/bash
# Start all pack workers for dockerized providers
# Usage: ./scripts/start_pack_workers.sh

set -e

# Configuration
export STORAGE_HOST_ROOT="${STORAGE_HOST_ROOT:-/home/gaopeng/localstorage/docalchemy}"
export STORAGE_PROVIDER_ROOT="${STORAGE_PROVIDER_ROOT:-/storage}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
CELERY="$PROJECT_ROOT/.venv/bin/celery"
export PYTHONPATH="$PROJECT_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
mkdir -p "$PROJECT_ROOT/logs"

echo "Starting pack workers with storage mapping:"
echo "  Host:      $STORAGE_HOST_ROOT"
echo "  Provider:  $STORAGE_PROVIDER_ROOT"
echo ""

# Start workers in background
WORKERS=(
    "docling:http://localhost:8081:analysis.docling"
    "mineru:http://localhost:8082:analysis.mineru"
    "opendataloader:http://localhost:8083:analysis.opendataloader"
    "franken_ocr:http://localhost:8084:analysis.franken_ocr"
)

for worker_spec in "${WORKERS[@]}"; do
    IFS=':' read -r pack_id provider_url queue <<< "$worker_spec"

    echo "Starting $pack_id worker..."
    PACK_ID="$pack_id" \
    PROVIDER_URL="$provider_url" \
    PACK_QUEUE="$queue" \
    "$CELERY" -A app.infrastructure.workers.pack_worker worker \
        --loglevel=info \
        --concurrency=1 \
        --hostname="${pack_id}@%h" \
        > "$PROJECT_ROOT/logs/worker_${pack_id}.log" 2>&1 &

    echo "  → PID: $! (logs: logs/worker_${pack_id}.log)"
done

echo ""
echo "All workers started!"
echo "To stop: pkill -f 'celery.*pack_worker'"
echo "To view logs: tail -f logs/worker_*.log"

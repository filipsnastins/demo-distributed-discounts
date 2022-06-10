#!/bin/bash
set -euo pipefail

if [ $ENV = "development" ]; then
    echo "docker-entrypoint (development mode): initializing data..."
    python scripts/initial_data.py
fi

exec "$@"

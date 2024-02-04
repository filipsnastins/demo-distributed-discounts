#!/bin/bash
set -euo pipefail

echo "docker-entrypoint: initializing test data..."
python scripts/initial_data.py

exec "$@"

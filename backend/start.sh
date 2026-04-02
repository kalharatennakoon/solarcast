#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "Starting backend at http://localhost:8000"
echo "API docs at  http://localhost:8000/docs"

../.venv/bin/uvicorn api.main:app --host 0.0.0.0 --reload

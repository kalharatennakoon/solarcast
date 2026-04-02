#!/bin/bash
set -e

# Always run from the backend/ directory regardless of where the script is called from
cd "$(dirname "$0")"

# Create virtual environment only if it doesn't exist yet
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

# Install / update dependencies (skips already-installed packages)
echo "Checking dependencies..."
venv/bin/pip install -r requirements.txt --quiet

# Start the FastAPI server
echo "Starting backend at http://localhost:8000"
echo "API docs at  http://localhost:8000/docs"
venv/bin/uvicorn api.main:app --reload

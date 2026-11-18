#!/bin/bash
echo "=================================================================="
echo "  Automated Human Activity Change Detection System"
echo "  FastAPI Backend & Satellite Telemetry Dashboard"
echo "=================================================================="

# Navigate to the project root (directory of this script)
cd "$(dirname "$0")"

# Activate the virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "-> Virtual environment activated."
else
    echo "[WARNING] No venv found. Running with system Python."
fi

echo "-> Server running at: http://localhost:8000"
echo "-> API Documentation: http://localhost:8000/docs"
echo "=================================================================="

python run.py

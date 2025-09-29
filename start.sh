#!/bin/bash
# Start script for deployment platforms
PORT=${PORT:-8000}
echo "Starting County Health Data API on port $PORT"
python -m uvicorn main:app --host 0.0.0.0 --port $PORT
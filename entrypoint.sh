#!/bin/sh
echo "Seeding database..."
python seed.py
echo "Starting API..."
exec uvicorn api.mainapi:app --host 0.0.0.0 --port 8000
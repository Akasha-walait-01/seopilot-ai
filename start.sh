#!/bin/bash

echo "Starting FastAPI backend..."

uvicorn backend.main:app \
    --host 127.0.0.1 \
    --port 8000 &

BACKEND_PID=$!

echo "Backend started with PID $BACKEND_PID"

sleep 5

echo "Starting Streamlit frontend..."

streamlit run frontend/app.py \
    --server.address 0.0.0.0 \
    --server.port 7860 \
    --server.headless true
#!/usr/bin/env bash
set -e

# Start API in background
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Start Streamlit (foreground)
streamlit run frontend/app.py \
    --server.port 8501 \
    --server.headless true \
    --server.address 0.0.0.0

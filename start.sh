#!/usr/bin/env bash
set -e

# Contract Template Manager — start script

API_PORT=8000
STREAMLIT_PORT=8501

cleanup() {
    echo ""
    echo "Shutting down..."
    kill "$API_PID" "$STREAMLIT_PID" 2>/dev/null || true
    # Give processes up to 5 seconds to exit gracefully
    for i in $(seq 1 10); do
        kill -0 "$API_PID" 2>/dev/null || kill -0 "$STREAMLIT_PID" 2>/dev/null || break
        sleep 0.5
    done
    # Force-kill any survivors
    kill -9 "$API_PID" "$STREAMLIT_PID" 2>/dev/null || true
    wait "$API_PID" "$STREAMLIT_PID" 2>/dev/null || true
    echo "Done."
}
trap cleanup EXIT INT TERM

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "Error: Python 3 is required. Install it from https://python.org"
    exit 1
fi

PYTHON=$(command -v python3)
PY_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Using Python $PY_VERSION ($PYTHON)"

# Create venv if needed
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv .venv
fi

source .venv/bin/activate

# Install deps
echo "Installing dependencies..."
pip install -q -e ".[dev]"

# Create data directories
mkdir -p data

# Start API
echo "Starting API on port $API_PORT..."
uvicorn ctm_app.main:app --host 0.0.0.0 --port "$API_PORT" &
API_PID=$!

# Wait for API to be ready
echo "Waiting for API..."
for i in $(seq 1 30); do
    if curl -sf "http://localhost:$API_PORT/api/health" >/dev/null 2>&1; then
        echo "API is ready."
        break
    fi
    sleep 1
done

# Start Streamlit
echo "Starting Streamlit on port $STREAMLIT_PORT..."
streamlit run ctm_frontend/app.py --server.port "$STREAMLIT_PORT" --server.headless true &
STREAMLIT_PID=$!

sleep 2

echo ""
echo "============================================"
echo "  Contract Template Manager is running!"
echo "  API:      http://localhost:$API_PORT/docs"
echo "  Frontend: http://localhost:$STREAMLIT_PORT"
echo "  Press Ctrl+C to stop"
echo "============================================"
echo ""

# Open browser
if command -v open &>/dev/null; then
    open "http://localhost:$STREAMLIT_PORT"
elif command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:$STREAMLIT_PORT"
fi

# Wait for either process to exit
wait

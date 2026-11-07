#!/usr/bin/env bash
# ==============================================================================
# CropNet AI — Local Prototype Startup Script
# ==============================================================================
# Starts all components required to run the CropNet AI prototype locally:
# 1. Verifies local Ollama instance & Qwen3:8B model
# 2. Starts local FastAPI backend on http://127.0.0.1:8000
# 3. Starts local Flutter Web client on http://localhost:8080
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "======================================================================"
echo "  🌱 CropNet AI — Local Prototype Environment Launcher"
echo "======================================================================"

# 1. Check Ollama
echo "[1/3] Checking local Ollama service (127.0.0.1:11434)..."
if curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
    echo "  ✓ Ollama server is running."
    if curl -s http://127.0.0.1:11434/api/tags | grep -q "qwen3:8b"; then
        echo "  ✓ Model 'qwen3:8b' is installed and ready."
    else
        echo "  ⚠ Model 'qwen3:8b' not found in Ollama. Pulling model..."
        ollama pull qwen3:8b
    fi
else
    echo "  ✗ Ollama is not running on http://127.0.0.1:11434."
    echo "    Please launch Ollama (e.g. open /Applications/Ollama.app) and rerun."
    exit 1
fi

# 2. Check / Launch FastAPI
echo "[2/3] Starting FastAPI backend on http://127.0.0.1:8000..."
if curl -s http://127.0.0.1:8000/api/v1/health > /dev/null 2>&1; then
    echo "  ✓ FastAPI backend is already running on port 8000."
else
    cd "${ROOT_DIR}"
    python3 -m uvicorn cropnet.services.api.app.main:app --host 127.0.0.1 --port 8000 --reload &
    FASTAPI_PID=$!
    echo "  ✓ FastAPI started (PID: ${FASTAPI_PID}). Waiting for health check..."
    
    # Wait for health check
    for i in {1..30}; do
        if curl -s http://127.0.0.1:8000/api/v1/health > /dev/null 2>&1; then
            echo "  ✓ FastAPI health check passed."
            break
        fi
        sleep 1
    done
fi

# 3. Launch Flutter Web
echo "[3/3] Starting Flutter Web on Chrome (http://localhost:8080)..."
cd "${ROOT_DIR}/apps/mobile"

echo "----------------------------------------------------------------------"
echo "  CropNet AI Prototype Running!"
echo "  • Flutter Web UI:   http://localhost:8080"
echo "  • FastAPI API:      http://127.0.0.1:8000/api/v1"
echo "  • API Docs (Swagger): http://127.0.0.1:8000/api/v1/docs"
echo "  • Local Ollama:     http://127.0.0.1:11434 (qwen3:8b)"
echo "----------------------------------------------------------------------"

flutter run -d chrome --web-port=8080 --web-hostname=localhost

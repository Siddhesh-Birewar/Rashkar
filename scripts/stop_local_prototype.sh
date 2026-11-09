#!/usr/bin/env bash
# ==============================================================================
# CropNet AI — Local Prototype Shutdown Script
# ==============================================================================
# Gracefully stops local background processes associated with CropNet AI:
# - FastAPI backend on port 8000
# - Flutter Web / HTTP server on port 8080
# ==============================================================================

echo "======================================================================"
echo "  🛑 CropNet AI — Stopping Local Prototype Services"
echo "======================================================================"

# 1. Stop FastAPI on port 8000
PID_8000=$(lsof -ti:8000 2>/dev/null || true)
if [ -n "$PID_8000" ]; then
    echo "  → Terminating FastAPI process on port 8000 (PID: $PID_8000)..."
    kill -15 $PID_8000 2>/dev/null || true
    sleep 1
    # Force kill if still lingering
    if kill -0 $PID_8000 2>/dev/null; then
        kill -9 $PID_8000 2>/dev/null || true
    fi
    echo "  ✓ Port 8000 released."
else
    echo "  ✓ No process occupying port 8000."
fi

# 2. Stop Flutter Web / HTTP server on port 8080
PID_8080=$(lsof -ti:8080 2>/dev/null || true)
if [ -n "$PID_8080" ]; then
    echo "  → Terminating web server process on port 8080 (PID: $PID_8080)..."
    kill -15 $PID_8080 2>/dev/null || true
    sleep 1
    if kill -0 $PID_8080 2>/dev/null; then
        kill -9 $PID_8080 2>/dev/null || true
    fi
    echo "  ✓ Port 8080 released."
else
    echo "  ✓ No process occupying port 8080."
fi

echo "======================================================================"
echo "  ✓ All CropNet AI prototype services stopped cleanly."
echo "======================================================================"

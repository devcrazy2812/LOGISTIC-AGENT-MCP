#!/usr/bin/env bash
# ==============================================================================
# LogiSwarm AI - Autonomous Multi-Agent Logistics Engine Launcher
# Platform: Linux / macOS / WSL
# ==============================================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

# Locate python3 or python
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "[!] Error: Python 3.9+ is required but was not found on PATH." >&2
    exit 1
fi

# Detect virtual environment if present
if [ -d ".venv" ]; then
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        PYTHON_CMD="python"
    elif [ -f ".venv/Scripts/activate" ]; then
        source .venv/Scripts/activate
        PYTHON_CMD="python"
    fi
fi

echo "[*] Launching LogiSwarm AI Logistics Server..."
exec $PYTHON_CMD run.py "$@"

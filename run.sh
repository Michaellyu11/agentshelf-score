#!/bin/bash
# AgentShelf Score Experiment - Quick Start
# ==========================================
#
# Before running:
# 1. cp .env.example .env
# 2. Edit .env with your real API keys
# 3. pip install httpx pydantic-settings python-dotenv google-genai
# 4. Run this script
#
# Usage:
#   ./run.sh test     # Test all 5 engines (5 calls, ~$0.25)
#   ./run.sh quarter  # 1/4 data (900 calls, ~$40, ~1 hour)
#   ./run.sh half     # 1/2 data (1500 calls, ~$68, ~2 hours)  
#   ./run.sh full     # Full experiment (3000 calls, ~$135, ~4 hours)

set -e
cd "$(dirname "$0")"

if [ ! -f .env ]; then
    echo "ERROR: No .env file found!"
    echo "Run: cp .env.example .env"
    echo "Then edit .env with your API keys."
    exit 1
fi

case "${1:-test}" in
    test)
        echo "Running TEST mode (5 calls, ~\$0.25)..."
        python -m app.run_experiment --test
        ;;
    quarter)
        echo "Running 1/4 experiment (900 calls, ~\$40)..."
        python -m app.run_experiment --full --reps 3
        ;;
    half)
        echo "Running 1/2 experiment (1500 calls, ~\$68)..."
        python -m app.run_experiment --full --reps 5
        ;;
    full)
        echo "Running FULL experiment (3000 calls, ~\$135)..."
        python -m app.run_experiment --full
        ;;
    *)
        echo "Usage: ./run.sh [test|quarter|half|full]"
        exit 1
        ;;
esac

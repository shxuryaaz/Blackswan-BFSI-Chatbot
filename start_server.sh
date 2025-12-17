#!/bin/bash

# Horizon Finance - AI Loan Assistant Server Startup Script

# Navigate to project directory
cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

# Set OpenAI API Key (replace with your key or use environment variable)
export OPENAI_API_KEY="${OPENAI_API_KEY:-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}"

# Set port (default 8000, can be overridden with PORT environment variable)
PORT=${PORT:-8000}

# Start the server
echo "Starting Horizon Finance AI Loan Assistant..."
echo "Server will be available at: http://localhost:${PORT}"
echo "API Health Check: http://localhost:${PORT}/api/health"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

uvicorn backend.main:app --host 0.0.0.0 --port $PORT


#!/bin/bash

# Ensure we are in the project root
cd "$(dirname "$0")"

echo "📍 Current Directory: $(pwd)"

# Check if .venv exists, if so activate it
if [ -d ".venv" ]; then
    echo "🔌 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️  No .venv found. Using system python/pip (or active environment)."
fi

# Install dependencies if needed (quietly)
echo "📦 Checking dependencies..."
pip install -r backend/requirements.txt || echo "⚠️  Warning during pip install"

# Run the app
echo "🚀 Starting LifeXia..."
export FLASK_ENV=development
python3 -m backend.app

#!/bin/bash
# Script to run LifeXia Backend

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Python
if ! command_exists python3; then
    echo "Error: Python 3 is not installed."
    exit 1
fi

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# Install dependencies if needed
if [ -f "backend/requirements.txt" ]; then
    echo "Checking dependencies..."
    pip install -r backend/requirements.txt
else
    echo "Error: backend/requirements.txt not found."
    exit 1
fi

# Kill any existing process on port 5000
echo "Cleaning up port 5000..."
fuser -k 5000/tcp >/dev/null 2>&1

# Run the application
echo "Starting LifeXia Backend..."
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 -m backend.app

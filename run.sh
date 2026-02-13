#!/bin/bash

echo "🏥 Starting LIFEXIA Healthcare Chatbot..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source ~/ai_env/bin/activate
fi

# Set environment variables
export FLASK_APP=backend/app.py
export FLASK_ENV=development

# Create necessary directories
mkdir -p data/uploads logs flask_session

# Run the application
python backend/app.py
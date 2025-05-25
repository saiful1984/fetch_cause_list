#!/bin/bash

# High Court Cause List API Startup Script

echo "🚀 Starting High Court Cause List API..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Set default environment variables if not set
export API_KEY=${API_KEY:-"your-secret-api-key-here"}
export PORT=${PORT:-5001}
export FLASK_DEBUG=${FLASK_DEBUG:-"False"}

echo "🔑 API Key: ${API_KEY}"
echo "🌐 Port: ${PORT}"
echo "🐛 Debug Mode: ${FLASK_DEBUG}"

# Start the Flask application
echo "🎯 Starting Flask application..."
python app.py

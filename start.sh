#!/bin/bash

echo "Starting BinBot Inventory System..."

# Check if required environment variables are set
if [ -z "$OPENAI_API_KEY" ] && [ -z "$GEMINI_API_KEY" ]; then
    echo "Warning: No LLM API keys found. Set OPENAI_API_KEY or GEMINI_API_KEY environment variable."
    echo "The system will start but LLM functionality will be limited."
fi

# Validate configuration file exists
if [ ! -f "config.yaml" ]; then
    echo "Error: config.yaml not found!"
    exit 1
fi

echo "Configuration file found."

# Create data directories if they don't exist
mkdir -p /app/data/chromadb
mkdir -p /app/data/images

echo "Data directories ready."

# Start the FastAPI application
echo "Starting FastAPI server..."
exec python app.py

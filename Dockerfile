# Use Python 3.11 as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY config.yaml .
COPY api_schemas.py .
COPY frontend/ ./frontend/
COPY start.sh .

# Copy modular code structure
COPY config/ ./config/
COPY database/ ./database/
COPY llm/ ./llm/
COPY api/ ./api/
COPY session/ ./session/

# Make start script executable
RUN chmod +x start.sh

# Create data directory for ChromaDB persistence
RUN mkdir -p /app/data/chromadb

# Create directory for image storage
RUN mkdir -p /app/data/images

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Use start script as entry point
CMD ["./start.sh"]

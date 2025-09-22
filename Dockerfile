FROM python:3.12-slim

WORKDIR /app

# Install Node.js (using NodeSource for current 18.x version, better than apt's outdated version)
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install uv

# Copy dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Copy app
COPY . .

# Build frontend
RUN cd frontend && npm install && npm run build

EXPOSE 8000
CMD ["uv", "run", "python", "run_prod.py"]

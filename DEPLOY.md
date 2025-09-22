# BinBot Docker Deployment

## Quick Start

1. Set up environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

2. Run with Docker Compose:
```bash
docker-compose up --build
```

3. Access at http://localhost:8000

## Portainer Stack

Copy this into Portainer stack editor:

```yaml
version: '3.8'
services:
  binbot:
    image: your-registry/binbot:latest
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=your-key-here
      - OPENAI_API_KEY=your-key-here
    volumes:
      - binbot_data:/app/data
volumes:
  binbot_data:
```

## Build and Push

```bash
docker build -t binbot .
docker tag binbot your-registry/binbot:latest
docker push your-registry/binbot:latest
```

That's it!

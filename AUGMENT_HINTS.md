# Augment Development Hints for BinBot

This document provides quick reference hints for working with the BinBot inventory system during development with Augment.

## 🚀 Starting the Server

### Basic Startup
```bash
docker-compose --env-file .env up
```

### With Rebuild (when code changes)
```bash
docker-compose --env-file .env up --build
```

### Background Mode
```bash
docker-compose --env-file .env up -d
```

## 🔄 When to Rebuild

**Always rebuild when you change:**
- Python source code files (`.py`)
- Dependencies in `requirements.txt`
- Docker configuration files
- Any files copied into the container

**No rebuild needed for:**
- Environment variables in `.env` (just restart)
- Data files (they're mounted as volumes)

## ✅ Testing Server Health

### Quick Health Check
- server startup is fast.  A 2 second sleep is enough
```bash
curl -s http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-18T12:38:04.123456",
  "services": {
    "database": "connected",
    "llm": "available",
    "vision": "available"
  }
}
```

### Check Container Status
```bash
docker ps
```

### View Logs
```bash
docker-compose logs -f
```

## 🧪 API Testing Examples

### Text-Only Command
```bash
curl -X POST http://localhost:8000/nlp/command \
  -H "Content-Type: application/json" \
  -d '{"command": "add hammer to bin 5", "session_id": "test-session"}'
```

### Image Upload Command
```python
import requests
from PIL import Image, ImageDraw
import io

# Create test image
img = Image.new('RGB', (200, 200), color='white')
draw = ImageDraw.Draw(img)
draw.rectangle([50, 50, 150, 100], fill='red', outline='black')
draw.text((60, 65), 'Hammer', fill='black')

# Save to bytes
img_bytes = io.BytesIO()
img.save(img_bytes, format='JPEG')
img_bytes.seek(0)

# Test upload
files = {'image': ('test.jpg', img_bytes, 'image/jpeg')}
data = {'command': 'add these items to bin 9', 'session_id': 'test-session'}

response = requests.post('http://localhost:8000/nlp/upload-image', files=files, data=data)
print(response.json())
```

## 🐛 Common Issues & Solutions

### Container Won't Start
1. Check for syntax errors in Python files
2. Verify `.env` file exists and has required variables
3. Check Docker logs: `docker-compose logs`

### Code Changes Not Reflected
1. **Always rebuild** after code changes: `docker-compose --env-file .env up --build`
2. Check if files are properly copied in Dockerfile

### API Returns 500 Errors
1. Check container logs for Python exceptions
2. Verify all services initialized (database, LLM, vision)
3. Check `.env` file has all required API keys

### Vision Service Issues
1. Ensure `OPENAI_API_KEY` is set in `.env`
2. Check image file size (max 10MB)
3. Verify image format is supported (JPEG, PNG)

## 📁 Key Files to Watch

- **`api/nlp.py`** - Main API endpoints
- **`nlp/function_command_processor.py`** - Command processing logic
- **`nlp/function_handler.py`** - Function execution
- **`nlp/function_definitions.py`** - LLM function schemas
- **`.env`** - Environment variables (API keys, etc.)
- **`docker-compose.yml`** - Container configuration

## 🔧 Development Workflow

1. **Make code changes**
2. **Rebuild container**: `docker-compose --env-file .env up --build`
3. **Wait for startup** (look for "Uvicorn running on http://0.0.0.0:8000")
4. **Test health**: `curl -s http://localhost:8000/health`
5. **Test functionality** with API calls
6. **Check logs** if issues: `docker-compose logs -f`

## 📊 Monitoring

### Real-time Logs
```bash
docker-compose logs -f binbot
```

### Database Status
The health endpoint shows database connection status. ChromaDB logs will show collection operations.

### LLM Usage
OpenAI API calls are logged with request/response details when debug logging is enabled.

## 🎯 Quick Test Commands

```bash
# Health check
curl -s http://localhost:8000/health

# Simple command test
curl -X POST http://localhost:8000/nlp/command \
  -H "Content-Type: application/json" \
  -d '{"command": "what is in bin 1?"}'

# List all containers
docker ps

# Restart without rebuild
docker-compose --env-file .env restart

# Stop all containers
docker-compose down

# View container resource usage
docker stats
```

## 💡 Pro Tips

- **Always use `--env-file .env`** with docker-compose commands
- **Rebuild after every code change** - Docker caching can cause issues
- **Check logs first** when debugging - most issues show up there
- **Use unique session IDs** when testing to avoid conversation conflicts
- **Test both endpoints**: `/command` for text-only, `/upload-image` for images
- **Monitor ChromaDB logs** for database operation insights

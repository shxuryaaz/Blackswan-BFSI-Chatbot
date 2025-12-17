# Deployment Guide - Horizon Finance AI Loan Assistant

## Local Development

### Quick Start

1. **Install dependencies:**
   ```bash
   # Using uv (recommended)
   uv sync
   
   # OR using pip
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export OPENAI_API_KEY="your_openai_api_key_here"
   ```

3. **Start the server:**
   ```bash
   # Option 1: Using the startup script
   chmod +x start_server.sh
   ./start_server.sh
   
   # Option 2: Using uvicorn directly
   source .venv/bin/activate
   uvicorn backend.main:app --host 0.0.0.0 --port 8000
   
   # Option 3: Using Python directly
   source .venv/bin/activate
   python backend/main.py
   ```

4. **Access the application:**
   - Frontend: http://localhost:8000
   - API Health: http://localhost:8000/api/health
   - API Docs: http://localhost:8000/docs (FastAPI auto-generated)

---

## Deployment Options

### Option 1: Render.com (Recommended for Quick Deployment)

**Steps:**

1. **Create a Render account** at https://render.com

2. **Create a new Web Service:**
   - Connect your GitHub repository
   - Or use Render's manual deploy

3. **Configure the service:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Environment:** Python 3
   - **Python Version:** 3.11 or higher

4. **Set Environment Variables:**
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `PORT`: (Optional, Render sets this automatically)

5. **Deploy!**

**Render Configuration File** (create `render.yaml`):
```yaml
services:
  - type: web
    name: horizon-finance-ai
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: OPENAI_API_KEY
        sync: false
    healthCheckPath: /api/health
```

---

### Option 2: Railway.app

**Steps:**

1. **Create a Railway account** at https://railway.app

2. **Create a new project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo" or "Empty Project"

3. **Configure:**
   - Railway auto-detects Python projects
   - Add environment variable: `OPENAI_API_KEY`

4. **Create `Procfile`:**
   ```
   web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```

5. **Deploy!**

---

### Option 3: Fly.io

**Steps:**

1. **Install Fly CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login:**
   ```bash
   fly auth login
   ```

3. **Initialize Fly:**
   ```bash
   fly launch
   ```

4. **Set secrets:**
   ```bash
   fly secrets set OPENAI_API_KEY="your_key_here"
   ```

5. **Deploy:**
   ```bash
   fly deploy
   ```

**Create `fly.toml`:**
```toml
app = "horizon-finance-ai"
primary_region = "iad"

[build]

[env]
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]

[[services]]
  http_checks = []
  internal_port = 8080
  processes = ["app"]
  protocol = "tcp"
  script_checks = []

[[services.ports]]
  handlers = ["http"]
  port = 80

[[services.ports]]
  handlers = ["tls", "http"]
  port = 443
```

---

### Option 4: AWS (EC2 / Elastic Beanstalk)

**Using Elastic Beanstalk (Easiest):**

1. **Install EB CLI:**
   ```bash
   pip install awsebcli
   ```

2. **Initialize:**
   ```bash
   eb init -p python-3.11 horizon-finance-ai
   ```

3. **Create environment:**
   ```bash
   eb create horizon-finance-env
   ```

4. **Set environment variables:**
   ```bash
   eb setenv OPENAI_API_KEY="your_key_here"
   ```

5. **Deploy:**
   ```bash
   eb deploy
   ```

**Using EC2 (Manual):**

1. Launch EC2 instance (Ubuntu)
2. SSH into instance
3. Install Python, pip, and dependencies
4. Use systemd or PM2 to run as service
5. Configure nginx as reverse proxy

---

### Option 5: Google Cloud Run

**Steps:**

1. **Install gcloud CLI**

2. **Create Dockerfile** (see below)

3. **Build and deploy:**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT-ID/horizon-finance-ai
   gcloud run deploy horizon-finance-ai \
     --image gcr.io/PROJECT-ID/horizon-finance-ai \
     --platform managed \
     --region us-central1 \
     --set-env-vars OPENAI_API_KEY="your_key_here"
   ```

---

### Option 6: DigitalOcean App Platform

**Steps:**

1. **Create account** at https://cloud.digitalocean.com

2. **Create App:**
   - Connect GitHub repo
   - Select Python
   - Build command: `pip install -r requirements.txt`
   - Run command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

3. **Set environment variables:**
   - `OPENAI_API_KEY`

4. **Deploy!**

---

## Docker Deployment

### Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for generated letters
RUN mkdir -p generated_letters

# Expose port
EXPOSE 8000

# Set environment variables
ENV PORT=8000

# Run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build and Run Docker Container

```bash
# Build image
docker build -t horizon-finance-ai .

# Run container
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY="your_key_here" \
  --name horizon-finance \
  horizon-finance-ai
```

### Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./generated_letters:/app/generated_letters
    restart: unless-stopped
```

Run: `docker-compose up -d`

---

## Environment Variables

Required:
- `OPENAI_API_KEY`: Your OpenAI API key

Optional:
- `PORT`: Server port (default: 8000)
- `HOST`: Server host (default: 0.0.0.0)

---

## Production Considerations

### Security Improvements Needed:

1. **CORS Configuration:**
   - Update `backend/main.py` to restrict CORS origins
   - Change `allow_origins=["*"]` to specific domains

2. **Rate Limiting:**
   - Add rate limiting middleware
   - Install: `pip install slowapi`
   - Configure limits per IP

3. **Authentication:**
   - Add JWT or OAuth authentication
   - Protect API endpoints

4. **Database:**
   - Replace in-memory state with database (PostgreSQL/MongoDB)
   - Add session persistence

5. **Logging:**
   - Add structured logging
   - Set up log aggregation

6. **Monitoring:**
   - Add health checks
   - Set up error tracking (Sentry)
   - Monitor API usage

---

## Quick Commands Reference

```bash
# Local development
./start_server.sh

# Using uvicorn directly
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Production (with multiple workers)
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4

# Check if server is running
curl http://localhost:8000/api/health

# View logs
tail -f logs/app.log  # if logging is configured
```

---

## Troubleshooting

**Port already in use:**
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
PORT=8080 ./start_server.sh
```

**OpenAI API errors:**
- Verify API key is set correctly
- Check API key has sufficient credits
- Verify network connectivity

**Import errors:**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`
- Check Python version (requires 3.11+)


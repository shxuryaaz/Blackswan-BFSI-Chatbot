# Quick Deployment Guide

## 🚀 Option 1: Render.com (Easiest - 5 minutes)

### Steps:

1. **Push your code to GitHub** (if not already):
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Go to Render.com:**
   - Visit https://render.com
   - Sign up/Login (free tier available)

3. **Create New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your repository

4. **Configure:**
   - **Name:** `horizon-finance-ai` (or any name)
   - **Region:** Choose closest to you
   - **Branch:** `main` (or your branch)
   - **Root Directory:** Leave empty (or `.` if needed)
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

5. **Add Environment Variable:**
   - Click "Advanced" → "Add Environment Variable"
   - **Key:** `OPENAI_API_KEY`
   - **Value:** Your OpenAI API key (the one you're using)

6. **Deploy:**
   - Click "Create Web Service"
   - Wait 2-3 minutes for build
   - Your app will be live at: `https://your-app-name.onrender.com`

---

## 🚂 Option 2: Railway.app (Also Easy)

### Steps:

1. **Go to Railway:**
   - Visit https://railway.app
   - Sign up/Login (free tier available)

2. **Create New Project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure:**
   - Railway auto-detects Python
   - It will use your `Procfile` automatically

4. **Add Environment Variable:**
   - Go to "Variables" tab
   - Add: `OPENAI_API_KEY` = Your API key

5. **Deploy:**
   - Railway auto-deploys on git push
   - Your app will be live at: `https://your-app-name.up.railway.app`

---

## 🐳 Option 3: Docker (Local or Cloud)

### Local Docker:

```bash
# Build the image
docker build -t horizon-finance-ai .

# Run the container
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY="your_key_here" \
  --name horizon-finance \
  horizon-finance-ai

# Access at http://localhost:8000
```

### Docker Compose:

```bash
# Set your API key
export OPENAI_API_KEY="your_key_here"

# Start
docker-compose up -d

# Stop
docker-compose down
```

---

## ✅ After Deployment

1. **Test your app:**
   - Visit your deployed URL
   - Check health: `https://your-url.com/api/health`

2. **Monitor logs:**
   - Render: Go to "Logs" tab
   - Railway: Go to "Deployments" → View logs

3. **Update your app:**
   - Just push to GitHub
   - Render/Railway auto-deploys

---

## 🔧 Troubleshooting

**Build fails:**
- Check that `requirements.txt` is correct
- Verify Python version (3.11+)

**App crashes:**
- Check logs for errors
- Verify `OPENAI_API_KEY` is set correctly
- Make sure port is `$PORT` (not hardcoded 8000)

**Can't access:**
- Wait 1-2 minutes after deployment
- Check health endpoint first
- Verify environment variables are set

---

## 📝 Notes

- **Free tiers:** Render and Railway both offer free tiers (with limitations)
- **Auto-deploy:** Both platforms auto-deploy on git push
- **Environment variables:** Keep your `OPENAI_API_KEY` secret!
- **Custom domain:** Both platforms allow custom domains (paid feature)


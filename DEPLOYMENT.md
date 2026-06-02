# 🚀 Deployment Guide - Render.com

This guide will walk you through deploying the Football Stats Web App to Render.com.

## 📋 Prerequisites

Before you begin, make sure you have:

1. A [GitHub account](https://github.com) with this repository
2. A [Render account](https://render.com) (free tier available)
3. An API-Football API key from [RapidAPI](https://rapidapi.com/api-sports/api/api-football)

## 🎯 Deployment Options

### Option 1: Blueprint Deployment (Recommended - Easiest)

This method uses the `render.yaml` file to automatically set up all services.

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Create Blueprint on Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Blueprint"
   - Connect your GitHub account if not already connected
   - Select the `footballwebapp` repository
   - Render will detect the `render.yaml` file automatically

3. **Configure Environment Variables**
   - In the blueprint setup, you'll need to manually set:
     - `API_KEY`: Your API-Football key from RapidAPI
   - Other variables are auto-configured from `render.yaml`

4. **Deploy**
   - Click "Apply" to create all services
   - Render will:
     - Create PostgreSQL database
     - Create Redis instance
     - Deploy web service
     - Connect everything automatically

5. **Wait for deployment** (5-10 minutes for first deploy)

6. **Access your app**
   - Once deployed, you'll get a URL like: `https://football-webapp.onrender.com`

### Option 2: Manual Deployment (More Control)

If you prefer to set up services individually:

#### Step 1: Create PostgreSQL Database

1. From Render Dashboard, click "New +" → "PostgreSQL"
2. Configure:
   - **Name**: `football-db`
   - **Database**: `football_db`
   - **User**: `football_user`
   - **Region**: Choose closest to your users
   - **Plan**: Free (or Starter for production)
3. Click "Create Database"
4. Save the **Internal Database URL** (starts with `postgres://`)

#### Step 2: Create Redis Instance

1. Click "New +" → "Redis"
2. Configure:
   - **Name**: `football-redis`
   - **Region**: Same as database
   - **Plan**: Free (or Starter for production)
   - **Maxmemory Policy**: `allkeys-lru`
3. Click "Create Redis"
4. Save the **Internal Redis URL**

#### Step 3: Deploy Web Service

1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `football-webapp`
   - **Region**: Same as database and Redis
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --config gunicorn_config.py app:app`
   - **Plan**: Free (or Starter for production)

4. **Add Environment Variables**:
   ```
   API_KEY=your_api_football_key_here
   DATABASE_URL=<paste Internal Database URL from Step 1>
   REDIS_URL=<paste Internal Redis URL from Step 2>
   FLASK_ENV=production
   SECRET_KEY=<click "Generate" button>
   CACHE_TYPE=redis
   CACHE_TIMEOUT=300
   LOG_LEVEL=info
   WORKERS=4
   PYTHON_VERSION=3.11.0
   ```

5. **Advanced Settings**:
   - **Health Check Path**: `/health`
   - **Auto-Deploy**: Yes (recommended)

6. Click "Create Web Service"

## 🔑 Getting Your API Key

1. Go to [RapidAPI API-Football](https://rapidapi.com/api-sports/api/api-football)
2. Sign up or log in
3. Subscribe to a plan (free tier available)
4. Copy your API key from the dashboard
5. Add it to Render environment variables

## ✅ Verify Deployment

After deployment completes:

1. **Check Health Endpoint**
   ```bash
   curl https://your-app.onrender.com/health
   ```
   Should return: `{"status": "healthy", ...}`

2. **Check Detailed Health**
   ```bash
   curl https://your-app.onrender.com/health/detailed
   ```

3. **Visit the App**
   - Open your browser to your Render URL
   - You should see the home page with league options

## 🐛 Troubleshooting

### Service Won't Start

**Check Logs**:
- Go to your web service in Render Dashboard
- Click "Logs" tab
- Look for error messages

**Common Issues**:

1. **Missing API_KEY**
   - Error: `API_KEY environment variable is missing`
   - Solution: Add API_KEY in environment variables

2. **Database Connection Failed**
   - Error: `could not connect to server`
   - Solution: Verify DATABASE_URL is correct and database is running

3. **Redis Connection Failed**
   - Error: `Error connecting to Redis`
   - Solution: Verify REDIS_URL is correct and Redis is running

4. **Import Errors**
   - Error: `ModuleNotFoundError`
   - Solution: Check requirements.txt includes all dependencies

### Slow Performance

1. **Upgrade Plan**: Free tier has limitations
2. **Check Cache**: Verify Redis is connected and working
3. **Increase Workers**: Set `WORKERS=8` for more concurrent requests
4. **Enable CDN**: In Render Dashboard → Settings → Enable CDN

### Database Issues

**Reset Database**:
```bash
# From Render Shell (Dashboard → Shell tab)
python
>>> from app import app, db
>>> with app.app_context():
...     db.drop_all()
...     db.create_all()
>>> exit()
```

## 🔄 Updates and Redeployment

### Automatic Deployments

If you enabled auto-deploy:
```bash
git add .
git commit -m "Your changes"
git push origin main
```
Render will automatically redeploy.

### Manual Deployment

From Render Dashboard:
1. Go to your web service
2. Click "Manual Deploy" → "Deploy latest commit"

## 📊 Monitoring

### View Logs
- Render Dashboard → Your Service → Logs
- Real-time log streaming
- Filter by log level

### Metrics
- Dashboard shows CPU, Memory, Response times
- `/metrics` endpoint for Prometheus integration

### Alerts (Paid Plans)
- Set up alerts for:
  - Service down
  - High error rate
  - High response time

## 💰 Cost Optimization

### Free Tier Limitations
- Services spin down after 15 min of inactivity
- 750 hours/month free
- Limited resources

### Staying on Free Tier
- Use free PostgreSQL (500MB storage)
- Use free Redis (25MB storage)
- Keep services minimal

### Upgrading for Production
Recommended upgrades:
- **Web Service**: Starter ($7/mo) - Always on, more resources
- **PostgreSQL**: Starter ($7/mo) - 1GB storage, backups
- **Redis**: Starter ($7/mo) - 100MB, better performance

## 🔐 Security Best Practices

1. **Never commit secrets**
   - Keep `.env` in `.gitignore`
   - Use Render environment variables

2. **Use Strong SECRET_KEY**
   - Let Render generate it
   - Don't reuse across environments

3. **Enable HTTPS**
   - Render provides free SSL
   - Force HTTPS in production (already configured)

4. **Regular Updates**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

5. **Monitor Logs**
   - Check for suspicious activity
   - Set up log alerts

## 🆘 Support

- **Render Support**: [support.render.com](https://support.render.com)
- **Documentation**: [render.com/docs](https://render.com/docs)
- **Community**: [community.render.com](https://community.render.com)
- **GitHub Issues**: [Your repo issues page]

## 📝 Post-Deployment Checklist

- [ ] All services are running (green status)
- [ ] Health endpoint returns healthy status
- [ ] Can view league standings
- [ ] Can compare players
- [ ] Caching is working (check logs)
- [ ] No errors in logs
- [ ] Custom domain configured (optional)
- [ ] Analytics set up (optional)
- [ ] Monitoring enabled

## 🎉 Success!

Your Football Stats Web App is now live! Share your URL:
- Add to your portfolio
- Share on LinkedIn
- Include in your resume
- Show to potential employers

---

**Next Steps**:
- Set up custom domain
- Add Google Analytics
- Implement more features
- Optimize performance
- Add tests and CI/CD

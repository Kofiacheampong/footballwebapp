# Deploy to VPS + Cloudflare Tunnel

## Overview

- **VPS**: Any cheap Linux VM (Hetzner CX22, DigitalOcean $6, etc.)
- **App**: Docker container running Flask behind Gunicorn
- **Tunnel**: `cloudflared` exposes it through Cloudflare — no open ports, free SSL

---

## 1. VPS Provisioning

Minimum specs: **1 CPU, 1GB RAM, 20GB storage** (2GB RAM for Postgres/Redis stack)

Recommended providers:
| Provider | Plan | Price |
|----------|------|-------|
| Hetzner | CX22 (2 vCPU, 4GB) | ~€4/mo |
| DigitalOcean | Basic $6 | $6/mo |
| Linode | Nanode 1GB | $5/mo |

OS: **Ubuntu 24.04 LTS**

---

## 2. Install Dependencies on VPS

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker

# Install cloudflared
sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg > /dev/null
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt update && sudo apt install cloudflared -y
```

---

## 3. Deploy the App

Choose one of two stacks:

### Option A: Lightweight (SQLite) — ~512MB RAM

```bash
# Clone repo
git clone <your-repo-url> /opt/footballwebapp
cd /opt/footballwebapp

# Create .env
cat > .env << 'EOF'
API_KEY=your_rapidapi_key_here
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=sqlite:///football_stats.db
FLASK_ENV=production
LOG_LEVEL=info
WORKERS=2
EOF

# Build image
docker build -t football-webapp -f Dockerfile --target application .

# Run container
docker run -d \
  --restart=always \
  --name football-webapp \
  -p 127.0.0.1:5000:5000 \
  -v /opt/footballwebapp/.env:/app/.env \
  -v football-data:/app/instance \
  football-webapp

# Verify
curl http://localhost:5000/health
```

### Option B: Full stack (PostgreSQL + Redis) — ~1GB+ RAM

```bash
# Clone repo
git clone <your-repo-url> /opt/footballwebapp
cd /opt/footballwebapp

# Create .env
cat > .env << 'EOF'
API_KEY=your_rapidapi_key_here
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql://football_user:football_pass@postgres:5432/football_db
REDIS_URL=redis://redis:6379/0
FLASK_ENV=production
LOG_LEVEL=info
WORKERS=4
EOF

# Start all services (web, postgres, redis)
docker compose up -d

# Verify
curl http://localhost:5000/health
```

---

## 4. Cloudflare Tunnel

### 4a. Authenticate and create tunnel

```bash
# Log in to Cloudflare (opens browser)
cloudflared tunnel login

# Create a tunnel
cloudflared tunnel create football-tunnel
# ^ This creates <tunnel-id>.json in ~/.cloudflared/
#   and returns a <tunnel-id> string
```

### 4b. Configure DNS

```bash
# Replace yourdomain.com with your actual domain
cloudflared tunnel route dns football-tunnel yourdomain.com
```

### 4c. Create tunnel config

Create `/etc/cloudflared/config.yml`:

```yaml
tunnel: <tunnel-id>
credentials-file: /root/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: yourdomain.com
    service: http://localhost:5000
  - service: http_status:404
```

Replace `<tunnel-id>` with the ID from step 4a.

### 4d. Run as a systemd service

```bash
# Install as systemd service
sudo cloudflared service install

# Start and enable
sudo systemctl enable cloudflared
sudo systemctl start cloudflared

# Check status
sudo systemctl status cloudflared
```

---

## 5. Verify

```bash
# Local health check
curl http://localhost:5000/health

# Via tunnel (from anywhere)
curl https://yourdomain.com/health
```

---

## 6. ETL & Updates

**Run ETL manually** (after first deploy):
```bash
docker exec football-webapp python -c "
from app import app, db, League, Team, Player, PlayerStats
from etl import run_etl
with app.app_context():
    run_etl(db, League, Team, Player, PlayerStats)
"
```

**Update the app** after pushing new code:
```bash
cd /opt/footballwebapp
git pull
docker compose down
docker compose up -d --build
```

---

## 7. Monitoring

```bash
# View logs
docker logs -f football-webapp
# or
docker compose logs -f web

# Restart tunnel
sudo systemctl restart cloudflared
```

#!/bin/bash
set -e

echo "========================================="
echo "  派单管理系统 - 服务器部署脚本"
echo "  域名: 168heima.cn"
echo "  数据库: PostgreSQL"
echo "========================================="

# --- 1. System packages ---
echo "[1/8] Installing system packages..."
apt-get update -qq
apt-get install -y -qq \
  build-essential curl git wget \
  nginx \
  postgresql postgresql-contrib \
  python3.11 python3.11-venv python3.11-dev python3-pip \
  supervisor \
  certbot python3-certbot-nginx \
  > /dev/null 2>&1
echo "  Done."

# --- 2. PostgreSQL setup ---
echo "[2/8] Configuring PostgreSQL..."
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='dispatch'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE USER dispatch WITH PASSWORD 'dispatch123';"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='dispatch_db'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE DATABASE dispatch_db OWNER dispatch;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE dispatch_db TO dispatch;" 2>/dev/null || true
echo "  PostgreSQL: user=dispatch, db=dispatch_db"

# --- 3. Application directory ---
echo "[3/8] Setting up application directory..."
APP_DIR="/opt/dispatch-system"
mkdir -p $APP_DIR
mkdir -p $APP_DIR/uploads
mkdir -p $APP_DIR/app/logs

# Copy backend files (exclude web/node_modules, .git, db.sqlite3)
echo "  Copying application files..."
rsync -a --delete \
  --exclude='web/node_modules' \
  --exclude='web/dist' \
  --exclude='.git' \
  --exclude='db.sqlite3' \
  --exclude='migrations' \
  --exclude='__pycache__' \
  --exclude='.venv' \
  --exclude='miniprogram' \
  /tmp/dispatch-system-upload/ $APP_DIR/

# Copy web dist
mkdir -p $APP_DIR/web/dist
cp -r /tmp/dispatch-web-dist/* $APP_DIR/web/dist/

# --- 4. Python virtual environment ---
echo "[4/8] Setting up Python environment..."
cd $APP_DIR
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q 2>/dev/null || pip install \
  "fastapi==0.111.0" \
  "tortoise-orm==0.23.0" \
  "asyncpg>=0.29.0" \
  "pydantic==2.10.5" \
  "email-validator==2.2.0" \
  "passlib==1.7.4" \
  "pyjwt==2.10.1" \
  "loguru==0.7.3" \
  "pydantic-settings==2.7.1" \
  "argon2-cffi==23.1.0" \
  "uvicorn==0.34.0" \
  "aerich==0.8.1" \
  "aiosqlite==0.20.0" \
  "httpx>=0.27.0" \
  -q
echo "  Done."

# --- 5. Environment config ---
echo "[5/8] Creating environment config..."
cat > $APP_DIR/.env << 'ENVEOF'
DB_TYPE=postgres
DB_HOST=localhost
DB_PORT=5432
DB_USER=dispatch
DB_PASSWORD=dispatch123
DB_NAME=dispatch_db
DEBUG=false
WECHAT_APPID=
WECHAT_SECRET=
WECHAT_SUBSCRIBE_TEMPLATE_ID=
ENVEOF

# --- 6. Supervisor config ---
echo "[6/8] Configuring Supervisor..."
cat > /etc/supervisor/conf.d/dispatch.conf << 'SUPEOF'
[program:dispatch-backend]
directory=/opt/dispatch-system
command=/opt/dispatch-system/.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 9999 --workers 2
user=root
autostart=true
autorestart=true
startsecs=5
stopwaitsecs=10
redirect_stderr=true
stdout_logfile=/opt/dispatch-system/app/logs/uvicorn.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
environment=
    DB_TYPE="postgres",
    DB_HOST="localhost",
    DB_PORT="5432",
    DB_USER="dispatch",
    DB_PASSWORD="dispatch123",
    DB_NAME="dispatch_db",
    DEBUG="false"
SUPEOF

supervisorctl reread > /dev/null 2>&1
supervisorctl update > /dev/null 2>&1
echo "  Done."

# --- 7. Nginx config ---
echo "[7/8] Configuring Nginx..."
cat > /etc/nginx/sites-available/168heima.cn << 'NGINXEOF'
server {
    listen 80;
    server_name 168heima.cn www.168heima.cn;

    # Frontend static files
    root /opt/dispatch-system/web/dist;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript image/svg+xml;

    # API reverse proxy
    location /api/ {
        proxy_pass http://127.0.0.1:9999/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
        proxy_send_timeout 60s;

        # WebSocket support (for future use)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Upload files
    location /uploads/ {
        alias /opt/dispatch-system/uploads/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # Static assets cache
    location /assets/ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # SPA fallback - all routes go to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # File upload size
    client_max_body_size 50M;
}
NGINXEOF

# Enable site
ln -sf /etc/nginx/sites-available/168heima.cn /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and reload nginx
nginx -t
systemctl reload nginx
echo "  Done."

# --- 8. Start services ---
echo "[8/8] Starting services..."
supervisorctl restart dispatch-backend 2>/dev/null || supervisorctl start dispatch-backend
sleep 3

# Check if backend is running
if curl -s http://127.0.0.1:9999/api/v1/base/access_token -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"123456"}' | grep -q access_token; then
  echo "  Backend: RUNNING"
else
  echo "  Backend: checking logs..."
  tail -20 /opt/dispatch-system/app/logs/uvicorn.log
fi

echo ""
echo "========================================="
echo "  Deployment Complete!"
echo "  Website: http://168heima.cn"
echo "  API: http://168heima.cn/api/v1/"
echo "  Default login: admin / 123456"
echo ""
echo "  To enable HTTPS:"
echo "  certbot --nginx -d 168heima.cn -d www.168heima.cn"
echo "========================================="

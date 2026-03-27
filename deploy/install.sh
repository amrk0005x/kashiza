#!/bin/bash
#
# Kashiza - Installation Script for Fresh VPS
# Supports: Ubuntu 20.04/22.04, Debian 11/12
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

KASHIZA_DIR="/opt/kashiza"
KASHIZA_USER="kashiza"
KASHIZA_PORT="${KASHIZA_PORT:-8080}"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                               ║${NC}"
echo -e "${BLUE}║   Kashiza - VPS Installation                           ║${NC}"
echo -e "${BLUE}║                                                               ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
   echo -e "${RED}❌ Please run as root (sudo)${NC}"
   exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
else
    echo -e "${RED}❌ Cannot detect OS${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Detected OS: $OS $VERSION${NC}"

# Update system
echo -e "${YELLOW}🔄 Updating system packages...${NC}"
apt-get update -qq
apt-get upgrade -y -qq

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    nginx \
    certbot \
    python3-certbot-nginx \
    sqlite3 \
    redis-server \
    supervisor \
    htop \
    vim \
    ufw

# Install Node.js (for dashboard build if needed)
echo -e "${YELLOW}📦 Installing Node.js...${NC}"
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y -qq nodejs

# Create kashiza user
echo -e "${YELLOW}👤 Creating kashiza user...${NC}"
if ! id "$KASHIZA_USER" &>/dev/null; then
    useradd -m -s /bin/bash -d "$KASHIZA_DIR" "$KASHIZA_USER"
fi

# Create directories
echo -e "${YELLOW}📁 Creating directories...${NC}"
mkdir -p "$KASHIZA_DIR"
mkdir -p "$KASHIZA_DIR/logs"
mkdir -p "$KASHIZA_DIR/config"
mkdir -p "$KASHIZA_DIR/data"
mkdir -p "$KASHIZA_DIR/plugins"

# Copy project files (if running from project directory)
if [ -f "./run.py" ]; then
    echo -e "${YELLOW}📂 Copying project files...${NC}"
    cp -r ./* "$KASHIZA_DIR/"
else
    echo -e "${YELLOW}📥 Cloning from repository...${NC}"
    git clone https://github.com/amirko/kashiza.git "$KASHIZA_DIR" 2>/dev/null || true
fi

# Set permissions
chown -R "$KASHIZA_USER:$KASHIZA_USER" "$KASHIZA_DIR"
chmod -R 755 "$KASHIZA_DIR"

# Create virtual environment
echo -e "${YELLOW}🐍 Creating Python virtual environment...${NC}"
sudo -u "$KASHIZA_USER" bash -c "
    cd $KASHIZA_DIR
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel -q
    pip install -r requirements.txt -q
"

# Generate master key
echo -e "${YELLOW}🔐 Generating master encryption key...${NC}"
MASTER_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

cat > "$KASHIZA_DIR/.env" << EOF
# Kashiza Environment
KASHIZA_MASTER_KEY=$MASTER_KEY
JWT_SECRET=$JWT_SECRET
KASHIZA_PORT=$KASHIZA_PORT
KASHIZA_HOST=0.0.0.0
KASHIZA_ENV=production

# AI Provider API Keys (add your own)
# Anthropic (Claude) - https://console.anthropic.com
# ANTHROPIC_API_KEY=your_key_here

# OpenAI (GPT) - https://platform.openai.com
# OPENAI_API_KEY=your_key_here

# Google (Gemini) - https://aistudio.google.com/app/apikey
# GOOGLE_API_KEY=your_key_here

# Groq (Fast inference) - https://console.groq.com/keys
# GROQ_API_KEY=your_key_here

# Kimi (Moonshot AI) - https://platform.moonshot.cn
# KIMI_API_KEY=your_key_here

# DeepSeek - https://platform.deepseek.com
# DEEPSEEK_API_KEY=your_key_here

# OpenRouter (Unified API) - https://openrouter.ai/keys
# OPENROUTER_API_KEY=your_key_here

# Ollama (Local) - Optional: override default host
# OLLAMA_HOST=http://localhost:11434

# Database
DATABASE_URL=sqlite:///$KASHIZA_DIR/data/kashiza.db

# Redis (for caching)
REDIS_URL=redis://localhost:6379/0

# SSL (optional)
# SSL_KEYFILE=/etc/letsencrypt/live/yourdomain.com/privkey.pem
# SSL_CERTFILE=/etc/letsencrypt/live/yourdomain.com/fullchain.pem
EOF

chown "$KASHIZA_USER:$KASHIZA_USER" "$KASHIZA_DIR/.env"
chmod 600 "$KASHIZA_DIR/.env"

# Create systemd service
echo -e "${YELLOW}⚙️  Creating systemd service...${NC}"
cat > /etc/systemd/system/kashiza.service << EOF
[Unit]
Description=Kashiza API Server
After=network.target redis.service

[Service]
Type=simple
User=$KASHIZA_USER
Group=$KASHIZA_USER
WorkingDirectory=$KASHIZA_DIR
Environment=PATH=$KASHIZA_DIR/venv/bin
EnvironmentFile=$KASHIZA_DIR/.env
ExecStart=$KASHIZA_DIR/venv/bin/python -c "from api.enhanced_server import main; main()"
Restart=always
RestartSec=10
StandardOutput=append:$KASHIZA_DIR/logs/kashiza.log
StandardError=append:$KASHIZA_DIR/logs/kashiza.error.log

[Install]
WantedBy=multi-user.target
EOF

# Create config
echo -e "${YELLOW}⚙️  Creating configuration...${NC}"
sudo -u "$KASHIZA_USER" bash -c "
mkdir -p $KASHIZA_DIR/config
cat > $KASHIZA_DIR/config/wrapper.yaml << 'EOFCFG'
# Kashiza Configuration
daily_budget: 50.0
monthly_budget: 500.0
alert_thresholds: [0.5, 0.8, 1.0]
auto_switch_cheaper: true
target_quality: 7.0
auto_optimize: true
auto_correct: true
max_concurrent_tasks: 10
cache_ttl: 3600
context_compression_threshold: 3000
max_retries: 3
base_delay: 1.0
exponential_base: 2.0
circuit_breaker_threshold: 5
monitoring_interval: 60
metrics_retention_days: 7
api_host: 0.0.0.0
api_port: $KASHIZA_PORT
cors_origins: ["*"]
push_notifications: true
offline_sync: true
sync_interval: 300
wake_word: hey kashiza
speech_rate: 1.0
language: en-US
default_role: developer
enable_realtime: true
rate_limit: 100
EOFCFG
"

# Setup firewall
echo -e "${YELLOW}🛡️  Configuring firewall...${NC}"
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow "$KASHIZA_PORT"/tcp
ufw --force enable

# Setup Nginx (optional)
read -p "🌐 Setup Nginx reverse proxy? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter your domain (e.g., api.example.com): " domain
    
    cat > /etc/nginx/sites-available/kashiza << EOF
server {
    listen 80;
    server_name $domain;

    location / {
        proxy_pass http://127.0.0.1:$KASHIZA_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # WebSocket support
        proxy_read_timeout 86400;
    }

    location /ws {
        proxy_pass http://127.0.0.1:$KASHIZA_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    client_max_body_size 100M;
}
EOF

    ln -sf /etc/nginx/sites-available/kashiza /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl restart nginx
    
    # Setup SSL with Certbot
    read -p "🔒 Setup SSL with Let's Encrypt? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        certbot --nginx -d "$domain" --non-interactive --agree-tos --email admin@$domain
    fi
fi

# Start services
echo -e "${YELLOW}🚀 Starting services...${NC}"
systemctl daemon-reload
systemctl enable kashiza
systemctl enable redis
systemctl start redis

# Create management script
cat > /usr/local/bin/kashiza << 'EOFSCRIPT'
#!/bin/bash

KASHIZA_DIR="/opt/kashiza"
KASHIZA_USER="kashiza"

case "$1" in
    start)
        systemctl start kashiza
        echo "✅ Kashiza started"
        ;;
    stop)
        systemctl stop kashiza
        echo "🛑 Kashiza stopped"
        ;;
    restart)
        systemctl restart kashiza
        echo "🔄 Kashiza restarted"
        ;;
    status)
        systemctl status kashiza --no-pager
        ;;
    logs)
        tail -f "$KASHIZA_DIR/logs/kashiza.log"
        ;;
    update)
        echo "🔄 Updating Kashiza..."
        sudo -u "$KASHIZA_USER" bash -c "
            cd $KASHIZA_DIR
            git pull
            source venv/bin/activate
            pip install -r requirements.txt -q
        "
        systemctl restart kashiza
        echo "✅ Update complete"
        ;;
    shell)
        sudo -u "$KASHIZA_USER" bash -c "cd $KASHIZA_DIR && source venv/bin/activate && bash"
        ;;
    backup)
        backup_file="/root/kashiza-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
        tar -czf "$backup_file" -C "$KASHIZA_DIR" .
        echo "💾 Backup created: $backup_file"
        ;;
    uninstall)
        echo "⚠️  This will completely remove Kashiza and all data!"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" == "yes" ]; then
            sudo bash "$KASHIZA_DIR/deploy/uninstall.sh"
        else
            echo "Cancelled."
        fi
        ;;
    *)
        echo "Usage: kashiza {start|stop|restart|status|logs|update|shell|backup|uninstall}"
        exit 1
        ;;
esac
EOFSCRIPT

chmod +x /usr/local/bin/kashiza

# Create health check script
cat > /usr/local/bin/kashiza-health << 'EOFSCRIPT'
#!/bin/bash

KASHIZA_PORT="${KASHIZA_PORT:-8080}"

if curl -s "http://127.0.0.1:$KASHIZA_PORT/api/monitoring/health" > /dev/null; then
    echo "✅ Kashiza is healthy"
    exit 0
else
    echo "❌ Kashiza is not responding"
    exit 1
fi
EOFSCRIPT

chmod +x /usr/local/bin/kashiza-health

# Final instructions
echo ""
echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}📍 Installation directory:${NC} $KASHIZA_DIR"
echo -e "${YELLOW}👤 User:${NC} $KASHIZA_USER"
echo -e "${YELLOW}🌐 Port:${NC} $KASHIZA_PORT"
echo -e "${YELLOW}📊 Dashboard:${NC} http://YOUR_VPS_IP:$KASHIZA_PORT"
echo ""
echo -e "${YELLOW}🔐 Master Key:${NC} ${MASTER_KEY:0:16}... (saved in $KASHIZA_DIR/.env)"
echo -e "${YELLOW}🔐 JWT Secret:${NC} ${JWT_SECRET:0:16}... (saved in $KASHIZA_DIR/.env)"
echo ""
echo -e "${YELLOW}🚀 Start server:${NC} kashiza start"
echo -e "${YELLOW}🛑 Stop server:${NC} kashiza stop"
echo -e "${YELLOW}📊 View logs:${NC} kashiza logs"
echo -e "${YELLOW}🔄 Restart:${NC} kashiza restart"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT:${NC}"
echo "1. Add your API keys to: $KASHIZA_DIR/.env"
echo "2. Start the server: kashiza start"
echo "3. Access dashboard at: http://YOUR_VPS_IP:$KASHIZA_PORT"
echo ""
if [ -n "$domain" ]; then
    echo -e "${GREEN}🌐 Domain configured:${NC} https://$domain"
fi
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

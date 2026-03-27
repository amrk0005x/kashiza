#!/bin/bash
#
# Kashiza Fresh Install Script for Linux
# Supports: Ubuntu 20.04+, Debian 11+, CentOS 8+, Fedora 35+
#

set -e

# Colors (no emojis, ASCII only)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Config
KASHIZA_VERSION="2.2"
INSTALL_DIR="/opt/kashiza"
SERVICE_USER="kashiza"
PYTHON_VERSION="3.11"
START_TIME=$(date +%s)

# Progress tracking
TOTAL_STEPS=12
CURRENT_STEP=0

# Progress bar function
progress() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    local percent=$((CURRENT_STEP * 100 / TOTAL_STEPS))
    local filled=$((percent / 2))
    local empty=$((50 - filled))
    
    local bar="["
    for ((i=0; i<filled; i++)); do bar+="#"; done
    for ((i=0; i<empty; i++)); do bar+="-"; done
    bar+="]"
    
    local elapsed=$(($(date +%s) - START_TIME))
    local eta=$((elapsed * (TOTAL_STEPS - CURRENT_STEP) / CURRENT_STEP))
    
    printf "\r${BOLD}${BLUE}%s${NC} ${CYAN}%3d%%${NC} | Step %d/%d | %02d:%02d elapsed | ~%02d:%02d remaining" \
        "$bar" "$percent" "$CURRENT_STEP" "$TOTAL_STEPS" \
        $((elapsed/60)) $((elapsed%60)) $((eta/60)) $((eta%60))
    echo ""
}

# Logging (ASCII only)
log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Draw line
line() {
    echo -e "${BOLD}$(printf '=%.0s' $(seq 1 60))${NC}"
}

# Banner
banner() {
    clear
    line
    echo -e "${BOLD}${CYAN}  Kashiza v${KASHIZA_VERSION} - Fresh Install${NC}"
    echo -e "${BOLD}  Multi-Agent AI Orchestration Platform${NC}"
    line
    echo ""
}

# Detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
    else
        error "Cannot detect OS"
    fi
    log "OS: $OS $VERSION"
}

# Check root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "Please run as root: sudo bash fresh-install.sh"
    fi
}

# Install base dependencies
install_base_deps() {
    log "Installing base dependencies..."
    
    case $OS in
        ubuntu|debian)
            apt-get update -qq
            apt-get install -y -qq curl wget git vim nano \
                gcc build-essential libssl-dev zlib1g-dev \
                libbz2-dev libreadline-dev libsqlite3-dev \
                libncursesw5-dev xz-utils tk-dev libxml2-dev \
                libxmlsec1-dev libffi-dev liblzma-dev \
                redis-server nginx certbot python3-certbot-nginx \
                ufw fail2ban logrotate htop tree jq unzip
            systemctl enable redis-server nginx
            systemctl start redis-server nginx
            ;;
        centos|rhel|rocky|almalinux)
            yum install -y epel-release
            yum install -y curl wget git vim nano \
                gcc openssl-devel bzip2-devel libffi-devel \
                zlib-devel readline-devel sqlite-devel \
                redis nginx certbot python3-certbot-nginx \
                firewalld fail2ban logrotate htop tree jq unzip
            systemctl enable redis nginx
            systemctl start redis nginx
            ;;
        fedora)
            dnf install -y curl wget git vim nano \
                gcc openssl-devel bzip2-devel libffi-devel \
                zlib-devel readline-devel sqlite-devel \
                redis nginx certbot python3-certbot-nginx \
                firewalld fail2ban logrotate htop tree jq unzip
            systemctl enable redis nginx
            systemctl start redis nginx
            ;;
    esac
    
    progress
    success "Base dependencies installed"
}

# Install Python 3.11 (with fallbacks)
install_python() {
    log "Installing Python $PYTHON_VERSION..."
    
    # Check if Python 3.11 already exists
    if command -v python3.11 &> /dev/null; then
        success "Python 3.11 already installed"
        progress
        return
    fi
    
    # Try different methods
    case $OS in
        ubuntu|debian)
            # Method 1: Try deadsnakes PPA
            log "Trying deadsnakes PPA..."
            if add-apt-repository ppa:deadsnakes/ppa -y 2>/dev/null; then
                apt-get update -qq
                if apt-get install -y -qq python3.11 python3.11-venv python3.11-dev 2>/dev/null; then
                    success "Python 3.11 installed via deadsnakes"
                    progress
                    return
                fi
            fi
            
            # Method 2: Try standard repos (Ubuntu 22.04+, Debian 12+)
            log "Trying standard repositories..."
            apt-get update -qq
            if apt-get install -y -qq python3.11 python3.11-venv python3.11-dev 2>/dev/null; then
                success "Python 3.11 installed via apt"
                progress
                return
            fi
            ;;
            
        centos|rhel|rocky|almalinux|fedora)
            # Try to install from package
            if yum install -y python3.11 python3.11-devel 2>/dev/null || \
               dnf install -y python3.11 python3.11-devel 2>/dev/null; then
                success "Python 3.11 installed via yum/dnf"
                progress
                return
            fi
            ;;
    esac
    
    # Method 3: Build from source (universal fallback)
    log "Building Python 3.11 from source..."
    cd /tmp
    wget -q "https://www.python.org/ftp/python/3.11.8/Python-3.11.8.tgz"
    tar -xzf Python-3.11.8.tgz
    cd Python-3.11.8
    ./configure --prefix=/usr/local --enable-optimizations --enable-shared 2>&1 | tail -5
    make -j$(nproc) 2>&1 | tail -5
    make altinstall
    ldconfig
    
    # Verify
    if command -v python3.11 &> /dev/null; then
        success "Python 3.11 built from source"
    else
        error "Failed to install Python 3.11"
    fi
    
    progress
}

# Create service user
create_user() {
    log "Creating service user..."
    
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/bash -d "$INSTALL_DIR" -m "$SERVICE_USER"
        success "User '$SERVICE_USER' created"
    else
        warn "User '$SERVICE_USER' already exists"
    fi
    
    progress
}

# Clone/install Kashiza
install_kashiza() {
   current_dir=$(pwd)  # /opt/kashiza
    
    if [ "$current_dir" = "$INSTALL_DIR" ]; then
        # 1. Copie dans /tmp AVANT suppression
        cp -r "$current_dir" /tmp/kashiza-source
        
        # 2. Supprime /opt/kashiza
        rm -rf "$INSTALL_DIR"
        
        # 3. Restaure depuis /tmp
        cp -r /tmp/kashiza-source/* "$INSTALL_DIR/"
    fi
}

# Setup Python virtual environment
setup_venv() {
    log "Setting up Python virtual environment..."
    
    cd "$INSTALL_DIR"
    
    # Create venv with Python 3.11
    sudo -u "$SERVICE_USER" python3.11 -m venv venv
    
    # Upgrade pip
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip -q
    
    # Install requirements
    log "Installing Python packages (this may take a few minutes)..."
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install -r requirements.txt -q 2>&1 | tail -10
    
    progress
    success "Virtual environment ready"
}

# Install Node.js (for dashboard)
install_nodejs() {
    log "Installing Node.js..."
    
    if ! command -v node &> /dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash - 2>/dev/null
        apt-get install -y -qq nodejs 2>/dev/null || \
        yum install -y nodejs 2>/dev/null || \
        dnf install -y nodejs 2>/dev/null
    fi
    
    progress
    success "Node.js installed"
}

# Setup configuration
setup_config() {
    log "Setting up configuration..."
    
    cd "$INSTALL_DIR"
    
    # Generate secrets
    MASTER_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)
    HEALTH_SECRET=$(openssl rand -hex 16)
    
    # Create directories
    mkdir -p data logs config plugins skills
    chown -R "$SERVICE_USER:$SERVICE_USER" data logs config plugins skills
    
    # Create .env
    cat > .env << EOF
# Kashiza Environment
KASHIZA_MASTER_KEY=$MASTER_KEY
JWT_SECRET=$JWT_SECRET
KASHIZA_HOST=0.0.0.0
KASHIZA_PORT=8080
KASHIZA_ENV=production
HEALTH_SECRET=$HEALTH_SECRET

# AI Provider API Keys (REQUIRED - add at least one)
# ANTHROPIC_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here
# GROQ_API_KEY=your_key_here
# DEEPSEEK_API_KEY=your_key_here

# Database
DATABASE_URL=sqlite:///$INSTALL_DIR/data/kashiza.db

# Redis
REDIS_URL=redis://localhost:6379/0
EOF
    
    chown "$SERVICE_USER:$SERVICE_USER" .env
    chmod 600 .env
    
    progress
    success "Configuration created"
}

# Setup systemd service
setup_systemd() {
    log "Setting up systemd service..."
    
    # Detect correct redis service name
    if systemctl list-unit-files | grep -q "redis-server.service"; then
        REDIS_SERVICE="redis-server.service"
    else
        REDIS_SERVICE="redis.service"
    fi
    
    cat > /etc/systemd/system/kashiza.service << EOF
[Unit]
Description=Kashiza Multi-Agent Orchestration System
After=network.target $REDIS_SERVICE


[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/python -c "from api.enhanced_server import main; main()"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable kashiza
    
    progress
    success "Systemd service created"
}

# Setup firewall
setup_firewall() {
    log "Configuring firewall..."
    
    case $OS in
        ubuntu|debian)
            ufw default deny incoming
            ufw default allow outgoing
            ufw allow 22/tcp
            ufw allow 80/tcp
            ufw allow 443/tcp
            ufw allow 8080/tcp
            ufw --force enable
            ;;
        centos|rhel|rocky|almalinux|fedora)
            systemctl enable firewalld
            systemctl start firewalld
            firewall-cmd --permanent --add-service=ssh
            firewall-cmd --permanent --add-service=http
            firewall-cmd --permanent --add-service=https
            firewall-cmd --permanent --add-port=8080/tcp
            firewall-cmd --reload
            ;;
    esac
    
    progress
    success "Firewall configured"
}

# Setup fail2ban
setup_fail2ban() {
    log "Setting up fail2ban..."
    
    cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[kashiza]
enabled = true
port = 8080
filter = kashiza
logpath = $INSTALL_DIR/logs/kashiza.log
maxretry = 10
EOF

    cat > /etc/fail2ban/filter.d/kashiza.conf << EOF
[Definition]
failregex = ^.*Failed login attempt from <HOST>.*$
            ^.*Invalid API key from <HOST>.*$
ignoreregex =
EOF

    systemctl restart fail2ban
    
    progress
    success "Fail2ban configured"
}

# Setup logrotate
setup_logrotate() {
    log "Setting up logrotate..."
    
    cat > /etc/logrotate.d/kashiza << EOF
$INSTALL_DIR/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 644 $SERVICE_USER $SERVICE_USER
}
EOF
    
    progress
    success "Logrotate configured"
}

# Create CLI command
create_cli() {
    log "Creating CLI command..."
    
    cat > /usr/local/bin/kashiza << 'EOFSCRIPT'
#!/bin/bash
KASHIZA_DIR="/opt/kashiza"
KASHIZA_USER="kashiza"

show_help() {
    echo "Kashiza Management CLI"
    echo ""
    echo "Usage: kashiza <command>"
    echo ""
    echo "Commands:"
    echo "  start          Start Kashiza service"
    echo "  stop           Stop Kashiza service"
    echo "  restart        Restart Kashiza service"
    echo "  status         Check service status"
    echo "  logs           View logs (tail -f)"
    echo "  cli            Start interactive CLI"
    echo "  config         Edit configuration (.env)"
    echo "  setup          Interactive setup (configure AI providers)"
    echo "  update         Update to latest version"
    echo "  backup         Create backup"
    echo "  providers      List AI providers"
    echo "  test           Test configuration"
    echo "  uninstall      Remove Kashiza"
    echo "  help           Show this help"
}

case "$1" in
    start)
        systemctl start kashiza
        echo "[OK] Kashiza started"
        ;;
    stop)
        systemctl stop kashiza
        echo "[OK] Kashiza stopped"
        ;;
    restart)
        systemctl restart kashiza
        echo "[OK] Kashiza restarted"
        ;;
    status)
        systemctl status kashiza --no-pager
        ;;
    logs)
        tail -f "$KASHIZA_DIR/logs/kashiza.log"
        ;;
    cli)
        cd "$KASHIZA_DIR" && sudo -u "$KASHIZA_USER" "$KASHIZA_DIR/venv/bin/python" run_cli.py
        ;;
    config)
        nano "$KASHIZA_DIR/.env"
        echo "[INFO] Run 'kashiza restart' to apply changes"
        ;;
    setup)
        bash "$KASHIZA_DIR/deploy/setup-env.sh"
        ;;
    update)
        cd "$KASHIZA_DIR"
        git pull
        sudo -u "$KASHIZA_USER" "$KASHIZA_DIR/venv/bin/pip" install -r requirements.txt -q
        systemctl restart kashiza
        echo "[OK] Kashiza updated"
        ;;
    backup)
        BACKUP_DIR="/var/backups/kashiza/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        cp -r "$KASHIZA_DIR/data" "$BACKUP_DIR/"
        cp "$KASHIZA_DIR/.env" "$BACKUP_DIR/"
        tar -czf "$BACKUP_DIR.tar.gz" -C "$BACKUP_DIR" .
        rm -rf "$BACKUP_DIR"
        echo "[OK] Backup created: $BACKUP_DIR.tar.gz"
        ;;
    providers)
        cd "$KASHIZA_DIR"
        sudo -u "$KASHIZA_USER" "$KASHIZA_DIR/venv/bin/python" -c "
from core.providers import get_provider_manager
pm = get_provider_manager()
providers = pm.list_available_providers()
if providers:
    print(f'[OK] {len(providers)} providers configured')
    for p in providers:
        print(f'   - {p.name}')
else:
    print('[WARN] No providers configured')
    print('   Run: kashiza setup')
"
        ;;
    test)
        cd "$KASHIZA_DIR"
        sudo -u "$KASHIZA_USER" "$KASHIZA_DIR/venv/bin/python" -c "
import sys
try:
    from core.providers import get_provider_manager
    pm = get_provider_manager()
    providers = pm.list_available_providers()
    if providers:
        print('[OK] Kashiza is configured correctly')
        print(f'   Providers: {len(providers)}')
        sys.exit(0)
    else:
        print('[WARN] No AI providers configured')
        print('   Run: kashiza setup')
        sys.exit(1)
except Exception as e:
    print(f'[ERROR] {e}')
    sys.exit(1)
"
        ;;
    uninstall)
        echo "[WARN] This will completely remove Kashiza!"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            bash "$KASHIZA_DIR/deploy/uninstall.sh"
        else
            echo "Cancelled"
        fi
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac
EOFSCRIPT

    chmod +x /usr/local/bin/kashiza
    progress
    success "CLI command created"
}

# Final setup
final_setup() {
    log "Starting Kashiza service..."
    systemctl start kashiza
    sleep 2
    
    # Check if running
    if systemctl is-active --quiet kashiza; then
        success "Kashiza is running"
    else
        warn "Service may need configuration. Check: kashiza status"
    fi
    
    progress
}

# Print final info
print_info() {
    local elapsed=$(($(date +%s) - START_TIME))
    
    line
    echo -e "${BOLD}${GREEN}  Installation Complete!${NC}"
    line
    echo ""
    echo "  Installation Directory: $INSTALL_DIR"
    echo "  Service User: $SERVICE_USER"
    echo "  Installation Time: $((elapsed/60))m $((elapsed%60))s"
    echo ""
    echo -e "${BOLD}  Next Steps:${NC}"
    echo "    1. Configure AI providers:"
    echo "       kashiza setup"
    echo ""
    echo "    2. Or manually edit .env:"
    echo "       kashiza config"
    echo ""
    echo "    3. Check status:"
    echo "       kashiza status"
    echo ""
    echo "    4. Start CLI:"
    echo "       kashiza cli"
    echo ""
    echo -e "${BOLD}  Dashboard:${NC} http://localhost:8080"
    echo ""
    line
}

# Main
main() {
    banner
    
    check_root
    detect_os
    
    echo -e "${BOLD}Starting installation...${NC}"
    echo ""
    
    install_base_deps
    install_python
    create_user
    install_kashiza
    setup_venv
    install_nodejs
    setup_config
    setup_systemd
    setup_firewall
    setup_fail2ban
    setup_logrotate
    create_cli
    final_setup
    
    print_info
}

main "$@"

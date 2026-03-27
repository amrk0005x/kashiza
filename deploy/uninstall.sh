#!/bin/bash
#
# Kashiza Uninstall Script
# Completely removes Kashiza and all its configuration
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

INSTALL_DIR="/opt/kashiza"
SERVICE_USER="kashiza"

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
}

line() {
    echo -e "${BOLD}$(printf '=%.0s' $(seq 1 60))${NC}"
}

# Check root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root (use sudo)"
fi

line
echo -e "${BOLD}${YELLOW}  WARNING - Kashiza Uninstaller${NC}"
line
echo ""
echo "This will COMPLETELY REMOVE Kashiza and ALL DATA!"
echo ""

read -p "Are you sure? Type 'yes' to continue: " confirm
if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

read -p "Also remove all backups? (yes/no): " remove_backups
read -p "Remove Nginx configuration? (yes/no): " remove_nginx
read -p "Remove $SERVICE_USER user? (yes/no): " remove_user

log "Starting uninstallation..."
echo ""

# Stop and disable service
log "Stopping Kashiza service..."
systemctl stop kashiza 2>/dev/null || true
systemctl disable kashiza 2>/dev/null || true
rm -f /etc/systemd/system/kashiza.service
systemctl daemon-reload
success "Service removed"

# Remove Nginx config
if [ "$remove_nginx" = "yes" ]; then
    log "Removing Nginx configuration..."
    rm -f /etc/nginx/sites-available/kashiza
    rm -f /etc/nginx/sites-enabled/kashiza
    nginx -t && systemctl reload nginx 2>/dev/null || true
    success "Nginx config removed"
fi

# Remove fail2ban config
log "Removing fail2ban configuration..."
rm -f /etc/fail2ban/jail.local
rm -f /etc/fail2ban/filter.d/kashiza.conf
systemctl restart fail2ban 2>/dev/null || true
success "Fail2ban config removed"

# Remove logrotate config
log "Removing logrotate configuration..."
rm -f /etc/logrotate.d/kashiza
success "Logrotate config removed"

# Remove CLI command
log "Removing CLI command..."
rm -f /usr/local/bin/kashiza
rm -f /usr/local/bin/kashiza-health
success "CLI commands removed"

# Remove backups
if [ "$remove_backups" = "yes" ]; then
    log "Removing backups..."
    rm -rf /var/backups/kashiza
    success "Backups removed"
fi

# Remove installation directory
log "Removing installation directory..."
rm -rf "$INSTALL_DIR"
success "Installation directory removed"

# Remove user
if [ "$remove_user" = "yes" ]; then
    log "Removing user $SERVICE_USER..."
    userdel -r "$SERVICE_USER" 2>/dev/null || true
    success "User removed"
fi

# Clean up Redis
log "Cleaning up Redis..."
redis-cli FLUSHDB 2>/dev/null || true
success "Redis cleaned"

echo ""
line
echo -e "${BOLD}${GREEN}  Uninstall Complete!${NC}"
line
echo ""

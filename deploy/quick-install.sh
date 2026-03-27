#!/bin/bash
#
# Kashiza Quick Install - One-liner installation
# Usage: curl -fsSL https://yourdomain.com/install.sh | sudo bash
#

set -e

REPO_URL="https://github.com/amrk0005x/kashiza.git"
INSTALL_DIR="/opt/kashiza"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${BOLD}${BLUE}  Kashiza Quick Installer${NC}"
echo -e "${BOLD}  Multi-Agent AI Orchestration${NC}"
echo ""

# Check root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} Please run as root: curl ... | sudo bash"
    exit 1
fi

# Detect OS
if [ -f /etc/debian_version ]; then
    OS="debian"
elif [ -f /etc/redhat-release ]; then
    OS="redhat"
else
    echo -e "${RED}[ERROR]${NC} Unsupported OS. Use fresh-install.sh instead."
    exit 1
fi

echo "[1/4] Installing base dependencies..."

if [ "$OS" = "debian" ]; then
    apt-get update -qq
    apt-get install -y -qq curl git python3 python3-venv python3-dev redis-server nginx
else
    yum install -y curl git python3 redis nginx 2>/dev/null || \
    dnf install -y curl git python3 redis nginx
fi

echo -e "${GREEN}[OK]${NC} Dependencies installed"
echo ""
echo "[2/4] Downloading Kashiza..."

if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
fi

# Clone or copy
cd /tmp
if [ -d "/home/ubuntu/kashiza/.git" ] || [ -f "/home/ubuntu/kashiza/run.py" ]; then
    cp -r /home/ubuntu/kashiza "$INSTALL_DIR"
    echo -e "${GREEN}[OK]${NC} Kashiza copied from local directory"
else
    git clone --depth 1 "$REPO_URL" "$INSTALL_DIR" 2>/dev/null || {
        echo -e "${YELLOW}[WARN]${NC} Could not clone repository."
        echo "Please clone manually and run: sudo bash deploy/fresh-install.sh"
        exit 1
    }
    echo -e "${GREEN}[OK]${NC} Kashiza cloned from GitHub"
fi

cd "$INSTALL_DIR"

echo ""
echo "[3/4] Running installation..."
echo ""

if [ -f "deploy/fresh-install.sh" ]; then
    bash deploy/fresh-install.sh
else
    echo -e "${RED}[ERROR]${NC} fresh-install.sh not found!"
    exit 1
fi

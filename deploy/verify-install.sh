#!/bin/bash
#
# Post-Installation Verification Script
#

KASHIZA_DIR="${KASHIZA_DIR:-/opt/kashiza}"
KASHIZA_PORT="${KASHIZA_PORT:-8080}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 Kashiza - Installation Verification${NC}"
echo ""

ERRORS=0

# Function to check command
check_cmd() {
    if command -v "$1" &> /dev/null; then
        echo -e "${GREEN}✅${NC} $1 installed"
        return 0
    else
        echo -e "${RED}❌${NC} $1 not found"
        ((ERRORS++))
        return 1
    fi
}

# Function to check file
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} $2"
        return 0
    else
        echo -e "${RED}❌${NC} $2 missing"
        ((ERRORS++))
        return 1
    fi
}

# Function to check directory
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✅${NC} $2"
        return 0
    else
        echo -e "${RED}❌${NC} $2 missing"
        ((ERRORS++))
        return 1
    fi
}

# Function to check service
check_service() {
    if systemctl is-active --quiet "$1" 2>/dev/null; then
        echo -e "${GREEN}✅${NC} Service $1 is running"
        return 0
    else
        echo -e "${YELLOW}⚠️${NC} Service $1 is not running"
        return 1
    fi
}

# Function to check port
check_port() {
    if netstat -tlnp 2>/dev/null | grep -q ":$1 "; then
        echo -e "${GREEN}✅${NC} Port $1 is listening"
        return 0
    else
        echo -e "${YELLOW}⚠️${NC} Port $1 is not listening"
        return 1
    fi
}

echo -e "${BLUE}📦 System Dependencies${NC}"
check_cmd python3
check_cmd pip3
check_cmd git
check_cmd nginx
check_cmd redis-server
check_cmd curl
check_cmd ufw

echo ""
echo -e "${BLUE}📁 Installation Directory${NC}"
check_dir "$KASHIZA_DIR" "Main directory"
check_dir "$KASHIZA_DIR/core" "Core modules"
check_dir "$KASHIZA_DIR/skills" "Skills"
check_dir "$KASHIZA_DIR/api" "API"
check_file "$KASHIZA_DIR/run.py" "Main entry point"
check_file "$KASHIZA_DIR/requirements.txt" "Requirements"

echo ""
echo -e "${BLUE}⚙️  Configuration${NC}"
check_file "$KASHIZA_DIR/.env" "Environment file"
check_file "$KASHIZA_DIR/config/wrapper.yaml" "Configuration"

# Check .env content
echo ""
echo -e "${YELLOW}🔐 Checking .env configuration...${NC}"
if [ -f "$KASHIZA_DIR/.env" ]; then
    if grep -q "KASHIZA_MASTER_KEY=" "$KASHIZA_DIR/.env"; then
        echo -e "${GREEN}✅${NC} MASTER_KEY configured"
    else
        echo -e "${RED}❌${NC} MASTER_KEY not found"
        ((ERRORS++))
    fi
    
    if grep -q "JWT_SECRET=" "$KASHIZA_DIR/.env"; then
        echo -e "${GREEN}✅${NC} JWT_SECRET configured"
    else
        echo -e "${RED}❌${NC} JWT_SECRET not found"
        ((ERRORS++))
    fi
fi

echo ""
echo -e "${BLUE}🐍 Python Environment${NC}"
if [ -d "$KASHIZA_DIR/venv" ]; then
    echo -e "${GREEN}✅${NC} Virtual environment exists"
    
    # Check if key packages are installed
    sudo -u kashiza bash -c "source $KASHIZA_DIR/venv/bin/activate && python -c 'import fastapi'" 2>/dev/null && \
        echo -e "${GREEN}✅${NC} FastAPI installed" || \
        echo -e "${RED}❌${NC} FastAPI not installed"
else
    echo -e "${RED}❌${NC} Virtual environment missing"
    ((ERRORS++))
fi

echo ""
echo -e "${BLUE}🔧 Services${NC}"
check_service redis

echo ""
echo -e "${BLUE}🌐 Network${NC}"
check_port "$KASHIZA_PORT"
check_port 80
check_port 443

# Check firewall
echo ""
echo -e "${YELLOW}🛡️  Checking firewall...${NC}"
if ufw status | grep -q "Status: active"; then
    echo -e "${GREEN}✅${NC} Firewall is active"
    
    if ufw status | grep -q "$KASHIZA_PORT/tcp"; then
        echo -e "${GREEN}✅${NC} Port $KASHIZA_PORT allowed"
    else
        echo -e "${YELLOW}⚠️${NC} Port $KASHIZA_PORT not in firewall rules"
    fi
else
    echo -e "${YELLOW}⚠️${NC} Firewall is not active"
fi

# Check nginx
echo ""
echo -e "${YELLOW}🌐 Checking Nginx...${NC}"
if [ -f "/etc/nginx/sites-enabled/kashiza" ]; then
    echo -e "${GREEN}✅${NC} Nginx config exists"
    
    if nginx -t 2>&1 | grep -q "successful"; then
        echo -e "${GREEN}✅${NC} Nginx config valid"
    else
        echo -e "${RED}❌${NC} Nginx config invalid"
        ((ERRORS++))
    fi
else
    echo -e "${YELLOW}⚠️${NC} Nginx config not found (optional)"
fi

# Health check
echo ""
echo -e "${BLUE}🏥 Health Check${NC}"
if curl -s "http://localhost:$KASHIZA_PORT/api/monitoring/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} API is responding"
    
    # Get status
    STATUS=$(curl -s "http://localhost:$KASHIZA_PORT/api/monitoring/health")
    echo -e "${BLUE}📊${NC} Status: $STATUS"
else
    echo -e "${YELLOW}⚠️${NC} API not responding (service may not be running)"
fi

# Summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ Verification complete! No errors found.${NC}"
    echo ""
    echo -e "🚀 Start the server: ${YELLOW}kashiza start${NC}"
    echo -e "🌐 Access dashboard: ${YELLOW}http://YOUR_IP:$KASHIZA_PORT${NC}"
    exit 0
else
    echo -e "${RED}❌ Verification complete with $ERRORS error(s)${NC}"
    echo ""
    echo "Please fix the issues above before starting the server."
    exit 1
fi

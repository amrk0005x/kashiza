#!/bin/bash
#
# Kashiza Interactive Environment Setup
# ASCII-only, no emojis
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

INSTALL_DIR="/opt/kashiza"
ENV_FILE="$INSTALL_DIR/.env"

# Check root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} Please run as root: sudo kashiza setup"
    exit 1
fi

# Header
line() {
    echo -e "${BOLD}$(printf '=%.0s' $(seq 1 60))${NC}"
}

header() {
    clear
    line
    echo -e "${BOLD}${CYAN}  Kashiza Environment Setup${NC}"
    echo -e "${BOLD}  AI Provider Configuration${NC}"
    line
    echo ""
}

# Providers info
declare -A PROVIDER_URLS
declare -A PROVIDER_DESC

PROVIDER_URLS[anthropic]="https://console.anthropic.com"
PROVIDER_URLS[openai]="https://platform.openai.com/api-keys"
PROVIDER_URLS[google]="https://aistudio.google.com/app/apikey"
PROVIDER_URLS[groq]="https://console.groq.com/keys"
PROVIDER_URLS[kimi]="https://platform.moonshot.cn"
PROVIDER_URLS[deepseek]="https://platform.deepseek.com"
PROVIDER_URLS[openrouter]="https://openrouter.ai/keys"

PROVIDER_DESC[anthropic]="Claude models - Best for complex reasoning"
PROVIDER_DESC[openai]="GPT models - Best general purpose"
PROVIDER_DESC[google]="Gemini models - 2M context window"
PROVIDER_DESC[groq]="Fast inference - Llama, Mixtral (cheap & fast)"
PROVIDER_DESC[kimi]="Moonshot AI - Chinese/English bilingual"
PROVIDER_DESC[deepseek]="DeepSeek - Excellent for coding (very cheap)"
PROVIDER_DESC[openrouter]="Unified API - Access to 100+ models"

# Progress spinner
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\\'
    while [ -d /proc/$pid ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# Test API key
test_key() {
    local provider=$1
    local key=$2
    
    echo -n "  Testing connection..."
    
    case $provider in
        anthropic)
            curl -s -o /dev/null -w "%{http_code}" \
                -H "x-api-key: $key" \
                -H "anthropic-version: 2023-06-01" \
                https://api.anthropic.com/v1/models 2>/dev/null | grep -q "200" && return 0
            ;;
        openai)
            curl -s -o /dev/null -w "%{http_code}" \
                -H "Authorization: Bearer $key" \
                https://api.openai.com/v1/models 2>/dev/null | grep -q "200" && return 0
            ;;
        groq)
            curl -s -o /dev/null -w "%{http_code}" \
                -H "Authorization: Bearer $key" \
                https://api.groq.com/openai/v1/models 2>/dev/null | grep -q "200" && return 0
            ;;
        deepseek)
            curl -s -o /dev/null -w "%{http_code}" \
                -H "Authorization: Bearer $key" \
                https://api.deepseek.com/v1/models 2>/dev/null | grep -q "200" && return 0
            ;;
        *)
            return 1
            ;;
    esac
    return 1
}

# Configure provider
configure_provider() {
    local name=$1
    local key_var=$2
    
    echo ""
    echo -e "${BOLD}[$name]${NC} ${PROVIDER_DESC[$name]}"
    echo "  Get key: ${PROVIDER_URLS[$name]}"
    
    # Check if already configured
    if grep -q "^${key_var}=" "$ENV_FILE" 2>/dev/null && \
       ! grep -q "^${key_var}=.*your_key_here\|^${key_var}=#" "$ENV_FILE" 2>/dev/null; then
        local existing=$(grep "^${key_var}=" "$ENV_FILE" | cut -d'=' -f2)
        echo -n "  Enter API key (press Enter to keep existing): "
        read -s key
        echo ""
        [ -z "$key" ] && key="$existing"
    else
        echo -n "  Enter API key (or press Enter to skip): "
        read -s key
        echo ""
    fi
    
    if [ -n "$key" ]; then
        # Test key
        if test_key "$name" "$key"; then
            echo -e "  ${GREEN}[OK]${NC} Key is valid!"
            update_env "$key_var" "$key"
            return 0
        else
            echo -e "  ${YELLOW}[WARN]${NC} Could not verify key (will be saved anyway)"
            update_env "$key_var" "$key"
            return 0
        fi
    fi
    
    return 1
}

# Update .env file
update_env() {
    local key=$1
    local value=$2
    
    if grep -q "^#*${key}=" "$ENV_FILE" 2>/dev/null; then
        # Update existing
        sed -i "s|^#*${key}=.*|${key}=${value}|" "$ENV_FILE"
    else
        # Add new
        echo "${key}=${value}" >> "$ENV_FILE"
    fi
}

# Install Ollama
install_ollama() {
    echo ""
    line
    echo -e "${BOLD}Ollama (Local Models)${NC}"
    line
    echo ""
    echo "Ollama allows you to run AI models locally for free."
    echo "Recommended models: llama3.2, qwen2.5-coder, mistral"
    echo ""
    read -p "Install Ollama? (y/N): " install_ollama
    
    if [[ $install_ollama =~ ^[Yy]$ ]]; then
        echo ""
        echo "Installing Ollama..."
        
        if ! command -v ollama &> /dev/null; then
            curl -fsSL https://ollama.com/install.sh | sh
            systemctl enable ollama
            systemctl start ollama
            
            # Pull models
            echo ""
            echo "Pulling recommended models..."
            ollama pull llama3.2 &
            spinner $!
            echo "[OK] llama3.2"
            
            update_env "OLLAMA_HOST" "http://localhost:11434"
            echo -e "${GREEN}[OK]${NC} Ollama installed!"
        else
            echo -e "${GREEN}[OK]${NC} Ollama already installed"
        fi
    fi
}

# Main setup
main() {
    header
    
    echo "Kashiza requires at least one AI provider to function."
    echo "You can configure multiple providers for redundancy."
    echo ""
    read -p "Start interactive setup? (Y/n): " start_setup
    
    if [[ $start_setup =~ ^[Nn]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
    
    # Ensure .env exists
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${RED}[ERROR]${NC} Kashiza not installed. Run fresh-install.sh first."
        exit 1
    fi
    
    # Configure cloud providers
    header
    echo -e "${BOLD}Cloud AI Providers${NC}"
    echo ""
    
    configure_provider "anthropic" "ANTHROPIC_API_KEY"
    configure_provider "openai" "OPENAI_API_KEY"
    configure_provider "groq" "GROQ_API_KEY"
    configure_provider "deepseek" "DEEPSEEK_API_KEY"
    
    # Optional providers
    header
    echo -e "${BOLD}Optional Providers${NC}"
    echo ""
    
    read -p "Configure Google (Gemini)? (y/N): " cfg_google
    [[ $cfg_google =~ ^[Yy]$ ]] && configure_provider "google" "GOOGLE_API_KEY"
    
    read -p "Configure Kimi (Moonshot)? (y/N): " cfg_kimi
    [[ $cfg_kimi =~ ^[Yy]$ ]] && configure_provider "kimi" "KIMI_API_KEY"
    
    read -p "Configure OpenRouter? (y/N): " cfg_or
    [[ $cfg_or =~ ^[Yy]$ ]] && configure_provider "openrouter" "OPENROUTER_API_KEY"
    
    # Install Ollama
    install_ollama
    
    # Summary
    header
    echo -e "${BOLD}${GREEN}Configuration Complete!${NC}"
    echo ""
    
    # Count configured providers
    local count=$(grep -E "^(ANTHROPIC|OPENAI|GROQ|DEEPSEEK|GOOGLE|KIMI|OPENROUTER)_API_KEY=" "$ENV_FILE" 2>/dev/null | grep -v "your_key_here" | wc -l)
    
    echo "Configured providers: $count"
    echo ""
    
    if [ $count -eq 0 ]; then
        echo -e "${YELLOW}[WARN]${NC} No providers configured!"
        echo "Kashiza will not work without at least one API key."
        echo "Run 'kashiza setup' again to configure."
    else
        echo -e "${GREEN}[OK]${NC} Setup complete!"
        echo ""
        echo "Next steps:"
        echo "  1. Restart Kashiza: kashiza restart"
        echo "  2. Test setup:      kashiza test"
        echo "  3. Start CLI:       kashiza cli"
        echo "  4. View dashboard:  http://localhost:8080"
    fi
    
    echo ""
    line
}

main "$@"

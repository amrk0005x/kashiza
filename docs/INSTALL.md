# Kashiza Installation Guide

## Quick Install (Recommended)

### One-liner (Ubuntu/Debian)

```bash
curl -fsSL https://raw.githubusercontent.com/amrk0005x/kashiza/main/deploy/quick-install.sh | sudo bash
```

### Manual Install

```bash
# 1. Clone repository
git clone https://github.com/amrk0005x/kashiza.git
cd kashiza

# 2. Run fresh install
sudo bash deploy/fresh-install.sh
```

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Ubuntu 20.04, Debian 11, CentOS 8 | Ubuntu 22.04 LTS |
| RAM | 2 GB | 4 GB+ |
| Disk | 10 GB | 20 GB+ SSD |
| Python | 3.11 | 3.11+ |
| Network | IPv4 | IPv4 + IPv6 |

---

## Step-by-Step Installation

### 1. Prepare Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Set hostname (optional)
sudo hostnamectl set-hostname kashiza-server
```

### 2. Run Installer

```bash
# Download and run
sudo bash deploy/fresh-install.sh
```

The installer will:
- ✅ Update system packages
- ✅ Install Python 3.11, Node.js 20, Redis, Nginx
- ✅ Create service user `kashiza`
- ✅ Setup virtual environment
- ✅ Configure systemd service
- ✅ Setup firewall (UFW/Firewalld)
- ✅ Configure fail2ban
- ✅ Setup logrotate
- ✅ Create CLI command

### 3. Configure AI Providers

```bash
# Edit configuration
kashiza config
```

Add at least one API key:

```bash
# Example: Add OpenAI
OPENAI_API_KEY=sk-your-key-here

# Example: Add multiple providers
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
DEEPSEEK_API_KEY=sk-...
```

### 4. Start Service

```bash
# Start Kashiza
kashiza start

# Check status
kashiza status

# Test configuration
kashiza test
```

### 5. Access Dashboard

```
Local:  http://localhost:8080
Network: http://YOUR_IP:8080
```

---

## Post-Installation

### Configure Domain + SSL

```bash
# Edit Nginx config
sudo nano /etc/nginx/sites-available/kashiza

# Change server_name to your domain
server_name api.yourdomain.com;

# Reload nginx
sudo nginx -t && sudo systemctl reload nginx

# Setup SSL
sudo certbot --nginx -d api.yourdomain.com
```

### Setup Ollama (Local Models)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull llama3.2
ollama pull qwen2.5-coder

# Start service
sudo systemctl enable ollama
sudo systemctl start ollama

# Update .env
kashiza config
# Add: OLLAMA_HOST=http://localhost:11434

# Restart
kashiza restart
```

---

## Management Commands

```bash
# Service management
kashiza start          # Start service
kashiza stop           # Stop service
kashiza restart        # Restart service
kashiza status         # Check status
kashiza logs           # View logs

# Configuration
kashiza config         # Edit .env
kashiza test           # Test setup
kashiza providers      # List AI providers

# Interactive
kashiza cli            # Start interactive CLI

# Maintenance
kashiza update         # Update to latest
kashiza backup         # Create backup
kashiza uninstall      # Remove Kashiza
```

---

## Troubleshooting

### Service won't start

```bash
# Check logs
sudo journalctl -u kashiza -n 100

# Test manually
cd /opt/kashiza
source venv/bin/activate
python -c "from api.enhanced_server import main; main()"
```

### No providers available

```bash
# Check .env
cat /opt/kashiza/.env | grep -E "API_KEY"

# Test provider
kashiza providers
```

### Port already in use

```bash
# Find process
sudo lsof -i :8080

# Kill or change port
kashiza config
# Change: KASHIZA_PORT=8081
kashiza restart
```

### Permission denied

```bash
# Fix permissions
sudo chown -R kashiza:kashiza /opt/kashiza
sudo chmod 750 /opt/kashiza
sudo chmod 600 /opt/kashiza/.env
```

---

## Docker Install

```bash
# Clone repository
git clone https://github.com/amrk0005x/kashiza.git
cd kashiza

# Create .env
cp .env.example .env
nano .env  # Add your API keys

# Start with Docker Compose
docker-compose -f deploy/docker-compose.yml up -d

# View logs
docker-compose -f deploy/docker-compose.yml logs -f
```

---

## Uninstall

```bash
# Interactive uninstall
kashiza uninstall

# Or manual
sudo bash /opt/kashiza/deploy/uninstall.sh
```

---

## Security Checklist

- [ ] Change default KASHIZA_MASTER_KEY
- [ ] Enable firewall (done automatically)
- [ ] Configure fail2ban (done automatically)
- [ ] Setup SSL/TLS for production
- [ ] Use strong API keys
- [ ] Regular backups: `kashiza backup`
- [ ] Keep system updated

---

## Next Steps

1. **Configure Providers**: `kashiza config`
2. **Test Setup**: `kashiza test`
3. **Read Docs**: [docs/PROVIDERS.md](PROVIDERS.md)
4. **Try CLI**: `kashiza cli`
5. **Deploy Dashboard**: Configure Nginx + SSL

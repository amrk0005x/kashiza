# Security Guide - Kashiza

## 🔐 Security Checklist for VPS Deployment

### Pre-Deployment

- [ ] Use dedicated VPS (not shared)
- [ ] Enable automatic security updates
- [ ] Configure firewall (UFW)
- [ ] Disable root SSH login
- [ ] Use SSH key authentication only
- [ ] Change default SSH port (optional)
- [ ] Setup fail2ban
- [ ] Configure log monitoring

### Post-Deployment

- [ ] Change default JWT secret
- [ ] Generate unique master key
- [ ] Enable API key encryption
- [ ] Configure SSL/TLS
- [ ] Setup rate limiting
- [ ] Enable audit logging
- [ ] Configure backup strategy
- [ ] Setup monitoring alerts

---

## 🛡️ Hardening Steps

### 1. System Updates
```bash
# Automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 2. SSH Hardening
```bash
sudo nano /etc/ssh/sshd_config

# Change these lines:
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2

sudo systemctl restart sshd
```

### 3. Firewall (UFW)
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp      # SSH (change if you changed port)
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
# Only if not using nginx:
# sudo ufw allow 8080/tcp
sudo ufw enable
```

### 4. Fail2Ban
```bash
sudo apt install fail2ban
sudo nano /etc/fail2ban/jail.local

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

[kashiza-api]
enabled = true
port = 8080
filter = kashiza
logpath = /opt/kashiza/logs/kashiza.log
maxretry = 100
bantime = 3600

sudo systemctl restart fail2ban
```

### 5. API Security
```bash
# Generate strong keys
openssl rand -hex 32 > /tmp/master_key
openssl rand -hex 32 > /tmp/jwt_secret

# Update .env
sudo nano /opt/kashiza/.env
KASHIZA_MASTER_KEY=$(cat /tmp/master_key)
JWT_SECRET=$(cat /tmp/jwt_secret)

# Secure permissions
sudo chmod 600 /opt/kashiza/.env
sudo chown kashiza:kashiza /opt/kashiza/.env

# Remove temp files
shred -u /tmp/master_key /tmp/jwt_secret
```

### 6. SSL/TLS Configuration
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal test
sudo certbot renew --dry-run

# Strong SSL config
sudo nano /etc/nginx/nginx.conf

# Add in http block:
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers off;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:50m;
ssl_stapling on;
ssl_stapling_verify on;
add_header Strict-Transport-Security "max-age=63072000" always;
```

---

## 🔑 API Key Management

### Best Practices

1. **Never commit keys to git**
   ```bash
   # Add to .gitignore
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
   ```

2. **Use environment variables**
   ```bash
   # Instead of hardcoding
   export ANTHROPIC_API_KEY=$(cat /secure/path/to/key)
   ```

3. **Rotate keys regularly**
   ```bash
   # Set calendar reminder every 90 days
   # Use: kashiza update-keys
   ```

4. **Use IP whitelisting**
   ```bash
   # In .env
   IP_WHITELIST=123.45.67.89,10.0.0.0/8
   ```

5. **Monitor usage**
   ```bash
   # Check logs for suspicious activity
   sudo tail -f /opt/kashiza/logs/kashiza.log | grep "API_KEY"
   ```

---

## 🚨 Security Monitoring

### Log Analysis
```bash
# Failed auth attempts
sudo grep "401" /opt/kashiza/logs/kashiza.log

# Rate limit hits
sudo grep "rate limit" /opt/kashiza/logs/kashiza.log

# Suspicious patterns
sudo grep -E "(union|select|drop|insert|delete)" /opt/kashiza/logs/kashiza.log
```

### Alerts Setup
```bash
# Install logwatch
sudo apt install logwatch

# Daily security report
echo "0 6 * * * root /usr/sbin/logwatch --output mail --mailto admin@example.com --detail high" | sudo tee /etc/cron.daily/logwatch
```

---

## 📝 Security Audit Script

```bash
#!/bin/bash
# Run weekly: sudo bash security-audit.sh

echo "🔍 Security Audit"
echo "=================="

# Check for updates
echo "📦 Available updates:"
apt list --upgradable 2>/dev/null | wc -l

# Check failed logins
echo "❌ Failed login attempts (last 24h):"
grep "Failed password" /var/log/auth.log | wc -l

# Check firewall
echo "🛡️  Firewall status:"
ufw status verbose

# Check SSL expiry
echo "🔒 SSL certificate expiry:"
openssl x509 -in /etc/letsencrypt/live/*/fullchain.pem -noout -dates 2>/dev/null | grep notAfter

# Check file permissions
echo "🔐 Sensitive file permissions:"
ls -la /opt/kashiza/.env

# Check running services
echo "⚙️  Running services:"
systemctl list-units --type=service --state=running | grep kashiza

echo "✅ Audit complete"
```

---

## 🎯 Incident Response

### If Compromised

1. **Immediate**
   ```bash
   # Stop service
   kashiza stop
   
   # Block all traffic
   sudo ufw default deny incoming
   
   # Change all keys
   # Rotate: ANTHROPIC_API_KEY, OPENAI_API_KEY, JWT_SECRET, MASTER_KEY
   ```

2. **Investigate**
   ```bash
   # Check logs
   sudo journalctl -u kashiza --since "1 hour ago"
   
   # Check active connections
   sudo netstat -tulpn | grep 8080
   
   # Check processes
   ps aux | grep kashiza
   ```

3. **Restore**
   ```bash
   # Restore from backup
   tar -xzf /root/kashiza-backup-YYYYMMDD.tar.gz -C /opt/kashiza
   
   # Restart
   kashiza start
   ```

4. **Post-incident**
   - Change all API keys
   - Review access logs
   - Update security rules
   - Document incident

---

## 📋 Compliance

### GDPR (if applicable)
- [ ] User data encrypted at rest
- [ ] Audit logs retained for required period
- [ ] Data deletion capability
- [ ] User consent tracking

### SOC 2 (if applicable)
- [ ] Access controls documented
- [ ] Change management process
- [ ] Regular security audits
- [ ] Incident response plan

---

## 🔗 Additional Resources

- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

**Security is a process, not a product.**

Review and update security measures monthly.

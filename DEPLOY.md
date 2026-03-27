# Déploiement Kashiza sur VPS

## Méthode 1: Installation Automatique (Recommandé)

### En une commande
```bash
curl -fsSL https://raw.githubusercontent.com/amirko/kashiza/main/deploy/quick-install.sh | sudo bash
```

### Ou manuellement
```bash
# 1. Cloner le repo
git clone https://github.com/amirko/kashiza.git /opt/kashiza
cd /opt/kashiza

# 2. Lancer l'installation
sudo bash deploy/install.sh
```

### Post-installation
```bash
# Ajouter vos clés API
sudo nano /opt/kashiza/.env

# Démarrer le service
kashiza start

# Voir les logs
kashiza logs
```

## Méthode 2: Docker (Plus simple)

### Prérequis
- Docker + Docker Compose installés

### Installation
```bash
# 1. Cloner
git clone https://github.com/amirko/kashiza.git
cd kashiza/deploy

# 2. Configurer
cp .env.example .env
nano .env  # Ajouter vos clés API

# 3. Démarrer
docker-compose up -d

# 4. Vérifier
docker-compose ps
docker-compose logs -f kashiza
```

### Fichier .env pour Docker
```env
KASHIZA_PORT=8080
KASHIZA_MASTER_KEY=votre-master-key-32-chars
JWT_SECRET=votre-jwt-secret-32-chars
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
```

## Méthode 3: Manuel (Full Control)

### 1. Prérequis
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv git nginx redis-server

# CentOS/RHEL
sudo yum install python3 python3-pip git nginx redis
```

### 2. Installation
```bash
# Créer utilisateur
sudo useradd -m -s /bin/bash kashiza

# Cloner
sudo -u kashiza git clone https://github.com/amirko/kashiza.git /home/kashiza/kashiza

# Virtual env
sudo -u kashiza bash -c "
    cd ~/kashiza
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
"

# Config
sudo -u kashiza cp .env.example .env
sudo -u kashiza nano .env
```

### 3. Service SystemD
```bash
sudo nano /etc/systemd/system/kashiza.service
```

Contenu:
```ini
[Unit]
Description=Kashiza
After=network.target

[Service]
Type=simple
User=kashiza
WorkingDirectory=/home/kashiza/kashiza
Environment=PATH=/home/kashiza/kashiza/venv/bin
ExecStart=/home/kashiza/kashiza/venv/bin/python -c "from api.enhanced_server import main; main()"
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable kashiza
sudo systemctl start kashiza
```

## Configuration Nginx (Reverse Proxy)

### Sans SSL
```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_cache_bypass $http_upgrade;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Avec SSL (Let's Encrypt)
```bash
# Installer Certbot
sudo apt install certbot python3-certbot-nginx

# Obtenir certificat
sudo certbot --nginx -d votre-domaine.com

# Auto-renewal activé automatiquement
```

## Vérification

### Health Check
```bash
# Via CLI
kashiza-health

# Via API
curl http://localhost:8080/api/monitoring/health

# Dashboard
http://votre-ip:8080
```

### Commandes de gestion
```bash
kashiza start      # Démarrer
kashiza stop       # Arrêter
kashiza restart    # Redémarrer
kashiza status     # Statut
kashiza logs       # Logs temps réel
kashiza update     # Mettre à jour
kashiza backup     # Sauvegarder
kashiza shell      # Shell interactif
```

## Sécurité

### Firewall (UFW)
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 8080/tcp    # Hermes (si pas de nginx)
sudo ufw enable
```

### Clés API
```bash
# Générer master key
openssl rand -hex 32

# Stocker de façon sécurisée
sudo nano /opt/kashiza/.env
```

### Mises à jour
```bash
# Automatique
kashiza update

# Manuelle
cd /opt/kashiza
sudo -u kashiza git pull
sudo -u kashiza bash -c "source venv/bin/activate && pip install -r requirements.txt"
sudo systemctl restart kashiza
```

## Troubleshooting

### Service ne démarre pas
```bash
# Vérifier logs
journalctl -u kashiza -n 50

# Vérifier permissions
ls -la /opt/kashiza

# Tester manuellement
sudo -u kashiza bash
cd /opt/kashiza
source venv/bin/activate
python -c "from api.enhanced_server import main; main()"
```

### Port déjà utilisé
```bash
# Changer le port
sudo nano /opt/kashiza/.env
KASHIZA_PORT=8081

sudo systemctl restart kashiza
```

### Redis non connecté
```bash
sudo systemctl start redis
sudo systemctl enable redis
```

## Performances

### Optimisations VPS
```bash
# Augmenter les limites
sudo nano /etc/security/limits.conf
kashiza soft nofile 65536
kashiza hard nofile 65536

# Optimiser Redis
sudo nano /etc/redis/redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### Monitoring
```bash
# Utilisation
htop

# Logs temps réel
kashiza logs

# Métriques
curl http://localhost:8080/api/monitoring/status
```

## Coûts VPS Recommandés

| Usage | VPS | CPU | RAM | Prix/mois |
|-------|-----|-----|-----|-----------|
| Perso | DigitalOcean Droplet | 1 vCPU | 2 GB | ~$12 |
| Pro | Hetzner CPX11 | 2 vCPU | 4 GB | ~€6 |
| Team | AWS EC2 t3.small | 2 vCPU | 2 GB | ~$15 |
| Scale | OVH VPS Comfort | 4 vCPU | 8 GB | ~€15 |

## Support

Problèmes? Vérifier:
1. Logs: `kashiza logs`
2. Health: `kashiza-health`
3. Permissions: `ls -la /opt/kashiza`
4. Ports: `sudo netstat -tlnp | grep 8080`

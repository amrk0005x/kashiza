# 🚀 Déploiement VPS - Récapitulatif

## ✅ Oui, c'est 100% déployable sur un VPS fresh!

### Testé sur:
- ✅ Ubuntu 20.04 / 22.04
- ✅ Debian 11 / 12
- ✅ CentOS 8 / Rocky Linux 8
- ✅ Docker 20.10+

---

## 📋 Méthodes d'Installation

### 1️⃣ Auto-Install (1 commande)
```bash
curl -fsSL https://raw.githubusercontent.com/amirko/kashiza/main/deploy/quick-install.sh | sudo bash
```
**Temps:** ~5 minutes
**Config:** Automatique

### 2️⃣ Docker (Recommandé)
```bash
git clone https://github.com/amirko/kashiza.git
cd kashiza/deploy
cp .env.example .env
# Edit .env avec vos clés
docker-compose up -d
```
**Temps:** ~2 minutes
**Config:** Fichier .env

### 3️⃣ Manuel (Contrôle total)
```bash
git clone https://github.com/amirko/kashiza.git /opt/kashiza
cd /opt/kashiza
sudo bash deploy/install.sh
```
**Temps:** ~10 minutes
**Config:** Interactive

---

## 📦 Ce qui est installé automatiquement

| Composant | Utilisation |
|-----------|-------------|
| Python 3.11 + venv | Runtime |
| FastAPI + Uvicorn | API Server |
| Redis | Cache & sessions |
| Nginx | Reverse proxy |
| Certbot | SSL Let's Encrypt |
| Systemd service | Auto-start |
| UFW Firewall | Sécurité |
| Hermes CLI | Commandes faciles |

---

## 🔧 Commandes de gestion

```bash
kashiza start       # Démarrer
kashiza stop        # Arrêter
kashiza restart     # Redémarrer
kashiza status      # Statut service
kashiza logs        # Logs temps réel
kashiza update      # Mise à jour auto
kashiza backup      # Sauvegarde
kashiza shell       # Shell interactif
```

---

## 🌐 Accès après installation

```
Dashboard:    http://VOTRE_IP:8080
API:          http://VOTRE_IP:8080/api
WebSocket:    ws://VOTRE_IP:8080/ws/{client_id}
Health:       http://VOTRE_IP:8080/api/monitoring/health
```

Avec Nginx + SSL:
```
Dashboard:    https://votre-domaine.com
```

---

## 🔒 Sécurité (activée par défaut)

- ✅ Firewall UFW actif
- ✅ API keys chiffrées (AES-256)
- ✅ JWT authentication
- ✅ Rate limiting (100 req/min)
- ✅ Auto-fail2ban sur ports
- ✅ Logs audités
- ✅ Permissions 600 sur .env

---

## 📊 Ressources requises

| Type | CPU | RAM | Disk | Prix ~ |
|------|-----|-----|------|--------|
| Perso | 1 vCPU | 2 GB | 20 GB | $5-10/mois |
| Pro | 2 vCPU | 4 GB | 40 GB | $10-20/mois |
| Team | 4 vCPU | 8 GB | 80 GB | $20-40/mois |

**Fournisseurs recommandés:**
- Hetzner (meilleur rapport qualité/prix)
- DigitalOcean (simple)
- OVH (Europe)
- AWS Lightsail (si déjà sur AWS)

---

## 🔄 Mise à jour

```bash
# Via CLI
kashiza update

# Manuelle
cd /opt/kashiza
sudo -u kashiza git pull
sudo -u kashiza bash -c "source venv/bin/activate && pip install -r requirements.txt"
sudo systemctl restart kashiza
```

---

## 🐛 Troubleshooting

### Service ne démarre pas
```bash
# Voir erreurs
journalctl -u kashiza -n 50

# Vérifier config
cat /opt/kashiza/.env

# Tester manuellement
sudo -u kashiza bash
cd /opt/kashiza
source venv/bin/activate
python -c "from api.enhanced_server import main; main()"
```

### Port déjà utilisé
```bash
# Trouver processus
sudo lsof -i :8080

# Changer port
sudo nano /opt/kashiza/.env
KASHIZA_PORT=8081
kashiza restart
```

### Vérification complète
```bash
bash /opt/kashiza/deploy/verify-install.sh
```

---

## 📁 Structure sur VPS

```
/opt/kashiza/
├── venv/                   # Python virtual env
├── data/                   # Database
├── logs/                   # Log files
├── plugins/                # Custom plugins
├── config/                 # Configuration
├── .env                    # Secrets (chmod 600)
└── deploy/
    ├── install.sh          # Install script
    ├── verify-install.sh   # Verification
    └── docker-compose.yml  # Docker config
```

---

## 📝 Configuration post-install

```bash
# 1. Éditer .env
sudo nano /opt/kashiza/.env

# Ajouter:
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# 2. Redémarrer
kashiza restart

# 3. Vérifier
kashiza-health
```

---

## 🎯 Prochaines étapes après install

1. **Configurer domaine** (optionnel mais recommandé)
   ```bash
   sudo certbot --nginx -d votre-domaine.com
   ```

2. **Créer premier user**
   ```bash
   curl -X POST http://localhost:8080/auth/login \
     -d '{"username": "admin", "password": "changeme"}'
   ```

3. **Ajouter clés API**
   - Via dashboard: http://IP:8080 → Security
   - Ou CLI: éditer `/opt/kashiza/.env`

4. **Tester**
   ```bash
   curl http://localhost:8080/api/agents
   ```

---

## 💡 Conseils

- **Backup auto:** `crontab -e` → `0 2 * * * kashiza backup`
- **Monitoring:** Dashboard inclut monitoring temps réel
- **Scale:** Utiliser Redis externe si > 1000 connexions WS
- **SSL:** Toujours utiliser HTTPS en production

---

## ❓ FAQ

**Q: Puis-je l'installer sur un VPS 2€/mois?**
R: Oui mais limite: 1 vCPU / 2GB RAM. Suffisant pour perso/test.

**Q: Faut-il un GPU?**
R: Non, tout est CPU. GPU uniquement si tu ajoutes du training ML.

**Q: Puis-je mettre à jour sans perdre mes données?**
R: Oui, données dans `/opt/kashiza/data/` (persists lors des updates).

**Q: Supporte-t-il Docker Swarm/K8s?**
R: Docker Compose inclus. Pour K8s, créer helm chart basé sur docker-compose.yml.

**Q: Comment désinstaller complètement?**
R: Utilise `kashiza uninstall` ou `sudo bash /opt/kashiza/deploy/uninstall.sh`

---

## 🗑️ Désinstallation

Pour supprimer complètement Kashiza:

```bash
# Méthode facile
kashiza uninstall

# Ou manuellement
sudo bash /opt/kashiza/deploy/uninstall.sh
```

**Le script de désinstallation supprime:**
- ✅ Service systemd arrêté et désactivé
- ✅ Répertoire `/opt/kashiza` entier
- ✅ Commandes CLI (`kashiza`, `kashiza-health`)
- ✅ Configurations nginx
- ✅ Règles firewall
- ✅ Cache Redis
- ✅ Logs et fichiers temporaires
- ✅ Option: backups (demande confirmation)

---

## 📞 Support

En cas de problème:
1. Vérifier logs: `kashiza logs`
2. Vérifier install: `bash deploy/verify-install.sh`
3. Vérifier health: `curl localhost:8080/api/monitoring/health`

---

**Ready to deploy! 🚀**

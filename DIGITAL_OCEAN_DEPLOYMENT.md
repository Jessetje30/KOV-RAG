# Digital Ocean Deployment Guide

## Quick Start

Volg deze stappen om de RAG applicatie op Digital Ocean te deployen.

## Voorbereiding

### 1. Digital Ocean Droplet Setup

- **Minimale specs**: 4GB RAM, 2 vCPUs, 80GB SSD
- **OS**: Ubuntu 22.04 LTS
- **IP**: 159.223.5.149 (jouw droplet)

### 2. Firewall Configuratie

Zorg dat de volgende poorten open staan in Digital Ocean firewall:

```bash
# SSH naar je droplet
ssh root@159.223.5.149

# Open poorten (als ufw actief is)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8501/tcp  # Streamlit (tijdelijk, later via nginx)
sudo ufw allow 8000/tcp  # Backend API (tijdelijk, later via nginx)
sudo ufw allow 6333/tcp  # Qdrant (optioneel, voor debugging)
sudo ufw enable

# Check status
sudo ufw status
```

**Belangrijk**: Check ook de Digital Ocean Cloud Firewall in het control panel!

## Deployment met Docker Compose

### Stap 1: Installeer Docker (als nog niet gedaan)

```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version
```

### Stap 2: Clone Repository

```bash
cd /opt
git clone https://github.com/Jessetje30/KOV-RAG.git
cd KOV-RAG
```

### Stap 3: Configureer Environment Variables

```bash
# Kopieer .env.example naar .env
cp .env.example .env

# Edit .env met je productie settings
nano .env
```

**Belangrijke settings voor productie:**

```bash
# OpenAI API
OPENAI_API_KEY=your_real_openai_api_key_here
USE_OPENAI=true
OPENAI_LLM_MODEL=gpt-4
OPENAI_EMBED_MODEL=text-embedding-3-large

# JWT Secret (genereer nieuwe!)
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Cookie Encryption
COOKIE_ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Database
DATABASE_URL=sqlite:///./rag_app.db

# Qdrant (gebruik container naam)
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Frontend (gebruik publiek IP of domain)
BACKEND_URL=http://159.223.5.149:8000

# CORS (update met je domain)
CORS_ORIGINS=http://159.223.5.149:8501,http://159.223.5.149:3000,http://localhost:8501
```

### Stap 4: Start Applicatie met Docker Compose

```bash
# Build en start alle containers
docker compose up -d --build

# Check of alles draait
docker compose ps

# Check logs
docker compose logs -f
```

### Stap 5: Verifieer Deployment

Test elk component:

```bash
# Test Qdrant
curl http://localhost:6333/health

# Test Backend
curl http://localhost:8000/health

# Test Frontend (in browser)
# Open: http://159.223.5.149:8501
```

## Troubleshooting

### Container draait niet

```bash
# Check container status
docker compose ps

# Check logs van specifieke service
docker compose logs backend
docker compose logs frontend
docker compose logs qdrant

# Restart containers
docker compose restart
```

### Kan niet bereiken vanaf internet

1. **Check firewall**:
```bash
sudo ufw status
sudo iptables -L
```

2. **Check Digital Ocean Cloud Firewall** in control panel

3. **Check of services luisteren op juiste interface**:
```bash
# Should show 0.0.0.0:8501 en 0.0.0.0:8000
sudo netstat -tulpn | grep -E '8501|8000|6333'
```

4. **Check Docker port binding**:
```bash
docker compose ps
# Ports should show: 0.0.0.0:8501->8501/tcp
```

### Environment variables niet geladen

```bash
# Check of .env bestaat
ls -la /opt/KOV-RAG/.env

# Restart containers na .env changes
docker compose down
docker compose up -d
```

### Database errors

```bash
# Reset database (VOORZICHTIG: verliest data!)
docker compose down -v
docker compose up -d
```

## Productie Best Practices

### 1. Gebruik Nginx Reverse Proxy

Voordelen:
- HTTPS/SSL support
- Domain name mapping
- Better performance
- Security headers

Zie: `NGINX_SETUP.md` voor instructies

### 2. Automatische Updates

Maak een update script:

```bash
#!/bin/bash
# update.sh

cd /opt/KOV-RAG
git pull
docker compose down
docker compose up -d --build
```

### 3. Backups

```bash
# Backup volumes
docker run --rm \
  -v rag-app_qdrant_data:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar czf /backup/qdrant-backup-$(date +%Y%m%d).tar.gz /data

# Backup database
cp /opt/KOV-RAG/backend/rag_app.db /opt/KOV-RAG/backups/
```

### 4. Monitoring

```bash
# Check resource usage
docker stats

# Setup logs rotation
sudo nano /etc/logrotate.d/docker-compose
```

### 5. Security

```bash
# Disable root login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no

# Use SSH keys only
# Disable password authentication

# Keep system updated
sudo apt update && sudo apt upgrade -y

# Setup fail2ban
sudo apt install fail2ban -y
```

## Volgende Stappen

1. **DNS Setup**: Wijs een domain naar 159.223.5.149
2. **SSL/HTTPS**: Gebruik Certbot voor gratis SSL certificaat
3. **Nginx**: Setup reverse proxy (zie NGINX_SETUP.md)
4. **Monitoring**: Setup Prometheus/Grafana
5. **Backups**: Automatiseer backups

## Support

Bij problemen:
1. Check logs: `docker compose logs -f`
2. Check GitHub issues: https://github.com/Jessetje30/KOV-RAG/issues
3. Verify firewall settings in DO control panel

# Deployment Guide - LaboonChat2

> **Guida completa per il deployment di LaboonChat2 in ambienti di produzione**

Questa guida fornisce istruzioni dettagliate per il deployment di LaboonChat2 in diversi ambienti, dalla configurazione locale al deployment in produzione.

## 📋 Indice

- [Panoramica del Deployment](#panoramica-del-deployment)
- [Requisiti di Sistema](#requisiti-di-sistema)
- [Deployment Locale](#deployment-locale)
- [Deployment Docker](#deployment-docker)
- [Deployment Cloud](#deployment-cloud)
- [Configurazione di Produzione](#configurazione-di-produzione)
- [Monitoring e Logging](#monitoring-e-logging)
- [Backup e Recovery](#backup-e-recovery)
- [Sicurezza in Produzione](#sicurezza-in-produzione)
- [Troubleshooting](#troubleshooting)

---

## Panoramica del Deployment

### Architetture di Deployment Supportate

LaboonChat2 supporta diverse architetture di deployment:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Deployment Options                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │     Local       │  │     Docker      │  │     Cloud       │ │
│  │   Development   │  │   Container     │  │   Production    │ │
│  │                 │  │                 │  │                 │ │
│  │ • Quick setup   │  │ • Isolated      │  │ • Scalable      │ │
│  │ • Development   │  │ • Reproducible  │  │ • Managed       │ │
│  │ • Testing       │  │ • Portable      │  │ • Monitored     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Standalone    │  │   Distributed   │  │   Kubernetes    │ │
│  │    Server       │  │    Network      │  │    Cluster      │ │
│  │                 │  │                 │  │                 │ │
│  │ • Single node   │  │ • Multi-node    │  │ • Orchestrated  │ │
│  │ • Simple setup  │  │ • Load balanced │  │ • Auto-scaling  │ │
│  │ • Small scale   │  │ • High availability│ • Enterprise    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Requisiti di Sistema

### Requisiti Hardware Minimi

```yaml
# Ambiente di Sviluppo
development:
  cpu: 2 cores
  memory: 4 GB RAM
  storage: 10 GB
  network: 100 Mbps

# Ambiente di Test
testing:
  cpu: 4 cores
  memory: 8 GB RAM
  storage: 50 GB
  network: 1 Gbps

# Ambiente di Produzione
production:
  cpu: 8+ cores
  memory: 16+ GB RAM
  storage: 100+ GB SSD
  network: 10+ Gbps
```

### Requisiti Software

```yaml
# Sistema Operativo
os_support:
  - Ubuntu 20.04+ LTS
  - CentOS 8+
  - Windows 10/11
  - macOS 11+

# Runtime
python:
  version: "3.9+"
  packages:
    - asyncio
    - cryptography
    - aiohttp
    - websockets

# Database (Opzionale)
database:
  sqlite: "Built-in"
  postgresql: "13+"
  mysql: "8.0+"

# Reverse Proxy (Produzione)
proxy:
  nginx: "1.20+"
  apache: "2.4+"
  traefik: "2.0+"
```

---

## Deployment Locale

### Setup Rapido per Sviluppo

```bash
# 1. Clone del repository
git clone https://github.com/your-org/LaboonChat2.git
cd LaboonChat2

# 2. Setup ambiente virtuale
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. Installazione dipendenze
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Per sviluppo

# 4. Configurazione iniziale
cp config/config.example.json config/config.json
python -m laboon_chat2.setup --init

# 5. Avvio applicazione
python -m laboon_chat2.launcher.laboon_launcher
```

### Configurazione Ambiente di Sviluppo

```json
{
  "environment": "development",
  "debug": true,
  "logging": {
    "level": "DEBUG",
    "file": "logs/laboon_dev.log",
    "console": true
  },
  "network": {
    "port": 9494,
    "host": "localhost",
    "discovery": {
      "enabled": true,
      "bootstrap_peers": []
    }
  },
  "security": {
    "encryption": "development",
    "key_rotation_interval": 86400,
    "audit_logging": true
  },
  "plugins": {
    "enabled": ["chatbot", "file_sharing"],
    "development_mode": true
  }
}
```

### Script di Sviluppo

```bash
#!/bin/bash
# scripts/dev-setup.sh

set -e

echo "🚀 Setting up LaboonChat2 development environment..."

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2)
required_version="3.9.0"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.9+ required. Found: $python_version"
    exit 1
fi

# Setup virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
pre-commit install

# Initialize configuration
if [ ! -f "config/config.json" ]; then
    echo "⚙️ Initializing configuration..."
    cp config/config.example.json config/config.json
fi

# Create data directories
mkdir -p data/{messages,files,keys,logs}

# Run initial tests
echo "🧪 Running initial tests..."
pytest tests/test_basic.py -v

echo "✅ Development environment ready!"
echo "🎯 Run: python -m laboon_chat2.launcher.laboon_launcher"
```

---

## Deployment Docker

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 laboon && \
    chown -R laboon:laboon /app
USER laboon

# Create data directories
RUN mkdir -p data/{messages,files,keys,logs}

# Expose port
EXPOSE 9494

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -m laboon_chat2.health_check || exit 1

# Start application
CMD ["python", "-m", "laboon_chat2.launcher.laboon_launcher"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  laboonchat2:
    build: .
    container_name: laboonchat2
    restart: unless-stopped
    ports:
      - "9494:9494"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - ./logs:/app/logs
    environment:
      - LABOON_ENV=production
      - LABOON_LOG_LEVEL=info
      - LABOON_CONFIG_PATH=/app/config/config.json
    networks:
      - laboon-network
    healthcheck:
      test: ["CMD", "python", "-m", "laboon_chat2.health_check"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Reverse proxy (opzionale)
  nginx:
    image: nginx:alpine
    container_name: laboon-proxy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - laboonchat2
    networks:
      - laboon-network

  # Monitoring (opzionale)
  prometheus:
    image: prom/prometheus
    container_name: laboon-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    networks:
      - laboon-network

  grafana:
    image: grafana/grafana
    container_name: laboon-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    networks:
      - laboon-network

networks:
  laboon-network:
    driver: bridge

volumes:
  prometheus-data:
  grafana-data:
```

### Build e Deploy con Docker

```bash
#!/bin/bash
# scripts/docker-deploy.sh

set -e

echo "🐳 Building and deploying LaboonChat2 with Docker..."

# Build image
echo "🔨 Building Docker image..."
docker build -t laboonchat2:latest .

# Tag for registry (se necessario)
if [ "$1" = "push" ]; then
    echo "📤 Pushing to registry..."
    docker tag laboonchat2:latest your-registry/laboonchat2:latest
    docker push your-registry/laboonchat2:latest
fi

# Deploy with docker-compose
echo "🚀 Deploying with docker-compose..."
docker-compose down
docker-compose up -d

# Wait for health check
echo "⏳ Waiting for application to be healthy..."
timeout 60 bash -c 'until docker-compose ps | grep -q "healthy"; do sleep 2; done'

echo "✅ Deployment completed!"
echo "🌐 Application available at: http://localhost:9494"
```

---

## Deployment Cloud

### AWS Deployment

#### EC2 Instance

```bash
#!/bin/bash
# scripts/aws-ec2-deploy.sh

# Launch EC2 instance
aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --instance-type t3.medium \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxxxxxx \
    --subnet-id subnet-xxxxxxxxx \
    --user-data file://scripts/ec2-user-data.sh \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=LaboonChat2}]'
```

```bash
#!/bin/bash
# scripts/ec2-user-data.sh

yum update -y
yum install -y python3 python3-pip git docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Start Docker
systemctl start docker
systemctl enable docker

# Clone and deploy
cd /opt
git clone https://github.com/your-org/LaboonChat2.git
cd LaboonChat2

# Setup configuration
cp config/config.example.json config/config.json
# Customize configuration for production

# Deploy
docker-compose up -d

# Setup log rotation
cat > /etc/logrotate.d/laboonchat2 << EOF
/opt/LaboonChat2/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
EOF
```

#### ECS Deployment

```json
{
  "family": "laboonchat2",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "laboonchat2",
      "image": "your-registry/laboonchat2:latest",
      "portMappings": [
        {
          "containerPort": 9494,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "LABOON_ENV",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/laboonchat2",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "python -m laboon_chat2.health_check || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### Google Cloud Platform

```yaml
# gcp-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: laboonchat2
spec:
  replicas: 3
  selector:
    matchLabels:
      app: laboonchat2
  template:
    metadata:
      labels:
        app: laboonchat2
    spec:
      containers:
      - name: laboonchat2
        image: gcr.io/your-project/laboonchat2:latest
        ports:
        - containerPort: 9494
        env:
        - name: LABOON_ENV
          value: "production"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          exec:
            command:
            - python
            - -m
            - laboon_chat2.health_check
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          exec:
            command:
            - python
            - -m
            - laboon_chat2.health_check
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: laboonchat2-service
spec:
  selector:
    app: laboonchat2
  ports:
  - port: 80
    targetPort: 9494
  type: LoadBalancer
```

### Azure Container Instances

```yaml
# azure-container-group.yaml
apiVersion: 2019-12-01
location: eastus
name: laboonchat2-group
properties:
  containers:
  - name: laboonchat2
    properties:
      image: your-registry.azurecr.io/laboonchat2:latest
      resources:
        requests:
          cpu: 1
          memoryInGb: 2
      ports:
      - port: 9494
        protocol: TCP
      environmentVariables:
      - name: LABOON_ENV
        value: production
  osType: Linux
  restartPolicy: Always
  ipAddress:
    type: Public
    ports:
    - protocol: TCP
      port: 9494
```

---

## Configurazione di Produzione

### Configurazione Base di Produzione

```json
{
  "environment": "production",
  "debug": false,
  "logging": {
    "level": "INFO",
    "file": "/var/log/laboonchat2/app.log",
    "console": false,
    "rotation": {
      "max_size": "100MB",
      "backup_count": 10
    }
  },
  "network": {
    "port": 9494,
    "host": "0.0.0.0",
    "max_connections": 1000,
    "timeout": 30,
    "discovery": {
      "enabled": true,
      "bootstrap_peers": [
        "peer1.example.com:9494",
        "peer2.example.com:9494"
      ]
    }
  },
  "security": {
    "encryption": "production",
    "key_rotation_interval": 3600,
    "audit_logging": true,
    "rate_limiting": {
      "enabled": true,
      "max_requests_per_minute": 100
    }
  },
  "database": {
    "type": "sqlite",
    "path": "/var/lib/laboonchat2/data.db",
    "backup": {
      "enabled": true,
      "interval": 3600,
      "retention_days": 30
    }
  },
  "plugins": {
    "enabled": ["chatbot", "file_sharing", "encryption"],
    "development_mode": false
  },
  "monitoring": {
    "metrics": {
      "enabled": true,
      "port": 9595
    },
    "health_check": {
      "enabled": true,
      "endpoint": "/health"
    }
  }
}
```

### Variabili d'Ambiente

```bash
# Environment variables for production
export LABOON_ENV=production
export LABOON_CONFIG_PATH=/etc/laboonchat2/config.json
export LABOON_DATA_DIR=/var/lib/laboonchat2
export LABOON_LOG_DIR=/var/log/laboonchat2
export LABOON_SECRET_KEY=your-secret-key
export LABOON_DB_ENCRYPTION_KEY=your-db-encryption-key
```

### Configurazione Nginx

```nginx
# /etc/nginx/sites-available/laboonchat2
upstream laboonchat2_backend {
    server 127.0.0.1:9494;
    # Add more servers for load balancing
    # server 127.0.0.1:9495;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;

    # Proxy Configuration
    location / {
        proxy_pass http://laboonchat2_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://laboonchat2_backend/health;
        access_log off;
    }

    # Static files (if any)
    location /static/ {
        alias /var/www/laboonchat2/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## Monitoring e Logging

### Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'laboonchat2'
    static_configs:
      - targets: ['laboonchat2:9595']
    metrics_path: /metrics
    scrape_interval: 10s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "LaboonChat2 Monitoring",
    "panels": [
      {
        "title": "Active Connections",
        "type": "stat",
        "targets": [
          {
            "expr": "laboon_active_connections",
            "legendFormat": "Connections"
          }
        ]
      },
      {
        "title": "Messages per Second",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(laboon_messages_total[5m])",
            "legendFormat": "Messages/sec"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "process_resident_memory_bytes",
            "legendFormat": "Memory"
          }
        ]
      }
    ]
  }
}
```

### Logging Configuration

```python
# logging_config.py
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
        },
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/laboonchat2/app.log',
            'maxBytes': 100 * 1024 * 1024,  # 100MB
            'backupCount': 10,
            'formatter': 'detailed'
        },
        'security': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/laboonchat2/security.log',
            'maxBytes': 50 * 1024 * 1024,  # 50MB
            'backupCount': 20,
            'formatter': 'json'
        }
    },
    'loggers': {
        'laboon_chat2': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'laboon_chat2.security': {
            'handlers': ['security'],
            'level': 'WARNING',
            'propagate': False
        }
    }
}
```

---

## Backup e Recovery

### Backup Strategy

```bash
#!/bin/bash
# scripts/backup.sh

set -e

BACKUP_DIR="/var/backups/laboonchat2"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="laboonchat2_backup_$DATE"

echo "🔄 Starting backup: $BACKUP_NAME"

# Create backup directory
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

# Backup database
echo "📊 Backing up database..."
sqlite3 /var/lib/laboonchat2/data.db ".backup $BACKUP_DIR/$BACKUP_NAME/data.db"

# Backup configuration
echo "⚙️ Backing up configuration..."
cp -r /etc/laboonchat2/ "$BACKUP_DIR/$BACKUP_NAME/config/"

# Backup keys
echo "🔑 Backing up keys..."
cp -r /var/lib/laboonchat2/keys/ "$BACKUP_DIR/$BACKUP_NAME/keys/"

# Backup logs (last 7 days)
echo "📝 Backing up recent logs..."
find /var/log/laboonchat2/ -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/$BACKUP_NAME/logs/" \;

# Create archive
echo "📦 Creating archive..."
cd "$BACKUP_DIR"
tar -czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME/"
rm -rf "$BACKUP_NAME/"

# Cleanup old backups (keep last 30)
echo "🧹 Cleaning up old backups..."
ls -t laboonchat2_backup_*.tar.gz | tail -n +31 | xargs -r rm

echo "✅ Backup completed: $BACKUP_DIR/$BACKUP_NAME.tar.gz"
```

### Recovery Procedure

```bash
#!/bin/bash
# scripts/recovery.sh

set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

BACKUP_FILE="$1"
RECOVERY_DIR="/tmp/laboonchat2_recovery"

echo "🔄 Starting recovery from: $BACKUP_FILE"

# Stop application
echo "⏹️ Stopping application..."
systemctl stop laboonchat2

# Extract backup
echo "📦 Extracting backup..."
mkdir -p "$RECOVERY_DIR"
tar -xzf "$BACKUP_FILE" -C "$RECOVERY_DIR"

# Find backup directory
BACKUP_DIR=$(find "$RECOVERY_DIR" -name "laboonchat2_backup_*" -type d | head -1)

if [ -z "$BACKUP_DIR" ]; then
    echo "❌ Invalid backup file"
    exit 1
fi

# Backup current data
echo "💾 Backing up current data..."
cp -r /var/lib/laboonchat2/ "/var/lib/laboonchat2.backup.$(date +%Y%m%d_%H%M%S)"

# Restore database
echo "📊 Restoring database..."
cp "$BACKUP_DIR/data.db" /var/lib/laboonchat2/data.db

# Restore configuration
echo "⚙️ Restoring configuration..."
cp -r "$BACKUP_DIR/config/"* /etc/laboonchat2/

# Restore keys
echo "🔑 Restoring keys..."
cp -r "$BACKUP_DIR/keys/"* /var/lib/laboonchat2/keys/

# Set permissions
echo "🔒 Setting permissions..."
chown -R laboonchat2:laboonchat2 /var/lib/laboonchat2/
chmod 600 /var/lib/laboonchat2/keys/*

# Start application
echo "▶️ Starting application..."
systemctl start laboonchat2

# Verify recovery
echo "✅ Verifying recovery..."
sleep 10
if systemctl is-active --quiet laboonchat2; then
    echo "✅ Recovery completed successfully"
else
    echo "❌ Recovery failed - check logs"
    exit 1
fi

# Cleanup
rm -rf "$RECOVERY_DIR"
```

---

## Sicurezza in Produzione

### Hardening Checklist

```yaml
# Security hardening checklist
system_hardening:
  - name: "Disable root login"
    command: "sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config"
  
  - name: "Setup firewall"
    commands:
      - "ufw default deny incoming"
      - "ufw default allow outgoing"
      - "ufw allow 22/tcp"
      - "ufw allow 9494/tcp"
      - "ufw --force enable"
  
  - name: "Install fail2ban"
    commands:
      - "apt-get install -y fail2ban"
      - "systemctl enable fail2ban"

application_hardening:
  - name: "Run as non-root user"
    user: "laboonchat2"
    group: "laboonchat2"
  
  - name: "Secure file permissions"
    permissions:
      config: "600"
      keys: "600"
      logs: "644"
      data: "600"
  
  - name: "Enable audit logging"
    config: "security.audit_logging: true"

network_hardening:
  - name: "Use TLS for all connections"
    config: "network.tls.enabled: true"
  
  - name: "Implement rate limiting"
    config: "security.rate_limiting.enabled: true"
  
  - name: "Setup intrusion detection"
    tool: "OSSEC"
```

### SSL/TLS Configuration

```bash
#!/bin/bash
# scripts/setup-ssl.sh

# Generate SSL certificate (Let's Encrypt)
certbot --nginx -d your-domain.com

# Setup automatic renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -

# Test SSL configuration
curl -I https://your-domain.com
```

### Security Monitoring

```python
# security_monitor.py
import asyncio
import logging
from typing import Dict, List

class SecurityMonitor:
    def __init__(self):
        self.logger = logging.getLogger('security')
        self.threat_patterns = self.load_threat_patterns()
        self.alert_thresholds = {
            'failed_logins': 5,
            'suspicious_ips': 10,
            'rate_limit_violations': 100
        }
    
    async def monitor_security_events(self):
        """Monitor security events continuously."""
        while True:
            try:
                # Check for suspicious activities
                await self.check_failed_logins()
                await self.check_rate_limiting()
                await self.check_unusual_patterns()
                
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Security monitoring error: {e}")
    
    async def handle_security_incident(self, incident: Dict):
        """Handle detected security incident."""
        severity = incident.get('severity', 'medium')
        
        if severity == 'high':
            # Immediate action required
            await self.block_suspicious_ip(incident['ip'])
            await self.send_alert(incident)
        elif severity == 'medium':
            # Log and monitor
            self.logger.warning(f"Security incident: {incident}")
        
        # Update threat intelligence
        await self.update_threat_patterns(incident)
```

---

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

```bash
# Check logs
tail -f /var/log/laboonchat2/app.log

# Check configuration
python -m laboon_chat2.config --validate

# Check permissions
ls -la /var/lib/laboonchat2/
```

#### 2. Network Connectivity Issues

```bash
# Check port availability
netstat -tlnp | grep 9494

# Test connectivity
telnet your-domain.com 9494

# Check firewall
ufw status
```

#### 3. Performance Issues

```bash
# Check resource usage
htop
iotop

# Check application metrics
curl http://localhost:9595/metrics

# Analyze logs for bottlenecks
grep -i "slow\|timeout\|error" /var/log/laboonchat2/app.log
```

### Diagnostic Tools

```bash
#!/bin/bash
# scripts/diagnostics.sh

echo "🔍 LaboonChat2 Diagnostics"
echo "=========================="

# System information
echo "📊 System Information:"
uname -a
free -h
df -h

# Application status
echo "🚀 Application Status:"
systemctl status laboonchat2

# Network status
echo "🌐 Network Status:"
netstat -tlnp | grep 9494
ss -tlnp | grep 9494

# Log analysis
echo "📝 Recent Errors:"
tail -n 50 /var/log/laboonchat2/app.log | grep -i error

# Configuration validation
echo "⚙️ Configuration:"
python -m laboon_chat2.config --validate --verbose

# Health check
echo "❤️ Health Check:"
curl -s http://localhost:9494/health | jq .
```

### Performance Tuning

```python
# performance_tuning.py
class PerformanceTuner:
    def __init__(self):
        self.metrics = MetricsCollector()
        self.optimizer = SystemOptimizer()
    
    async def tune_performance(self):
        """Automatically tune system performance."""
        # Collect current metrics
        current_metrics = await self.metrics.collect()
        
        # Analyze bottlenecks
        bottlenecks = self.analyze_bottlenecks(current_metrics)
        
        # Apply optimizations
        for bottleneck in bottlenecks:
            optimization = self.get_optimization(bottleneck)
            await optimization.apply()
        
        # Verify improvements
        new_metrics = await self.metrics.collect()
        improvement = self.calculate_improvement(current_metrics, new_metrics)
        
        return improvement
```

---

## Conclusioni

Questa guida fornisce una base completa per il deployment di LaboonChat2 in diversi ambienti. Ricorda di:

- **🔒 Sicurezza Prima**: Implementa sempre le best practice di sicurezza
- **📊 Monitora Tutto**: Setup monitoring e alerting appropriati
- **💾 Backup Regolari**: Implementa una strategia di backup robusta
- **🧪 Testa Sempre**: Verifica deployment in ambiente di test prima della produzione
- **📚 Documenta**: Mantieni documentazione aggiornata delle configurazioni

Per supporto aggiuntivo, consulta la [documentazione completa](README.md) o contatta il team di sviluppo.

---

*Guida al deployment per LaboonChat2 v2.0.0*
*Ultima modifica: 2025-01-27*
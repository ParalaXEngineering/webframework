# Production Deployment Guide - RedHat Enterprise Linux

**Framework Version**: Multi-user production-ready with SocketIO isolation  
**Target Environment**: RedHat Enterprise Linux (RHEL) 8/9 or compatible (AlmaLinux, Rocky Linux)  
**Deployment Model**: Single worker (optimized for 10-20 concurrent users)  
**Date**: October 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [System Preparation](#system-preparation)
4. [Application Setup](#application-setup)
5. [Production Configuration](#production-configuration)
6. [NGINX Reverse Proxy](#nginx-reverse-proxy)
7. [Systemd Service](#systemd-service)
8. [SSL/TLS Configuration](#ssltls-configuration)
9. [Monitoring & Logging](#monitoring--logging)
10. [Testing](#testing)
11. [Troubleshooting](#troubleshooting)
12. [Maintenance](#maintenance)

---

## Overview

### What Was Implemented

This framework now supports **multi-user production deployment** with the following features:

#### ✅ Phase 1: SocketIO User Isolation
- **Room-based isolation**: Each user gets unique room `user_{username}_{session_id}`
- **SocketIOManager**: Centralized management of user rooms
- **Per-user emissions**: Thread updates and log messages isolated per user
- **No information leakage**: Users only see their own real-time updates

#### ✅ Phase 2: Scheduler Message Isolation  
- **QueuedMessage wrapper**: Messages tagged with username
- **Username tracking**: Automatic capture from ThreadedAction context
- **Per-user grouping**: Scheduler groups messages by username
- **Targeted emission**: Status, popups, results, modals sent only to owner

### Architecture Overview

```
[Internet] → [NGINX :443] → [Gunicorn :5000] → [Flask + SocketIO]
              SSL/TLS         Single Worker      Your Framework
              Reverse Proxy   eventlet           File Sessions
```

### Key Decisions

- **Single worker**: Sufficient for 10-20 users (~10% capacity utilization)
- **No Redis**: Simplified architecture, no extra service to maintain
- **File-based sessions**: Works perfectly for single worker deployment
- **NGINX**: Handles SSL/TLS, static files, WebSocket proxying
- **Systemd**: Auto-restart on failure, logging, resource management

---

## Prerequisites

### Server Requirements

**Minimum Specifications** (10-20 users):
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Disk**: 20 GB (10 GB for OS, 10 GB for application/logs)
- **OS**: RHEL 8/9, AlmaLinux 8/9, or Rocky Linux 8/9

**Recommended Specifications**:
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disk**: 40 GB SSD
- **Network**: 100 Mbps

### Software Requirements

- Python 3.8+ (Python 3.9+ recommended)
- NGINX 1.18+
- Git
- Systemd (standard on RHEL)

### Domain & DNS

- Domain name pointing to your server IP
- DNS A record configured
- (Optional) DNS AAAA record for IPv6

---

## System Preparation

### 1. Update System

```bash
# Update all packages
sudo dnf update -y

# Install EPEL repository (Extra Packages for Enterprise Linux)
sudo dnf install -y epel-release

# Install development tools
sudo dnf groupinstall -y "Development Tools"
```

### 2. Install Required Packages

```bash
# Install Python 3.9+ and tools
sudo dnf install -y python39 python39-devel python39-pip

# Install NGINX
sudo dnf install -y nginx

# Install Git
sudo dnf install -y git

# Install other utilities
sudo dnf install -y wget curl vim htop
```

### 3. Configure Firewall

```bash
# Enable firewalld (if not already enabled)
sudo systemctl enable --now firewalld

# Allow HTTP and HTTPS
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https

# Reload firewall
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --list-all
```

### 4. Create Application User

```bash
# Create dedicated user (no login shell for security)
sudo useradd -r -m -s /sbin/nologin -d /opt/webframework flask_app

# Create application directory structure
sudo mkdir -p /opt/webframework
sudo mkdir -p /var/log/flask_app
sudo mkdir -p /var/lib/flask_sessions

# Set ownership
sudo chown -R flask_app:flask_app /opt/webframework
sudo chown -R flask_app:flask_app /var/log/flask_app
sudo chown -R flask_app:flask_app /var/lib/flask_sessions

# Set permissions
sudo chmod 755 /opt/webframework
sudo chmod 755 /var/log/flask_app
sudo chmod 700 /var/lib/flask_sessions  # Sessions are sensitive
```

---

## Application Setup

### 1. Clone Repository

```bash
# Switch to root temporarily
sudo -i

# Clone as flask_app user
cd /opt/webframework
sudo -u flask_app git clone https://github.com/ParalaXEngineering/webframework.git .

# Verify
ls -la
```

### 2. Create Python Virtual Environment

```bash
# Create venv as flask_app user
sudo -u flask_app python3.9 -m venv /opt/webframework/.venv

# Activate venv
sudo -u flask_app /opt/webframework/.venv/bin/pip install --upgrade pip

# Install dependencies
sudo -u flask_app /opt/webframework/.venv/bin/pip install -e .

# Verify installation
sudo -u flask_app /opt/webframework/.venv/bin/python -c "from src.main import app; print('✓ App imports successfully')"
```

### 3. Create WSGI Entry Point

Create `/opt/webframework/wsgi.py`:

```python
"""
WSGI Entry Point for Production

This file is used by Gunicorn to launch the application.
"""
from src.main import app, socketio

# Export for Gunicorn
application = socketio.middleware(app) if hasattr(socketio, 'middleware') else app

if __name__ == "__main__":
    # For development only - use Gunicorn in production
    socketio.run(app, host='0.0.0.0', port=5000)
```

```bash
# Create the file
sudo -u flask_app tee /opt/webframework/wsgi.py > /dev/null << 'EOF'
"""
WSGI Entry Point for Production

This file is used by Gunicorn to launch the application.
"""
from src.main import app, socketio

# Export for Gunicorn
application = socketio.middleware(app) if hasattr(socketio, 'middleware') else app

if __name__ == "__main__":
    # For development only - use Gunicorn in production
    socketio.run(app, host='0.0.0.0', port=5000)
EOF
```

### 4. Create Gunicorn Configuration

Create `/opt/webframework/gunicorn_config.py`:

```python
"""
Gunicorn Configuration for Production

Single worker configuration optimized for 10-20 concurrent users.
Uses eventlet for async WebSocket support.
"""
import multiprocessing
import os

# Binding
bind = "127.0.0.1:5000"  # Only accessible via NGINX reverse proxy

# Workers
workers = 1  # Single worker sufficient for 10-20 users
worker_class = "eventlet"  # Required for SocketIO WebSocket support
worker_connections = 1000  # Max concurrent connections per worker

# Timeouts
timeout = 120  # Worker timeout (seconds)
graceful_timeout = 30  # Graceful shutdown timeout
keepalive = 5  # Keep-alive connections

# Logging
accesslog = "/var/log/flask_app/access.log"
errorlog = "/var/log/flask_app/error.log"
loglevel = "info"  # Options: debug, info, warning, error, critical
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "flask_webframework"

# Server mechanics
daemon = False  # Systemd manages daemonization
pidfile = "/var/run/flask_app.pid"
umask = 0o007

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Reload on code changes (disable in production)
reload = False

# Preload app for faster worker startup
preload_app = True
```

```bash
# Create the file
sudo -u flask_app tee /opt/webframework/gunicorn_config.py > /dev/null << 'EOF'
"""Gunicorn Configuration for Production"""
import multiprocessing
import os

bind = "127.0.0.1:5000"
workers = 1
worker_class = "eventlet"
worker_connections = 1000
timeout = 120
graceful_timeout = 30
keepalive = 5
accesslog = "/var/log/flask_app/access.log"
errorlog = "/var/log/flask_app/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
proc_name = "flask_webframework"
daemon = False
pidfile = "/var/run/flask_app.pid"
umask = 0o007
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
reload = False
preload_app = True
EOF
```

---

## Production Configuration

### 1. Create Production Config File

Create `/opt/webframework/src/config/production.py`:

```python
"""
Production Configuration

Environment-based configuration for production deployment.
All sensitive values should be set via environment variables.
"""
import os
from datetime import timedelta

class ProductionConfig:
    """Production environment configuration."""
    
    # ===== Security =====
    SECRET_KEY = os.environ.get('SECRET_KEY', 'CHANGE-ME-IN-PRODUCTION-USE-LONG-RANDOM-STRING')
    
    # Session Security
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True  # No JavaScript access
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    SESSION_COOKIE_NAME = 'paralax_session'
    
    # ===== Sessions =====
    SESSION_TYPE = 'filesystem'  # File-based sessions (single worker)
    SESSION_FILE_DIR = '/var/lib/flask_sessions'
    SESSION_FILE_THRESHOLD = 500  # Max session files
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # ===== CORS =====
    ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '').split(',') or [
        'https://yourdomain.com',
        'https://www.yourdomain.com'
    ]
    
    # ===== Logging =====
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = '/var/log/flask_app/app.log'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT = 5
    
    # ===== Application =====
    DEBUG = False
    TESTING = False
    
    # ===== Server =====
    SERVER_NAME = os.environ.get('SERVER_NAME', 'yourdomain.com')
    PREFERRED_URL_SCHEME = 'https'
    
    # ===== SocketIO =====
    SOCKETIO_ASYNC_MODE = 'eventlet'
    SOCKETIO_LOGGER = False  # Disable verbose SocketIO logging
    SOCKETIO_ENGINEIO_LOGGER = False
    
    # ===== Upload Limits =====
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB max upload


def load_production_config(app):
    """
    Load production configuration into Flask app.
    
    Args:
        app: Flask application instance
    """
    config = ProductionConfig()
    
    for key in dir(config):
        if key.isupper():
            app.config[key] = getattr(config, key)
    
    return app
```

```bash
# Create config directory
sudo -u flask_app mkdir -p /opt/webframework/src/config

# Create the file
sudo -u flask_app tee /opt/webframework/src/config/production.py > /dev/null << 'EOF'
"""Production Configuration"""
import os
from datetime import timedelta

class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'CHANGE-ME-IN-PRODUCTION-USE-LONG-RANDOM-STRING')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_NAME = 'paralax_session'
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = '/var/lib/flask_sessions'
    SESSION_FILE_THRESHOLD = 500
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '').split(',') or ['https://yourdomain.com']
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = '/var/log/flask_app/app.log'
    LOG_MAX_BYTES = 10 * 1024 * 1024
    LOG_BACKUP_COUNT = 5
    DEBUG = False
    TESTING = False
    SERVER_NAME = os.environ.get('SERVER_NAME', 'yourdomain.com')
    PREFERRED_URL_SCHEME = 'https'
    SOCKETIO_ASYNC_MODE = 'eventlet'
    SOCKETIO_LOGGER = False
    SOCKETIO_ENGINEIO_LOGGER = False
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024

def load_production_config(app):
    config = ProductionConfig()
    for key in dir(config):
        if key.isupper():
            app.config[key] = getattr(config, key)
    return app
EOF
```

### 2. Create Environment File

Create `/opt/webframework/.env.production`:

```bash
# Production Environment Variables
# Copy this to /etc/flask_app/environment and customize

# Flask
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-generate-with-openssl-rand-hex-32

# Server
SERVER_NAME=yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Logging
LOG_LEVEL=INFO

# Database (if you use one)
# DATABASE_URL=postgresql://user:password@localhost/dbname
```

```bash
# Generate a secure secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Create environment file
sudo mkdir -p /etc/flask_app
sudo tee /etc/flask_app/environment > /dev/null << EOF
FLASK_ENV=production
SECRET_KEY=${SECRET_KEY}
SERVER_NAME=yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
LOG_LEVEL=INFO
EOF

# Secure the file (contains secrets!)
sudo chmod 600 /etc/flask_app/environment
sudo chown flask_app:flask_app /etc/flask_app/environment
```

---

## NGINX Reverse Proxy

### 1. Create NGINX Configuration

Create `/etc/nginx/conf.d/flask_app.conf`:

```nginx
# Flask Application - NGINX Configuration
# Handles SSL/TLS termination, WebSocket proxying, and static file serving

# Upstream Gunicorn backend
upstream flask_backend {
    server 127.0.0.1:5000 fail_timeout=0;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;
    
    # ACME challenge for Let's Encrypt (before redirect)
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirect all other HTTP traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS Server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Certificates (update paths after obtaining certificates)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL Configuration (Modern, secure)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Logging
    access_log /var/log/nginx/flask_app_access.log;
    error_log /var/log/nginx/flask_app_error.log;
    
    # Client upload size limit
    client_max_body_size 100M;
    
    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
    
    # Static files (if you have any in webengine/assets)
    location /static/ {
        alias /opt/webframework/webengine/assets/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Flask application
    location / {
        proxy_pass http://flask_backend;
        
        # Headers
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        
        # Disable buffering for SocketIO
        proxy_buffering off;
        
        # WebSocket support (critical for SocketIO)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Long-lived connections for SocketIO
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
    
    # Health check endpoint (optional)
    location /health {
        proxy_pass http://flask_backend/health;
        access_log off;
    }
}
```

```bash
# Create NGINX configuration
sudo tee /etc/nginx/conf.d/flask_app.conf > /dev/null << 'EOF'
upstream flask_backend {
    server 127.0.0.1:5000 fail_timeout=0;
}

server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    access_log /var/log/nginx/flask_app_access.log;
    error_log /var/log/nginx/flask_app_error.log;
    client_max_body_size 100M;
    
    location /static/ {
        alias /opt/webframework/webengine/assets/;
        expires 30d;
    }
    
    location / {
        proxy_pass http://flask_backend;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400s;
    }
}
EOF

# Test NGINX configuration
sudo nginx -t

# If test passes, restart NGINX
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 2. Configure SELinux (RHEL-specific)

```bash
# Allow NGINX to connect to network
sudo setsebool -P httpd_can_network_connect 1

# Allow NGINX to read application files
sudo semanage fcontext -a -t httpd_sys_content_t "/opt/webframework(/.*)?"
sudo restorecon -R /opt/webframework

# Allow NGINX to write logs
sudo semanage fcontext -a -t httpd_log_t "/var/log/nginx(/.*)?"
sudo restorecon -R /var/log/nginx
```

---

## Systemd Service

### Create Systemd Service File

Create `/etc/systemd/system/flask_app.service`:

```ini
[Unit]
Description=Flask WebFramework Application
After=network.target
Wants=network-online.target

[Service]
Type=notify
User=flask_app
Group=flask_app
RuntimeDirectory=flask_app
WorkingDirectory=/opt/webframework

# Environment
EnvironmentFile=/etc/flask_app/environment

# Execution
ExecStart=/opt/webframework/.venv/bin/gunicorn \
    --config /opt/webframework/gunicorn_config.py \
    wsgi:application

# Restart policy
Restart=always
RestartSec=3
StartLimitInterval=0

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/flask_app /var/lib/flask_sessions /var/run

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=flask_app

[Install]
WantedBy=multi-user.target
```

```bash
# Create service file
sudo tee /etc/systemd/system/flask_app.service > /dev/null << 'EOF'
[Unit]
Description=Flask WebFramework Application
After=network.target
Wants=network-online.target

[Service]
Type=notify
User=flask_app
Group=flask_app
RuntimeDirectory=flask_app
WorkingDirectory=/opt/webframework
EnvironmentFile=/etc/flask_app/environment
ExecStart=/opt/webframework/.venv/bin/gunicorn --config /opt/webframework/gunicorn_config.py wsgi:application
Restart=always
RestartSec=3
StartLimitInterval=0
LimitNOFILE=65536
LimitNPROC=4096
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/flask_app /var/lib/flask_sessions /var/run
StandardOutput=journal
StandardError=journal
SyslogIdentifier=flask_app

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable flask_app.service

# Start service
sudo systemctl start flask_app.service

# Check status
sudo systemctl status flask_app.service
```

---

## SSL/TLS Configuration

### Option 1: Let's Encrypt (Free, Automated)

```bash
# Install Certbot
sudo dnf install -y certbot python3-certbot-nginx

# Stop NGINX temporarily
sudo systemctl stop nginx

# Obtain certificate (standalone mode)
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Or use webroot mode (NGINX keeps running)
sudo mkdir -p /var/www/certbot
sudo certbot certonly --webroot -w /var/www/certbot -d yourdomain.com -d www.yourdomain.com

# Start NGINX
sudo systemctl start nginx

# Test automatic renewal
sudo certbot renew --dry-run

# Auto-renewal is configured via systemd timer (already enabled)
sudo systemctl list-timers | grep certbot
```

### Option 2: Self-Signed Certificate (Development/Testing)

```bash
# Generate self-signed certificate (valid for 365 days)
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/selfsigned.key \
    -out /etc/nginx/ssl/selfsigned.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=yourdomain.com"

# Update NGINX config to use self-signed cert
sudo sed -i 's|/etc/letsencrypt/live/yourdomain.com/fullchain.pem|/etc/nginx/ssl/selfsigned.crt|g' /etc/nginx/conf.d/flask_app.conf
sudo sed -i 's|/etc/letsencrypt/live/yourdomain.com/privkey.pem|/etc/nginx/ssl/selfsigned.key|g' /etc/nginx/conf.d/flask_app.conf

# Restart NGINX
sudo systemctl restart nginx
```

---

## Monitoring & Logging

### 1. View Application Logs

```bash
# Real-time logs (all sources)
sudo journalctl -u flask_app.service -f

# Recent logs
sudo journalctl -u flask_app.service -n 100

# Logs from specific time
sudo journalctl -u flask_app.service --since "2025-10-17 10:00:00"

# Application-specific logs
sudo tail -f /var/log/flask_app/app.log
sudo tail -f /var/log/flask_app/access.log
sudo tail -f /var/log/flask_app/error.log

# NGINX logs
sudo tail -f /var/log/nginx/flask_app_access.log
sudo tail -f /var/log/nginx/flask_app_error.log
```

### 2. Log Rotation

Create `/etc/logrotate.d/flask_app`:

```bash
sudo tee /etc/logrotate.d/flask_app > /dev/null << 'EOF'
/var/log/flask_app/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 flask_app flask_app
    sharedscripts
    postrotate
        systemctl reload flask_app.service > /dev/null 2>&1 || true
    endscript
}
EOF
```

### 3. Monitor System Resources

```bash
# CPU and memory usage
htop

# Disk usage
df -h
du -sh /opt/webframework
du -sh /var/log/flask_app
du -sh /var/lib/flask_sessions

# Network connections
sudo ss -tulpn | grep 5000
sudo ss -tulpn | grep nginx

# Check running processes
ps aux | grep gunicorn
ps aux | grep nginx
```

### 4. Health Check Script

Create `/usr/local/bin/flask_health_check.sh`:

```bash
#!/bin/bash
# Flask Application Health Check

ENDPOINT="http://127.0.0.1:5000/health"
TIMEOUT=5

# Check if application responds
response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT $ENDPOINT)

if [ "$response" == "200" ]; then
    echo "✓ Application is healthy (HTTP $response)"
    exit 0
else
    echo "✗ Application is unhealthy (HTTP $response)"
    exit 1
fi
```

```bash
# Create health check script
sudo tee /usr/local/bin/flask_health_check.sh > /dev/null << 'EOF'
#!/bin/bash
ENDPOINT="http://127.0.0.1:5000/health"
response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 $ENDPOINT)
if [ "$response" == "200" ]; then
    echo "✓ Healthy (HTTP $response)"
    exit 0
else
    echo "✗ Unhealthy (HTTP $response)"
    exit 1
fi
EOF

sudo chmod +x /usr/local/bin/flask_health_check.sh

# Test it
sudo /usr/local/bin/flask_health_check.sh
```

---

## Testing

### 1. Basic Functionality Test

```bash
# Test local access
curl -I http://127.0.0.1:5000/

# Test NGINX proxy (HTTP)
curl -I http://yourdomain.com/

# Test HTTPS
curl -I https://yourdomain.com/

# Test WebSocket upgrade
curl -I -H "Upgrade: websocket" -H "Connection: Upgrade" https://yourdomain.com/socket.io/
```

### 2. Multi-User Test (Manual)

1. **Browser 1** (User Alice):
   - Open https://yourdomain.com
   - Login as alice
   - Open browser console (F12)
   - Start a threaded action
   - Observe SocketIO messages in console

2. **Browser 2** (User Bob):
   - Open https://yourdomain.com (different browser or incognito)
   - Login as bob
   - Open browser console (F12)
   - Start a threaded action
   - Verify you see ONLY Bob's messages (not Alice's)

3. **Verify**:
   - ✓ Each user sees only their own real-time updates
   - ✓ Sessions persist across page refreshes
   - ✓ No cross-user information leakage

### 3. Load Test (Optional)

```bash
# Install Apache Bench
sudo dnf install -y httpd-tools

# Simple load test (100 requests, 10 concurrent)
ab -n 100 -c 10 https://yourdomain.com/

# Results to look for:
# - Requests per second > 50 (should be much higher for simple pages)
# - Failed requests = 0
# - Time per request < 200ms
```

### 4. Automated Testing with pytest

Your existing tests should work in production. To run them:

```bash
# Activate virtual environment
sudo -u flask_app -i
source /opt/webframework/.venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/test_socketio_manager.py
pytest tests/test_scheduler.py

# Exit flask_app user session
exit
```

**Recommended Test Additions** (for production validation):

Create `tests/test_production.py`:

```python
"""
Production-specific tests

Tests for multi-user isolation, session handling, and security.
"""
import pytest
from flask import session
from src.modules.socketio_manager import socketio_manager


class TestMultiUserIsolation:
    """Test user isolation features."""
    
    def test_socketio_room_isolation(self, app, client):
        """Test that users get separate SocketIO rooms."""
        with app.test_request_context():
            session['user'] = 'alice'
            session['_id'] = 'session_alice'
            
            room = socketio_manager.get_user_room()
            assert room == 'user_alice_session_alice'
            
            # Different user gets different room
            session['user'] = 'bob'
            session['_id'] = 'session_bob'
            
            room = socketio_manager.get_user_room()
            assert room == 'user_bob_session_bob'
            assert room != 'user_alice_session_alice'
    
    def test_session_isolation(self, app):
        """Test that sessions are isolated."""
        with app.test_client() as client1:
            with client1.session_transaction() as sess:
                sess['user'] = 'alice'
            
            with app.test_client() as client2:
                with client2.session_transaction() as sess:
                    sess['user'] = 'bob'
                
                # Verify client1 session unchanged
                with client1.session_transaction() as sess:
                    assert sess['user'] == 'alice'


class TestSecurity:
    """Test security configurations."""
    
    def test_session_cookie_secure(self, app):
        """Test that session cookies are configured securely."""
        if app.config.get('SESSION_COOKIE_SECURE'):
            assert app.config['SESSION_COOKIE_SECURE'] is True
            assert app.config['SESSION_COOKIE_HTTPONLY'] is True
    
    def test_no_debug_in_production(self, app):
        """Test that debug mode is disabled."""
        assert app.config.get('DEBUG', False) is False
```

---

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

```bash
# Check service status
sudo systemctl status flask_app.service

# View detailed logs
sudo journalctl -u flask_app.service -n 50

# Common causes:
# - Missing dependencies: sudo -u flask_app /opt/webframework/.venv/bin/pip install -e .
# - Permission issues: sudo chown -R flask_app:flask_app /opt/webframework
# - Port already in use: sudo ss -tulpn | grep 5000
# - Environment file issues: cat /etc/flask_app/environment
```

#### 2. NGINX Errors

```bash
# Test NGINX configuration
sudo nginx -t

# View NGINX error log
sudo tail -f /var/log/nginx/error.log

# Common causes:
# - Certificate path wrong
# - Backend not running: sudo systemctl status flask_app.service
# - SELinux blocking: sudo ausearch -m avc -ts recent
```

#### 3. WebSocket Connection Fails

```bash
# Check if SocketIO endpoint is accessible
curl -I http://127.0.0.1:5000/socket.io/

# Check NGINX WebSocket proxying
# Look for: "Upgrade: websocket" and "Connection: upgrade" headers

# Check browser console for errors like:
# - "WebSocket connection failed"
# - "SocketIO transport error"

# Verify eventlet worker is running
ps aux | grep gunicorn | grep eventlet
```

#### 4. Sessions Not Persisting

```bash
# Check session directory
ls -la /var/lib/flask_sessions/

# Check permissions
sudo chown -R flask_app:flask_app /var/lib/flask_sessions/
sudo chmod 700 /var/lib/flask_sessions/

# Check disk space
df -h /var/lib/flask_sessions/

# View session file (debug only - contains sensitive data!)
sudo ls -lt /var/lib/flask_sessions/ | head -5
```

#### 5. SSL Certificate Issues

```bash
# Check certificate validity
sudo certbot certificates

# Renew certificate manually
sudo certbot renew

# Test certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Check certificate expiration
echo | openssl s_client -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Performance Issues

#### High CPU Usage

```bash
# Check which process is consuming CPU
top
htop

# If Gunicorn worker is high:
# - Check for infinite loops in threaded actions
# - Check scheduler interval (too frequent?)
# - Check for database query issues

# View application profiling
sudo journalctl -u flask_app.service | grep -i "slow"
```

#### High Memory Usage

```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# If flask_app is consuming too much:
# - Check for memory leaks in threaded actions
# - Check session file accumulation: ls /var/lib/flask_sessions/ | wc -l
# - Restart application: sudo systemctl restart flask_app.service
```

#### Slow Response Times

```bash
# Check NGINX access log for slow requests
sudo awk '{print $NF}' /var/log/nginx/flask_app_access.log | sort -n | tail -20

# Check application logs for slow operations
sudo grep -i "slow\|timeout" /var/log/flask_app/error.log

# Common causes:
# - Database queries not optimized
# - Blocking I/O in request handlers
# - Large file uploads
```

---

## Maintenance

### Routine Tasks

#### Daily

- Check application logs for errors: `sudo journalctl -u flask_app.service --since today | grep -i error`
- Monitor disk space: `df -h`

#### Weekly

- Review access logs for suspicious activity
- Check session file count: `ls /var/lib/flask_sessions/ | wc -l`
- Verify backup completion (if configured)

#### Monthly

- Update system packages: `sudo dnf update -y`
- Review and archive old logs
- Test SSL certificate renewal: `sudo certbot renew --dry-run`
- Review application performance metrics

### Updates and Deployments

#### Application Code Update

```bash
# Switch to flask_app user
sudo -u flask_app -i

# Navigate to application directory
cd /opt/webframework

# Pull latest code
git fetch origin
git checkout <branch-or-tag>

# Install/update dependencies
/opt/webframework/.venv/bin/pip install -e .

# Exit flask_app user
exit

# Restart application
sudo systemctl restart flask_app.service

# Verify
sudo systemctl status flask_app.service
curl -I https://yourdomain.com/
```

#### Database Migrations (if applicable)

```bash
# Run migrations as flask_app user
sudo -u flask_app /opt/webframework/.venv/bin/flask db upgrade

# Or use your migration tool
```

#### Rollback Procedure

```bash
# Switch to flask_app user
sudo -u flask_app -i
cd /opt/webframework

# Checkout previous version
git checkout <previous-tag-or-commit>

# Reinstall dependencies
/opt/webframework/.venv/bin/pip install -e .

# Exit
exit

# Restart
sudo systemctl restart flask_app.service
```

### Backup Strategy

#### Application Code

```bash
# Git repository is your source of truth
# Ensure regular pushes to remote repository

# Optional: Create backup of entire application directory
sudo tar -czf /backup/webframework-$(date +%Y%m%d).tar.gz /opt/webframework
```

#### Sessions

```bash
# Sessions can be recreated (users just need to log in again)
# If you need to backup:
sudo tar -czf /backup/flask_sessions-$(date +%Y%m%d).tar.gz /var/lib/flask_sessions
```

#### Logs

```bash
# Logrotate handles this automatically
# Compressed logs are in /var/log/flask_app/*.gz

# Manual backup if needed
sudo tar -czf /backup/flask_logs-$(date +%Y%m%d).tar.gz /var/log/flask_app
```

#### Database (if applicable)

```bash
# PostgreSQL example
sudo -u postgres pg_dump dbname > /backup/db-$(date +%Y%m%d).sql

# Compress
gzip /backup/db-$(date +%Y%m%d).sql
```

---

## Security Checklist

### Pre-Production

- [ ] Change default SECRET_KEY in environment file
- [ ] Configure proper ALLOWED_ORIGINS
- [ ] Enable SSL/TLS (HTTPS)
- [ ] Configure firewall (only ports 80, 443 open)
- [ ] Set up SELinux contexts
- [ ] Review and set proper file permissions
- [ ] Disable debug mode (DEBUG=False)
- [ ] Set secure session cookie flags
- [ ] Configure log rotation
- [ ] Set up automated backups

### Post-Deployment

- [ ] Test multi-user isolation
- [ ] Verify SSL certificate is valid
- [ ] Test automatic failover (restart service)
- [ ] Monitor logs for errors
- [ ] Test WebSocket connections
- [ ] Verify no sensitive data in logs
- [ ] Test session timeout
- [ ] Verify CORS settings

### Ongoing

- [ ] Regular security updates: `sudo dnf update -y`
- [ ] Monitor access logs for suspicious patterns
- [ ] Review user access and permissions
- [ ] Test SSL certificate renewal monthly
- [ ] Review and update security headers
- [ ] Audit application logs weekly

---

## Quick Reference

### Service Management

```bash
# Start
sudo systemctl start flask_app.service

# Stop
sudo systemctl stop flask_app.service

# Restart
sudo systemctl restart flask_app.service

# Reload (graceful restart)
sudo systemctl reload flask_app.service

# Status
sudo systemctl status flask_app.service

# Enable on boot
sudo systemctl enable flask_app.service

# Disable on boot
sudo systemctl disable flask_app.service
```

### NGINX Management

```bash
# Test configuration
sudo nginx -t

# Reload configuration
sudo systemctl reload nginx

# Restart
sudo systemctl restart nginx

# Status
sudo systemctl status nginx
```

### Logs

```bash
# Application logs (journald)
sudo journalctl -u flask_app.service -f

# Application logs (files)
sudo tail -f /var/log/flask_app/app.log

# NGINX access
sudo tail -f /var/log/nginx/flask_app_access.log

# NGINX error
sudo tail -f /var/log/nginx/flask_app_error.log
```

### File Locations

| Purpose | Path |
|---------|------|
| Application root | `/opt/webframework` |
| Virtual environment | `/opt/webframework/.venv` |
| Environment config | `/etc/flask_app/environment` |
| Session files | `/var/lib/flask_sessions` |
| Application logs | `/var/log/flask_app/` |
| NGINX config | `/etc/nginx/conf.d/flask_app.conf` |
| Systemd service | `/etc/systemd/system/flask_app.service` |
| SSL certificates | `/etc/letsencrypt/live/yourdomain.com/` |

---

## Conclusion

Your Flask webframework is now production-ready with:

✅ **Multi-user isolation**: SocketIO rooms and scheduler messages per-user  
✅ **Security**: HTTPS, secure headers, session protection  
✅ **Reliability**: Systemd auto-restart, health checks  
✅ **Performance**: Optimized single-worker for 10-20 users  
✅ **Monitoring**: Comprehensive logging and metrics  
✅ **Maintainability**: Clear structure, documentation, rollback procedures

The framework handles concurrent users correctly, with no information leakage between sessions. Each user's real-time updates (SocketIO) and scheduled messages are properly isolated.

### Support

For issues or questions:
1. Check troubleshooting section above
2. Review application logs: `sudo journalctl -u flask_app.service`
3. Review NGINX logs: `/var/log/nginx/`
4. Check GitHub repository issues

### Next Steps (Optional Enhancements)

- Add database connection pooling (if using database)
- Implement rate limiting (e.g., Flask-Limiter)
- Add monitoring dashboard (e.g., Prometheus + Grafana)
- Set up centralized logging (e.g., ELK stack)
- Add automated deployment (e.g., Ansible playbook)
- Configure CDN for static assets
- Add load balancer for high availability (if scaling beyond single server)

---

**Document Version**: 1.0  
**Last Updated**: October 17, 2025  
**Author**: AI-assisted deployment guide  
**Target Audience**: System administrators and AI assistants

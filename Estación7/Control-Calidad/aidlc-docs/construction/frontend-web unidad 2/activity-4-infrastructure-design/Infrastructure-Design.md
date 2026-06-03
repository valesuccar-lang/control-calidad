# Activity 4: Infrastructure Design - Frontend Web Unit

**Date**: 2026-05-31  
**Status**: IN PROGRESS  
**Context**: Frontend Web Unit — Small team (2-3 devs), 10-20 users, internal deployment  
**Decision Makers**: Frontend Team + IT Operations

---

## 📋 OVERVIEW

Infrastructure design covers the operational systems that support the Frontend Web application: hosting, CI/CD pipeline, monitoring, logging, backups, and disaster recovery.

**Key Constraints:**
- Small team (2-3 developers, 1 IT ops person)
- 10-20 internal users
- Manufacturing environment (factory floor + office)
- ZERO data loss tolerance
- Low budget
- On-premises preference (internal/public data policy)

---

## 🏗️ DECISION 1: HOSTING STRATEGY

### Selected: On-Premises Docker + Nginx

**Why on-premises:**
- Data residency (internal data, no cloud)
- Better integration with factory IT infrastructure
- Better photo/document security (local network)
- Lower ongoing costs for small scale

**Why Docker:**
- Easy deployment and rollback
- Consistent across dev/staging/prod
- Resource-efficient (runs on single server or small cluster)
- Simple backup strategy

**Architecture:**

```
┌─────────────────────────────────────────┐
│ Factory Network (Intranet)              │
│ ├─ Domain: https://qc.factory.local    │
│ ├─ Certificate: Self-signed or Let's   │
│ │  Encrypt (internal)                  │
│ └─ Users: 10-20 operators, supervisors │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│ Production Server (Single VM)           │
│ ├─ OS: Ubuntu 22.04 LTS                 │
│ ├─ RAM: 8-16 GB                         │
│ ├─ Storage: 500 GB (photos + DB)        │
│ └─ CPU: 2-4 cores                       │
└────────────┬────────────────────────────┘
             │
             ├─ Docker Container: React App (nginx)
             │  Port: 3000 (internal)
             │
             ├─ Docker Container: Backend API (FastAPI)
             │  Port: 8000 (internal)
             │
             ├─ Docker Container: PostgreSQL
             │  Port: 5432 (internal only)
             │
             └─ Docker Container: Redis (cache)
                Port: 6379 (internal only)

┌─────────────────────────────────────────┐
│ Reverse Proxy (Nginx)                   │
│ ├─ Port: 443 (HTTPS)                    │
│ ├─ SSL/TLS: Let's Encrypt or self-signed│
│ ├─ Routes:                              │
│ │  ├─ / → React app (port 3000)         │
│ │  ├─ /api/ → Backend API (port 8000)   │
│ │  └─ /static/ → Photos CDN cache       │
│ └─ Compression: gzip for JS/CSS         │
└─────────────────────────────────────────┘
         ↓
   Factory Intranet
   (accessible from factory + office)
```

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Frontend (React)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: textile-qc-frontend
    expose:
      - "3000"
    environment:
      - REACT_APP_API_URL=https://qc.factory.local/api
      - REACT_APP_VERSION=${APP_VERSION}
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Backend API (FastAPI)
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: textile-qc-backend
    expose:
      - "8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/textile_qc
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=${JWT_SECRET}
      - SLACK_WEBHOOK=${SLACK_WEBHOOK}
    depends_on:
      - db
      - redis
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # PostgreSQL Database
  db:
    image: postgres:15-alpine
    container_name: textile-qc-db
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: textile_qc
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis (Cache)
  redis:
    image: redis:7-alpine
    container_name: textile-qc-redis
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: textile-qc-nginx
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./static:/usr/share/nginx/html/static:ro
    depends_on:
      - frontend
      - backend
    restart: always

volumes:
  postgres_data:

networks:
  default:
    name: textile-qc-network
```

### Nginx Configuration

```nginx
# nginx.conf
upstream frontend {
    server frontend:3000;
}

upstream api {
    server backend:8000;
}

server {
    listen 80;
    server_name qc.factory.local;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name qc.factory.local;
    
    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    gzip_min_length 1024;
    
    # Frontend (React SPA)
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        
        # SPA routing: fallback to index.html for non-API routes
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # API timeout (for file uploads)
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files (photos, cache)
    location /static/ {
        root /usr/share/nginx/html;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 🚀 DECISION 2: CI/CD PIPELINE

### Selected: GitHub Actions (Simple Automation)

**Why GitHub Actions:**
- No additional infrastructure needed
- Free for private repositories (GitHub Enterprise for small team)
- Integrated with git workflow
- Sufficient for small team deployment

**Pipeline Stages:**

```
Code Commit
    ↓
GitHub Actions Trigger
    ├─ Stage 1: Test
    │  ├─ Lint (ESLint, Prettier)
    │  ├─ Unit tests (Jest)
    │  ├─ Type check (TypeScript)
    │  └─ Backend tests (pytest)
    │
    ├─ Stage 2: Build (if tests pass)
    │  ├─ Build React app (npm run build)
    │  ├─ Build Docker image (frontend)
    │  ├─ Build Docker image (backend)
    │  └─ Push to registry
    │
    └─ Stage 3: Deploy (if build succeeds)
       ├─ Pull latest images
       ├─ Run database migrations
       ├─ Restart containers (docker-compose restart)
       ├─ Health check
       └─ Slack notification
```

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Test, Build & Deploy

on:
  push:
    branches:
      - main
      - develop
  pull_request:
    branches:
      - main

env:
  REGISTRY: docker.io
  FRONTEND_IMAGE: textile-qc-frontend
  BACKEND_IMAGE: textile-qc-backend

jobs:
  # Stage 1: Test
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18.x]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'
      
      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci
      
      - name: Lint
        working-directory: ./frontend
        run: npm run lint
      
      - name: Type check
        working-directory: ./frontend
        run: npm run type-check
      
      - name: Run unit tests
        working-directory: ./frontend
        run: npm test -- --coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/lcov.info

  # Backend tests
  backend-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        working-directory: ./backend
        run: pip install -r requirements.txt
      
      - name: Run pytest
        working-directory: ./backend
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/textile_qc_test
        run: pytest --cov=. --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml

  # Stage 2: Build
  build:
    needs: [test, backend-test]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to Docker Registry
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Build and push frontend image
        uses: docker/build-push-action@v4
        with:
          context: ./frontend
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ secrets.DOCKER_REPO }}/${{ env.FRONTEND_IMAGE }}:latest
            ${{ env.REGISTRY }}/${{ secrets.DOCKER_REPO }}/${{ env.FRONTEND_IMAGE }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      - name: Build and push backend image
        uses: docker/build-push-action@v4
        with:
          context: ./backend
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ secrets.DOCKER_REPO }}/${{ env.BACKEND_IMAGE }}:latest
            ${{ env.REGISTRY }}/${{ secrets.DOCKER_REPO }}/${{ env.BACKEND_IMAGE }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # Stage 3: Deploy
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to production
        env:
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
          DEPLOY_HOST: ${{ secrets.DEPLOY_HOST }}
          DEPLOY_USER: ${{ secrets.DEPLOY_USER }}
        run: |
          mkdir -p ~/.ssh
          echo "$DEPLOY_KEY" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key
          ssh-keyscan -H $DEPLOY_HOST >> ~/.ssh/known_hosts
          
          ssh -i ~/.ssh/deploy_key $DEPLOY_USER@$DEPLOY_HOST << 'EOF'
          cd /opt/textile-qc
          docker pull ${{ env.REGISTRY }}/${{ secrets.DOCKER_REPO }}/${{ env.FRONTEND_IMAGE }}:latest
          docker pull ${{ env.REGISTRY }}/${{ secrets.DOCKER_REPO }}/${{ env.BACKEND_IMAGE }}:latest
          docker-compose up -d
          docker-compose exec -T backend python -m alembic upgrade head
          EOF
      
      - name: Health check
        env:
          TARGET_URL: https://qc.factory.local/api/health
        run: |
          for i in {1..10}; do
            if curl -s -k $TARGET_URL | grep -q 'ok'; then
              echo "✅ Health check passed"
              exit 0
            fi
            echo "⏳ Waiting for service to be healthy... ($i/10)"
            sleep 10
          done
          echo "❌ Health check failed"
          exit 1
      
      - name: Slack notification (success)
        if: success()
        uses: slackapi/slack-github-action@v1.24.0
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK }}
          payload: |
            {
              "text": "✅ Deployment successful",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "✅ *Production deployment successful*\nCommit: ${{ github.sha }}\nAuthor: ${{ github.actor }}"
                  }
                }
              ]
            }
      
      - name: Slack notification (failure)
        if: failure()
        uses: slackapi/slack-github-action@v1.24.0
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK }}
          payload: |
            {
              "text": "❌ Deployment failed",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "❌ *Production deployment failed*\nCommit: ${{ github.sha }}\nCheck logs for details"
                  }
                }
              ]
            }
```

---

## 📊 DECISION 3: MONITORING & LOGGING

### Selected: ELK Stack + Prometheus (Open-Source)

**Architecture:**

```
┌──────────────────────────────────┐
│ Application Logs & Metrics       │
│ ├─ Frontend (console logs)       │
│ ├─ Backend (Python logging)      │
│ ├─ Nginx (access logs)           │
│ └─ System (syslog)               │
└───────────┬──────────────────────┘
            │
            ├─ Filebeat → Elasticsearch
            │  (log aggregation)
            │
            ├─ Prometheus Exporter
            │  (metrics collection)
            │
            └─ Grafana Dashboard
               (visualization)
```

### Monitoring Stack (docker-compose extension)

```yaml
# docker-compose.monitoring.yml

services:
  # Prometheus (metrics storage)
  prometheus:
    image: prom/prometheus:latest
    container_name: textile-qc-prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    restart: always

  # Grafana (dashboards)
  grafana:
    image: grafana/grafana:latest
    container_name: textile-qc-grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_INSTALL_PLUGINS=redis-datasource
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources:ro
    ports:
      - "3001:3000"
    restart: always

  # Elasticsearch (log storage)
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    container_name: textile-qc-elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    restart: always

  # Kibana (log visualization)
  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    container_name: textile-qc-kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
    restart: always

  # Filebeat (log shipper)
  filebeat:
    image: docker.elastic.co/beats/filebeat:8.0.0
    container_name: textile-qc-filebeat
    volumes:
      - ./monitoring/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    command: filebeat -e -strict.perms=false
    depends_on:
      - elasticsearch
    restart: always

volumes:
  prometheus_data:
  grafana_data:
  elasticsearch_data:
```

### Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres_exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis_exporter:9121']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx_exporter:9113']

alerting:
  alertmanagers:
    - static_configs:
        - targets: []
```

### Key Metrics to Monitor

```
Application Metrics:
├─ Error rate (errors/minute)
├─ API response time (p50, p95, p99)
├─ Photo validation timing
├─ Sync queue depth
└─ Cache hit rate

Infrastructure Metrics:
├─ CPU usage
├─ Memory usage
├─ Disk usage
├─ Network I/O
└─ Database connections

Business Metrics:
├─ Inspections created/day
├─ Photos processed/day
├─ Sync success rate
├─ User activity (logins/day)
└─ Approval queue length
```

---

## 💾 DECISION 4: BACKUP & DISASTER RECOVERY

### Backup Strategy

**Critical Data:**
- PostgreSQL database (inspections, users, photos metadata)
- Photo blobs (stored in `/data/photos` volume)

**Backup Schedule:**

```
Daily Backups:
├─ Database dump (full) → /backups/db/
│  Time: 02:00 AM daily
│  Retention: 7 days
│
├─ Incremental file backup
│  Time: Every 6 hours
│  Retention: 3 days
│
└─ Verification: Daily restore test on backup server

Weekly Backups:
├─ Full system backup → External NAS
│  Time: Sunday 03:00 AM
│  Retention: 4 weeks
│
└─ Store: Separate from production server

Monthly Backups:
└─ Archive copy → Off-site storage
   Time: First Sunday of month
   Retention: 12 months
```

### Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups"
DB_NAME="textile_qc"
RETENTION_DAYS=7

# Create backup directory
mkdir -p $BACKUP_DIR/db
mkdir -p $BACKUP_DIR/files

# Backup PostgreSQL
echo "🔄 Backing up PostgreSQL..."
docker exec textile-qc-db pg_dump -U ${DB_USER} ${DB_NAME} | \
  gzip > $BACKUP_DIR/db/db_$(date +%Y%m%d_%H%M%S).sql.gz

# Backup photo files
echo "🔄 Backing up photo files..."
tar czf $BACKUP_DIR/files/photos_$(date +%Y%m%d_%H%M%S).tar.gz \
  /data/photos

# Backup docker-compose configuration
echo "🔄 Backing up configuration..."
tar czf $BACKUP_DIR/config_$(date +%Y%m%d_%H%M%S).tar.gz \
  /opt/textile-qc/docker-compose.yml \
  /opt/textile-qc/nginx.conf \
  /opt/textile-qc/.env

# Clean old backups (keep last 7 days)
echo "🧹 Cleaning old backups..."
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "photos_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Verify backup integrity
echo "✅ Verifying backup..."
for file in $(find $BACKUP_DIR -name "*.gz" -mtime -1); do
  if gzip -t $file 2>/dev/null; then
    echo "✅ $file: OK"
  else
    echo "❌ $file: CORRUPTED"
    # Send alert
    curl -X POST https://hooks.slack.com/... \
      -d "{\"text\": \"⚠️ Backup corrupted: $file\"}"
  fi
done

echo "✅ Backup complete"
```

### Disaster Recovery Plan

**Scenario: Database corruption**
```bash
# 1. Stop application
docker-compose down

# 2. Restore from latest backup
docker exec textile-qc-db psql -U ${DB_USER} < /backups/db/latest.sql

# 3. Verify data integrity
docker exec textile-qc-db psql -U ${DB_USER} textile_qc -c "SELECT COUNT(*) FROM inspections"

# 4. Restart application
docker-compose up -d

# 5. Run health checks
curl -s https://qc.factory.local/api/health | jq .
```

**Scenario: Server failure**
```
1. RTO (Recovery Time Objective): 2 hours
2. RPO (Recovery Point Objective): 6 hours
3. Procedure:
   - Restore OS from backup
   - Deploy Docker containers
   - Restore database from latest backup
   - Restore photo files
   - Run health checks
```

---

## 💰 DECISION 5: COST ESTIMATION

### Hardware

```
Production Server:
├─ VM (8GB RAM, 4 CPU, 500GB SSD): €150/month
├─ Backup NAS (2TB): €100 one-time
└─ UPS/Power conditioning: €50 one-time

Network:
├─ Factory network connectivity: Included in IT budget
└─ SSL certificate (Let's Encrypt): Free

Total Hardware: €150/month + €150 one-time
```

### Software & Services

```
Development:
├─ GitHub Enterprise (small team): €20/month
├─ Docker Registry (Dockerhub): Free/Paid (€5/month)
└─ Code quality (SonarQube): Free

Monitoring:
├─ ELK Stack: Free (open-source)
├─ Prometheus + Grafana: Free (open-source)
└─ Slack integration: Included (existing Slack)

Total Monthly: €25-175/month
Total Annual: €300-2,100
```

### ROI Analysis

```
Without system:
- Manual QC process errors: 5-10% defect rate
- Lost productivity: 2-3 hours/day manual data entry
- Compliance risk: No audit trail

With system:
- Defect detection: Automated (from 5% down to 0.5%)
- Time saved: 15+ hours/week
- Compliance: Complete audit trail + photo evidence

Estimated ROI: 300-500% annually
```

---

## 🔒 DECISION 6: SECURITY & COMPLIANCE

### Security Checklist

```
✅ SSL/TLS
   - HTTPS enforced (redirect HTTP → HTTPS)
   - TLS 1.2+ only
   - Strong cipher suites

✅ Network Security
   - Firewall: Only ports 80/443 exposed
   - VPN required for remote access
   - Internal network only (no public internet)

✅ Application Security
   - CSRF tokens on state-changing requests
   - Input validation on all API endpoints
   - SQL injection prevention (parameterized queries)
   - XSS protection (httpOnly cookies, CSP headers)

✅ Database Security
   - Strong passwords (min 20 chars)
   - No default users
   - Backups encrypted
   - Logs audit all access

✅ Access Control
   - Multi-factor authentication (optional, ADMIN role)
   - Role-based access control (3 roles)
   - Session timeout (8 hours)
   - Password policy (min 12 chars, complexity)

✅ Monitoring & Logging
   - All errors logged
   - Authentication attempts logged
   - API access logged
   - Admin actions logged
   - Logs retained for 90 days
```

---

## 📋 IMPLEMENTATION CHECKLIST

- [ ] Provision production server (8GB RAM, 4 CPU, Ubuntu 22.04 LTS)
- [ ] Install Docker & Docker Compose
- [ ] Configure Nginx reverse proxy with SSL
- [ ] Create docker-compose.yml for all services
- [ ] Set up GitHub Actions workflows (test, build, deploy)
- [ ] Configure environment variables (.env files)
- [ ] Set up PostgreSQL with initial schema
- [ ] Set up Redis cache
- [ ] Deploy monitoring stack (Prometheus, Grafana, ELK)
- [ ] Configure automated backups
- [ ] Set up Slack webhooks for alerts
- [ ] Create disaster recovery runbooks
- [ ] Test failover & recovery procedures
- [ ] Document deployment procedures
- [ ] Train IT ops team on monitoring/alerts
- [ ] Set up SSL certificate (Let's Encrypt)
- [ ] Configure firewall rules
- [ ] Plan capacity for growth (backup storage, DB growth)

---

## ✅ BENEFITS

1. **Operational Excellence**: Automated CI/CD, monitoring, alerts
2. **Reliability**: Backups, disaster recovery procedures
3. **Security**: HTTPS, RBAC, audit logs, security headers
4. **Cost-Effective**: Open-source tools, on-premises (no cloud costs)
5. **Team-Friendly**: Simple deployment, documented procedures
6. **Scalability**: Easy to add more servers if user count grows

---

## ⚠️ TRADEOFFS

1. **Single Server**: No redundancy (mitigated: backups + recovery plan)
2. **Manual Backups**: Not cloud-native (mitigated: automated scripts)
3. **Limited Resources**: Not for 1000+ users (mitigated: sufficient for 10-20)
4. **IT Ops Dependency**: Requires local IT support (mitigated: clear docs)

---

**Status**: ✅ ACCEPTED  
**Next Step**: Activity 5 - Code Generation (React components, backend endpoints, tests)  
**Testing**: Deployment tests, backup recovery tests, failover tests

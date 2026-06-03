# Activity 4: Infrastructure Design — Unit 3 (Maestros y Configuración)

**Date**: 2026-06-01  
**Unit**: Maestros y Configuración (Masters & Configuration Domain)  
**Scope**: Service definitions, deployment architecture, monitoring, and operational requirements  
**Audience**: DevOps Engineers, Infrastructure Architects, System Administrators  

---

## 📋 OVERVIEW

This document specifies the infrastructure required to deploy and operate the Masters & Configuration backend service. It covers service definitions, deployment topology, operational requirements, and disaster recovery.

**Key Infrastructure Components**:
- FastAPI Backend Service (REST API)
- PostgreSQL Database (master data store)
- Redis Cache (performance optimization)
- Celery Workers (async CSV imports)
- Nginx Reverse Proxy (load balancing, SSL)
- ELK Stack (logging & monitoring)
- Scheduled Jobs (cache refresh, cleanup)

---

## 🏗️ SERVICE DEFINITIONS

### 1. FastAPI Backend Service (masters-api)

**Purpose**: REST API for master data CRUD operations and CSV imports

**Runtime Environment**:
- **Language**: Python 3.10+
- **Framework**: FastAPI 0.104+
- **ASGI Server**: Uvicorn
- **Dependencies**: SQLAlchemy, Pydantic, python-jose, passlib, celery, redis

**Service Configuration**:

| Property | Value | Notes |
|----------|-------|-------|
| **Port** | 8000 | Internal; behind nginx |
| **Workers** | 4 | 1 per CPU core (typical 4-core server) |
| **Timeout** | 60 seconds | HTTP request timeout |
| **Health Check** | `/health` | Liveness probe |
| **Readiness** | `/ready` | DB connectivity check |
| **Max Connections** | 100 | Per worker |
| **Request Size** | 100 MB | Max CSV file size |
| **Memory** | 500 MB per worker | Total ~2GB for 4 workers |

**Environment Variables**:
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/masters_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=5

# Cache
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# Security
SECRET_KEY=<generated-secret-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
REFRESH_TOKEN_EXPIRE_DAYS=30

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# File Storage
UPLOAD_DIR=/data/uploads/
MAX_FILE_SIZE_MB=100

# Logging
LOG_LEVEL=INFO
STRUCTURED_LOGGING=true
```

**Startup Checks**:
1. Verify database connectivity
2. Verify Redis connectivity
3. Verify file upload directory exists
4. Load initial system masters from seed data

**Graceful Shutdown**:
- Accept no new requests (drain)
- Wait for in-flight requests to complete (timeout: 30s)
- Close database connections
- Flush logs

---

### 2. PostgreSQL Database (masters_db)

**Purpose**: Persistent storage for all master data, audit logs, and operational state

**Version**: PostgreSQL 12+

**Configuration**:

| Setting | Value | Purpose |
|---------|-------|---------|
| **max_connections** | 50 | Support multiple services + admin connections |
| **shared_buffers** | 256MB | Cache frequently accessed data |
| **effective_cache_size** | 1GB | Query planner hint |
| **work_mem** | 16MB | Sort/hash buffer per operation |
| **maintenance_work_mem** | 64MB | Index creation, vacuum |
| **checkpoint_timeout** | 15 min | WAL checkpoint frequency |
| **wal_level** | replica | Enable point-in-time recovery |

**Replication** (if high availability needed):
- Primary: on-premises server
- Standby: separate physical server (optional; for HA)
- WAL archiving to backup location

**Backup Strategy**:
- **Full Backup**: Daily at 02:00 UTC (pg_dump)
- **WAL Archiving**: Continuous to /backup/wal/
- **Retention**: 30 days of backups
- **Recovery Test**: Weekly restore to test server

**Database Schema**:
- `masters_db`: Main database
- Tables: users, defects, machines, fabrics, lotes, inspections, approvals, audit_log
- Indexes: On name, status, created_at, is_system
- Indexes: On audit_log(entity_id, timestamp) for audit queries

**Monitoring Metrics**:
- Connection count (alert if > 40)
- Slow queries (log if > 1s)
- Index bloat (monthly check)
- Table bloat (monthly check)
- Backup status (verify daily)

---

### 3. Redis Cache (cache-store)

**Purpose**: Distributed cache for master lists, sessions, task state

**Version**: Redis 6.0+

**Configuration**:

| Setting | Value | Purpose |
|---------|-------|---------|
| **maxmemory** | 1GB | Prevent out-of-memory |
| **maxmemory_policy** | allkeys-lru | Evict least-recently-used keys |
| **appendonly** | yes | Persistence (AOF) |
| **appendfsync** | everysec | Balance durability/performance |
| **timeout** | 0 | No idle timeout |
| **tcp-backlog** | 511 | Connection queue |

**Data Structures**:
- **Strings**: Master lists (cache:defects:all → JSON array)
- **Hashes**: Cached masters by ID (cache:defect:{id} → {name, status, ...})
- **Sets**: User sessions (sessions:{user_id})
- **Lists**: Job queues (via Celery)

**TTLs**:
- Master lists: 1 hour (3600s)
- Individual masters: 1 hour
- Sessions: 30 days
- Job results: 7 days

**Monitoring**:
- Memory usage (alert if > 80%)
- Hit rate (target > 80%)
- Eviction rate (alert if > 100/min)
- Command latency (target < 1ms)

---

### 4. Celery Worker (background-jobs)

**Purpose**: Process long-running tasks asynchronously (CSV imports, cleanup jobs)

**Configuration**:

| Setting | Value | Purpose |
|---------|-------|---------|
| **Broker** | Redis (localhost:6379/1) | Task queue |
| **Result Backend** | Redis (localhost:6379/2) | Task results |
| **Concurrency** | 4 | Parallel tasks |
| **Task Timeout** | 300 seconds (5 min) | Max time per task |
| **Soft Time Limit** | 250 seconds | Graceful warning |
| **Prefetch** | 4 | Tasks pre-fetched per worker |
| **Log Level** | INFO | Task logging |

**Task Types**:
1. **import_csv_task**: Process CSV file, insert masters
   - Time: 1-3 minutes for 10k rows
   - Retry: 3 times on failure
   - Timeout: 5 minutes

2. **refresh_cache_task**: Rebuild cache for master lists
   - Time: < 5 seconds
   - Frequency: Hourly
   - Timeout: 60 seconds

3. **cleanup_old_uploads_task**: Delete old CSV files
   - Time: < 30 seconds
   - Frequency: Daily at 03:00 UTC
   - Timeout: 120 seconds

**Monitoring**:
- Active task count (alert if > 10)
- Task execution time (target < 60s for import, < 5s for cache)
- Failed tasks (alert on any failure)
- Queue depth (alert if > 100 tasks waiting)

---

### 5. Nginx Reverse Proxy (api-gateway)

**Purpose**: HTTP/HTTPS termination, load balancing, SSL/TLS, request routing

**Configuration**:

```nginx
# /etc/nginx/sites-available/masters-api

upstream masters_backend {
    server 127.0.0.1:8000 weight=1 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

server {
    listen 80;
    server_name masters-api.internal;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name masters-api.internal;
    
    # SSL Certificate
    ssl_certificate /etc/ssl/certs/masters-api.crt;
    ssl_certificate_key /etc/ssl/private/masters-api.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=general:10m rate=100r/s;
    limit_req zone=general burst=200 nodelay;
    
    # CORS Headers
    add_header Access-Control-Allow-Origin "https://masters-ui.internal" always;
    add_header Access-Control-Allow-Methods "GET, POST, PATCH, DELETE, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
    
    location / {
        proxy_pass http://masters_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket support (for import progress)
    location /ws/ {
        proxy_pass http://masters_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://masters_backend;
        access_log off;
    }
    
    # Deny direct access to sensitive files
    location ~ /\.env {
        deny all;
    }
}
```

**SSL Certificate Management**:
- Self-signed or internal CA certificate
- Auto-renewal 30 days before expiry
- Update: 2026-06-30 (renew annually)

**Performance Tuning**:
- **Worker Processes**: Match CPU cores (4)
- **Gzip Compression**: On (for API responses)
- **Client Body Timeout**: 60s
- **Keepalive Timeout**: 65s

---

### 6. ELK Stack (Logging & Monitoring)

**Purpose**: Centralized logging, performance monitoring, alerting

#### 6.1 Elasticsearch

**Purpose**: Full-text indexing and aggregation of logs

**Configuration**:
- **Version**: 7.10+
- **Heap Size**: 1GB (auto-balanced)
- **Index Rotation**: Daily (logs-masters-2026-06-01)
- **Retention**: 30 days
- **Shard Count**: 1 (single node)
- **Replica Count**: 0 (no HA needed)

**Indices**:
- `logs-masters-*`: Application logs (JSON structured)
- `logs-postgresql-*`: Database logs
- `logs-nginx-*`: Nginx access/error logs

---

#### 6.2 Logstash

**Purpose**: Log collection, parsing, transformation

**Configuration**:
```logstash
# /etc/logstash/conf.d/masters.conf

input {
  file {
    path => "/var/log/masters-api/*.log"
    codec => json
    start_position => "beginning"
    tags => ["masters-api"]
  }
  
  file {
    path => "/var/log/postgresql/*.log"
    codec => multiline {
      pattern => "^%{TIMESTAMP_ISO8601}"
      negate => true
      what => previous
    }
    tags => ["postgresql"]
  }
}

filter {
  if "masters-api" in [tags] {
    json {
      source => "message"
    }
    
    # Add trace ID for correlation
    if ![trace_id] {
      mutate {
        add_field => { "trace_id" => "%{[@metadata][trace_id]}" }
      }
    }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "logs-masters-%{+YYYY.MM.dd}"
  }
  
  # Alert on errors
  if [level] == "ERROR" {
    email {
      to => "ops-team@example.com"
      subject => "Masters API Error: %{message}"
    }
  }
}
```

---

#### 6.3 Kibana

**Purpose**: Log visualization, querying, dashboarding

**Dashboards**:
1. **Overview**: Request rate, error rate, response time, uptime
2. **Performance**: Slow queries, cache hit rate, task execution time
3. **Security**: Failed auth attempts, audit trail queries
4. **Errors**: Error rate by endpoint, error distribution
5. **CSV Imports**: Import success/failure, duration, row count

**Saved Searches**:
- Errors in last hour: `level: "ERROR" AND timestamp: [now-1h TO now]`
- Slow requests: `duration_ms: [1000 TO *]`
- Failed imports: `operation: "csv_import" AND status: "FAILED"`

---

#### 6.4 Prometheus & Grafana (Metrics)

**Purpose**: Metrics collection, alerting, performance monitoring

**Prometheus Configuration**:
```yaml
# /etc/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']

rule_files:
  - '/etc/prometheus/alerts.yml'

scrape_configs:
  - job_name: 'masters-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:5432']
    
  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:6379']
```

**Key Metrics**:
- `http_request_duration_seconds`: Request latency
- `http_requests_total`: Request count by endpoint/method
- `db_query_duration_seconds`: Database query time
- `redis_hits_total`, `redis_misses_total`: Cache performance
- `celery_task_duration_seconds`: Task execution time
- `celery_task_failures_total`: Failed tasks

**Alert Rules**:
```yaml
# /etc/prometheus/alerts.yml
groups:
  - name: masters_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        annotations:
          summary: "High error rate on masters-api"
      
      - alert: SlowQueries
        expr: histogram_quantile(0.95, db_query_duration_seconds) > 1
        annotations:
          summary: "95th percentile query time > 1s"
      
      - alert: CacheHitRateLow
        expr: cache_hit_ratio < 0.7
        annotations:
          summary: "Cache hit rate below 70%"
      
      - alert: CeleryQueueDepth
        expr: celery_queue_length > 100
        annotations:
          summary: "Task queue backing up"
```

---

## 📊 DEPLOYMENT ARCHITECTURE

### Single-Server On-Premises Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                      Masters & Configuration                    │
│                   Single Server Deployment                      │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  Internet / Internal Network                                          │
└──────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │   Nginx Reverse Proxy      │
                    │  (SSL/TLS Termination)     │
                    │   Port 443, Port 80        │
                    └──────────────┬──────────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                │                  │                  │
        ┌───────▼────────┐  ┌──────▼──────┐  ┌──────▼──────┐
        │  FastAPI       │  │  Celery     │  │  Scheduled  │
        │  Backend       │  │  Workers    │  │  Jobs       │
        │  (4 workers)   │  │  (4 tasks)  │  │  (APScheduler)
        │  Port 8000     │  │             │  │             │
        └────────┬───────┘  └──────┬──────┘  └──────┬──────┘
                 │                 │                 │
                 └─────────┬────────┴────────┬───────┘
                           │                 │
                  ┌────────▼──────────┐   ┌──▼───────────────┐
                  │ Shared Services   │   │  File Storage   │
                  │                   │   │                 │
                  │ - PostgreSQL      │   │ /data/uploads/  │
                  │ - Redis Cache     │   │ /data/backups/  │
                  │ - Nginx           │   │                 │
                  └───────────────────┘   └─────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  Monitoring & Logging (ELK Stack)                                     │
│  ├── Elasticsearch (logs, metrics)                                    │
│  ├── Logstash (log collection)                                        │
│  ├── Kibana (visualization)                                           │
│  ├── Prometheus (metrics)                                             │
│  └── Grafana (dashboards)                                             │
└──────────────────────────────────────────────────────────────────────┘
```

### Service Dependencies

```mermaid
graph TD
    A[FastAPI Backend] -->|Query| B[PostgreSQL DB]
    A -->|Cache Read/Write| C[Redis]
    A -->|Enqueue Jobs| D[Celery Workers]
    D -->|Store Results| C
    D -->|Write Data| B
    E[Nginx] -->|Proxy| A
    F[Scheduled Jobs] -->|Invalidate Cache| C
    F -->|Cleanup| G[File Storage]
    G -->|Temp Files| A
    B -->|Query Logs| H[ELK Stack]
    A -->|Structured Logs| H
    C -->|Metrics| I[Prometheus]
    B -->|Metrics| I
    I -->|Visualize| J[Grafana]
    H -->|Visualize| K[Kibana]
```

---

## 🔒 SECURITY CONFIGURATION

### Network Security

**Firewall Rules**:
```
Inbound:
  - Port 443 (HTTPS): Allow from internal network
  - Port 22 (SSH): Allow from admin IPs only
  - Port 5432 (PostgreSQL): Deny from internet, allow localhost only
  - Port 6379 (Redis): Deny from internet, allow localhost only

Outbound:
  - Port 443: Allow (for external API calls, if needed)
  - Port 587: Allow (for email alerts)
```

**Database Security**:
- User: `masters_user` (read/write to schema)
- Read-only user: `masters_readonly` (for backups)
- Host: `127.0.0.1` (local connection only)
- Authentication: Password + peer verification

**API Security**:
- JWT token validation on all routes (except /health, /docs)
- RBAC: ADMIN role for mutations
- Rate limiting: 100 req/s per IP
- Request size limit: 100 MB (CSV upload)
- CORS: Allow from masters-ui.internal only

**File Storage Security**:
- Uploaded CSVs stored in `/data/uploads/`
- Ownership: `masters:masters` (non-root user)
- Permissions: `700` (owner read/write/execute only)
- Cleanup: Files deleted after 7 days
- Virus scan: Optional (if handling external files)

---

## 📦 DEPLOYMENT PROCESS

### Docker Containerization

**Dockerfile** (FastAPI service):
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/app ./app

# Create non-root user
RUN useradd -m -u 1000 masters && chown -R masters:masters /app
USER masters

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Docker Compose** (local development):
```yaml
# docker-compose.yml
version: '3.9'

services:
  masters-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://masters_user:password@postgres:5432/masters_db
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/1
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs
      - ./data/uploads:/data/uploads

  postgres:
    image: postgres:13-alpine
    environment:
      POSTGRES_USER: masters_user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: masters_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./migrations:/docker-entrypoint-initdb.d

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  celery-worker:
    build: .
    command: celery -A app.tasks worker --loglevel=info --concurrency=4
    environment:
      DATABASE_URL: postgresql://masters_user:password@postgres:5432/masters_db
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/1
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  redis_data:
```

### Production Deployment Steps

1. **Prepare Server** (one-time):
   ```bash
   # Install OS packages
   sudo apt-get update && sudo apt-get install -y \
     docker.io docker-compose nginx postgresql-client \
     elasticsearch logstash kibana prometheus grafana-server
   
   # Create directories
   sudo mkdir -p /data/uploads /data/backups /var/log/masters-api
   sudo chown masters:masters /data/uploads /data/backups
   
   # Copy SSL certificates
   sudo cp masters-api.crt /etc/ssl/certs/
   sudo cp masters-api.key /etc/ssl/private/
   sudo chmod 600 /etc/ssl/private/masters-api.key
   ```

2. **Deploy Application**:
   ```bash
   # Pull code
   cd /opt/masters-api
   git pull origin main
   
   # Build Docker image
   docker build -t masters-api:latest .
   
   # Run with Docker Compose
   docker-compose up -d
   
   # Run database migrations
   docker-compose exec masters-api \
     alembic upgrade head
   
   # Verify health
   curl -k https://masters-api.internal/health
   ```

3. **Configure Monitoring**:
   - Update Prometheus scrape configs
   - Create Grafana dashboards
   - Set up Kibana log queries
   - Configure alert receivers (email, Slack, etc.)

---

## 🔄 OPERATIONAL PROCEDURES

### Backup & Recovery

**Daily Backup Script**:
```bash
#!/bin/bash
# /usr/local/bin/backup-masters.sh

BACKUP_DIR="/data/backups"
DB_NAME="masters_db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Full database dump
pg_dump -U masters_user -d $DB_NAME | gzip > \
  $BACKUP_DIR/masters_db_$TIMESTAMP.sql.gz

# Archive WAL files
pg_archivewal -d $DB_NAME

# Verify backup
gunzip -c $BACKUP_DIR/masters_db_$TIMESTAMP.sql.gz | head -10

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "masters_db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/masters_db_$TIMESTAMP.sql.gz"
```

**Recovery Procedure**:
1. Stop application: `docker-compose down`
2. Drop database: `dropdb -U masters_user masters_db`
3. Restore from backup: `gunzip -c backup.sql.gz | psql -U masters_user`
4. Restart application: `docker-compose up -d`
5. Verify: `curl https://masters-api.internal/health`

### Scaling Considerations

**If Performance Issues Arise**:

1. **CSV Imports Slow**:
   - Increase Celery workers: `docker-compose scale celery-worker=8`
   - Add database read replicas (if using standard PostgreSQL)
   - Profile slow queries in Prometheus

2. **API Latency High**:
   - Increase FastAPI workers: Modify Dockerfile
   - Increase Redis memory: `redis-cli CONFIG SET maxmemory 2gb`
   - Review slow query logs

3. **Database Connection Exhaustion**:
   - Increase pool size in SQLAlchemy config
   - Add PgBouncer connection pooler
   - Check for long-running connections: `SELECT * FROM pg_stat_activity`

4. **Many Concurrent Users**:
   - Add second FastAPI instance (with load balancing)
   - Consider distributed Redis (Redis Sentinel or Cluster)
   - Add database connection pooling layer (PgBouncer)

**Horizontal Scaling Topology** (if needed):
```
┌────────────────────────────────────┐
│    Load Balancer (HAProxy)         │
└────────────┬───────────────────────┘
             │
    ┌────────┼────────┐
    │        │        │
┌───▼──┐ ┌──▼───┐ ┌──▼───┐
│API 1 │ │API 2 │ │API 3 │
└──────┘ └──────┘ └──────┘
    │        │        │
    └────────┼────────┘
             │
    ┌────────▼─────────┐
    │  Shared Services │
    │  - PostgreSQL    │
    │  - Redis         │
    │  - Celery        │
    └──────────────────┘
```

---

## ✅ CHECKLIST: INFRASTRUCTURE READY

- [ ] Server provisioned (4 CPU, 8GB RAM, 100GB disk)
- [ ] OS installed (Ubuntu 20.04 LTS or similar)
- [ ] Docker & Docker Compose installed
- [ ] PostgreSQL installed and configured
- [ ] Redis installed and configured
- [ ] Nginx installed with SSL certificates
- [ ] ELK Stack deployed (Elasticsearch, Logstash, Kibana)
- [ ] Prometheus & Grafana deployed
- [ ] Application Dockerfile built and tested
- [ ] Docker Compose file validated
- [ ] Environment variables configured (.env file)
- [ ] Database schema initialized (alembic migrate)
- [ ] System masters seeded (defects, machines, fabrics)
- [ ] Backup script configured and tested
- [ ] Monitoring dashboards created
- [ ] Alert rules configured
- [ ] Firewall rules configured
- [ ] Health checks passing
- [ ] Load test completed (happy path scenarios)
- [ ] Documentation updated (runbooks, troubleshooting)

---

## 🎯 OPERATIONAL METRICS & SLOs

### Service Level Objectives (SLOs)

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| **Availability** | 99.5% uptime | < 99% over 1h |
| **Response Time** | < 200ms (p95) | > 500ms (p95) |
| **Error Rate** | < 0.5% | > 1% |
| **Cache Hit Rate** | > 80% | < 70% |
| **CSV Import Time** | < 3 min (10k rows) | > 5 min |
| **Backup Success** | 100% daily | Failed backup |

### Monitoring Dashboard Queries (Prometheus)

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Response time (p95)
histogram_quantile(0.95, http_request_duration_seconds)

# Cache hit rate
cache_hits_total / (cache_hits_total + cache_misses_total)

# Database connection pool usage
db_connections_active / db_connections_max
```

---

**Status**: ✅ **ACTIVITY 4 PHASE 1 COMPLETE**  
**Next Step**: Activity 4 Phase 2 — Deployment Architecture Diagrams  
**Related Documents**: 
- [NFR-Design-Consolidated.md](../activity-3-nfr-design/NFR-Design-Consolidated.md)
- [Business-Logic-Model.md](../activity-2-nfr-requirements/Business-Logic-Model.md)

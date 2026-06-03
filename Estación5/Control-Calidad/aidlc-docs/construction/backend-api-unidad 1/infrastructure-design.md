# Infrastructure Design — Architecture Decision Records (ADRs)
**Date**: 2026-05-28  
**Unit**: Backend API (Python FastAPI)  
**Status**: ✅ ACCEPTED

---

## 📋 ADR INDEX

| # | Componente | Pregunta | Patrón | Estado |
|---|-----------|----------|--------|--------|
| ADR-009 | Database | ¿Cómo diseñar schema PostgreSQL para 110K inspections? | Normalized + Indexes | ✅ ACCEPTED |
| ADR-010 | Deployment | ¿Cómo deployar Backend en on-premise Eliot? | Docker + Systemd | ✅ ACCEPTED |
| ADR-011 | CI/CD | ¿Cómo automatizar build, test, deploy? | GitHub Actions | ✅ ACCEPTED |
| ADR-012 | File Storage | ¿Cómo almacenar 900GB/month de fotos? | Local Filesystem | ✅ ACCEPTED |
| ADR-013 | Monitoring | ¿Dónde corren Prometheus + Grafana? | On-Premise VM | ✅ ACCEPTED |
| ADR-014 | Configuration | ¿Cómo manejar secrets, env vars, settings? | .env + config.yaml | ✅ ACCEPTED |
| ADR-015 | Project Layout | ¿Cómo organizar código, tests, docs? | FastAPI Standard | ✅ ACCEPTED |

---

---

# ADR-009: Database Schema (PostgreSQL)

## 🤔 PREGUNTA

**¿Cómo diseñar schema PostgreSQL para 110K+ inspections con performance <1s y confiabilidad 100%?**

---

## ✅ REQUIREMENT

**Requirement**: DATABASE SCHEMA
- **DBMS**: PostgreSQL (13+)
- **Tables**: 8 (lotes, inspections, approvals, defects, machines, fabrics, users, audit_logs)
- **Indexes**: Strategic on hot paths
- **Constraints**: ACID compliance, referential integrity
- **Partitioning**: By date (future optimization)

---

## 🏗️ PATRÓN TÉCNICO

**Patrón**: **Normalized Relational Schema + Indexes + ACID Constraints**

### Core Tables

```sql
-- 1. USERS (Authentication & RBAC)
CREATE TABLE users (
    id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(200),
    roles TEXT[] NOT NULL,  -- Array: ['ANALISTA', 'JEFE_QA']
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. LOTES (Production Batches)
CREATE TABLE lotes (
    lote_id VARCHAR(50) PRIMARY KEY,  -- HDR-12847
    fabric_id VARCHAR(50) NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, IN_PROCESS, INSPECTED, APPROVED, REJECTED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_lotes_fabric 
        FOREIGN KEY (fabric_id) REFERENCES fabrics(fabric_id)
);

-- 3. INSPECTIONS (Defect Findings)
CREATE TABLE inspections (
    inspection_id UUID PRIMARY KEY,
    lote_id VARCHAR(50) NOT NULL,
    analista_id VARCHAR(50) NOT NULL,
    defect_id VARCHAR(50) NOT NULL,
    comment_text VARCHAR(500) NOT NULL,
    photo_id UUID NOT NULL,
    photo_checksum VARCHAR(64) NOT NULL,  -- SHA256
    photo_path VARCHAR(500) NOT NULL,  -- /storage/photos/2026/05/28/inspection_id.jpg
    machine_id VARCHAR(50) NOT NULL,
    check_in TIMESTAMP NOT NULL,
    check_out TIMESTAMP,
    elapsed_seconds INT,
    sync_status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, SYNCED, SYNC_FAILED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_inspections_lote 
        FOREIGN KEY (lote_id) REFERENCES lotes(lote_id),
    CONSTRAINT fk_inspections_analista 
        FOREIGN KEY (analista_id) REFERENCES users(id),
    CONSTRAINT fk_inspections_defect 
        FOREIGN KEY (defect_id) REFERENCES defects(defect_id),
    CONSTRAINT fk_inspections_machine 
        FOREIGN KEY (machine_id) REFERENCES machines(machine_id),
    
    UNIQUE(inspection_id)  -- Idempotency key for sync
);

-- 4. APPROVALS (QA Decisions)
CREATE TABLE approvals (
    approval_id UUID PRIMARY KEY,
    inspection_id UUID NOT NULL,
    jefe_qa_id VARCHAR(50) NOT NULL,
    decision VARCHAR(20) NOT NULL,  -- APPROVED, REJECTED
    rejection_reason VARCHAR(500),
    rejection_code VARCHAR(50),  -- PHOTO_BLURRY, FALSE_ALARM, etc.
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, APPROVED, REJECTED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_approvals_inspection 
        FOREIGN KEY (inspection_id) REFERENCES inspections(inspection_id),
    CONSTRAINT fk_approvals_jefe_qa 
        FOREIGN KEY (jefe_qa_id) REFERENCES users(id),
    
    UNIQUE(inspection_id)  -- One approval per inspection
);

-- 5. DEFECTS (Masters - Read-Only)
CREATE TABLE defects (
    defect_id VARCHAR(50) PRIMARY KEY,  -- DEF-TON
    defect_name VARCHAR(200) NOT NULL,
    description TEXT,
    typical_process VARCHAR(100),
    typical_machine_id VARCHAR(50),
    status VARCHAR(20) DEFAULT 'ACTIVE',  -- ACTIVE, INACTIVE (soft delete)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_defects_machine 
        FOREIGN KEY (typical_machine_id) REFERENCES machines(machine_id)
);

-- 6. MACHINES (Masters - Read-Only)
CREATE TABLE machines (
    machine_id VARCHAR(50) PRIMARY KEY,  -- MAQ-AGO-80
    machine_name VARCHAR(200) NOT NULL,
    process VARCHAR(100),
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. FABRICS (Masters - Read-Only)
CREATE TABLE fabrics (
    fabric_id VARCHAR(50) PRIMARY KEY,  -- TEJ-001
    fabric_name VARCHAR(200) NOT NULL,
    composition VARCHAR(200),
    width FLOAT,
    weight FLOAT,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. AUDIT_LOG (Compliance & Traceability)
CREATE TABLE audit_logs (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,  -- CREATE, UPDATE, DELETE
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100),
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(50)
);

-- ===== INDEXES (Performance Optimization) =====

-- Hot path: Find inspections by lote
CREATE INDEX idx_inspections_lote_id 
    ON inspections(lote_id);

-- Hot path: Find recent inspections by analyst
CREATE INDEX idx_inspections_analista_created 
    ON inspections(analista_id, created_at DESC);

-- Hot path: Find pending approvals
CREATE INDEX idx_approvals_status 
    ON approvals(status) 
    WHERE status = 'PENDING';

-- Hot path: Find pending syncs
CREATE INDEX idx_inspections_sync_status 
    ON inspections(sync_status) 
    WHERE sync_status IN ('PENDING', 'SYNC_FAILED');

-- Foreign keys (auto-indexed in PostgreSQL)
CREATE INDEX idx_approvals_inspection_id 
    ON approvals(inspection_id);

-- Masters read-only queries
CREATE INDEX idx_defects_status 
    ON defects(status) WHERE status = 'ACTIVE';

CREATE INDEX idx_machines_status 
    ON machines(status) WHERE status = 'ACTIVE';

-- Audit log for compliance
CREATE INDEX idx_audit_logs_timestamp 
    ON audit_logs(timestamp DESC);

CREATE INDEX idx_audit_logs_user 
    ON audit_logs(user_id, timestamp DESC);
```

---

## 📋 ADR-009

### CONTEXTO

**Requisitos**:
- 110K+ inspections en 5 años
- 1,800 inspections/mes = ~60/día
- Queries <1s (p99)
- ACID compliance (zero data loss)
- Referential integrity (no orphaned records)

**Constraints**:
- On-premise PostgreSQL (local)
- Limited disk space (need archival strategy for future)

---

### DECISIÓN

**Implementar: Normalized Schema + Strategic Indexes + ACID Constraints**

**Tabla Mapping → Domain Model**:
- `users` ← User aggregate
- `lotes` ← Lote aggregate
- `inspections` ← Inspection aggregate
- `approvals` ← Approval aggregate
- `defects, machines, fabrics` ← Masters aggregates
- `audit_logs` ← Compliance

**Indexes Strategy**:
- (lote_id) → Fast inspection queries by batch
- (analista_id, created_at DESC) → Fast analyst history
- (status) WHERE PENDING → Fast pending queries
- (sync_status) WHERE PENDING/FAILED → Fast offline queries

**Idempotency**:
- `inspection_id` is UNIQUE → safe retries
- `approvals(inspection_id)` is UNIQUE → one approval per inspection

---

### ALTERNATIVAS

| Alternativa | Pros | Cons | Decisión |
|-------------|------|------|----------|
| **Document DB (MongoDB)** | Flexible schema | ❌ No ACID, complex queries | REJECTED |
| **Time-Series DB (InfluxDB)** | Optimized for events | ❌ Not relational | REJECTED |
| **Partitioned by Date** | Faster old queries | ❌ Premature (optimize later) | FUTURE |

---

### CONSECUENCIAS

**Positivas** ✅
- ACID compliance (zero data loss)
- Referential integrity (no orphaned data)
- Query performance <1s (with indexes)
- Easy to backup, restore
- Standard SQL (familiar)

**Negativas** ❌
- Schema migrations needed (Alembic)
- Manual index tuning
- Disk space grows (~500MB/year for photos)

---

### ESTADO

**Status**: **✅ ACCEPTED**

---

---

# ADR-010: Deployment Architecture

## 🤔 PREGUNTA

**¿Cómo deployar Backend API en on-premise Eliot sin .NET/cloud dependency?**

---

## ✅ REQUIREMENT

**Requirement**: DEPLOYMENT ARCHITECTURE
- **Target**: On-premise Linux server (Eliot facility)
- **Containerization**: Docker (reproducible)
- **Process Manager**: Systemd (auto-restart)
- **Port**: 8000 (FastAPI), exposed via Nginx reverse proxy
- **Database**: PostgreSQL (local connection)

---

## 🏗️ PATRÓN TÉCNICO

**Patrón**: **Docker Container + Systemd Service**

### Dockerfile

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy app
COPY app/ ./app
COPY main.py .
COPY config.yaml .

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml (Local Dev)

```yaml
version: '3.9'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:password@postgres:5432/eliot_qc
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      ENVIRONMENT: development
    depends_on:
      - postgres
    volumes:
      - ./app:/app/app  # Hot reload in dev
      - ./storage/photos:/app/storage/photos

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: eliot_qc
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Systemd Service (Production)

```ini
# /etc/systemd/system/fastapi-qc.service

[Unit]
Description=Eliot QC Backend API (FastAPI)
After=network.target postgres.service
Wants=postgres.service

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/eliot-qc

# Environment variables
EnvironmentFile=/opt/eliot-qc/.env

# Start command
ExecStart=/usr/bin/python3 -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4

# Auto-restart
Restart=always
RestartSec=5
StartLimitInterval=600
StartLimitBurst=3

# Logging
StandardOutput=journal
StandardError=journal

# Resource limits
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/eliot-qc

upstream fastapi_backend {
    server localhost:8000;
}

server {
    listen 443 ssl http2;
    server_name api.eliot.local;

    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    # Redirect HTTP to HTTPS
    if ($scheme != "https") {
        return 301 https://$server_name$request_uri;
    }

    location / {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /health {
        proxy_pass http://fastapi_backend;
        access_log off;  # Don't log health checks
    }
}
```

---

## 📋 ADR-010

### CONTEXTO

**Objetivo**:
- Reproducible deployment (Docker)
- Auto-recovery (systemd restart)
- Secure (HTTPS via Nginx)
- Simple operations (no Kubernetes complexity)

---

### DECISIÓN

**Implementar: Docker Container + Systemd Service + Nginx Reverse Proxy**

**Deployment Flow**:
```
1. Build Docker image (on dev machine)
2. Push to local registry or copy to server
3. Run systemd service (manages container lifecycle)
4. Nginx routes traffic (reverse proxy + SSL/TLS)
5. Auto-restart on failure (systemd handles)
```

---

### ALTERNATIVAS

| Alternativa | Decisión |
|-------------|----------|
| Kubernetes | REJECTED (too complex for single server) |
| AWS EC2 | REJECTED (violates on-premise) |
| Manual setup (no Docker) | REJECTED (not reproducible) |

---

### ESTADO

**Status**: **✅ ACCEPTED**

---

---

# ADR-011: CI/CD Pipeline

## 🤔 PREGUNTA

**¿Cómo automatizar build, test, deploy sin cloud CI/CD services?**

---

## ✅ REQUIREMENT

**Requirement**: CI/CD PIPELINE
- **Version Control**: Git (GitHub)
- **Automation**: GitHub Actions (free tier)
- **Stages**: Build → Test → Security Scan → Deploy
- **Trigger**: On push to main branch

---

## 🏗️ PATRÓN TÉCNICO

**Patrón**: **GitHub Actions Workflow**

```yaml
# .github/workflows/build-test-deploy.yml

name: Build, Test & Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov black flake8
      
      - name: Lint (black)
        run: black --check app/
      
      - name: Lint (flake8)
        run: flake8 app/ --max-line-length=100
      
      - name: Run tests
        run: |
          pytest tests/ --cov=app --cov-report=xml --cov-report=html
      
      - name: Check coverage
        run: |
          coverage report --fail-under=60
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
      
      - name: Build Docker image
        run: |
          docker build -t ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} .
          docker build -t ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest .
      
      - name: Login to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Push Docker image
        run: |
          docker push ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          docker push ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    
    steps:
      - name: Deploy to production
        run: |
          # SSH to server and pull latest image
          ssh -i ${{ secrets.DEPLOY_KEY }} appuser@eliot.local \
            'cd /opt/eliot-qc && docker pull ghcr.io/${{ github.repository }}:latest && \
             systemctl restart fastapi-qc'
      
      - name: Verify deployment
        run: |
          sleep 5
          curl -f https://api.eliot.local/health || exit 1
      
      - name: Notify Slack (optional)
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Deploy ${{ job.status }}'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## 📋 ADR-011

### CONTEXTO

**Objetivo**:
- Automate testing (catch bugs early)
- Automate building (reproducible binaries)
- Automate deployment (reduce manual errors)

---

### DECISIÓN

**Implementar: GitHub Actions (free tier) + Docker Registry**

---

### ESTADO

**Status**: **✅ ACCEPTED**

---

---

# ADR-012: File Storage Strategy

## 🤔 PREGUNTA

**¿Cómo almacenar 900GB/month de fotos de defectos?**

---

## ✅ REQUIREMENT

**Requirement**: FILE STORAGE
- **Volume**: 900GB/month (500KB × 1,800 inspections/month)
- **Location**: On-premise (Eliot data center)
- **Retention**: Keep all (archive after 1 year, future)
- **Access**: Fast retrieval (<5s)

---

## 🏗️ PATRÓN TÉCNICO

**Patrón**: **Local Filesystem + Directory Sharding**

```
Directory structure:
/storage/photos/
  ├── 2026/
  │   ├── 01/
  │   │   ├── 01/
  │   │   │   ├── 550e8400-e29b-41d4-a716-446655440000.jpg
  │   │   │   ├── 550e8400-e29b-41d4-a716-446655440001.jpg
  │   │   │   └── ...
  │   │   ├── 02/
  │   │   └── ...
  │   ├── 02/
  │   └── ...
  └── ...

Advantages:
- No cloud dependency (on-premise)
- Fast access (local filesystem)
- Easy backup (incremental daily)
- Sharding prevents too many files per dir

Naming:
  /storage/photos/{YYYY}/{MM}/{DD}/{inspection_id}.jpg

Example:
  /storage/photos/2026/05/28/550e8400-e29b-41d4-a716-446655440000.jpg
```

### Python Implementation

```python
from pathlib import Path
from datetime import datetime

class PhotoStorage:
    def __init__(self, base_path="/storage/photos"):
        self.base_path = Path(base_path)
    
    def get_photo_path(self, inspection_id: str) -> Path:
        """Get full path for inspection photo"""
        today = datetime.utcnow().date()
        
        directory = self.base_path / str(today.year) / f"{today.month:02d}" / f"{today.day:02d}"
        directory.mkdir(parents=True, exist_ok=True)
        
        return directory / f"{inspection_id}.jpg"
    
    def save_photo(self, inspection_id: str, photo_bytes: bytes) -> str:
        """Save photo and return path"""
        path = self.get_photo_path(inspection_id)
        
        # Verify size < 500KB
        if len(photo_bytes) > 500 * 1024:
            raise ValueError("Photo exceeds 500KB")
        
        # Write to disk
        path.write_bytes(photo_bytes)
        
        return str(path)
    
    def get_photo(self, photo_path: str) -> bytes:
        """Retrieve photo from disk"""
        path = Path(photo_path)
        if not path.exists():
            raise FileNotFoundError(f"Photo not found: {photo_path}")
        
        return path.read_bytes()
```

---

## 📋 ADR-012

### CONTEXTO

**Objetivo**:
- Store photos efficiently
- Keep on-premise (no cloud)
- Fast retrieval

---

### DECISIÓN

**Implementar: Local Filesystem + Directory Sharding by Date**

---

### ALTERNATIVAS

| Alternativa | Decisión |
|-------------|----------|
| S3 / Cloud Storage | REJECTED (on-premise only) |
| Database BLOB | REJECTED (slows down queries) |
| NAS / Network Drive | ACCEPTED (future v1.1) |

---

### ESTADO

**Status**: **✅ ACCEPTED**

---

---

# ADR-013: Monitoring Infrastructure

## 🤔 PREGUNTA

**¿Dónde y cómo ejecutar Prometheus + Grafana en on-premise?**

---

## ✅ REQUIREMENT

**Requirement**: MONITORING INFRASTRUCTURE
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **Alerting**: Alert Manager (email, Slack)
- **Location**: On-premise VM

---

## 🏗️ PATRÓN TÉCNICO

**Patrón**: **Prometheus + Grafana Stack (Docker Compose)**

```yaml
# docker-compose.monitoring.yml

version: '3.9'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=90d'  # 90 days retention

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      - prometheus

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager_data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'

volumes:
  prometheus_data:
  grafana_data:
  alertmanager_data:
```

### prometheus.yml

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']

rule_files:
  - '/etc/prometheus/alert_rules.yml'
```

### alertmanager.yml

```yaml
global:
  resolve_timeout: 5m
  slack_api_url: ${SLACK_WEBHOOK_URL}

route:
  receiver: 'slack-notifications'
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - channel: '#alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

---

## 📋 ADR-013

### ESTADO

**Status**: **✅ ACCEPTED**

---

---

# ADR-014: Configuration Management

## 🤔 PREGUNTA

**¿Cómo manejar secrets, env vars, y settings de forma segura?**

---

## ✅ REQUIREMENT

**Requirement**: CONFIGURATION MANAGEMENT
- **Secrets**: JWT_SECRET_KEY, DB_PASSWORD (never in git)
- **Environment**: development vs production settings
- **Configuration**: Feature flags, audit levels (parametrizable)

---

## 🏗️ PATRÓN TÉCNICO

**Patrón**: **.env File + config.yaml**

```
.env (git-ignored):
JWT_SECRET_KEY=super-secret-key-here
DATABASE_URL=postgresql://user:password@localhost/eliot_qc
ENVIRONMENT=production
GRAFANA_PASSWORD=grafana-secret
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

config.yaml (git-tracked):
audit:
  enabled: true
  log_level: "ALL"  # or "CRITICAL"
  sample_rate: 1.0

photo_storage:
  base_path: /storage/photos
  max_size_kb: 500

retry:
  backoff_seconds: [5, 10, 30, 60]
  max_attempts: 5
```

```python
# config.py
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET_KEY: str
    DATABASE_URL: str
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 📋 ADR-014

### ESTADO

**Status**: **✅ ACCEPTED**

---

---

# ADR-015: Project Layout

## 🤔 PREGUNTA

**¿Cómo organizar directorios de código, tests, docs?**

---

## ✅ REQUIREMENT

**Requirement**: PROJECT STRUCTURE
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Testing**: Pytest
- **Docs**: Auto-generated (Swagger)

---

## 🏗️ PATRÓN TÉCNICO

**Patrón**: **FastAPI Standard Project Layout**

```
eliot-qc-backend/
├── app/                          # Application code
│   ├── main.py                   # FastAPI app entry
│   ├── config.py                 # Settings & environment
│   ├── database.py               # SQLAlchemy setup
│   │
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── lote.py
│   │   ├── inspection.py
│   │   ├── approval.py
│   │   ├── defect.py
│   │   ├── machine.py
│   │   ├── fabric.py
│   │   └── audit_log.py
│   │
│   ├── domain/                   # DDD Domain Layer
│   │   ├── __init__.py
│   │   ├── inspection/
│   │   │   ├── __init__.py
│   │   │   ├── aggregate.py      # Inspection aggregate root
│   │   │   ├── value_objects.py  # DefectType, Comment, Photo, etc.
│   │   │   ├── services.py       # InspectionService (business logic)
│   │   │   └── events.py         # Domain events
│   │   ├── approval/
│   │   │   ├── aggregate.py
│   │   │   ├── value_objects.py
│   │   │   ├── services.py
│   │   │   └── events.py
│   │   └── masters/
│   │       ├── aggregate.py
│   │       ├── services.py
│   │       └── events.py
│   │
│   ├── application/              # Application Layer (Use Cases)
│   │   ├── __init__.py
│   │   ├── dtos.py               # Request/response DTOs
│   │   ├── inspection_use_cases.py
│   │   ├── approval_use_cases.py
│   │   └── masters_use_cases.py
│   │
│   ├── repositories/             # Repositories (Persistence)
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── inspection_repository.py
│   │   ├── approval_repository.py
│   │   ├── defect_repository.py
│   │   ├── machine_repository.py
│   │   └── fabric_repository.py
│   │
│   ├── routes/                   # API Routes (Presentation)
│   │   ├── __init__.py
│   │   ├── auth.py               # POST /api/auth/login
│   │   ├── inspections.py        # /api/inspections/*
│   │   ├── approvals.py          # /api/approvals/*
│   │   ├── masters.py            # /api/masters/*
│   │   └── health.py             # GET /health
│   │
│   ├── dependencies.py           # FastAPI dependencies (auth, db session)
│   ├── exceptions.py             # Custom exceptions
│   ├── middlewares.py            # HTTP middlewares (logging, rate limiting)
│   └── utils/
│       ├── __init__.py
│       ├── security.py           # JWT, password hashing
│       ├── validators.py         # Input validation
│       ├── photo_storage.py      # File operations
│       └── monitoring.py         # Prometheus metrics
│
├── tests/                        # Test Suite
│   ├── __init__.py
│   ├── conftest.py               # Pytest fixtures
│   ├── unit/                     # Unit tests
│   │   ├── domain/
│   │   │   ├── test_inspection_service.py
│   │   │   ├── test_approval_service.py
│   │   │   └── test_value_objects.py
│   │   └── repositories/
│   │       └── test_inspection_repository.py
│   ├── integration/              # Integration tests
│   │   ├── test_api_inspections.py
│   │   ├── test_api_approvals.py
│   │   └── test_api_auth.py
│   └── fixtures/
│       └── factories.py           # Factory Boy for test data
│
├── migrations/                   # Alembic (DB schema migrations)
│   ├── env.py
│   ├── alembic.ini
│   └── versions/
│       ├── 001_initial_schema.py
│       └── ...
│
├── aidlc-docs/                   # AI-DLC Workflow Documentation
│   ├── construction/
│   │   ├── domain-entities.md
│   │   ├── business-rules.md
│   │   ├── business-logic-model.md
│   │   ├── nfr-requirements-elicited.md
│   │   ├── nfr-design.md
│   │   └── infrastructure-design.md ← THIS FILE
│   └── ...
│
├── .github/
│   └── workflows/
│       └── build-test-deploy.yml  # GitHub Actions CI/CD
│
├── .env.example                  # Example env file (no secrets)
├── requirements.txt              # Python dependencies
├── pytest.ini                    # Pytest configuration
├── pyproject.toml                # Project metadata
├── Dockerfile                    # Docker container
├── docker-compose.yml            # Local dev setup
├── docker-compose.monitoring.yml # Prometheus + Grafana
├── systemd-service.ini           # Systemd service definition
├── nginx.conf                    # Nginx reverse proxy
├── README.md                     # Project documentation
└── .gitignore                    # Ignore .env, __pycache__, etc.
```

---

## 📋 ADR-015

### DECISIÓN

**Implementar: FastAPI Standard Layout with DDD Organization**

**Key Principle**: 
- Domain Layer (domain/) = Pure business logic (testable, framework-agnostic)
- Application Layer (application/) = Use cases & DTOs
- Infrastructure Layer (repositories/) = Persistence
- Presentation Layer (routes/) = HTTP endpoints

---

### ESTADO

**Status**: **✅ ACCEPTED**

---

---

## ✅ SUMMARY: All Infrastructure ADRs ACCEPTED

| ADR | Componente | Patrón | Estado |
|-----|-----------|--------|--------|
| ADR-009 | Database | Normalized PostgreSQL + Indexes | ✅ ACCEPTED |
| ADR-010 | Deployment | Docker + Systemd + Nginx | ✅ ACCEPTED |
| ADR-011 | CI/CD | GitHub Actions | ✅ ACCEPTED |
| ADR-012 | File Storage | Local Filesystem + Sharding | ✅ ACCEPTED |
| ADR-013 | Monitoring | Prometheus + Grafana + AlertManager | ✅ ACCEPTED |
| ADR-014 | Configuration | .env + config.yaml | ✅ ACCEPTED |
| ADR-015 | Project Layout | FastAPI Standard + DDD | ✅ ACCEPTED |

---

## 🚀 PRÓXIMOS PASOS

1. ✅ **Functional Design** — COMPLETED
2. ✅ **NFR Requirements** — COMPLETED
3. ✅ **NFR Design** — COMPLETED
4. ✅ **Infrastructure Design** — COMPLETED
5. ➡️ **Code Generation** — FastAPI routes, SQLAlchemy models, tests
6. ➡️ **Build & Test** — Execute build, run tests, verify quality
7. ➡️ **Deploy to Production** — Package, deploy, monitor

---

**Status**: ✅ **ACTIVITY 4 (Infrastructure Design) COMPLETE**

**Ready for**: Code Generation Phase

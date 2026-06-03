# Deployment Architecture — Textile Quality Control System
**Date**: 2026-05-28  
**Unit**: Backend API (Python FastAPI)  
**Environment**: On-Premise Eliot Server  
**Status**: ✅ ACCEPTED

---

## 📋 OVERVIEW

This document provides visual deployment architecture diagrams for the Backend API Unit, complementing the ADR-based infrastructure design. All decisions and rationales are documented in `infrastructure-design.md` (ADR-009 through ADR-015).

---

## 1️⃣ OVERALL SYSTEM ARCHITECTURE

```mermaid
graph TB
    subgraph "FRONTEND LAYER (React PWA)"
        Browser["🌐 Web Browser<br/>React SPA + PWA"]
        ServiceWorker["⚙️ Service Worker<br/>Offline Sync"]
        IndexedDB["💾 IndexedDB<br/>Local Cache"]
    end

    subgraph "NETWORK"
        HTTPS["🔒 HTTPS/TLS<br/>Port 443"]
    end

    subgraph "ON-PREMISE ELIOT SERVER"
        subgraph "REVERSE PROXY"
            Nginx["📡 Nginx<br/>Reverse Proxy<br/>Port 443→8000"]
        end
        
        subgraph "FASTAPI BACKEND"
            FastAPI["🚀 FastAPI<br/>Python 3.11<br/>4 Uvicorn Workers<br/>Port 8000"]
            JWT["🔐 JWT Auth<br/>+ RBAC"]
            Routes["📝 Routes<br/>/inspections<br/>/approvals<br/>/masters<br/>/health"]
        end

        subgraph "DATABASE LAYER"
            PostgreSQL["🗄️ PostgreSQL 13+<br/>Relational DB<br/>110K+ Inspections"]
            ConnPool["🔗 Connection Pool<br/>pool_size=10<br/>max_overflow=20"]
        end

        subgraph "FILE STORAGE"
            PhotoStorage["📸 Local Filesystem<br/>/storage/photos<br/>Sharded by Date<br/>900GB/month"]
        end

        subgraph "MONITORING STACK"
            Prometheus["📊 Prometheus<br/>Metrics Collection<br/>90-day Retention"]
            Grafana["📈 Grafana<br/>Dashboards<br/>Visualization"]
            AlertManager["🔔 AlertManager<br/>Slack Integration"]
            JSONLogs["📋 JSON Logs<br/>loguru<br/>Structured Logs"]
        end
    end

    Browser -->|HTTP/REST| HTTPS
    ServiceWorker -->|Sync Requests| HTTPS
    HTTPS --> Nginx
    Nginx --> FastAPI
    FastAPI --> JWT
    FastAPI --> Routes
    Routes -->|SQLAlchemy ORM| ConnPool
    ConnPool --> PostgreSQL
    Routes -->|Read/Write| PhotoStorage
    FastAPI -->|Emit Metrics| Prometheus
    FastAPI -->|Write Logs| JSONLogs
    Prometheus --> Grafana
    Prometheus --> AlertManager
    AlertManager -->|Alerts| Slack["📱 Slack<br/>Notifications"]

    style Browser fill:#e1f5ff
    style FastAPI fill:#c8e6c9
    style PostgreSQL fill:#fff9c4
    style PhotoStorage fill:#f8bbd0
    style Prometheus fill:#ffe0b2
    style Grafana fill:#d1c4e9
```

**Key Characteristics**:
- **Frontend**: React PWA with offline capability (Service Worker + IndexedDB)
- **Transport**: HTTPS/TLS for all communication (encrypted in transit)
- **Reverse Proxy**: Nginx routes requests to FastAPI backend
- **Backend**: 4 Uvicorn worker processes handling concurrent requests
- **Database**: PostgreSQL with connection pooling (ADR-009, ADR-004)
- **File Storage**: Local filesystem with date-based sharding (ADR-012)
- **Monitoring**: Prometheus + Grafana + AlertManager (ADR-013)

---

## 2️⃣ DEPLOYMENT ARCHITECTURE (ELIOT SERVER)

```mermaid
graph TD
    subgraph "SYSTEMD SERVICE MANAGEMENT"
        Service["📋 systemd Service<br/>fastapi-qc.service<br/>Restart=always<br/>RestartSec=5"]
        HealthCheck["🏥 Health Check<br/>GET /health<br/>5s interval"]
    end

    subgraph "FASTAPI APPLICATION"
        AppDir["📁 App Directory<br/>/opt/fastapi-qc"]
        Venv["🐍 Python venv<br/>Python 3.11<br/>Dependencies: pip install"]
        MainApp["🚀 main.py<br/>FastAPI Instance<br/>async routes"]
    end

    subgraph "DOCKER CONTAINER (Optional Packaging)"
        DockerImg["🐳 Docker Image<br/>Multi-stage Build<br/>Builder + Runtime"]
        Container["📦 Container<br/>Python 3.11<br/>Minimal Base<br/>~150MB"]
    end

    subgraph "SYSTEMD EXECUTION"
        ExecStart["▶️ ExecStart<br/>uvicorn app.main:app<br/>--host 0.0.0.0<br/>--port 8000<br/>--workers 4"]
        EnvVars["🔑 Environment<br/>.env file<br/>DATABASE_URL<br/>JWT_SECRET_KEY<br/>LOG_LEVEL"]
    end

    subgraph "PERSISTENT STORAGE"
        DBConn["🗄️ PostgreSQL<br/>localhost:5432<br/>fastapi_qc database"]
        PhotoDir["📸 /storage/photos<br/>YYYY/MM/DD/<br/>inspection_id.jpg"]
        LogDir["📋 /var/log/fastapi<br/>JSON logs<br/>loguru output"]
    end

    Service --> HealthCheck
    Service --> ExecStart
    ExecStart --> MainApp
    AppDir --> Venv
    Venv --> MainApp
    EnvVars --> MainApp
    MainApp -->|SQLAlchemy| DBConn
    MainApp -->|Write Photos| PhotoDir
    MainApp -->|Write Logs| LogDir
    DockerImg --> Container
    Container -->|Optional| ExecStart

    style Service fill:#c8e6c9
    style MainApp fill:#bbdefb
    style DBConn fill:#fff9c4
    style PhotoDir fill:#f8bbd0
    style HealthCheck fill:#ffccbc
```

**Key Components**:
- **systemd Service**: Manages FastAPI application lifecycle (ADR-010)
- **Python venv**: Isolated Python environment with locked dependencies
- **Uvicorn Workers**: 4 parallel worker processes for request handling
- **Health Check**: Endpoint for systemd and external monitoring to verify application health
- **Environment Variables**: Sensitive config in .env (JWT_SECRET_KEY, DATABASE_URL) — git-ignored (ADR-014)
- **Persistent Storage**: Database, photos, and logs persist on disk

**Deployment Steps** (ADR-010):
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run database migrations
alembic upgrade head

# 3. Enable and start service
sudo systemctl enable fastapi-qc
sudo systemctl start fastapi-qc

# 4. Update code and restart
git pull origin main
sudo systemctl restart fastapi-qc
```

---

## 3️⃣ CI/CD PIPELINE (GITHUB ACTIONS)

```mermaid
graph LR
    subgraph "SOURCE CONTROL"
        Git["📦 GitHub Repo<br/>main branch push"]
    end

    subgraph "BUILD STAGE"
        Checkout["✅ Checkout Code"]
        SetupPy["🐍 Setup Python 3.11"]
        Install["📚 Install Dependencies<br/>pip install -r requirements.txt"]
    end

    subgraph "VALIDATION STAGE"
        Lint["🔍 Lint Code<br/>black<br/>flake8<br/>isort"]
        Test["✅ Run Tests<br/>pytest<br/>coverage >60%"]
        TypeCheck["📋 Type Check<br/>mypy"]
    end

    subgraph "PACKAGE STAGE"
        Docker["🐳 Build Docker Image<br/>Dockerfile multi-stage"]
        Tag["🏷️ Tag Image<br/>latest + commit_sha"]
        Push["📤 Push to Registry<br/>Docker Hub/<br/>Quay.io"]
    end

    subgraph "DEPLOY STAGE"
        SSH["🔐 SSH to Eliot<br/>Authentication key"]
        Deploy["🚀 Deploy Script<br/>systemctl restart<br/>fastapi-qc"]
        Verify["🏥 Verify Health<br/>GET /health<br/>Check 200 OK"]
    end

    Git -->|Push trigger| Checkout
    Checkout --> SetupPy
    SetupPy --> Install
    Install --> Lint
    Lint --> Test
    Test --> TypeCheck
    TypeCheck -->|All pass| Docker
    Docker --> Tag
    Tag --> Push
    Push --> SSH
    SSH --> Deploy
    Deploy --> Verify
    Verify -->|Health OK| Success["✅ Deployment<br/>Complete"]
    Verify -->|Health FAIL| Rollback["⚠️ Rollback<br/>Previous Version"]

    style Git fill:#e1f5ff
    style Success fill:#c8e6c9
    style Rollback fill:#ffcdd2
    style Verify fill:#ffccbc
```

**Pipeline Details** (ADR-011):
- **Trigger**: Push to `main` branch
- **Lint**: Code style consistency (black, flake8, isort)
- **Test**: Unit + integration tests with coverage >60%
- **Type Check**: Static type analysis (mypy)
- **Docker Build**: Multi-stage build for minimal image size
- **Registry Push**: Docker image to container registry
- **SSH Deploy**: Secure connection to on-premise Eliot server
- **Health Verification**: POST-deploy health check validation
- **Rollback**: Automatic rollback if health check fails

**Workflow File**: `.github/workflows/deploy.yml`

---

## 4️⃣ ON-PREMISE NETWORK & SECURITY

```mermaid
graph TB
    subgraph "INTERNET"
        Users["👥 Textile QC Users<br/>Factory Floor<br/>Office"]
    end

    subgraph "FACTORY NETWORK (On-Premise)"
        Firewall["🔥 Firewall<br/>Port 443 HTTPS only<br/>Block non-SSL"]
        
        subgraph "ELIOT SERVER"
            Nginx_NET["📡 Nginx<br/>0.0.0.0:443<br/>SSL/TLS Certificate<br/>Self-signed or Let's Encrypt"]
            
            subgraph "APPLICATION NETWORK (localhost)"
                FastAPI_NET["🚀 FastAPI<br/>127.0.0.1:8000<br/>Internal only"]
            end
            
            subgraph "DATABASE NETWORK (localhost)"
                PostgreSQL_NET["🗄️ PostgreSQL<br/>127.0.0.1:5432<br/>Internal only"]
            end
        end

        WiFi["📡 Factory WiFi<br/>802.11ac<br/>Intermittent"]
        Ethernet["🔗 Wired Ethernet<br/>More Stable"]
    end

    Users -->|HTTPS Port 443| Firewall
    Firewall --> Nginx_NET
    Nginx_NET -->|Reverse Proxy| FastAPI_NET
    FastAPI_NET -->|SQLAlchemy ORM| PostgreSQL_NET
    Users ---|WiFi/Ethernet| Firewall

    style Firewall fill:#ffcdd2
    style Nginx_NET fill:#bbdefb
    style FastAPI_NET fill:#c8e6c9
    style PostgreSQL_NET fill:#fff9c4
    style WiFi fill:#ffccbc
```

**Security Model** (ADR-003):
- **HTTPS Only**: Nginx enforces SSL/TLS on port 443
- **JWT Authentication**: All API requests require Bearer token (8h expiration)
- **RBAC**: Role-based access control (ANALISTA, JEFE_QA, ADMIN, GERENTE)
- **Internal Services**: FastAPI and PostgreSQL listen only on localhost (127.0.0.1)
- **Firewall**: Factory firewall blocks non-HTTPS traffic to Eliot server
- **Network Resilience**: WiFi unreliability handled by offline-first sync (ADR-001)

---

## 5️⃣ DATA FLOW — ONLINE INSPECTION REGISTRATION

```mermaid
sequenceDiagram
    participant Analista as 📱 Analista<br/>Browser
    participant SW as ⚙️ Service Worker<br/>IndexedDB
    participant Nginx as 📡 Nginx<br/>443
    participant FastAPI as 🚀 FastAPI<br/>8000
    participant DB as 🗄️ PostgreSQL<br/>5432
    participant FS as 📸 File System<br/>/storage

    Analista->>Analista: 1. Fill Inspection Form<br/>(lote, defect, comment)
    Analista->>Analista: 2. Capture Photo
    Analista->>SW: 3. Click "Save"<br/>IndexedDB write
    SW->>SW: 4. Validate Photo<br/>(Laplacian blur, brightness)
    alt Photo Invalid
        SW-->>Analista: ❌ Photo quality issues
    else Photo Valid
        SW->>SW: 5. Generate UUID<br/>inspection_id
        SW->>SW: 6. Create Inspection<br/>object in IndexedDB
        Analista->>Nginx: 7. POST /api/inspections<br/>(offline, auto-sync)
        Nginx->>FastAPI: 8. Forward request
        FastAPI->>FastAPI: 9. Validate JWT token<br/>+ RBAC (ANALISTA role)
        FastAPI->>FastAPI: 10. Generate server<br/>timestamp (check_in)
        FastAPI->>DB: 11. INSERT inspection<br/>(inspection_id, UUID)
        DB-->>FastAPI: 12. Confirm insert<br/>(UNIQUE constraint)
        FastAPI->>FS: 13. Save photo to<br/>/storage/photos/YYYY/MM/DD/
        FS-->>FastAPI: 14. Photo saved
        FastAPI->>FastAPI: 15. Create domain event<br/>InspectionCreated
        FastAPI-->>Nginx: 16. 201 Created<br/>{inspection_id, sync_status}
        Nginx-->>SW: 17. Response
        SW->>SW: 18. Update IndexedDB<br/>sync_status = SYNCED
        SW-->>Analista: ✅ Inspection Saved<br/>(Online sync success)
    end
```

**Key Characteristics**:
- **Idempotency**: UUID inspection_id prevents duplicate submissions (ADR-001)
- **Photo Quality**: Client-side validation before sync (ADR-002)
- **Server Timestamp**: Server generates check_in time, not client (Business Rule BR-006)
- **Async Processing**: FastAPI async routes (ADR-004)
- **Offline Handling**: IndexedDB fallback if network unavailable

---

## 6️⃣ DATA FLOW — OFFLINE INSPECTION SYNC (RETRY LOOP)

```mermaid
sequenceDiagram
    participant IndexedDB as 💾 IndexedDB<br/>Pending Queue
    participant SW as ⚙️ Service Worker<br/>Retry Logic
    participant Nginx as 📡 Nginx
    participant FastAPI as 🚀 FastAPI

    IndexedDB->>IndexedDB: Store: sync_status=PENDING<br/>retry_count=0
    
    loop Every 5 seconds (when offline or manual sync)
        SW->>SW: 1. Check PENDING items<br/>in IndexedDB
        alt Items exist
            SW->>Nginx: 2. POST /api/inspections/sync-batch<br/>[inspection1, inspection2, ...]
            Nginx->>FastAPI: 3. Forward batch
            FastAPI->>FastAPI: 4. Validate each inspection<br/>idempotency check
            alt Server error (500) or timeout
                FastAPI-->>Nginx: ❌ Error response
                Nginx-->>SW: 5. 500/timeout
                SW->>SW: 6. Calculate backoff<br/>retry_count++<br/>wait_time = min(5*2^count, 60s)<br/>= 5s, 10s, 30s, 60s, 60s...
                IndexedDB->>IndexedDB: 7. Update: retry_count=N
            else Success
                FastAPI->>FastAPI: 8. Validate idempotency<br/>UNIQUE(inspection_id)
                FastAPI->>DB: 9. INSERT (if new)<br/>or skip (if exists)
                DB-->>FastAPI: ✅ Confirmed
                FastAPI-->>Nginx: 10. 201 Created
                Nginx-->>SW: 11. Success response
                SW->>IndexedDB: 12. Update:<br/>sync_status=SYNCED<br/>retry_count=0
                IndexedDB-->>SW: ✅ Cleared from pending
            end
        else No pending items
            SW->>SW: 🔄 Sleep 30s<br/>(reduced check frequency)
        end
    end
```

**Retry Parameters** (ADR-001, ADR-005):
- **Initial Delay**: 5 seconds
- **Exponential Backoff**: 5s → 10s → 30s → 60s → 60s (capped)
- **Max Retries**: 5 attempts before manual intervention
- **Total Window**: ~2 minutes for all retries to complete
- **Idempotency**: Duplicate submissions prevented by inspection_id UUID

**Success Guarantee**: Multi-layer persistence (ADR-001):
1. Layer 1: IndexedDB (local storage before sync)
2. Layer 2: Idempotent API (inspection_id unique constraint)
3. Layer 3: Exponential backoff retry (5x attempts)
4. **Result**: Zero data loss for inspections (100% guaranteed)

---

## 7️⃣ STORAGE ARCHITECTURE

```mermaid
graph TD
    subgraph "PHOTO STORAGE"
        Photos["📸 Photos Directory<br/>/storage/photos"]
        
        subgraph "Date-Sharded Structure"
            Year["📁 /2026"]
            Month["📁 /05"]
            Day["📁 /28"]
            Files["📄 inspection_id.jpg<br/>(500KB max each)"]
        end
        
        Manifest["📋 manifest.json<br/>Photo registry<br/>(optional)"]
    end

    subgraph "DATABASE STORAGE"
        Tables["🗄️ PostgreSQL Tables"]
        Users["👤 users"]
        Lotes["📦 lotes"]
        Inspections["🔍 inspections"]
        Approvals["✅ approvals"]
        Defects["❌ defects"]
        Machines["⚙️ machines"]
        Fabrics["🧵 fabrics"]
        AuditLogs["📋 audit_logs"]
    end

    subgraph "BACKUP STRATEGY"
        DBBackup["🔄 PostgreSQL Backups<br/>Daily snapshots<br/>30-day retention"]
        PhotoBackup["📸 Photo Backups<br/>Sync to NAS<br/>(optional)"]
    end

    Photos -->|Directory structure| Year
    Year --> Month
    Month --> Day
    Day --> Files
    Files -->|Indexed by| Manifest
    
    Tables --> Users
    Tables --> Lotes
    Tables --> Inspections
    Tables --> Approvals
    Tables --> Defects
    Tables --> Machines
    Tables --> Fabrics
    Tables --> AuditLogs
    
    Inspections -->|Reference| Files
    Inspections -.->|Foreign key| Defects
    
    Lotes -.->|Backup| DBBackup
    Inspections -.->|Backup| DBBackup
    Approvals -.->|Backup| DBBackup
    
    Files -.->|Backup| PhotoBackup

    style Photos fill:#f8bbd0
    style Tables fill:#fff9c4
    style DBBackup fill:#c8e6c9
    style PhotoBackup fill:#bbdefb
```

**Photo Storage** (ADR-012):
- **Path**: `/storage/photos/YYYY/MM/DD/{inspection_id}.jpg`
- **Sharding**: By date to avoid too many files per directory
- **Max Size**: 500KB per photo (enforced on client and server)
- **Access**: Via `PhotoStorage` class methods

**Database Storage** (ADR-009):
- **Tables**: 8 tables covering users, lotes, inspections, approvals, masters
- **Schema**: Fully normalized with FK constraints and indexes
- **Indexes**: Strategic indexes on hot query paths (lote_id, analista_id, sync_status)
- **Retention**: Perpetual (no deletion, archival planned for future)

**Backup Strategy**:
- Database: Daily PostgreSQL snapshots with 30-day retention
- Photos: Optional sync to NAS for redundancy

---

## 8️⃣ MONITORING & OBSERVABILITY ARCHITECTURE

```mermaid
graph TB
    subgraph "APPLICATION INSTRUMENTATION"
        FastAPI_Metrics["📊 FastAPI Metrics<br/>http_requests_total<br/>http_request_duration_seconds<br/>sync_failures_total<br/>inspections_created_total"]
        
        JSONLogs["📋 JSON Logs<br/>loguru<br/>structured format<br/>user_id, action, timestamp"]
    end

    subgraph "PROMETHEUS STACK"
        Prometheus["📊 Prometheus<br/>localhost:9090<br/>90-day retention<br/>scrape_interval=15s"]
        
        AlertRules["⚠️ Alert Rules<br/>error_rate > 1%<br/>latency_p99 > 5s<br/>sync_failures > 10%"]
        
        AlertManager["🔔 AlertManager<br/>localhost:9093"]
    end

    subgraph "VISUALIZATION & ALERTING"
        Grafana["📈 Grafana<br/>localhost:3000<br/>Dashboards"]
        
        Slack["📱 Slack<br/>Notifications<br/>via webhook"]
    end

    subgraph "LOG AGGREGATION"
        LogDir["📋 /var/log/fastapi<br/>JSON logs"]
        LogViewer["🔍 Log Viewer<br/>jq or ELK<br/>optional"]
    end

    FastAPI_Metrics -->|Expose /metrics| Prometheus
    JSONLogs -->|Write to| LogDir
    
    Prometheus -->|Evaluate| AlertRules
    AlertRules -->|Trigger| AlertManager
    AlertManager -->|Send| Slack
    
    Prometheus -->|Query data| Grafana
    Grafana -->|Display| Dashboards["📊 Dashboards<br/>Request rate<br/>Error rate<br/>Latency p50/p95/p99<br/>Sync success rate"]
    
    LogDir -->|Review| LogViewer
    
    style FastAPI_Metrics fill:#bbdefb
    style Prometheus fill:#ffe0b2
    style Grafana fill:#d1c4e9
    style Slack fill:#ffccbc
    style JSONLogs fill:#c8e6c9
```

**Metrics** (ADR-008):
- `http_requests_total`: Total requests by endpoint, method, status
- `http_request_duration_seconds`: Histogram (p50, p95, p99 latency)
- `sync_failures_total`: Count of failed sync attempts
- `inspections_created_total`: Count of created inspections (business metric)

**Logs** (ADR-008):
- Format: JSON (structured, queryable)
- Fields: timestamp, user_id, action, duration_ms, status, error_message
- Storage: `/var/log/fastapi/app.log`
- Tool: loguru (Python logging replacement)

**Alerts** (ADR-013):
- **Error Rate**: If >1% of requests fail → alert
- **Latency**: If p99 latency >5s → alert
- **Sync Failures**: If >10% of sync attempts fail → alert
- **Notifications**: Sent to Slack via webhook

**Grafana Dashboards**:
- Request rate and error rate trends
- Latency percentiles (p50, p95, p99)
- Sync success vs. failure rates
- Inspection creation trends
- Database connection pool utilization

---

## 9️⃣ CONFIGURATION & SECRETS MANAGEMENT

```mermaid
graph LR
    subgraph "LOCAL DEVELOPMENT (.env file)"
        EnvLocal["🔑 .env<br/>(git-ignored)<br/>LOCAL development values"]
        LocalVars["<br/>DATABASE_URL=postgresql://localhost/fastapi_qc<br/>JWT_SECRET_KEY=dev-secret-key<br/>ENVIRONMENT=development<br/>LOG_LEVEL=DEBUG"]
    end

    subgraph "PRODUCTION ELIOT SERVER"
        EnvProd["🔑 .env<br/>(git-ignored)<br/>PRODUCTION secrets"]
        ProdVars["<br/>DATABASE_URL=postgresql://db.eliot/fastapi_qc<br/>JWT_SECRET_KEY=***production-key***<br/>ENVIRONMENT=production<br/>GRAFANA_PASSWORD=***secure***<br/>SLACK_WEBHOOK_URL=***webhook***"]
    end

    subgraph "APPLICATION CODE"
        ConfigFile["⚙️ config.yaml<br/>(git-tracked)<br/>Non-secret settings"]
        ConfigContent["<br/>audit:<br/>  enabled: true<br/>  log_level: INFO<br/>photo_storage:<br/>  max_size_kb: 500<br/>  base_path: /storage/photos<br/>retry:<br/>  initial_delay_s: 5<br/>  max_retries: 5"]
        
        PyConfig["🐍 config.py<br/>Pydantic BaseSettings<br/>reads .env + config.yaml"]
    end

    EnvLocal --> LocalVars
    EnvProd --> ProdVars
    ConfigFile --> ConfigContent
    
    LocalVars -->|Load at startup| PyConfig
    ProdVars -->|Load at startup| PyConfig
    ConfigContent -->|Load at startup| PyConfig
    PyConfig -->|Inject into routes| Routes["🚀 Routes<br/>Use config values"]

    style EnvLocal fill:#ffcdd2
    style EnvProd fill:#c8e6c9
    style ConfigFile fill:#bbdefb
    style PyConfig fill:#ffe0b2
```

**Secrets Management** (ADR-014):
- **.env file**: Git-ignored, contains sensitive values
  - `DATABASE_URL`: PostgreSQL connection string
  - `JWT_SECRET_KEY`: Secret key for JWT signing
  - `GRAFANA_PASSWORD`: Admin password
  - `SLACK_WEBHOOK_URL`: For alert notifications
- **config.yaml**: Git-tracked, contains non-sensitive settings
  - Audit logging configuration
  - Photo storage parameters
  - Retry logic parameters
  - Feature flags

**Configuration Loading**:
```python
# config.py (Pydantic BaseSettings)
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str  # Reads DATABASE_URL from .env
    jwt_secret_key: str  # Reads JWT_SECRET_KEY from .env
    environment: str = "development"  # Defaults to development
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

---

## 🔟 RESOURCE REQUIREMENTS (ELIOT SERVER)

```mermaid
graph TD
    subgraph "CPU & MEMORY"
        CPU["🖥️ CPU<br/>Minimum: 4 cores<br/>Recommended: 8 cores"]
        RAM["💾 RAM<br/>Minimum: 8 GB<br/>Recommended: 16 GB<br/>(4GB FastAPI + 4GB PostgreSQL)"]
    end

    subgraph "STORAGE"
        AppStorage["📦 Application<br/>~500 MB<br/>(Python packages + code)"]
        DBStorage["🗄️ Database<br/>50-100 GB<br/>(110K+ inspections)"]
        PhotoStorage["📸 Photos<br/>900 GB/month<br/>(at 50 concurrent users<br/>20 photos/day per user)"]
        LogStorage["📋 Logs<br/>10-20 GB/month<br/>(JSON structured logs)"]
    end

    subgraph "NETWORK"
        Bandwidth["📡 Network Bandwidth<br/>Minimum: 100 Mbps LAN<br/>Recommended: 1 Gbps LAN"]
    end

    subgraph "DISK I/O"
        DiskType["💿 Disk Type<br/>SSD preferred<br/>Min: 7200 RPM HDD"]
        IOPS["🔄 IOPS<br/>~5000 IOPS for<br/>peak load"]
    end

    CPU --> Total["📊 TOTAL CAPACITY"]
    RAM --> Total
    AppStorage -->|Combined| TotalStorage["📦 1-2 TB<br/>Initial + growth"]
    DBStorage --> TotalStorage
    PhotoStorage --> TotalStorage
    LogStorage --> TotalStorage
    TotalStorage --> Total
    Bandwidth --> Total
    DiskType --> Total
    IOPS --> Total

    style CPU fill:#bbdefb
    style RAM fill:#c8e6c9
    style TotalStorage fill:#fff9c4
    style Total fill:#f0f4c3
```

**Server Sizing** (ADR-010):
- **CPU**: 4 cores minimum (1 per Uvicorn worker), 8 cores recommended
- **RAM**: 8 GB minimum (4GB FastAPI + 4GB PostgreSQL), 16 GB recommended
- **Storage**: 1-2 TB SSD (application + database + photos + logs)
- **Network**: 1 Gbps LAN preferred for reliability
- **Disk I/O**: ~5000 IOPS during peak inspection sync

---

## ✅ DEPLOYMENT CHECKLIST

Before deploying to on-premise Eliot server:

### Pre-Deployment
- [ ] PostgreSQL 13+ installed and running
- [ ] /storage/photos directory created with correct permissions
- [ ] systemd service file copied to /etc/systemd/system/fastapi-qc.service
- [ ] .env file created with production secrets (DATABASE_URL, JWT_SECRET_KEY, etc.)
- [ ] config.yaml in place with audit and photo storage settings
- [ ] SSL/TLS certificate installed on Nginx (self-signed or Let's Encrypt)
- [ ] Python 3.11 venv created with dependencies installed

### Deployment Steps
- [ ] Run database migrations: `alembic upgrade head`
- [ ] Enable systemd service: `sudo systemctl enable fastapi-qc`
- [ ] Start service: `sudo systemctl start fastapi-qc`
- [ ] Verify health endpoint: `curl https://localhost/health`
- [ ] Check Nginx reverse proxy: `curl https://localhost` (should proxy to FastAPI)
- [ ] Verify FastAPI is listening: `ss -tln | grep 8000`

### Post-Deployment
- [ ] Test offline inspection sync (take offline, create inspection, bring online)
- [ ] Verify photo storage working (check /storage/photos/{YYYY}/{MM}/{DD}/)
- [ ] Check Prometheus metrics: `curl http://localhost:9090/api/v1/targets`
- [ ] Verify Grafana dashboards load: http://localhost:3000
- [ ] Test AlertManager alerts with Slack integration
- [ ] Validate authentication: Test JWT token creation and RBAC enforcement
- [ ] Run health check script: Monitor /health endpoint for 5 minutes

### Monitoring Setup
- [ ] Prometheus configured to scrape FastAPI /metrics
- [ ] Grafana dashboards created for key metrics
- [ ] AlertManager rules configured (error rate, latency, sync failures)
- [ ] Slack webhook URL configured for notifications
- [ ] Log aggregation setup (tail -f /var/log/fastapi/app.log)

---

## 📋 REFERENCES

For detailed architecture decision rationale, see:
- **ADR-009**: Database Schema (PostgreSQL)
- **ADR-010**: Deployment Architecture (Docker + Systemd)
- **ADR-011**: CI/CD Pipeline (GitHub Actions)
- **ADR-012**: File Storage (Local Filesystem)
- **ADR-013**: Monitoring Infrastructure (Prometheus + Grafana)
- **ADR-014**: Configuration Management (.env + config.yaml)
- **ADR-015**: Project Layout (FastAPI Standard + DDD)

All located in `infrastructure-design.md`

---

**Status**: ✅ ACCEPTED  
**Last Updated**: 2026-05-28

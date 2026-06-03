# Deployment Architecture — Complete Mermaid Diagrams
## Activity 4 — Frontend Web Unit

**Date**: 2026-05-31  
**Status**: ACCEPTED  
**Scope**: Full deployment topology, CI/CD pipeline, data flows, and disaster recovery

---

## 1️⃣ DEPLOYMENT TOPOLOGY (On-Premises)

```mermaid
graph TB
    subgraph "Factory Network (Intranet - 192.168.x.x)"
        subgraph "Production Server (Ubuntu 22.04 LTS)"
            subgraph "Docker Containers"
                FE["React App<br/>(nginx:3000)"]
                BE["Backend API<br/>(FastAPI:8000)"]
                DB["PostgreSQL<br/>(5432)"]
                CACHE["Redis<br/>(6379)"]
            end
            
            subgraph "Infrastructure"
                NGINX["Nginx Reverse Proxy<br/>(443/80)"]
                LOG["Logging Stack<br/>(Filebeat→ELK)"]
                MON["Monitoring<br/>(Prometheus)"]
            end
            
            subgraph "Storage"
                PHOTOS["Photo Storage<br/>(/data/photos)"]
                BACKUP["Local Backups<br/>(/backups)"]
            end
            
            NGINX -->|HTTPS| FE
            NGINX -->|API /api/*| BE
            FE -->|HTTP| BE
            BE -->|ORM| DB
            BE -->|Session/Cache| CACHE
            BE -->|Logs| LOG
            BE -->|Metrics| MON
            BE -->|Photos| PHOTOS
            DB -->|Backup| BACKUP
        end
        
        subgraph "Monitoring & Alerting"
            ELASTIC["Elasticsearch<br/>(9200)"]
            KIBANA["Kibana<br/>(5601)"]
            PROM["Prometheus<br/>(9090)"]
            GRAFANA["Grafana<br/>(3001)"]
            SLACK["Slack Webhook<br/>(Alerts)"]
        end
        
        LOG -->|Ship| ELASTIC
        ELASTIC -->|Visualize| KIBANA
        MON -->|Scrape| PROM
        PROM -->|Visualize| GRAFANA
        PROM -->|Alert| SLACK
    end
    
    subgraph "External (Optional)"
        GH["GitHub<br/>(Code + Actions)"]
        DOCKER["Docker Registry<br/>(Images)"]
    end
    
    GH -.->|Webhook| BE
    GH -.->|Push Images| DOCKER
    
    subgraph "Users"
        OP["Operarios<br/>(Analistas)"]
        QA["Jefe QA<br/>(Supervisores)"]
        ADM["Admin"]
    end
    
    OP -->|HTTPS| NGINX
    QA -->|HTTPS| NGINX
    ADM -->|HTTPS| NGINX
```

---

## 2️⃣ CONTINUOUS INTEGRATION & DEPLOYMENT (CI/CD)

```mermaid
graph LR
    subgraph "Development"
        DEV["Developer<br/>Commits Code"]
    end
    
    subgraph "GitHub (Source Control)"
        GH["Repository<br/>(main/develop)"]
    end
    
    subgraph "GitHub Actions (CI/CD)"
        subgraph "Stage 1: Test"
            LINT["Lint<br/>(ESLint)"]
            TYPE["Type Check<br/>(TypeScript)"]
            TEST["Unit Tests<br/>(Jest)"]
            PYTEST["Backend Tests<br/>(pytest)"]
        end
        
        subgraph "Stage 2: Build"
            BUILD_FE["Build Frontend<br/>(React)"]
            BUILD_IMG_FE["Docker Image<br/>(frontend)"]
            BUILD_IMG_BE["Docker Image<br/>(backend)"]
            PUSH_IMG["Push to Registry<br/>(Docker Hub)"]
        end
        
        subgraph "Stage 3: Deploy"
            PULL["Pull Images<br/>(Latest)"]
            MIGRATE["DB Migrations<br/>(Alembic)"]
            DEPLOY["Deploy<br/>(docker-compose up)"]
            HEALTH["Health Check<br/>(curl /health)"]
        end
    end
    
    subgraph "Production Server"
        PROD["Running Services<br/>(Frontend + Backend)"]
    end
    
    subgraph "Notifications"
        SLACK_OK["✅ Slack<br/>Success"]
        SLACK_FAIL["❌ Slack<br/>Failure"]
    end
    
    DEV -->|git push| GH
    GH -->|trigger| LINT
    LINT --> TYPE
    TYPE --> TEST
    TEST --> PYTEST
    PYTEST -->|pass| BUILD_FE
    BUILD_FE --> BUILD_IMG_FE
    BUILD_IMG_FE --> BUILD_IMG_BE
    BUILD_IMG_BE --> PUSH_IMG
    PUSH_IMG --> PULL
    PULL --> MIGRATE
    MIGRATE --> DEPLOY
    DEPLOY --> HEALTH
    HEALTH -->|pass| SLACK_OK
    HEALTH -->|fail| SLACK_FAIL
    SLACK_OK --> PROD
```

---

## 3️⃣ FRONTEND ARCHITECTURE (Services & State)

```mermaid
graph TB
    subgraph "React Component Layer"
        PAGES["Pages<br/>(Inspection, Approval, Config, Dashboard)"]
        COMP["Components<br/>(Forms, Tables, Modals, Auth)"]
    end
    
    subgraph "Zustand Store Layer"
        AUTH_STORE["Auth Store<br/>(user, token, roles)"]
        INSP_STORE["Inspection Store<br/>(lotes, defects, drafts)"]
        APPR_STORE["Approval Store<br/>(pending, history)"]
        MASTER_STORE["Master Store<br/>(defects, machines, fabrics)"]
        OFFLINE_STORE["Offline Store<br/>(syncQueue, status)"]
    end
    
    subgraph "Service Layer"
        AUTH_SVC["Auth Service<br/>(login, refresh)"]
        INSP_SVC["Inspection Service<br/>(register, sync)"]
        APPR_SVC["Approval Service<br/>(approve, reject)"]
        MASTER_SVC["Master Service<br/>(CRUD)"]
        TRACK_SVC["Tracking Services<br/>(errors, performance, analytics)"]
        SYNC_SVC["Offline Sync Service<br/>(queue, retry)"]
    end
    
    subgraph "Local Storage Layer"
        DB["IndexedDB<br/>(Dexie.js)"]
        SW["Service Worker<br/>(Background sync)"]
    end
    
    subgraph "API Layer"
        API["Axios Instance<br/>(Interceptors, auth, errors)"]
    end
    
    subgraph "Backend API"
        BE["FastAPI Backend<br/>(https://api.company.local)"]
    end
    
    PAGES -->|useState| COMP
    COMP -->|useAuth, useInspection, etc| AUTH_STORE
    COMP -->|useInspection| INSP_STORE
    COMP -->|useApproval| APPR_STORE
    COMP -->|useMaster| MASTER_STORE
    COMP -->|useOffline| OFFLINE_STORE
    
    AUTH_STORE -->|call| AUTH_SVC
    INSP_STORE -->|call| INSP_SVC
    APPR_STORE -->|call| APPR_SVC
    MASTER_STORE -->|call| MASTER_SVC
    INSP_SVC -->|call| SYNC_SVC
    
    INSP_SVC -->|save| DB
    INSP_SVC -->|notify| SW
    
    AUTH_SVC -->|call| API
    INSP_SVC -->|call| API
    APPR_SVC -->|call| API
    MASTER_SVC -->|call| API
    TRACK_SVC -->|POST /api/errors| API
    TRACK_SVC -->|POST /api/analytics| API
    
    SW -->|retry on online| API
    
    API -->|HTTP/REST| BE
    DB -->|local cache| INSP_SVC
```

---

## 4️⃣ BACKEND ARCHITECTURE (FastAPI Services)

```mermaid
graph TB
    subgraph "HTTP Requests"
        REQ["HTTP Requests<br/>(Clients)"]
    end
    
    subgraph "Nginx Reverse Proxy"
        PROXY["Nginx<br/>(SSL/TLS, routing)"]
    end
    
    subgraph "FastAPI Application"
        subgraph "Middleware Layer"
            CORS["CORS<br/>Middleware"]
            AUTH_MID["JWT Auth<br/>Middleware"]
            RBAC_MID["RBAC<br/>Middleware"]
            LOG_MID["Logging<br/>Middleware"]
            ERR_MID["Error Handler<br/>Middleware"]
        end
        
        subgraph "Route Layer"
            AUTH_ROUTE["/auth<br/>(login, refresh, logout)"]
            INSP_ROUTE["/inspections<br/>(create, list, sync)"]
            APPR_ROUTE["/approvals<br/>(create, stats)"]
            MASTER_ROUTE["/masters<br/>(CRUD)"]
            HEALTH_ROUTE["/health<br/>(status)"]
            ERROR_ROUTE["/api/errors<br/>(logging)"]
            ANALYTICS_ROUTE["/api/analytics<br/>(events)"]
        end
        
        subgraph "Service Layer"
            AUTH_SVC["AuthService<br/>(JWT, password hashing)"]
            INSP_SVC["InspectionService<br/>(register, retrieve)"]
            APPR_SVC["ApprovalService<br/>(approve, reject)"]
            MASTER_SVC["MasterService<br/>(CRUD, cache)"]
            SYNC_SVC["SyncService<br/>(merge offline)"]
        end
        
        subgraph "Data Access Layer"
            ORM["SQLAlchemy ORM<br/>(Models)"]
        end
    end
    
    subgraph "Database & Storage"
        DB["PostgreSQL<br/>(users, inspections, approvals)"]
        CACHE["Redis<br/>(sessions, cache)"]
        FILES["File Storage<br/>(/data/photos)"]
    end
    
    subgraph "Monitoring & Logging"
        LOGGER["Python Logger<br/>(JSON format)"]
        FILEBEAT["Filebeat<br/>(ship logs)"]
    end
    
    REQ -->|HTTPS| PROXY
    PROXY -->|route| CORS
    CORS --> AUTH_MID
    AUTH_MID --> RBAC_MID
    RBAC_MID --> LOG_MID
    LOG_MID --> ERR_MID
    
    ERR_MID --> AUTH_ROUTE
    ERR_MID --> INSP_ROUTE
    ERR_MID --> APPR_ROUTE
    ERR_MID --> MASTER_ROUTE
    ERR_MID --> HEALTH_ROUTE
    ERR_MID --> ERROR_ROUTE
    ERR_MID --> ANALYTICS_ROUTE
    
    AUTH_ROUTE -->|call| AUTH_SVC
    INSP_ROUTE -->|call| INSP_SVC
    APPR_ROUTE -->|call| APPR_SVC
    MASTER_ROUTE -->|call| MASTER_SVC
    INSP_ROUTE -->|call| SYNC_SVC
    
    AUTH_SVC -->|query| ORM
    INSP_SVC -->|query| ORM
    APPR_SVC -->|query| ORM
    MASTER_SVC -->|query| ORM
    
    ORM -->|SQL| DB
    AUTH_SVC -->|sessions| CACHE
    MASTER_SVC -->|cache| CACHE
    INSP_SVC -->|save photos| FILES
    
    LOG_MID -->|JSON logs| LOGGER
    FILEBEAT -->|collect| LOGGER
```

---

## 5️⃣ DATA FLOW: INSPECTION CREATION (Happy Path)

```mermaid
sequenceDiagram
    participant User as User (Operario)
    participant Frontend as Frontend (React)
    participant IDB as IndexedDB
    participant SW as Service Worker
    participant API as API (Axios)
    participant Backend as Backend (FastAPI)
    participant DB as PostgreSQL
    participant Files as File Storage
    
    User->>Frontend: Busca lote HDR-12847
    Frontend->>API: GET /api/lotes/{id}
    API->>Backend: Query lote
    Backend->>DB: SELECT lote
    DB-->>Backend: Lote data
    Backend-->>API: { fabric, id, ... }
    API-->>Frontend: Cached in Zustand
    
    User->>Frontend: Captura foto (Offline!)
    Frontend->>IDB: Save photo blob
    IDB-->>Frontend: Photo saved
    
    User->>Frontend: Selecciona defecto + comentario
    Frontend->>Frontend: Completa inspection draft
    Frontend->>IDB: Save inspection draft
    
    User->>Frontend: Presiona "Guardar"
    Frontend->>IDB: Create syncQueue item
    Frontend->>Zustand: Update sync status "PENDING"
    
    alt Online?
        Frontend->>SW: Notify sync triggered
        SW->>IDB: Query pending items
        IDB-->>SW: [inspection, photos]
        SW->>API: POST /api/inspections/sync
        API->>Backend: { inspection, photos: [base64] }
        Backend->>Files: Save photo.jpg
        Backend->>DB: INSERT inspection
        DB-->>Backend: OK
        Backend-->>API: { id, synced: true }
        API-->>SW: Success
        SW->>IDB: Update syncQueue item → SYNCED
        Frontend->>Frontend: UI shows "✅ Synced"
    else Offline
        Frontend->>Frontend: UI shows "📴 Guardado localmente"
        Frontend->>Frontend: Retry cuando hay wifi
    end
```

---

## 6️⃣ DATA FLOW: APPROVAL WORKFLOW

```mermaid
sequenceDiagram
    participant QA as Jefe QA
    participant Frontend as Frontend
    participant API as API
    participant Backend as Backend
    participant DB as PostgreSQL
    participant Slack as Slack Webhook
    
    QA->>Frontend: Abre Approval Queue
    Frontend->>API: GET /api/inspections/pending-approval
    API->>Backend: Query inspections where status=REGISTERED
    Backend->>DB: SELECT * WHERE approved_at IS NULL
    DB-->>Backend: [Inspection 1, 2, 3, ...]
    Backend-->>API: Response with photo URLs
    API-->>Frontend: Display in table
    
    QA->>Frontend: Selecciona Inspection #1
    Frontend->>API: GET /api/inspections/{id}
    API-->>Frontend: Full details + photo
    Frontend->>Frontend: Show modal
    
    QA->>Frontend: Presiona "APROBAR"
    Frontend->>API: POST /api/approvals
    Note over API: { inspection_id, status: APPROVED, comment? }
    API->>Backend: Validate RBAC (JEFE_QA role)
    Backend->>DB: BEGIN TRANSACTION
    Backend->>DB: INSERT approval
    Backend->>DB: UPDATE inspection SET approved_by=user_id
    Backend->>DB: COMMIT
    DB-->>Backend: OK
    Backend->>Slack: Send notification (optional)
    Backend-->>API: { id, status: APPROVED }
    API-->>Frontend: Success
    Frontend->>Frontend: Remove from list, show success toast
```

---

## 7️⃣ OFFLINE SYNCHRONIZATION FLOW

```mermaid
graph LR
    subgraph "Offline Phase"
        CAP["Capture Inspection<br/>(offline)"]
        IDB_SAVE["Save to IndexedDB"]
        QUEUE["Add to syncQueue<br/>(status=PENDING)"]
        LOCAL_OK["✅ Show 'Saved locally'"]
    end
    
    subgraph "Online Phase"
        CHECK["Detect online<br/>(navigator.onLine)"]
        RETRY["Retry failed items<br/>(status=SYNCED)"]
        BACKOFF["Exponential Backoff<br/>([5s, 10s, 30s, 60s, 60s])"]
        SYNC["POST /api/inspections/sync<br/>(+ photos base64)"]
        MERGE["Server merges<br/>offline changes"]
        UPDATE["Update local<br/>(status=SYNCED)"]
        DONE["✅ All synced"]
    end
    
    subgraph "Failure Path"
        FAILED["Failed after 5 retries<br/>(status=FAILED)"]
        ALERT["Alert user<br/>(🔴 Manual retry)"]
        RETRY_MANUAL["User taps Retry"]
    end
    
    CAP --> IDB_SAVE
    IDB_SAVE --> QUEUE
    QUEUE --> LOCAL_OK
    LOCAL_OK -.->|Auto-check every 30s| CHECK
    CHECK -->|Online?| SYNC
    SYNC -->|Success| MERGE
    MERGE --> UPDATE
    UPDATE --> DONE
    CHECK -->|Offline| CHECK
    
    SYNC -->|Failure| BACKOFF
    BACKOFF -->|Retry| SYNC
    BACKOFF -->|5 attempts failed| FAILED
    FAILED --> ALERT
    ALERT --> RETRY_MANUAL
    RETRY_MANUAL --> SYNC
```

---

## 8️⃣ MONITORING & ALERTING ARCHITECTURE

```mermaid
graph TB
    subgraph "Data Collection"
        APP["Application Metrics<br/>(Prometheus /metrics)"]
        LOGS["Application Logs<br/>(JSON format)"]
        ERRORS["Error Reports<br/>(POST /api/errors)"]
        ANALYTICS["Analytics Events<br/>(POST /api/analytics)"]
    end
    
    subgraph "Log Aggregation"
        FILEBEAT["Filebeat<br/>(Ship logs)"]
        LOGSTASH["Logstash<br/>(Parse)"]
        ELASTIC["Elasticsearch<br/>(Store)"]
    end
    
    subgraph "Metrics Storage"
        PROM["Prometheus<br/>(Time-series DB)"]
        PROM_RULES["Alert Rules<br/>(thresholds)"]
    end
    
    subgraph "Visualization"
        KIBANA["Kibana<br/>(Logs dashboard)"]
        GRAFANA["Grafana<br/>(Metrics dashboard)"]
    end
    
    subgraph "Alerting"
        PROM_ALERT["Prometheus Alertmanager"]
        SLACK_ALERT["Slack Webhook<br/>(Notifications)"]
        EMAIL_ALERT["Email Alerts<br/>(Critical only)"]
    end
    
    subgraph "Dashboards (Examples)"
        DASH1["Error Rate % (Red if >1%)"]
        DASH2["API Response Time p99 (Red if >5s)"]
        DASH3["Sync Queue Depth (Red if >100)"]
        DASH4["Server Resources (CPU, RAM, Disk)"]
        DASH5["Database Connections (Red if >80)"]
    end
    
    APP -->|scrape| PROM
    LOGS --> FILEBEAT
    ERRORS -->|POST| ELASTIC
    ANALYTICS -->|POST| ELASTIC
    
    FILEBEAT --> LOGSTASH
    LOGSTASH --> ELASTIC
    
    PROM --> PROM_RULES
    PROM_RULES --> PROM_ALERT
    PROM_ALERT --> SLACK_ALERT
    PROM_ALERT --> EMAIL_ALERT
    
    ELASTIC -->|query| KIBANA
    PROM -->|query| GRAFANA
    
    GRAFANA --> DASH1
    GRAFANA --> DASH2
    GRAFANA --> DASH3
    GRAFANA --> DASH4
    GRAFANA --> DASH5
    
    KIBANA -->|search| LOGS
```

---

## 9️⃣ DISASTER RECOVERY FLOW

```mermaid
graph TB
    subgraph "Backup Strategy"
        DAILY["Daily Backup<br/>(Full DB + files)<br/>Time: 02:00 AM<br/>Retention: 7 days"]
        WEEKLY["Weekly Backup<br/>(Full system)<br/>Time: Sunday 03:00 AM<br/>Retention: 4 weeks"]
        MONTHLY["Monthly Archive<br/>(Off-site)<br/>Time: 1st Sunday<br/>Retention: 12 months"]
        VERIFY["Verification<br/>(Daily restore test)"]
    end
    
    subgraph "Failure Scenarios"
        SCENARIO1["DB Corruption<br/>(Data loss)"]
        SCENARIO2["Server Failure<br/>(Hardware)"]
        SCENARIO3["Disk Full<br/>(No space)"]
        SCENARIO4["Data Loss<br/>(Accidental delete)"]
    end
    
    subgraph "Recovery Procedures"
        PROC1["Restore from Daily<br/>(RTO: 30min)<br/>(RPO: 6hr)"]
        PROC2["Rebuild from Weekly<br/>(RTO: 2hr)<br/>(RPO: 7 days)"]
        PROC3["Disk cleanup +<br/>compress photos<br/>(RTO: 15min)"]
        PROC4["Restore from Archive<br/>(RTO: 24hr)<br/>(RPO: 30 days)"]
    end
    
    subgraph "Validation"
        TEST1["Data Integrity<br/>CHECK"]
        TEST2["Service Health<br/>CHECK"]
        TEST3["User Access<br/>CHECK"]
        NOTIFY["Send Slack<br/>Notification"]
    end
    
    DAILY --> VERIFY
    WEEKLY --> VERIFY
    MONTHLY --> VERIFY
    
    SCENARIO1 --> PROC1
    SCENARIO2 --> PROC2
    SCENARIO3 --> PROC3
    SCENARIO4 --> PROC4
    
    PROC1 --> TEST1
    PROC2 --> TEST1
    PROC3 --> TEST2
    PROC4 --> TEST1
    
    TEST1 --> TEST2
    TEST2 --> TEST3
    TEST3 --> NOTIFY
```

---

## 🔟 DEPLOYMENT CHECKLIST

```mermaid
checklist
- [ ] Production Server provisioned (8GB RAM, 4 CPU, 500GB SSD, Ubuntu 22.04)
- [ ] Docker & Docker Compose installed
- [ ] Nginx reverse proxy configured with SSL
- [ ] PostgreSQL database initialized with schema
- [ ] Redis cache running
- [ ] GitHub Actions workflow configured for CI/CD
- [ ] Environment variables (.env) set securely
- [ ] ELK stack running (Elasticsearch, Logstash, Kibana)
- [ ] Prometheus + Grafana for metrics
- [ ] Backup scripts scheduled (cron jobs)
- [ ] Slack webhooks configured
- [ ] Service Worker + IndexedDB working (tested in browser)
- [ ] DNS configured (qc.factory.local)
- [ ] SSL certificate installed (Let's Encrypt)
- [ ] Firewall rules applied (only 80/443 exposed)
- [ ] Health check endpoint configured
- [ ] Monitoring dashboards created
- [ ] Disaster recovery plan documented
- [ ] Team trained on deployment procedures
- [ ] Smoke tests passed on production
```

---

## 📊 DEPLOYMENT SUMMARY TABLE

| Component | Technology | Config | Status |
|-----------|-----------|--------|--------|
| **OS** | Ubuntu 22.04 LTS | Server, VM | ✅ |
| **Web Server** | Nginx Alpine | Reverse proxy, SSL | ✅ |
| **Frontend** | React 18 | Docker, Node 18 | ✅ |
| **Backend** | FastAPI | Docker, Python 3.11 | ✅ |
| **Database** | PostgreSQL 15 | Docker, alpine | ✅ |
| **Cache** | Redis 7 | Docker, alpine | ✅ |
| **Logs** | ELK Stack | Elasticsearch, Kibana | ✅ |
| **Metrics** | Prometheus | Time-series DB | ✅ |
| **Visualization** | Grafana | Dashboards | ✅ |
| **Backup** | Tar + Cron | Daily/Weekly/Monthly | ✅ |
| **Monitoring** | Custom services | /metrics, /health | ✅ |
| **CI/CD** | GitHub Actions | Test, build, deploy | ✅ |
| **Storage** | Filesystem | /data/photos | ✅ |
| **SSL/TLS** | Let's Encrypt | https:// enforced | ✅ |

---

**Status**: ✅ ACCEPTED  
**Implementation**: Docker Compose + GitHub Actions + ELK + Prometheus/Grafana  
**Testing**: Deployment tests, backup recovery tests, failover tests, load tests


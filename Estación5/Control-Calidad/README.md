# Textile Quality Control — Backend API

FastAPI backend for textile quality control system with offline-first synchronization, JWT authentication, and role-based access control.

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- pip/venv

### Installation

1. **Clone and setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials and secrets
```

3. **Initialize database**
```bash
alembic upgrade head
```

4. **Run server**
```bash
uvicorn app.main:app --reload --port 8000
```

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://user:password@localhost/fastapi_qc` |
| `JWT_SECRET_KEY` | Secret key for JWT signing | `your-secret-key-here` |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_EXPIRATION_HOURS` | Access token expiration | `8` |
| `ENVIRONMENT` | Deployment environment | `development` or `production` |
| `LOG_LEVEL` | Logging level | `DEBUG`, `INFO`, `WARNING` |

## Project Structure

```
app/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration & settings (Pydantic)
├── database.py          # PostgreSQL async session
├── lifespan.py          # Startup/shutdown events
│
├── domain/              # Pure business logic (DDD)
│   ├── entities.py      # Aggregates: Inspection, Approval, Lote
│   ├── value_objects.py # DefectType, Comment, Photograph, etc.
│   ├── events.py        # Domain events
│   └── services/        # Domain services
│       ├── inspection_service.py
│       ├── approval_service.py
│       └── masters_service.py
│
├── models/              # SQLAlchemy ORM models
│   ├── base.py          # Base model class
│   └── orm.py           # All 8 tables
│
├── repositories/        # Data access layer
│   ├── base.py          # BaseRepository interface
│   ├── inspection_repository.py
│   ├── approval_repository.py
│   ├── masters_repository.py
│   ├── user_repository.py
│   └── audit_repository.py
│
├── application/         # Use cases & orchestration
│   └── use_cases.py
│
├── auth/                # Authentication & authorization
│   ├── security.py      # JWT, password hashing
│   └── dependencies.py  # FastAPI dependencies
│
├── routes/              # API endpoints
│   ├── auth.py
│   ├── inspections.py
│   ├── approvals.py
│   ├── masters.py
│   └── config.py
│
├── schemas/             # Pydantic request/response models
│   ├── inspection_schemas.py
│   ├── approval_schemas.py
│   ├── masters_schemas.py
│   └── common.py
│
├── middleware/          # Request/response middleware
│   └── auth_middleware.py
│
└── monitoring/          # Logging & metrics
    ├── audit_logger.py
    └── events.py

tests/
├── conftest.py          # Pytest fixtures
├── unit/                # Unit tests (>80% coverage)
│   ├── test_inspection_service.py
│   ├── test_approval_service.py
│   ├── test_masters_service.py
│   └── test_repositories.py
│
└── integration/         # Integration tests (E2E)
    ├── test_inspection_routes.py
    ├── test_approval_routes.py
    ├── test_masters_routes.py
    ├── test_auth_routes.py
    └── test_offline_sync.py

migrations/
├── env.py               # Alembic environment
├── script.py.mako       # Migration template
└── versions/            # Migration files (001_initial_schema.py, etc.)
```

## API Endpoints

### Authentication
- `POST /auth/login` — Login with email/password, returns JWT token
- `POST /auth/refresh` — Refresh expired access token

### Inspections
- `POST /api/inspections` — Create new inspection (ANALISTA)
- `POST /api/inspections/sync-batch` — Batch sync for offline entries
- `GET /api/inspections` — List inspections with pagination

### Approvals
- `POST /api/approvals` — Approve/reject inspection (JEFE_QA)
- `GET /api/approvals/pending` — List pending approvals

### Masters
- `GET /api/defects` — List defect types
- `GET /api/machines` — List machines
- `GET /api/fabrics` — List fabrics
- `POST /api/masters/import-csv` — Bulk import masters (ADMIN)

### Config
- `GET /api/config` — Fetch frontend configuration

## Testing

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

### Run only unit tests
```bash
pytest tests/unit
```

### Run only integration tests
```bash
pytest tests/integration
```

## Database Migrations

### Create a new migration
```bash
alembic revision --autogenerate -m "Add column to inspections"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback last migration
```bash
alembic downgrade -1
```

## Deployment (On-Premise Eliot)

See `aidlc-docs/construction/deployment-architecture.md` for detailed deployment guide.

### Quick deploy
```bash
git pull origin main
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart fastapi-qc
```

## Monitoring

- **Metrics**: Prometheus endpoint at `/metrics`
- **Logs**: JSON structured logs in `/var/log/fastapi/app.log`
- **Health**: `GET /health` for liveness/readiness checks

## Documentation

- **Architecture**: `aidlc-docs/construction/deployment-architecture.md`
- **API Design**: `aidlc-docs/construction/infrastructure-design.md`
- **Business Rules**: `aidlc-docs/construction/business-rules.md`
- **Domain Model**: `aidlc-docs/construction/domain-entities.md`
- **Code Summary**: `aidlc-docs/construction/code-summary.md` (generated)

## Support

For issues, questions, or contributions, contact the development team.

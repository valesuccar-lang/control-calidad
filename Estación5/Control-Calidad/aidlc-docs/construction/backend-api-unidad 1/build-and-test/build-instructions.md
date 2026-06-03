# Build Instructions — Backend API (Python FastAPI)

**Date**: 2026-05-28  
**Unit**: Backend API (Python FastAPI)  
**Target Environment**: On-Premise Eliot Server + Local Development

---

## 🔨 LOCAL DEVELOPMENT BUILD

### **Prerequisites**
- Python 3.11+ installed
- PostgreSQL 13+ running locally (or Docker container)
- Git installed

### **Step 1: Clone Repository**
```bash
cd ~/projects
git clone <repository-url>
cd backend
```

### **Step 2: Create Virtual Environment**
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### **Step 3: Install Dependencies**
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### **Step 4: Configure Environment**
```bash
cp .env.example .env
# Edit .env with your local PostgreSQL credentials
```

**Example .env for local development:**
```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/textile_qc_dev
JWT_SECRET_KEY=dev-secret-key-change-in-production
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

### **Step 5: Initialize Database**
```bash
# Initialize Alembic (one-time)
alembic init migrations

# Create migration from SQLAlchemy models
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

### **Step 6: Verify Installation**
```bash
# Check Python version
python --version  # Should be 3.11+

# Check package imports
python -c "import fastapi, sqlalchemy, pydantic; print('All imports OK')"

# Check database connection
python -c "from app.database import init_db; print('Database configured')"
```

### **Step 7: Run Application (Development Mode)**
```bash
# With auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using main.py directly
python app/main.py
```

**Output should show:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### **Step 8: Test API is Running**
```bash
# In another terminal
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","environment":"development","database":"connected"}
```

---

## 🐳 DOCKER BUILD

### **Build Docker Image**
```bash
# Build with tag
docker build -t textile-qc-api:1.0.0 .
docker build -t textile-qc-api:latest .

# Verify image
docker images | grep textile-qc-api
```

### **Run Container Locally**
```bash
# With environment file
docker run -d \
  --name textile-qc-api \
  --env-file .env \
  -p 8000:8000 \
  -v $(pwd)/logs:/var/log/fastapi \
  textile-qc-api:latest

# Check logs
docker logs textile-qc-api
```

### **Push to Registry** (Production)
```bash
# Tag for registry
docker tag textile-qc-api:1.0.0 quay.io/patprimo/textile-qc-api:1.0.0
docker tag textile-qc-api:latest quay.io/patprimo/textile-qc-api:latest

# Login to registry
docker login quay.io

# Push images
docker push quay.io/patprimo/textile-qc-api:1.0.0
docker push quay.io/patprimo/textile-qc-api:latest
```

---

## ✔️ BUILD VERIFICATION CHECKLIST

- [ ] Python 3.11+ installed
- [ ] Virtual environment activated
- [ ] All dependencies installed (`pip list | grep fastapi`)
- [ ] .env file configured with DATABASE_URL
- [ ] Database migrations applied (`alembic current`)
- [ ] Application starts without errors
- [ ] `/health` endpoint responds 200 OK
- [ ] OpenAPI docs available at http://localhost:8000/docs
- [ ] Docker image builds successfully (if using Docker)

---

## 🚨 COMMON BUILD ISSUES

### **Issue: "Module not found: fastapi"**
```bash
# Solution: Verify virtual environment is activated
which python  # Should show path inside venv/
pip install -r requirements.txt
```

### **Issue: "database connection refused"**
```bash
# Solution: Check PostgreSQL is running
psql -U postgres -h localhost  # Should connect to PostgreSQL

# Or start with Docker
docker run -d \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:13
```

### **Issue: "Alembic table doesn't exist"**
```bash
# Solution: Create alembic_version table
alembic stamp head
alembic upgrade head
```

### **Issue: "Port 8000 already in use"**
```bash
# Solution: Use different port
uvicorn app.main:app --port 8001
```

---

## 📋 BUILD OUTPUTS

After successful build:

```
backend/
├── venv/                    # Virtual environment
├── app/                     # Application code (40+ Python files)
├── tests/                   # Test files
├── migrations/              # Alembic migration scripts
├── logs/                    # Application logs (runtime)
├── .env                     # Configuration (git-ignored)
└── __pycache__/             # Compiled Python (git-ignored)
```

**Key generated files:**
- `migrations/versions/001_initial_schema.py` — Initial database schema
- `logs/app.log` — JSON structured logs

---

**Status**: ✅ Build process defined  
**Next**: Run unit tests to verify build quality

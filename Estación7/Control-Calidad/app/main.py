"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger
from contextlib import asynccontextmanager

from app.config import settings
from app.lifespan import lifespan
from app.middleware.auth_middleware import AuthMiddleware
from app.routes import auth, inspections, approvals, masters, config as config_routes


# Exception handlers
async def validation_exception_handler(request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(
        "Validation error",
        path=request.url.path,
        errors=exc.errors()
    )
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )


async def general_exception_handler(request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        error=str(exc),
        exc_info=exc
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# FastAPI app
app = FastAPI(
    title="Textile Quality Control API",
    description="Backend API for textile inspection, approval, and quality management",
    version="1.0.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(AuthMiddleware)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.is_development else ["localhost", "127.0.0.1"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(inspections.router, prefix="/api/inspections", tags=["inspections"])
app.include_router(approvals.router, prefix="/api/approvals", tags=["approvals"])
app.include_router(masters.router, prefix="/api/masters", tags=["masters"])
app.include_router(config_routes.router, prefix="/api", tags=["config"])


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    from app.database import get_db_session
    try:
        async with get_db_session() as session:
            await session.execute("SELECT 1")
        return {
            "status": "healthy",
            "environment": settings.environment,
            "database": "connected"
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "environment": settings.environment,
            "database": "disconnected",
            "error": str(e)
        }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Textile Quality Control API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        workers=4 if settings.is_production else 1,
        reload=settings.is_development,
        log_level=settings.logging.level.lower()
    )

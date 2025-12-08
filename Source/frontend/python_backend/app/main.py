"""Main FastAPI application."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from .config import get_settings
from .database import wait_for_database, engine
from .routers import health, zones, assets, alerts, resources, risk, communications, plans, admin
# Temporarily disabled prediction routers for deployment
# from .routers import predict, rules

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup
    logger.info("Starting Flood Prediction API...")
    
    # Wait for database connection
    if not await wait_for_database():
        logger.error("Failed to connect to database. Exiting.")
        raise RuntimeError("Database connection failed")
    
    logger.info(f"Flood Prediction API running on port {settings.port}")
    logger.info(f"Environment: {'development' if settings.debug else 'production'}")
    logger.info(f"Database: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    logger.info(f"API Documentation: http://localhost:{settings.port}/docs")
    
    yield
    
    # Shutdown
    logger.info("Shutting down gracefully...")
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="PostgreSQL-backed REST API for Flood Prediction System",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "details": str(exc) if settings.debug else None
        }
    )


# Include routers
app.include_router(health.router)
app.include_router(zones.router)
app.include_router(assets.router)
app.include_router(alerts.router)
app.include_router(resources.router)
app.include_router(risk.router)
app.include_router(communications.router)
app.include_router(plans.router)
app.include_router(admin.router)
# Temporarily disabled prediction routers for deployment
# app.include_router(predict.router)
# app.include_router(rules.router)


# 404 handler
@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(path_name: str):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found"}
    )

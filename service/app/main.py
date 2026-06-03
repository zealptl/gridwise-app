"""GridWise FastAPI Application Entry Point"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import close_mongo_connection, connect_to_mongo
from app.routers import constructors, drivers, rules, teams
from app.routers import agent as agent_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup: Connect to MongoDB
    await connect_to_mongo()

    # Startup: Verify AgentCore Gateway connectivity (non-fatal)
    try:
        from app.agent.gateway import AgentCoreGateway

        gw = AgentCoreGateway()
        if not gw.verify_gateway_connection():
            logger.warning("AgentCore Gateway not reachable at startup")
    except Exception as exc:
        logger.warning("Could not verify AgentCore Gateway: %s", exc)

    yield
    # Shutdown: Close MongoDB connection
    await close_mongo_connection()


# Create FastAPI app instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    redirect_slashes=False,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(drivers.router, prefix=settings.API_V1_PREFIX)
app.include_router(constructors.router, prefix=settings.API_V1_PREFIX)
app.include_router(rules.router, prefix=settings.API_V1_PREFIX)
app.include_router(teams.router, prefix=settings.API_V1_PREFIX)
app.include_router(agent_router.router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": settings.VERSION}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "GridWise API",
        "version": settings.VERSION,
        "docs": "/docs",
    }

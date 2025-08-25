"""
Main FastAPI application for logWise Docker extension backend.
Handles container log ingestion, vector storage, and RAG querying.
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from math import log

from app.api import containers, logs, query
from app.ingestion.watcher import DockerWatcher
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🚀 Starting logWise Backend...")
    app.state.docker_watcher = DockerWatcher()
    
    try:
        # Start the Docker watcher
        await app.state.docker_watcher.start()
        logger.info("✅ Docker watcher started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start Docker watcher: {str(e)}")
        # Continue anyway - the app can still work without the watcher
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down logWise Backend...")
    if hasattr(app.state, 'docker_watcher'):
        try:
            await app.state.docker_watcher.stop()
            logger.info("✅ Docker watcher stopped successfully")
        except Exception as e:
            logger.error(f"❌ Error stopping Docker watcher: {str(e)}")


app = FastAPI(
    title="logWise Backend",
    description="Docker Container Log Analysis.",
    version="0.0.1",
    # lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(containers.router, tags=["containers"])
# app.include_router(logs.router, tags=["logs"])
app.include_router(query.router, tags=["query"])

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "logWise Backend is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check."""
    watcher_status = "running" if hasattr(app.state, 'docker_watcher') else "stopped"
    
    return {
        "status": "healthy",
        "services": {
            "docker_watcher": watcher_status
        },
        "endpoints": {
            "docs": "/docs",
            "containers": "/api/containers",
            # "logs": "/api/logs",
            "query": "/api/logs/query"
        }
    } 


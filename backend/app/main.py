from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, APIRouter
from app.core.config import settings
from app.core.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager that handles FastAPI startup and shutdown procedures.
    """
    logger.info("Starting up ProposalPilot AI...")
    logger.info(f"App Version: {settings.APP_VERSION}")
    logger.info(f"App Environment: {settings.APP_ENV}")
    logger.info(f"Debug Mode: {settings.DEBUG}")

    # Validate critical environment settings
    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY is not configured! LLM services will fail.")
    else:
        logger.info("GROQ_API_KEY is configured.")

    # Ensure output directory exists
    output_path = Path(settings.OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Verified output directory exists at: {output_path.resolve()}")

    logger.info("ProposalPilot AI initialized successfully and ready to accept requests.")
    
    yield

    # Shutdown sequence
    logger.info("Shutting down ProposalPilot AI...")
    logger.info("ProposalPilot AI cleanup complete.")

# Initialize the FastAPI app with configurations
app = FastAPI(
    title=settings.APP_NAME,
    description="Autonomous AI-Powered Proposal Generation Platform Backend",
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Define temporary health check router (will be refactored to health api in Module 4)
health_router = APIRouter()

@health_router.get("/health", tags=["Health"])
async def health_check():
    """
    Service health check endpoint.
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV
    }

# Register routers
app.include_router(health_router)

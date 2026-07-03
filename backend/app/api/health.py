from datetime import datetime, timezone
from fastapi import APIRouter, Request, HTTPException, status
from app.core.config import settings
from app.core.logger import logger
from app.schemas.response import HealthResponse

router = APIRouter()

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["Health"],
    summary="Get application health status"
)
async def get_health(request: Request):
    """
    Get the health status, metadata, and uptime of the ProposalPilot AI application.
    """
    logger.info("Health endpoint invoked.")
    try:
        # Retrieve startup time from app state (default to current time if not set)
        startup_time = getattr(request.app.state, "startup_time", None)
        
        if startup_time:
            uptime_delta = datetime.now(timezone.utc) - startup_time
            days = uptime_delta.days
            hours, remainder = divmod(uptime_delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"
        else:
            uptime_str = "Uptime unavailable (startup time not recorded)"
            
        current_time_str = datetime.now(timezone.utc).isoformat()
        
        response_data = HealthResponse(
            status="healthy",
            service=settings.APP_NAME,
            version=settings.APP_VERSION,
            environment=settings.APP_ENV,
            timestamp=current_time_str,
            uptime=uptime_str,
            message="Application is running successfully."
        )
        
        logger.info("Successful health check response returned.")
        return response_data
        
    except Exception as e:
        logger.exception(f"Unexpected error in health check: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error checking system health"
        )

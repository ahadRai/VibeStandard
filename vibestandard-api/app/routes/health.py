from fastapi import APIRouter, Request
from app.models.responses import HealthResponse
from app.config import settings

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        active_scans=request.app.state.scanner.active_scan_count,
        queued_scans=request.app.state.scanner.queued_scan_count,
    )

from fastapi import APIRouter, Request
from app.models.requests import ScanRequest
from app.models.responses import ScanRequestResponse, JobStatusResponse, JobStatus
from app.exceptions import JobNotFoundException

router = APIRouter(prefix="/api", tags=["scan"])


@router.post("/scan", response_model=ScanRequestResponse, status_code=202)
async def submit_scan(request: Request, body: ScanRequest):
    # 1. Get scanner from request.app.state.scanner
    scanner = request.app.state.scanner
    
    # 2. Call scanner.submit_scan(body.github_url)
    job = scanner.submit_scan(body.github_url)
    
    # 3. Return ScanRequestResponse
    return ScanRequestResponse(
        job_id=job.job_id,
        status=JobStatus.QUEUED,
        message="Scan queued. Poll /api/scan/{job_id}/status for updates.",
        estimated_duration_seconds=60,
    )


@router.get("/scan/{job_id}/status", response_model=JobStatusResponse)
async def get_scan_status(job_id: str, request: Request):
    # 1. Get scanner from request.app.state.scanner
    scanner = request.app.state.scanner
    
    # 2. Call scanner.get_job(job_id)
    job = scanner.get_job(job_id)
    
    # 3. If None: raise JobNotFoundException(job_id)
    if job is None:
        raise JobNotFoundException(job_id)
    
    # 4. Return JobStatusResponse built from the job
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        github_url=job.github_url,
        created_at=job.created_at,
        updated_at=job.updated_at,
        progress_message=job.progress_message,
        result=job.result,
        error=job.error,
    )

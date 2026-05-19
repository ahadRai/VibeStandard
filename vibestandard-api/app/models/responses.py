from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "queued"
    CLONING = "cloning"
    SCANNING = "scanning"
    COMPLETE = "complete"
    FAILED = "failed"


class ScanRequestResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str
    estimated_duration_seconds: int = 60


class FindingResponse(BaseModel):
    rule_id: str
    name: str
    severity: str
    message: str
    fix: str
    file: str
    line: Optional[int]
    analyzer: str
    ecosystem: str


class ScanResultResponse(BaseModel):
    score: int
    raw_score: int
    grade: str
    vibe_label: str
    scanned_path: str
    ecosystems: List[str]
    total_files: int
    skipped_files: int
    duration_seconds: float
    deduplicated_count: int
    summary: dict
    analyzer_breakdown: dict
    adjustments_applied: List[dict]
    findings: List[FindingResponse]
    analyzer_errors: List[str]


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    github_url: str
    created_at: str
    updated_at: str
    progress_message: str
    result: Optional[ScanResultResponse] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    active_scans: int
    queued_scans: int

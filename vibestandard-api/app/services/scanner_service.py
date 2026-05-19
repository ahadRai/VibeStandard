import uuid
import threading
import time
import shutil
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from app.config import settings
from app.models.responses import JobStatus, ScanResultResponse, FindingResponse
from app.services.github_service import GitHubService

logger = logging.getLogger(__name__)


class Job:
    def __init__(self, job_id: str, github_url: str):
        self.job_id = job_id
        self.github_url = github_url
        self.status = JobStatus.QUEUED
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
        self.progress_message = "Scan queued"
        self.result: Optional[ScanResultResponse] = None
        self.error: Optional[str] = None
        self.clone_path: Optional[Path] = None


class ScannerService:
    def __init__(self, settings):
        self._jobs: dict[str, Job] = {}  # in-memory job store
        self._jobs_lock = threading.Lock()  # thread-safe access
        self._executor = ThreadPoolExecutor(
            max_workers=settings.max_concurrent_scans
        )
        self._settings = settings
        self._github_service = GitHubService()
        # Start background cleanup thread
        self._start_cleanup_worker()

    def submit_scan(self, github_url: str) -> Job:
        # 1. Create a new Job with status=QUEUED
        job_id = str(uuid.uuid4())
        job = Job(job_id, github_url)
        
        # 2. Store it in self._jobs under its job_id
        with self._jobs_lock:
            self._jobs[job_id] = job
        
        # 3. Submit _run_scan(job) to the ThreadPoolExecutor
        self._executor.submit(self._run_scan, job)
        
        # 4. Return the job immediately (non-blocking)
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        # Thread-safe lookup of job by ID
        with self._jobs_lock:
            return self._jobs.get(job_id)

    def _run_scan(self, job: Job) -> None:
        """This runs in a background thread."""
        try:
            # Step 1: Update status to CLONING
            self._update_job(job, status=JobStatus.CLONING, progress_message="Cloning repository...")
            
            # Step 2: Clone the repository
            try:
                clone_path = self._github_service.clone_repo(job.github_url)
                job.clone_path = clone_path
            except Exception as e:
                self._update_job(job, status=JobStatus.FAILED, error=str(e))
                return
            
            # Step 3: Update status to SCANNING
            self._update_job(job, status=JobStatus.SCANNING, progress_message="Running analyzers...")
            
            # Step 4: Execute VibeStandard scan
            try:
                scan_result = self._execute_vibestandard_scan(clone_path)
            except Exception as e:
                self._update_job(job, status=JobStatus.FAILED, error=str(e))
                self._cleanup_clone(clone_path)
                return
            
            # Step 5: Convert ScanResult to ScanResultResponse
            result_response = self._convert_to_response(scan_result)
            
            # Step 6: Update status to COMPLETE
            self._update_job(
                job,
                status=JobStatus.COMPLETE,
                result=result_response,
                progress_message="Scan complete"
            )
            
            # Step 7: Cleanup clone directory
            self._cleanup_clone(clone_path)
            
        except Exception as e:
            # Never let an exception escape the thread
            logger.error(f"Scan failed for job {job.job_id}: {str(e)}")
            self._update_job(job, status=JobStatus.FAILED, error=str(e))
            if job.clone_path:
                self._cleanup_clone(job.clone_path)

    def _execute_vibestandard_scan(self, clone_path: Path):
        """Import and call VibeStandard core directly (not as subprocess)."""
        from vibestandard.ingestion.file_tree import build_file_tree, detect_ecosystems
        from vibestandard.analyzers.dependency import DependencyAnalyzer
        from vibestandard.analyzers.config import ConfigAnalyzer
        from vibestandard.analyzers.security import SecurityAnalyzer
        from vibestandard.analyzers.infra import InfraAnalyzer
        from vibestandard.analyzers.observability import ObservabilityAnalyzer
        from vibestandard.engine.scorer import ScoringEngine
        from vibestandard.analyzers.rules_loader import load_all_rules
        import concurrent.futures
        
        start = time.time()
        rules = load_all_rules()
        files = build_file_tree(clone_path)
        ecosystems = detect_ecosystems(files)
        
        analyzers = [
            DependencyAnalyzer(clone_path, files, rules, ecosystems=ecosystems),
            ConfigAnalyzer(clone_path, files, rules, ecosystems=ecosystems),
            SecurityAnalyzer(clone_path, files, rules, ecosystems=ecosystems),
            InfraAnalyzer(clone_path, files, rules, ecosystems=ecosystems),
            ObservabilityAnalyzer(clone_path, files, rules, ecosystems=ecosystems),
        ]
        
        all_findings = []
        analyzer_errors = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(a.analyze): a.name for a in analyzers}
            for future in concurrent.futures.as_completed(futures):
                try:
                    all_findings.extend(future.result())
                except Exception as e:
                    analyzer_errors.append(f"{futures[future]}: {str(e)}")
        
        metadata = {
            "scanned_path": str(clone_path),
            "ecosystems": ecosystems,
            "total_files": len(files),
            "duration_seconds": time.time() - start,
            "skipped_files": 0,
            "analyzer_errors": analyzer_errors
        }
        
        engine = ScoringEngine()
        return engine.score(all_findings, metadata)

    def _convert_to_response(self, scan_result) -> ScanResultResponse:
        """Convert ScanResult dataclass to ScanResultResponse Pydantic model."""
        findings_response = [
            FindingResponse(
                rule_id=f.rule_id,
                name=f.name,
                severity=f.severity,
                message=f.message,
                fix=f.fix,
                file=f.file,
                line=f.line,
                analyzer=f.analyzer,
                ecosystem=f.ecosystem,
            )
            for f in scan_result.findings
        ]
        
        return ScanResultResponse(
            score=scan_result.score,
            raw_score=scan_result.raw_score,
            grade=scan_result.grade,
            vibe_label=scan_result.vibe_label,
            scanned_path=scan_result.scanned_path,
            ecosystems=scan_result.ecosystems,
            total_files=scan_result.total_files,
            skipped_files=scan_result.skipped_files,
            duration_seconds=scan_result.duration_seconds,
            deduplicated_count=scan_result.deduplicated_count,
            summary=scan_result.summary,
            analyzer_breakdown=scan_result.analyzer_breakdown,
            adjustments_applied=scan_result.adjustments_applied,
            findings=findings_response,
            analyzer_errors=scan_result.analyzer_errors,
        )

    def _cleanup_clone(self, path: Path) -> None:
        """Safely delete the cloned repo directory."""
        try:
            if path and path.exists():
                shutil.rmtree(path, ignore_errors=True)
                logger.info(f"Cleaned up clone directory: {path}")
        except Exception as e:
            logger.error(f"Failed to cleanup clone directory {path}: {str(e)}")

    def _update_job(self, job: Job, **kwargs) -> None:
        """Thread-safe job update."""
        with self._jobs_lock:
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            job.updated_at = datetime.utcnow().isoformat()

    def _start_cleanup_worker(self) -> None:
        """Start a daemon thread that cleans up old jobs."""
        def cleanup_loop():
            while True:
                time.sleep(60)  # Run every 60 seconds
                try:
                    cutoff_time = datetime.utcnow().timestamp() - self._settings.job_ttl_seconds
                    
                    with self._jobs_lock:
                        expired_jobs = [
                            job_id for job_id, job in self._jobs.items()
                            if datetime.fromisoformat(job.updated_at).timestamp() < cutoff_time
                        ]
                        
                        for job_id in expired_jobs:
                            job = self._jobs[job_id]
                            if job.clone_path:
                                self._cleanup_clone(job.clone_path)
                            del self._jobs[job_id]
                            
                            if expired_jobs:
                                logger.info(f"Cleaned up {len(expired_jobs)} expired jobs")
                                
                except Exception as e:
                    logger.error(f"Cleanup worker error: {str(e)}")
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()

    @property
    def active_scan_count(self) -> int:
        with self._jobs_lock:
            return sum(1 for j in self._jobs.values()
                      if j.status in (JobStatus.CLONING, JobStatus.SCANNING))

    @property
    def queued_scan_count(self) -> int:
        with self._jobs_lock:
            return sum(1 for j in self._jobs.values()
                      if j.status == JobStatus.QUEUED)

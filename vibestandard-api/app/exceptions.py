from fastapi import Request
from fastapi.responses import JSONResponse


class VibeStandardException(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code


class RepoNotFoundException(VibeStandardException):
    def __init__(self, url: str):
        super().__init__(f"Repository not found: {url}", 404)


class RepoPrivateException(VibeStandardException):
    def __init__(self):
        super().__init__("Repository is private. Only public repositories can be scanned.", 403)


class RepoTooLargeException(VibeStandardException):
    def __init__(self, size_mb: int, limit_mb: int):
        super().__init__(f"Repository is too large ({size_mb}MB). Maximum allowed size is {limit_mb}MB.", 413)


class CloneTimeoutException(VibeStandardException):
    def __init__(self):
        super().__init__("Repository clone timed out after 120 seconds.", 504)


class CloneFailedException(VibeStandardException):
    def __init__(self, reason: str):
        super().__init__(f"Failed to clone repository: {reason}", 500)


class JobNotFoundException(VibeStandardException):
    def __init__(self, job_id: str):
        super().__init__(f"Scan job not found: {job_id}", 404)


class RateLimitException(VibeStandardException):
    def __init__(self):
        super().__init__("Rate limit exceeded. Maximum 10 scans per minute per IP.", 429)


def register_exception_handlers(app):
    """Register all custom exception handlers with the FastAPI app."""
    
    @app.exception_handler(VibeStandardException)
    async def vibestandard_exception_handler(request: Request, exc: VibeStandardException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message, "status_code": exc.status_code}
        )

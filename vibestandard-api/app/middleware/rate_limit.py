import time
import threading
from collections import defaultdict
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int, window_seconds: int):
        super().__init__(app)
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()
        self._max_requests = max_requests
        self._window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        # Only rate limit POST /api/scan
        if request.url.path == "/api/scan" and request.method == "POST":
            ip = request.client.host
            now = time.time()
            with self._lock:
                # Remove timestamps outside the window
                self._requests[ip] = [
                    t for t in self._requests[ip]
                    if now - t < self._window_seconds
                ]
                if len(self._requests[ip]) >= self._max_requests:
                    from app.exceptions import RateLimitException
                    raise RateLimitException()
                self._requests[ip].append(now)
        return await call_next(request)

from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.config import settings
from app.middleware.cors import add_cors_middleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.exceptions import register_exception_handlers
from app.routes import scan, health
from pathlib import Path


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.scanner_service import ScannerService
    
    # Startup: initialise ScannerService, create clone_dir
    app.state.scanner = ScannerService(settings)
    Path(settings.clone_dir).mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Shutdown: shutdown the ThreadPoolExecutor gracefully
    app.state.scanner._executor.shutdown(wait=False)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

add_cors_middleware(app, settings)
app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds
)
register_exception_handlers(app)
app.include_router(scan.router)
app.include_router(health.router)

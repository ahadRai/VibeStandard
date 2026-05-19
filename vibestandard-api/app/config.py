from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API
    app_name: str = "VibeStandard API"
    app_version: str = "0.1.0"
    debug: bool = False

    # CORS — comma-separated list of allowed origins
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Rate limiting
    rate_limit_requests: int = 10        # max requests
    rate_limit_window_seconds: int = 60  # per this many seconds

    # Scanning
    max_repo_size_mb: int = 100          # reject repos larger than this
    scan_timeout_seconds: int = 300      # kill scan after 5 minutes
    max_concurrent_scans: int = 5        # max parallel scans
    clone_dir: str = "/tmp/vibestandard-clones"  # where repos are cloned
    cleanup_after_seconds: int = 3600    # delete clone after 1 hour

    # Job storage
    job_ttl_seconds: int = 7200          # keep job results for 2 hours

    class Config:
        env_file = ".env"


settings = Settings()

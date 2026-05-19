# VibeStandard

**Production readiness auditor for AI-generated code.** Scan your GitHub repository for 90+ production issues including databases, secrets, security, infrastructure, and observability.

## Prerequisites

- Docker Desktop
- Docker Compose v2
- Git

## Quick Start (One Command)

```bash
git clone https://github.com/ahadRai/VibeStandard.git
cd VibeStandard
cp .env.example .env
docker compose up --build
```

Then open **http://localhost:3000** in your browser.

## Development Mode (With Hot Reload)

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

- API available at **http://localhost:8000/api/docs** (Swagger UI)
- Frontend available at **http://localhost:5173**

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/scan` | Submit a GitHub URL for scanning |
| GET | `/api/scan/{job_id}/status` | Poll for scan status and result |
| GET | `/api/health` | Health check |
| GET | `/api/docs` | Swagger UI |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated list of allowed origins |
| `MAX_CONCURRENT_SCANS` | `5` | Maximum parallel scans |
| `MAX_REPO_SIZE_MB` | `100` | Maximum repository size in MB |
| `SCAN_TIMEOUT_SECONDS` | `300` | Kill scan after this many seconds |
| `JOB_TTL_SECONDS` | `7200` | Keep job results for this many seconds |
| `CLONE_DIR` | `/tmp/vibestandard-clones` | Where repos are cloned |
| `RATE_LIMIT_REQUESTS` | `10` | Max requests per window |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate limit window in seconds |
| `VITE_API_URL` | `http://localhost:8000` | Frontend API URL |

## Architecture

```
Browser
  ↓ http://localhost:3000
[nginx] → React App
  ↓ http://localhost:8000/api
[uvicorn] → FastAPI
  ↓ imports directly
[VibeStandard Core]
  ↓ git clone
[GitHub]
```

## How It Works

1. User opens http://localhost:3000 and pastes a GitHub repo URL
2. React calls `POST http://localhost:8000/api/scan`
3. FastAPI validates the URL, creates a job, starts the scan in background, returns `job_id`
4. React polls `GET http://localhost:8000/api/scan/{job_id}/status` every 2 seconds
5. Status progresses: `queued` → `cloning` → `scanning` → `complete` or `failed`
6. When complete, React renders the results — score, grade, vibe_label, findings grouped by severity

## Limitations

- Only public GitHub repositories can be scanned
- Maximum repository size: 100MB
- Scan results are stored in memory and lost on container restart
- Maximum 10 scans per minute per IP address
- No domain yet — runs on localhost only

## Project Structure

```
vibestandard-analyzers/          # Python CLI core (unchanged)
    vibestandard/
    rules/
    tests/

vibestandard-api/                # FastAPI wrapper (NEW)
    app/
        main.py                  # FastAPI entry point
        routes/                  # API endpoints
        services/                # Business logic
        models/                  # Pydantic models
        middleware/              # CORS, rate limiting
        config.py                # Settings
        exceptions.py            # Custom exceptions

vibestandard-frontend/
    vibestandard-web/            # React frontend
        src/
            api/                 # API client
            hooks/               # React hooks
            components/          # UI components
            pages/               # Page components

docker-compose.yml               # Production-like local setup
docker-compose.dev.yml           # Development overrides
```

## License

MIT License — see [LICENSE](vibestandard-analyzers/LICENSE)

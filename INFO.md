# VibeStandard — Full Project Reference (AI Onboarding Doc)

> **Purpose of this file:** This is a private reference document (gitignored) meant to be read by any AI or developer picking up this project. It contains everything needed to understand, modify, and extend the codebase without having to re-explore it.

---

## 1. What This Project Is

VibeStandard is a **production-readiness auditor for AI-generated (vibe-coded) codebases**. Users paste a public GitHub URL into a web UI → the backend clones the repo → runs 5 static analysis engines → computes a 0–100 score with a letter grade → returns a detailed report with actionable fix suggestions.

**Three sub-projects in a monorepo:**

| Sub-project | Path | Stack | Role |
|---|---|---|---|
| **Analyzers** | `vibestandard-analyzers/` | Python 3.13, Typer, Rich, PyYAML, GitPython, Jinja2, pathspec | CLI core — 5 analyzers, scoring engine, reporters, YAML rules |
| **API** | `vibestandard-api/` | FastAPI, Uvicorn, Pydantic v2, pydantic-settings, httpx | REST API wrapper around the CLI core |
| **Frontend** | `vibestandard-frontend/vibestandard-web/` | React 19, Vite 8, Tailwind CSS 3, Framer Motion, React Router v7 | Web UI — submit scans + view results |

---

## 2. Architecture & Data Flow

```
Browser (React on :3000 prod / :5173 dev)
    ↓ POST /api/scan { github_url }
    ↓ GET  /api/scan/{job_id}/status (polled every 2s)
nginx (:3000 prod) / Vite dev server (:5173 dev)
    ↓
FastAPI (uvicorn :8000)
    ↓ ScannerService.submit_scan() → ThreadPoolExecutor
    ↓ GitHubService.clone_repo()    → git clone --depth=1
    ↓ _execute_vibestandard_scan()  → imports analyzer core directly
    ↓
VibeStandard Core (Python library)
    1. ingest()         → resolve source to local Path
    2. build_file_tree() → walk directory, filter binaries/gitignored
    3. detect_ecosystems() → java/python/node/go/docker
    4. load_all_rules()  → parse YAML rule files
    5. Run 5 analyzers   → each returns list[Finding]
    6. ScoringEngine.score() → deduplicate, score, grade, enrich
    7. Reporter.render() → terminal/JSON/HTML output
```

### Job Lifecycle (API)
```
POST /api/scan → creates Job → status=QUEUED
                  ThreadPool picks up → status=CLONING
                  clone completes      → status=SCANNING
                  scan completes       → status=COMPLETE + ScanResultResponse attached
                  any error            → status=FAILED + error message
Frontend polls GET /api/scan/{job_id}/status every 2 seconds until COMPLETE or FAILED
```

---

## 3. Complete File Map

### 3.1 vibestandard-analyzers/ (CLI Core)

```
vibestandard-analyzers/
├── main.py                              # Entry point: `python main.py scan <source>`
├── pyproject.toml                       # Package config, deps, CLI entry point
├── LICENSE                              # MIT
├── README.md                            # Detailed README with usage examples
├── vibestandard/
│   ├── __init__.py                      # Exports __version__ = "0.1.0"
│   ├── cli.py                           # Typer CLI: scan, version, rules list, rules add
│   ├── models.py                        # Finding + ScanResult dataclasses
│   ├── analyzers/
│   │   ├── base.py                      # BaseAnalyzer ABC (analyze, add_finding, read_file_safe)
│   │   ├── dependency.py                # DependencyAnalyzer — Java/Node/Python dep checks
│   │   ├── config.py                    # ConfigAnalyzer — debug mode, test DBs, hardcoded secrets
│   │   ├── security.py                  # SecurityAnalyzer — 10 rules + Semgrep integration
│   │   ├── infra.py                     # InfraAnalyzer — 12 rules for Docker/Compose/K8s/CI
│   │   ├── observability.py             # ObservabilityAnalyzer — 9 rules for logging/monitoring
│   │   ├── rules_loader.py              # YAML loader: load_all_rules(), get_rules_for_analyzer()
│   │   └── ecosystem_fixes.py           # Ecosystem-aware fix messages for observability
│   ├── engine/
│   │   ├── __init__.py                  # Exports ScoringEngine
│   │   ├── scorer.py                    # ScoringEngine — dedup, score, grade, vibe_label, enrich
│   │   └── rules_loader.py             # (Appears to be duplicate/stale — engine/__init__ uses scorer)
│   ├── ingestion/
│   │   ├── loader.py                    # ingest() — resolves local path / GitHub URL / ZIP → Path
│   │   └── file_tree.py                 # build_file_tree(), detect_ecosystems()
│   └── reporters/
│       ├── __init__.py                  # Exports TerminalReporter, JsonReporter, HtmlReporter
│       ├── base.py                      # BaseReporter ABC (render, _filter_findings, _write_output)
│       ├── cli_reporter.py              # TerminalReporter — Rich-formatted terminal output
│       ├── json_reporter.py             # JsonReporter — machine-readable JSON
│       ├── html_reporter.py             # HtmlReporter — Jinja2 template rendering
│       └── templates/
│           └── report.html              # HTML report Jinja2 template
├── rules/                               # YAML rule definitions
│   ├── java.yaml                        # Java ecosystem rules
│   ├── python.yaml                      # Python ecosystem rules
│   ├── node.yaml                        # Node.js ecosystem rules
│   └── docker.yaml                      # Docker ecosystem rules
└── tests/
    ├── __init__.py
    ├── test_analyzers.py                # Analyzer tests
    ├── test_reporters.py                # Reporter tests
    ├── test_scorer.py                   # Scoring engine tests
    └── fixtures/                        # Test fixture files
```

### 3.2 vibestandard-api/ (FastAPI Backend)

```
vibestandard-api/
├── Dockerfile                           # Production: python:3.13-slim, installs semgrep, analyzer pkg
├── requirements.txt                     # fastapi, uvicorn, pydantic, pydantic-settings, gitpython, httpx
├── .env.example                         # VITE_API_URL default
└── app/
    ├── __init__.py
    ├── main.py                          # FastAPI app factory, lifespan, middleware registration
    ├── config.py                        # Settings (pydantic-settings): CORS, rate limits, scan params
    ├── exceptions.py                    # VibeStandardException hierarchy + exception handler registration
    ├── middleware/
    │   ├── __init__.py
    │   ├── cors.py                      # add_cors_middleware() — parses comma-separated origins
    │   └── rate_limit.py                # RateLimitMiddleware — per-IP sliding window rate limiter
    ├── models/
    │   ├── __init__.py
    │   ├── requests.py                  # ScanRequest (github_url with validator)
    │   └── responses.py                 # JobStatus enum, ScanRequestResponse, FindingResponse,
    │                                    #   ScanResultResponse, JobStatusResponse, HealthResponse
    ├── routes/
    │   ├── __init__.py
    │   ├── scan.py                      # POST /api/scan, GET /api/scan/{job_id}/status
    │   └── health.py                    # GET /api/health
    └── services/
        ├── __init__.py
        ├── scanner_service.py           # ScannerService — job management, ThreadPoolExecutor,
        │                                #   imports & calls vibestandard core directly
        └── github_service.py            # GitHubService — clone_repo (shallow clone, size check)
```

### 3.3 vibestandard-frontend/vibestandard-web/ (React Frontend)

```
vibestandard-web/
├── Dockerfile                           # Production: node build → nginx
├── Dockerfile.dev                       # Dev: node + vite dev server
├── nginx.conf                           # Serves built React app, proxies /api to backend
├── package.json                         # React 19, Vite 8, Tailwind 3, Framer Motion
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── index.html
├── public/
│   └── ...                              # Static assets
└── src/
    ├── main.jsx                         # React DOM entry point
    ├── App.jsx                          # BrowserRouter: /, /docs, /about
    ├── App.css
    ├── index.css                        # Tailwind directives + base styles
    ├── api/
    │   └── client.js (or similar)       # API client for /api/scan endpoints
    ├── hooks/
    │   └── useScan.js (or similar)      # Custom hook for scan submission + polling
    ├── context/
    │   └── ThemeContext.jsx             # Theme provider (dark mode)
    ├── components/
    │   ├── home/
    │   │   ├── AnimatedBackground.jsx   # Particle/grid animation
    │   │   ├── FeatureCards.jsx         # Feature highlight cards
    │   │   ├── HeroSection.jsx          # Main hero with title + description
    │   │   ├── HowItWorks.jsx           # Step-by-step explanation
    │   │   └── SearchBar.jsx            # GitHub URL input + submit + polling logic
    │   ├── layout/
    │   │   ├── Navbar.jsx               # Navigation bar
    │   │   └── Footer.jsx               # Footer
    │   ├── results/
    │   │   └── ResultsPanel.jsx (etc)   # Scan results display
    │   └── ui/
    │       └── ...                      # Reusable UI components
    ├── pages/
    │   ├── HomePage.jsx                 # Composes home components
    │   ├── DocsPage.jsx                 # API documentation page
    │   └── AboutPage.jsx                # About page
    └── styles/
        └── ...                          # Additional stylesheets
```

---

## 4. Key Classes & Interfaces

### 4.1 Data Models (`vibestandard-analyzers/vibestandard/models.py`)

```python
@dataclass
class Finding:
    rule_id: str        # e.g. "h2-database"
    name: str           # Human readable name
    severity: str       # "critical" | "high" | "medium" | "low"
    message: str        # Full explanation
    why_it_matters: str
    fix: str            # Concrete suggested fix
    file: str           # Relative path to file
    line: int | None
    analyzer: str       # "dependency" | "config" | "security" | "infra" | "observability"
    ecosystem: str      # "java" | "node" | "python" | "docker" | "generic"

@dataclass
class ScanResult:
    score: int              # 0–100
    grade: str              # "A" | "B" | "C" | "D" | "F"
    vibe_label: str         # "PRODUCTION_READY" | "STAGING_READY" | "TEST_GRADE"
    scanned_path: str
    ecosystems: list[str]
    total_files: int
    skipped_files: int
    duration_seconds: float
    findings: list[Finding]
    summary: dict           # {"critical": N, "high": N, "medium": N, "low": N}
    analyzer_breakdown: dict
    category_breakdown: dict
    enrichment: dict        # Maps str(id(finding)) → {"severity_rank": int, "display_color": str}
    analyzer_errors: list[str]
    deduplicated_count: int
    raw_score: int
    final_score: int
    adjustments_applied: list[dict]  # [{"reason": str, "delta": int}, ...]
```

### 4.2 BaseAnalyzer (`vibestandard-analyzers/vibestandard/analyzers/base.py`)

```python
class BaseAnalyzer(ABC):
    name: str       # Set by each subclass: "dependency", "config", etc.
    ecosystem: str  # Set by each subclass: "generic", "docker", etc.

    def __init__(self, root: Path, file_tree: list[Path], rules: dict,
                 options: dict | None = None, ecosystems: list[str] | None = None):
        self.root = root              # Absolute path to scanned project
        self.file_tree = file_tree    # List of relative Paths
        self.rules = rules            # Dict of rule_id → rule_dict (from YAML)
        self.findings: list[Finding] = []
        self.options = options or {}
        self.ecosystems = ecosystems or []

    @abstractmethod
    def analyze(self) -> list[Finding]: ...

    def add_finding(self, rule_id: str, file: str, line: int | None = None) -> None:
        # Looks up rule by rule_id in self.rules, creates Finding, appends to self.findings

    def read_file_safe(self, path: Path) -> str | None:
        # Never raises — returns None on encoding/permission errors
```

**Convention:** Analyzers that use YAML rules call `self.add_finding(rule_id, file)`. Analyzers with hardcoded rules (security, infra, observability) have their own `add_security_finding()` / `_add_infra_finding()` / `_add_obs_finding()` methods that create Findings directly from inline dicts.

### 4.3 Concrete Analyzers

| Analyzer | Rules Source | Rule Count | Key Methods |
|---|---|---|---|
| `DependencyAnalyzer` | YAML (`rules/*.yaml`) | ~20+ | `_check_java_dependencies`, `_check_node_dependencies`, `_check_python_dependencies` |
| `ConfigAnalyzer` | YAML (`rules/*.yaml`) | ~15+ | `_apply_config_rules`, `_apply_rules_for_ecosystem`, `_apply_rule_to_file` |
| `SecurityAnalyzer` | **Hardcoded** (`SECURITY_RULES` dict) | 10 + Semgrep | `_check_sql_injection`, `_check_eval_on_input`, `_check_ssl_verify_disabled`, `_check_csrf_disabled`, `_check_password_not_hashed`, `_check_jwt_hardcoded_secret`, `_check_pickle_untrusted_data`, `_check_open_redirect`, `_check_unrestricted_file_upload`, `_check_missing_auth_on_sensitive_route`, `_run_semgrep`, `_deduplicate` |
| `InfraAnalyzer` | **Hardcoded** (`INFRA_RULES` dict) | 12 | `_check_docker_run_as_root`, `_check_no_healthcheck`, `_check_latest_image_tag`, `_check_db_no_volume`, `_check_no_restart_policy`, `_check_no_resource_limits`, `_check_secrets_as_env_vars`, `_check_missing_dockerignore`, `_check_no_multi_stage_build`, `_check_compose_only_no_k8s`, `_check_no_ci_pipeline`, `_check_port_bound_to_all_interfaces` |
| `ObservabilityAnalyzer` | **Hardcoded** (`OBS_RULES` dict) | 9 | `_check_no_structured_logging`, `_check_no_error_tracking`, `_check_no_health_endpoint`, `_check_no_request_id_middleware`, `_check_log_rotation_not_configured`, `_check_debug_logging_in_production`, `_check_no_metrics_endpoint`, `_check_no_graceful_shutdown`, `_check_no_dependency_monitoring` |

### 4.4 ScoringEngine (`vibestandard-analyzers/vibestandard/engine/scorer.py`)

Pipeline: `score(findings, metadata) → ScanResult`

1. **Deduplicate** — key=(rule_id, file, line), keep longer message
2. **Base score** — start at 100, deduct: critical=−30, high=−15, medium=−7, low=−3. Diminishing returns after 3 findings of same severity (half deduction).
3. **Context adjustments** — bonuses/penalties (±5 to ±15) for: no critical findings, small project bonus, large project penalty, analyzer errors, etc.
4. **Grade** — A(90+), B(75–89), C(55–74), D(30–54), F(0–29)
5. **Vibe label** — PRODUCTION_READY(score≥90 + 0 critical/high + 0 errors), STAGING_READY(score≥55 + 0 critical + ≤1 error), TEST_GRADE(everything else)
6. **Enrich** — attach severity_rank and display_color to each finding
7. **Assemble** ScanResult

### 4.5 API Models (`vibestandard-api/app/models/`)

```python
# requests.py
class ScanRequest(BaseModel):
    github_url: str  # Validated: must match https://github.com/owner/repo pattern

# responses.py
class JobStatus(str, Enum):
    QUEUED, CLONING, SCANNING, COMPLETE, FAILED

class ScanRequestResponse:  job_id, status, message, estimated_duration_seconds
class FindingResponse:       rule_id, name, severity, message, fix, file, line, analyzer, ecosystem
class ScanResultResponse:    score, raw_score, grade, vibe_label, ..., findings: List[FindingResponse]
class JobStatusResponse:     job_id, status, github_url, created_at, updated_at, progress_message, result?, error?
class HealthResponse:        status, version, active_scans, queued_scans
```

### 4.6 Exception Hierarchy (`vibestandard-api/app/exceptions.py`)

```
VibeStandardException (base, status_code)
├── RepoNotFoundException        (404)
├── RepoPrivateException         (403)
├── RepoTooLargeException        (413)
├── CloneTimeoutException        (504)
├── CloneFailedException         (500)
├── JobNotFoundException         (404)
└── RateLimitException           (429)
```

All handled by a single `register_exception_handlers(app)` that returns `{"error": str, "status_code": int}`.

### 4.7 ScannerService (`vibestandard-api/app/services/scanner_service.py`)

Key internals:
- **`_jobs: dict[str, Job]`** — in-memory store (no persistence)
- **`_jobs_lock: threading.Lock`** — thread-safe access
- **`_executor: ThreadPoolExecutor`** — concurrent scans (default max 5)
- **`_run_scan(job)`** — background thread: clone → scan → convert → update job
- **`_execute_vibestandard_scan(clone_path)`** — imports vibestandard core, runs all 5 analyzers, returns ScanResult
- **`_start_cleanup_worker()`** — daemon thread deletes expired jobs (TTL=2h) and cloned repos (TTL=1h)

### 4.8 Frontend Routes

| Route | Page Component | Components Used |
|---|---|---|
| `/` | `HomePage` | `AnimatedBackground`, `HeroSection`, `SearchBar`, `FeatureCards`, `HowItWorks` |
| `/docs` | `DocsPage` | API documentation content |
| `/about` | `AboutPage` | Project info |

---

## 5. YAML Rules Format

Rules live in `vibestandard-analyzers/rules/*.yaml`. Each file is a list of rule objects:

```yaml
- id: h2-database                    # Unique rule ID (used as key everywhere)
  name: "H2 in-memory database detected"
  severity: "critical"               # critical | high | medium | low
  ecosystem: "java"                 # java | python | node | docker | generic
  analyzer: "dependency"            # dependency | config (only these two use YAML rules)
  match:
    files:                          # Glob patterns for file matching
      - "pom.xml"
      - "build.gradle"
    pattern: "h2database|com\\.h2database"  # Regex pattern to search in file content
  message: "Your project uses H2..."
  why_it_matters: "H2 is an in-memory database..."
  fix: "Replace H2 with PostgreSQL..."
```

**Important:** Only `DependencyAnalyzer` and `ConfigAnalyzer` consume YAML rules. The other 3 analyzers (security, infra, observability) have rules **hardcoded as Python dicts** inside their source files.

---

## 6. How to Run

### Production (Docker)
```bash
cp .env.example .env
docker compose up --build
# → Frontend: http://localhost:3000
# → API:      http://localhost:8000/api/docs
```

### Development (Docker with hot reload)
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
# → Frontend: http://localhost:5173  (Vite dev server)
# → API:      http://localhost:8000  (uvicorn --reload)
```

### CLI Only (no Docker)
```bash
cd vibestandard-analyzers
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python main.py scan /path/to/project
python main.py scan https://github.com/user/repo
python main.py scan project.zip
python main.py scan . --output json --output-file report.json
python main.py scan . --output html --output-file report.html
python main.py scan . --no-semgrep --severity high --fail-on critical
```

### Run Tests
```bash
cd vibestandard-analyzers
pip install -e ".[dev]"
pytest tests/ -v
pytest tests/ --cov=vibestandard --cov-report=html
```

---

## 7. Coding Conventions

### Python (Analyzers + API)
- **Python 3.13** minimum (uses `X | Y` union syntax, not `Optional[X]`)
- `from __future__ import annotations` used in most files
- Dataclasses for models, not Pydantic (in the analyzer core)
- Pydantic v2 `BaseModel` only in the API layer
- Private methods prefixed with `_`
- Rule analysis methods named `_check_{rule_name}`
- Error handling: analyzers catch exceptions per-analyzer so one failure doesn't crash the whole scan

### Frontend
- Functional React components with hooks
- React Router v7 for routing
- Tailwind CSS 3 for styling (not vanilla CSS)
- Framer Motion for animations
- Named exports (not default) for components: `export const Navbar = () => ...`
- Context API for theme management

### General
- No database — all state is in-memory
- No authentication
- Environment variables via `.env` / `pydantic-settings`
- Docker context for API is the project root (`.`), not `vibestandard-api/`, because it needs to COPY `vibestandard-analyzers/` into the image

---

## 8. Configuration Reference

### API Settings (`vibestandard-api/app/config.py`)

| Setting | Default | Environment Variable |
|---|---|---|
| `debug` | `false` | `DEBUG` |
| `cors_origins` | `http://localhost:3000,http://localhost:5173` | `CORS_ORIGINS` |
| `rate_limit_requests` | `10` | `RATE_LIMIT_REQUESTS` |
| `rate_limit_window_seconds` | `60` | `RATE_LIMIT_WINDOW_SECONDS` |
| `max_repo_size_mb` | `100` | `MAX_REPO_SIZE_MB` |
| `scan_timeout_seconds` | `300` | `SCAN_TIMEOUT_SECONDS` |
| `max_concurrent_scans` | `5` | `MAX_CONCURRENT_SCANS` |
| `clone_dir` | `/tmp/vibestandard-clones` | `CLONE_DIR` |
| `cleanup_after_seconds` | `3600` | `CLEANUP_AFTER_SECONDS` |
| `job_ttl_seconds` | `7200` | `JOB_TTL_SECONDS` |

### Frontend Build Arg
- `VITE_API_URL` — injected at build time, defaults to `http://3.26.114.125:8000` (EC2 IP)

---

## 9. Git History & Branches

- **Single branch:** `main`
- **Remote:** `origin/main` → `https://github.com/ahadRai/VibeStandard.git`
- **Tags:** `v1.0.0`, `v1.0.1`
- **20 commits total** (as of last check)

Development timeline:
1. Phase 1–2: scaffold, models, base classes
2. Added analyzers: Dependency → Security → Infra → Observability
3. Scoring engine + reporters
4. CLI polish: ecosystem awareness, HTML reports
5. v1.0.0: GitHub Actions CI for binary releases
6. v1.0.1: minor fixes, web experience message
7. Directory restructuring into monorepo
8. React frontend template
9. FastAPI backend + Docker integration
10. EC2 deployment: CORS iterations, env var support, port configs

---

## 10. Deployment Info

- **Target:** AWS EC2 instance at `3.26.114.125`
- **Production compose** serves React via nginx on `:3000`, API via uvicorn on `:8000`
- CORS is currently set to `*` (wildcard) in `docker-compose.yml` — production should restrict this
- Semgrep is installed in the Docker image as optional (graceful fallback if failed)
- Non-root user (`vibestandard`) in Docker for security
- Health checks configured for both API and web containers
- GitHub Actions workflow exists for building PyInstaller binaries on release tags

---

## 11. Current State: What Works vs. What's Incomplete

### ✅ Fully Implemented
- All 5 analyzers with real detection logic (~90 KB of analyzer code)
- YAML rules for 4 ecosystems (java, python, node, docker)
- Scoring engine with diminishing returns, context adjustments, deduplication
- 3 output reporters: terminal (Rich), JSON, HTML (Jinja2)
- CLI with scan, version, rules subcommands
- Ingestion: local path, GitHub URL, ZIP file
- FastAPI backend with complete job lifecycle
- Rate limiting, CORS, error handling
- React frontend with scan submission, polling, results display
- Full Docker setup (production + dev)
- GitHub Actions CI for binary releases

### ⚠️ Stubs / Incomplete
- **`rules list` CLI command** — prints "not yet implemented (Phase 3+)"
- **`rules add` CLI command** — prints "not yet implemented (Phase 3+)"
- No support for custom rule directories at runtime (stub only)
- No private repo support (needs GitHub token)
- `engine/rules_loader.py` may be a stale duplicate of `analyzers/rules_loader.py`

### 🚫 Missing Entirely
- **No tests for the API** — zero test files in `vibestandard-api/`
- **No tests for the frontend** — zero test files
- **No persistent storage** — jobs are in-memory, lost on restart
- **No user authentication** — anyone can scan
- **No scan history** — no way to view past scans
- **No domain/SSL** — runs on raw IP only
- **No CI/CD for deployment** — only binary release CI exists
- **No Go ecosystem YAML rules** — Go is detected but has no rules file

### 🔧 Technical Debt
- CORS set to `*` in production compose (should be restricted)
- `.env.example` contains actual EC2 IP (should be placeholder)
- `FindingResponse` in API doesn't include `why_it_matters` field (data loss from core → API)
- Security/Infra/Observability analyzers have hardcoded rules instead of YAML (inconsistent with Dependency/Config)

---

## 12. How to Extend

### Adding a New Analyzer
1. Create `vibestandard/analyzers/new_analyzer.py`
2. Subclass `BaseAnalyzer`, set `name` and `ecosystem`
3. Implement `analyze() → list[Finding]`
4. Wire it up in `vibestandard/cli.py` (import + add to progress bar section)
5. Add to `_ALL_ANALYZERS` set in `engine/scorer.py`
6. Wire it up in `vibestandard-api/app/services/scanner_service.py` `_execute_vibestandard_scan()`

### Adding a New YAML Rule
1. Add rule object to the appropriate `rules/*.yaml` file
2. Ensure `analyzer` field matches "dependency" or "config" (YAML rules only work for these two)
3. The rule will be automatically loaded by `rules_loader.py`

### Adding a New Security/Infra/Observability Rule
1. Add the rule to the `SECURITY_RULES` / `INFRA_RULES` / `OBS_RULES` dict in the respective analyzer
2. Add a new `_check_*` method
3. Call it from the `analyze()` method

### Adding a New Ecosystem
1. Add markers to `_ECOSYSTEM_MARKERS` in `ingestion/file_tree.py`
2. Add extensions to `_ECOSYSTEM_EXTENSIONS`
3. Create `rules/{ecosystem}.yaml` with rules
4. Add ecosystem-specific logic to analyzers as needed
5. Add fix messages to `ecosystem_fixes.py`

### Adding a New Reporter
1. Subclass `BaseReporter` in `reporters/`
2. Implement `render() → str | None`
3. Register it in `cli.py`'s `reporters` dict

### Adding a New API Endpoint
1. Create route in `vibestandard-api/app/routes/`
2. Register with `app.include_router()` in `main.py`

### Adding a New Frontend Page
1. Create component in `src/pages/`
2. Add route in `App.jsx`
3. Add nav link in `Navbar.jsx`

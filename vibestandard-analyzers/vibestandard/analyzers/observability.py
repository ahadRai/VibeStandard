"""
Observability Analyzer — checks whether the application has instrumentation for production monitoring.

Implements 9 rules covering logging, error tracking, health checks, metrics, and graceful shutdown.
Uses a codebase index to avoid reading files multiple times.
"""

from __future__ import annotations

import re
from pathlib import Path

from vibestandard.analyzers.base import BaseAnalyzer
from vibestandard.analyzers.ecosystem_fixes import get_ecosystem_fix
from vibestandard.models import Finding

# Files and directories to skip
_SKIP_DIRS = {"tests", "test", "node_modules", "venv", ".venv", "__pycache__", ".git"}
_SKIP_FILE_PATTERNS = {"test_", "_test.py"}
_MAX_FILE_SIZE = 300 * 1024  # 300KB

# Source file extensions to scan
_SOURCE_EXTENSIONS = {".py", ".js", ".ts", ".java", ".properties", ".yml", ".yaml"}

# Hardcoded rule definitions
OBS_RULES = {
    "no-structured-logging": {
        "name": "No structured logging library",
        "severity": "medium",
        "explanation": "No structured logging library found. The application appears to use print() statements for output. In production, print() output is unstructured, unsearchable, and often lost entirely depending on how the process is managed.",
        "why_it_matters": "Without structured logs, debugging production issues means SSH-ing into servers and grepping through unstructured text. Mean time to resolution increases from minutes to hours.",
        "fix": ""  # Will be populated dynamically based on ecosystem
    },
    "no-error-tracking": {
        "name": "No error tracking service",
        "severity": "medium",
        "explanation": "No error tracking service detected. Unhandled exceptions in production will be silent — you will only learn about errors from user complaints.",
        "why_it_matters": "Without error tracking, production bugs go unnoticed until users report them. You lose the stack trace, context, and frequency data needed to prioritize and fix issues quickly.",
        "fix": ""  # Will be populated dynamically based on ecosystem
    },
    "no-health-endpoint": {
        "name": "No health check endpoint",
        "severity": "high",
        "explanation": "No health check endpoint found. Without a /health endpoint, load balancers, container orchestrators, and uptime monitors cannot verify your application is running correctly. Unhealthy instances will continue receiving traffic.",
        "why_it_matters": "Without a health endpoint, your orchestrator cannot detect a deadlocked or crashed application. Traffic keeps routing to broken instances, causing user-visible outages that persist until manual intervention.",
        "fix": "Add a simple health endpoint that returns HTTP 200 when the app is running. In FastAPI: @app.get('/health') def health(): return {'status': 'ok'}. Make it check database connectivity if possible."
    },
    "no-request-id-middleware": {
        "name": "No request ID middleware",
        "severity": "low",
        "explanation": "No request ID or correlation ID middleware found. Without request IDs, tracing a single user request across multiple log lines or services is extremely difficult when debugging production issues.",
        "why_it_matters": "In a multi-service architecture, a single user request generates logs across dozens of services. Without correlation IDs, reconstructing the full request timeline for debugging is nearly impossible.",
        "fix": "Add request ID middleware that generates a UUID per request and attaches it to logs. In FastAPI use the asgi-correlation-id package. In Django use django-request-id. Log the request ID with every log statement."
    },
    "log-rotation-not-configured": {
        "name": "Log rotation not configured",
        "severity": "medium",
        "explanation": "Logging is configured to write to a file without log rotation. Log files will grow indefinitely and eventually fill the disk, causing the application and potentially the entire server to stop functioning.",
        "why_it_matters": "Unrotated log files fill disks over time. A full disk crashes not only your application but every other service on the same host, turning a logging oversight into a full outage.",
        "fix": "Use RotatingFileHandler or TimedRotatingFileHandler from Python's logging module. Or better yet, log to stdout and let your container runtime or log aggregator (Datadog, CloudWatch, Loki) handle storage and rotation."
    },
    "debug-logging-in-production": {
        "name": "Debug logging hardcoded",
        "severity": "medium",
        "explanation": "Logging level is hardcoded to DEBUG. In production, DEBUG logging generates extremely high log volume, exposes sensitive data in logs, and can significantly degrade performance.",
        "why_it_matters": "DEBUG logging in production can generate gigabytes of logs per hour, filling disks, driving up log storage costs, and making it impossible to find actual errors in the noise.",
        "fix": "Set the log level from an environment variable: logging.basicConfig(level=os.environ.get('LOG_LEVEL', 'INFO')). Set LOG_LEVEL=DEBUG locally and LOG_LEVEL=INFO or WARNING in production."
    },
    "no-metrics-endpoint": {
        "name": "No metrics instrumentation",
        "severity": "low",
        "explanation": "No metrics instrumentation found. Without metrics you cannot track response times, error rates, or throughput — the three signals needed to understand production performance.",
        "why_it_matters": "Without metrics, you cannot detect performance degradation, set up alerts for anomalies, or capacity-plan. Issues are only discovered after users complain about slowness or outages.",
        "fix": ""  # Will be populated dynamically based on ecosystem
    },
    "no-graceful-shutdown": {
        "name": "No graceful shutdown handling",
        "severity": "medium",
        "explanation": "No graceful shutdown handling detected. When the container receives a SIGTERM signal during deployment or scaling, the application will be killed immediately, dropping any in-flight requests.",
        "why_it_matters": "Without graceful shutdown, every deployment kills in-flight requests. Users see 502 errors, database transactions are left half-complete, and data integrity is at risk.",
        "fix": "Register a SIGTERM handler that stops accepting new requests and waits for in-flight requests to complete before exiting. In FastAPI use @app.on_event('shutdown'). In Flask use atexit.register(). Allow at least 30 seconds for graceful shutdown."
    },
    "no-dependency-monitoring": {
        "name": "No dependency monitoring",
        "severity": "low",
        "explanation": "External HTTP calls are made with no timeout or retry logic. A slow or unresponsive external service will cause your application's threads to hang indefinitely, eventually exhausting the thread pool and taking down the entire application.",
        "why_it_matters": "A single slow external dependency can cascade into a full outage. Without timeouts, threads pile up waiting for responses that never come, eventually exhausting resources and crashing the entire application.",
        "fix": "Always set timeouts on external calls: requests.get(url, timeout=5). Add retry logic with exponential backoff using the tenacity library. Consider a circuit breaker pattern for critical dependencies."
    }
}


class ObservabilityAnalyzer(BaseAnalyzer):
    """Analyzes codebase for observability and monitoring instrumentation."""
    
    name = "observability"
    ecosystem = "generic"
    
    def analyze(self) -> list[Finding]:
        """Run all observability checks using a codebase index."""
        # 1. Get all relevant source and config files
        source_files = self._get_source_files()
        
        if not source_files:
            return []
        
        # 2. Build the codebase index once
        index = self._build_index(source_files)
        
        # 3. Run all 9 checks passing the index
        self._check_no_structured_logging(index)
        self._check_no_error_tracking(index)
        self._check_no_health_endpoint(index)
        self._check_no_request_id_middleware(index)
        self._check_log_rotation_not_configured(index)
        self._check_debug_logging_in_production(index)
        self._check_no_metrics_endpoint(index)
        self._check_no_graceful_shutdown(index)
        self._check_no_dependency_monitoring(index)
        
        return self.findings
    
    def _add_obs_finding(self, rule_id: str, file: str | None = None, line: int | None = None) -> None:
        """Add an observability finding with ecosystem-aware fix."""
        rule = OBS_RULES.get(rule_id)
        if not rule:
            return
        
        # Get ecosystem-aware fix message
        fix = rule["fix"]
        if not fix:
            # Dynamically generate fix based on detected ecosystems
            fix = get_ecosystem_fix(rule_id, self.ecosystems)
        
        finding = Finding(
            rule_id=rule_id,
            name=rule["name"],
            severity=rule["severity"],
            explanation=rule["explanation"],
            why_it_matters=rule["why_it_matters"],
            fix=fix,
            file=file or "N/A",
            line=line,
            analyzer=self.name,
            ecosystem=self.ecosystem,
        )
        self.findings.append(finding)
    
    def _get_source_files(self) -> list[Path]:
        """Get all source and config files, filtering out tests and large files."""
        source_files = []
        for rel_path in self.file_tree:
            # Skip excluded directories
            if any(part in _SKIP_DIRS for part in rel_path.parts[:-1]):
                continue
            
            # Skip test files
            if any(rel_path.name.startswith(p) or rel_path.name.endswith(p) 
                   for p in _SKIP_FILE_PATTERNS):
                continue
            
            # Only scan relevant extensions
            if rel_path.suffix.lower() not in _SOURCE_EXTENSIONS:
                continue
            
            # Skip files larger than 300KB
            abs_path = self.root / rel_path
            try:
                if abs_path.stat().st_size > _MAX_FILE_SIZE:
                    continue
            except OSError:
                continue
            
            source_files.append(rel_path)
        
        return source_files
    
    def _build_index(self, files: list[Path]) -> dict:
        """Build a codebase index from all source files."""
        index = {
            "all_content": "",
            "all_lines": [],
            "imports": set(),
            "route_definitions": [],
            "file_contents": {}
        }
        
        for rel_path in files:
            abs_path = self.root / rel_path
            content = self.read_file_safe(abs_path)
            if not content:
                continue
            
            index["file_contents"][str(rel_path)] = content
            index["all_content"] += content + "\n"
            
            lines = content.splitlines()
            for line_num, line_text in enumerate(lines, 1):
                index["all_lines"].append((rel_path, line_num, line_text))
                
                # Extract imports (Python)
                if rel_path.suffix.lower() == ".py":
                    stripped = line_text.strip()
                    if stripped.startswith("import ") or stripped.startswith("from "):
                        index["imports"].add(stripped)
                
                # Extract route definitions
                route_patterns = [
                    r'@(app|router|api_view)\.(route|get|post|put|delete|patch)',
                    r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping)',
                ]
                for pattern in route_patterns:
                    if re.search(pattern, line_text):
                        index["route_definitions"].append((rel_path, line_num, line_text))
                        break
        
        return index
    
    def _check_no_structured_logging(self, index: dict) -> None:
        """Rule 1: Flag if no structured logging library is used."""
        # Check for structured logging imports
        structured_libs = {
            "import logging", "from logging", "import structlog", "import loguru",
            "from loguru", "import log4j", "import slf4j", "import winston",
            "import pino", "import bunyan"
        }
        
        has_structured_logging = any(lib in index["all_content"] for lib in structured_libs)
        
        if has_structured_logging:
            return
        
        # Count files with print() statements
        files_with_print = set()
        for rel_path, line_num, line_text in index["all_lines"]:
            if re.search(r'\bprint\s*\(', line_text):
                files_with_print.add(str(rel_path))
        
        # Skip if only in CLI entry points
        cli_files = {"main.py", "cli.py", "__main__.py"}
        non_cli_print_files = {
            f for f in files_with_print
            if Path(f).name not in cli_files
        }
        
        if len(non_cli_print_files) < 3:
            return
        
        # Check for logging config files
        config_files = {"logging.ini", "logging.yaml", "log4j.properties", "log4j2.xml"}
        has_config = any(f.name in config_files for f in self.file_tree)
        
        if has_config:
            return
        
        self._add_obs_finding("no-structured-logging")
    
    def _check_no_error_tracking(self, index: dict) -> None:
        """Rule 2: Flag if no error tracking service is integrated."""
        error_tracking_patterns = {
            "sentry_sdk", "import sentry", "Sentry.init",
            "import rollbar", "rollbar.init",
            "import bugsnag", "bugsnag.configure",
            "import datadog", "from datadog",
            "import newrelic", "import honeybadger", "import airbrake",
            "SENTRY_DSN", "ROLLBAR_TOKEN", "BUGSNAG_API_KEY"
        }
        
        has_error_tracking = any(pattern in index["all_content"] for pattern in error_tracking_patterns)
        
        if not has_error_tracking:
            self._add_obs_finding("no-error-tracking")
    
    def _check_no_health_endpoint(self, index: dict) -> None:
        """Rule 3: Flag if no health check endpoint exists."""
        health_paths = {
            "/health", "/healthz", "/health/", "/health/check",
            "/ping", "/pong",
            "/ready", "/readiness",
            "/live", "/liveness",
            "/status"
        }
        
        # Check route definitions
        for rel_path, line_num, line_text in index["route_definitions"]:
            if any(path in line_text for path in health_paths):
                return
        
        # Check for health check packages in dependencies
        health_packages = {
            "django-health-check", "fastapi-health", "spring-boot-starter-actuator"
        }
        
        if any(pkg in index["all_content"] for pkg in health_packages):
            return
        
        self._add_obs_finding("no-health-endpoint")
    
    def _check_no_request_id_middleware(self, index: dict) -> None:
        """Rule 4: Flag if no request ID middleware is configured."""
        request_id_patterns = {
            "X-Request-ID", "X-Correlation-ID", "X-Trace-ID",
            "request_id", "correlation_id", "trace_id",
            "asgi-correlation-id", "django-request-id", "flask-request-id",
            "opentelemetry", "from opentelemetry"
        }
        
        has_request_id = any(pattern in index["all_content"] for pattern in request_id_patterns)
        
        if not has_request_id:
            self._add_obs_finding("no-request-id-middleware")
    
    def _check_log_rotation_not_configured(self, index: dict) -> None:
        """Rule 5: Flag if file logging is used without rotation."""
        # Check for file handlers
        file_handler_patterns = {
            "FileHandler", "logging.FileHandler", "file=", "filename=",
            "sink="  # loguru
        }
        
        has_file_handler = any(pattern in index["all_content"] for pattern in file_handler_patterns)
        
        if not has_file_handler:
            return  # Only flag if file handlers are used
        
        # Check for rotation handlers
        rotation_patterns = {
            "RotatingFileHandler", "TimedRotatingFileHandler",
            "rotation=", "logrotate"
        }
        
        has_rotation = any(pattern in index["all_content"] for pattern in rotation_patterns)
        
        if not has_rotation:
            self._add_obs_finding("log-rotation-not-configured")
    
    def _check_debug_logging_in_production(self, index: dict) -> None:
        """Rule 6: Flag if DEBUG logging is hardcoded without env var guard."""
        debug_patterns = [
            r'logging\.basicConfig\s*\(.*level\s*=\s*logging\.DEBUG',
            r'LOG_LEVEL\s*=\s*DEBUG',
            r'level:\s*DEBUG',
            r'setLevel\s*\(\s*(logging\.)?DEBUG',
            r'setLevel\s*\(\s*["\']DEBUG["\']'
        ]
        
        for rel_path, line_num, line_text in index["all_lines"]:
            # Skip test files
            if any(p in str(rel_path) for p in {"test/", "tests/"}):
                continue
            
            for pattern in debug_patterns:
                if re.search(pattern, line_text, re.IGNORECASE):
                    # Check if it's guarded by env var
                    if "os.environ" not in line_text and "os.getenv" not in line_text:
                        # Skip .env.example files
                        if rel_path.name != ".env.example":
                            self._add_obs_finding(
                                "debug-logging-in-production",
                                str(rel_path),
                                line_num
                            )
                            return
    
    def _check_no_metrics_endpoint(self, index: dict) -> None:
        """Rule 7: Flag if no metrics instrumentation exists."""
        metrics_patterns = {
            "prometheus_client", "from prometheus_client",
            "statsd", "import statsd",
            "datadog.statsd", "DogStatsd",
            "opentelemetry.metrics",
            "micrometer", "prom-client",
            "/metrics"
        }
        
        has_metrics = any(pattern in index["all_content"] for pattern in metrics_patterns)
        
        if not has_metrics:
            self._add_obs_finding("no-metrics-endpoint")
    
    def _check_no_graceful_shutdown(self, index: dict) -> None:
        """Rule 8: Flag if web app has no graceful shutdown handling."""
        # Check if project has web framework
        web_frameworks = {
            "flask", "fastapi", "django", "express", "spring"
        }
        
        has_web_framework = any(
            re.search(rf'\b(import|from)\s+{fw}\b', line, re.IGNORECASE)
            for line in index["imports"]
            for fw in web_frameworks
        )
        
        # Also check for route definitions
        has_routes = len(index["route_definitions"]) > 0
        
        if not has_web_framework and not has_routes:
            return  # Not a web application
        
        # Check for graceful shutdown patterns
        shutdown_patterns = {
            "signal.signal(signal.SIGTERM", "signal.signal(signal.SIGINT",
            '@app.on_event("shutdown"', "@app.on_event('shutdown')",
            "atexit.register(", "process.on('SIGTERM'",
            "Runtime.getRuntime().addShutdownHook", "server.close("
        }
        
        has_shutdown = any(pattern in index["all_content"] for pattern in shutdown_patterns)
        
        if not has_shutdown:
            self._add_obs_finding("no-graceful-shutdown")
    
    def _check_no_dependency_monitoring(self, index: dict) -> None:
        """Rule 9: Flag if external HTTP calls have no timeout or retry logic."""
        # Check for HTTP client imports
        http_clients = {
            "import requests", "from requests", "import httpx", "from httpx",
            "import aiohttp", "from aiohttp", "import axios", "from axios"
        }
        
        has_http_client = any(client in index["all_content"] for client in http_clients)
        
        if not has_http_client:
            return  # No external HTTP calls
        
        # Check for retry/circuit breaker libraries
        retry_libs = {
            "tenacity", "backoff", "circuitbreaker", "resilience4j",
            "import retry", "@retry", "pybreaker"
        }
        
        has_retry = any(lib in index["all_content"] for lib in retry_libs)
        
        # Check for timeout parameters
        has_timeout = bool(re.search(r'(requests|httpx|aiohttp)\.(get|post|put|delete|patch)\s*\(.*timeout\s*=', index["all_content"]))
        
        if not has_retry and not has_timeout:
            self._add_obs_finding("no-dependency-monitoring")

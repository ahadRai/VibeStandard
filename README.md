# VibeStandard

**AI-Generated Code Production-Readiness Auditor**

VibeStandard is a Python CLI tool that audits vibe-coded and AI-generated software for production readiness. It scans your codebase across 5 dimensions — dependencies, configuration, security, infrastructure, and observability — then produces a comprehensive score with actionable recommendations.

## Features

- **5 Specialized Analyzers:**
  - **Dependency Analyzer** — Detects unpinned versions, missing lock files, and outdated packages
  - **Config Analyzer** — Finds development settings in production configs (debug mode, test databases, hardcoded secrets)
  - **Security Analyzer** — Identifies SQL injection, eval/exec, missing auth, insecure deserialization, and more (with optional Semgrep integration)
  - **Infra Analyzer** — Audits Docker, Docker Compose, Kubernetes, and CI/CD configurations for production safety
  - **Observability Analyzer** — Checks for structured logging, error tracking, health endpoints, metrics, and graceful shutdown

- **Intelligent Scoring Engine:**
  - 0-100 score with diminishing returns to prevent unfair penalization
  - Letter grades (A-F) and production readiness verdicts (PRODUCTION_READY / STAGING_READY / TEST_GRADE)
  - Context-aware adjustments for project size, critical findings, and analyzer health

- **Multiple Output Formats:**
  - Beautiful terminal output with rich formatting
  - Machine-readable JSON for CI/CD integration
  - Shareable HTML reports (coming soon)

- **Smart Detection:**
  - Automatic ecosystem detection (Python, Node.js, Java, Docker)
  - Cross-analyzer deduplication
  - False positive reduction with context analysis

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/ahadRai/VibeStandard.git
cd VibeStandard

# Create and activate virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with dependencies
pip install -e .
```

### Requirements

- Python 3.13 or higher
- Dependencies are automatically installed (typer, rich, PyYAML, gitpython, jinja2, etc.)

## Quick Start

### Basic Scan

Scan a local project directory:

```bash
python main.py scan /path/to/your/project
```

### Scan with Options

```bash
# Faster scan (skip Semgrep, works offline)
python main.py scan /path/to/project --no-semgrep

# Only show high and critical issues
python main.py scan /path/to/project --severity high

# Export as JSON for CI/CD
python main.py scan /path/to/project --output json --output-file report.json

# Fail CI if critical issues found
python main.py scan /path/to/project --fail-on critical

# Scan a GitHub repository
python main.py scan https://github.com/user/repo

# Scan a ZIP file
python main.py scan project.zip
```

## Output

### Terminal Report

The default terminal output includes:

```
╔══════════════════════════════════════════════╗
║           VibeStandard Report                ║
╚══════════════════════════════════════════════╝

Scanned:   ./my-project
Files:     142 files · 3 ecosystem(s) detected: java, docker, python
Duration:  4.2s

╔══════════════════════════════════════════════╗
║  Score: 34/100     Grade: D     TEST_GRADE   ║
╚══════════════════════════════════════════════╝

● CRITICAL (3 findings)
  h2-database              src/main/resources/application.properties:12
  └─ Your configuration file contains an H2 database URL...
     Fix: Replace the H2 JDBC URL with a PostgreSQL or MySQL...

Analyzer Breakdown:
┌───────────────┬──────────┬──────────┬──────┬────────┬─────┬────────────────────┐
│ Analyzer      │ Findings │ Critical │ High │ Medium │ Low │                    │
├───────────────┼──────────┼──────────┼──────┼────────┼─────┼────────────────────┤
│ dependency    │    4     │    1     │  1   │   2    │  0  │ ████████░░░░░░░░░░ │
│ config        │    3     │    2     │  0   │   1    │  0  │ ██████░░░░░░░░░░░░ │
│ security      │    2     │    1     │  1   │   0    │  0  │ ████░░░░░░░░░░░░░░ │
│ infra         │    5     │    1     │  2   │   2    │  0  │ ██████████░░░░░░░░ │
│ observability │    2     │    0     │  1   │   1    │  0  │ ████░░░░░░░░░░░░░░ │
└───────────────┴──────────┴──────────┴──────┴────────┴─────┴────────────────────┘
```

### JSON Report

For CI/CD pipelines and dashboards:

```bash
python main.py scan /path/to/project --output json --output-file report.json
```

Produces a complete JSON schema with score, findings, analyzer breakdown, and metadata.

## Scoring System

### Score Calculation

- Starts at 100 points
- Deductions per finding: Critical (-30), High (-15), Medium (-7), Low (-3)
- Diminishing returns after 3 findings of the same severity
- Context adjustments (+10 to -15 range)

### Grades

- **A** (90-100): Excellent
- **B** (75-89): Good
- **C** (55-74): Acceptable
- **D** (30-54): Needs Work
- **F** (0-29): Critical Issues

### Production Readiness Verdicts

- **PRODUCTION_READY**: Score ≥ 90, zero critical/high findings, no analyzer errors
- **STAGING_READY**: Score ≥ 55, zero critical findings, ≤ 1 analyzer error
- **TEST_GRADE**: Everything else

## CLI Options

| Option | Description |
|--------|-------------|
| `source` | Local path, GitHub URL, or ZIP file to scan |
| `--output, -o` | Output format: `terminal` (default), `json`, `html` |
| `--output-file` | Save report to a file |
| `--severity` | Filter findings: `critical`, `high`, `medium`, `low` |
| `--fail-on` | Exit code 1 if findings at this severity exist (for CI) |
| `--no-semgrep` | Skip Semgrep scan (faster, works offline) |
| `--no-cve` | Skip OSV CVE lookups (faster, works offline) |

## CI/CD Integration

### GitHub Actions

```yaml
- name: Audit code with VibeStandard
  run: |
    pip install -e .
    python main.py scan . --fail-on critical --output json --output-file audit.json
    
- name: Upload audit report
  uses: actions/upload-artifact@v4
  with:
    name: audit-report
    path: audit.json
```

### GitLab CI

```yaml
security_audit:
  script:
    - pip install -e .
    - python main.py scan . --fail-on high --severity medium
```

## Project Structure

```
VibeStandard/
├── vibestandard/
│   ├── analyzers/          # Analysis engines
│   │   ├── base.py        # Base analyzer class
│   │   ├── dependency.py  # Dependency checks
│   │   ├── config.py      # Configuration checks
│   │   ├── security.py    # Security vulnerability checks
│   │   ├── infra.py       # Infrastructure checks
│   │   ├── observability.py # Monitoring checks
│   │   └── rules_loader.py # YAML rule parser
│   ├── engine/
│   │   └── scorer.py      # Scoring engine
│   ├── reporters/          # Output formatters
│   │   ├── base.py        # Base reporter
│   │   ├── cli_reporter.py # Terminal output
│   │   └── json_reporter.py # JSON output
│   ├── ingestion/          # Code ingestion
│   │   ├── loader.py      # Local/GitHub/ZIP loading
│   │   └── file_tree.py   # File tree building
│   ├── models.py          # Data models
│   └── cli.py             # CLI entry point
├── rules/                  # YAML rule definitions
│   ├── java.yaml
│   ├── python.yaml
│   └── node.yaml
└── main.py                 # Main entry point
```

## Adding Custom Rules

Rules are defined in YAML files under `rules/`. Each rule specifies:

```yaml
- id: my-custom-rule
  name: "Descriptive rule name"
  severity: "high"
  ecosystem: "python"
  analyzer: "config"
  patterns:
    - "REGEX_PATTERN_TO_DETECT"
  message: "Explanation of the issue"
  fix: "How to resolve it"
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=vibestandard --cov-report=html
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Author

Built by Ahad Rai

---

**VibeStandard** — Because AI-generated code still needs to meet production standards.

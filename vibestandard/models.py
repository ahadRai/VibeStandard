from dataclasses import dataclass

@dataclass
class Finding:
    rule_id: str        # e.g. "h2-database"
    name: str           # Human readable name e.g. "H2 in-memory database detected"
    severity: str       # "critical", "high", "medium", "low"
    message: str        # Full explanation of the problem
    fix: str            # Concrete suggested fix
    file: str           # Relative path to the file where it was found
    line: int | None    # Line number if applicable, else None
    analyzer: str       # "dependency", "config", "security", "infra", "observability"
    ecosystem: str      # "java", "node", "python", "docker", "generic"

@dataclass
class ScanResult:
    score: int
    grade: str              # "A", "B", "C", "D", "F"
    vibe_label: str         # "PRODUCTION_READY", "STAGING_READY", "TEST_GRADE"
    scanned_path: str
    ecosystems: list[str]
    total_files: int
    duration_seconds: float
    findings: list[Finding]
    summary: dict           # {"critical": 3, "high": 2, "medium": 1, "low": 0}

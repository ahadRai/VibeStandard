from dataclasses import dataclass, field

@dataclass
class Finding:
    rule_id: str        # e.g. "h2-database"
    name: str           # Title: human readable name e.g. "H2 in-memory database detected"
    severity: str       # "critical", "high", "medium", "low"
    explanation: str    # Detailed explanation of the problem
    why_it_matters: str # Why this issue matters — impact and risk
    fix: str            # Concrete recommended fix
    file: str           # Affected file: relative path to the file where it was found
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
    skipped_files: int
    duration_seconds: float
    findings: list[Finding]
    summary: dict           # {"critical": 3, "high": 2, "medium": 1, "low": 0}
    analyzer_breakdown: dict
    category_breakdown: dict
    enrichment: dict        # Maps str(id(finding)) -> {"severity_rank": int, "display_color": str}
    analyzer_errors: list[str]
    deduplicated_count: int   # how many duplicate findings were removed
    raw_score: int            # score before context adjustments
    final_score: int          # score after context adjustments (same as score, kept for clarity)
    adjustments_applied: list[dict]
    # List of adjustments that were applied during context adjustment step:
    # [{"reason": "No critical findings bonus", "delta": +5}, ...]

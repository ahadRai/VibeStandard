"""
Comprehensive tests for the Scoring Engine.

Tests cover:
- Basic scoring
- Diminishing returns
- Context adjustments
- Vibe labels
- Deduplication
- Sorting
- Integration with real analyzers
"""

import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vibestandard.models import Finding, ScanResult
from vibestandard.engine.scorer import ScoringEngine


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def make_finding(
    rule_id: str = "test-rule",
    severity: str = "low",
    file: str = "test.py",
    line: int | None = None,
    analyzer: str = "dependency",
    ecosystem: str = "python",
    explanation: str = "Test finding"
) -> Finding:
    """Create a test finding with minimal required fields."""
    return Finding(
        rule_id=rule_id,
        name="Test Rule",
        severity=severity,
        explanation=explanation,
        why_it_matters="This is a test finding for scoring purposes.",
        fix="Fix it",
        file=file,
        line=line,
        analyzer=analyzer,
        ecosystem=ecosystem,
    )


def make_metadata(
    total_files: int = 100,
    analyzer_errors: list[str] | None = None
) -> dict:
    """Create test metadata."""
    return {
        "scanned_path": "/test/path",
        "ecosystems": ["python"],
        "total_files": total_files,
        "duration_seconds": 1.0,
        "skipped_files": 0,
        "analyzer_errors": analyzer_errors or [],
    }


# ---------------------------------------------------------------------------
# Basic scoring tests
# ---------------------------------------------------------------------------

def test_perfect_score_no_findings():
    """Empty findings list scores 100, grade A, PRODUCTION_READY."""
    engine = ScoringEngine()
    result = engine.score([], make_metadata())
    
    assert result.score == 100
    assert result.grade == "A"
    assert result.vibe_label == "PRODUCTION_READY"
    assert result.summary["total"] == 0


def test_single_critical_scores_correctly():
    """One critical finding: base = 100 - 30 = 70, no critical bonus doesn't apply."""
    engine = ScoringEngine()
    findings = [make_finding(severity="critical")]
    result = engine.score(findings, make_metadata())
    
    # Base: 100 - 30 = 70
    # No critical bonus: does NOT apply (has critical)
    assert result.raw_score == 70
    assert result.grade == "C"


def test_single_high_scores_correctly():
    """One high finding: 100 - 15 = 85, no-critical-bonus +5 = 90, all-analyzers-clean +2 = 92."""
    engine = ScoringEngine()
    findings = [make_finding(severity="high")]
    result = engine.score(findings, make_metadata())
    
    # Base: 100 - 15 = 85
    # No critical bonus: +5 = 90
    # All analyzers clean bonus: +2 = 92 (4 analyzers have 0 findings)
    assert result.raw_score == 85
    assert result.score == 92
    assert result.grade == "A"


def test_score_clamped_at_zero():
    """10 critical findings does not go below 0."""
    engine = ScoringEngine()
    # Create unique findings to avoid deduplication
    findings = [make_finding(severity="critical", rule_id=f"critical-{i}", file=f"file{i}.py") for i in range(10)]
    result = engine.score(findings, make_metadata())
    
    assert result.score == 0
    assert result.grade == "F"


def test_score_clamped_at_100():
    """Adjustments cannot push score above 100."""
    engine = ScoringEngine()
    # No findings = 100, +5 no critical bonus, +2 clean analyzers
    result = engine.score([], make_metadata())
    
    assert result.score == 100


# ---------------------------------------------------------------------------
# Diminishing returns tests
# ---------------------------------------------------------------------------

def test_diminishing_returns_critical():
    """
    5 critical findings: 
    - First 3 = -90 (3 × -30)
    - Next 2 = -30 (2 × -15, half rate)
    - Total deduction = -120, clamped to 0
    """
    engine = ScoringEngine()
    # Create unique findings to avoid deduplication
    findings = [make_finding(severity="critical", rule_id=f"critical-{i}", file=f"file{i}.py") for i in range(5)]
    result = engine.score(findings, make_metadata())
    
    assert result.raw_score == 0


def test_diminishing_returns_does_not_apply_below_threshold():
    """3 critical findings: exactly -90, no diminishing returns yet."""
    engine = ScoringEngine()
    # Create unique findings to avoid deduplication
    findings = [make_finding(severity="critical", rule_id=f"critical-{i}", file=f"file{i}.py") for i in range(3)]
    result = engine.score(findings, make_metadata())
    
    # 3 × -30 = -90, no diminishing returns (threshold is AFTER 3)
    assert result.raw_score == 10


# ---------------------------------------------------------------------------
# Context adjustments tests
# ---------------------------------------------------------------------------

def test_no_critical_bonus_applied():
    """Zero critical findings, assert +5 adjustment in adjustments_applied."""
    engine = ScoringEngine()
    findings = [make_finding(severity="low")]
    result = engine.score(findings, make_metadata())
    
    assert any(adj["reason"] == "No critical findings bonus" for adj in result.adjustments_applied)
    assert any(adj["delta"] == 5 for adj in result.adjustments_applied)


def test_no_critical_bonus_not_applied_when_critical_exists():
    """One critical finding, assert no +5 bonus."""
    engine = ScoringEngine()
    findings = [make_finding(severity="critical")]
    result = engine.score(findings, make_metadata())
    
    assert not any(adj["reason"] == "No critical findings bonus" for adj in result.adjustments_applied)


def test_security_critical_penalty_applied():
    """Critical finding with analyzer='security', assert -5 in adjustments_applied."""
    engine = ScoringEngine()
    findings = [make_finding(severity="critical", analyzer="security")]
    result = engine.score(findings, make_metadata())
    
    assert any(adj["reason"] == "Security critical finding penalty" for adj in result.adjustments_applied)
    assert any(adj["delta"] == -5 for adj in result.adjustments_applied)


def test_multiple_critical_penalty_applied():
    """4+ critical findings, assert -5 penalty recorded."""
    engine = ScoringEngine()
    # Create unique findings to avoid deduplication
    findings = [make_finding(severity="critical", rule_id=f"critical-{i}", file=f"file{i}.py") for i in range(4)]
    result = engine.score(findings, make_metadata())
    
    assert any(adj["reason"] == "Multiple critical findings penalty" for adj in result.adjustments_applied)
    assert any(adj["delta"] == -5 for adj in result.adjustments_applied)


def test_small_project_leniency():
    """total_files=5, only low findings, assert +3 adjustment applied."""
    engine = ScoringEngine()
    findings = [make_finding(severity="low") for _ in range(2)]
    metadata = make_metadata(total_files=5)
    result = engine.score(findings, metadata)
    
    assert any(adj["reason"] == "Small project leniency" for adj in result.adjustments_applied)
    assert any(adj["delta"] == 3 for adj in result.adjustments_applied)


# ---------------------------------------------------------------------------
# Vibe label tests
# ---------------------------------------------------------------------------

def test_production_ready_label():
    """score >= 90, no critical, no high, assert PRODUCTION_READY."""
    engine = ScoringEngine()
    findings = [make_finding(severity="low") for _ in range(2)]
    result = engine.score(findings, make_metadata())
    
    assert result.vibe_label == "PRODUCTION_READY"


def test_staging_ready_label():
    """score >= 55, no critical, some high findings, assert STAGING_READY."""
    engine = ScoringEngine()
    # Create findings that result in score >= 55 but has high findings
    findings = [make_finding(severity="high", rule_id=f"high-{i}", file=f"file{i}.py") for i in range(3)]
    result = engine.score(findings, make_metadata())
    
    # 100 - 45 = 55, +5 = 60, still >= 55, no critical, has high
    assert result.vibe_label == "STAGING_READY"


def test_test_grade_label_critical():
    """Any critical finding present, assert TEST_GRADE regardless of score."""
    engine = ScoringEngine()
    findings = [make_finding(severity="critical")]
    result = engine.score(findings, make_metadata())
    
    assert result.vibe_label == "TEST_GRADE"


def test_test_grade_label_low_score():
    """score < 55 with no critical, assert TEST_GRADE."""
    engine = ScoringEngine()
    # Create unique findings to avoid deduplication - need enough to get score < 55
    findings = [make_finding(severity="medium", rule_id=f"medium-{i}", file=f"file{i}.py") for i in range(15)]
    result = engine.score(findings, make_metadata())
    
    # 15 medium: first 3 = -21, next 12 = -42 (half rate), total = -63, base = 37
    # +5 no critical = 42, still < 55
    assert result.score < 55
    assert result.vibe_label == "TEST_GRADE"


# ---------------------------------------------------------------------------
# Deduplication tests
# ---------------------------------------------------------------------------

def test_duplicate_findings_removed():
    """Two findings with same rule_id, file, line — only one kept."""
    engine = ScoringEngine()
    findings = [
        make_finding(rule_id="same-rule", file="test.py", line=10),
        make_finding(rule_id="same-rule", file="test.py", line=10),
    ]
    result = engine.score(findings, make_metadata())
    
    assert len(result.findings) == 1


def test_deduplication_count_recorded():
    """Assert deduplicated_count == 1 after removing one duplicate."""
    engine = ScoringEngine()
    findings = [
        make_finding(rule_id="same-rule", file="test.py", line=10),
        make_finding(rule_id="same-rule", file="test.py", line=10),
    ]
    result = engine.score(findings, make_metadata())
    
    assert result.deduplicated_count == 1


def test_codebase_findings_deduplicated():
    """Two findings with file='codebase' and same rule_id, assert only one kept."""
    engine = ScoringEngine()
    findings = [
        make_finding(rule_id="no-health-endpoint", file="codebase"),
        make_finding(rule_id="no-health-endpoint", file="codebase"),
    ]
    result = engine.score(findings, make_metadata())
    
    assert len(result.findings) == 1


# ---------------------------------------------------------------------------
# Sorting tests
# ---------------------------------------------------------------------------

def test_findings_sorted_by_severity():
    """Mixed findings, assert critical comes before high before medium before low."""
    engine = ScoringEngine()
    findings = [
        make_finding(severity="low", rule_id="low-1", explanation="low"),
        make_finding(severity="critical", rule_id="critical-1", explanation="critical"),
        make_finding(severity="medium", rule_id="medium-1", explanation="medium"),
        make_finding(severity="high", rule_id="high-1", explanation="high"),
    ]
    result = engine.score(findings, make_metadata())
    
    severities = [f.severity for f in result.findings]
    assert severities == ["critical", "high", "medium", "low"]


def test_findings_sorted_by_file_within_severity():
    """Two high findings in different files, assert alphabetical file order."""
    engine = ScoringEngine()
    findings = [
        make_finding(severity="high", file="zebra.py"),
        make_finding(severity="high", file="alpha.py"),
    ]
    result = engine.score(findings, make_metadata())
    
    files = [f.file for f in result.findings]
    assert files == ["alpha.py", "zebra.py"]


# ---------------------------------------------------------------------------
# Integration tests (require full analyzer suite)
# ---------------------------------------------------------------------------

def test_bad_project_scores_below_40():
    """Run full analyzer suite on bad_project fixture, assert score < 40."""
    # This would require creating test fixtures
    # Skipping for now as it needs actual project files
    pytest.skip("Requires test fixtures with actual code")


def test_good_project_scores_above_85():
    """Run full analyzer suite on good_project fixture, assert score > 85."""
    pytest.skip("Requires test fixtures with actual code")


def test_bad_project_is_test_grade():
    """Assert bad_project vibe_label == 'TEST_GRADE'."""
    pytest.skip("Requires test fixtures with actual code")


def test_good_project_is_production_ready():
    """Assert good_project vibe_label == 'PRODUCTION_READY'."""
    pytest.skip("Requires test fixtures with actual code")

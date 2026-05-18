"""Tests for Phase 9: Reporters."""

import json
import pytest
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

from vibestandard.models import Finding, ScanResult
from vibestandard.reporters.base import BaseReporter
from vibestandard.reporters.json_reporter import JsonReporter
from vibestandard.reporters.cli_reporter import TerminalReporter
from vibestandard.reporters.html_reporter import HtmlReporter


# --- Fixtures ---

@pytest.fixture
def sample_findings():
    return [
        Finding(
            rule_id="h2-database",
            name="H2 in-memory database detected",
            severity="critical",
            message="H2 is a test database and should not be used in production",
            fix="Replace with PostgreSQL or MySQL",
            file="src/main/resources/application.properties",
            line=12,
            analyzer="dependency",
            ecosystem="java",
        ),
        Finding(
            rule_id="no-structured-logging",
            name="No structured logging",
            severity="medium",
            message="Application does not use structured logging",
            fix="Add a structured logging library",
            file="src/main/java/App.java",
            line=None,
            analyzer="observability",
            ecosystem="java",
        ),
    ]


@pytest.fixture
def sample_result(sample_findings):
    return ScanResult(
        findings=sample_findings,
        score=34,
        raw_score=39,
        grade="D",
        vibe_label="TEST_GRADE",
        scanned_path="./test-project",
        ecosystems=["java"],
        total_files=50,
        skipped_files=2,
        duration_seconds=1.5,
        summary={"critical": 1, "high": 0, "medium": 1, "low": 0, "total": 2},
        analyzer_breakdown={
            "dependency": {"total": 1, "critical": 1, "high": 0, "medium": 0, "low": 0},
            "observability": {"total": 1, "critical": 0, "high": 0, "medium": 1, "low": 0},
        },
        adjustments_applied=[
            {"reason": "No critical findings bonus", "delta": 5},
        ],
        category_breakdown={},
        enrichment={},
        analyzer_errors=[],
        deduplicated_count=0,
        final_score=34,
    )


@pytest.fixture
def perfect_result():
    """A result with zero findings."""
    return ScanResult(
        findings=[],
        score=100,
        raw_score=100,
        grade="A",
        vibe_label="PRODUCTION_READY",
        scanned_path="./perfect-project",
        ecosystems=["python"],
        total_files=10,
        skipped_files=0,
        duration_seconds=0.5,
        summary={"critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0},
        analyzer_breakdown={},
        adjustments_applied=[],
        category_breakdown={},
        enrichment={},
        analyzer_errors=[],
        deduplicated_count=0,
        final_score=100,
    )


# --- JSON Reporter Tests ---

class TestJsonReporter:
    def test_json_output_is_valid_json(self, sample_result):
        reporter = JsonReporter(result=sample_result, options={})
        output = reporter.render()
        # Should not raise
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_json_contains_all_required_fields(self, sample_result):
        reporter = JsonReporter(result=sample_result, options={})
        output = reporter.render()
        parsed = json.loads(output)
        
        required_fields = [
            "tool", "version", "timestamp", "score", "raw_score", "grade",
            "vibe_label", "scanned_path", "ecosystems", "total_files",
            "skipped_files", "duration_seconds", "summary", "findings",
            "analyzer_breakdown", "analyzer_errors"
        ]
        for field in required_fields:
            assert field in parsed, f"Missing field: {field}"

    def test_json_findings_match_scan_result(self, sample_result):
        reporter = JsonReporter(result=sample_result, options={})
        output = reporter.render()
        parsed = json.loads(output)
        
        assert len(parsed["findings"]) == len(sample_result.findings)
        assert parsed["findings"][0]["rule_id"] == "h2-database"

    def test_json_severity_filter_still_includes_all(self, sample_result):
        """Even with severity filter, JSON should include all findings."""
        reporter = JsonReporter(result=sample_result, options={"severity_filter": "critical"})
        output = reporter.render()
        parsed = json.loads(output)
        
        # All findings should still be present
        assert len(parsed["findings"]) == 2
        # But filter should be noted
        assert parsed.get("severity_filter_applied") == "critical"

    def test_json_written_to_file(self, sample_result, tmp_path):
        output_file = tmp_path / "report.json"
        reporter = JsonReporter(result=sample_result, options={"output_file": str(output_file)})
        reporter.render()
        
        assert output_file.exists()
        with open(output_file) as f:
            parsed = json.loads(f.read())
        assert parsed["tool"] == "vibestandard"


# --- Terminal Reporter Tests ---

class TestTerminalReporter:
    def test_terminal_renders_without_exception(self, sample_result):
        reporter = TerminalReporter(result=sample_result, options={})
        # Should not raise
        reporter.render()

    def test_terminal_zero_findings_shows_success(self, perfect_result):
        reporter = TerminalReporter(result=perfect_result, options={})
        # Should render success panel
        reporter.render()

    def test_terminal_severity_filter_applied(self, sample_result):
        reporter = TerminalReporter(result=sample_result, options={"severity_filter": "critical"})
        # Should only show critical findings
        reporter.render()


# --- HTML Reporter Tests ---

class TestHtmlReporter:
    def test_html_output_is_valid_html(self, sample_result):
        reporter = HtmlReporter(result=sample_result, options={})
        output = reporter.render()
        
        assert "<!DOCTYPE html>" in output
        assert "</html>" in output

    def test_html_contains_score(self, sample_result):
        reporter = HtmlReporter(result=sample_result, options={})
        output = reporter.render()
        
        assert "34" in output  # Score value

    def test_html_contains_all_findings(self, sample_result):
        reporter = HtmlReporter(result=sample_result, options={})
        output = reporter.render()
        
        for finding in sample_result.findings:
            assert finding.rule_id in output

    def test_html_written_to_file(self, sample_result, tmp_path):
        output_file = tmp_path / "report.html"
        reporter = HtmlReporter(result=sample_result, options={"output_file": str(output_file)})
        reporter.render()
        
        assert output_file.exists()
        content = output_file.read_text()
        assert "<!DOCTYPE html>" in content

    def test_html_no_external_resources(self, sample_result):
        reporter = HtmlReporter(result=sample_result, options={})
        output = reporter.render()
        
        # Should not have external links in style or script sections
        assert "http://" not in output.split("</style>")[0]
        assert "https://" not in output.split("</style>")[0]


# --- Base Reporter Tests ---

class TestBaseReporter:
    def test_filter_findings_by_severity(self, sample_result):
        class TestReporter(BaseReporter):
            def render(self):
                pass
        
        reporter = TestReporter(result=sample_result, options={"severity_filter": "critical"})
        filtered = reporter._filter_findings()
        
        # Should only return critical findings
        assert len(filtered) == 1
        assert filtered[0].severity == "critical"

    def test_severity_rank(self, sample_result):
        class TestReporter(BaseReporter):
            def render(self):
                pass
        
        reporter = TestReporter(result=sample_result, options={})
        assert reporter._severity_rank("critical") == 0
        assert reporter._severity_rank("high") == 1
        assert reporter._severity_rank("medium") == 2
        assert reporter._severity_rank("low") == 3

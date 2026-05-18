"""
Scoring Engine — takes all findings from all analyzers and produces a ScanResult.

Implements deduplication, base scoring with diminishing returns, context adjustments,
grade/vibe calculation, and finding enrichment.
"""

from __future__ import annotations

from vibestandard.models import Finding, ScanResult

# Severity deduction values
_SEVERITY_DEDUCTIONS = {
    "critical": 30,
    "high": 15,
    "medium": 7,
    "low": 3,
}

# Severity ordering for sorting and enrichment
_SEVERITY_RANK = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}

_SEVERITY_COLORS = {
    "critical": "red",
    "high": "yellow",
    "medium": "blue",
    "low": "dim",
}

# All analyzer names (always included in breakdown)
_ALL_ANALYZERS = {"dependency", "config", "security", "infra", "observability"}


class ScoringEngine:
    """Calculates production-readiness scores from analyzer findings."""

    def score(
        self,
        findings: list[Finding],
        metadata: dict
    ) -> ScanResult:
        """
        Main scoring pipeline.
        
        Flow:
        1. Deduplicate findings
        2. Calculate base score with diminishing returns
        3. Apply context adjustments
        4. Calculate grade
        5. Calculate vibe label
        6. Build summary
        7. Build analyzer breakdown
        8. Build category breakdown
        9. Sort findings
        10. Enrich findings
        11. Assemble and return ScanResult
        """
        # 1. Deduplicate findings, record how many were removed
        original_count = len(findings)
        deduplicated = self._deduplicate_findings(findings)
        deduplicated_count = original_count - len(deduplicated)
        
        # 2. Calculate base score with diminishing returns
        raw_score = self._calculate_base_score(deduplicated)
        
        # 3. Apply context adjustments, record each one applied
        final_score, adjustments = self._apply_context_adjustments(
            raw_score, deduplicated, metadata
        )
        
        # 4. Calculate grade
        grade = self._calculate_grade(final_score)
        
        # 5. Calculate vibe label
        vibe_label = self._calculate_vibe_label(final_score, deduplicated, metadata)
        
        # 6. Build summary
        summary = self._build_summary(deduplicated)
        
        # 7. Build analyzer breakdown
        analyzer_breakdown = self._build_analyzer_breakdown(deduplicated)
        
        # 8. Build category breakdown
        category_breakdown = self._build_category_breakdown(deduplicated)
        
        # 9. Sort findings
        sorted_findings = self._sort_findings(deduplicated)
        
        # 10. Enrich findings
        enrichment = self._enrich_findings(sorted_findings)
        
        # 11. Assemble and return ScanResult
        return ScanResult(
            score=final_score,
            grade=grade,
            vibe_label=vibe_label,
            scanned_path=metadata.get("scanned_path", ""),
            ecosystems=metadata.get("ecosystems", []),
            total_files=metadata.get("total_files", 0),
            skipped_files=metadata.get("skipped_files", 0),
            duration_seconds=metadata.get("duration_seconds", 0.0),
            findings=sorted_findings,
            summary=summary,
            analyzer_breakdown=analyzer_breakdown,
            category_breakdown=category_breakdown,
            enrichment=enrichment,
            analyzer_errors=metadata.get("analyzer_errors", []),
            deduplicated_count=deduplicated_count,
            raw_score=raw_score,
            final_score=final_score,
            adjustments_applied=adjustments,
        )

    def _deduplicate_findings(self, findings: list[Finding]) -> list[Finding]:
        """
        Remove duplicate findings.
        
        Two findings are duplicates if they share the same (rule_id, file, line).
        Keep the one with the longer message if duplicates exist.
        Also deduplicate whole-codebase findings (file == "codebase").
        """
        seen = {}
        
        for finding in findings:
            # Create deduplication key
            key = (finding.rule_id, finding.file, finding.line)
            
            if key in seen:
                # Keep the one with the longer, more descriptive message
                existing = seen[key]
                if len(finding.message) > len(existing.message):
                    seen[key] = finding
            else:
                seen[key] = finding
        
        return list(seen.values())

    def _calculate_base_score(self, findings: list[Finding]) -> int:
        """
        Calculate base score starting at 100 with deductions per finding.
        
        Applies diminishing returns: after first 3 findings of same severity,
        each additional finding deducts only half the normal amount.
        """
        score = 100
        
        # Count findings by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for finding in findings:
            severity = finding.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Apply deductions with diminishing returns
        for severity, count in severity_counts.items():
            base_deduction = _SEVERITY_DEDUCTIONS.get(severity, 0)
            
            if count == 0:
                continue
            
            # First 3 findings at full rate
            full_rate_count = min(count, 3)
            score -= full_rate_count * base_deduction
            
            # Remaining findings at half rate
            half_rate_count = max(0, count - 3)
            if half_rate_count > 0:
                score -= half_rate_count * (base_deduction / 2)
        
        # Clamp between 0 and 100
        return max(0, min(100, int(score)))

    def _apply_context_adjustments(
        self, score: int, findings: list[Finding], metadata: dict
    ) -> tuple[int, list[dict]]:
        """
        Apply context adjustments to the score.
        
        Returns tuple of (adjusted_score, list_of_adjustments_applied).
        """
        adjustments = []
        
        # Count findings by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for finding in findings:
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1
        
        total_files = metadata.get("total_files", 0)
        analyzer_errors = metadata.get("analyzer_errors", [])
        
        # Small project leniency (+3)
        if total_files < 10:
            has_only_low_or_medium = all(
                f.severity in ("low", "medium") for f in findings
            )
            if has_only_low_or_medium and len(findings) > 0:
                score += 3
                adjustments.append({"reason": "Small project leniency", "delta": 3})
        
        # No critical findings bonus (+5)
        if severity_counts["critical"] == 0:
            score += 5
            adjustments.append({"reason": "No critical findings bonus", "delta": 5})
        
        # All analyzers clean bonus (+2)
        analyzers_with_findings = set(f.analyzer for f in findings)
        clean_analyzers = _ALL_ANALYZERS - analyzers_with_findings
        if len(clean_analyzers) >= 3:
            score += 2
            adjustments.append({"reason": "All analyzers clean bonus", "delta": 2})
        
        # Critical finding in security analyzer penalty (-5)
        has_security_critical = any(
            f.analyzer == "security" and f.severity == "critical"
            for f in findings
        )
        if has_security_critical:
            score -= 5
            adjustments.append({"reason": "Security critical finding penalty", "delta": -5})
        
        # Multiple critical findings penalty (-5)
        if severity_counts["critical"] >= 4:
            score -= 5
            adjustments.append({"reason": "Multiple critical findings penalty", "delta": -5})
        
        # Analyzer error penalty (-3)
        if len(analyzer_errors) > 0:
            score -= 3
            adjustments.append({"reason": "Analyzer error penalty", "delta": -3})
        
        # Clamp between 0 and 100
        score = max(0, min(100, score))
        
        return score, adjustments

    def _calculate_grade(self, score: int) -> str:
        """Calculate letter grade from score."""
        if score >= 90:
            return "A"
        elif score >= 75:
            return "B"
        elif score >= 55:
            return "C"
        elif score >= 30:
            return "D"
        else:
            return "F"

    def _calculate_vibe_label(
        self, score: int, findings: list[Finding], metadata: dict
    ) -> str:
        """
        Calculate human-readable production readiness verdict.
        
        Rules applied strictly in order - first match wins.
        """
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for finding in findings:
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1
        
        analyzer_errors = metadata.get("analyzer_errors", [])
        
        # PRODUCTION_READY
        if (score >= 90 and
            severity_counts["critical"] == 0 and
            severity_counts["high"] == 0 and
            len(analyzer_errors) == 0):
            return "PRODUCTION_READY"
        
        # STAGING_READY
        if (score >= 55 and
            severity_counts["critical"] == 0 and
            len(analyzer_errors) <= 1):
            return "STAGING_READY"
        
        # TEST_GRADE (anything else)
        return "TEST_GRADE"

    def _build_summary(self, findings: list[Finding]) -> dict:
        """Build summary counts by severity."""
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for finding in findings:
            severity = finding.severity
            summary[severity] = summary.get(severity, 0) + 1
        
        summary["total"] = len(findings)
        return summary

    def _build_analyzer_breakdown(self, findings: list[Finding]) -> dict:
        """
        Build breakdown by analyzer.
        
        Always includes all five analyzers even if they produced zero findings.
        """
        breakdown = {}
        
        for analyzer in _ALL_ANALYZERS:
            breakdown[analyzer] = {
                "total": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            }
        
        for finding in findings:
            analyzer = finding.analyzer
            if analyzer not in breakdown:
                continue
            
            breakdown[analyzer]["total"] += 1
            severity = finding.severity
            breakdown[analyzer][severity] = breakdown[analyzer].get(severity, 0) + 1
        
        return breakdown

    def _build_category_breakdown(self, findings: list[Finding]) -> dict:
        """
        Build breakdown by ecosystem.
        
        Only includes ecosystems that have at least one finding.
        """
        breakdown = {}
        
        for finding in findings:
            ecosystem = finding.ecosystem
            if ecosystem not in breakdown:
                breakdown[ecosystem] = {"total": 0, "critical": 0}
            
            breakdown[ecosystem]["total"] += 1
            if finding.severity == "critical":
                breakdown[ecosystem]["critical"] += 1
        
        return breakdown

    def _sort_findings(self, findings: list[Finding]) -> list[Finding]:
        """
        Sort findings by:
        1. Severity (critical first, then high, medium, low)
        2. Analyzer name alphabetically
        3. File path alphabetically
        4. Line number ascending (None lines go last)
        """
        def sort_key(finding: Finding):
            severity_rank = _SEVERITY_RANK.get(finding.severity, 99)
            analyzer_name = finding.analyzer
            file_path = finding.file
            # None lines go last (use infinity)
            line_num = finding.line if finding.line is not None else float('inf')
            
            return (severity_rank, analyzer_name, file_path, line_num)
        
        return sorted(findings, key=sort_key)

    def _enrich_findings(self, findings: list[Finding]) -> dict:
        """
        Add severity_rank and display_color to findings.
        
        Returns dict mapping str(id(finding)) -> enrichment data.
        """
        enrichment = {}
        
        for finding in findings:
            finding_id = str(id(finding))
            enrichment[finding_id] = {
                "severity_rank": _SEVERITY_RANK.get(finding.severity, 99),
                "display_color": _SEVERITY_COLORS.get(finding.severity, "white"),
            }
        
        return enrichment

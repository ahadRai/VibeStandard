"""JSON Reporter — machine-readable output for CI pipelines and integrations."""

import json
from datetime import datetime, timezone
from dataclasses import asdict
from importlib.metadata import version, PackageNotFoundError

from rich.console import Console

from vibestandard.reporters.base import BaseReporter

console = Console()


class JsonReporter(BaseReporter):
    """Produces complete, stable, machine-readable JSON output."""

    def render(self) -> str | None:
        """Render and optionally save JSON report."""
        output = self._build_json()
        json_str = json.dumps(output, indent=2, ensure_ascii=False)
        
        output_file = self.options.get("output_file")
        
        if output_file:
            self._write_output(json_str, output_file)
            console.print(f"[green]Saved JSON report to {output_file}[/]")
        else:
            print(json_str)
        
        return json_str

    def _build_json(self) -> dict:
        """Build the complete JSON output structure."""
        # Get version
        try:
            app_version = version("vibestandard")
        except PackageNotFoundError:
            app_version = "0.1.0"
        
        # Generate timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Convert findings to dicts
        findings_dicts = [asdict(f) for f in self.result.findings]
        
        output = {
            "tool": "vibestandard",
            "version": app_version,
            "timestamp": timestamp,
            "score": self.result.score,
            "raw_score": self.result.raw_score,
            "grade": self.result.grade,
            "vibe_label": self.result.vibe_label,
            "scanned_path": self.result.scanned_path,
            "ecosystems": self.result.ecosystems,
            "total_files": self.result.total_files,
            "skipped_files": self.result.skipped_files,
            "duration_seconds": self.result.duration_seconds,
            "deduplicated_count": self.result.deduplicated_count,
            "adjustments_applied": self.result.adjustments_applied,
            "summary": self.result.summary,
            "analyzer_breakdown": self.result.analyzer_breakdown,
            "findings": findings_dicts,
            "analyzer_errors": self.result.analyzer_errors,
        }
        
        # Add severity filter info if applied
        severity_filter = self.options.get("severity_filter")
        if severity_filter:
            output["severity_filter_applied"] = severity_filter
        
        return output

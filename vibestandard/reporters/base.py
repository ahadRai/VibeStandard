"""Base Reporter — abstract interface for all reporters."""

from abc import ABC, abstractmethod
from pathlib import Path

from vibestandard.models import ScanResult


class BaseReporter(ABC):
    """Abstract base class for all reporters."""

    def __init__(self, result: ScanResult, options: dict):
        self.result = result
        self.options = options
        # options may contain:
        # "severity_filter": str   — only show findings at or above this level
        # "output_file": str | None — save output to this path if set
        # "fail_on": str | None    — exit with code 1 if findings at this severity exist

    @abstractmethod
    def render(self) -> str | None:
        """
        Return the rendered output as a string.
        
        For the terminal reporter, print directly and return None.
        For JSON and HTML reporters, return the string and also
        write to output_file if options["output_file"] is set.
        """
        pass

    def _filter_findings(self) -> list:
        """
        Filter findings by options["severity_filter"].
        
        Severity order: critical > high > medium > low
        "high" filter means: return critical and high only
        """
        severity_filter = self.options.get("severity_filter")
        
        if not severity_filter:
            return self.result.findings
        
        severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        threshold = severity_rank.get(severity_filter, 99)
        
        return [
            f for f in self.result.findings
            if severity_rank.get(f.severity, 99) <= threshold
        ]

    def _severity_rank(self, severity: str) -> int:
        """Return numeric rank for severity (lower = more severe)."""
        return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(severity, 99)

    def _write_output(self, content: str, output_file: str | None = None) -> None:
        """Write output to file if specified."""
        if output_file:
            path = Path(output_file)
            path.write_text(content, encoding="utf-8")

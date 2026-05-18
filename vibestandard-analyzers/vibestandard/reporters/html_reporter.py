"""HTML Reporter — generates beautiful, self-contained HTML reports."""

import math
from datetime import datetime, timezone
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from rich.console import Console

from vibestandard.reporters.base import BaseReporter

console = Console()


class HtmlReporter(BaseReporter):
    """Generates a beautiful, self-contained HTML report."""

    def render(self) -> str | None:
        """Render and save HTML report."""
        # Pre-calculate SVG gauge math
        radius = 80
        circumference = 2 * math.pi * radius
        offset = circumference - (self.result.score / 100) * circumference
        
        # Determine colors
        if self.result.score >= 75:
            score_color = "green"
        elif self.result.score >= 55:
            score_color = "amber"
        else:
            score_color = "red"
        
        if self.result.grade in ("A", "B"):
            grade_color = "green"
        elif self.result.grade == "C":
            grade_color = "amber"
        else:
            grade_color = "red"
        
        # Generate timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Get version
        try:
            app_version = version("vibestandard")
        except PackageNotFoundError:
            app_version = "0.1.0"
        
        # Filter findings
        filtered_findings = self._filter_findings()
        
        # Load template
        template_dir = Path(__file__).parent / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        
        try:
            template = env.get_template("report.html.j2")
        except TemplateNotFound:
            console.print("[red]Error: HTML template not found[/]")
            return None
        
        # Render template
        html_content = template.render(
            result=self.result,
            findings=filtered_findings,
            score_color=score_color,
            grade_color=grade_color,
            timestamp=timestamp,
            version=app_version,
            gauge_circumference=circumference,
            gauge_offset=offset,
        )
        
        # Write to file
        output_file = self.options.get("output_file")
        if not output_file:
            output_file = "vibestandard-report.html"
        
        self._write_output(html_content, output_file)
        console.print(f"[green]Saved HTML report to {Path(output_file).resolve()}[/]")
        
        return html_content

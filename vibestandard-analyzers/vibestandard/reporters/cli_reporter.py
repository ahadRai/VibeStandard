"""Terminal Reporter — beautiful, scannable terminal output using rich."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich.text import Text

from vibestandard.reporters.base import BaseReporter


class TerminalReporter(BaseReporter):
    """Renders scan results to the terminal using rich components."""

    def __init__(self, result, options):
        super().__init__(result, options)
        self.console = Console()

    def render(self) -> str | None:
        """Render the full terminal report."""
        filtered = self._filter_findings()
        
        # Section 1 — Header
        self.console.print()
        self.console.print(
            Panel(
                "[bold cyan]VibeStandard Report[/]",
                border_style="cyan",
                padding=(0, 2),
            )
        )
        self.console.print()
        
        # Section 2 — Scan metadata
        self.console.print(f"[bold]Scanned:[/]   {self.result.scanned_path}")
        self.console.print(
            f"[bold]Files:[/]     {self.result.total_files} files · "
            f"{len(self.result.ecosystems)} ecosystem(s) detected: "
            f"{', '.join(self.result.ecosystems) if self.result.ecosystems else 'none'}"
        )
        self.console.print(f"[bold]Duration:[/]  {self.result.duration_seconds:.1f}s")
        
        if self.result.skipped_files > 0:
            self.console.print(
                f"[bold]Skipped:[/]   {self.result.skipped_files} files (binary or unreadable)"
            )
        
        # Show finding counts summary
        summary = self.result.summary
        if summary.get("total", 0) > 0:
            counts = []
            if summary.get("critical", 0) > 0:
                counts.append(f"[bold red]{summary['critical']} critical[/]")
            if summary.get("high", 0) > 0:
                counts.append(f"[bold yellow]{summary['high']} high[/]")
            if summary.get("medium", 0) > 0:
                counts.append(f"[bold blue]{summary['medium']} medium[/]")
            if summary.get("low", 0) > 0:
                counts.append(f"[dim]{summary['low']} low[/]")
            if counts:
                self.console.print(f"[bold]Findings:[/]  {', '.join(counts)}")
        
        self.console.print()
        
        # Section 3 — Score banner
        grade = self.result.grade
        if grade in ("A", "B"):
            border_color = "green"
        elif grade == "C":
            border_color = "yellow"
        else:
            border_color = "red"
        
        # Score color
        if self.result.score >= 75:
            score_color = "green"
        elif self.result.score >= 55:
            score_color = "yellow"
        else:
            score_color = "red"
        
        score_text = Text()
        score_text.append("Score: ", style="bold")
        score_text.append(f"{self.result.score}/100", style=f"bold {score_color}")
        score_text.append("     ")
        score_text.append("Grade: ", style="bold")
        score_text.append(grade, style=f"bold {border_color}")
        score_text.append("     ")
        score_text.append(self.result.vibe_label, style="bold")
        
        self.console.print(
            Panel(score_text, border_style=border_color, padding=(1, 2))
        )
        
        # Adjustments
        if self.result.adjustments_applied:
            self.console.print()
            self.console.print("[bold]Adjustments:[/]")
            for adj in self.result.adjustments_applied:
                delta_str = f"+{adj['delta']}" if adj['delta'] > 0 else str(adj['delta'])
                color = "green" if adj['delta'] > 0 else "red"
                self.console.print(f"  [{color}]{delta_str}[/] {adj['reason']}")
        
        self.console.print()
        
        # Section 4 — Findings grouped by severity
        if not filtered:
            # Zero findings - show success panel
            self.console.print(
                Panel(
                    "[bold green]✔  No issues found. Looks production-ready![/]",
                    border_style="green",
                    padding=(1, 2),
                )
            )
        else:
            # Severity filter note
            if self.options.get("severity_filter"):
                self.console.print(
                    f"[dim]Showing {self.options['severity_filter']} and above findings only. "
                    f"Use --severity low to see all.[/dim]\n"
                )
            
            # Group by severity
            severity_order = ["critical", "high", "medium", "low"]
            severity_colors = {
                "critical": "bold red",
                "high": "bold yellow",
                "medium": "bold blue",
                "low": "dim",
            }
            
            for severity in severity_order:
                sev_findings = [f for f in filtered if f.severity == severity]
                if not sev_findings:
                    continue
                
                # Severity header
                count = len(sev_findings)
                finding_word = "finding" if count == 1 else "findings"
                self.console.print(
                    f"[{severity_colors[severity]}]● {severity.upper()}  ({count} {finding_word})[/]"
                )
                self.console.print()
                
                # Each finding
                for idx, finding in enumerate(sev_findings, 1):
                    # Calculate global finding number
                    global_num = sum(
                        len([f for f in filtered if f.severity == s])
                        for s in severity_order[:severity_order.index(severity)]
                    ) + idx
                    
                    # rule_id and file:line with number
                    file_display = f"{finding.file}:{finding.line}" if finding.line else finding.file
                    
                    self.console.print(
                        f"  [{severity_colors[severity]}]{global_num}. {finding.rule_id}[/]"
                    )
                    self.console.print(f"     [dim]{file_display}[/]")
                    
                    # Message
                    self.console.print(f"     {finding.message}")
                    
                    # Fix
                    if finding.fix:
                        # Truncate long fixes for readability
                        fix_text = finding.fix
                        if len(fix_text) > 200:
                            fix_text = fix_text[:200] + "..."
                        # Replace newlines with spaces for terminal display
                        fix_text = fix_text.replace("\n", " ").replace("\r", "")
                        self.console.print(f"     [green]Fix:[/] {fix_text}")
                    
                    self.console.print()
            
            # Section 5 — Analyzer breakdown table
            self.console.print(Rule())
            self.console.print("[bold]Analyzer Breakdown[/]\n")
            
            table = Table(show_header=True, header_style="bold")
            table.add_column("Analyzer", style="bold")
            table.add_column("Findings", justify="center")
            table.add_column("Critical", justify="center")
            table.add_column("High", justify="center")
            table.add_column("Medium", justify="center")
            table.add_column("Low", justify="center")
            table.add_column("Bar", justify="left")
            
            # Find max for bar scaling
            breakdown = self.result.analyzer_breakdown
            max_findings = max(
                (data["total"] for data in breakdown.values()),
                default=1
            )
            if max_findings == 0:
                max_findings = 1
            
            bar_width = 18
            
            for analyzer in ["dependency", "config", "security", "infra", "observability"]:
                data = breakdown.get(analyzer, {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0})
                
                # Build bar
                filled = int((data["total"] / max_findings) * bar_width)
                bar = "█" * filled + "░" * (bar_width - filled)
                
                table.add_row(
                    analyzer,
                    str(data["total"]),
                    f"[red]{data['critical']}[/]",
                    f"[yellow]{data['high']}[/]",
                    f"[blue]{data['medium']}[/]",
                    f"[dim]{data['low']}[/]",
                    bar,
                )
            
            self.console.print(table)
        
        # Section 6 — Footer
        self.console.print()
        self.console.print(Rule())
        self.console.print("[dim]Run with --output html to generate a shareable report.[/]")
        self.console.print("[dim]Run with --output json for CI integration.[/]")
        self.console.print(f"[dim]vibestandard v1.0.1[/]")
        self.console.print(f"[bold blue]Web Experience Coming Soon![/]")
        
        # Fail-on warning
        fail_on = self.options.get("fail_on")
        if fail_on:
            rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            threshold = rank.get(fail_on, 99)
            worst = min(
                (rank[f.severity] for f in self.result.findings),
                default=99
            )
            if worst <= threshold:
                self.console.print()
                self.console.print(
                    f"[bold red]✖  Exiting with code 1 — {fail_on} findings detected (--fail-on {fail_on})[/]"
                )
        
        self.console.print()
        return None

"""
VibeStandard CLI — built with Typer + Rich.
"""

from __future__ import annotations

import time
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from vibestandard import __version__
from vibestandard.ingestion.loader import ingest
from vibestandard.ingestion.file_tree import build_file_tree, detect_ecosystems
from vibestandard.analyzers.rules_loader import load_all_rules, get_rules_for_analyzer
from vibestandard.analyzers.dependency import DependencyAnalyzer

app = typer.Typer(
    name="vibestandard",
    help="AI-Generated Code Production-Readiness Auditor",
    add_completion=False,
)

console = Console()

# ---------------------------------------------------------------------------
# vibestandard scan
# ---------------------------------------------------------------------------

@app.command()
def scan(
    source: str = typer.Argument(
        ...,
        help="Local path, GitHub URL, or ZIP file to scan.",
    ),
    output: str = typer.Option(
        "terminal",
        "--output", "-o",
        help="Output format: terminal, json, or html.",
    ),
    output_file: Optional[str] = typer.Option(
        None,
        "--output-file",
        help="Save report to a file.",
    ),
    severity: Optional[str] = typer.Option(
        None,
        "--severity",
        help="Only show findings at or above this severity (critical|high|medium|low).",
    ),
    fail_on: Optional[str] = typer.Option(
        None,
        "--fail-on",
        help="Exit with code 1 if findings at this severity exist (for CI).",
    ),
    no_semgrep: bool = typer.Option(
        False,
        "--no-semgrep",
        help="Skip semgrep scan (faster, works offline).",
    ),
    no_cve: bool = typer.Option(
        False,
        "--no-cve",
        help="Skip OSV CVE lookups (faster, works offline).",
    ),
) -> None:
    """Scan a codebase for production-readiness issues."""
    start = time.time()

    # --- Ingest ---
    root = ingest(source)

    # --- Build file tree ---
    file_tree = build_file_tree(root)
    ecosystems = detect_ecosystems(file_tree)
    
    # --- Load rules ---
    all_rules = load_all_rules()
    dependency_rules = get_rules_for_analyzer(all_rules, "dependency")
    
    # --- Run Dependency Analyzer ---
    dep_analyzer = DependencyAnalyzer(root, file_tree, dependency_rules)
    findings = dep_analyzer.analyze()
    
    duration = time.time() - start

    # --- Display findings ---
    console.print()
    
    if findings:
        # Sort findings by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        findings.sort(key=lambda f: severity_order.get(f.severity, 4))
        
        # Summary
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in findings:
            severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1
        
        console.print(
            Panel(
                f"[bold]Scanned:[/]  {root}\n"
                f"[bold]Files:[/]    {len(file_tree)} files across "
                f"{len(ecosystems)} ecosystem(s) ({', '.join(ecosystems) if ecosystems else 'none detected'})\n"
                f"[bold]Time:[/]     {duration:.1f}s\n"
                f"[bold]Findings:[/] {len(findings)} issues found\n"
                f"  [red]Critical:[/] {severity_counts['critical']}  "
                f"[bold red]High:[/] {severity_counts['high']}  "
                f"[yellow]Medium:[/] {severity_counts['medium']}  "
                f"[dim]Low:[/] {severity_counts['low']}",
                title="[bold cyan]VibeStandard Scan[/]",
                border_style="cyan",
            )
        )
        console.print()
        
        # Detailed findings
        console.print("[bold]Findings:[/]\n")
        for i, finding in enumerate(findings, 1):
            severity_color = {
                "critical": "red",
                "high": "bold red",
                "medium": "yellow",
                "low": "dim",
            }.get(finding.severity, "white")
            
            console.print(f"[bold]{i}.[/] [{severity_color}]{finding.severity.upper()}[/] {finding.name}")
            console.print(f"   [dim]File:[/] {finding.file}")
            if finding.line:
                console.print(f"   [dim]Line:[/] {finding.line}")
            console.print(f"   [dim]Rule:[/] {finding.rule_id}")
            console.print(f"   {finding.message}")
            if finding.fix:
                console.print(f"   [bold green]Fix:[/] {finding.fix}")
            console.print()
    else:
        console.print(
            Panel(
                f"[bold]Scanned:[/]  {root}\n"
                f"[bold]Files:[/]    {len(file_tree)} files across "
                f"{len(ecosystems)} ecosystem(s) ({', '.join(ecosystems) if ecosystems else 'none detected'})\n"
                f"[bold]Time:[/]     {duration:.1f}s\n"
                f"[bold green]No dependency issues found![/]",
                title="[bold cyan]VibeStandard Scan[/]",
                border_style="cyan",
            )
        )
    
    console.print()


# ---------------------------------------------------------------------------
# vibestandard version
# ---------------------------------------------------------------------------

@app.command()
def version() -> None:
    """Print current version."""
    console.print(f"VibeStandard v{__version__}")


# ---------------------------------------------------------------------------
# vibestandard rules  (sub-group stub)
# ---------------------------------------------------------------------------

rules_app = typer.Typer(
    name="rules",
    help="Manage rule definitions.",
    add_completion=False,
)
app.add_typer(rules_app, name="rules")


@rules_app.command("list")
def rules_list() -> None:
    """List all currently loaded rules."""
    console.print("[dim]Rules listing not yet implemented (Phase 3+).[/]")


@rules_app.command("add")
def rules_add(
    yaml_file: str = typer.Argument(..., help="Path to a custom YAML rules file."),
) -> None:
    """Add a custom rules YAML file."""
    console.print(f"[dim]Adding rules from {yaml_file} — not yet implemented (Phase 3+).[/]")

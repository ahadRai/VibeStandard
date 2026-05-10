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
from vibestandard.analyzers.config import ConfigAnalyzer
from vibestandard.analyzers.security import SecurityAnalyzer
from vibestandard.analyzers.infra import InfraAnalyzer
from vibestandard.analyzers.observability import ObservabilityAnalyzer
from vibestandard.engine.scorer import ScoringEngine

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
    config_rules = get_rules_for_analyzer(all_rules, "config")
    
    # --- Run Dependency Analyzer ---
    dep_analyzer = DependencyAnalyzer(root, file_tree, dependency_rules)
    dep_findings = dep_analyzer.analyze()
    
    # --- Run Config Analyzer ---
    cfg_analyzer = ConfigAnalyzer(root, file_tree, config_rules)
    cfg_findings = cfg_analyzer.analyze()
    
    # --- Run Security Analyzer ---
    security_options = {"use_semgrep": not no_semgrep}
    sec_analyzer = SecurityAnalyzer(root, file_tree, {}, options=security_options)
    sec_findings = sec_analyzer.analyze()
    
    # --- Run Infra Analyzer ---
    infra_analyzer = InfraAnalyzer(root, file_tree, {})
    infra_findings = infra_analyzer.analyze()
    
    # --- Run Observability Analyzer ---
    obs_analyzer = ObservabilityAnalyzer(root, file_tree, {})
    obs_findings = obs_analyzer.analyze()
    
    # --- Combine all findings ---
    all_findings = dep_findings + cfg_findings + sec_findings + infra_findings + obs_findings
    analyzer_errors = []  # Will be populated if any analyzer fails
    
    # --- Run Scoring Engine ---
    metadata = {
        "scanned_path": str(root),
        "ecosystems": list(ecosystems),
        "total_files": len(file_tree),
        "duration_seconds": 0.0,  # Will be updated after timing
        "skipped_files": 0,
        "analyzer_errors": analyzer_errors
    }
    
    engine = ScoringEngine()
    result = engine.score(all_findings, metadata)
    
    duration = time.time() - start
    result.duration_seconds = duration
    metadata["duration_seconds"] = duration

    # --- Display findings ---
    console.print()
    
    if result.findings:
        console.print(
            Panel(
                f"[bold]Scanned:[/]  {result.scanned_path}\n"
                f"[bold]Files:[/]    {result.total_files} files across "
                f"{len(result.ecosystems)} ecosystem(s) ({', '.join(result.ecosystems) if result.ecosystems else 'none detected'})\n"
                f"[bold]Time:[/]     {result.duration_seconds:.1f}s\n"
                f"[bold]Score:[/]    {result.score}/100 (Grade: {result.grade})\n"
                f"[bold]Verdict:[/]  {result.vibe_label}\n"
                f"[bold]Findings:[/] {result.summary['total']} issues found\n"
                f"  [red]Critical:[/] {result.summary['critical']}  "
                f"[bold red]High:[/] {result.summary['high']}  "
                f"[yellow]Medium:[/] {result.summary['medium']}  "
                f"[dim]Low:[/] {result.summary['low']}",
                title="[bold cyan]VibeStandard Scan[/]",
                border_style="cyan",
            )
        )
        console.print()
        
        # Show score adjustments if any
        if result.adjustments_applied:
            console.print("[bold]Score Adjustments:[/]")
            for adj in result.adjustments_applied:
                delta_str = f"+{adj['delta']}" if adj['delta'] > 0 else str(adj['delta'])
                console.print(f"  {adj['reason']}: [{ 'green' if adj['delta'] > 0 else 'red'}]{delta_str}[/]")
            console.print()
        
        # Detailed findings
        console.print("[bold]Findings:[/]\n")
        for i, finding in enumerate(result.findings, 1):
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
            console.print(f"   [dim]Analyzer:[/] {finding.analyzer}")
            console.print(f"   {finding.message}")
            if finding.fix:
                console.print(f"   [bold green]Fix:[/] {finding.fix}")
            console.print()
    else:
        console.print(
            Panel(
                f"[bold]Scanned:[/]  {result.scanned_path}\n"
                f"[bold]Files:[/]    {result.total_files} files across "
                f"{len(result.ecosystems)} ecosystem(s) ({', '.join(result.ecosystems) if result.ecosystems else 'none detected'})\n"
                f"[bold]Time:[/]     {result.duration_seconds:.1f}s\n"
                f"[bold]Score:[/]    {result.score}/100 (Grade: {result.grade})\n"
                f"[bold]Verdict:[/]  {result.vibe_label}\n"
                f"[bold green]No issues found![/]",
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

"""
VibeStandard CLI — built with Typer + Rich.
"""

from __future__ import annotations

import time
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

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
from vibestandard.reporters.cli_reporter import TerminalReporter
from vibestandard.reporters.json_reporter import JsonReporter
from vibestandard.reporters.html_reporter import HtmlReporter

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
    
    # --- Run analyzers with progress bar ---
    all_findings = []
    analyzer_errors = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        # Task 1: Dependency Analyzer
        task1 = progress.add_task("Running dependency analyzer...", total=None)
        try:
            dep_analyzer = DependencyAnalyzer(root, file_tree, dependency_rules, ecosystems=list(ecosystems))
            dep_findings = dep_analyzer.analyze()
            all_findings.extend(dep_findings)
        except Exception as e:
            analyzer_errors.append({"analyzer": "dependency", "error": str(e)})
        progress.update(task1, description="[green]✓[/] Dependency analyzer complete")
        
        # Task 2: Config Analyzer
        task2 = progress.add_task("Running config analyzer...", total=None)
        try:
            cfg_analyzer = ConfigAnalyzer(root, file_tree, config_rules, ecosystems=list(ecosystems))
            cfg_findings = cfg_analyzer.analyze()
            all_findings.extend(cfg_findings)
        except Exception as e:
            analyzer_errors.append({"analyzer": "config", "error": str(e)})
        progress.update(task2, description="[green]✓[/] Config analyzer complete")
        
        # Task 3: Security Analyzer
        task3 = progress.add_task("Running security analyzer...", total=None)
        try:
            security_options = {"use_semgrep": not no_semgrep}
            sec_analyzer = SecurityAnalyzer(root, file_tree, {}, options=security_options, ecosystems=list(ecosystems))
            sec_findings = sec_analyzer.analyze()
            all_findings.extend(sec_findings)
        except Exception as e:
            analyzer_errors.append({"analyzer": "security", "error": str(e)})
        progress.update(task3, description="[green]✓[/] Security analyzer complete")
        
        # Task 4: Infra Analyzer
        task4 = progress.add_task("Running infra analyzer...", total=None)
        try:
            infra_analyzer = InfraAnalyzer(root, file_tree, {}, ecosystems=list(ecosystems))
            infra_findings = infra_analyzer.analyze()
            all_findings.extend(infra_findings)
        except Exception as e:
            analyzer_errors.append({"analyzer": "infra", "error": str(e)})
        progress.update(task4, description="[green]✓[/] Infra analyzer complete")
        
        # Task 5: Observability Analyzer
        task5 = progress.add_task("Running observability analyzer...", total=None)
        try:
            obs_analyzer = ObservabilityAnalyzer(root, file_tree, {}, ecosystems=list(ecosystems))
            obs_findings = obs_analyzer.analyze()
            all_findings.extend(obs_findings)
        except Exception as e:
            analyzer_errors.append({"analyzer": "observability", "error": str(e)})
        progress.update(task5, description="[green]✓[/] Observability analyzer complete")
    
    # --- Run Scoring Engine ---
    metadata = {
        "scanned_path": str(root),
        "ecosystems": list(ecosystems),
        "total_files": len(file_tree),
        "duration_seconds": 0.0,
        "skipped_files": 0,
        "analyzer_errors": analyzer_errors
    }
    
    engine = ScoringEngine()
    result = engine.score(all_findings, metadata)
    
    duration = time.time() - start
    result.duration_seconds = duration
    metadata["duration_seconds"] = duration

    # --- Render using selected reporter ---
    reporters = {
        "terminal": TerminalReporter,
        "json": JsonReporter,
        "html": HtmlReporter,
    }
    
    reporter_class = reporters.get(output, TerminalReporter)
    reporter = reporter_class(result=result, options={
        "severity_filter": severity,
        "output_file": output_file,
        "fail_on": fail_on,
    })
    reporter.render()
    
    # --- Handle --fail-on exit code ---
    if fail_on:
        rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        threshold = rank[fail_on]
        worst = min((rank[f.severity] for f in result.findings), default=99)
        if worst <= threshold:
            raise typer.Exit(code=1)


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

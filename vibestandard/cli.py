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
    duration = time.time() - start

    # --- Summary (Phase 2 output — analyzers not wired yet) ---
    eco_str = ", ".join(ecosystems) if ecosystems else "none detected"
    console.print()
    console.print(
        Panel(
            f"[bold]Scanned:[/]  {root}\n"
            f"[bold]Files:[/]    {len(file_tree)} files across "
            f"{len(ecosystems)} ecosystem(s) ({eco_str})\n"
            f"[bold]Time:[/]     {duration:.1f}s",
            title="[bold cyan]VibeStandard Scan[/]",
            border_style="cyan",
        )
    )
    console.print(
        "[dim]Analyzers not yet wired — run again after Phase 3+.[/]\n"
    )


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

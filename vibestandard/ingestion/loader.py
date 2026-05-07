"""
Ingestion loader — resolves a source string (local path, GitHub URL, or ZIP file)
into a local directory Path that the analyzers can work with.
"""

from __future__ import annotations

import re
import sys
import tempfile
import zipfile
from pathlib import Path

from rich.console import Console

console = Console(stderr=True)

# Pattern to recognise GitHub URLs (https or git@ style)
_GITHUB_RE = re.compile(
    r"^(https?://github\.com/[\w.\-]+/[\w.\-]+(?:\.git)?)"
    r"|^(git@github\.com:[\w.\-]+/[\w.\-]+(?:\.git)?)$"
)


def _is_github_url(source: str) -> bool:
    return bool(_GITHUB_RE.match(source))


def _is_zip_file(source: str) -> bool:
    return Path(source).suffix.lower() == ".zip" and Path(source).is_file()


def _clone_github(url: str) -> Path:
    """Clone a GitHub repo to a temporary directory and return its path."""
    try:
        import git  # gitpython
    except ImportError:
        console.print(
            "[bold red]Error:[/] gitpython is not installed. "
            "Install it with: pip install gitpython"
        )
        sys.exit(1)

    tmp_dir = Path(tempfile.mkdtemp(prefix="vibestandard_"))
    console.print(f"[cyan]Cloning[/] {url} → {tmp_dir} …")

    try:
        git.Repo.clone_from(url, str(tmp_dir), depth=1)
    except git.exc.GitCommandError as exc:
        console.print(f"[bold red]Clone failed:[/] {exc}")
        sys.exit(1)

    console.print("[green]Clone complete.[/]")
    return tmp_dir


def _extract_zip(zip_path: str) -> Path:
    """Extract a ZIP file to a temporary directory and return its path."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="vibestandard_"))
    console.print(f"[cyan]Extracting[/] {zip_path} → {tmp_dir} …")

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)
    except (zipfile.BadZipFile, OSError) as exc:
        console.print(f"[bold red]ZIP extraction failed:[/] {exc}")
        sys.exit(1)

    # If the ZIP contains a single top-level directory, descend into it
    children = list(tmp_dir.iterdir())
    if len(children) == 1 and children[0].is_dir():
        return children[0]

    console.print("[green]Extraction complete.[/]")
    return tmp_dir


def ingest(source: str) -> Path:
    """
    Resolve *source* to a local directory ``Path``.

    Supported source types:
    * Local directory path
    * GitHub HTTPS / SSH URL
    * Path to a ``.zip`` file
    """
    # 1. GitHub URL
    if _is_github_url(source):
        return _clone_github(source)

    # 2. ZIP file
    if _is_zip_file(source):
        return _extract_zip(source)

    # 3. Local path
    local = Path(source).resolve()
    if not local.exists():
        console.print(f"[bold red]Error:[/] path does not exist: {local}")
        sys.exit(1)
    if not local.is_dir():
        console.print(f"[bold red]Error:[/] path is not a directory: {local}")
        sys.exit(1)

    return local

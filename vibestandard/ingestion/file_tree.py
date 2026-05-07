"""
File-tree walker — builds a filtered, sorted list of project files
and detects which ecosystems are present.
"""

from __future__ import annotations

from pathlib import Path

import pathspec

# Directories that are always excluded, regardless of .gitignore
_ALWAYS_EXCLUDE_DIRS: set[str] = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
    ".mypy_cache",
    ".tox",
    "dist",
    "build",
    ".eggs",
    "*.egg-info",
}

# Binary extensions we never attempt to read as text
BINARY_EXTENSIONS: set[str] = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib", ".class", ".jar", ".war",
    ".pyc", ".pyo", ".o", ".a",
    ".mp3", ".mp4", ".avi", ".mov", ".wav", ".flac",
    ".sqlite", ".db",
}

# Mapping: ecosystem name → set of marker filenames
_ECOSYSTEM_MARKERS: dict[str, set[str]] = {
    "java": {
        "pom.xml", "build.gradle", "build.gradle.kts",
        "settings.gradle", "settings.gradle.kts",
    },
    "python": {
        "requirements.txt", "pyproject.toml", "setup.py",
        "setup.cfg", "Pipfile", "Pipfile.lock",
    },
    "node": {
        "package.json", "package-lock.json", "yarn.lock",
        "pnpm-lock.yaml", "tsconfig.json",
    },
    "docker": {
        "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
        ".dockerignore",
    },
}

# File extensions that also signal an ecosystem
_ECOSYSTEM_EXTENSIONS: dict[str, set[str]] = {
    "java": {".java", ".kt", ".kts"},
    "python": {".py"},
    "node": {".js", ".ts", ".jsx", ".tsx"},
}


def _load_gitignore_spec(root: Path) -> pathspec.PathSpec | None:
    """Load .gitignore patterns from project root, if present."""
    gitignore = root / ".gitignore"
    if gitignore.is_file():
        try:
            lines = gitignore.read_text(encoding="utf-8").splitlines()
            return pathspec.PathSpec.from_lines("gitwildmatch", lines)
        except Exception:
            return None
    return None


def _is_excluded_dir(name: str) -> bool:
    """Check whether a directory name matches the always-exclude list."""
    return name in _ALWAYS_EXCLUDE_DIRS or name.endswith(".egg-info")


def build_file_tree(root: Path) -> list[Path]:
    """
    Walk *root* recursively and return a sorted list of **relative** ``Path``
    objects, filtering out ignored and binary files.
    """
    root = root.resolve()
    gitignore_spec = _load_gitignore_spec(root)
    result: list[Path] = []

    for item in sorted(root.rglob("*")):
        # Skip directories themselves — we only want files
        if item.is_dir():
            continue

        rel = item.relative_to(root)

        # Skip if any parent directory is in the exclude list
        if any(_is_excluded_dir(part) for part in rel.parts[:-1]):
            continue

        # Skip binary files
        if item.suffix.lower() in BINARY_EXTENSIONS:
            continue

        # Skip if matched by .gitignore
        if gitignore_spec and gitignore_spec.match_file(str(rel)):
            continue

        result.append(rel)

    return result


def detect_ecosystems(file_tree: list[Path]) -> list[str]:
    """
    Scan file names in *file_tree* and return a sorted list of detected
    ecosystem names (e.g. ``["docker", "java", "python"]``).
    """
    detected: set[str] = set()

    for rel_path in file_tree:
        name = rel_path.name

        # Check marker filenames
        for eco, markers in _ECOSYSTEM_MARKERS.items():
            if name in markers:
                detected.add(eco)

        # Check file extensions
        suffix = rel_path.suffix.lower()
        for eco, exts in _ECOSYSTEM_EXTENSIONS.items():
            if suffix in exts:
                detected.add(eco)

    # Also detect Dockerfile variants like "Dockerfile.prod"
    for rel_path in file_tree:
        if rel_path.name.startswith("Dockerfile"):
            detected.add("docker")
            break

    return sorted(detected)

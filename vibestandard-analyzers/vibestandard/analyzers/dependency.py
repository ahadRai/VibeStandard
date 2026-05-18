"""
Dependency Analyzer — scans dependency manifest files for production-readiness issues.

Checks for:
- In-memory/test databases (H2, HSQLDB, Derby, SQLite)
- Unpinned dependencies (latest, *, no version)
- Dev dependencies in production bundles
- Missing lock files
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from vibestandard.analyzers.base import BaseAnalyzer
from vibestandard.models import Finding


# Dev-only packages for Node.js ecosystem
_NODE_DEV_PACKAGES = {
    "nodemon", "webpack-dev-server", "jest", "mocha", "eslint",
    "prettier", "ts-node", "tsx", "vitest", "@types/node",
    "typescript", "babel", "webpack", "vite", "rollup",
}

# Dev-only packages for Python ecosystem
_PYTHON_DEV_PACKAGES = {
    "pytest", "coverage", "black", "isort", "flake8", "pylint",
    "mypy", "ipython", "ipdb", "pdb", "bandit", "debugpy",
    "pytest-cov", "pytest-asyncio", "tox", "sphinx",
}


class DependencyAnalyzer(BaseAnalyzer):
    """Analyzes dependency manifest files for production-readiness issues."""
    
    name = "dependency"
    ecosystem = "generic"  # Will be set per-file
    
    def analyze(self) -> list[Finding]:
        """Run all dependency checks across all ecosystems."""
        self._check_java_dependencies()
        self._check_node_dependencies()
        self._check_python_dependencies()
        return self.findings
    
    def _check_java_dependencies(self) -> None:
        """Check Java dependency files (pom.xml, build.gradle)."""
        # Check for H2, HSQLDB, Derby in pom.xml and build.gradle
        java_files = [
            f for f in self.file_tree
            if f.name in {"pom.xml", "build.gradle", "build.gradle.kts"}
        ]
        
        for rel_path in java_files:
            abs_path = self.root / rel_path
            content = self.read_file_safe(abs_path)
            if not content:
                continue
            
            # Apply all Java dependency rules
            for rule_id, rule in self.rules.items():
                if rule.get("analyzer") != "dependency":
                    continue
                if rule.get("ecosystem") != "java":
                    continue
                
                match_config = rule.get("match", {})
                file_patterns = match_config.get("files", [])
                
                # Check if this file matches the rule's file patterns
                if not self._matches_file_pattern(rel_path.name, file_patterns):
                    continue
                
                pattern_str = match_config.get("pattern", "")
                if not pattern_str:
                    continue
                
                try:
                    pattern = re.compile(pattern_str, re.MULTILINE)
                    if pattern.search(content):
                        self.add_finding(rule_id, str(rel_path))
                except re.error:
                    continue
    
    def _check_node_dependencies(self) -> None:
        """Check Node.js dependency files (package.json)."""
        package_json_files = [
            f for f in self.file_tree if f.name == "package.json"
        ]
        
        for rel_path in package_json_files:
            abs_path = self.root / rel_path
            content = self.read_file_safe(abs_path)
            if not content:
                continue
            
            try:
                pkg_data = json.loads(content)
            except json.JSONDecodeError:
                continue
            
            # Check for unpinned versions
            self._check_node_unpinned_versions(pkg_data, rel_path)
            
            # Check for dev dependencies in production
            self._check_node_dev_in_prod(pkg_data, rel_path)
        
        # Check for missing lock file
        self._check_node_lock_file()
    
    def _check_python_dependencies(self) -> None:
        """Check Python dependency files (requirements.txt, pyproject.toml, Pipfile)."""
        python_dep_files = [
            f for f in self.file_tree
            if f.name in {"requirements.txt", "pyproject.toml", "Pipfile", "setup.py", "setup.cfg"}
        ]
        
        # Track which rules have been triggered to avoid duplicates
        triggered_rules = set()
        
        for rel_path in python_dep_files:
            abs_path = self.root / rel_path
            content = self.read_file_safe(abs_path)
            if not content:
                continue
            
            # Check for dev packages in requirements.txt
            if rel_path.name == "requirements.txt":
                self._check_python_dev_in_prod(rel_path, content, triggered_rules)
            
            # Check for unpinned versions in requirements.txt
            if rel_path.name == "requirements.txt":
                self._check_python_unpinned_versions(rel_path, content, triggered_rules)
            
            # Apply other YAML rules for python ecosystem
            self._apply_yaml_rules_for_file_safe(rel_path, "python", triggered_rules)
    
    def _check_node_unpinned_versions(self, pkg_data: dict, rel_path: Path) -> None:
        """Check for dependencies pinned to 'latest' or '*'."""
        dependencies = pkg_data.get("dependencies", {})
        
        has_unpinned = False
        for dep_name, version in dependencies.items():
            if version in ("latest", "*"):
                has_unpinned = True
                break
        
        if has_unpinned:
            # Add finding only once per file
            for rule_id, rule in self.rules.items():
                if rule.get("id") == "unpinned-version-node":
                    self.add_finding(rule_id, str(rel_path))
                    break
    
    def _check_node_dev_in_prod(self, pkg_data: dict, rel_path: Path) -> None:
        """Check for dev packages in production dependencies."""
        dependencies = pkg_data.get("dependencies", {})
        
        dev_in_prod = []
        for dep_name in dependencies:
            if dep_name in _NODE_DEV_PACKAGES or dep_name.lower() in _NODE_DEV_PACKAGES:
                dev_in_prod.append(dep_name)
        
        if dev_in_prod:
            # Add finding only once per file
            for rule_id, rule in self.rules.items():
                if rule.get("id") == "dev-dep-in-prod-node":
                    self.add_finding(rule_id, str(rel_path))
                    break
    
    def _check_node_lock_file(self) -> None:
        """Check if a Node.js project has a lock file."""
        has_package_json = any(f.name == "package.json" for f in self.file_tree)
        has_lock_file = any(
            f.name in {"package-lock.json", "yarn.lock", "pnpm-lock.yaml"}
            for f in self.file_tree
        )
        
        if has_package_json and not has_lock_file:
            # Add finding only once
            for rule_id, rule in self.rules.items():
                if rule.get("id") == "no-lock-file":
                    # Find the package.json file to report
                    for f in self.file_tree:
                        if f.name == "package.json":
                            self.add_finding(rule_id, str(f))
                            return
    
    def _check_python_dev_in_prod(self, rel_path: Path, content: str, triggered_rules: set) -> None:
        """Check for dev packages in production requirements."""
        lines = content.strip().split('\n')
        
        dev_in_prod = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Extract package name (before any version specifier)
            pkg_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
            if pkg_name.lower() in _PYTHON_DEV_PACKAGES:
                dev_in_prod.append(pkg_name)
        
        if dev_in_prod and "dev-dep-in-prod-python" not in triggered_rules:
            for rule_id, rule in self.rules.items():
                if rule.get("id") == "dev-dep-in-prod-python":
                    self.add_finding(rule_id, str(rel_path))
                    triggered_rules.add(rule_id)
                    break
    
    def _check_python_unpinned_versions(self, rel_path: Path, content: str, triggered_rules: set) -> None:
        """Check for unpinned versions in requirements.txt."""
        lines = content.strip().split('\n')
        
        has_unpinned = False
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Check if line has no version specifier
            if '==' not in line and '>=' not in line and '<=' not in line and '~=' not in line:
                has_unpinned = True
                break
        
        if has_unpinned and "unpinned-version-python" not in triggered_rules:
            for rule_id, rule in self.rules.items():
                if rule.get("id") == "unpinned-version-python":
                    self.add_finding(rule_id, str(rel_path))
                    triggered_rules.add(rule_id)
                    break
    
    def _apply_yaml_rules_for_file_safe(self, rel_path: Path, ecosystem: str, triggered_rules: set) -> None:
        """Apply YAML rules to a specific file, avoiding duplicates."""
        abs_path = self.root / rel_path
        content = self.read_file_safe(abs_path)
        if not content:
            return
        
        for rule_id, rule in self.rules.items():
            if rule_id in triggered_rules:
                continue
            if rule.get("analyzer") != "dependency":
                continue
            if rule.get("ecosystem") != ecosystem:
                continue
            
            match_config = rule.get("match", {})
            file_patterns = match_config.get("files", [])
            
            # Check if this file matches the rule's file patterns
            if not self._matches_file_pattern(rel_path.name, file_patterns):
                continue
            
            pattern_str = match_config.get("pattern", "")
            if not pattern_str:
                continue
            
            try:
                pattern = re.compile(pattern_str, re.MULTILINE)
                if pattern.search(content):
                    self.add_finding(rule_id, str(rel_path))
                    triggered_rules.add(rule_id)
            except re.error:
                continue
    
    def _matches_file_pattern(self, filename: str, patterns: list[str]) -> bool:
        """Check if a filename matches any of the given patterns."""
        for pattern in patterns:
            # Convert glob pattern to regex
            regex_pattern = pattern.replace(".", r"\.").replace("*", ".*")
            if re.fullmatch(regex_pattern, filename):
                return True
        return False

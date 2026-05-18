"""
Config Analyzer — scans configuration files for production-readiness issues.

Checks for:
- Test databases in config (H2, SQLite connection strings)
- Debug mode enabled (DEBUG=True, debug: true)
- Hardcoded secrets, passwords, API keys
- Dangerous DDL settings (create-drop)
- CORS misconfigurations (wildcard origins)
- ALLOWED_HOSTS wildcard in Django
"""

from __future__ import annotations

import re
from pathlib import Path

from vibestandard.analyzers.base import BaseAnalyzer
from vibestandard.models import Finding


# Config file patterns by ecosystem
_CONFIG_FILE_PATTERNS = {
    "java": {
        "application.properties",
        "application.yml",
        "application.yaml",
        "application-*.properties",
        "application-*.yml",
        "application-*.yaml",
    },
    "python": {
        "settings.py",
        "config.py",
        ".env",
        ".env.*",
        "*.cfg",
        "*.ini",
    },
    "node": {
        ".env",
        ".env.*",
        "config.js",
        "config.ts",
        "config.json",
        "*.config.js",
        "*.config.ts",
    },
    "generic": {
        ".env",
        "docker-compose.yml",
        "docker-compose.yaml",
        "appsettings.json",
        "appsettings.*.json",
    },
}


class ConfigAnalyzer(BaseAnalyzer):
    """Analyzes configuration files for production-readiness issues."""
    
    name = "config"
    ecosystem = "generic"
    
    def analyze(self) -> list[Finding]:
        """Run all config checks across all ecosystems."""
        # Track findings to avoid duplicates
        self._apply_config_rules()
        return self.findings
    
    def _apply_config_rules(self) -> None:
        """Apply all config analyzer rules from loaded YAML rules."""
        # Get all config rules
        config_rules = {
            rule_id: rule
            for rule_id, rule in self.rules.items()
            if rule.get("analyzer") == "config"
        }
        
        # Group rules by ecosystem
        rules_by_ecosystem: dict[str, dict] = {}
        for rule_id, rule in config_rules.items():
            eco = rule.get("ecosystem", "generic")
            if eco not in rules_by_ecosystem:
                rules_by_ecosystem[eco] = {}
            rules_by_ecosystem[eco][rule_id] = rule
        
        # Apply rules for each ecosystem
        for ecosystem, rules in rules_by_ecosystem.items():
            self._apply_rules_for_ecosystem(ecosystem, rules)
    
    def _apply_rules_for_ecosystem(self, ecosystem: str, rules: dict[str, dict]) -> None:
        """Apply config rules for a specific ecosystem."""
        # Apply each rule to matching files
        for rule_id, rule in rules.items():
            match_config = rule.get("match", {})
            file_patterns = match_config.get("files", [])
            
            # Find all files that match this rule's patterns
            for rel_path in self.file_tree:
                if self._matches_file_pattern(rel_path.name, file_patterns):
                    abs_path = self.root / rel_path
                    content = self.read_file_safe(abs_path)
                    if content:
                        self._apply_rule_to_file(rule_id, rule, rel_path, content)
    
    def _find_config_files_for_ecosystem(self, ecosystem: str) -> list[Path]:
        """Find all config files that match an ecosystem's patterns."""
        patterns = _CONFIG_FILE_PATTERNS.get(ecosystem, set())
        matching_files = []
        
        for rel_path in self.file_tree:
            filename = rel_path.name
            
            # Check exact matches
            if filename in patterns:
                matching_files.append(rel_path)
                continue
            
            # Check glob patterns (e.g., "application-*.properties")
            for pattern in patterns:
                if "*" in pattern:
                    # Convert glob to regex
                    regex_pattern = pattern.replace(".", r"\.").replace("*", ".*")
                    if re.fullmatch(regex_pattern, filename):
                        matching_files.append(rel_path)
                        break
        
        return matching_files
    
    def _apply_rule_to_file(
        self,
        rule_id: str,
        rule: dict,
        rel_path: Path,
        content: str,
    ) -> None:
        """Apply a single rule to a file's content."""
        match_config = rule.get("match", {})
        file_patterns = match_config.get("files", [])
        
        # Check if this file matches the rule's file patterns
        if not self._matches_file_pattern(rel_path.name, file_patterns):
            return
        
        pattern_str = match_config.get("pattern", "")
        if not pattern_str:
            return
        
        try:
            pattern = re.compile(pattern_str, re.MULTILINE)
            if pattern.search(content):
                self.add_finding(rule_id, str(rel_path))
        except re.error:
            # Invalid regex pattern, skip
            return
    
    def _matches_file_pattern(self, filename: str, patterns: list[str]) -> bool:
        """Check if a filename matches any of the given glob patterns."""
        for pattern in patterns:
            # Convert glob pattern to regex
            regex_pattern = pattern.replace(".", r"\.").replace("*", ".*")
            if re.fullmatch(regex_pattern, filename):
                return True
        return False

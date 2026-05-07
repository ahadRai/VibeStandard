"""
YAML rules loader — loads rule definitions from YAML files in the rules/ directory.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml


def _load_rules_from_file(file_path: Path) -> list[dict]:
    """Load rules from a single YAML file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            rules = yaml.safe_load(f)
        if not isinstance(rules, list):
            return []
        return rules
    except Exception:
        return []


def load_all_rules(rules_dir: Path | None = None) -> dict[str, dict]:
    """
    Load all rule definitions from YAML files in the rules directory.
    
    Returns a dictionary mapping rule_id -> rule_dict for fast lookup.
    """
    if rules_dir is None:
        # Default to the rules/ directory next to this package
        rules_dir = Path(__file__).parent.parent.parent / "rules"
    
    if not rules_dir.is_dir():
        return {}
    
    all_rules: dict[str, dict] = {}
    
    for yaml_file in sorted(rules_dir.glob("*.yaml")):
        rules = _load_rules_from_file(yaml_file)
        for rule in rules:
            if "id" in rule:
                all_rules[rule["id"]] = rule
    
    return all_rules


def get_rules_for_analyzer(rules: dict[str, dict], analyzer: str) -> dict[str, dict]:
    """Filter rules to only those belonging to a specific analyzer."""
    return {
        rule_id: rule
        for rule_id, rule in rules.items()
        if rule.get("analyzer") == analyzer
    }


def get_rules_for_ecosystem(rules: dict[str, dict], ecosystem: str) -> dict[str, dict]:
    """Filter rules to only those belonging to a specific ecosystem."""
    return {
        rule_id: rule
        for rule_id, rule in rules.items()
        if rule.get("ecosystem") == ecosystem
    }


def compile_rule_patterns(rules: dict[str, dict]) -> dict[str, re.Pattern | None]:
    """
    Pre-compile regex patterns for all rules.
    Returns a dict mapping rule_id -> compiled pattern (or None if pattern is invalid).
    """
    compiled: dict[str, re.Pattern | None] = {}
    
    for rule_id, rule in rules.items():
        pattern_str = rule.get("match", {}).get("pattern", "")
        if not pattern_str:
            compiled[rule_id] = None
            continue
        
        try:
            compiled[rule_id] = re.compile(pattern_str, re.MULTILINE)
        except re.error:
            # Invalid regex — will be skipped during analysis
            compiled[rule_id] = None
    
    return compiled

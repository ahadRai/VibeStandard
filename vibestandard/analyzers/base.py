from abc import ABC, abstractmethod
from pathlib import Path
from vibestandard.models import Finding

class BaseAnalyzer(ABC):
    name: str
    ecosystem: str

    def __init__(self, root: Path, file_tree: list[Path], rules: dict, options: dict | None = None):
        self.root = root
        self.file_tree = file_tree
        self.rules = rules
        self.findings: list[Finding] = []
        self.options = options or {}

    @abstractmethod
    def analyze(self) -> list[Finding]:
        pass

    def add_finding(self, rule_id: str, file: str, line: int | None = None) -> None:
        """
        Looks up the rule from self.rules by rule_id and creates a Finding.
        Adds the finding to self.findings list.
        """
        rule = self.rules.get(rule_id)
        if not rule:
            return
        
        finding = Finding(
            rule_id=rule_id,
            name=rule.get("name", "Unknown"),
            severity=rule.get("severity", "low"),
            message=rule.get("message", ""),
            fix=rule.get("fix", ""),
            file=file,
            line=line,
            analyzer=self.name,
            ecosystem=self.ecosystem,
        )
        self.findings.append(finding)

    def read_file_safe(self, path: Path) -> str | None:
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            # Returns None on encoding errors or permission errors
            # Never raises an exception
            return None

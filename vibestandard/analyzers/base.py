from abc import ABC, abstractmethod
from pathlib import Path
from vibestandard.models import Finding

class BaseAnalyzer(ABC):
    name: str
    ecosystem: str

    def __init__(self, root: Path, file_tree: list[Path], rules: dict):
        self.root = root
        self.file_tree = file_tree
        self.rules = rules
        self.findings: list[Finding] = []

    @abstractmethod
    def analyze(self) -> list[Finding]:
        pass

    def add_finding(self, rule_id, file, line=None):
        # Looks up the rule from self.rules by rule_id and creates a Finding
        pass

    def read_file_safe(self, path: Path) -> str | None:
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            # Returns None on encoding errors or permission errors
            # Never raises an exception
            return None

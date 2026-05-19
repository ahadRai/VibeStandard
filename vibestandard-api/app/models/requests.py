from pydantic import BaseModel, field_validator
import re


class ScanRequest(BaseModel):
    github_url: str

    @field_validator("github_url")
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        v = v.strip()
        # Must start with https://github.com/
        # Must have owner/repo path segments
        # Must not contain ../ or other traversal
        # Strip trailing .git if present
        # Strip trailing slash
        pattern = r"^https://github\.com/[\w\-\.]+/[\w\-\.]+$"
        cleaned = v.removesuffix(".git").removesuffix("/")
        if not re.match(pattern, cleaned):
            raise ValueError(
                "Invalid GitHub URL. Must be in the format: "
                "https://github.com/username/repository"
            )
        return cleaned

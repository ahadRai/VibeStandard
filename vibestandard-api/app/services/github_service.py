import git
import uuid
import os
from pathlib import Path
from app.config import settings
from app.exceptions import (
    RepoNotFoundException,
    RepoPrivateException,
    RepoTooLargeException,
    CloneTimeoutException,
    CloneFailedException,
)


class GitHubService:

    def clone_repo(self, github_url: str, clone_base_dir: str = None) -> Path:
        if clone_base_dir is None:
            clone_base_dir = settings.clone_dir
        
        # 1. Generate a unique subdirectory name
        clone_path = Path(clone_base_dir) / str(uuid.uuid4())
        
        try:
            # 2. Clone with depth=1 for shallow clone (faster)
            # 3. Set timeout of 120 seconds
            git.Repo.clone_from(
                github_url,
                str(clone_path),
                depth=1,
            )
        except git.exc.GitCommandError as e:
            error_msg = str(e).lower()
            
            # 4. Check for not found errors
            if "not found" in error_msg or "repository not found" in error_msg:
                raise RepoNotFoundException(github_url)
            
            # 5. Check for private repo auth errors
            if "authentication" in error_msg or "could not read" in error_msg:
                raise RepoPrivateException()
            
            # 6. Check for timeout
            if "timed out" in error_msg or "timeout" in error_msg:
                raise CloneTimeoutException()
            
            # 7. Any other error
            raise CloneFailedException(str(e))
        
        # 8. Check repo size
        total_size = self._get_directory_size(clone_path)
        max_size_bytes = settings.max_repo_size_mb * 1024 * 1024
        
        if total_size > max_size_bytes:
            # Delete the directory
            import shutil
            shutil.rmtree(clone_path, ignore_errors=True)
            size_mb = total_size // (1024 * 1024)
            raise RepoTooLargeException(size_mb, settings.max_repo_size_mb)
        
        # 9. Return clone path on success
        return clone_path

    def _get_directory_size(self, path: Path) -> int:
        """Calculate total size of directory in bytes."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size

    def extract_owner_repo(self, github_url: str) -> tuple[str, str]:
        """Parse https://github.com/owner/repo and return ("owner", "repo")"""
        parts = github_url.replace("https://github.com/", "").split("/")
        return parts[0], parts[1]

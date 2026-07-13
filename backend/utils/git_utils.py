import shutil
from pathlib import Path

import git

from backend.utils.logging import get_logger

logger = get_logger(__name__)


def clone_repository(url: str, dest: Path, branch: str = "main") -> Path:
    """Clone *url* into *dest*. Returns the clone path."""
    if dest.exists():
        logger.info("Removing existing clone at %s", dest)
        shutil.rmtree(dest)

    dest.mkdir(parents=True, exist_ok=True)
    logger.info("Cloning %s (branch=%s) → %s", url, branch, dest)

    try:
        git.Repo.clone_from(url, str(dest), branch=branch, depth=1)
    except git.GitCommandError:
        # Fall back to default branch if the specified branch doesn't exist
        logger.warning("Branch '%s' not found, cloning default branch", branch)
        git.Repo.clone_from(url, str(dest), depth=1)

    return dest


def pull_latest(repo_path: Path) -> None:
    """Pull latest changes for an existing clone."""
    repo = git.Repo(str(repo_path))
    origin = repo.remotes.origin
    origin.pull()
    logger.info("Pulled latest at %s", repo_path)

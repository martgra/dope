from pathlib import Path

from git import Repo

from app.consumers.base import BaseConsumer


class GitConsumer(BaseConsumer):
    """Git consumer."""

    def __init__(self, root_path: Path, base_branch: str):
        """Initialize git consumer.

        Args:
            root_path (Path): Root path of repository.
            base_branch (str): Base branch to diff against.
        """
        self.base_branch = base_branch
        self.repo = self._get_repo(root_path)
        self.root_path = Path(self.repo.git.rev_parse("--show-toplevel"))

    @staticmethod
    def _get_repo(root_path):
        return Repo(root_path, search_parent_directories=True)

    def discover_files(self, branch_name=None):
        """Return list of changed file compared to branch."""
        diff_files = self.repo.git.diff(
            branch_name if branch_name else self.base_branch,
            "--name-only",
            "--",
            ".",
            ":(exclude)*lock*",
        ).splitlines()
        return [Path(rel_path) for rel_path in diff_files]

    def get_content(self, file_path):
        """Return content of changed file."""
        diff = self.repo.git.diff(self.base_branch, "--", str(file_path))
        return diff

    def get_full_content(self, file_path):
        """Return content of code file."""
        code_path = Path(self.repo.working_tree_dir) / file_path

        if code_path.is_file():
            with code_path.open("r") as file:
                return file.read()
        else:
            raise FileNotFoundError(str(code_path))

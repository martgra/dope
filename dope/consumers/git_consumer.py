from pathlib import Path
from typing import Literal

from git import Repo

from dope.consumers.base import BaseConsumer
from dope.models.domain.doc import CodeMetadata


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

    def discover_files(
        self, mode: Literal["diff", "all"] = "diff", branch_name=None, exclude_patterns=None
    ):
        """Discover files in the Git repository.

        Args:
            mode (str): 'diff' to get changed files compared to a branch,
                        'all' to get all committed files.
            branch_name (str, optional): Branch to compare against. Uses base_branch if None.
            exclude_patterns (list[str], optional): List of Git exclude pathspecs.

        Returns:
            list[Path]: List of Path objects for discovered files.
        """
        exclude_patterns = exclude_patterns or [":(exclude)*lock*"]

        if mode == "diff":
            return self._get_diff_files(branch_name, exclude_patterns)
        elif mode == "all":
            return self._get_all_files()
        else:
            raise ValueError(f"Unsupported mode: {mode}")

    def _get_diff_files(self, branch_name, exclude_patterns):
        ref = branch_name if branch_name else self.base_branch
        args = [ref, "--name-only", "--", ".", *exclude_patterns]
        file_list = self.repo.git.diff(*args).splitlines()
        return [Path(path) for path in file_list]

    def _get_all_files(self):
        file_list = self.repo.git.ls_files().splitlines()
        return [Path(path) for path in file_list]

    def get_content(self, file_path) -> bytes:
        """Return diff content of changed file as bytes."""
        diff = self.repo.git.diff(self.base_branch, f"--unified={5}", "--", str(file_path))
        return diff.encode("utf-8")

    def get_full_content(self, file_path):
        """Return content of code file."""
        code_path = Path(self.repo.working_tree_dir) / file_path

        if code_path.is_file():
            with code_path.open("r") as file:
                return file.read()
        else:
            raise FileNotFoundError(str(code_path))

    def _get_lines_of_code(self):
        all_files = self._get_all_files()

        loc = 0
        for p in all_files:
            try:
                for _ in (self.root_path / p).open("r", errors="ignore"):
                    loc += 1
            except (OSError, UnicodeDecodeError):
                continue
        return loc

    def get_metadata(self, branch_name: str | None = None) -> CodeMetadata:
        """Return repo metadata.

        Args:
            branch_name (str, optional): Branch to count commits on. Defaults to None.

        Returns:
            CodeMetadata: metadata about repo.
        """
        commits = list(self.repo.iter_commits(branch_name or self.base_branch))
        contributors = sorted({c.author.email or c.author.name for c in commits})
        branches = [h.name for h in self.repo.heads]
        tags = [t.name for t in self.repo.tags]

        return CodeMetadata(
            commits=len(commits),
            num_contributors=len(contributors),
            branches=branches,
            tags=tags,
            lines_of_code=self._get_lines_of_code(),
        )

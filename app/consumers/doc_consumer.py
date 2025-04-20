import os
from pathlib import Path

from git import InvalidGitRepositoryError, Repo

from app.consumers.base import BaseConsumer
from app.models.internal import FileSuffix


class DocConsumer(BaseConsumer):
    """Doc consumer."""

    def __init__(self, root_path: Path, file_type_filter: set[FileSuffix], exclude_dirs: set[str]):
        """Initialize doc consumer.

        Args:
            root_path (Path): Root path of repository.
            file_type_filter (list[FileSuffix]): File types to include.
            exclude_dirs (list[str]): name of directories to exclude.
        """
        self.filter = ("md", "mdx")
        self.root_path: Path = self._get_root_path(root_path)
        self.exclude_dirs = {"node_modules", ".venv"}
        self.file_type_filter = file_type_filter
        self.exclude_dirs = exclude_dirs

    @staticmethod
    def _get_root_path(root_path) -> Path:
        root_path = Path(root_path)
        if not root_path.is_dir():
            raise NotADirectoryError(f"{root_path} is not a valid directory")
        return root_path

    def discover_files(self, file_filter=None, exclude_dirs=None) -> list[Path]:
        """Returns a list of Path objects."""
        base_dir = self.root_path

        if file_filter is not None:
            combined_filter = self.file_type_filter.union({ext.lower() for ext in file_filter})
        else:
            combined_filter = self.file_type_filter

        if exclude_dirs is not None:
            combined_excludes = self.exclude_dirs.union({d.lower() for d in exclude_dirs})
        else:
            combined_excludes = self.exclude_dirs

        ignored_files = None
        repo_root = None
        try:
            repo = Repo(base_dir, search_parent_directories=True)
            repo_root = Path(repo.working_tree_dir)
            ignored_files = set(
                repo.git.ls_files("--others", "-i", "--exclude-standard").splitlines()
            )
        except (InvalidGitRepositoryError, Exception):
            ignored_files = None

        discovered = []
        for dirpath, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d.lower() not in combined_excludes]
            for file in files:
                file_path = Path(dirpath) / file
                if combined_filter and file_path.suffix.lower() not in combined_filter:
                    continue
                if ignored_files is not None:
                    try:
                        rel_path = file_path.relative_to(repo_root).as_posix()
                    except ValueError:
                        rel_path = None
                    if rel_path and rel_path in ignored_files:
                        continue

                discovered.append(file_path)

        return discovered

    def get_content(self, file_path) -> str:
        """Return content of changed file."""
        with open(file_path) as file:
            return file.read()

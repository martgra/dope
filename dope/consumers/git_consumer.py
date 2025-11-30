import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from git import Repo

from dope.consumers.base import BaseConsumer
from dope.exceptions import DocumentNotFoundError
from dope.models.domain.documentation import CodeMetadata

if TYPE_CHECKING:
    pass

# File patterns for automatic classification
TRIVIAL_FILE_PATTERNS = {
    "test": ["*_test.py", "*.spec.ts", "*.spec.js", "tests/*", "test_*.py", "**/test/**"],
    "lock": ["*.lock", "*.sum", "package-lock.json", "poetry.lock", "Cargo.lock", "yarn.lock"],
    "vendor": ["vendor/*", "node_modules/*", "dist/*", "build/*", ".venv/*", "venv/*"],
    "generated": ["*_pb2.py", "*.pb.go", "*_generated.py", "*.generated.ts"],
    "minified": ["*.min.js", "*.min.css", "*.bundle.js"],
}

DOC_CRITICAL_PATTERNS = {
    "readme": ["README.md", "readme.md", "README.rst"],
    "api_docs": ["docs/api/*", "api/*"],
    "entry_points": ["__init__.py", "index.ts", "index.js", "lib.rs", "main.py", "main.go"],
    "config": ["*.config.js", "*.config.ts", "pyproject.toml", "setup.py", "Cargo.toml"],
}


@dataclass
class FileClassification:
    """Classification of a file based on path analysis."""

    classification: Literal["SKIP", "HIGH", "NORMAL"]
    reason: str
    matched_pattern: str | None = None


@dataclass
class ChangeMagnitude:
    """Magnitude of changes in a file."""

    lines_added: int
    lines_deleted: int
    total_lines: int
    is_rename: bool
    score: float  # 0.0 to 1.0, higher = more significant
    rename_similarity: int | None = None
    related_docs: list[str] = field(default_factory=list)  # Docs mentioning terms from this change

    def __post_init__(self):
        """Initialize mutable default."""
        if self.related_docs is None:
            self.related_docs = []


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
            raise ValueError(f"Unsupported discover_files mode: {mode}. Use 'diff' or 'all'.")

    def _get_diff_files(self, branch_name, exclude_patterns):
        ref = branch_name if branch_name else self.base_branch
        args = [ref, "--name-only", "--", ".", *exclude_patterns]
        file_list = self.repo.git.diff(*args).splitlines()
        return [Path(path) for path in file_list]

    def _get_all_files(self):
        file_list = self.repo.git.ls_files().splitlines()
        return [Path(path) for path in file_list]

    def get_content(self, file_path, normalize_whitespace: bool = False) -> bytes:
        """Return diff content of changed file as bytes.

        Args:
            file_path: Path to the file to get diff for.
            normalize_whitespace: If True, ignore whitespace changes in diff.

        Returns:
            Diff content as bytes.
        """
        args = [self.base_branch, f"--unified={5}"]

        if normalize_whitespace:
            args.extend(["-w", "-b", "--ignore-blank-lines"])

        args.extend(["--", str(file_path)])
        diff = self.repo.git.diff(*args)
        return diff.encode("utf-8")

    def get_normalized_diff(self, file_path) -> bytes:
        """Get whitespace-normalized diff for better comparison.

        This diff ignores:
        - Whitespace changes (-w)
        - Blank line changes (-b)
        - Uses histogram algorithm for better diffs

        Args:
            file_path: Path to the file to get diff for.

        Returns:
            Normalized diff content as bytes.
        """
        diff = self.repo.git.diff(
            self.base_branch,
            "-w",  # ignore whitespace
            "-b",  # ignore blank lines
            "--ignore-blank-lines",
            "--diff-algorithm=histogram",
            f"--unified={5}",
            "--",
            str(file_path),
        )
        return diff.encode("utf-8")

    def get_full_content(self, file_path):
        """Return content of code file."""
        code_path = Path(self.repo.working_tree_dir) / file_path

        if code_path.is_file():
            with code_path.open("r") as file:
                return file.read()
        else:
            raise DocumentNotFoundError(str(code_path))

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

    def classify_file_by_path(self, file_path: Path) -> FileClassification:
        """Fast path-based classification before any LLM processing.

        Classifies files into three categories:
        - SKIP: Trivial files that don't need documentation (tests, locks, vendor)
        - HIGH: Critical files that likely need documentation (README, entry points)
        - NORMAL: Regular files that may need documentation

        Args:
            file_path: Path to classify.

        Returns:
            FileClassification with classification and reasoning.
        """
        path_str = str(file_path).lower()

        # Check for trivial files to skip
        for category, patterns in TRIVIAL_FILE_PATTERNS.items():
            for pattern in patterns:
                if fnmatch.fnmatch(path_str, pattern.lower()):
                    return FileClassification(
                        classification="SKIP",
                        reason=f"Trivial file type: {category}",
                        matched_pattern=pattern,
                    )

        # Check for critical files to prioritize
        for category, patterns in DOC_CRITICAL_PATTERNS.items():
            for pattern in patterns:
                if fnmatch.fnmatch(path_str, pattern.lower()):
                    return FileClassification(
                        classification="HIGH",
                        reason=f"Critical file type: {category}",
                        matched_pattern=pattern,
                    )

        # Default to normal priority
        return FileClassification(
            classification="NORMAL", reason="Regular file requiring standard analysis"
        )

    def get_change_magnitude(self, file_path: Path) -> ChangeMagnitude:
        """Calculate the magnitude of changes in a file.

        Analyzes:
        - Lines added/deleted
        - Whether file was renamed
        - Rename similarity percentage
        - Overall significance score

        Args:
            file_path: Path to analyze.

        Returns:
            ChangeMagnitude with detailed change metrics.
        """
        # Get diff with rename detection
        diff_output = self.repo.git.diff(
            self.base_branch,
            "-M90%",  # Detect renames with 90% similarity threshold
            "--numstat",  # Get line counts
            "--",
            str(file_path),
        )

        # Parse numstat output: "added\tdeleted\tfilename"
        lines_added = 0
        lines_deleted = 0
        is_rename = False
        rename_similarity = None

        if diff_output:
            lines = diff_output.strip().split("\n")
            if lines:
                parts = lines[0].split("\t")
                if len(parts) >= 2:
                    # Handle binary files (marked as '-')
                    added_str = parts[0]
                    deleted_str = parts[1]

                    lines_added = 0 if added_str == "-" else int(added_str)
                    lines_deleted = 0 if deleted_str == "-" else int(deleted_str)

        # Check for rename/move
        rename_output = self.repo.git.diff(
            self.base_branch, "-M90%", "--summary", "--", str(file_path)
        )

        if "rename" in rename_output.lower():
            is_rename = True
            # Try to extract similarity percentage
            import re

            match = re.search(r"(\d+)%", rename_output)
            if match:
                rename_similarity = int(match.group(1))

        # Calculate significance score (0.0 to 1.0)
        total_lines = lines_added + lines_deleted

        # Base score on change volume
        if total_lines == 0:
            score = 0.0
        elif total_lines < 5:
            score = 0.2
        elif total_lines < 20:
            score = 0.4
        elif total_lines < 50:
            score = 0.6
        elif total_lines < 100:
            score = 0.8
        else:
            score = 1.0

        # Reduce score for renames (mostly trivial)
        if is_rename and rename_similarity and rename_similarity > 95:
            score *= 0.3  # Pure rename with minimal changes
        elif is_rename:
            score *= 0.6  # Rename with some changes

        return ChangeMagnitude(
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            total_lines=total_lines,
            is_rename=is_rename,
            rename_similarity=rename_similarity,
            score=score,
        )

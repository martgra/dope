"""Project and Git repository utilities."""

from git import Repo


def get_graphical_repo_tree(repo_path: str) -> str:
    """Generate graphical representation of repository structure.

    Args:
        repo_path: Path to Git repository

    Returns:
        String representation of repository file tree

    Note:
        This function is deprecated. Use dope.core.tree.get_structure() instead.
    """
    repo = Repo(repo_path)
    tree = repo.head.commit.tree

    def traverse(tree, prefix=""):
        entries = list(tree)
        lines = []
        for i, item in enumerate(entries):
            is_last = i == len(entries) - 1
            branch = "└── " if is_last else "├── "
            line = f"{prefix}{branch}{item.name}"
            lines.append(line)
            if item.type == "tree":
                extension = "    " if is_last else "│   "
                lines.extend(traverse(item, prefix + extension))
        return lines

    tree_lines = []
    for item in tree:
        if item.type == "tree":
            tree_lines.append(f"{item.name}/")
            tree_lines.extend(traverse(item, prefix=""))
        else:
            tree_lines.append(item.name)

    return "\n".join(tree_lines)

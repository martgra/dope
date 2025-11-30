"""Tree structure building and rendering utilities."""

from pathlib import Path

from anytree import Node, RenderTree


def build_tree(paths: list[Path], base_dir: Path = Path(".")) -> Node:
    """Build tree structure from file paths.

    Args:
        paths: List of file paths to include in tree
        base_dir: Base directory for relative path calculation

    Returns:
        Root node of the tree structure

    Example:
        >>> paths = [Path("src/main.py"), Path("src/utils.py")]
        >>> root = build_tree(paths)
        >>> root.name
        '.'
    """
    nodes: dict[str, Node] = {}
    root = Node(base_dir.name)
    nodes[str(base_dir)] = root

    for path in paths:
        parts = path.relative_to(base_dir).parts
        current_path = base_dir
        for part in parts:
            current_path = current_path / part
            key = str(current_path)
            if key not in nodes:
                parent_key = str(current_path.parent)
                nodes[key] = Node(part, parent=nodes[parent_key])
    return root


def render_tree(root: Node) -> str:
    r"""Render tree structure as string.

    Args:
        root: Root node of tree structure

    Returns:
        String representation of tree with visual branches

    Example:
        >>> root = Node("project")
        >>> Node("src", parent=root)
        >>> render_tree(root)
        'project\n└── src'
    """
    lines = []
    for pre, _, node in RenderTree(root):
        lines.append(f"{pre}{node.name}")
    return "\n".join(lines)


def get_structure(paths: list[Path], base_dir: Path = Path(".")) -> str:
    """Get tree structure of paths as formatted string.

    Args:
        paths: List of file paths to visualize
        base_dir: Base directory for structure

    Returns:
        String representation of directory tree

    Example:
        >>> paths = [Path("docs/readme.md"), Path("src/main.py")]
        >>> structure = get_structure(paths)
        >>> print(structure)
        .
        ├── docs
        │   └── readme.md
        └── src
            └── main.py
    """
    tree = build_tree(paths, base_dir)
    return render_tree(tree)

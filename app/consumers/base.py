from abc import ABC, abstractmethod
from pathlib import Path

from anytree import Node, RenderTree


class BaseConsumer(ABC):
    """Base consumer clas."""

    @abstractmethod
    def __init__(self, root_path: str | Path):
        """Initialize the consumer with a root path.

        Args:
            root_path: The root path for the consumer.
        """
        self.root_path = root_path

    @abstractmethod
    def discover_files(self) -> list[Path]:
        """Discover files."""
        pass

    @abstractmethod
    def get_content(self, file_path) -> bytes:
        """Get file content."""
        pass

    @staticmethod
    def _render_tree_to_string(root_node: Node) -> str:
        lines = []
        for pre, _, node in RenderTree(root_node):
            lines.append(f"{pre}{node.name}")
        return "\n".join(lines)

    @staticmethod
    def _build_tree(paths: list[Path]) -> Node:
        base_dir = Path(".")
        nodes = {}  # Maps full path strings to nodes
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

    def get_structure(self, paths: list[Path]) -> str:
        """Return tree.

        Args:
            paths (list[Path]): _description_

        Returns:
            str: _description_
        """
        root = self._build_tree(paths)
        return self._render_tree_to_string(root)

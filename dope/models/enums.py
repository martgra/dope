from enum import Enum


class Provider(str, Enum):
    """Enum for llm providers."""

    OPENAI = "openai"
    AZURE = "azure"


class ProjectSize(str, Enum):
    """Enum for project size."""

    TRIVIAL = "trivial"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    XL = "xl"
    UNSURE = "unsure"

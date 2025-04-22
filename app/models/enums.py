from enum import Enum


class Provider(str, Enum):
    """Enum for llm providers."""

    OPENAI = "openai"
    AZURE = "azure"

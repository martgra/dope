"""Versioned prompt registry for every LLM-facing prompt in dope.

Every prompt bound to an agent, or every user-prompt template
formatted per call, lives here as a versioned :class:`Prompt`. A
:class:`PromptRegistry` resolves a name (e.g. ``"change_doc"``) to a
specific version, falling back to a production manifest
(``production.yaml`` in this package) when no version is specified.

Why version prompts at all:

* We can A/B test variants without moving code across files or
  branches — every variant lives in the registry.
* Evals can pin an exact version so a report is reproducible.
* Rolling back a bad prompt change is editing one line of the
  manifest.
* Runtime callers stay agnostic: ``PromptRegistry.get("align_doc")``
  returns whatever production says today; evals pass
  ``version="v2-minimal"`` for the challenger.

Registration is done at import time. To keep the registry populated
without callers having to import every prompt module by hand, this
package eagerly imports the per-service modules at the bottom of
this file.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

import yaml

_MANIFEST_PATH = Path(__file__).parent / "production.yaml"


@dataclass(frozen=True)
class Prompt:
    """A single versioned prompt.

    Attributes:
        name: Logical identifier, e.g. ``"change_doc"`` or
            ``"judge.change_category"``. Namespaced with dots when the
            prompt belongs to a family of related ones.
        version: Free-form version tag, e.g. ``"v1"``, ``"v2-minimal"``,
            or ``"v3-diff"``. Sorts lexicographically for
            :meth:`PromptRegistry.list_versions`.
        template: The prompt text. May contain ``{placeholder}`` fields
            that :meth:`render` will substitute via :meth:`str.format`.
        description: One-line human-readable purpose. Never sent to the
            LLM; used by tooling and manifest edits.
    """

    name: str
    version: str
    template: str
    description: str = ""

    def render(self, **kwargs: Any) -> str:
        """Substitute placeholders via :meth:`str.format`; return the result."""
        return self.template.format(**kwargs)


class PromptRegistry:
    """Process-wide registry of :class:`Prompt` instances.

    Prompt modules call :meth:`register` at import time. Callers use
    :meth:`get` to fetch a specific version, or the production version
    when ``version`` is ``None``.
    """

    _prompts: ClassVar[dict[tuple[str, str], Prompt]] = {}
    _production: ClassVar[dict[str, str] | None] = None

    @classmethod
    def register(cls, prompt: Prompt) -> Prompt:
        """Register ``prompt`` under its ``(name, version)`` key.

        Returns the prompt back so registration can be used as an
        expression in module-level bindings.
        """
        cls._prompts[(prompt.name, prompt.version)] = prompt
        return prompt

    @classmethod
    def get(cls, name: str, version: str | None = None) -> Prompt:
        """Return the prompt for ``name`` at ``version``.

        When ``version`` is ``None``, the production manifest decides.
        Raises :class:`KeyError` for unknown names/versions or when the
        manifest has no entry for the name.
        """
        if version is None:
            version = cls._production_version(name)
        key = (name, version)
        if key not in cls._prompts:
            raise KeyError(f"Prompt {name!r} version {version!r} not registered")
        return cls._prompts[key]

    @classmethod
    def list_versions(cls, name: str) -> list[str]:
        """Return every registered version of ``name`` in sorted order."""
        return sorted(v for (n, v) in cls._prompts if n == name)

    @classmethod
    def list_names(cls) -> list[str]:
        """Return every registered prompt name in sorted order."""
        return sorted({n for (n, _) in cls._prompts})

    @classmethod
    def _production_version(cls, name: str) -> str:
        if cls._production is None:
            cls._load_manifest()
        assert cls._production is not None
        if name not in cls._production:
            raise KeyError(f"No production version for prompt {name!r}")
        return cls._production[name]

    @classmethod
    def _load_manifest(cls) -> None:
        if _MANIFEST_PATH.exists():
            cls._production = yaml.safe_load(_MANIFEST_PATH.read_text()) or {}
        else:
            cls._production = {}

    @classmethod
    def reload_manifest(cls) -> None:
        """Force reloading of the production manifest (useful in tests)."""
        cls._production = None
        cls._load_manifest()


# Eager import of all prompt modules so the registry is populated by
# the time anyone calls PromptRegistry.get(). The imports appear here
# rather than at the top of the file because they depend on the
# Prompt and PromptRegistry classes defined above.

from dope.prompts import (  # noqa: E402, F401
    change,
    describe,
    judge,
    scope,
    suggest,
)

__all__ = ["Prompt", "PromptRegistry"]

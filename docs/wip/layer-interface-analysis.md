# Layer & Interface Analysis

**Date:** 2024-12-01
**Status:** Analysis Complete

## Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                            │
│   Typer commands, factories, user interaction               │
└─────────────────────────────────────────────────────────────┘
                              │ uses
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Services Layer                         │
│   Business logic, orchestration, LLM agent coordination     │
└─────────────────────────────────────────────────────────────┘
                      │           │
          ┌───────────┘           └───────────┐
          ▼                                   ▼
┌─────────────────────┐           ┌───────────────────────────┐
│   Repositories      │           │      Consumers            │
│   State persistence │           │   External I/O (git, fs)  │
└─────────────────────┘           └───────────────────────────┘
                       ↘         ↙
┌─────────────────────────────────────────────────────────────┐
│                      Core Layer                             │
│   Protocols, shared utilities, no business logic            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Models Layer                            │
│   Pydantic models, enums, constants (no logic)              │
└─────────────────────────────────────────────────────────────┘
```

## Issues Found

### 1. Missing Public API Definitions

**Problem:** Most `__init__.py` files are empty, making it unclear what the public API is.

**Impact:**

- Hard to know what to import
- No protection against internal refactoring breaking consumers
- IDE autocomplete shows internal implementation details

**Affected modules:**

- `dope/core/__init__.py` - empty
- `dope/consumers/__init__.py` - empty
- `dope/services/__init__.py` - empty
- `dope/cli/__init__.py` - empty

### 2. Protocol vs Implementation Naming Collision

**Problem:** `FileClassifier` exists as both:

- Protocol in `dope/core/protocols.py`
- Concrete class in `dope/core/classification.py`

**Impact:** Confusing imports, unclear which to use for type hints

### 3. Consumer Layer Has Business Logic

**Problem:** `GitConsumer` contains:

- `classify_file_by_path()` - classification logic
- `get_change_magnitude()` - analysis logic

**Impact:**

- Consumers should be "dumb" I/O wrappers
- Classification logic should be in `core/` or injected via protocol
- Makes testing harder (can't test classification without git)

### 4. Services Creating Own Dependencies

**Problem:** `DescriberService.__init__` creates its own repository:

```python
if repository is not None:
    self._repository = repository
elif state_filepath is not None:
    self._repository = DescriberRepository(state_filepath)
```

**Impact:**

- Violates single responsibility
- Makes testing harder
- Inconsistent with other services

### 5. Inconsistent Service Patterns

**Problem:** Services have different structures:

| Service              | Repository          | Agent Lazy-Load | Usage Tracker |
| -------------------- | ------------------- | --------------- | ------------- |
| `DocChangeSuggester` | ✅ Injected         | ✅ Lazy         | ✅ Protocol   |
| `DescriberService`   | ⚠️ Optional/creates | ❌ Direct       | ✅ Concrete   |
| `DocsChanger`        | ❌ None             | ✅ Lazy         | ✅ Optional   |
| `ScopeService`       | ❌ None             | ❌ Direct       | ✅ Optional   |

### 6. Public Methods That Should Be Private

**Problem:** Internal methods exposed without underscore prefix:

In `DescriberService`:

- `load_state()` - should be `_load_state()` (use repository directly)
- `save_state()` - should be `_save_state()` (use repository directly)

In `GitConsumer`:

- `classify_file_by_path()` - business logic shouldn't be in consumer

### 7. Missing Protocols for Key Interfaces

**Problem:** Some key interfaces lack protocol definitions:

- `SuggestionAgent` protocol defined inline in `suggester_service.py`
- No protocol for `DocsChanger` or `ScopeService` dependencies
- `BaseConsumer` is ABC not Protocol (can't use for duck typing)

---

## Recommended Changes

### Phase 1: Define Public APIs (Low Risk)

Add `__all__` to each layer's `__init__.py`:

```python
# dope/core/__init__.py
from dope.core.protocols import (
    FileClassifier,
    FileConsumer,
    StateRepository,
    UsageTrackerProtocol,
)
from dope.core.usage import UsageTracker
from dope.core.classification import FileClassification, ChangeMagnitude

__all__ = [
    # Protocols (for type hints)
    "FileClassifier",
    "FileConsumer",
    "StateRepository",
    "UsageTrackerProtocol",
    # Implementations
    "UsageTracker",
    # Data classes
    "FileClassification",
    "ChangeMagnitude",
]
```

```python
# dope/consumers/__init__.py
from dope.consumers.doc_consumer import DocConsumer
from dope.consumers.git_consumer import GitConsumer

__all__ = ["DocConsumer", "GitConsumer"]
```

```python
# dope/repositories/__init__.py (already good, keep as-is)
```

```python
# dope/services/__init__.py
from dope.services.describer.describer_base import (
    CodeDescriberService,
    DescriberService,
)
from dope.services.suggester.suggester_service import DocChangeSuggester
from dope.services.changer.changer_service import DocsChanger
from dope.services.scoper.scoper_service import ScopeService

__all__ = [
    "CodeDescriberService",
    "DescriberService",
    "DocChangeSuggester",
    "DocsChanger",
    "ScopeService",
]
```

### Phase 2: Fix Protocol Naming (Low Risk)

Rename protocol to avoid collision:

```python
# dope/core/protocols.py
@runtime_checkable
class FileClassifierProtocol(Protocol):  # Renamed from FileClassifier
    """Protocol for classifying files based on path patterns."""

    def classify(self, file_path: Path) -> tuple[str, str]:
        ...
```

### Phase 3: Move Classification Out of Consumer (Medium Risk)

Move classification logic from `GitConsumer` to be injected:

```python
# dope/consumers/git_consumer.py
class GitConsumer(BaseConsumer):
    def __init__(
        self,
        root_path: Path,
        base_branch: str,
        classifier: FileClassifierProtocol | None = None,  # Inject
    ):
        ...
        self._classifier = classifier

    # Remove classify_file_by_path and get_change_magnitude
    # These should be in services layer or injected
```

```python
# dope/services/describer/describer_base.py
class CodeDescriberService(DescriberService):
    def __init__(
        self,
        consumer: GitConsumer,
        repository: DescriberRepository,  # Required, not optional
        classifier: FileClassifier,  # New: inject classifier
        usage_tracker: UsageTracker | None = None,
    ):
        ...
```

### Phase 4: Require Repository Injection (Medium Risk)

Remove self-creation of repositories:

```python
# Before (current)
class DescriberService:
    def __init__(
        self,
        consumer: BaseConsumer,
        state_filepath: Path | None = None,  # Remove
        repository: DescriberRepository | None = None,  # Make required
        ...
    ):
        if repository is not None:
            self._repository = repository
        elif state_filepath is not None:
            self._repository = DescriberRepository(state_filepath)

# After (proposed)
class DescriberService:
    def __init__(
        self,
        consumer: BaseConsumer,
        repository: DescriberRepository,  # Required
        usage_tracker: UsageTracker | None = None,
        doc_term_index_path: Path | None = None,
    ):
        self._repository = repository
```

### Phase 5: Standardize Service Pattern (Medium Risk)

All services should follow this pattern:

```python
class ServiceBase:
    """Base pattern for services."""

    def __init__(
        self,
        *,  # Keyword-only for clarity
        repository: RepositoryProtocol,  # Required, injected
        usage_tracker: UsageTrackerProtocol | None = None,
    ):
        self._repository = repository
        self._usage_tracker = usage_tracker or UsageTracker()
        self._agent = None  # Lazy-loaded

    @property
    def agent(self) -> AgentProtocol:
        """Lazy-load agent."""
        if self._agent is None:
            self._agent = self._create_agent()
        return self._agent

    def _create_agent(self) -> AgentProtocol:
        """Override in subclasses."""
        raise NotImplementedError
```

---

## Summary of Visibility Changes

### Should Be Public (in `__all__`)

| Layer          | Public Items                                                                          |
| -------------- | ------------------------------------------------------------------------------------- |
| `models`       | All domain models, enums, constants, Settings                                         |
| `core`         | Protocols, UsageTracker, FileClassification, ChangeMagnitude                          |
| `repositories` | JsonStateRepository, DescriberRepository, SuggestionRepository                        |
| `consumers`    | DocConsumer, GitConsumer                                                              |
| `services`     | DescriberService, CodeDescriberService, DocChangeSuggester, DocsChanger, ScopeService |
| `cli`          | Nothing (internal wiring)                                                             |

### Should Be Private (underscore prefix)

| Class              | Methods to Make Private                                    |
| ------------------ | ---------------------------------------------------------- |
| `DescriberService` | `load_state` → `_load_state`, `save_state` → `_save_state` |
| `GitConsumer`      | Move `classify_file_by_path`, `get_change_magnitude` out   |
| `ChangeProcessor`  | Consider making module-level functions (no state)          |

### Should Use Protocols

| Current                  | Proposed                                             |
| ------------------------ | ---------------------------------------------------- |
| `BaseConsumer` (ABC)     | Keep ABC, add `FileConsumer` protocol for type hints |
| Inline `SuggestionAgent` | Move to `protocols.py`                               |
| None for changer/scoper  | Add protocols if needed for testing                  |

---

## Implementation Priority

1. **Phase 1** (Low risk, high value): Add `__all__` exports - **DO FIRST**
2. **Phase 2** (Low risk): Rename `FileClassifier` protocol
3. **Phase 4** (Medium risk): Require repository injection in DescriberService
4. **Phase 3** (Medium risk): Move classification out of consumer
5. **Phase 5** (Ongoing): Standardize service patterns

---

## Design Decisions

1. **Consumers = dumb I/O** → Classification logic moves to services layer
2. **Required DI** → Services must receive dependencies, no self-creation
3. **Layer boundaries > `__all__`** → Focus on clean interfaces, not export lists

## Implementation Plan

### Step 1: Make DescriberService require repository injection

- Remove `state_filepath` parameter
- Make `repository` required (not optional)
- Update factories to always provide repository

### Step 2: Move classification out of GitConsumer

- Remove `classify_file_by_path()` from GitConsumer
- Remove `get_change_magnitude()` from GitConsumer
- Move to `CodeDescriberService` where it belongs (uses `FileClassifier` from core)

### Step 3: Clean up public/private boundaries

- Rename `load_state()` → `_load_state()`
- Rename `save_state()` → `_save_state()`
- These are internal implementation details

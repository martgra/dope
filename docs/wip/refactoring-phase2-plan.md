# Refactoring Phase 2: Architecture Simplification

## Executive Summary

This document outlines a comprehensive refactoring plan to address complexity, coupling, and testability issues in the `dope` application.

## Current State Analysis

### Identified Issues

#### 1. **Tight Coupling**

- Services directly instantiate agents via `get_*_agent()` functions with `@lru_cache`
- Settings accessed via global `get_settings()` function throughout codebase
- Consumers (GitConsumer, DocConsumer) directly instantiated in CLI commands
- Hard to mock dependencies in tests

#### 2. **Complex Services**

- `DescriberService` and `CodeDescriberService` have too many responsibilities:
  - State management (load/save)
  - File scanning
  - Hash computation
  - Agent invocation
  - Term index building
- `CodeDescriberService` has 250+ lines with complex filtering logic mixed in

#### 3. **Duplicated Patterns**

- State persistence pattern repeated in:
  - `SuggestionStateRepository`
  - `DescriberService.load_state()/save_state()`
  - Manual JSON handling in CLI commands
- Similar agent creation patterns across services

#### 4. **Mixed Concerns in CLI**

- CLI commands contain business logic
- Direct instantiation of services with complex setup
- State file path resolution mixed with command logic

#### 5. **Unclear Domain Boundaries**

- `models/domain/doc.py` contains both suggestion models AND code metadata
- `models/internal.py` has only `FileSuffix` class
- Some domain concepts spread across multiple files

### Current Architecture (Simplified)

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│    CLI      │────▶│    Services     │────▶│   Agents    │
│  (typer)    │     │  (mixed logic)  │     │ (pydantic)  │
└─────────────┘     └─────────────────┘     └─────────────┘
       │                    │                      │
       │                    ▼                      │
       │            ┌─────────────┐               │
       │            │  Consumers  │               │
       │            │ (Git/Doc)   │               │
       │            └─────────────┘               │
       │                    │                      │
       └────────────────────┼──────────────────────┘
                           ▼
                    ┌─────────────┐
                    │  Settings   │
                    │  (global)   │
                    └─────────────┘
```

## Proposed Architecture

### Design Principles

1. **Dependency Injection**: Pass dependencies explicitly, no global state
2. **Single Responsibility**: Each class does one thing well
3. **Interface Segregation**: Define protocols for testability
4. **Clean Layers**: CLI → Service → Repository/Consumer

### New Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                           │
│  • Command handlers only (no business logic)                │
│  • Dependency wiring via factory functions                  │
│  • Error presentation                                       │
└───────────────────────────┬─────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                          │
│  • Business logic                                           │
│  • Orchestrates repositories and consumers                  │
│  • Receives dependencies via constructor                    │
└──────────┬─────────────────────────────────┬────────────────┘
           │                                 │
           ▼                                 ▼
┌────────────────────────┐     ┌────────────────────────────┐
│    Repository Layer    │     │      Consumer Layer        │
│  • State persistence   │     │  • External data access    │
│  • Caching logic       │     │  • Git operations          │
│  • File I/O            │     │  • File system             │
└────────────────────────┘     └────────────────────────────┘
           │                                 │
           ▼                                 ▼
┌────────────────────────────────────────────────────────────┐
│                     Infrastructure                         │
│  • LLM clients (via factory)                               │
│  • File system                                             │
│  • Git operations                                          │
└────────────────────────────────────────────────────────────┘
```

## Refactoring Steps

### Phase 1: Define Interfaces (Protocols)

Create protocol definitions for dependency injection:

```python
# dope/core/protocols.py
from typing import Protocol, Any
from pathlib import Path

class StateRepository(Protocol):
    """Protocol for state persistence."""
    def load(self) -> dict[str, Any]: ...
    def save(self, state: dict[str, Any]) -> None: ...
    def compute_hash(self, data: Any) -> str: ...

class FileConsumer(Protocol):
    """Protocol for file discovery and content access."""
    def discover_files(self) -> list[Path]: ...
    def get_content(self, file_path: Path) -> bytes: ...

class AgentRunner(Protocol):
    """Protocol for running LLM agents."""
    def run(self, prompt: str) -> Any: ...
```

### Phase 2: Extract Generic State Repository

Create a single, reusable state repository:

```python
# dope/repositories/state_repository.py
class JsonStateRepository:
    """Generic JSON state repository."""

    def __init__(self, state_path: Path):
        self._path = state_path

    def load(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text())

    def save(self, state: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(state, indent=2))
```

### Phase 3: Simplify Services

Extract responsibilities into focused classes:

```python
# BEFORE: Mixed responsibilities in DescriberService
class DescriberService:
    def __init__(self, consumer, state_filepath, usage_tracker, doc_term_index_path):
        # Too many dependencies

    def scan(self): ...  # Scanning
    def describe(self): ...  # LLM interaction
    def load_state(self): ...  # Persistence
    def save_state(self): ...  # Persistence
    def _build_term_index(self): ...  # Index building

# AFTER: Single responsibility
class DocScanner:
    """Scans documentation files and detects changes."""

    def __init__(self, consumer: FileConsumer, repository: StateRepository):
        self._consumer = consumer
        self._repository = repository

    def scan(self) -> ScanResult:
        """Scan files and return changed files."""
        ...

class DocDescriber:
    """Generates descriptions for documentation files."""

    def __init__(self, agent_runner: AgentRunner):
        self._agent = agent_runner

    def describe(self, content: str) -> DocSummary:
        """Generate description for document content."""
        ...
```

### Phase 4: Decouple Agents

Replace direct agent instantiation with factory injection:

```python
# BEFORE: Tight coupling
class DocChangeSuggester:
    @property
    def agent(self):
        if self._agent is None:
            self._agent = get_suggester_agent()  # Global function
        return self._agent

# AFTER: Dependency injection
class DocChangeSuggester:
    def __init__(
        self,
        repository: StateRepository,
        agent: AgentRunner,
        usage_tracker: UsageTracker | None = None,
    ):
        self._repository = repository
        self._agent = agent
        self._usage = usage_tracker or UsageTracker()
```

### Phase 5: Clean CLI Layer

Extract service wiring to factory module:

```python
# dope/cli/factories.py
def create_suggester(settings: Settings, tracker: UsageTracker) -> DocChangeSuggester:
    """Factory to create configured DocChangeSuggester."""
    return DocChangeSuggester(
        repository=JsonStateRepository(settings.state_directory / SUGGESTION_STATE_FILENAME),
        agent=create_suggester_agent(settings),
        usage_tracker=tracker,
    )

# dope/cli/suggest.py - Now clean and simple
@app.callback(invoke_without_command=True)
def suggest(branch: get_branch_option() = None):
    settings = require_config()
    tracker = UsageTracker()

    suggester = create_suggester(settings, tracker)
    result = suggester.get_suggestions(...)

    display_suggestions(result)
    tracker.log()
```

### Phase 6: Consolidate Domain Models

Reorganize models for clarity:

```
models/
├── __init__.py
├── constants.py          # All constants
├── enums.py              # All enums
└── domain/
    ├── __init__.py
    ├── code.py           # Code-related models (CodeChange, CodeChanges, CodeMetadata)
    ├── doc.py            # Doc-related models (DocSummary, DocSection)
    ├── suggestion.py     # Suggestion models (SuggestedChange, ChangeSuggestion, DocSuggestions)
    └── scope.py          # Scope models (ScopeTemplate, etc.)
```

## File Changes Summary

### New Files to Create

- `dope/core/protocols.py` - Interface definitions
- `dope/repositories/__init__.py` - Repository package
- `dope/repositories/state_repository.py` - Generic state repository
- `dope/cli/factories.py` - Service factory functions
- `dope/services/scanner.py` - Simplified scanner service
- `dope/services/describer.py` - Simplified describer service

### Files to Modify

- `dope/services/suggester/suggester_service.py` - Simplify, use injection
- `dope/services/describer/describer_base.py` - Extract to new services
- `dope/cli/scan.py` - Use factories, reduce logic
- `dope/cli/suggest.py` - Use factories, reduce logic
- `dope/models/domain/doc.py` - Move CodeMetadata to code.py

### Files to Remove (After Migration)

- `dope/services/suggester/state_repository.py` - Replaced by generic
- `dope/cli/config.py.bak` - Backup file, no longer needed

## Testing Strategy

### Unit Tests

Each new class will have corresponding unit tests with mocked dependencies:

```python
def test_doc_scanner_detects_new_files():
    # Arrange
    mock_consumer = Mock(spec=FileConsumer)
    mock_consumer.discover_files.return_value = [Path("new.md")]
    mock_repository = Mock(spec=StateRepository)
    mock_repository.load.return_value = {}

    scanner = DocScanner(mock_consumer, mock_repository)

    # Act
    result = scanner.scan()

    # Assert
    assert "new.md" in result.new_files
```

### Integration Tests

Test service composition with real (but isolated) dependencies.

## Migration Path

1. Create new interfaces/protocols (non-breaking)
2. Create new repository implementation (non-breaking)
3. Add factories alongside existing code (non-breaking)
4. Migrate CLI commands one at a time
5. Remove deprecated code after migration

## Success Criteria

1. **Testability**: All services can be unit tested with mocked dependencies
2. **Simplicity**: No class > 150 lines, cyclomatic complexity < 8
3. **Clarity**: Clear separation between layers
4. **Maintainability**: Changes in one layer don't affect others

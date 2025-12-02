"""Vulture whitelist for false positives.

This file tells vulture to ignore certain code patterns that appear unused
but are actually used through frameworks, decorators, or external APIs.

Categories:
- Pydantic model fields (accessed via model serialization)
- Pydantic validators (called by Pydantic framework)
- Protocol method signatures (define contracts, not implementations)
- Typer CLI commands (registered via decorators)
- PydanticAI agent decorators (registered via @agent.system_prompt)
- Enum values (used via serialization/deserialization)
- Exception classes (part of public API, used by callers)
"""

# Pydantic model fields - accessed via .model_dump(), serialization, etc.
specific_changes  # dope/models/domain/code.py - CodeChanges field
functional_impact  # dope/models/domain/code.py - CodeChanges field
programming_language  # dope/models/domain/code.py - CodeChanges field
num_contributors  # dope/models/domain/code.py - CodeMetadata field
lines_of_code  # dope/models/domain/code.py - CodeMetadata field
suggestion  # dope/models/domain/documentation.py - ChangeSuggestion field
code_references  # dope/models/domain/documentation.py - ChangeSuggestion field
themes  # dope/models/domain/scope.py - DocSectionTemplate field
roles  # dope/models/domain/scope.py - DocSectionTemplate/DocTemplate field
matched_pattern  # dope/core/classification.py - FileClassification field
model_config  # dope/models/settings.py - Pydantic settings config

# Pydantic validators - called by Pydantic framework
_.validate_base_url_required_for_custom  # dope/models/settings.py

# Enum values - used via serialization
CHANGE  # dope/models/enums.py - ChangeType.CHANGE
DELETE  # dope/models/enums.py - ChangeType.DELETE

# Protocol method signatures - define contracts for type checking
_.filter  # dope/consumers/doc_consumer.py - attribute used in filtering

# Typer CLI commands - registered via decorators, called by CLI framework
show  # dope/cli/config/__init__.py - typer command
init  # dope/cli/config/__init__.py - typer command
update_setting  # dope/cli/config/__init__.py - typer command
code  # dope/cli/scan.py - typer command
create  # dope/cli/scope.py - typer command

# PydanticAI agent system prompts - registered via @agent.system_prompt decorator
_add_summarization_prompt  # Used in multiple agent files
_add_complexity_prompt  # dope/services/scoper/scoper_agents.py
_add_scope_creator_prompt  # dope/services/scoper/scoper_agents.py
_fill_file_prompt  # dope/services/scoper/scoper_agents.py

# PydanticAI agent tools - registered via @agent.tool decorator
get_code_file_content  # dope/services/changer/changer_agents.py
get_code_file_content  # dope/services/describer/describer_agents.py

# Exception classes - public API for error handling
ConfigNotFoundError  # dope/exceptions.py
InvalidConfigError  # dope/exceptions.py
GitRepositoryNotFoundError  # dope/exceptions.py
GitBranchNotFoundError  # dope/exceptions.py

# Repository methods - public API for state management
_.delete  # dope/repositories/json_state.py
_.is_file_changed  # dope/repositories/describer_state.py
_.needs_summary  # dope/repositories/describer_state.py
_.update_file_state  # dope/repositories/describer_state.py
_.remove_stale_files  # dope/repositories/describer_state.py
_.get_files_needing_summary  # dope/repositories/describer_state.py
_.get_processable_files  # dope/repositories/describer_state.py

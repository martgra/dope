# Unreleased

- **CLI Output Unification**: Centralized CLI user interface refactor. Direct calls to Rich progress and print in `scan`, `status`, `update`, `scope`, `suggest`, and other commands have been replaced with a unified UI abstraction (ProgressReporter and StatusFormatter) and standardized logging functions (`info`, `success`, `warning`, `error`) for more consistent command-line messaging and easier customization.
- **Progress Visibility**: Enhanced progress feedback (real-time bars, M/N counts, skipped vs. processed file stats) in `scan` and `update` commands for better user experience.
- **Uncommitted Changes Detection**: Fixed branch resolution in `CommandContext` to default correctly and allow `dope scan code` to detect both staged and unstaged changes when run on the current branch.
- **Empty-state Handling in suggestion_state**: `load_suggestions` now returns an empty `DocSuggestions` instance when no suggestion data exists, preventing errors on missing or empty state.
- **Suggestion Preview in CLI update command**: In dry-run mode, `dope update` shows a preview (first 80 characters) of each suggestion's text for easier inspection.
- Added `dope scope` command group with `create` subcommand for interactive documentation‑scope generation
- Introduced `ScopeService`, `DocScope`, and AI agents for scope definition
- Added `get_structure` and repository metadata features (anytree)
- Added `get_graphical_repo_tree` utility
- Added Python dependencies: anytree >=2.13.0, questionary >=2.1.0
- Updated import paths for domain models (`dope.models.domain.domain`)
- Rename `--apply-change` option to `--apply` for the `dope change docs` command.
- Add a new `--branch <branch-name>` option to specify which Git branch to compare against (defaulting to the configured default branch) for the following commands:
  - `dope scan docs`
  - `dope describe code`
  - `dope suggest docs`
  - `dope change docs --apply`
  - `dope scope create`
- **Telemetry & Usage Tracking**: Added `UsageContext().log_usage()` calls to CLI commands (`describe`, `change`, `suggest`, and `scope`) and passed `usage=UsageContext().usage` into all agent `run_sync` calls to enable centralized usage tracking and analytics. (dope/cli/scan.py, dope/cli/change.py, dope/cli/scope.py, dope/cli/suggest.py, dope/services/changer/changer_service.py, dope/services/describer/describer_agents.py, dope/services/scoper/scoper_agents.py, dope/services/suggester/suggester_agents.py)
- **CI Workflow**: Added a new GitHub Actions workflow (`.github/workflows/ci.yaml`) to run on pull requests to `main` and manual dispatch, performing code checkout, dependency install (with `uv` caching), linting via Ruff, and static analysis using Pylint (fail threshold 9). (.github/workflows/ci.yaml)
- Enhanced `init` command to support interactive prompts for configuration fields: `state_directory`, `code_repo_root`, `docs_root`, `exclude_dirs`, `doc_filetypes`, `provider`, `deployment_endpoint`, and `token`, including URL validation and graceful abort handling. ([dope/cli/config.py])
- Renamed `GitSettings` to `CodeRepoSettings` and introduced new `docs_root` and `code_repo_root` attributes; default values for file suffixes, excludes, and branch are now driven by constants. ([dope/core/settings.py], [dope/models/constants.py])
- `generate_local_config_file` now omits `None` values when writing YAML; `generate_local_cache` supports custom `cache_dir_path` and `add_to_git` behavior with `.gitignore` creation. ([dope/core/utils.py])
- Refactored the code-describing CLI to use the new `CodeDescriberService` (moved from `dope.services.describer.describer_service` to `dope.services.describer.describer_base`).
- Introduced a generic `Scanner` class in `dope.services.describer.describer_base` for incremental file scanning, state persistence, and content summarization.
- Added a `Deps` dataclass and `get_code_file_content` tool to the `code_change_agent` for reliable retrieval of full file contents and explicit error handling.
- Expanded the documentation prompts (`DOC_DESCRIPTION_PROMPT` and `CODE_DESCRIPTION_PROMPT`) to clarify input formats and improve the accuracy of generated summaries.
- Added `dope apply` command to apply suggested documentation changes via the DocsChanger service.
- Added `dope config` command group with subcommands `init`, `show`, `validate`, and `set` to manage application configuration.
- Added `--concurrency` option (default 5) for `dope scan docs` and `dope scan code` commands, enabling parallel LLM calls during scans.
- Enhanced empty-state handling: `get_suggestions` in the `suggestion_state` repository now immediately returns an empty `DocSuggestions` instance when no suggestion data is available.
- Improved suggestion preview: in dry-run mode, the CLI's `update` command now displays a preview (first 80 characters) of each suggestion's `suggestion` attribute for better readability.
- Added ChangeCategory enum and infer_change_category function for semantic classification of code changes (dope/core/classification.py).
- Introduced FreshnessLevel enum and UpdateTriggers model, and added update_triggers and freshness_requirement fields to DocSectionTemplate and all scope templates to support dynamic documentation update triggers (dope/models/domain/scope.py and dope/services/scoper/scope_template/*).
- Added load_scope_from_yaml to load and validate scope templates from YAML files (dope/core/config_io.py).
- Added ScopeFilterSettings and the scope_filter attribute in Settings for tuning scope-based change filtering (dope/models/settings.py).
- Enhanced DocChangeSuggester and service_factory to automatically load and apply project scopes and scope_filter_settings to suggestions (dope/services/suggester/suggester_service.py, dope/core/service_factory.py).
- Updated CLI suggest and update commands to simplify scope usage by removing external --scope-file parameters (dope/cli/suggest.py, dope/cli/update.py).
- Updated suggestion prompts to leverage detailed change metadata (priority, magnitude, scope relevance, category, and affected docs) for more accurate suggestions (dope/services/suggester/prompts.py).
- Enhanced metadata output to include scope relevance, category, and affected docs sections for each change (dope/services/suggester/change_processor.py).

- Introduced DocTermIndex.filter_relevant_docs to score and filter documentation files by term relevance, scope alignment, and priority.
- Added ChangeProcessor.format_changes_adaptive and helper _prune_summary_by_relevance for dynamic detail pruning of change summaries based on combined relevance scores.
- Enhanced ScopeAlignmentFilter to use code content for term-matching boosts in relevance calculation.
- Added detailed analytics logging in _log_analytics for monitoring filtering effectiveness and prompt token usage.
- Added ScopeFilterSettings configuration fields (enable_adaptive_pruning, detail thresholds, term-boost weight, match threshold, min_docs_threshold) for fine-tuning adaptive pruning behavior.

# Version History

<!--
Chronological list of past releases and their release notes.
-->

# Upgrade Notes

<!--
Add any migration tips or compatibility notes for upgrading between versions.
-->

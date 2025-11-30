# Unreleased

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
- **Telemetry & Usage Tracking**: Added `UsageContext().log_usage()` calls to CLI commands (`describe`, `change`, `suggest`, and `scope`) and passed `usage=UsageContext().usage` into all agent `run_sync` calls to enable centralized usage tracking and analytics. (app/cli/describe.py, app/cli/change.py, app/cli/scope.py, app/cli/suggest.py, app/services/changer/changer_service.py, app/services/describer/describer_service.py, app/services/scoper/scoper_service.py, app/services/suggester/suggester_service.py)
- **CI Workflow**: Added a new GitHub Actions workflow (`.github/workflows/ci_backend.yaml`) to run on pull requests to `main` and manual dispatch, performing code checkout, dependency install (with `uv` caching), linting via Ruff, and static analysis using Pylint (fail threshold 9). (.github/workflows/ci_backend.yaml)
- Enhanced `init` command to support interactive prompts for configuration fields: `state_directory`, `code_repo_root`, `docs_root`, `exclude_dirs`, `doc_filetypes`, `provider`, `deployment_endpoint`, and `token`, including URL validation and graceful abort handling. ([app/cli/config.py])
- Renamed `GitSettings` to `CodeRepoSettings` and introduced new `docs_root` and `code_repo_root` attributes; default values for file suffixes, excludes, and branch are now driven by constants. ([app/core/settings.py], [app/models/constants.py])
- `generate_local_config_file` now omits `None` values when writing YAML; `generate_local_cache` supports custom `cache_dir_path` and `add_to_git` behavior with `.gitignore` creation. ([app/core/utils.py])
- Refactored the code-describing CLI to use the new `CodeDescriberService` (moved from `dope.services.describer.describer_service` to `dope.services.describer.describer_base`).
- Introduced a generic `Scanner` class in `dope.services.describer.describer_base` for incremental file scanning, state persistence, and content summarization.
- Added a `Deps` dataclass and `get_code_file_content` tool to the `code_change_agent` for reliable retrieval of full file contents and explicit error handling.
- Expanded the documentation prompts (`DOC_DESCRIPTION_PROMPT` and `CODE_DESCRIPTION_PROMPT`) to clarify input formats and improve the accuracy of generated summaries.

# Version History

<!--
Chronological list of past releases and their release notes.
-->

# Upgrade Notes

<!--
Add any migration tips or compatibility notes for upgrading between versions.
-->

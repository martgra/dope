# Unreleased

- Added `dope scope` command group with `create` subcommand for interactive documentation‑scope generation
- Introduced `ScopeService`, `DocScope`, and AI agents for scope definition
- Added `get_structure` and repository metadata features (anytree)
- Added `get_graphical_repo_tree` utility
- Added Python dependencies: anytree >=2.13.0, questionary >=2.1.0
- Updated import paths for domain models (`app.models.domain.domain`)
- Rename `--apply-change` option to `--apply` for the `dope change docs` command.
- Add a new `--branch <branch-name>` option to specify which Git branch to compare against (defaulting to the configured default branch) for the following commands:
  - `dope scan docs`
  - `dope describe code`
  - `dope suggest docs`
  - `dope change docs --apply`
  - `dope scope create`
- **Telemetry & Usage Tracking**: Added `UsageContext().log_usage()` calls to CLI commands (`describe`, `change`, `suggest`, and `scope`) and passed `usage=UsageContext().usage` into all agent `run_sync` calls to enable centralized usage tracking and analytics. (app/cli/describe.py, app/cli/change.py, app/cli/scope.py, app/cli/suggest.py, app/services/changer/changer_service.py, app/services/describer/describer_service.py, app/services/scoper/scoper_service.py, app/services/suggester/suggester_service.py)
- **CI Workflow**: Added a new GitHub Actions workflow (`.github/workflows/ci_backend.yaml`) to run on pull requests to `main` and manual dispatch, performing code checkout, dependency install (with `uv` caching), linting via Ruff, and static analysis using Pylint (fail threshold 9). (.github/workflows/ci_backend.yaml)

# Version History

<!--
Chronological list of past releases and their release notes.
-->

# Upgrade Notes

<!--
Add any migration tips or compatibility notes for upgrading between versions.
-->

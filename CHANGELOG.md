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

# Version History

<!--
Chronological list of past releases and their release notes.
-->

# Upgrade Notes

<!--
Add any migration tips or compatibility notes for upgrading between versions.
-->

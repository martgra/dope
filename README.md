![Alt](resources/banner.png)

# Getting started with dope

## Project Overview

An AI‑powered command‑line tool to scan your code and documentation, generate structured summaries, and suggest or apply documentation updates based on code changes.

## Key Features

- Scan documentation files (`.md`, `.rst`, etc.) and code diffs in Git
- Generate human‑readable summaries of docs and code changes
- Suggest documentation updates using AI
- Automate application of suggestions via an agent
- Inspect current configuration
- Apply suggested documentation changes directly to files using the `--apply` flag in the `dope change docs` command.
- **Interactive documentation scope generation with `dope scope create` (requires questionary library)**
- **Tree‑based file structure visualization via anytree in the new `get_structure` and `get_graphical_repo_tree` features**
- **Initialize or re-create the application YAML configuration file with `dope config init` (includes options to force overwrite, initialize all defaults, and select an LLM provider).**

## Quick Install

### Prerequisites

- Python 3.12 (see `.python-version`)
- An Azure OpenAI or OpenAI API token (export as `AGENT_TOKEN` or set `OPENAI_API_KEY`)
- [Git](https://git-scm.com/) for code scanning
- [`anytree` >=2.13.0](https://pypi.org/project/anytree/) for directory tree rendering
- [`questionary` >=2.1.0](https://pypi.org/project/questionary/) for interactive CLI prompts

### Installation

```bash
# Clone the repository
git clone https://github.com/martgra/dope.git
cd dope

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install .
```

## Hello World Example

All commands are exposed under the `dope` CLI entry point. For help:
```bash
dope --help
```

Note: All commands accept an optional `--branch <branch-name>` parameter (defaulting to your configured default branch).

```
# Scan documentation on current branch
dope scan docs
# Or on a specific branch
dope scan docs --branch <branch-name>

# Scan code changes on current branch
dope scan code
# Or on a specific branch
dope scan code --branch <branch-name>

# Describe documentation on a branch
dope describe docs --branch <branch-name>

# Describe code changes on a branch
dope describe code --branch <branch-name>

# Suggest documentation updates against a branch
dope suggest docs --branch <branch-name>

# Apply suggested changes (formerly --apply-change) on a branch
dope change docs --apply --branch <branch-name>

# Generate documentation scope interactively on a branch
dope scope create --branch <branch-name>
```

You can also combine flags if you want both behaviors. Example usages:

- To preview changes:
  ```bash
  dope change docs --output
  ```
- To apply changes directly to files:
  ```bash
  dope change docs --apply
  ```
- To both print and apply changes:
  ```bash
  dope change docs --apply --output
  ```

## Getting Help and Support

- For setup and quickstart instructions, see [QUICKSTART.md](QUICKSTART.md)
- To learn how to contribute, see [CONTRIBUTING.md](CONTRIBUTING.md)
- To review project changes and releases, see [CHANGELOG.md](CHANGELOG.md)
- For our documentation‑update decision guide, refer to [SCOPE.md](SCOPE.md)

## License and Attribution

TODO: Add license terms and project credits here.

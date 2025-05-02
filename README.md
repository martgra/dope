# ![Alt](resources/banner.png)

# Getting Started with dope

## Project Overview

An AI‑powered command‑line tool to scan your code and documentation, generate structured summaries, and suggest or apply documentation updates based on code changes.

## Quick Install

### Prerequisites

- Python 3.12 (see `.python-version`)
- An Azure OpenAI or OpenAI API token (export as `AGENT_TOKEN` or set `OPENAI_API_KEY`)
- [Git](https://git-scm.com/) for code scanning

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

Note: Many commands accept an optional `--branch <branch-name>` parameter (defaulting to your configured default branch).

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

# Apply suggested changes on a branch
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

### Branch Option for Advanced Commands

For the following commands, you can provide a `--branch <branch>` option to specify which Git branch to compare changes against. It defaults to your repository's default branch if omitted.

- `dope scan code --branch <branch>`  
  > Scan for code changes against the specified branch.
- `dope describe code --branch <branch>`  
  > Describe code changes against the specified branch.
- `dope suggest docs --branch <branch>`  
  > Suggest documentation updates considering code/doc differences on the given branch.
- `dope change docs --apply --branch <branch>`  
  > Apply suggested documentation updates with respect to the specified branch.

Example:
```bash
dope scan code --branch develop
```

#### Option:
```
--branch TEXT   Specify the git branch to compare changes against (defaults to your repository’s default branch).
```

## Scope Commands

Use the `scope` command group to define or reorganize documentation structure for your project.

- **Create a documentation scope interactively or by specifying options:**
  ```bash
  dope scope create                      # interactive mode for project size/sections
  dope scope create --project-size small --output scope.yml
  ```
  Walks you through selecting the project size and documentation sections and produces a `scope.yaml` file.

- **Apply a previously generated scope YAML to your docs:**
  ```bash
  dope scope apply                       # applies scope.yaml from state directory
  dope scope apply --state-file path/to/scope.yaml
  ```

  `scope apply` uses the stored scope definition plus Git and Doc consumers to scaffold or reorganize your documentation structure.

## Getting Help and Support

- For setup and quickstart instructions, see [QUICKSTART.md](QUICKSTART.md)
- To learn how to contribute, see [CONTRIBUTING.md](CONTRIBUTING.md)
- To review project changes and releases, see [CHANGELOG.md](CHANGELOG.md)

## License and Attribution

TODO: Add license terms and project credits here.

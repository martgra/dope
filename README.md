![Alt](resources/banner.png)

# Getting started with dope

An AI‑powered command‑line tool to scan your code and documentation, generate structured summaries, and suggest or apply documentation updates based on code changes.

## Features

- Scan documentation files (`.md`, `.rst`, etc.) and code diffs in Git
- Generate human‑readable summaries of docs and code changes
- Suggest documentation updates using AI
- Automate application of suggestions via an agent
- Inspect current configuration
- Apply suggested documentation changes directly to files using the `--apply-change` flag in the `dope change-doc` command.
- **Initialize or re-create the application YAML configuration file with `dope config init` (includes options to force overwrite, initialize all defaults, and select an LLM provider).**

## Prerequisites

- Python 3.12 (see `.python-version`)
- An Azure OpenAI or OpenAI API token (export as `AGENT_TOKEN` or set `OPENAI_API_KEY`)
- [Git](https://git-scm.com/) for code scanning

## Installation

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

## Development Setup (VSCode Dev Container)

We provide a [VSCode Dev Container](.devcontainer/) configuration:
1. Open this folder in VSCode.
2. When prompted, reopen in Dev Container. This sets up Python 3.12, zsh history persistence, recommended extensions, and pre-commit hooks.

## Usage

All commands are exposed under the `dope` CLI entry point. Run:
```bash
dope --help
```

### Scan Documentation

```bash
dope scan docs --root path/to/docs --show-diff
```

### Scan Code Changes

```bash
dope scan code --root path/to/repo --show-diff
```

### Describe

Generate structured summaries:
```bash
dope describe docs --root path/to/docs
# or
dope describe code --root path/to/repo
```

### Suggest Documentation Updates

```bash
dope suggest docs --show-output
```

### View Current Configuration

```bash
dope config show
```

### Initialize or Re-create Configuration

```bash
# Initialize a local config file with default settings
dope config init

# Force overwrite existing config
dope config init --force
```

### Apply/Print Suggested Changes

```bash
dope change docs --apply-change
```

You can also combine flags if you want both behaviors. Some example usages:

- To preview changes:
  ```bash
  dope change docs --output
  ```
- To apply changes directly to files:
  ```bash
  dope change docs --apply-change
  ```
- To both print and apply changes:
  ```bash
  dope change docs --apply-change --output
  ```

## Configuration

You can configure Dope using a YAML configuration file or environment variables.

- **YAML configuration file**: Place a `.doperc.yaml` file in your project root or in a global config location (e.g. `~/.config/dope/.doperc.yaml`). Generate or overwrite this file using:
  ```bash
  dope config init
  ```
- **Supported settings include**:
  - `agent.provider`: LLM provider (`OPENAI` or `AZURE`)
  - `agent.base_url`: Required if provider is `AZURE`
  - `agent.api_version`: API version string for Azure/OpenAI
  - Other agent, scan, and configuration options

- **Environment variables**: The application will use `agent___TOKEN` (recommended for API tokens)
- **Default behaviors**:
  - **Default Documentation Types**: By default, `.md` and `.mdx` are scanned
  - **Directories to Exclude**: By default, excludes `node_modules`, `.venv`, `.pytest_cache`
  - **Default Git Branch**: Defaults to `main`
  - **State files** (scan, describe, suggestion caches): Stored under your platform’s user cache directory (e.g., `~/.cache/dope/`).

You can view all current configuration settings with:
```bash
dope config show
```

> **Note:** `.doperc.yaml` (and the `.dope/` cache directory) are user- and project-specific and are included in `.gitignore` by default.

## Testing

Run the test suite with:
```bash
pytest
```

## Contributing

1. Fork the repo and create a feature branch.
2. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```
3. Commit your changes and push.
4. Open a Pull Request.

# doc-updater

An AI‑powered command‑line tool to scan your code and documentation, generate structured summaries, and suggest or apply documentation updates based on code changes.

## Features

- Scan documentation files (`.md`, `.rst`, etc.) and code diffs in Git
- Generate human‑readable summaries of docs and code changes
- Suggest documentation updates using AI
- Automate application of suggestions via an agent
- Inspect current configuration

## Prerequisites

- Python 3.12 (see `.python-version`)
- An Azure OpenAI or OpenAI API token (export as `AGENT_TOKEN` or set `OPENAI_API_KEY`)
- [Git](https://git-scm.com/) for code scanning

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/doc-updater.git
cd doc-updater

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

All commands are exposed under the `doc-updater` CLI entry point. Run:
```bash
doc-updater --help
```

### Scan Documentation

```bash
doc-updater scan docs --root path/to/docs --show-diff
```

### Scan Code Changes

```bash
doc-updater scan code --root path/to/repo --show-diff
```

### Describe

Generate structured summaries:
```bash
doc-updater describe docs --root path/to/docs
# or
doc-updater describe code --root path/to/repo
```

### Suggest Documentation Updates

```bash
doc-updater suggest docs --show-output
```

### View Current Configuration

```bash
doc-updater config show
```

## Configuration

The application can be configured using environment variables or by editing the `.env` file in the project root. Main configurable options include:

- **API Token**: Set via `AGENT_TOKEN` or `OPENAI_API_KEY`
- **Default Documentation Types**: By default, `.md` and `.mdx` are scanned
- **Directories to Exclude**: By default, excludes `node_modules`, `.venv`, `.pytest_cache`
- **Default Git Branch**: Defaults to `main`
- **Internal State Filepaths**: Caches scanned states in your platform's user cache directory

You can view all current configuration settings with:
```bash
doc-updater config show
```

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

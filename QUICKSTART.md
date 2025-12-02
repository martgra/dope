# Quickstart Guide

## Prerequisites

- Python 3.13+
- Git
- OpenAI or Azure API key set in environment variables (e.g., `OPENAI_API_KEY`)

## Installation

```bash
git clone https://github.com/your-org/dope.git
cd dope
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install .
```

## Initialize Configuration

After installing, run:

```bash
dope config init
```

This will walk you through interactive prompts for setting up the state directory, code repo root, docs root, excludes, file types, LLM provider, endpoint, and token.

You can force overwrite an existing configuration with:

```bash
dope config init --force
```

## First Run

To scan your documentation files:

```bash
# Run a parallel documentation scan with up to 10 concurrent LLM calls
dope scan docs --branch main --concurrency 10
```

_Expected:_ Lists documentation files.

When you run this command, a documentation term index file (`doc-terms.json`) will be created in the state directory. This index helps the application match relevant terms between code and docs, improving the relevance of suggestions for future commands.

**Note:** The `--concurrency` flag controls how many concurrent LLM calls are made (default: 5). Increasing concurrency can speed up scanning at the cost of higher API usage.

**Note:** If you run a command without proper configuration, the CLI will now display a red-colored error message and exit with code 1, so CI or scripts can catch the failure.

## Verify Setup

To describe the code structure:

```bash
# Verify code setup with parallel summaries
dope scan code --branch main --concurrency 8
```

_Expected:_ Summary of code structure.

> Note: When run on the current branch, `dope scan code` now compares against HEAD and includes any staged or unstaged (uncommitted) changes, so you can document work-in-progress modifications.

The `dope scan code` command now detects and includes any staged or unstaged (uncommitted) changes when run on the current branch by comparing against HEAD, allowing you to document work-in-progress code changes.

## Next Steps

Explore the main CLI commands—all support the `--branch <branch-name>` option for branch-based workflows:

```bash
# Scan documentation files
dope scan docs --branch <branch-name> [--concurrency <N>]  # (default: 5)

# Scan the code structure
dope scan code --branch <branch-name> [--concurrency <N>]  # (default: 5)

# Suggest documentation updates (optionally on a branch)
dope suggest --branch <branch-name>

# Apply suggested documentation changes
dope apply --branch <branch-name>

# Create a documentation scope interactively
dope scope create --branch <branch-name>

# Create a documentation scope with project size and output file
dope scope create --project-size medium --output scope.yml --branch <branch-name>

# Apply a documentation scope from file
dope scope apply --scope-file scope.yml --branch <branch-name>

# Run the entire documentation update flow in one command
dope update --branch <branch-name> [--dry-run]
```

For `dope suggest` and `dope apply`, the commands utilize the generated `doc-terms.json` index and intelligent file pre-filtering, focusing suggestions and updates on high-priority documentation changes where code and documentation terms align.

- Read `CONTRIBUTING.md` to learn how to contribute
- See `CHANGELOG.md` for the latest changes

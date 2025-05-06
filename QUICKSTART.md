# Quickstart Guide

## Prerequisites

- Python 3.12+
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
dope init
```

This will walk you through interactive prompts for setting up the state directory, code repo root, docs root, excludes, file types, LLM provider, endpoint, and token.

You can force overwrite an existing configuration with:

```bash
dope init --force
```

## First Run

To scan your documentation files:

```bash
dope scan docs --branch main
```

_Expected:_ Lists documentation files.

## Verify Setup

To describe the code structure:

```bash
dope describe code --branch main
```

_Expected:_ Summary of code structure.

## Next Steps

Explore the main CLI commands— all support the `--branch <branch-name>` option for branch-based workflows:

```bash
# Scan documentation files
dope scan docs --branch <branch-name>

# Describe the code structure
dope describe code --branch <branch-name>

# Suggest documentation updates (optionally on a branch)
dope suggest docs --branch <branch-name>

# Apply suggested documentation changes
dope change docs --apply --branch <branch-name>

# Create a documentation scope interactively
dope scope create --branch <branch-name>

# Create a documentation scope with project size and output file
dope scope create --project-size medium --output scope.yml --branch <branch-name>

# Apply a documentation scope from file
dope scope apply --scope-file scope.yml --branch <branch-name>
```

- Read `CONTRIBUTING.md` to learn how to contribute
- See `CHANGELOG.md` for the latest changes

# Quickstart Guide

## Prerequisites

- Python 3.12+
- Git
- OpenAI or Azure API key set in environment variables (e.g., `OPENAI_API_KEY`)
- (Installed automatically) `anytree` and `questionary` via pip

## Installation

```bash
git clone https://github.com/your-org/dope.git
cd dope
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install .
```

## First Run

To scan your documentation files:

```bash
dope scan docs [--branch <branch-name>]
```

_Expected:_ Lists documentation files.

## Verify Setup

To describe the code structure:

```bash
dope describe code [--branch <branch-name>]
```

_Expected:_ Summary of code structure.

## Next Steps

Explore the main CLI commands— all support the `--branch <branch-name>` option for branch-based workflows:

```bash
# Scan documentation files
dope scan docs [--branch <branch-name>]

# Describe the code structure
dope describe code [--branch <branch-name>]

# Suggest documentation updates (optionally on a branch)
dope suggest docs [--branch <branch-name>]

# Apply suggested documentation changes
dope change docs --apply [--branch <branch-name>]

# Create a documentation scope based on branch changes
dope scope create [--branch <branch-name>]
```

- Read `CONTRIBUTING.md` to learn how to contribute
- See `CHANGELOG.md` for the latest changes

# Quickstart Guide

## Prerequisites

- Python 3.13+
- Git
- An OpenAI or Azure API key for the primary LLM provider, set in environment variables (for example, `OPENAI_API_KEY`)
- Optional: `typesafe__API_KEY` for the TypeSafe/Jev typed-judgment provider. This is only required when using TypeSafe models or TypeSafe-powered judgment features.

## Installation

```bash
git clone https://github.com/your-org/dope.git
cd dope
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install .
```

The default package installation includes `pydantic-ai[typesafe]>=2.51.0`, so you do not need to install the TypeSafe extra separately.

### Optional: Evaluation Dependencies

Contributors running the evaluation harnesses must also install the `evals` dependency group, which provides `pydantic-evals`:

```bash
uv sync --group evals
```

Evaluation dependencies are not included in the default application installation.

## Initialize Configuration

After installing, run:

```bash
dope config init
```

This quick setup prompts for an LLM provider and token, then detects sensible project defaults. For full customization of paths, excludes, and file types, use `dope config init --interactive`.

You can force overwrite an existing configuration with:

```bash
dope config init --force
```

### Optional: Configure TypeSafe/Jev

Set `typesafe__API_KEY` in your environment or `.env` file to enable the optional TypeSafe/Jev provider:

```bash
export typesafe__API_KEY="your-typesafe-api-key"
```

For example, in `.env`:

```dotenv
typesafe__API_KEY=your-typesafe-api-key
```

TypeSafe is used for typed judgments rather than general free-form generation. It is optional unless you enable or request a TypeSafe model or a TypeSafe-powered feature. If a TypeSafe model is requested without the key configured, Dope displays a clear setup error explaining that `typesafe__API_KEY` must be set.

You can configure adaptive pruning and term-filtering options using `dope config set`. For example:

```bash
dope config set scope_filter_settings.enable_adaptive_pruning true
dope config set scope_filter_settings.high_detail_threshold 0.8
dope config set scope_filter_settings.medium_detail_threshold 0.5
dope config set scope_filter_settings.doc_term_boost_weight 1.0
dope config set scope_filter_settings.doc_term_match_threshold 3
dope config set scope_filter_settings.min_docs_threshold 5
```

This enables dynamic pruning of low-relevance changes and boosts documents matching code terms.

## First Run

To scan your documentation files:

```bash
# Run a parallel documentation scan with up to 10 concurrent LLM calls
dope scan docs --concurrency 10
```

_Expected:_ Lists documentation files.

When you run this command, a documentation term index file (`doc-terms.json`) is created in the state directory. This index helps the application match relevant terms between code and docs, improving the relevance of suggestions for future commands.

**Note:** The `--concurrency` flag controls how many concurrent LLM calls are made (default: 5). Increasing concurrency can speed up scanning at the cost of higher API usage.

**Note:** If you run a command without proper configuration, the CLI displays a red-colored error message and exits with code 1, so CI or scripts can catch the failure.

## Verify Setup

To describe the code structure:

```bash
# Verify code setup with parallel summaries
dope scan code --branch main --concurrency 8
```

_Expected:_ Summary of code structure.

> Note: When run on the current branch, `dope scan code` compares against HEAD and includes any staged or unstaged (uncommitted) changes, so you can document work-in-progress modifications.

## Next Steps

Explore the main CLI commands—all support the `--branch <branch-name>` option for branch-based workflows:

```bash
# Scan documentation files
dope scan docs [--concurrency <N>]  # (default: 5)

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
dope scope apply --state-file scope.yml --branch <branch-name>

# Run the entire documentation update flow in one command
dope update --branch <branch-name>              # Preview suggested changes
dope update --branch <branch-name> --apply      # Apply suggested changes
```

For `dope suggest` and `dope apply`, the commands use the generated `doc-terms.json` index and intelligent file pre-filtering, focusing suggestions and updates on high-priority documentation changes where code and documentation terms align.

- Read `CONTRIBUTING.md` to learn how to contribute
- See `CHANGELOG.md` for the latest changes

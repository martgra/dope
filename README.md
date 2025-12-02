![Alt](resources/banner.png)

# Getting Started with dope

## Project Overview

DOPE is an AI-powered CLI tool for scanning code and documentation, generating structured summaries, and suggesting or applying documentation updates based on code changes. It now supports semantic change categorization via a ChangeCategory enum, configurable update triggers and freshness requirements for documentation sections, and automatic scope-based suggestion filtering.

- **Adaptive suggestion formatting:** DOPE now dynamically adjusts the level of detail included in suggestions based on a combined relevance score (scope alignment, term relevance, and priority), pruning low-relevance changes to reduce token usage while preserving critical context.

## Quick Install

### Prerequisites

- Python 3.13 (see `.python-version`)
- An Azure OpenAI or OpenAI API token (export as `AGENT_TOKEN` or set `OPENAI_API_KEY`)
- [Git](https://git-scm.com/) for code scanning
- PyYAML (install via `pip install pyyaml`) for loading and validating scope templates.

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

## Quick Start

All commands are exposed under the `dope` CLI entry point. For help:
```bash
dope --help
```

### Getting Started

```bash
# 1. Initialize configuration (quickstart mode)
dope config init

# For full customization, use interactive mode
dope config init -i

# 2. Scan your documentation and code
dope scan docs --branch <branch-name> [--concurrency <N>]
dope scan code --branch <branch-name> [--concurrency <N>]

# 3. Generate suggestions
dope suggest

# 4. Check status
dope status

# 5. Apply suggested changes
dope apply

# (NEW) All-in-one step: run the full update workflow
dope update --branch <branch-name> [--dry-run]
```

You can enable adaptive pruning and tune relevance thresholds in your configuration:
```yaml
scope_filter_settings:
  enable_adaptive_pruning: true
  high_detail_threshold: 0.8
  medium_detail_threshold: 0.5
  doc_term_boost_weight: 1.0
  doc_term_match_threshold: 3
  min_docs_threshold: 5
```
Then rerun:
```
dope suggest --branch <branch>
```

> Scanning operations (`dope scan docs` and `dope scan code`) now generate a documentation term index file named `doc-terms.json` in the configured state directory. This file is automatically used in later commands (`dope suggest`, `dope apply`) to boost the relevance of suggestions and updates based on documentation-term matching.  
> Both `dope scan docs` and `dope scan code` accept an optional `--concurrency <N>` argument to control the number of simultaneous LLM API calls (default: 5). Increase or decrease as needed for your environment.

> You can inspect and update your configuration at any time using `dope config show`, `dope config validate`, and `dope config set <key> <value>`.

> **Note:** If configuration is missing or invalid, the CLI prints a colored error message and exits with status code 1, allowing automation scripts to detect failures.

### Command Reference

Note: Most commands accept an optional `--branch <branch>` or `-b <branch>` parameter (defaulting to your configured default branch).

```bash
# Configuration Commands
dope config init              # Quick setup (use -i for interactive mode)
dope config show              # Display configuration (table format)
dope config show --format json  # Display as JSON
dope config validate          # Validate configuration
dope config set KEY VALUE     # Update a single setting

# Scanning Commands
dope scan docs [--branch <branch>] [--concurrency <N>]   # Scan documentation files, build a `doc-terms.json` index in the state directory, and classify files for later filtering. (default concurrency: 5, controls parallel LLM calls)
dope scan code [--branch <branch>] [--concurrency <N>]   # Scan code files with intelligent pre-filtering (classification and change-magnitude scoring) and use the `doc-terms.json` index to boost relevance of code-to-doc mappings. (default concurrency: 5, controls parallel LLM calls) (Note: when run on the current branch, the command compares against HEAD and includes any staged or unstaged (uncommitted) changes in the analysis.)

# Documentation Workflow
dope suggest [--branch <branch>]   # Generate documentation suggestions; suggestions are filtered and targeted based on automatically loaded project scope.
dope apply -b <branch>               # Apply suggested changes
dope status                          # Show current processing status

# All-in-one Workflow
dope update --branch <branch-name> [--dry-run] [--concurrency <N>]  # Run the full documentation update workflow (scan docs, scan code, generate suggestions, then apply or preview changes) in a single step.

# Documentation Structure
dope scope create                    # Create documentation scope
dope scope apply                     # Apply documentation scope
```

**Note:** If you run `dope scan code --branch <branch-name>` on the current branch, the tool will compare against HEAD and include any staged or unstaged (uncommitted) changes in its analysis.

### Branch Comparison

Most commands support the `--branch` or `-b` option to specify which Git branch to compare against:

```bash
dope scan code -b develop        # Scan against develop branch
dope suggest -b feature/new-api  # Generate suggestions for feature branch
dope apply -b main              # Apply changes for main branch
```

If omitted, commands use your configured default branch (typically `main`).

## Key Features

### Core Functionality
- **AI-Powered Analysis**: Scan documentation files (`.md`, `.mdx`, `.rst`, etc.) and code changes using LLMs
- **Smart Suggestions**: Generate human-readable summaries and documentation update suggestions
- **Automated Updates**: Apply AI-generated suggestions directly to documentation files
- **Status Tracking**: Monitor scan progress and pending suggestions with `dope status`
- **Intelligent file pre-filtering**: Files are automatically classified (SKIP, NORMAL, HIGH) and quantified by change magnitude to skip trivial changes and prioritize critical files (e.g., README, config, entry points) before invoking LLM processing.
- **Documentation term indexing**: A `doc-terms.json` index is built during scanning to match code changes to related documentation terms, improving the focus and quality of subsequent suggestions and applies.
- **All-in-one Workflow**: Use `dope update` to run the complete workflow (scan, suggest, apply) or preview all planned updates with `--dry-run`.
- **Semantic change categorization**: Uses a ChangeCategory enum and infer_change_category function to classify code changes automatically.
- **Configurable update triggers and freshness requirements**: Allows per-section configuration of triggers (code patterns, change types, magnitude, relevant terms) and minimum documentation freshness level via UpdateTriggers and FreshnessLevel.
- **Automatic scope-based suggestion filtering**: Loads and applies project documentation scope templates and enables scope-based filtering in suggestion generation, configurable via new `scope_filter` settings.
- **Improved suggestion relevance**: Leverages detailed change metadata (priority, change magnitude, scope relevance, category, and affected docs) in LLM prompting and change processing workflows.
- **Doc-term-based filtering**: New `DocTermIndex.filter_relevant_docs` method identifies and boosts documentation files most relevant to code changes by matching extracted terms.
- **Adaptive change formatting**: New `ChangeProcessor.format_changes_adaptive` prunes details for medium/low relevance changes to optimize prompt size.
- **Suggestion analytics**: Built-in logging of filtering and token-usage analytics via a private `_log_analytics` method.

### Configuration
- **Quick Setup**: Get started with just 2-3 questions using `dope config init`
- **Interactive Mode**: Full customization with `dope config init -i`
- **Easy Updates**: Change individual settings with `dope config set`
- **Validation**: Check configuration health with `dope config validate`
- **Multi-Provider Support**: Works with OpenAI and Azure OpenAI

### Documentation Management
- **Scope Templates**: Define documentation structure by project size
- **Interactive Scope Creation**: Questionary-based project setup
- **Tree Visualization**: View file structure with anytree integration
- **Flexible File Types**: Support for MD, MDX, RST, AsciiDoc, Org, Wiki formats

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

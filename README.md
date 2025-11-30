# ![Alt](resources/banner.png)

# Getting Started with dope

## Project Overview

An AI‑powered command‑line tool to scan your code and documentation, generate structured summaries, and suggest or apply documentation updates based on code changes.

## Quick Install

### Prerequisites

- Python 3.13 (see `.python-version`)
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
dope scan docs
dope scan code

# 3. Generate suggestions
dope suggest

# 4. Check status
dope status

# 5. Apply suggested changes
dope apply
```

> You can inspect and update your configuration at any time using `dope config show`, `dope config validate`, and `dope config set <key> <value>`.

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
dope scan docs                # Scan documentation files
dope scan code -b <branch>    # Scan code changes against branch

# Documentation Workflow
dope suggest -b <branch>      # Generate documentation suggestions
dope apply -b <branch>        # Apply suggested changes
dope status                   # Show current processing status

# Documentation Structure
dope scope create             # Create documentation scope
dope scope apply              # Apply documentation scope
```

## Key Features

### Core Functionality
- **AI-Powered Analysis**: Scan documentation files (`.md`, `.mdx`, `.rst`, etc.) and code changes using LLMs
- **Smart Suggestions**: Generate human-readable summaries and documentation update suggestions
- **Automated Updates**: Apply AI-generated suggestions directly to documentation files
- **Status Tracking**: Monitor scan progress and pending suggestions with `dope status`

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

### Branch Comparison

Most commands support the `--branch` or `-b` option to specify which Git branch to compare against:

```bash
dope scan code -b develop        # Scan against develop branch
dope suggest -b feature/new-api  # Generate suggestions for feature branch
dope apply -b main              # Apply changes for main branch
```

If omitted, commands use your configured default branch (typically `main`).

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

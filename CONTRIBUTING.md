# Purpose

Contributions are welcome! We appreciate bug reports, feature requests, documentation improvements, and code contributions. Your feedback helps us improve the project for everyone.

# Issue Reporting

- Open an issue at https://github.com/your-org/dope/issues
- Use the provided bug or feature request template.
- Clearly describe the problem or suggested feature.
- Include environment details and steps to reproduce when reporting bugs.

# Pull Request Workflow

1. Fork the repository and create a feature branch based on `main`.
2. Write clear, concise commits and update or add tests as needed.
3. Ensure code style and quality by running `pytest` and `pre-commit install`.
4. If your change affects agent behavior, prompts, models, or evaluation fixtures, run the relevant evaluation suite as described in [Evaluation and Validation](#evaluation-and-validation).
5. Submit a pull request against the `main` branch and reference any related issues.
6. Participate in the review process by responding to feedback and making requested changes.

# Evaluation and Validation

Evaluation dependencies are optional and are not installed by default. Install them when you need to run the evaluation suites:

```bash
uv sync --group evals
```

Evaluation runs call configured model providers and can incur API costs. Configure the provider credentials required by your local application settings before running them. The changer, doc aligner, suggester, and scope creator evaluations require configured OpenAI or Azure credentials. Judge evaluation additionally requires `typesafe__API_KEY` in `.env`.

Run an individual production evaluation suite with:

```bash
uv run python -m evals.changer_eval
uv run python -m evals.doc_aligner_eval
uv run python -m evals.suggester_eval
uv run python -m evals.scope_creator_eval
uv run python -m evals.judge_eval
```

Use the model A/B runners when comparing a candidate model with a baseline:

```bash
uv run python -m evals.changer_ab --baseline gpt-5.6-sol --challenger gpt-5.6-terra
uv run python -m evals.doc_aligner_ab --baseline gpt-5.6-sol --challenger gpt-5.6-terra
uv run python -m evals.suggester_ab --baseline gpt-5.6-terra --challenger gpt-5.6-luna
uv run python -m evals.scope_creator_ab --baseline gpt-5.6-terra --challenger gpt-5.6-luna
```

Review accuracy, cost, token, request, and duration metrics before changing a production model or prompt. Keep fixture changes focused and explain any changed expected results in the pull request.

# Prompt Changes

Prompts are versioned in the `dope/prompts` registry. Do not overwrite an existing prompt version when changing agent behavior.

1. Register a new named and versioned prompt in the appropriate module under `dope/prompts`.
2. Run the relevant prompt A/B evaluation against the current production version.
3. Promote the candidate only after reviewing the evaluation results by selecting its version in `dope/prompts/production.yaml`.

For example, compare versions of the changer or document-aligner system prompts while holding the model constant:

```bash
uv run python -m evals.changer_prompt_ab --baseline v1 --challenger v2-minimal
uv run python -m evals.doc_aligner_prompt_ab --baseline v1 --challenger v2-minimal
```

Use `--model` to evaluate both versions on a different model tier:

```bash
uv run python -m evals.changer_prompt_ab \
  --model gpt-5.6-terra \
  --baseline v1 \
  --challenger v2-minimal
```

Historical registered prompt versions remain available even after production promotion. Preserve them so evaluations can pin exact versions and remain reproducible.

# Code of Conduct

Please follow our [Code of Conduct](https://github.com/your-org/dope/blob/main/CODE_OF_CONDUCT.md) to help foster an open, welcoming, and productive community for all contributors.

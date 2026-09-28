# TypeSafe (Jev) Integration Plan

**Author:** Martin Gran
**Date:** 2026-09-28
**Status:** In progress — foundation landed, `diff_judge` mid-build

## Goal

Introduce TypeSafe's Jev System-One model into dope as a source of typed,
calibrated semantic judgments over code changes. Jev complements — does not
replace — the existing pydantic-ai agents: it fronts the pipeline with cheap
constrained decisions, so the existing free-form generation (doc rewrites,
change summaries) only runs when the judgments say it should.

## Integration path

pydantic-ai 2.45+ ships first-class TypeSafe support. dope is already on
pydantic-ai 2.51.0, so integration is native rather than parallel SDKs.

- Extra: `pydantic-ai[typesafe]` (installs `typesafe-sdk` as a peer dep).
- Model class: `pydantic_ai.models.typesafe.TypeSafeModel`.
- Provider: `pydantic_ai.providers.typesafe.TypeSafeProvider` (auto-reads
  `TYPESAFE_API_KEY` from env when no `api_key` is passed).
- Model IDs available today: `jev-latest`, `jev-preview`.

**Primitive → output_type mapping** (as documented by pydantic-ai):

| Jev primitive | `output_type` on the Agent |
| --- | --- |
| Noul (yes/no with probability) | `bool` |
| Choice (pick one) | `Enum` or `Literal[...]` |
| Score (ordinal rubric) | `int` with per-level descriptions in `instructions` |

Trade-off accepted: pydantic-ai wraps one question per Agent, so batching six
judgments takes six concurrent Agents via `asyncio.gather` rather than a single
`system_one()` call. Wall-clock stays ~180 ms (parallel), but we lose the
docs-cited ~11× token efficiency of true batching. Acceptable for now because
it keeps the whole codebase on one client library; direct `typesafe-sdk` usage
is a follow-up if cost/latency measurement warrants it.

## Opportunity map (ranked)

The full inventory of Jev opportunities identified in the repo, in priority
order. `diff_judge` (opportunity 10 below) is the first bite because it lands
the framework in one place and its outputs feed several downstream targets.

### Tier 1 — Rule-based today, semantic tomorrow

1. **`ScopeAlignmentFilter._calculate_relevance`** — `dope/services/suggester/scope_filter.py:211-267`
   Replace `fnmatch + category + magnitude + term-overlap` sum with a `Score`
   or `Noul` per (diff, section). Highest quality leverage in the repo.
2. **`infer_change_category`** — `dope/core/classification.py:210-278`
   Path-substring guessing → `Choice` over `ChangeCategory` on diff content.
3. **`FileClassifier.classify` HIGH vs NORMAL** — `dope/core/classification.py:128-165`
   Fnmatch globs → `Noul` "is this file doc-critical?"

### Tier 2 — Constrained pydantic-ai calls → cheaper, calibrated Jev

4. **`get_project_complexity_agent`** — `dope/services/scoper/scoper_agents.py`
   `gpt-4.1-mini` picking one of 5 ordered `ProjectTier` values → `Score`.
5. **Suggester decomposition** — `dope/services/suggester/suggester_agents.py`
   Split the single `o4-mini` call into: `Noul` (needs docs?) + `Choice` (which
   doc file?) + `Choice` over `ChangeType`. Keep pydantic-ai for the prose body.
6. **`get_scope_creator_agent` per-section mapping** — same file
   Per-entry `Choice` over candidate paths.

### Tier 3 — Verification layer (new capability)

7. **Pre-apply citation check** — before `dope apply`
   `Choice` "does this suggested edit actually address the linked change?" —
   confidence threshold gates auto-apply vs. surface-to-user.

### New capabilities (not replacements)

8. **Doc staleness scan.** `Noul`/`Score` over doc sections **without** a
   triggering diff. Powers a proposed `dope audit` command. `FreshnessLevel`
   in `dope/models/domain/scope.py:13-22` is a ready-made `Score` ladder.
9. **Doc contradiction detector.** Pairwise `Noul` on related section summaries.
10. **One-diff, six-questions (`diff_judge`).** Extract structured metadata
    from every diff up front. **This is the current build.**
11. **Duplicate suggestion detection.** `Noul` "do these two suggestions
    describe the same doc change?" — merge before user sees them.
12. **Calibrated priority.** Replace `_get_significance_label`
    (`change_processor.py:10-16`) magnitude bucketing with `Score` "how
    important is documenting this?".
13. **Completeness check.** `Noul` "does this suggestion fully address the
    change, or only partially?" — flag partials.
14. **Decomposable relevance.** Split opaque relevance `Score` into 3-4
    `Noul`s (topical / terminology / API-surface / example overlap) — user can
    re-weight in config without rerunning inference.

## Current build: `diff_judge`

For each diff, produce a `DiffJudgment` with six typed fields, resolved
in parallel via six pydantic-ai Agents backed by `TypeSafeModel`.

### `DiffJudgment` shape (`dope/models/domain/judgment.py`)

| Field | Primitive | Type | Backing enum |
| --- | --- | --- | --- |
| `change_category` | Choice | `ChangeCategory` | `dope/core/classification.py:14` |
| `change_type` | Choice | `ChangeType` | `dope/models/enums.py:13` |
| `is_breaking` | Noul | `bool` | — |
| `is_user_facing` | Noul | `bool` | — |
| `needs_docs` | Noul | `bool` | — |
| `doc_priority` | Choice-over-levels | `Literal[0, 1, 2, 3, 4]` | inline rubric in instructions |

**Gotcha discovered during smoke test:** pydantic-ai's TypeSafe adapter does
**not** accept a bare `int` output type ("Output field 'response' is not
supported by this model"). Supported forms are `bool`, `Enum`/`Literal` of
2+ strings-or-whole-numbers, `float` bounded `[0, 1]`, `list` of `Literal`/
`Enum`, or a proper **rubric** — which requires the JSON schema to carry
`anyOf`/`const` with a description per level (see
`pydantic_ai.models.decision._rubric`). A bare `Literal[0, 1, 2, 3, 4]`
resolves to Choice-over-numbers, which is what we ship. True Score semantics
(probability-weighted expected value across ordered levels) is a follow-up
that requires a proper rubric type.

Calibrated confidence is **not** exposed in v1 — pydantic-ai returns the typed
value only, and the exact `RunResult` field for confidence is unverified. Added
as a follow-up.

### Module layout

```
dope/services/judge/
    __init__.py           # public re-exports
    judge_agents.py       # six @lru_cache pydantic-ai Agents
    judge_service.py      # async judge_diff(diff: str) -> DiffJudgment
    prompts.py            # per-question instructions + Score rubric
tests/unit/services/judge/
    __init__.py
    judge_service_test.py # mock Agent.run(), assert assembly
```

Placement rationale: mirrors the existing `describer/`, `changer/`,
`suggester/`, `scoper/` service structure (`*_agents.py` + `*_service.py` +
`prompts.py`) so callers and reviewers don't have to learn a new pattern.

### Where `diff_judge` gets called (deferred, not this PR)

Natural landing spot is inside `CodeDescriberService._run_agent_async`
(`dope/services/describer/describer_base.py:452-463`), where the git diff is
already loaded. Wiring is a **separate PR** to keep this change small:

1. Ship the judge module + tests standalone.
2. Verify against a real Jev call.
3. Add a call site + persist `DiffJudgment` into the state metadata dict.
4. Downstream consumers (`scope_filter`, `change_processor`) start reading
   `state[file]["judgment"]` instead of running their fnmatch heuristics.

## Implementation checklist

Progress captured in the task list; canonical status here.

- [x] `uv add "pydantic-ai[typesafe]"` — installed `typesafe-sdk==0.7.2`.
      Note: initial install left `griffe/__init__.py` missing (hardlink
      fallback bug); fixed with `UV_LINK_MODE=copy uv sync --reinstall-package griffelib`.
      Consider setting `UV_LINK_MODE=copy` in devcontainer if it recurs.
- [x] `dope/llms/model_factory.py` — added `get_typesafe_model()` and
      imports for `TypeSafeModel` / `TypeSafeModelName`.
- [x] `dope/models/domain/judgment.py` — `DiffJudgment` model + export from
      `dope.models.domain.__init__`.
- [x] `dope/services/judge/{__init__,judge_agents,judge_service,prompts}.py`.
- [x] `tests/unit/services/judge/judge_service_test.py`.
- [x] `uv run ruff check --fix .` / `uv run prek run --all-files` / `uv run pytest`.
- [x] `TypeSafeSettings` group in `dope/models/settings.py`; `get_typesafe_model()`
      now reads `settings.typesafe.api_key` and raises `AgentNotConfiguredError`
      if unset. Env var: `typesafe__API_KEY` (double-underscore delimiter,
      matches `agent__TOKEN`).
- [x] End-to-end smoke against a real Jev call — passes with a synthetic
      "add new CLI command" diff, returns
      `{feature, add, is_breaking=false, is_user_facing=true, needs_docs=true,
      doc_priority=2}`. Fixed a `doc_priority: int` output type that Jev
      rejected — switched to `Literal[0, 1, 2, 3, 4]`. Also caught: the .env
      key must use `typesafe__API_KEY` (double underscore), single-underscore
      is silently ignored.

## Model migration to GPT-5.6 family

Migrated all seven OpenAI callsites off the deprecated `gpt-4.1*` / `o4-mini`
lineage to the GPT-5.6 tiers:

| Callsite | Was | Now |
| --- | --- | --- |
| `describer/get_code_change_agent` | gpt-4.1-mini | `gpt-5.6-luna` |
| `describer/get_doc_summarization_agent` | gpt-4.1-mini | `gpt-5.6-luna` |
| `scoper/get_project_complexity_agent` | gpt-4.1-mini | `gpt-5.6-luna` |
| `scoper/get_scope_creator_agent` | gpt-4.1 | `gpt-5.6-terra` |
| `suggester/get_suggester_agent` | o4-mini | `gpt-5.6-terra` |
| `changer/get_changer_agent` | gpt-4.1 | `gpt-5.6-sol` |
| `scoper/get_doc_aligner_agent` | gpt-4.1 | `gpt-5.6-sol` |

**Required fix during migration:** the GPT-5.6 family rejects function tools
under `/v1/chat/completions` unless `reasoning_effort='none'`. Baked into
`get_model()` in `dope/llms/model_factory.py` via `OpenAIChatModelSettings`;
no-op on older models.

## End-to-end integration test

Ran `dope scan docs && dope scan code --branch main && dope suggest` against
the uncommitted changes on this branch (model rename + TypeSafe integration).
Result: **2 accurate suggestions** covering README.md and QUICKSTART.md that
correctly identified the model rename across all four services, the new
TypeSafe settings group, the new `DiffJudgment` domain model, and the
dependency bump.

Known limitation: the all-in-one `dope update` command hits a pre-existing
`RuntimeError: Event loop is closed` because `get_retry_client()` in
`dope/llms/retry_config.py` `@lru_cache`s an `httpx.AsyncClient` that binds
to the first event loop, which is then closed by subsequent `asyncio.run()`
calls in the pipeline. Not related to this PR's changes; worth a small
follow-up to either recreate the client per event loop or migrate to
`AsyncHTTPX2TenacityTransport` per pydantic-ai's deprecation warning.

## Event-loop bug fix (`dope update`)

`dope update` previously crashed with `RuntimeError: Event loop is closed`
because every LLM factory in the chain (`get_retry_client`, both provider
factories, all agent factories) was decorated with `@lru_cache`. Each cached
value transitively held an `httpx.AsyncClient` bound to the event loop that
first touched it, but the pipeline runs three back-to-back `asyncio.run()`
calls (scan docs → scan code → suggest), each of which closes its loop.
When the third phase opened a fresh loop and asked the cache for the agent,
it got the stale one and the retry client's socket cleanup blew up.

Fix: new `dope/core/loop_cache.py` exposes `loop_scoped_cache`, a decorator
that keys entries by the running event loop (via a
`weakref.WeakKeyDictionary`, since `id(loop)` gets reused after GC). Applied
to `get_retry_client`, `_get_openai_provider`, `_get_typesafe_provider`, and
every `*_agents.py` factory (12 sites). Fresh loop → fresh entry; same loop
→ same entry (pooling preserved).

## `diff_judge` wired into `CodeDescriberService`

`_run_agent_async` in `dope/services/describer/describer_base.py` now runs
the summary agent and `judge_diff` concurrently via `asyncio.gather`, and
attaches the judgment under `summary["judgment"]` in the state dict. Gated
on `settings.typesafe.api_key` being set — pipeline still works for users
without TypeSafe.

**Usage-limit gotcha:** the six Jev calls per file must run outside the
shared `UsageTracker`, otherwise pydantic-ai's default per-run
`request_limit=50` fires within a handful of files. Fix: pass no tracker to
`judge_diff`. Downside: Jev tokens aren't in the CLI's total-tokens line;
acceptable given they're cheap and the tracker is primarily an OpenAI
cost/limit signal.

## End-to-end validation (post-fixes)

`dope update --dry-run` now runs cleanly in one process (no crash). With
`diff_judge` enriching the code state, the suggester produced **5**
suggestions vs 2 previously — README, QUICKSTART, CHANGELOG, CONTRIBUTING,
and an architecture analysis doc — because the enriched judgments give it
signal about which changes are user-facing and priority.

## Follow-ups (out of scope for this PR)

- Land opportunities 2 and 4 from the map (`ChangeCategory` `Choice`,
  `ProjectTier` `Score`) — smallest surface area next.
- Investigate exposing confidence on `DiffJudgment` (may require reaching
  into `RunResult` or a small `typesafe-sdk` shim for the batched case).
- Evaluate whether the six-agents-parallel pattern is worth swapping for a
  direct `system_one()` batched call once we have real latency/cost numbers.
- Migrate `retry_config.py` from `AsyncTenacityTransport` +
  `httpx.AsyncClient` to `AsyncHTTPX2TenacityTransport` + `httpx2.AsyncClient`
  per pydantic-ai's deprecation warning (unrelated but nearby).

## Non-goals

- **`changer` service** (full doc rewrites) — genuine free-form generation,
  stays on pydantic-ai + OpenAI/Azure.
- **`describer` summaries** — extraction with tools, stays as-is.
- **`AlignedScope.content`** — free-form output, stays as-is.
- Adding a new provider abstraction for TypeSafe in `AgentSettings`. Env-based
  auth is idiomatic and requires no schema changes.

# Eval-driven cost & precision optimization

**Author:** Martin Gran (with Claude Opus 4.7)
**Date:** 2026-09-29
**Status:** Landed. Follow-ups documented at the bottom.

## Why this work happened

dope is about **changing docs just enough, and being precise about what
to communicate**. Off-the-shelf LLM behavior tends to fail on either
edge — models over-rewrite ("while I'm here, let me improve that intro
too") or they miss the important bits (broad summaries that skip the
API rename). The goal of this session was to:

1. Build eval infrastructure that MEASURES both failure modes.
2. Use it to A/B cost-optimize every LLM callsite in dope.
3. Wire the TypeSafe/Jev integration through so its typed judgments
   actually influence what the suggester does.
4. Fix production bugs surfaced along the way.

Everything below is either shipped or explicitly documented as
unfinished follow-up.

## Architecture that got built

### `evals/` package

Six eval suites, one per agent-shaped callsite, each a pydantic-evals
`Dataset` + custom `Evaluator`s + optional A/B runner:

| Suite | Fixtures | What it scores |
|---|---:|---|
| `evals.judge_eval` | 10 | Per-field accuracy on the six Jev fields |
| `evals.project_complexity_eval` | 6 | Tier exact-match + within-1 ordinal distance |
| `evals.suggester_eval` | 15 | File-path F1 + change_type accuracy |
| `evals.changer_eval` | 17 | 5 LLMJudge rubrics + `ContentSimilarity` + `PreservedSpecifics` |
| `evals.scope_creator_eval` | 8 | Key coverage + path accuracy + no-extra-keys |
| `evals.doc_aligner_eval` | 7 | 5 LLMJudge rubrics + `ContentSimilarity` + `PreservedSpecifics` + `CrossFileChangesCount` |

Every suite also records `cost_usd`, `tokens`, `requests`, and
per-case duration via a shared `UsageTracker` side channel and a
`CostMetrics` evaluator. Full sweep across all six suites costs
~$0.20 and finishes in <60 seconds.

**Over-change specific instrumentation** (added after the
"changing too aggressively" review):

- `ContentSimilarity` — `difflib.SequenceMatcher(input, output).ratio()`
  as an observability metric. Higher = smaller edit surface.
- `char_delta_ratio` — `abs(len(out) - len(in)) / max(len(in), 1)`
  as a "did the model bloat the doc" signal.
- `PreservedSpecifics` — fraction of a fixture-declared list of
  substrings that survive verbatim (version strings, exact command
  syntax, config keys, stylistic quirks).
- A fifth LLMJudge rubric on the changer and aligner —
  `minimal_change`: "did the model make ONLY the requested edit or
  also rephrase / reorganize unrelated content?"

### A/B runners

Six of them, each pairs a baseline (production defaults) with a
challenger, uses `pydantic-evals`' native `report.print(baseline=...)`
diff renderer for the delta table:

| Runner | Axis | Default match |
|---|---|---|
| `evals.suggester_ab` | model | luna vs terra |
| `evals.changer_ab` | model | sol vs terra |
| `evals.scope_creator_ab` | model | terra vs luna |
| `evals.doc_aligner_ab` | model | sol vs terra |
| `evals.changer_prompt_ab` | `change.system` prompt version | v1 vs v2-minimal |
| `evals.doc_aligner_prompt_ab` | `scope.align_doc` version | v1 vs v2-minimal |
| `evals.suggester_prompt_ab` | `suggest.system` version | v1 vs v2-judgment |
| `evals.suggester_gate_ab` | `enable_judgment_gate` flag | off vs on |
| `evals.doc_aligner_diff_ab` | output-type architecture | full-content vs `EditedScope` (v3-diff) |

### `dope/prompts/` — versioned prompt registry

Every LLM-facing prompt in dope now lives in `dope/prompts/` as a
versioned `Prompt(name, version, template, description)`. A
`PromptRegistry.get(name, version=None)` resolves the request through
`dope/prompts/production.yaml`, which pins the live version per name.
Rolling back a bad prompt change is one line in that manifest, tracked
by git.

Structure:

```
dope/prompts/
├── __init__.py           # Prompt dataclass + PromptRegistry class
├── production.yaml       # {name: version} manifest of what's live
├── describe.py           # describer prompts (system + user templates)
├── suggest.py            # suggester prompts (v1, v2-judgment)
├── change.py             # changer prompts (v1, v2-minimal)
├── scope.py              # scoper prompts (v1, v2-minimal, v3-diff)
└── judge.py              # 6 Jev instruction prompts
```

20 prompts registered, 3 with multi-version A/B history.

### TypeSafe/Jev integration wired through

The judge already fired six Jev agents per file describer call (from a
prior session, commit ff7bd9a). This session made the outputs
ACTUALLY do something:

- `change_processor._build_metadata_dict` lifts `Jev Category`,
  `Breaking Change`, `User-Facing`, `Needs Docs`, `Doc Priority`, and
  `Jev Change Type` into the suggester's prompt metadata.
- `sort_by_priority` ranks by HIGH-priority first, then Jev
  `doc_priority` desc, then magnitude desc. Files without a judgment
  fall back to priority=-1 (still work, degrade to old ordering).
- New `filter_by_judgment_needs_docs()` function drops entries with
  explicit `needs_docs=false`. Gated behind
  `ScopeFilterSettings.enable_judgment_gate` (**default now True** as
  of commit badee33).
- New `suggest.system v2-judgment` prompt version teaches the model
  to weigh each judgment field. Registered but **not** promoted —
  see A/B results below.

## Cost + accuracy wins landed in production

### Model flips (all backed by A/B on eval fixtures)

| Service | Before | After | Basis |
|---|---|---|---|
| `suggester` | gpt-5.6-terra | gpt-5.6-luna | 15 fixtures, +2.5% F1, -87.7% cost (commit 5243810) |
| `changer` | gpt-5.6-sol | gpt-5.6-terra | 17 fixtures, +2.1pp assertion, -44.9% cost (commit badee33) |
| `scoper.doc_aligner` | gpt-5.6-sol | gpt-5.6-terra | 7 fixtures, accuracy unchanged, -45.7% cost |
| `scoper.scope_creator` | gpt-5.6-terra | gpt-5.6-luna | 8 fixtures, -3.2pp path acc, -89.9% cost (rarely-run service; trade accepted) |

**Zero `gpt-5.6-sol` callsites remain.** Combined workflow cost is
roughly 70% below where it started this session.

### Prompt promotions

- `scope.align_doc` v1 → **v2-minimal** (production.yaml)
  - 7 fixtures on sol: 91.4% → 100.0% assertion pass rate,
    content_similarity 0.58 → 0.74 (+27%), preserved_specifics
    0.83 → 1.00, at +9.2% cost (larger prompt).
  - Explicit "MINIMALITY (STRICT)" clause forbidding rephrasing,
    expansion, or style-correction of untouched content.
- `change.system` v2-minimal registered but not promoted — changer
  was already restrained by the existing "Output only the changed
  file in full" wording; A/B was marginal at +15% cost.
- `suggest.system` v2-judgment registered but not promoted — A/B
  showed +3.7% precision but -6.7% recall trade; the metadata wiring
  already delivered the strict-win portion (v1 F1 went 0.889 → 1.000
  on enriched fixtures) so the prompt guidance is preference-dependent.

### Judgment gate

`enable_judgment_gate: true` is now the default. On files where the
Jev DiffJudgment says `needs_docs=false`, the suggester short-circuits
before the LLM runs. On the 15-fixture suggester suite this cut
requests by 33% and cost by 13% with zero accuracy impact (the five
gated fixtures all expected empty suggestions anyway).

Filter is a no-op on files without a judgment attached, so repos
without TypeSafe configured see identical behavior.

### Production bug fixes

- `request_limit=50` crash on real-world diffs: pydantic-ai defaults
  `UsageLimits.request_limit=50` per run. dope shares one
  `UsageTracker` across every phase, so any repo with 45+ describer
  files crashed mid-run. Fixed with `DEFAULT_USAGE_LIMITS =
  UsageLimits(request_limit=None)` in `dope/llms/usage_limits.py`,
  threaded into all 15 `agent.run()` / `run_sync()` callsites.
  Verified by re-running the 110-file `dope update` that had killed
  the workflow before — now completes end-to-end at 219k tokens.
- `httpx.AsyncClient` deprecation: pydantic-ai deprecated the old
  client in the retry transport plumbing. Migrated `retry_config.py`
  to `httpx2.AsyncClient` + `AsyncHTTPX2TenacityTransport`. Retry
  policy (5 tries, exponential backoff, Retry-After respect) is
  unchanged. Two deprecation warnings gone from every long-running
  command.

## Experiments that did not win

### v3-diff aligner

Attacked over-rewriting at the architectural root: swap the aligner's
`AlignedScope.content: str` output for `EditedScope` (a list of
`LineEdit` operations). The theory was that content the model doesn't
touch stays byte-identical by construction.

Reality (7 fixtures, sol):

| Metric | Full-content v2-minimal | Diff-based v3-diff | Δ |
|---|---:|---:|---|
| Assertion pass | 100.0% | 97.1% | -2.9pp |
| content_similarity | 0.765 | 0.686 | -10.2% |
| char_delta_ratio | 1.10 | 1.79 | +62.7% |
| preserved_specifics | 1.00 | 1.00 | — |
| cost | $0.00536 | $0.00596 | +11.3% |

Root cause: the model emits `replace_range` edits on lines that were
already fine — structurally allowed even though the prompt forbids it.
One case introduced a hallucination.

**Meta-value**: the eval infrastructure surfaced the underperformance
cleanly. Would have looked like a "structural fix" that quietly
regressed quality without the char-level metrics + shared fixtures.

Follow-up documented under Open work: v4-diff banning `replace_range`
at the schema level.

### Metadata surfacing vs prompt guidance for judgment

Interesting decomposition on the suggester prompt A/B:

- Just adding the judgment fields as top-level metadata in
  `_build_metadata_dict` (no prompt change) bumped v1 F1 from 0.889
  → 1.000 on the enriched fixture set. **This is where the win
  actually lives.**
- Adding the v2-judgment prompt guidance on top further reduced
  `n_produced` by 16.7% (more surgical) at the cost of 6.7% recall.
  Preference-dependent trade.

The lesson: the model already reads metadata even without prompt
instructions telling it to. Prompt guidance mostly adjusts weighting,
which trades precision for recall.

## Current production defaults

Prompts (`dope/prompts/production.yaml`):

```yaml
describe.code: v1
describe.doc: v1
describe.user_template: v1
suggest.system: v1                # v2-judgment registered, not promoted
suggest.user_template: v1
change.system: v1                 # v2-minimal registered, not promoted
change.user_template: v1
change.add_user_template: v1
scope.complexity: v1
scope.creator: v1
scope.align_doc: v2-minimal       # promoted after A/B
scope.change_file_user_template: v1
scope.complexity_user_template: v1
scope.move_content_user_template: v1
judge.*: v1                       # all six
```

Models:

```
describer.code       = gpt-5.6-luna
describer.doc        = gpt-5.6-luna
suggester            = gpt-5.6-luna
scoper.complexity    = gpt-5.6-luna
scoper.scope_creator = gpt-5.6-luna
changer              = gpt-5.6-terra
scoper.doc_aligner   = gpt-5.6-terra
judge (×6)           = typesafe:jev-latest
```

Settings:

```
scope_filter_settings.enable_judgment_gate: True
scope_filter_settings.enable_adaptive_pruning: True (unchanged)
```

## Open work

**Untested but backed by design:**

- `dope update --max-cost $N`: pre-estimate token spend and refuse
  runs that exceed a caller-provided budget. The 110-file sanity
  run this session burned 219k tokens (~$0.04 on luna); realistic
  repos could 10× that.
- Wire the full eval sweep into CI as a regression gate. Sweep costs
  ~$0.20 and takes <60s. Assert per-suite averages haven't dropped
  more than 5% vs a checked-in baseline JSON.

**Architecture experiments left as follow-ups:**

- **v4-diff aligner**: retry the diff-based output type with
  `replace_range` banned at the schema level (Literal narrowed to
  `insert_after` + `delete_range` only). The v3-diff failure was
  entirely `replace_range` abuse — the schema-only ban is the
  smallest possible next step.
- Migrate the suggester output to structured line edits too (same
  shape as `EditedScope`). Would prevent prose-heavy suggestions in
  favor of specific "add bullet X after line N" instructions.

**Documentation lift:**

- Consumer-facing docs (README, QUICKSTART) still describe the
  pre-session model matrix. `dope update` on the current branch
  suggests the update automatically (verified this session);
  running `dope apply` against those suggestions would close the
  loop.

## Commit chain (this session)

```
badee33 Land the proven wins: judgment gate on by default + 3 model flips
0bd58fb Add suggester judgment-gate A/B: strict cost cut, zero accuracy loss
6f87143 Enrich remaining 9 suggester fixtures + rerun A/B with full judgment
98fd10b Enrich 6 suggester fixtures with judgment blocks + prompt A/B runner
638826a Wire Jev DiffJudgment into the suggester pipeline
4a4ce67 Fix request_limit=50 crash + migrate to httpx2
d2ef049 Add diff-based aligner architecture (v3-diff) + apply_edits + A/B
f1a55b0 Migrate every LLM prompt to a versioned PromptRegistry
d18da00 Add 3 aligner stress fixtures + prompt A/B infra + tightened prompts
eaf3531 Add minimal-change evaluators + over-rewrite stress fixtures
b27460c Grow scope_creator to 8 fixtures + A/B both scoper services
7c3e1ce Add scope_creator + doc_aligner eval suites
cf3292f Grow changer fixtures to 12 + fix judge input serialization
5243810 Add changer eval (LLM-as-judge) + flip suggester to gpt-5.6-luna
cbc6945 Grow suggester eval to 15 cases + terra vs luna A/B runner
28b9cbe Add suggester eval suite (file-path F1, change_type)
45abc7a Add project_complexity eval suite
e10b0d1 Add judge eval suite (pydantic-evals)
```

298 tests passing. Working tree clean at commit `badee33`.

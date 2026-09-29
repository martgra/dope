"""Shared usage-limit config for every LLM call in dope.

pydantic-ai's :class:`UsageLimits` defaults to ``request_limit=50``,
which is checked against the shared :class:`RunUsage` counter passed to
``agent.run()``. dope shares one :class:`UsageTracker` across every
phase of a workflow — for example :func:`DocsChanger.apply_suggestion`
runs the changer once per suggested file, and the describer fires one
agent call per code diff. On any repo with more than ~45 items to
process the default limit trips ``UsageLimitExceeded`` and the whole
command dies mid-run.

The counter itself is useful (we surface total tokens / cost via
:class:`UsageTracker.log`), so the fix is to disable the *per-run*
request limit rather than to shard the tracker.

Pass :data:`DEFAULT_USAGE_LIMITS` explicitly to every ``agent.run()``
/ ``agent.run_sync()`` call. Adding a stricter per-run cap (cost,
tokens) is fine — construct a fresh :class:`UsageLimits` at the call
site with ``request_limit=None`` kept from here.
"""

from pydantic_ai.usage import UsageLimits

DEFAULT_USAGE_LIMITS = UsageLimits(request_limit=None)

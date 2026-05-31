# Project guidance for Claude Code

This repository's coding rules live in `.cursor/rules/` (Cursor's `.mdc`
format). Read those files instead of duplicating their content here, so the
user only maintains one set.

## Rule loading protocol

Each rule file has YAML frontmatter:

```
---
description: <selection hint>
alwaysApply: true | false
---
```

**Always-apply rules** (`alwaysApply: true`) — read these at the start of every
session **before any non-trivial code change**, and follow them throughout:

- `.cursor/rules/clean-architecture.mdc`
- `.cursor/rules/clean-code.mdc`
- `.cursor/rules/simplicity-first.mdc`
- `.cursor/rules/testing-python.mdc`

**On-demand rules** (`alwaysApply: false`) — read when the work touches the
relevant area:

| Rule file | Read when |
|---|---|
| `.cursor/rules/typescript.mdc` | editing or reviewing TypeScript code |
| `.cursor/rules/react.mdc` | editing or reviewing React components |
| `.cursor/rules/markdown.mdc` | authoring docs or Mermaid diagrams |

## Unlisted rules — discover and load

The table above is a hint, not an allowlist. Before any non-trivial code
change, enumerate `.cursor/rules/*.mdc` (e.g. `Glob ".cursor/rules/*.mdc"`).
For each file not already accounted for above:

1. Read its YAML frontmatter (`description` + `alwaysApply`).
2. If `alwaysApply: true` — read the whole file and follow it for the rest of
   the session, exactly like the listed always-apply rules.
3. If `alwaysApply: false` — judge from the `description` whether it applies
   to the current task. If yes, read the whole file before continuing. If
   unsure, read it anyway — a brief read is cheaper than a missed rule.

This way new rule files added by the user take effect immediately without
requiring an edit to `CLAUDE.md`.

## Conflicts

If a rule conflicts with a direct user instruction in the current session, the
user wins. Flag the conflict so they can decide whether to update the rule.

If two rules conflict, the more specific one wins (e.g. `php.mdc` over the
language-agnostic `clean-code.mdc`).

## Additional Rules
These rules apply to every task in this project unless explicitly overridden.
Bias: caution over speed on non-trivial work. Use judgment on trivial tasks.

## Rule 1 — Think Before Coding
State assumptions explicitly. If uncertain, ask rather than guess.
Present multiple interpretations when ambiguity exists.
Push back when a simpler approach exists.
Stop when confused. Name what's unclear.

## Rule 2 — Simplicity First
Minimum code that solves the problem. Nothing speculative.
No features beyond what was asked. No abstractions for single-use code.
Test: would a senior engineer say this is overcomplicated? If yes, simplify.

## Rule 3 — Surgical Changes
Touch only what you must. Clean up only your own mess.
Don't "improve" adjacent code, comments, or formatting.
Don't refactor what isn't broken. Match existing style.

## Rule 4 — Goal-Driven Execution
Define success criteria. Loop until verified.
Don't follow steps. Define success and iterate.
Strong success criteria let you loop independently.

## Rule 5 — Use the model only for judgment calls
Use me for: classification, drafting, summarization, extraction.
Do NOT use me for: routing, retries, deterministic transforms.
If code can answer, code answers.

## Rule 6 — Surface conflicts, don't average them
If two patterns contradict, pick one (more recent / more tested).
Explain why. Flag the other for cleanup.
Don't blend conflicting patterns.

## Rule 7 — Read before you write
Before adding code, read exports, immediate callers, shared utilities.
"Looks orthogonal" is dangerous. If unsure why code is structured a way, ask.

## Rule 8 — Tests verify intent, not just behavior
Tests must encode WHY behavior matters, not just WHAT it does.
A test that can't fail when business logic changes is wrong.

## Rule 9 — Checkpoint after every significant step
Summarize what was done, what's verified, what's left.
Don't continue from a state you can't describe back.
If you lose track, stop and restate.

## Rule 10 — Match the codebase's conventions, even if you disagree
Conformance > taste inside the codebase.
If you genuinely think a convention is harmful, surface it. Don't fork silently.

## Rule 11 — Fail loud
"Completed" is wrong if anything was skipped silently.
"Tests pass" is wrong if any were skipped.
Default to surfacing uncertainty, not hiding it.

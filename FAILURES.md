# Dimension & Weight Integrity — Failure Log

What was attempted that didn't work, why it didn't work, and what was
tried next.

Lower bar than DECISIONS.md — capture failures even when they didn't
produce a durable rule. The whole point: future-you (or future-Claude)
shouldn't re-attempt dead ends because the lesson got lost.

---

## Format

### YYYY-MM-DD — [One-line failure description]

**Attempted:** [What was tried]

**Why it didn't work:** [Concrete reason]

**What we tried instead:** [The next attempt]

**Status:** Resolved / open / abandoned

**Tags:** [keywords for future text-search]

---

## Entries

### 2026-06-04 — Vitest tests fail silently when globals: true is missing

**Attempted:** Ran frontend tests with default vitest config (no `globals: true`).

**Why it didn't work:** @testing-library/react detects the test framework by checking for global `afterEach`. Without `globals: true`, vitest doesn't expose this global, so cleanup never runs. DOM accumulates across tests — 4 of 5 ChapterNav tests failed because multiple renders stacked in the same document body.

**What we tried instead:** Added `globals: true` to vitest config in `vite.config.ts`. All tests passed immediately.

**Status:** Resolved

**Tags:** vitest, testing-library, globals, cleanup, DOM

---

### 2026-06-04 — Agent worktree isolation unavailable despite valid git repo

**Attempted:** Dispatched U11–U14 subagents with `isolation: "worktree"` for parallel file writes.

**Why it didn't work:** Agent tool returned "Cannot create agent worktree: not in a git repository" even though `git status` worked fine from PowerShell. Likely a platform-level detection issue on Windows.

**What we tried instead:** Fell back to shared-directory dispatch with constraints: subagents instructed not to run `git add`, `git commit`, or the full test suite. All 4 agents wrote to `styles.css` sequentially without collision — verified post-completion that all styles were present.

**Status:** Resolved (workaround)

**Tags:** worktree, subagent, parallel, isolation, windows

---

### 2026-06-04 — TypeScript strict errors after U10 scaffold

**Attempted:** Built frontend scaffold with `CHAPTER_ORDER[idx + 1]` array access and unused params in domain.ts.

**Why it didn't work:** `CHAPTER_ORDER[idx + 1]` returns `Chapter | undefined`, but `navigate()` expects `Chapter`. Four params in `computeParadox` were declared but unused, triggering noUnusedParameters.

**What we tried instead:** Wrapped array access with `const next = CHAPTER_ORDER[idx + 1]; if (next) { navigate(next) }`. Prefixed unused params with underscore (`_rateTables`, `_heroMor`, `_gdsn`, `_parcel`).

**Status:** Resolved

**Tags:** typescript, strict, unused-params, array-access

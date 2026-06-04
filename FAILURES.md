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

---

### 2026-06-04 — Runtime assertion broke app by assuming all_skus.json is an array

**Attempted:** Replaced `as unknown as AllSkusData` with runtime assertion `assertAllSkusData` that checked `Array.isArray(data)`.

**Why it didn't work:** `AllSkusData` is `{ skus: SkuSummary[], aggregate: {...} }` — an object with a `skus` array inside, not an array itself. The assertion threw immediately on import, breaking the entire app. Vite HMR couldn't recover.

**What we tried instead:** Fixed the assertion to check `Array.isArray(obj.skus) && obj.aggregate` instead. Had to restart the dev server because HMR was stuck on the old error.

**Status:** Resolved

**Tags:** typescript, runtime-assertion, type-guard, vite-hmr

---

### 2026-06-04 — Dead import survives dev server, tests, and code review — only caught by production build

**Attempted:** `domain.ts` line 1 had `import type { RateTables } from './types'` — a leftover from an earlier refactor. Dev server, Vitest, and code review all passed.

**Why it didn't work:** Vite dev server and Vitest use esbuild for transforms, which strips type-only imports without running `tsc -b`. The unused import only fails during `npm run build` (which runs `tsc -b`). Code review agents didn't run the production build either.

**What we tried instead:** Removed the dead import. Added production build verification to the QA checklist.

**Status:** Resolved

**Tags:** typescript, dead-import, production-build, tsc, vite, esbuild

---

### 2026-06-04 — Wrangler CLI lacks pages domain and DNS commands

**Attempted:** Tried `npx wrangler pages project add-domain` to register custom domain, and used wrangler's OAuth token for DNS record creation.

**Why it didn't work:** `add-domain` subcommand doesn't exist in wrangler. The wrangler OAuth token has `zone:read` scope but not DNS write — returned authentication error on `POST dns_records`.

**What we tried instead:** Used Cloudflare REST API directly for both domain registration (`POST /pages/projects/.../domains`) and DNS record creation (`POST /zones/.../dns_records`) with a separate API token that had DNS write permissions.

**Status:** Resolved

**Tags:** cloudflare, wrangler, pages, dns, api, custom-domain

---

### 2026-06-04 — preview_screenshot consistently times out on Windows

**Attempted:** Used `preview_screenshot` during QA testing — timed out at 30s on every attempt.

**Why it didn't work:** Appears to be a renderer/tooling issue on Windows, not an app problem. The preview server was responsive and all other preview tools worked.

**What we tried instead:** Used `preview_snapshot` (DOM text), `preview_inspect` (CSS values), and `preview_eval` (JS assertions) for all verification. Full QA coverage achieved without screenshots.

**Status:** Open (tooling limitation, not project issue)

**Tags:** preview-tools, screenshot, windows, qa, timeout

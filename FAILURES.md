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

### 2026-07-27 — Reading the DOM in the same tick as a click reported a working feature as broken

**Attempted:** Verified the Paradox toggles by clicking "Fix Retail", "Fix DTC", and "Current State" and snapshotting the DOM — all inside one synchronous `javascript_tool` call.

**Why it didn't work:** React re-renders asynchronously. All three snapshots returned identical values, which looked exactly like "the toggles do nothing." The feature was fine; the measurement was wrong. This nearly became a false bug report on working code.

**What we tried instead:** Split click and read into separate tool calls (or `await` a timeout between them). Both toggles then showed correct mirror-image behavior — Fix Retail zeroes LTL + chargebacks, Fix DTC zeroes parcel.

**Status:** Resolved

**Tags:** react, async-render, browser-tools, false-positive, verification-method

---

### 2026-07-27 — Docker Desktop cannot be started headlessly for a pipeline rebuild

**Attempted:** Needed a Postgres to rebuild dbt marts. Local PG was down, so launched Docker Desktop via `Start-Process` and polled `docker info` for 180s.

**Why it didn't work:** The CLI is installed but the daemon never came up — Docker Desktop on this machine needs an interactive start (known recurring stale-socket crash loop). Polling just burned three minutes.

**What we tried instead:** Native Postgres 16 at `C:\Users\mssha\tools\pg16` on port 5433 (the documented workaround), with a **throwaway `dwi_rebuild` database** so the real `cinderhaven` DB was never touched. Loaded the committed raw CSVs, ran `dbt build`, re-exported, dropped the DB. Worth knowing: dbt only sources the 4 raw system tables, so the whole rebuild works offline from committed data — no Fly DB or `product_master` needed.

**Status:** Resolved (workaround)

**Tags:** docker, postgres, pg16, dbt, rebuild, offline, windows

---

### 2026-07-27 — Browser pane not compositing kills screenshots AND synthetic key presses

**Attempted:** Verified the new keyboard-accessibility fix by focusing a sort header and sending Enter via the browser `computer` tool (tried both "Return" and "Enter").

**Why it didn't work:** The Browser pane wasn't displayed, so the page never composites frames. Screenshots time out (same root cause as the 2026-06-04 entry below), and input events are not dispatched either — focus persisted on the button but the key never activated it. A programmatic `.click()` proved the handler was fine, isolating it to input dispatch.

**What we tried instead:** Proved keyboard operability with real Vitest + `userEvent.keyboard('{Enter}')` tests instead. Better outcome anyway — it runs in CI permanently rather than being a one-off manual check.

**Status:** Open (tooling limitation, not project issue)

**Tags:** browser-tools, screenshot, keyboard, input-dispatch, windows, a11y-testing

---

### 2026-06-04 — preview_screenshot consistently times out on Windows

**Attempted:** Used `preview_screenshot` during QA testing — timed out at 30s on every attempt.

**Why it didn't work:** Appears to be a renderer/tooling issue on Windows, not an app problem. The preview server was responsive and all other preview tools worked.

**What we tried instead:** Used `preview_snapshot` (DOM text), `preview_inspect` (CSS values), and `preview_eval` (JS assertions) for all verification. Full QA coverage achieved without screenshots.

**Status:** Open (tooling limitation, not project issue)

**Tags:** preview-tools, screenshot, windows, qa, timeout

---

### 2026-07-28 — Handed-down review finding prescribed the wrong fix for the LTL defect

**Attempted:** Implementing a Tier C fix list's Critical as written: "LTL delta is priced on a case, not a pallet — reprice the rate delta onto a pallet weight (40 × 21.50 lb = 8.60 cwt, Δ $15.48/pallet)." The finding noted no `ti`/`hi`/`cases_per_pallet` column existed and said "that field has to be generated first." Two strict-xfail tests already encoded this reading, asserting the cost basis would name a `shipped_unit_weight_lb` heavier than one case.

**Why it didn't work:** LTL is billed per hundredweight, so a reclassification penalty falls on tonnage shipped, not on how it is stacked. `cases_per_pallet` cancels out of the product entirely:

```
(cases_per_pallet × case_lb/100) × rate_delta × pallets_per_year
  == (case_lb/100) × rate_delta × annual_cases
```

`per_unit_delta` was therefore already correct as $/case. The only defect was the multiplier — a count of pallet *shipments* against a $/case figure. Implementing the finding would have added a physical field the model does not need and double-counted the pallet term. The related "confirm alongside: 52 vs 520 pallets/yr" was likewise the wrong axis: both are asserted pallet counts with no source, which is exactly why they compounded.

**What we tried instead:** Left `per_unit_delta` and all physics untouched; replaced only the multiplier with an annual case count derived from figures the dataset already discloses ($25M ÷ 50 SKUs ÷ `wholesale_price_per_unit` ÷ per-SKU `case_pack_qty`). One sourced price replaced two unsourced volumes. The two xfail tests encoded the wrong diagnosis and were rewritten to pin the actual unit contract. Correction recorded next to the original in PLAN.md.

**Status:** Resolved

**Tags:** ltl, freight, hundredweight, units, cwt, cases-per-pallet, ti-hi, review-findings, wrong-diagnosis, cost-model

---

### 2026-07-28 — Two more review findings failed verification: a false premise and a fix that made things worse

**Attempted:** Taking two further findings from the same fix list at face value — (1) "all four committed CSVs fail UTF-8 decode, which breaks `load_csvs_to_raw` on any Linux or macOS checkout"; (2) "status pills put white text on HK-35 (4.0:1) and Singapore-55 (2.5:1); use HK-5 and Singapore-8."

**Why it didn't work:**
1. `data/generated/` is in `.gitignore` and `git log -- data/generated/` is empty — the CSVs were **never committed**. A fresh clone has no CSVs at all, so the stated blast radius could not happen. (A stored project memory had carried the same false "committed CSVs" claim for months.)
2. The Singapore half was right (Singapore-8 on Singapore-55 = 5.33:1). The Hong Kong half was backwards: HK-5 text on an HK-35 fill measures **3.03:1**, worse than the 4.02:1 white it was meant to replace.

**What we tried instead:** The encoding fix was still worth making, but for the real reason — the pipeline hands these files between steps, so the generator and loader must agree on encoding regardless of git. For contrast, darkened the *fill* to HK-25 and kept white text (6.18:1) rather than darkening the text. Both ratios computed from the WCAG formula and confirmed against the browser's computed styles. Corrected the stale memory.

**Status:** Resolved

**Tags:** review-findings, verification, gitignore, utf-8, encoding, wcag, contrast, design-system, memory-drift

---

### 2026-07-28 — Ranked a parameter's leverage by gut, then measured the opposite

**Attempted:** Called `annual_wholesale_revenue_per_sku` (the even $25M/50 split) redistributable "without much changing the size" of the portfolio total, and ranked `annual_dtc_orders_per_sku` above it as the higher-leverage open assumption. Both from plausibility, not measurement.

**Why it didn't work:** The total is `sum(w_i * revenue_i)` with `w_i = per_unit_delta_i / (price * case_pack_i)`. Only 20 of 50 SKUs have `w > 0` and `w` spans 5.1x across them, so an even split is invariant to redistribution only in expectation and only under zero volume/divergence correlation — and even uncorrelated the realized total carries a 30% standard deviation (structural in the dataset, not a modelling choice). Across an 80/20 Pareto split the LTL lane ranges $48K-$548K. The revenue split is an allocation; `wholesale_price_per_unit` is a linear scalar that cannot reorder SKUs. The allocation is far higher-leverage — the reverse of the ranking.

**What we tried instead:** Measured it (20k-shuffle Monte Carlo + best/worst correlation bounds), recorded the band in the config SENSITIVITY block and PLAN.md, and adopted the rule: rank parameter risk by whether a value can REORDER SKUs or only RESCALE them, times uncertainty — allocations dominate scalars. Same failure mode as asserting a figure instead of computing it, one level up.

**Status:** Resolved

**Tags:** sensitivity-analysis, parameter-leverage, allocation-vs-scalar, monte-carlo, revenue-split, ranking, cinderhaven

---

### 2026-07-28 — Almost reported a layout bug from an unlaid-out browser tab

**Attempted:** Measured the new hero range line in a freshly opened preview tab; the first read showed 87px-wide body text and `document.scrollWidth > clientWidth` (horizontal scroll). Started to treat it as a real responsive-layout defect.

**Why it didn't work:** The reading included `innerWidth: 0` — the tab had no laid-out viewport yet, so every geometry value was a degenerate artifact, not a measurement. Acting on it would have been "fixing" a bug that did not exist.

**What we tried instead:** Forced the viewport with `resize_window` (1440x900, then 375 mobile) and re-measured: no horizontal scroll, copy capped at the 660px body measure, clean at both breakpoints. Lesson matches the day's theme — a true reading of a degenerate frame is still the wrong answer; check the frame is valid (`innerWidth > 0`) before trusting geometry.

**Status:** Resolved

**Tags:** browser-verification, viewport, degenerate-frame, false-positive, responsive, measurement-hygiene

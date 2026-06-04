# Dimension & Weight Integrity — Decisions Log

Permanent record of choices that should survive session turnover.
If a decision is reversed, strike it through and add the replacement
below — don't delete.

---

## Format

Each entry:
- **Date** — when decided
- **Decision** — one sentence, imperative voice
- **Why** — the reasoning, including what was tried and rejected
- **Scope** — what this applies to (file, chunk, deliverable, or "global")
- **Do not** — explicit anti-instructions, if any

---

## Architecture & Pipeline

[Pending brainstorm — stack and tooling decisions will land here]

---

## Data & Schema

### 2026-06-04 — This piece owns physical-attribute fields; Product Data Health Audit owns structural completeness
- **Why:** Prevents two models from writing the same dimension fields. Clear ownership boundary.
- **Scope:** Global — all models touching unit_*_weight, case_gross_weight, case_cube, length/width/height, ti, hi
- **Do not:** Let any other piece's models write these fields.

---

## Visualization

[Pending brainstorm]

---

## Output Formats

[Pending brainstorm]

---

## Writing & Voice

[Economist style per global CLAUDE.md]

---

## Reversed / Superseded

[None yet]

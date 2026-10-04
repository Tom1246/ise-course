# A2 — Domain Model and Testable Specification

- **Release** 2026-10-05 16:30 · **Deadline** 2026-10-12 16:30 (Asia/Shanghai) · **Platform** <https://learn.spaiq.ai>
- **Status:** artifacts complete; the platform record is submitted in the release window (opens 2026-10-05).
- **Tag:** `a2-v1`. A1's tag `a1-v2` is frozen and is not moved by A2 work.

Objective: turn the A1 workflow (course-plan conflict checking and the order to register in) into consistent
domain language, state, and independently checkable rules.

## Deliverables mapped to files

| A2 deliverable | File(s) here | State |
| --- | --- | --- |
| Domain glossary / context map | `domain-glossary.md`; `figs/context-map.dot` + `.png` | done |
| Process / event flow, state model | `figs/planning-flow.dot`, `figs/section-states.dot`, `figs/enrollment-states.dot` (+ `.png` each) | done |
| Data dictionary | `data-dictionary.md` (S1 / S2 / S5 field by field, 14 known traps) | done |
| Invariants and automated checks | `invariants.md`; `scripts/a2_check_invariants.py`; raw output `data/derived/a2/invariant-checks.md` | done — I1 reproduces the A1 case (3 conflicting pairs), I2/I3 limits stated |
| One material rule as decision table / contract / temporal property | `conflict-decision-table.md` (all three forms) | done |
| Data source / authority / quality / retention / deletion / privacy | `data-governance.md` (field-level authority, 8-step deletion procedure) | done |
| Model walkthrough record | `model-walkthrough.md`; `notebooks/a2-domain-model-walkthrough.ipynb` (executed, outputs stored) | done |
| Platform summary (150–300 words) | `A2-summary-en-2026-10-04.md` — count checked by `scripts/count_words.py` | done (251 words) |
| Reading copy of everything above | `A2-report-en-2026-10-04.md` + `.pdf` (56 pages, diagrams in the appendix) | done |

Regenerate everything from the repository root:

```bash
python3 scripts/a2_check_invariants.py          # the checks -> data/derived/a2/invariant-checks.md
bash doc/assignments/a2/figs/render.sh          # diagrams: .dot -> .png  (Graphviz)
python3 -m nbconvert --to notebook --execute --inplace notebooks/a2-domain-model-walkthrough.ipynb
python3 scripts/count_words.py                  # 150-300 word rule for every assignment summary
```

## The three invariants, and what the data did to them

1. **I1 — no two sections in one timetable overlap.** Holds only when *same weekday ∧ periods overlap ∧ weeks
   overlap*; week ranges are interval sets, so `[3,5]` vs `[6,8]` is fine while `[3,5]` vs `[4,8]` clashes.
   Reproduced against the committed catalogue: the three courses A1 names share 周四第 10-12 节 → 3 conflicting pairs.
2. **I2 — planned credits meet the programme's floors.** Floors only; the ceiling has no source and is *not*
   implemented rather than invented. The author's real plan is private, so a committed illustrative plan keeps the
   check runnable (13.5 credits vs a floor of 24 → the check reports "not satisfied", as it should for a sample).
3. **I3 — an enrolled count must be interpretable against a known capacity.** The first run reported 40
   violations; all 40 had `capacity = 0` with people enrolled. `0` (the official raw writes `"/"`) is a sentinel
   for *not set*, so the invariant was rewritten and the false finding disappeared. Real over-capacity in this
   snapshot: 0 — which is "cannot be determined", not "none exists".

## Rules carried over from A1

- numbers come from scripts, never hand-typed; frozen inputs keep their `.sha256` and capture time;
- failed runs, counterexamples and overturned intermediate claims stay in (see `data-dictionary.md` §6, where the
  dictionary contradicts a claim in A1's `data-authority.md`: the two sources agree on a *sample*, not on all 251
  shared course codes);
- no personal data, no other student's records, no credentials;
- diagrams ship as `.dot` source **plus** the render script — a PNG alone is not reproducible.

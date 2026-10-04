# A2 — Domain Model and Testable Specification

- **Release** 2026-10-05 16:30 · **Deadline** 2026-10-12 16:30 (Asia/Shanghai) · **Platform** <https://learn.spaiq.ai>
- **Status:** planning — artifacts land here as they are built.
- **Tag:** will be `a2-v1` on the final commit. A1's tag `a1-v2` is frozen.

Objective: turn the A1 workflow (course-plan conflict checking and the order to register in) into consistent
domain language, state, and independently checkable rules.

## Deliverables mapped to files

| A2 deliverable | File (in this folder) | State |
| --- | --- | --- |
| Domain glossary / context map | `domain-glossary.md`, `figs/context-map.dot` + `.png` | to build |
| Process / event flow, state model | `figs/planning-flow.dot`, `figs/section-states.dot`, `figs/enrollment-states.dot` (+ rendered PNG) | to build |
| Data dictionary | `data-dictionary.md` | to build |
| Invariants and automated checks | `invariants.md`, `scripts/a2_check_invariants.py`, raw output under `data/derived/a2/` | to build |
| Model walkthrough record | `model-walkthrough.md`, `notebooks/a2-domain-model-walkthrough.ipynb` | to build |
| Data source / authority / quality / retention / deletion / privacy | `data-governance.md` | to build |
| Platform summary (150-300 words) | `A2-summary-en-YYYY-MM-DD.md` | to build |

Supporting rules and the week plan live in the working folder (`A2/计划-A2-领域模型与可测试规格-*.md` locally);
the three invariants, the 8-row decision table and the known traps are drafted there.

## Rules carried over from A1

- Numbers come from scripts, never from hand-typing; frozen inputs keep their `.sha256` and capture time.
- Failed runs, counterexamples and overturned intermediate claims stay in.
- No personal data, no other students' records, no credentials.
- Diagrams ship as `.dot` source **plus** the render command — a PNG alone is not reproducible.

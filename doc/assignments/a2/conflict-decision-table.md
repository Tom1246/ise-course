# A2 — Material rule as a decision table, contract and temporal property

A2 asks for one material rule expressed as a decision table, a contract, an assertion, or a temporal property.
This repository does it three ways for the same rule, because the three forms disagree in the way they fail.

The rule: **I1 — two sections may not overlap in a timetable.**

---

## 1. Decision table (the primary form)

Inputs (all three are conditions on a pair of sections): same weekday?, period ranges overlap?, week ranges overlap?

| # | same weekday | periods overlap | weeks overlap | Verdict | Why |
| --- | --- | --- | --- | --- | --- |
| 1 | N | — | — | **no clash** | different days cannot clash |
| 2 | Y | N | — | **no clash** | same day, different periods |
| 3 | Y | Y | **N** | **no clash** | same slot in *disjoint week blocks* — the half-semester pattern |
| 4 | Y | Y | **Y** | **CLASH** | the only clashing row |

The two conditions marked `—` are *don't care*: their value cannot change the verdict. That is the whole point of
the table — a naive screen treats "same weekday ∧ periods overlap" as sufficient, which is row 3 stated wrongly
as a clash, and a whole-semester screen hides row 4 when the overlap is only partial.

**Executable form.** `scripts/a2_check_invariants.py` implements exactly this table:

```python
def conflict(a, b):
    return (a.weekday == b.weekday
            and overlap_periods(a, b)
            and overlap_weeks(a.weeks, b.weeks))
```

Its canonical cases (printed into `data/derived/a2/invariant-checks.md` §1, all four rows plus two registry
cases) — all six behave as the table says:

| case | verdict |
| --- | --- |
| same weekday + overlapping periods + overlapping weeks | clash |
| weeks disjoint `[3,5]` vs `[6,8]` | no clash (row 3) |
| weeks interleaving `[3,5]` vs `[4,8]` | **clash** (row 4) — the trap |
| same weeks, periods apart | no clash (row 2) |
| same weeks and periods, different weekday | no clash (row 1) |
| identical section (the same section compared with itself) | clash — matters because the calling code must never
compare a section with itself |

---

## 2. Contract form (design by contract)

```
operation  detectClash(a: Section, b: Section) -> Conflict | NoConflict

pre:      a ≠ b                                  # a section never clashes with itself
          a.weekday, a.periods, a.weeks are parsed   # an unparsable field is an error, not "no clash"
post:     result = Clash  ⟺  a.weekday = b.weekday
                              ∧ a.periods ∩ b.periods ≠ ∅
                              ∧ a.weeks ∩ b.weeks ≠ ∅
invariant (of the caller): collected plan P  ⟹  ∀ a,b ∈ P, a ≠ b : detectClash(a,b) = NoConflict
```

The two pre-conditions are the ones that actually bite:

- **`a ≠ b`** — a section compared with itself always "clashes", so a caller that forgets the guard reports the
  whole catalogue as broken. (The check counts self-clashes separately; the snapshot has 0 because the data
  contains no exact duplicate segments — but the guard is what makes that a *finding* rather than luck.)
- **fields must be parsed, not defaulted** — an empty or unparsable time field must raise, never be silently read
  as "no clash". A default of "no clash" turns missing data into a false all-clear, which is the single most
  dangerous failure mode for this whole project.

---

## 3. Temporal-property form

For the registration window, where the plan changes over time:

```
G( selected(a) ∧ selected(b) ∧ a ≠ b  →  ¬overlap(a, b) )
```

"At every moment, if two distinct sections are selected, they do not overlap." Two refinements that the model
makes explicit (see `domain-glossary.md` for the events):

- `F(SectionFull(s) ∧ selected(s))` — a section that was selected may become full later: the property holds on
  selection state, not on capacity state, so a delayed clash is possible in reality and is surfaced as a
  `SectionFull` event for the plan, not hidden;
- `F(PlanRevised) → G(¬overlap)` — after every plan revision the property must be re-established; that is why the
  product re-checks the whole plan after an edit instead of checking the edited pair only.

---

## 4. What this rule does **not** decide

- two sections in the same slot with **non-overlapping** week ranges are allowed, by design (row 3) — this is
  therefore not a "slot is taken" check but a "time is taken" check;
- a clash is *derived*, never stored: there is no `conflicts_with` field anywhere in the data, so a stale stored
  answer is impossible by construction;
- room, campus-travel and exam clashes are out of scope (see `invariants.md`, final section).

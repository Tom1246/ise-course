# A2 — Invariants and their automated checks

Three invariants, each stated in the domain's vocabulary (see `domain-glossary.md`), each backed by a check that
runs on the committed data. Raw output: `data/derived/a2/invariant-checks.md`. Re-run:

```bash
python3 scripts/a2_check_invariants.py        # writes the raw output, exits 0 whether or not it finds violations
```

A violation found by a check is a **finding about the data**, not a script error. Two of the three invariants
below are violated by the real data, and those violations are the interesting part.

---

## I1 — No timetable may contain two sections whose slots overlap

**Statement.** For any two sections `a`, `b` in the same plan:

```
conflict(a, b)  ⟺  weekday(a) = weekday(b)  ∧  periods(a) ∩ periods(b) ≠ ∅  ∧  weeks(a) ∩ weeks(b) ≠ ∅
```

All three conditions at once. Any two of them alone do not make a clash (the full truth table is in
`conflict-decision-table.md`).

**Why it is worded this way.** The naive screen — *same weekday and overlapping periods* — is wrong in both
directions: it **over-reports** (two courses in the same slot at disjoint week ranges are perfectly compatible,
which is the normal half-semester pattern in this data) and it **under-reports** nothing, because it is a
superset condition. A second naive screen — comparing whole-semester slots — **under-reports** the case of two
courses that only share part of a slot's week range.

**Check.** `scripts/a2_check_invariants.py` section 1–2:

| reading | result |
| --- | --- |
| decision-table cases (6 canonical cases incl. the week-interval trap) | all behave as specified |
| catalogue as a whole (347 scheduled courses, 146,427 segment comparisons) | **4,757 conflicting course pairs** = 7.9 % of course pairs = the *conflict density of the offer set* |
| an illustrative plan of 6 courses (`data/derived/a2/sample-plan.json`) | **1 internal conflicting pair** |
| the three courses named in A1 (计算机代数 / 数字图像处理与分析 / 深度学习) | all three at 周四 第 10-12 节 → **3 conflicting pairs** |

**The A1 case, reproduced.** A1 asserted that three courses in the author's plan all sit in one slot. That claim
is re-derivable from committed data alone:

| course | code | slot | weeks |
| --- | --- | --- | --- |
| 计算机代数在科学与工程中的应用 | `180081070100PX001Y` | 周四 第 10-12 节 | 2-18 |
| 数字图像处理与分析 | `180093081002P3008Y` | 周四 第 10-12 节 | 2-19 |
| 深度学习方法与应用 | `180206085406P3002Y` | 周四 第 10-12 节 | 2-4, 6-15 |

All three pairs conflict. The clash is a property of the **offer set**, which is why the planner needs the rule
rather than a printed plan.

**Limit.** The catalogue-level figure (4,757) is *not* a violation of I1: a timetable is a chosen subset, and a
student cannot take every course. Only the plan-level reading is an invariant check proper.

---

## I2 — Planned credits must satisfy the programme's floors

**Statement.** For the planned course set `P` and the programme's floors `f`: `Σ credits(P) ≥ f` for each floor
that the programme states.

**Check.** `scripts/a2_check_invariants.py` section 4: reads `data/s5-programme/degree-requirements.json`
(master track: total 36, course learning **24**, public degree 7, professional degree 12, practicum 12) and the
plan under test.

| reading | result |
| --- | --- |
| illustrative plan (6 courses) | 13.5 credits → **floor not satisfied** (the check works; the plan is deliberately a sample) |
| the author's real plan (private; only its aggregate is committed) | course-learning credits reached **26** (floor 24) — see `data/derived/credit-gap-summary.md` |

**Honest limits.** (a) The programme document states **floors only**, so the ceiling half of the invariant has no
source and is *left unimplemented rather than invented*. (b) The per-course plan is personal data and is not
committed, so the check ships with a committed illustrative plan so that it is runnable from the repository
alone; the real plan's aggregate is quoted from the committed summary. (c) The "planned course missing from the
catalogue" branch is a real case in 春季 and is not exercised by the illustrative plan.

---

## I3 — An enrolled count must be interpretable against a known capacity

**Statement (as first drafted).** `enrolled ≤ capacity` for every section.

**Statement (as the data forced it to be).** `enrolled` must be interpretable against a **known** capacity;
`capacity ∈ {empty, "0"}` means **unknown**, and unknown capacity must be surfaced to the planner — never
silently read as "unlimited" and never silently read as "full".

**Where the sentinel comes from.** In the official listing the unset value is written `"/"` (40 rows); the
committed derived snapshot renders that as `0`. Either way it means *not set* — but it is worth knowing which
layer produced the nicer-looking number (see `data-dictionary.md` §6 T2).

**Why the statement changed.** The first run reported 40 violations. Every single one of them had `capacity = 0`
with a non-zero enrolment — a row with 86 students against capacity `0` is not a section that admits nobody: it
is a row where the capacity field was never filled in. Reading it literally would have produced a headline
finding ("the school oversells 40 sections") that is simply wrong. After separating the sentinel:

| reading | result |
| --- | --- |
| sections with both figures present | 347 |
| capacity missing/empty | 0 |
| **rows with capacity `0` and enrolled > 0 (sentinel = not set)** | **40** |
| **violations with a real capacity (`enrolled > capacity > 0`)** | **0** |

**Check.** `scripts/a2_check_invariants.py` section 3 — it reports the two groups *separately*, so a sentinel row
can never be laundered into a violation count.

**Limit.** With capacity `0` meaning "not set", the honest conclusion about over-capacity in this snapshot is
*"cannot be determined from this field"*, not *"none exists"*. A1 observed over-capacity from an earlier crawl
(422/420 for 自然辩证法 sections); the two observations differ because they were taken at different times, which
is exactly why every frozen input in this repository carries a capture time and a hash.

---

## What the three invariants do **not** cover

- room clashes (same room, overlapping slots) — the data supports it, no invariant claimed;
- teaching loads, exam timetables, and travel time between campuses;
- fairness of the grab order (first-come-first-served is taken as given, not modelled);
- anything about the registration transaction itself, which is deliberately out of scope.

# Priority rules — two orders, not one

Working model for the "priority ranking" item of A1/A2/A4. It exists because the obvious reading of
"priority" (rank courses by how important they are) is *wrong as a grab order*, and the measured data
shows it.

Reproduce: `python3 scripts/rank_plan_priority.py`
Per-course output stays local at `data/private/plan-priority.md` (gitignored — it reveals which courses an
individual chose). Aggregates are committed at `data/derived/plan-priority-summary.md`.

## 1. Why two orders

Two questions get confused:

| Order | Question | What it decides |
| --- | --- | --- |
| **Deferability** | Can this course be taken later in the year? | what may be dropped when a clash is unavoidable |
| **Grab urgency** | Will the seat still be there when I get to it? | the order in which seats are taken inside the first-come-first-served window |

They are not the same order, and on the real plan they disagree:

* a course with **1 of 58 seats taken** (2% full) can sit in the "must take" group — no competition at all;
* a half-credit common course can be at **106 of 111 seats (95%)** before the window even opens.

So a single "importance" list is not enough. The tool has to emit **two outputs**: a conflict-free study
plan (what to take) and a **grab order** (what to take *first*). Anything that emits one list will be wrong
for one of the two questions.

A third, weaker order also matters:

| Order | Question | Measured as |
| --- | --- | --- |
| **Substitutability** | If this course clashes, is there another section I can move to? | number of sibling sections sharing the base course name |

Substitutability is the one dimension where a clash can be resolved by moving rather than by dropping.

## 2. What each dimension costs to measure

| Dimension | Source that carries it | Coverage on the 14 planned courses |
| --- | --- | --- |
| Deferability (semester) | the two official workbooks | **8 of 14** — the rest are in no official workbook at all |
| Grab urgency (capacity, enrolled) | the public listing | 13 of 14 |
| Substitutability (sibling sections) | the public listing | 14 of 14 |
| "Is the programme requiring it?" | **no source at all** | 0 of 14 — human input |

The last row is a design constraint, not a gap to paper over: no tool can derive the degree-programme
requirement from these sources, so the ranking must accept it as an explicit input
(`--must-take codes.txt`). By default the script derives a *candidate* must-take set from the course
attribute (学科核心课 / 专业核心课 / 公共必修课 / 专业课) and labels it as a candidate in every output.

## 3. Finding: the most urgent courses are also the least determined

Measured on the saved plan:

| Indicator | Value |
| --- | --- |
| planned courses | 14 |
| courses at >= 90% of capacity | **8 of 13** that have a capacity figure |
| courses whose semester is unknown from *every* source | **6 of 14** |
| of those 6, how many are at >= 95% of capacity | **5 of 6** |

Five of the six courses that no source can place in a semester are already at or above 95% of capacity.
The courses you would have to grab first are exactly the ones whose ability to be postponed cannot be
established. That is the sharpest measured statement of the problem in this brief, and it is invisible
to any check that only looks at weekday and period.

## 4. Tiers

Assigned by `scripts/rank_plan_priority.py`; the two inputs are the semester set from the official workbooks
and the remaining seats from the public listing.

| Tier | Meaning | Action |
| --- | --- | --- |
| **P0** | required by the programme, offered only this semester, and at or near capacity | first seat taken, in the first seconds of the window |
| **P1** | required, offered only this semester, but not contested | must be taken; order does not matter |
| **P2** | required, contested, but also offered next semester | take early if convenient, otherwise defer |
| **P3** | required, not contested, offered in both semesters | latest in the ordering |
| **PX** | not required by the programme (elective) | ordered by urgency only, first to be dropped under a clash |
| **PN** | **not offered this semester at all**, yet present in the plan | flag for review — a data or planning inconsistency, not a priority |
| **PU** | **deferability unknown**: absent from the official workbooks | cannot be ranked on deferability; must be resolved by hand or by another source |

Tier distribution on the current plan: `P0 3, P1 3, P3 1, PX 1, PU 6`.

Rule inside a tier: ascending remaining seats (a course with 0 seats left goes before one with 30).

## 5. Urgency distribution across the campus

From the public listing, the 347 Yuquanlu codes with a capacity figure (306 of 347 have one):

| Fill ratio | Courses |
| --- | --- |
| full (100%) | 43 |
| 90-99% | 39 |
| 70-90% | 39 |
| 30-70% | 54 |
| below 30% | 131 |

More than a quarter of the campus-offered courses with a capacity figure are at or above 90% full, which
is what makes the grab order a real problem rather than a theoretical one.

## 6. A snapshot is a snapshot

The plan's own copy of the capacity numbers and the public listing disagree, because they were captured
at different times: one course reads **376 / 420** in the planner backup and **415 / 420** in the listing
captured on 2026-09-27. Capacity is time-varying.

Consequence: every capacity figure must be frozen with a timestamp and a hash, exactly like the week and
period fields. An unfrozen fill ratio is not evidence.

## 7. Open questions to confirm

1. **The must-take set.** The tier assignment above uses a candidate set derived from course attributes.
   The real set comes from the degree programme and has to be supplied; until then every P0/P1/P2/P3 label
   is provisional.
2. **Tier ordering.** Is "deferability first, urgency inside a tier" the right lexicographic order? The
   alternative is "urgency first" — i.e. always grab the scarcest seat, even if the course could wait.
   The two give different orders whenever a full elective competes with a scarce required course.
3. **Thresholds.** >= 90% full, or <= 3 seats left. Both are arbitrary and should be calibrated against
   the observed distribution in section 5.

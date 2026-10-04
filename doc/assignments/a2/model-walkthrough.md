# A2 — Model walkthrough record

A walkthrough is done by taking the A1 scenarios and *running the A2 model against them*, in order, and writing
down every place where the model was wrong, ambiguous, or silent. The findings below are the record; several of
them changed the model, and those changes are noted in place.

- Model under test: `domain-glossary.md` (language), `figs/*.dot` (structure), `data-dictionary.md` (field
  reality), `invariants.md` + `conflict-decision-table.md` (rules).
- Data under test: the committed frozen inputs (`data/derived/course-library-snapshot.json`,
  `data/s1-plan-workbook/sections-snapshot.json`, `data/s5-programme/degree-requirements.json`) — no live system.
- Executed with: `python3 scripts/a2_check_invariants.py`, plus the SQL-free queries recorded inline.

---

## Scenario 1 — normal: plan one semester from the published documents

Walk: `CoursePlanPublished` → read the workbook (732 Yuquanlu records, 413 course codes) → `CatalogueSnapshotTaken`
from the listing (347 courses with slot and capacity) → parse slots → apply the decision table → emit a timetable
and a grab order.

Findings:

1. **The two upstream sources do not agree on what exists.** A1 measured this as 282 listing codes vs 234 workbook
   codes with 223 in common. The model must therefore treat "the catalogue" as *the union of the sources with an
   authority per field*, not as a single table — which is what `data-governance.md` §2 now specifies. **Model
   change:** the context map shows *two* upstreams, not one.
2. **"The course clashes" is almost never true.** A course normally has several sections (`-01`, `-08`,
   `-W003`), and the clash is a property of *sections*. An early draft of the glossary said "课程冲突"; it is
   wrong and is now listed among the words the model refuses to use loosely.
3. **The workbook cannot answer "when".** 0 of 732 records carry weekday/period or week ranges — the fields exist
   but are empty, and the empty `sessions` array is the evidence. A model that let the workbook be authoritative
   for slots would be silent exactly where the student needs an answer. **Model change:** field-level authority
   (`data-governance.md` §2) instead of source-level.

## Scenario 2 — boundary: half-semester courses, a full section, a stale snapshot

Walk: rows 3 and 4 of the decision table; `SectionFull`; `SnapshotStaled`.

Findings:

4. **Row 3 is not an edge case, it is the norm.** Slots are routinely split into week blocks (`第2-5,7-17周`).
   A screen that ignores weeks marks most of the catalogue as mutually exclusive. This is why the decision table,
   not a rule of thumb, is the specification.
5. **Two courses may even share *one* slot with different week blocks** — the data contains
   `周一(10-12)；周一(10-12)` with two different week ranges on the same weekday and periods. The model therefore
   stores a *set of slots* per section, and the UI must show the week block with every slot, not just the day.
6. **`capacity = 0` is a sentinel, not a capacity.** The first run of the I3 check reported "40 violations" — all
   of them rows with `capacity = 0` and real enrolments (up to 86). The model now states capacity as
   *integer or unknown*, and the check reports sentinel rows and real over-capacity rows separately. **Model
   change:** I3 was rewritten; see `invariants.md`.
7. **A stale snapshot is a first-class state, not an accident.** The listing is a snapshot taken 2026-09-27 and
   registration continues until 09-18 (…) — capacity keeps moving after the snapshot. `SnapshotStaled` is a domain
   event, and the plan it produces is a *hypothesis*. A1 observed the same section at 422/420 in one capture and
   differently later, which is why every frozen input carries a capture time and a hash.

## Scenario 3 — failure: the real plan that had to be rearranged

Walk: `SectionFull` → `SectionSwitched` → `PlanRevised` (the A1 record: 自然辩证法 moved from 周二第 1 节 +
周日第 1 节 to 周三第 5 节 + 周六第 5 节; 中特 from 周二第 1 节 to 周三第 1 节).

Findings:

8. **A switch is a multi-section event.** Moving one course changed three others; the model must re-run the whole
   plan check after every edit, which the temporal property in `conflict-decision-table.md` §3 states.
9. **The clash the plan actually contained is reproducible from committed data**: 计算机代数 / 数字图像处理与
   分析 / 深度学习 all at 周四第 10-12 节 → 3 conflicting pairs. The walkthrough closes the loop between the A1
   narrative and the A2 model: the narrative's claim is now a check, not a story.

## Scenario 4 — misuse: "just register for me"

Walk: the boundary where the model refuses. See A1's abuse scenario: an automatic seat-grabbing bot breaks
first-come-first-served and the school notice explicitly forbids disrupting or hoarding registrations.

Findings:

10. **The model has no actuator and must not grow one.** The deliverables are a timetable and an *order*; the
    registration context appears on the context map as a dashed, out-of-scope box precisely so that "add the
    posting step" is a visible scope change, not an implementation detail.
11. **The privacy boundary is part of the model, not a policy afterthought.** `Enrollment` is the identifying
    entity, so per-course and per-student detail lives outside the repository (`data/private/`, gitignored) while
    only aggregates are committed; the deletion procedure is written down in `data-governance.md` §5 so it can be
    executed rather than promised.

---

## What the walkthrough did **not** settle

- **The grab order is under-specified by this model.** "Which section first" depends on capacity pressure that is
  itself stale; A2 stores the inputs (capacity, enrolled, timing) but does not yet define the ordering rule. That
  is deliberate: it belongs to A3/A4, and pretending to specify it now would be a specification that cannot be
  tested.
- **`SectionOverCapacity` has no decision attached.** The model flags it; whether the planner should avoid such a
  section is a product decision this walkthrough did not make.
- **Spring-term data is thin** — 2027 spring is unpublished, so the model's "semester" value is exactly the case
  the data dictionary labels *unknown*, not a value to be guessed.

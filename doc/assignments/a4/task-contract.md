# A4 task contract — "which course do I register for first?"

> **Revision after peer review (2026-10-05, commit `731bc66`).** The rule table in §2 changed: measured cases
> now rank before unmeasurable ones, and a places figure is published **only with a dated enrolment figure** —
> the shipped data carries no capture time, so the real-data path prints no number at all. See `review/response.md`.

- **Slice id:** `a4-slice-v1` (branch `a4-slice` on a local clone of the upstream repository, commit `7e17a21`)
- **Written:** 2026-10-05 · **Submission window:** A4 opens 2026-11-02, closes 2026-11-09 16:30 (Asia/Shanghai)
- **Subject repository:** `HMBlankcat/UCAS-course-planner` @ `68e7080503084a41f42db6e0e9ff94c0e9ef2f19` (`ver 1.4`, MIT) — the
  repository investigated in A3 (`doc/assignments/a3/`)
- **Change boundary:** ADR-001 in A3 (`doc/assignments/a3/adr-001-change-boundary.md`) decided option **B** — extract a
  pure, independently testable function layer and leave UI/state/persistence alone. This slice is the first change
  made under that decision.

## 1. The requirement this slice comes from (traceability)

| Where it comes from | What it says | How it constrains this slice |
| --- | --- | --- |
| A1 brief, pain point 1 (`doc/assignments/a1/A1-brief-en-2026-09-28.md:87`) | "**I had not fixed the order to register in in advance**, and by the time I came to register for the important courses the section I wanted was already full." | The slice must answer *what to register for first*, not merely *what clashes*. |
| A1 brief, pain point 3 (`:111`) | Required courses run in the autumn only and registration pressure is heavy (sections full, one at 42/170). | Capacity pressure and "must take this term" are the inputs that matter; a closing order alone is not enough. |
| A1 brief, comparison of the existing tool (`:123`) | The tool has clash hints and filtering but "**there is no order to register in**". | The gap being filled is explicitly identified as absent, so the slice is not duplicating an existing feature. |
| A2 model (`doc/assignments/a2/conflict-decision-table.md`) | A clash = same weekday ∧ overlapping periods ∧ overlapping weeks; a plan containing a clash must be resolved before it can be judged. | The slice must **refuse to order a self-clashing plan** and say why, rather than advise about an impossible plan. |
| A3 finding (`doc/assignments/a3/architecture-map.md` §6, risk register R3) | `capacity`/`selected` exist in the data but the application never reads them; `capacity === 0` is a "not recorded" sentinel (99 of 2,077 rows). | The slice must map the sentinel to *unknown* — never to "full" — and surface missing data instead of guessing. |

## 2. What the slice delivers

A panel in the plan view that, for the courses already added, prints **one ordered list**: what to register for
first, each line carrying a label, a reason, and — where the data supports it — the number of places left.

Ordering rule (fixed, explainable, deterministic):

| Priority | Criterion | Why this order |
| --- | --- | --- |
| 1 | urgency: `critical` → `unknown` → `high` → `normal` | losing a full section is the failure A1 records; **not knowing** is placed above *known-safe*, because ignorance is closer to risk than to reassurance |
| 2 | degree course before elective (at equal urgency) | a missed degree course costs a year |
| 3 | autumn-only before spring-capable (at equal urgency) | it cannot be deferred to the spring |
| 4 | fewer places left first (only when known) | the same failure mode as (1), one level finer |
| 5 | course code | makes the output deterministic and testable |

Three honesty rules, each with a test:

1. **No capacity data ⇒ `unknown`, never `normal`.** (`tests/priority.test.ts`: "missing capacity is reported as unknown, never as safe")
2. **`capacity === 0` ⇒ `unknown`, never `critical`.** (`: "capacity 0 is a sentinel, not a full section"`)
3. **Self-clashing plan ⇒ no order for the clashing courses, plus a stated reason.** (`: "a plan that clashes internally is not given an order for the clashing courses"`, and end-to-end case C)

## 3. Scope

**In scope**
- the pure ranking layer (`lib/priority.ts`) and the data mapping (`lib/priority-mapping.ts`), both covered by tests;
- one panel in `app/page.tsx` that calls them (58 added lines; nothing else touched);
- local verification: unit, type check, lint, build and a browser end-to-end run against the built app.

**Out of scope (deliberate, with the reason)**
| Not done | Why |
| --- | --- |
| **Server / API / authorization (401, 403)** | Deferred by decision (2026-10-05) — the priority is local verification first. The upstream app is local-first with no server at all (A3 architecture map §3–4), so this is new construction, not a change to existing behaviour. `slice-notes.md` records what remains for that step. |
| Any change to the data pipeline or to add a semester field (A1 gap ①) | A separate requirement, larger than one slice. The panel states this limitation in the UI instead of hiding it. |
| Cross-semester credit totals (A1 gap ④) | Out of this slice's value: it does not change the ordering decision. |
| Changing the `localStorage` contract | A3 risk R4: a storage-version mismatch silently resets the user's plan. A slice that may have to be rolled back must not be able to wipe user data. |

## 4. Interface

```ts
// lib/priority.ts
rankPlan(courses: PlanCourse[]): RankResult      // pure; no I/O, no React, no storage
urgencyOf(course: PlanCourse): Urgency           // pure
placesLeft(capacity?: Capacity): number | null   // null = "not knowable", never 0
// lib/priority-mapping.ts
capacityFromRow(row: RawCourseRow): Capacity     // capacity === 0  ->  { kind: 'unknown' }
planCoursesFromRows(rows: RawCourseRow[]): PlanCourse[]
```

`RankResult = { order, unknownCodes, caveats }` — `caveats` is not decoration: it is where the slice reports what
it could **not** take into account (missing capacity, an unresolvable clash, an empty plan).

## 5. Acceptance criteria

| # | Criterion | Checked by |
| --- | --- | --- |
| 1 | A plan with a full section ranks that course first | `tests/priority.test.ts`; end-to-end case B |
| 2 | A course with no capacity data is labelled *unknown* and never placed below a known-safe course | unit test; end-to-end cases A and B |
| 3 | A self-clashing plan produces no order plus a stated reason | unit test; end-to-end case C |
| 4 | Same input ⇒ same order (determinism) | unit test (two runs compared) |
| 5 | Nothing is dropped: the order is a permutation of the ranked courses | unit test |
| 6 | The application still builds, lints and type-checks with the slice in place | `evidence/logs/03-build.log` (exit 0), `06-lint.log` (0/0), `07-typecheck.log` (exit 0) |
| 7 | The upstream test-free gap is not made worse: the slice ships tests where none existed | `evidence/logs/02-unit-tests.log` (20 pass) |
| 8 | A rollback cannot wipe a user's plan | `rollback.md`; `localStorage` untouched in the diff |

## 6. Known weaknesses (stated, not hidden)

- **The real snapshot cannot exercise `critical`/`high`.** In `public/data/courses.json` no 玉泉路 course is full and none has
  ≤10 places left (`selected` is 0 for essentially every row), so end-to-end case B uses **synthetic capacity values
  on real course objects**, labelled as such in `evidence/logs/05-e2e-priority.log`. The logic is exercised; the
  *data path from a live registration system* is not.
- **Capacity itself may be stale.** The numbers come from a snapshot shipped with the repository (A3 R3). The slice
  reports places left without a capture time, exactly the failure A1 warns about (`A1-brief-…:181`). Carrying a capture
  time is deliberately left out of this slice and listed as follow-on work.
- **The panel's placement is provisional.** It sits in the plan column so it is visible while choosing; no usability
  study beyond the three representative tasks in `usability.md`.

## 7. Evidence index

`evidence/logs/01-npm-ci.log` · `02-unit-tests.log` · `03-build.log` · `04-start.log` · `05-e2e-priority.log`
(+ `05a-e2e-first-attempt.log`, the first run whose fixture was wrong — kept) · `06-lint.log` · `07-typecheck.log`
· `08-hermes-verify-trap.log` · screenshots `priority-real.png`, `priority-synthetic.png`, `priority-clashing.png`

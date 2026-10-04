# A2 — Domain glossary and context map

The ubiquitous language for the course-planning domain. Terms are given Chinese-first (the data and the
rules are Chinese) with the English term that code and documents use. Where a term has a trap, the trap is
stated — half of this domain's bugs come from words, not from algorithms.

## 1. Bounded context

**Semester course planning** — from *the university says what will run* to *the student has a timetable and an
order to register in*. Everything in this repository lives inside this boundary.

- **Upstream, outside:** the university's course-offering system (publishing the plan and the listing) and the
  programme requirements document. We consume them; we cannot change them.
- **Downstream, outside this context:** the registration transaction itself. Registration is *not* automated here —
  out of scope by policy (see `data-governance.md` and A1's misuse scenario).
- **The unit of work** is one student, one semester, one plan. Not a cohort, not a department.

## 2. Entities — identity that persists across time

| Chinese | English | Identity | What it is | Traps found in the real data |
| --- | --- | --- | --- | --- |
| 课程 | Course | 课程编码 (18 characters) | a course as a catalogue entry | the code is not opaque: position 13 = 培养层次, 14 = 课程属性, **18 = 校区 (`Y` = 玉泉路)** |
| 班次 | Section | 课程编码 + suffix (`-01`, `-08`, `-W003`) | one teaching instance with its own slot, room, capacity | one course normally has several sections with *different* slots — "the course clashes" is almost always false; *sections* clash |
| 学期 | Term | e.g. 2026-2027 秋季 | the teaching period a section belongs to | the workbook **does** carry it, per row (秋季 400 / 春季 332 in the committed import) — A1 used exactly that column to show the three required courses are autumn-only; the public listing has no per-row term (the term is implied by the crawl) |
| 培养方案 | ProgrammeRequirement | 校发培养字〔2025〕92号 + programme code | the credit floors and degree-course rules a plan must satisfy | states floors only; no ceiling (see `invariants.md`, I2) |
| 选课方案 | Plan | the student's own | the chosen sections for one term, plus an order to register in | **personal data** — kept out of this repository (aggregates only) |
| 选课记录 | Enrollment | student × section | the state of one student's registration for one section | the privacy-sensitive entity: enrolment lists identify people |

## 3. Value objects — no identity, equal by value

| Chinese | English | Value | Notes |
| --- | --- | --- | --- |
| 周次区间 | `WeekRange` | `(start, end)`, e.g. `(2, 5)` | the field is an **interval set**, not a number: `第2-5,7-17周` is `[(2,5),(7,17)]` |
| 节次区间 | `PeriodRange` | `(first, last)`, e.g. `(10, 12)` | 节 are 1..12 within a day |
| 星期节次 | `DayPeriod` | `(weekday, PeriodRange)` | the listing packs several into one cell: `周三(5-7)；周六(5-7)` |
| 时段 | `Slot` | `DayPeriod` + `WeekRange` set | the unit the conflict rule compares |
| 学分 | `Credit` | number | used by I2 |
| 容量 / 已选 | `Capacity` / `Enrolled` | non-negative integer or *unknown* | **`0` is a sentinel for "not set"** — 40 rows in the snapshot have `0` capacity with people enrolled |
| 教室 | `Room` | string | informational; not part of any invariant |
| 课程属性 | `CourseAttribute` | 学位课 / 选修 / 必修 | the degree-course floors are expressed in this vocabulary |
| 校区 | `Campus` | `Y` = 玉泉路, `H` = 雁栖湖, `Z` = 中关村 | centralised-teaching students may not cross campuses (school notice, quoted in A1) |
| 冲突 | `Conflict` | boolean derived from two `Slot`s | **derived, never stored** — see the decision table |

## 4. Domain events — what happens, in the order it happens

| Event | Trigger | Meaning for the model |
| --- | --- | --- |
| `CoursePlanPublished` | the university issues the workbook (2026-08-28) | sections get a *planned* existence; no weekday/weeks yet |
| `CatalogueSnapshotTaken` | we crawl the listing (2026-09-27) | a **frozen** view; every later question is answered against it |
| `RegistrationWindowOpens` | 09-02 public electives, 09-03 professional, **09-04 12:30 for first-year master's**, 09-18 12:30 close | the order to register in becomes the scarce resource |
| `SectionFull` | `enrolled = capacity` | the section is effectively unavailable; the plan must change |
| `SectionOverCapacity` | `enrolled > capacity > 0` | a state the system allows; must be surfaced, never read as "a seat exists" |
| `SectionSelected` / `SectionDropped` / `SectionSwitched` | student action | **the real case in A1**: switching a full section re-arranged the whole timetable |
| `PlanRevised` | student action | A1's two saved versions are two instances of this event (22 removed / 45 added cells) |
| `SnapshotStaled` | time passes | the catalogue no longer matches the live system: the plan is a hypothesis, not a fact |

## 5. Context map

See `figs/context-map.dot` (source) and `figs/context-map.png` (rendered; regenerate with
`bash doc/assignments/a2/figs/render.sh`). Reading it: two upstream contexts (offering, requirements) feed the
planning context; the planning context emits a timetable plus a registration order; the registration context is
downstream and deliberately outside the automated boundary.

## 6. Words we refuse to use loosely

- **"课" alone** — always say 课程 (course) or 班次 (section). A1's own first draft confused the two, and the
  confusion is what makes "the course is full" sound true when only one section is.
- **"优先" / priority** — two different orders exist and they are *not* the same: the **plan order**
  (which course matters more when something must be dropped) and the **grab order** (which section to register
  first under first-come-first-served). Documents say which one is meant.
- **"抢课"** — the act of competing for seats. This project outputs an *order*, never an actuator.
- **"周次"** — never a single number; always an interval set. `第6周` is the degenerate set `[(6,6)]`.
- **"满" (full)** — a *state of a section*, not a violation of an invariant (see `invariants.md`, I3).

# A2 invariant checks — raw output

- Generated: 2026-10-04 20:58
- Reproduce with: `python3 scripts/a2_check_invariants.py`
- Inputs: `data/derived/course-library-snapshot.json` (347 courses), `data/s5-programme/degree-requirements.json`, `data/derived/a2/sample-plan.json`
- Violations below are **findings**, not script errors. Exit code 0 means the checks ran.

## 0. Parsing quality (what the data actually looks like)

| property | value |
| --- | --- |
| courses | 347 |
| courses with at least one scheduled session | 347 |
| courses with no session data at all (empty time **and** empty weeks) | 0 |
| unparsable time segments | 0 |
| unparsable week segments | 0 |
| time/weeks segment-count mismatches | 0 |
| courses whose session list contains an exact duplicate segment | 0 |
| courses with a slot repeated in two different week blocks (half-semester pattern) | 4 |

> Every course in this snapshot carries both a time and a week-range string, and the number of `；`-separated segments always matches between the two fields — so the parallel-list reading used below is safe **for this snapshot**. It is a property of the data, not a guarantee of the format: the check counts mismatches and would report them here rather than guess.

## 1. The conflict rule, checked as a decision table

| case | section A | section B | expected | actual | ok |
| --- | --- | --- | --- | --- | --- |
| same weekday + periods overlap + weeks overlap | 周3 (6-7) 第[(1, 16)]周 | 周3 (7-8) 第[(2, 4)]周 | True | True | yes |
| week ranges disjoint [3,5] vs [6,8] | 周3 (6-7) 第[(3, 5)]周 | 周3 (6-7) 第[(6, 8)]周 | False | False | yes |
| week ranges touching/interleaving [3,5] vs [4,8] | 周3 (6-7) 第[(3, 5)]周 | 周3 (6-7) 第[(4, 8)]周 | True | True | yes |
| same weeks, periods apart | 周3 (1-2) 第[(1, 16)]周 | 周3 (5-7) 第[(1, 16)]周 | False | False | yes |
| same weeks and periods, different weekday | 周2 (6-7) 第[(1, 16)]周 | 周3 (6-7) 第[(1, 16)]周 | False | False | yes |
| identical section (data duplicated) | 周3 (6-7) 第[(1, 16)]周 | 周3 (6-7) 第[(1, 16)]周 | True | True | yes |

- all decision-table cases behave as specified: **True**

## 2. I1 — no two sections of one timetable overlap

- scheduled courses compared: 347 (all unordered pairs of their session segments)
- segment comparisons performed: 146427
- **conflicting course pairs found: 4757** (7.9% of all course pairs)
- courses that clash with their own duplicated segment: 0

### Examples (the first 8 conflicting pairs, verbatim from the data)

| course A | its slot | course B | its slot |
| --- | --- | --- | --- |
| `180080070100MX018Y` | 周3 第5-7 节 / weeks [(2, 5), (7, 17)] | `180081070206P3006Y` | 周3 第5-7 节 / weeks [(2, 5), (7, 20)] |
| `180080070100MX018Y` | 周3 第5-7 节 / weeks [(2, 5), (7, 17)] | `180086081201P3003Y` | 周3 第5-7 节 / weeks [(3, 5), (7, 15)] |
| `180080070100MX018Y` | 周3 第5-7 节 / weeks [(2, 5), (7, 17)] | `180086081202P3001Y` | 周3 第5-6 节 / weeks [(2, 5), (7, 13)] |
| `180080070100MX018Y` | 周3 第5-7 节 / weeks [(2, 5), (7, 17)] | `180086085404P2003Y-1` | 周3 第5-7 节 / weeks [(2, 5), (7, 20)] |
| `180080070100MX018Y` | 周3 第5-7 节 / weeks [(2, 5), (7, 17)] | `180087120500PX011Y` | 周3 第5-7 节 / weeks [(2, 5), (7, 11)] |
| `180080070100MX018Y` | 周3 第5-7 节 / weeks [(2, 5), (7, 17)] | `180088071200MX014Y` | 周3 第5-7 节 / weeks [(2, 5), (7, 16)] |
| `180080070100MX018Y` | 周3 第5-7 节 / weeks [(2, 5), (7, 17)] | `180089050200MB001Y-W003` | 周3 第5-6 节 / weeks [(2, 5), (7, 17)] |
| `180080070100MX018Y` | 周3 第5-7 节 / weeks [(2, 5), (7, 17)] | `180089050200MX016Y` | 周3 第5-6 节 / weeks [(2, 5), (7, 16)] |

### Where the clashes concentrate

| slot | conflicting pairs naming this slot |
| --- | --- |
| 周3 第5-7 节 | 470 |
| 周2 第5-7 节 | 386 |
| 周2 第3-4 节 | 336 |
| 周1 第5-7 节 | 256 |
| 周1 第10-12 节 | 214 |
| 周2 第1-4 节 | 196 |

### 2.1 Catalogue-level reading: conflicts of *offer*, not yet a violation

A timetable is a chosen subset, so two overlapping courses in the catalogue are two offers that cannot be combined — not a broken invariant. The figure above is therefore the **conflict density of the offer set**. The invariant itself is exercised next on an actual plan (2.2) and on the A1 case (2.3).

### 2.2 Plan-level check — the invariant on a chosen timetable

- plan used: `data/derived/a2/sample-plan.json` (6 courses, illustrative)
- **internal conflicting pairs in that plan: 1**
  - `180081070200P1001Y` (周2 第7-8 节, weeks [(2, 5), (7, 20)]) vs `180081070206P3005Y` (周2 第5-7 节, weeks [(2, 5), (7, 20)])

### 2.3 The A1 case, reproduced from committed data

A1 claims three courses in the author's plan all sit at Thursday periods 10-12. The catalogue is committed, so that claim can be re-checked here:

| course | code | slot in the catalogue | week ranges |
| --- | --- | --- | --- |
| 计算机代数在科学与工程中的应用 | `180081070100PX001Y` | 周4 第10-12 节 | [(2, 18)] |
| 数字图像处理与分析 | `180093081002P3008Y` | 周4 第10-12 节 | [(2, 19)] |
| 深度学习方法与应用 | `180206085406P3002Y` | 周4 第10-12 节 | [(2, 4), (6, 15)] |

- conflicting pairs among the three: **3 [('计算机代数在科学与工程中的应用', '数字图像处理与分析'), ('计算机代数在科学与工程中的应用', '深度学习方法与应用'), ('数字图像处理与分析', '深度学习方法与应用')]**
- reading: the A1 case is reproducible from the committed catalogue — the clash is a property of the offer set, which is why the planner needs the rule rather than a printout.

## 3. I3 — enrolled must not exceed capacity (empty = unknown)

- sections with both figures present: 347
- sections with a missing figure (capacity unknown, **never treated as unlimited**): 0
- **rows whose capacity is literally `0` while enrolled > 0: 40**
- **violations with a real capacity (enrolled > capacity > 0): 0**

Finding (this is the interesting one): every over-capacity row in this snapshot has capacity `0`. Read literally that would be 40 violations; read as data it means **`0` is a sentinel for "not set"**, not a section that admits nobody — one of those rows shows 86 enrolled against it. The invariant is therefore stated as: *an enrolled count must be interpretable against a known capacity; a capacity of `0`/empty is unknown, and unknown capacity must be surfaced to the planner, never silently treated as either full or unlimited.*

| course code | course | enrolled | capacity |
| --- | --- | --- | --- |
| `180090125601M2004Y` | 财务与成本管理 | 86 | 0 (not set) |
| `180090125600M1003Y` | 工程经济学 | 72 | 0 (not set) |
| `180090125600M1004Y` | 高级管理学 | 72 | 0 (not set) |
| `180090125600M1006Y-01` | 工程管理导论-1班 | 72 | 0 (not set) |
| `180090125601M4001Y` | 工程哲学 | 64 | 0 (not set) |
| `180089050200MB001Y-304` | 英语A-304班（工程科学学院） | 42 | 0 (not set) |
| `18087B125100M1003Y` | 组织行为学(MBA脱产) | 35 | 0 (not set) |
| `18087B125100M1007Y` | 战略管理(MBA脱产) | 35 | 0 (not set) |

## 4. I2 — planned credits vs the programme floors

| planned course | credits | found in catalogue |
| --- | --- | --- |
| `180080070100MX018Y` 实用最优化算法 | 1 | yes |
| `180081070100PX001Y` 计算机代数在科学与工程中的应用 | 1 | yes |
| `180081070200P1001Y` 高等量子力学 | 3 | yes |
| `180081070202P3007Y` 物理中的概率和统计 | 3 | yes |
| `180081070206P2002Y` 理论声学I | 3 | yes |
| `180081070206P3005Y` 海洋声学 | 2.5 | yes |

- planned credits in this illustrative plan: **13.5**
- programme floors (master track): total 36, course learning 24, public degree 7, professional degree 12, practicum 12
- verdict for the illustrative plan: **NOT satisfied** (course-learning floor 24)
- courses in the plan that the catalogue does not contain: 0 

Two honest limits of this check: the programme document states **floors only**, so the ceiling half of the invariant has no source to test against and is left unimplemented rather than invented; and the "planned course is missing from the catalogue" branch (a real case in 春季) is not exercised by this illustrative plan.

> The author's real plan is private. Its committed aggregate lives in `data/derived/credit-gap-summary.md` (present in this checkout); the per-course detail stays in `data/private/`.

- real plan (aggregate): course-learning credits reached: 26 (requirement >= 24)
- real plan (aggregate): credits evidenced as open in 秋季: 25 (per-semester floor >= 10)


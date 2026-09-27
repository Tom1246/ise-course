# ISE-A1 — Evidence Brief: course-plan conflicts and seat-grab priority

Submission for **ISE-A1 (Problem and Stakeholder Evidence Brief)**, course *Intelligent Software Engineering*,
platform <https://learn.spaiq.ai>. Deadline **2026-09-28 16:30 (Asia/Shanghai)**.

**Claim of this brief.** Producing one input that supports both a timetable-conflict check and a seat-grab
ranking is impossible from any single source. Three sources must be joined by course code, they overlap only
partially, and after joining, 6 of the 14 courses in the current plan still have no semester recorded anywhere —
while 8 of the 13 courses that do have a capacity figure sit at or above 90% full.

## Repository layout

```
.
├── README.md                            this file
├── docs/
│   ├── A1-brief.md / .pdf               the brief (main deliverable)
│   ├── priority-rules.md                the two-order priority model (plan vs grab order)
│   ├── selection-design.md              the four-step selection design, formalised
│   ├── selection-design.pdf
│   ├── system-and-pain-points.zh.md     working doc (Chinese): system, workflow, 9 pain points
│   ├── system-and-pain-points.zh.pdf
│   └── prototype-issues.md              problems met while building the prototype (part auto-generated)
│   ├── evidence-ledger.md               every claim traced to a source, method and date
│   └── submission-summary.md            the 150-300 word summary posted on the platform
├── data/
│   └── degree-requirements.json         credit rules extracted from the 0854 programme document
├── src/
│   ├── freeze_snapshot.py               official workbooks -> frozen Yuquanlu snapshot + provenance
│   ├── credit_gap.py                    requirements -> classification -> gap -> filler candidates
│   ├── fetch_official_db.py             crawl the OFFICIAL course database (jwba.ucas.ac.cn)
│   ├── build_web_prototype.py           joins + parses + emits the single-file prototype page
│   ├── fetch_public_listing.py          public listing -> frozen Yuquanlu subset + join report
│   ├── inspect_plan_versions.py         measure the saved plan versions, diff them, week occupancy
│   ├── rank_plan_priority.py            deferability x grab urgency -> tiered grab order
│   └── count_words.py                   verify the submission summary is 150-300 words
├── raw/
│   ├── official/<term>-campus20.json    OFFICIAL database crawl, 玉泉路 (autumn + spring terms)
│   ├── sections-snapshot.json(.sha256)  official workbooks, 玉泉路 subset
│   ├── yuquanlu-live-courses.json(.sha256)  public listing, 玉泉路 subset
│   └── measurements/                    all committed script output (see below)
├── prototype/
│   ├── 启动选课参考系统.command          double-click launcher
│   └── 选课参考系统.html                 generated page -- GITIGNORED (embeds the personal plan)
└── ai/
    └── ai-use-log.md                    AI tools used, accepted/rejected advice, verification
```

`raw/private/` holds the per-course ranked table and is **gitignored**: it reveals which courses an individual
chose. Only aggregates are committed.

## Reproduce

```bash
python3 src/freeze_snapshot.py                              # official workbooks  -> raw/sections-snapshot.json
python3 src/fetch_public_listing.py                         # public listing      -> raw/yuquanlu-live-courses.json
python3 src/inspect_plan_versions.py                        # plan versions       -> raw/measurements/plan-versions.md
python3 src/rank_plan_priority.py                           # grab order          -> raw/measurements/plan-priority-summary.md
python3 src/credit_gap.py                                   # credit gap          -> raw/measurements/credit-gap-summary.md
python3 src/fetch_official_db.py --terms 89576,89577 --campus 20   # official DB crawl -> raw/official/
python3 src/build_web_prototype.py                          # prototype page      -> prototype/选课参考系统.html
python3 src/count_words.py                                  # submission summary word count
```

Environment: Python 3.11 with `openpyxl` 3.1.2. `fetch_public_listing.py` is the only script needing network
access; pass `--input <cached.json>` to run offline. `inspect_plan_versions.py` and `rank_plan_priority.py`
need the two personal plan files, whose paths are set at the top of each script and can be overridden.

## Authoritative source: the official course database

`https://jwba.ucas.ac.cn/sc/public/coursePublic` is the academic-affairs public listing: one server-rendered
table per (term, campus), no pagination, columns 开课院系/课程编号/课程名称/课时/学分/课程属性/**限选人数**/
**已选人数**/首席教授/主讲教师/**开课校区**, and every row links to `/sc/course/coursetime/<id>` which carries
**上课时间（星期＋节次）+ 上课地点 + 上课周次**. So the official system supplies campus, capacity *and* the
three-dimensional schedule — no login, no captcha, public by design.

Measured 2026-09-27: autumn (termId 89576, campusCode 20) = **341 Yuquanlu courses, 339 with a parsed
schedule**; spring (89577) = **0 rows — that term's listing is not published yet**. Cross-checked against the
third-party listing: the weekday/period/week fields agree exactly.

That said, switching to the official source **did not remove the join gap, it changed its shape**: only
**212** of the 341 official codes appear in the official workbooks, 129 appear only in the database (so their
学期 is unknown) and 202 appear only in the workbooks (so they have no schedule or capacity).

## The three sources and why joining them is the problem

| Source | What it is | Yuquanlu coverage | Carries | Does not carry |
| --- | --- | --- | --- | --- |
| A | official workbook `开课计划表0828.xlsx` | 441 records | campus, semester, attribute, credits | week range, weekday/period, capacity |
| B | official workbook `核心课和专业课列表0828.xlsx` | 291 records | same as A | same as A |
| C | public listing `default-courses.json` | 347 codes | week range, weekday/period, capacity, enrolled | **no campus field at all**; no semester |

A+B hold 732 Yuquanlu *records* covering 414 distinct courses. C carries the fields A+B lack, but identifies
campus only through the course-code rule (position 18 = `Y`). Joining A+B with C by course code:

| | Value |
| --- | --- |
| codes in both A+B and C (all fields obtainable) | **217** |
| codes only in A+B (no week, no period, no seats) | **197** |
| codes only in C (no campus, no semester) | **130** |

## Key measured findings

| Finding | Value |
| --- | --- |
| Official import: records / Yuquanlu records / distinct Yuquanlu courses | 4,877 / 732 / 414 |
| Yuquanlu records carrying 开课周 / 星期节次 | **0 / 0** |
| Import defects reported for the two official workbooks | 4 (the same two fields) |
| Yuquanlu courses offered only in autumn / only in spring / in both | 208 / 179 / 27 |
| Saved plan versions | 2 (2026-09-05, 2026-09-15) |
| Cell positions removed / added / edited in place between them | 22 / 45 / 0 |
| Slots occupied by two courses in disjoint week ranges (2026-09-05) | 1 (cell `C5`) |
| Plan courses at >= 90% of capacity | **8 of 13** |
| Plan courses with no semester in any source | **6 of 14** (5 of those 6 are >= 95% full) |
| Campus courses at >= 90% full (of 306 with a capacity figure) | 82 |

The last four rows are the crux: the courses that must be grabbed first are the ones whose ability to be
postponed cannot be established from any source.

## Credit accounting (steps 1-4 of the selection design)

`data/degree-requirements.json` holds the credit structure taken verbatim from the 0854 programme document
(校发培养字〔2025〕92号): master's total >= 36 = course learning >= 24 + required practicum 12; public degree
courses 7; professional degree courses >= 12 (core >= 4 credits and >= 2 courses, major >= 4 credits and >= 2
courses); public elective >= 2; professional elective >= 2; >= 10 credits per semester.

`src/credit_gap.py` classifies the plan against those categories and reports the gap plus filler candidates.
Measured on the current plan: course learning 26 of 24 required; two categories short; 25 credits evidenced as
open in autumn against a floor of 10. The public-degree shortage is exactly the 3 credits of master's English,
which is satisfied by an exemption and therefore **appears in no course data at all** — a tool that only reads
the course tables would wrongly advise taking another English course.

See `docs/selection-design.md` for the design, the three measured findings, and the rules still to be decided.

## Local prototype (v0.2)

`python3 src/build_web_prototype.py` emits a single self-contained HTML page that opens from disk with no
server and no network: course pool joined from the three sources, three-dimensional conflict detection that
names the overlapping week range, category-based credit accounting, and a grab order tiered by deferability
and seat scarcity. It starts with the saved plan loaded, so the page **contains personal data and is
gitignored** -- the generator is committed instead, and rebuilds the same page.

Second run measured on the real data: 544 courses in the pool (217 in both sources, 197 official-only, 130
live-only); 561 sessions parsed with 0 parse failures; 237 week ranges containing a gap; 31 courses whose
weeks run past the 20-week semester. Problems met while building are logged in `docs/prototype-issues.md`.

## Submission

* Platform summary: `docs/submission-summary.md`, word count verified with `src/count_words.py`.
* Repository URL + tag: tag `a1-v1` on this commit, cited in section 9 of the brief.

## Status

- [x] Three sources located, frozen and hashed; join quantified
- [x] Field coverage of each source measured
- [x] Plan versions diffed; week occupancy and shared-slot case measured
- [x] Priority model drafted with real capacity data (`docs/priority-rules.md`)
- [ ] Baseline stopwatch measurement of one manual conflict check (`docs/A1-brief.md` section 4)
- [ ] Must-take set supplied from the degree programme (not derivable from any source)
- [ ] Search record for "does an existing tool already do this" written up (`raw/search-log.md`)
- [ ] Push to GitHub and tag `a1-v1`

# Search record: does an existing tool already do this?

**STATUS: filled in on 2026-09-28** (was an empty template until then). A negative claim is only as good as
the search behind it, so every channel, query and result is recorded below.

## What the search was for

The brief originally claimed **no found tool joins these two official sources, or carries the week-range
dimension**. That claim had no recorded search; when the search was actually run, the result was **not** "nothing
exists" — see rows 4–5. Corrected conclusion is at the bottom of this file.

| # | Date | Where | Query or method | Result |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-28 | Bing (`bing.com/search?format=rss`, curl + Chrome UA) | `course timetable clash checker tool`; `timetable conflict detection university`; `选课 冲突 检测 工具` | **Channel degraded**: returned Coursera/MOOC home pages and dictionary entries for the words "course"/"timetable"; the Chinese query returned 0 items. No usable result — recorded as a failed channel, not as evidence of absence. |
| 2 | 2026-09-28 | GitHub API `search/repositories` | `course timetable clash checker` | 2 repos, both **0 stars**; generic timetable libraries (a Flutter clash checker, a small Python helper). No official-source data. |
| 3 | 2026-09-28 | GitHub API `search/repositories` | `timetable conflict detection` | 117 repos; mostly school timetable *generators* (for staff). Closest: `hku-tpg-course-selector` (★1) — has conflict detection, but for HKU and a single cohort. |
| 4 | 2026-09-28 | GitHub API `search/repositories` | `ucas course planner` | **3 hits, all course planners for this same university system**: `HMBlankcat/UCAS-course-planner` (**★12, MIT, created 2026-08-30, last push 2026-09-01**), `luyuzhe-1/ucasnanjing-course-planner` (★5), `GOODLIZI/visualized-course-planner-for-UCAS-students` (★1). |
| 5 | 2026-09-28 | GitHub raw + API (read the source and data of the ★12 repo) | `public/data/courses.json` (1.5 MB) + `app/page.tsx` (63 KB) + `public/data/README.md` | **2077 courses.** Fields: `code, academy, name, englishName, property, level, discipline, hoursCredits, capacity, selected, teachingMode, examMode, leadProfessor, teachers, campus, sessions[{weeks, dayPeriods, room}]`. It already filters campus by the **18th code digit** and does **week-level clash detection** ("exclude courses that clash with the chosen timetable on teaching week / period", v1.4). **But**: no `semester` field anywhere (data is a single-semester autumn set, "来自项目内置的秋季课程数据"); `app/page.tsx` contains **no** ordering / remaining-seat / priority logic (no 排序, no 抢课, no 剩余 hits); data is a self-supplied static JSON with a note to "核对课程信息的准确性和再分发权限" (i.e. no source or timestamp provenance). |

## Corrected conclusion (replaces the original claim)

**"No existing tool does this" is not true and must not be claimed.** What is true:

- A close open-source tool exists (`HMBlankcat/UCAS-course-planner`, ★12, MIT, 2026-09-01) and it already covers
  campus filtering by code, week-level clash detection, capacity/enrolled fields, and degree-requirement checks.
- What it does **not** cover — and what this project therefore still has to do:
  1. **开课学期 (which semester a course runs in)** — its data set is single-semester with no semester field, so
     "can this course be deferred to spring?" cannot be answered;
  2. **抢课决策** — no priority ordering (single-semester-only + remaining seats → the order to grab in the
     window); it only warns/screens;
  3. **来源可追溯** — no source/timestamp provenance, and it does not reconcile the coverage gap between the two
     official sources (59 / 11 courses).

Search terms, channels, dates and raw results are all above so the remaining claim can be re-checked.

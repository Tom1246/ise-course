# Evidence ledger

Every claim in `doc/assignments/A1-brief-en-2026-09-28.md` traced to a source, the method used to obtain it, the date, and where the
raw output lives. Regenerate everything with the commands in `README.md`.

## Sources

| ID | Type | Source | Method and date | Where the output lives |
| --- | --- | --- | --- | --- |
| E1 | Personal operation record | `选课规划-已选课程-2026-09-05.xlsx`, `选课规划-已选课程-2026-09-15.xlsx`, planner backup `选课地图-本地备份 (3).json` | file inspection, hashing, cross-version cell diff; 2026-09-25 to 2026-09-27 | `data/s3-my-plan-versions/plan-versions.md` |
| E2 | Official rule text | selection instructions plus the two official workbooks: `2026-2027学年秋季和春季开课计划表0828.xlsx`, `2026-2027学年研究生核心课和专业课列表…0828.xlsx` | read from the imported records; stable import sha256 recorded; 2026-09-27 | `data/s1-plan-workbook/snapshot-provenance.md` |
| E3 | Official workbooks, structured import | same two workbooks, via the planner backup (4,877 records) | `python3 scripts/freeze_snapshot.py`; 2026-09-27 | `data/s1-plan-workbook/sections-snapshot.json` + `.sha256`, `data/s1-plan-workbook/snapshot-provenance.md` |
| E4 | Course-library snapshot (crawled from the academic system) | archived raw download: `https://courseplanner.cysdy.cn/default-courses.json` (2,991 entries, 8,103,455 bytes) | `curl` then `python3 scripts/fetch_public_listing.py`; 2026-09-27 | `data/derived/course-library-snapshot.json` + `.sha256`, `data/derived/live-listing-provenance.md` |
| E5 | Join of E3 and E4 by course code, plus the saved plan | course-code join; 2026-09-27 | `data/derived/live-listing-provenance.md`, `data/derived/plan-priority-summary.md` |

## Hashes

| Artefact | sha256 |
| --- | --- |
| planner backup `选课地图-本地备份 (3).json` (not committed) | `62594e799e1c83a8fdc2cacd0239f36e14264b55282c768853c89f6690f463ad` |
| `data/s1-plan-workbook/sections-snapshot.json` (committed) | `ffcf1ae023e59fe8a09d83584fe7ba8293eb982cce8887f51e7db140f98d8c9e` |
| raw public listing download (not committed, 8,103,455 bytes) | `7c6090e40801d1ba4ebf3665c54eafaf4ec6e5e3565d996df74e63fac53e8413` |
| `data/derived/course-library-snapshot.json` (committed) | see `data/derived/course-library-snapshot.json.sha256` |

The two saved plan files are personal working files and are not committed; their hashes are recorded in
`data/s3-my-plan-versions/plan-versions.md`.

## Which fields exist where

| Field group | Official workbooks (E3) | Course-library snapshot (E4) |
| --- | --- | --- |
| campus | yes | **no field at all** (only inferable from course-code position 18 = `Y`) |
| semester | yes (208 autumn-only, 179 spring-only, 27 both) | no |
| attribute, credits | yes | yes |
| 开课周 (week range) | **0 of 732** | 347 of 347 |
| 星期节次 (weekday/period) | **0 of 732** | 347 of 347 |
| 限选 (capacity) / 已选 (enrolled) | **0 of 732** | 347 of 347 |
| degree-programme requirement | no | no — human input required |

## Independence check

E1 is the author's own working record; E2 and E3 come from the institution that publishes the plan; E4 comes
from a third-party tool that republishes the same official plan in a different shape; E5 is a join across them.
The independence that matters here is that **E3 and E4 are produced by different pipelines from the same
underlying plan**, which is why their coverage differs — and E1 is the only record of what actually changed
between two planning attempts.

## What would contradict the findings

- A single source carrying campus, semester, week range, weekday/period and remaining seats for the same
  courses would falsify the central claim. Searched on 2026-09-27\*; record in `ai/search-log.md`.
- Evidence that the missing 197 codes' week/period fields exist in some fourth source would change the scope
  from "join and fill" to "join".
- Evidence that the empty capacity cells in the official workbooks are intentional and meaningful (rather than
  simply absent) would change how "unknown" is reported.

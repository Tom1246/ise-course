# A2 — Data governance: source, authority, quality, retention, deletion, privacy

This document answers one question at field granularity, not at "dataset" granularity: **for each field of each
source, where does the value come from, who is allowed to believe it, how long it is kept, how one person's copy
of it is deleted, and what it costs if the field is wrong.**

Written 2026-10-05. Companions: `domain-glossary.md` (entities and value objects), `invariants.md` (the three
rules and their limits), `conflict-decision-table.md` (the 8-row rule), `data-dictionary.md` (field types),
`model-walkthrough.md` (which cites this file's §5 as the executable deletion procedure).

**Source numbering is fixed and must not be renumbered.** S1 = the official course-planning workbook (2026-08-28);
S2 = the university's public course listing, `jwba.ucas.ac.cn` (crawled 2026-09-27); S3 = the author's own two
saved plan versions; S4 = the AI-generated plan, which is **derived** from S1 and therefore is *not* an
independent source; S5 = the programme requirements (校发培养字〔2025〕92号); S6 = the school's autumn course-selection
notice. Two further inputs exist that are **outside the S1–S6 numbering** and are labelled `X1` / `X2` below so
that they can never be mistaken for an official source.

---

## 1. Source inventory

Acquisition time, method, hash, and authority grade, per source. Authority grade is one of three words and is
read per-field in §2:

- **authoritative (权威)** — this field is taken from here;
- **reference (参考)** — read for context, or used when the authoritative source lacks the field, and labelled as
  such in the output;
- **cross-check only (仅交叉验证)** — never a value's origin; used only to confirm or to distrust an authoritative
  value.

| ID | Source (form) | State | Acquired | Method | Artefact + sha256 | Authority grade |
| --- | --- | --- | --- | --- | --- | --- |
| **S1** | Official course-planning workbook — `2026-2027学年秋季和春季开课计划表0828.xlsx` + `…研究生核心课和专业课列表…0828.xlsx` (xlsx, 2 workbooks) | planned | issued 2026-08-28; imported & frozen **2026-09-27** | `python3 scripts/freeze_snapshot.py` (structured import via the planner backup) | `data/s1-plan-workbook/sections-snapshot.json` `ffcf1ae023e59fe8a09d83584fe7ba8293eb982cce8887f51e7db140f98d8c9e` (+ `.sha256`); provenance `snapshot-provenance.md` | **authoritative for 开课学期**; reference for 课程属性/学分/学时/开课校区 |
| **S2** | Public course listing, `https://jwba.ucas.ac.cn/sc/public/coursePublic` (list) + `/sc/course/coursetime/{cid}` (schedule) — server-rendered HTML, no login, no captcha | current at capture | 2026-09-27 (2026-27 terms captured **16:31:49** Asia/Shanghai) | `python3 scripts/fetch_official_db.py --terms … --campus 20`; `--sleep 0.25`, 3 retries; cached | `data/s2-public-listing/89576-campus20.json` (341 rows) `6510aa2e4127a096208de7d02916c6bc5c8643f66f050d68470cff2d83362db5` (+ `.sha256`); 6 past terms under `history/` with per-term list-page and output hashes (e.g. 74468 → `a90296c9…`, 84068 → `6e1f4505…`); provenance `official-db-provenance.md` | **authoritative for 开课校区, 课程属性, 学分, 课时, 开课周, 星期节次, 上课地点, 限选, 已选, 教师**; also the sole source of 学期 boundaries *only* as "which term it was crawled under" |
| **S3** | The author's two saved plan versions — `选课规划-已选课程-2026-09-05.xlsx`, `…-2026-09-15.xlsx` (xlsx, **not committed**) | own working record | exported 2026-09-05 11:33 / 2026-09-15 21:41; inspected **2026-09-27 15:37** | `python3 scripts/inspect_plan_versions.py`; hash + cross-version cell diff | only the report is committed: `data/s3-my-plan-versions/plan-versions.md`; the two files' hashes are recorded there (`8d6f9e65…`, `dcc6cae7…`) | **authoritative for "what I actually chose / what changed"**; nothing else |
| **S4** | AI-generated plan (2026-08-28) | derived from S1 | 2026-08-28 | — | `ai/ai-use-log.md`, `doc/prototype-issues.md` | **not a source** — kept only as a failure case; excluded from the independence count |
| **S5** | Programme requirements — 中国科学院大学电子信息专业学位研究生培养方案（校发培养字〔2025〕92号）(PDF, not committed) | official, stable | extracted **2026-09-27** | verbatim text extraction, §第二部分 + 六、必修环节及学分要求 | `data/s5-programme/degree-requirements.json` + `.sha256` sibling (added 2026-10-04); provenance `data/s5-programme/provenance.md` — but see §3.5, the transcription itself is still manual | **authoritative and sole source for the credit floors and degree-course rules** |
| **S6** | School notice on autumn course selection | official, event-scoped | read 2026-09 | quoted text | cited in the A1 brief and `doc/evidence-ledger.md`; no archived copy | **authoritative for the registration window and the conduct rules** (no cross-campus for centralised-teaching students; no disrupting/hoarding registrations) |
| **X1** | Third-party course library, `courseplanner.cysdy.cn/default-courses.json` (JSON) | snapshot, maintainer-updated 2026-09-14 13:00 | raw download 8,103,455 bytes; **not committed**; hash re-verified 2026-09-27 | `curl` + `python3 scripts/fetch_public_listing.py` | raw `7c6090e40801d1ba4ebf3665c54eafaf4ec6e5e3565d996df74e63fac53e8413` (kept, not committed); frozen subset `data/derived/course-library-snapshot.json` (347 Yuquanlu codes) `3724ade7ff05dcd3465c017f965feffe0eaa26cfbcaafebf976d268003122a69`; provenance `data/derived/live-listing-provenance.md` | **reference and cross-check only** — never authoritative for any field |
| **X2** | SEP auxiliary fields, frozen from X1's raw download | derived from X1 | frozen 2026-09-27 | `python3 scripts/freeze_aux_fields.py` (refuses to run unless the raw download's sha256 prefix matches `7c6090e4…`) | `data/derived/sep-aux-fields.json` (2,951 course codes) `7d48eb75e1af1477d2475d710449f2065307d36eb0658a615cea48fb906061cc` | **reference only** (授课方式/考试方式/是否远程教学/助教/培养层次) |

**Independence, stated honestly (unchanged from the ledger).** S1, S2, S5, S6 are official publications — one type.
S3 is the author's own record — the other type, and the only record of what actually changed between two planning
attempts. S4 is derived from S1 and is *not* counted. X1 is a third-party re-publication of SEP data: it is a
**different pipeline over the same underlying facts**, which is why it is usable as a cross-check (S2 and X1 agree
exactly on 星期节次+开课周 for sampled courses, e.g. 实用最优化算法 = 周三第 5–7 节, weeks 2–5/7–17) and *not*
usable as an authority.

### 1.1 What is deliberately not in the repository

Repeated here because retention (§4) and deletion (§5) depend on it: student ID, name, programme code and the
personal plan spreadsheets; any other student's selection record (never read); per-course personal priority detail
and the personal credit-gap file (`data/private/`); the prototype HTML (it embeds the personal plan); the raw HTML
crawl cache (`data/s2-public-listing/cache/`); the 8.1 MB X1 raw download; the 4,877-record planner backup; and
credentials/tokens/cookies, of which there are none anywhere in history.

---

## 2. Field-level authority

One row per field. "Authoritative source" is where the value is taken from; "fallback" is what is allowed when the
authoritative source has no value; "conflict rule" is what happens when two sources disagree.

| Field (Chinese) | Type | Authoritative | Fallback (labelled in output) | Conflict rule |
| --- | --- | --- | --- | --- |
| 课程编码 `code` | 18-char string | S2 (live) | S1 (planned) | Treat as identity: if the codes differ the rows are **different courses**, never merged. If S1 and S2 carry the same code with different names, S2 wins for the name and the difference is logged. |
| 课程名称 `name` | string | S2 | S1 | S2 wins (S2 is the current system); a mismatch is logged as a naming drift, not silently overwritten. |
| 开课校区 `campus` | enum (`Y`/`H`/`Z` by code position 18; S2 carries the word) | **S2** (a real column) | S1 (real column) | S2 wins. For **X1 only** — which has **no campus field at all** — campus is *inferred* from code position 18 and must stay labelled `inferred`; it is never promoted to a fact. |
| **开课学期 `semester`** | enum (秋/春/both) | **S1** — the only source that has it (208 autumn-only, 179 spring-only, 27 both in the kept subset) | none | S2 has no per-course term and X1 has none; the only S2-derived term statement is "this row belongs to the term it was crawled under" (2026-27 秋 = termId 89576). If S1 says 春季 and S2 shows it in the autumn crawl, that is a **coverage finding**, reported, not resolved. |
| 课程属性 `attribute` | enum | **S2** | S1 | S2 wins; S1 is the corroboration (data-authority §二 reached the same conclusion: ❷ may mutually confirm, ❶ is authoritative). |
| 学分 `credit` | number | **S2** | S1 | S2 wins. Type caveat: S2 stores `"1.00"` (string), S1 stores a number — coerce at the boundary, keep the source string. |
| 学时 `hours` | number | **S2** | S1 | S2 wins. |
| 开课周 `weeks` | **interval set**, e.g. `[(2,5),(7,17)]` | **S2** (detail page) — 347/347 rows in the frozen subset | none | S1 has this field in **0 of 732** rows; X2/X1 are cross-check only. Never a single number (see glossary: `第6周` = `[(6,6)]`). |
| 星期节次 `time` / session weekday+period | `DayPeriod` list | **S2** (detail page) — 347/347 | none | Same as above: 0 of 732 in S1. X1 is an exact-match cross-check. |
| 上课地点 / 教室 `room` | string, informational | S2 for 地点 | X1/X2 for 教室 | Not part of any invariant. Both are reference-grade; label the origin in the UI. |
| 限选 `capacity` | non-negative integer, or **unknown** | **S2** | X1/X2 **cross-check only** | S2 wins. `0` / empty = **unknown** (never "unlimited", never "full"); `"/"` = the official "no enrolment limit" — a *different* value from blank (A1 finding #3). |
| 已选 `enrolled` | non-negative integer | **S2** | X1/X2 cross-check only | S2 wins. Time-varying; always display with the capture time (§3). |
| 教师 `teacher` / `chief` | string (public professional info) | S2 | X1 | S2 wins. Instructor names are public course information; they are not used to build any per-person profile. |
| 授课方式 / 考试方式 / 是否远程教学 / 助教 / 培养层次 | enum/string | **none on any official source** | **X2 reference only** | X2 is human-copied from a logged-in SEP view; A1's reverse-lookup found 0 hits for these words on all three official pages. Treat as *unverified reference*, never as a row-trustworthy fact; if it drives a decision, say so in the output. |
| 培养方案学分下限 / 学位课规则 | numbers + rules | **S5** — sole source | none | No other source has it; where S5 is ambiguous it is a modelling gap (see `degree-requirements.json` `known_modelling_gaps`), not something to be filled from a course table. |
| "我实际选中的课 / 最终结果" | personal | **S3** | S2/S3 aggregate | Only S3 has it, and S3's raw files are never committed (§4). Post-2026-09-18 (system closed) it is only recoverable from an exported result. |
| 报名窗口 / 纪律规则 | dates + conduct | **S6** | none | Quoted text; not re-derived. |
| 冲突 `Conflict` | boolean | **derived** | — | Never stored, never sourced: computed from two `Slot`s by the three-condition rule (glossary §3, `conflict-decision-table.md`). |

**The one-line answer to "which source should I trust":** take S2 first; use S1 only to fill 开课学期 and to
corroborate 属性/学分/学时; demote X1/X2 to cross-check and auxiliary; use S5 for the credit floors and S6 for the
window and the rules; use S3 only for what actually happened to **my** plan.

---

## 3. Quality: known absences, sentinels, drift, expiry

### 3.1 Known absences (per field, per source)

| Absence | Measured | Consequence |
| --- | --- | --- |
| 开课周 in S1 | **0 of 732** | Nothing can be conflict-checked from S1 alone |
| 星期节次 in S1 | **0 of 732** | same |
| 限选 / 已选 in S1 | blank in the snapshot rows (e.g. `"capacity": "", "enrolled": ""`) | no capacity pressure from S1 |
| 开课学期 in S2 / X1 | no field | S1 is the only 学期 source; 6 of 14 planned courses have 学期 unknown **from every source** (`plan-priority-summary.md`) |
| campus in X1 | **no field at all** | inferred from code position 18, always labelled |
| 培养方案要求 | absent from **all** of S1/S2/X1/X2 | human input; frozen at `data/s5-programme/degree-requirements.json` |
| Join coverage | 217 codes in both; **197 S1-only** (no week/period/capacity at all); **130 X1-only** (no campus, no semester) | for 197 courses a conflict check is **impossible** from the structured sources; that is a measured limit, committed as a number, not smoothed over |
| S2 parse failures | 12 recorded failures across terms (e.g. `180089050200MB001Y-201`, 硕士学位英语（慕课学习）) | those courses exist but carry no parsed schedule; reported, not guessed |
| S2 spring 2026-27 (termId 89577) | **0 rows**, 158-byte file | 2027 spring was unpublished at capture; any spring statement is out of scope |

### 3.2 Sentinel values (this is where a literal reading produces a false headline)

- **`capacity = 0` means "not set", not "admits nobody".** 40 rows in the frozen snapshot have capacity `0` with a
  non-zero enrolment — one shows **86 enrolled** against it (`180090125601M2004Y` 财务与成本管理).
  `invariants.md` I3 records that reading this literally would have produced the wrong headline "the school
  oversells 40 sections"; after separating the sentinel: **real over-capacity violations (`enrolled > capacity > 0`)
  = 0**, and the honest conclusion is *"cannot be determined from this field"* — **not** *"none exists"*.
  A1 separately observed genuine over-capacity (自然辩证法 422/420) from an earlier crawl, which is exactly why
  "0 violations" and "422/420" can both be true: different capture times.
- **Empty ≠ `/` ≠ `0`.** Blank = unknown; `"/"` = the official "no enrolment limit"; `0` = not set. Three distinct
  meanings in one column; the checks report them in separate buckets so a sentinel can never be laundered into a
  violation count.
- **Stringly-typed numbers.** S2 gives `"111"`, `"22"`, `"1.00"`; S1 gives numbers. Compare numerically, keep the
  original string for the record.
- **Interval sets, not scalars.** 237 of 561 course records (42%) have discontinuous teaching weeks; this is
  normal, not an anomaly (A1 overturned claim #4).

### 3.3 Fields that move with time

`capacity`, `enrolled`, and therefore "remaining seats" and the whole **grab order**, are the only fields that are
*expected* to change between two captures. Everything else (name, attribute, credit, room, code) is stable within a
term.

- **Snapshot expiry risk.** The committed S2 snapshot was captured **2026-09-27**, which is **after** the
  registration window closed (2026-09-18 12:30). The conflict-check claim is unaffected (times do not move after
  publication), but the grab-order claim **cannot be validated against the committed snapshot at all**, and a
  later re-crawl would produce different numbers and different hashes.
- The model names this state `SnapshotStaled` (glossary §4): the plan is a hypothesis, not a fact. The only defence
  is that every output prints the capture time, and a stale one must be re-crawled.
- A1 measured the drift directly: 09-05 vs 09-15 enrolment figures differ, and the two plan versions differ by
  **22 removed / 45 added timetable cells**.

### 3.4 Format properties that are *not* guarantees

`invariants.md` §0 records that all 347 courses carry both a time and a week string, with matching `；`-separated
segment counts, and 0 unparsable segments. That is a property **of this snapshot**, not of the format: the check
*counts* mismatches and would report them rather than assume them.

### 3.5 Provenance hygiene defects found while writing this document (recorded, not fixed here)

These are small but real, and they are the kind of thing a governance section exists to surface:

1. **Stale filenames in two `.sha256` sidecars.** `data/derived/course-library-snapshot.json.sha256` names the file
   `yuquanlu-live-courses.json`, and `sep-aux-fields.json.sha256` names `aux-sep-fields.json`. The **hashes match
   the files they sit beside** (verified: `3724ade7…`, `7d48eb75…`), so integrity is intact — only the second
   column of the sidecar is stale from an earlier rename. A verification script that trusts the *filename* column
   would fail on a file that is perfectly fine.
2. **The 2026-27 captures (termId 89576/89577) are not covered by `official-db-provenance.md`**, whose six term
   sections stop at 84068 (2025-26 春). The 89576 file does carry its own `crawled_at` (2026-09-27 16:31:49) and a
   matching `.sha256`, so the record is not lost — but the provenance note is incomplete.
3. **`data/s5-programme/degree-requirements.json` had no `.sha256` sibling** (closed on 2026-10-04: the sibling and
   `data/s5-programme/provenance.md` are now committed, and the source PDF's own sha256 is recorded there). The
   harder half of the gap stays open and is stated rather than papered over: the extraction was done **by hand** from
   a PDF that is *not* committed (a university document), so the hash pins the JSON and the identity of its source,
   not the fidelity of the transcription. This remains the one irreproducible link in the I2 credit-floor claim.
4. **X2 holds 2,951 course codes against 2,991 raw X1 entries** (the file is keyed by course code, so 40 duplicate
   codes collapsed). The file's own metadata does not state this; the count is a measured fact, not a documented one.
5. **S1 and S2 do not share a row schema.** S1 stores one coarse `sessions[{room,time,weeks}]` plus top-level
   `time`/`weeks` (empty); S2 stores a parsed `schedule[{weekday,periods,weeks,rooms}]`. Any join must state which
   shape the field came from.

---

## 4. Retention

Three retention classes; **what is kept is a function of whether it can be re-derived**, not of whether it is
interesting.

### 4.1 Long-term (kept indefinitely, with hash and capture time)

Frozen official/derived inputs and their `.sha256` siblings — the audit trail, and the reason any A1/A2 number can
be re-checked years later. None of it is personal data; all of it is either published by the university or derived
from published data.

| Artefact | sha256 | Why kept |
| --- | --- | --- |
| `data/s1-plan-workbook/sections-snapshot.json` (+ `.sha256`) | `ffcf1ae0…` | the planned-offering side of every join; 开课学期's only source |
| `data/s2-public-listing/*.json` + `history/*.json` (+ `.sha256` each) | e.g. 89576 `6510aa2e…`, 74468 `a90296c9…`, 84068 `6e1f4505…` | the current-state side; re-crawl would change hashes |
| `data/derived/course-library-snapshot.json` (+ `.sha256`) | `3724ade7…` | X1's frozen subset — the schema/sha are already cited, so it must not change |
| `data/derived/sep-aux-fields.json` (+ `.sha256`) | `7d48eb75…` | X2 reference fields; frozen with a forced raw-hash check so the X1 chain stays intact |
| `data/derived/plan-priority-summary.md`, `credit-gap-summary.md`, `data/derived/a2/*` | (regenerated by script) | **aggregates only** — counts, tiers, buckets; no row-level personal detail |
| `data/derived/a2/sample-plan.json` | (regenerated) | an *illustrative* 6-course plan, explicitly not the real plan, so I1/I2 run from the repository alone |
| `data/s5-programme/degree-requirements.json`, `data/s3-my-plan-versions/plan-versions.md`, `doc/evidence-ledger.md`, `doc/data-authority.md` | — | the rules and the claim→source→file mapping |

### 4.2 Aggregates only (retained, but never at row level)

Anything touching a person: the plan's totals (14 courses, 26 course-learning credits, 25 evidenced-open in 秋季,
8 of 13 at ≥90% capacity, P0/P1/P3/PX/PU = 3/3/1/1/6), the credit-gap verdict (2 categories short). These are kept
because a claim needs a number; there is no per-course commitment anywhere in the repository.

### 4.3 Not retained (or local-only)

| Item | Policy | Why |
| --- | --- | --- |
| The two S3 `.xlsx` plan versions, the planner backup, the prototype HTML | **local only, never committed** (`*.xlsx`, `选课地图-本地备份*.json`, `prototype/*.html`, `data/private/` are all gitignored) | personal data; the prototype embeds the plan |
| `data/s2-public-listing/cache/` (1,400+ raw HTML pages) | **delete after a successful freeze** | re-fetchable and large; kept only so a crawl can resume |
| X1 raw download (8.1 MB) | **not committed**; keep the hash `7c6090e4…` only | re-fetchable; the hash is the evidence |
| The 4,877-record planner backup | **not committed**; keep the hash `62594e79…` only | contains the 开课校区 field for the whole school that S1's kept subset drops |
| `data/private/` (`credit-gap.md`, `plan-priority.md`) | **kept during the course, deleted at the end** (§5) | per-course personal priority detail |

### 4.4 Where it is retained

Public GitHub (`github.com/Tom1246/ise-course`) for §4.1 and §4.2; the author's local machine only for §4.3.
There is no third-party store, no cloud bucket, no analytics sink.

**Retention is limited by history, and this must be said plainly:** a file removed by a *new commit* still exists in
the repository's history. §4.1/§4.2 artefacts are chosen so that nothing personal has ever been committed; the
gitignore in §4.3 is the first line of defence, and the pre-commit protocol is not to stage anything under those
patterns.

---

## 5. Deletion

A procedure for removing **one person's data** — written so it can be *executed*, not promised. It assumes the
subject is the author (the only person whose data this project ever holds). Run it in order; each step's check must
pass before the next is attempted. **This document does not execute git operations**; steps 5 and 8 state the
commands to run and their expected output.

### Step 1 — delete the gitignored private working copies

```bash
rm -rf data/private/                       # credit-gap.md, plan-priority.md (per-course personal detail)
rm -rf prototype/*.html prototype/*.png    # the prototype embeds the plan; keep the generator
rm -rf data/s2-public-listing/cache/       # re-fetchable raw HTML, no personal content, but large
```

Delete the personal working files outside the repository as well (the original imports and any exported copy).
`~` globs are not recursive by default, so locate them explicitly rather than trusting `**`:

```bash
rm -f ~/Downloads/选课地图-本地备份*.json
rm -f ~/Downloads/选课规划-已选课程-*.xlsx
find ~/Desktop -maxdepth 6 -name '选课规划-已选课程-*.xlsx' -print -delete
```

### Step 2 — confirm the personal freeze inputs are gone and only their hashes remain

The two S3 `.xlsx` files and the planner backup are the *inputs* to S1's import and to the plan-version report.
They must be gone from every location, and the hashes recorded in `data/s3-my-plan-versions/plan-versions.md`
(`8d6f9e65…`, `dcc6cae7…`) and `doc/evidence-ledger.md` (`62594e79…`) are the only thing that needed to survive:

```bash
find ~ -name '选课规划-已选课程-*.xlsx' -o -name '选课地图-本地备份*.json' 2>/dev/null
# expect: no output
```

If a hash line is the only remaining trace, the deletion preserved the evidence and removed the data — which is the
intended end state. If the files are still present, the greps in step 4 will pass over an empty repository while the
data sits on disk, so this step is a precondition for step 4's result to mean anything.

### Step 3 — confirm the repository now holds only aggregates

Read, do not assume:

```bash
python3 -c "import json;d=json.load(open('data/derived/a2/sample-plan.json'));print(d['_note']);print(d['codes'])"
# expect: the illustrative note + 6 codes that are explicitly NOT the real plan
```

Then open `data/derived/credit-gap-summary.md` and `data/derived/plan-priority-summary.md` and confirm every
number is a count, a total, a tier or a bucket — no course name tied to the author, no per-course row.

### Step 4 — `git grep` for the four string classes

Run each over tracked files only (`git grep` reads tracked files, so gitignored private files cannot create false
confidence), from the repository root:

```bash
# The literal values are supplied locally and are deliberately not written down in this repository
# (writing them here would defeat the step that is meant to find them):
#     export SID='<student id>'  NAME='<name or pinyin>'   # then run the greps below

# (a) student ID
git grep -nE "$SID"

# (b) name / pinyin / handle
git grep -niE "$NAME|Tom1246"

# (c) programme code — ANCHORED, see the trap below
git grep -nE '(^|[^0-9])0854[0-9]{2}([^0-9]|$)'

# (d) local absolute paths / home-relative paths
git grep -nE '/Users/[A-Za-z0-9._-]+/|~/Desktop|~/Downloads|~/Documents|files/工作'
```

**The trap in (c), measured:** a naive `0854[0-9]{2}` matches **658 lines** in this repository, because almost
every course code embeds its programme code (`180086085404P2003Y` contains `085404`). The anchored pattern above
reduces that to **1 real hit**. An unanchored grep here is not a strict check — it is noise that trains the reader
to ignore the output.

**Measured result at the time of writing (A2, 2026-10-05) — non-zero, and that is the point of the step:**

| class | hits | where |
| --- | --- | --- |
| (a) student ID | **1** | `README.md:6` |
| (b) name / handle | **6** | `README.md:4,6,125` (byline + repo URL `Tom1246`), `doc/assignments/a2/A2-summary-en-2026-10-04.md:31`, `doc/assignments/a1/A1-summary-en-2026-09-28.md:20`, `doc/archive/A1-brief-en-v1-2026-09-27.md:5` (`Author: Liwei Tang`) |
| (c) programme code, anchored | **1** | `data/s5-programme/degree-requirements.json:9` (the programme string) |
| (d) local paths | **10** | `scripts/{inspect_plan_versions,build_web_prototype,credit_gap,freeze_snapshot,rank_plan_priority}.py` (the `~/Downloads/…` defaults), `doc/selection-design.md:102`, `data/s5-programme/degree-requirements.json:4` (`local_copy`), `data/s1-plan-workbook/snapshot-provenance.md:3`, and — before this pass — `notebooks/a2-domain-model-walkthrough.ipynb:36`, which printed the machine's absolute home path into a committed notebook |

A defect this scan actually caught: the A2 notebook's first cell once printed the machine's absolute home path into its stored output (a full `/Users/...` path, i.e. the author's local directory layout). The notebook now prints only the repository folder name, and the path is gone from the committed output. The finding is kept here because the scan is the reason it is gone — and because the same failure mode (a tool printing its working directory into a stored artefact) will recur in A3 and beyond.

**These non-zero hits are the honest part of the procedure.** As of A2 the repository still carries the author's
name and student ID (`README.md`), the GitHub handle in four files, the programme code in the committed
credit-rules file, and ten local-path strings — one of which is a full absolute path with the username. Most are
*deliberate* (attribution, reproducible script defaults, provenance of an uncommitted source) and the student ID is
the one that carries real risk. The deletion is finished only when every hit has been **classified** — keep with a
stated reason, or remove and regenerate the artefact — not when the count reaches zero. A check that is written to
expect zero, in a repository that legitimately contains attribution, will be disabled by the first person who sees
it fail for a good reason.

### Step 5 — re-scan committed PDFs page by page with pymupdf

The greps above see the `.md`/`.json`/`.py` text; PDFs hide theirs in a text layer. Extract and scan every
committed PDF:

```bash
python3 - <<'PY'
import pathlib, re, fitz
pats = {
  "student_id": re.compile(os.environ.get("SID_PATTERN", r"\b\d{4}[A-Z]\d{10}\b")),
  "name":       re.compile(os.environ.get("NAME_PATTERN", r"$^"), re.I),
  "prog_code":  re.compile(r"(?:^|[^0-9])0854\d{2}(?:[^0-9]|$)"),
  "local_path": re.compile(r"/Users/[\w.\-]+/|~/Desktop|~/Downloads|~/Documents"),
}
hits = 0
for p in pathlib.Path(".").rglob("*.pdf"):
    with fitz.open(p) as doc:
        for i, page in enumerate(doc, 1):
            text = page.get_text()
            for name, rx in pats.items():
                for m in rx.finditer(text):
                    hits += 1
                    print(f"{p} p{i} [{name}] ...{text[max(0,m.start()-40):m.end()+40]!r}...")
print("TOTAL HITS:", hits)
PY
```

Run it **once per PDF set** — the A1 briefs are text-layer PDFs, so this is the step that would catch an ID or a
personal course list that survived a Markdown edit. Each hit is then classified as (i) a public fact in an
offer-set claim, or (ii) personal detail, which must be removed and the PDF regenerated.

**Measured over the 9 committed PDFs (A2, 2026-10-05): 2 hits, 0 student-ID hits.**

| file | page | class | text |
| --- | --- | --- | --- |
| `doc/selection-design.pdf` | 4 | local_path | `本地（~/Desktop/files/工作/硕士/）` |
| `doc/archive/A1-brief-en-v1-2026-09-27.pdf` | 1 | name/handle | the first English draft's own byline |

The student ID appears in **no** committed PDF — the same string that §5 step 4 finds in `README.md`. That is the
point of scanning the PDFs separately: the two artefacts are generated from different sources, so passing one says
nothing about the other.

### Step 6 — scan the git history, not just the working tree

```bash
git log --all --oneline -- '*.xlsx' 'data/private/*' 'prototype/*.html' '选课地图-本地备份*'
```

If anything is returned, the data is in history even though the file is gone. Recovering it requires a history
rewrite (`git filter-repo`) and a force-push — a decision for the author, and the reason the gitignore exists.
Because this project's rule is "never commit it in the first place", the expected answer here is **empty**.

### Step 7 — verify the tree is clean and re-run the checks

```bash
git status --porcelain          # expect: no modifications to tracked files (deletions staged by the author)
python3 scripts/a2_check_invariants.py    # still exits 0: the checks must be runnable without private data
```

The point of step 7: deleting the personal data must not break the invariant checks. Because the checks run on
`data/derived/a2/sample-plan.json` and the committed catalogue, not on the real plan, they still pass — which is
itself the evidence that the repository never depended on the private data.

### Step 8 — record the deletion

Append the date, the bytes removed, and the grep results to the A2 log so the deletion is verifiable after the
fact. A deletion that is not recorded is indistinguishable from a deletion that was never run.

---

## 6. Privacy and access

### 6.1 Who may access what

| Tier | Contents | Who can read it | What protects it |
| --- | --- | --- | --- |
| **1 — public repository** | S1/S2 frozen snapshots, S5 rules, derived aggregates, scripts, docs, the illustrative sample plan | anyone, including anonymous GitHub readers | nothing withheld that is personal; the repository is public by design |
| **2 — gitignored, present in the local checkout** | `data/private/`, the `.xlsx` plan versions, the planner backup, the prototype HTML/PNG, the raw crawl cache | only the author's local account | `.gitignore` patterns (`*.xlsx`, `选课地图-本地备份*.json`, `data/private/`, `prototype/*.html`, `data/s2-public-listing/cache/`) |
| **3 — local-only, never inside the repository** | the original imports in `~/Downloads`, the A2 working folder, the real plan | only the author | never staged; §5 is the exit procedure |

The unit of work is **one student, one semester, one plan** (glossary §1) — no cohort, no department, so there is
no product reason to hold anyone else's row.

### 6.2 What is in tier 1 that mentions a person

Instructor names (`teacher`, `chief`) in the S2 snapshot — **public professional information**, published by the
university on a public page, retained verbatim as part of the official record, and used only to identify a course,
never to build a profile. The author's own name/ID appear only in the README byline (see §5 step 4, flagged).

### 6.3 Red lines (hard-coded, not policy aspirations)

1. **Do not collect another student's enrolment record.** `Enrollment` (student × section) is the identifying
   entity (glossary §2); the crawl touches course-level public pages only and never a per-student view. This is
   A1's abuse scenario 2, and the answer is that the data is never read — not that it is read and hidden.
2. **Do not register on anyone's behalf.** The system has **no actuator**; it emits a timetable and an *order*
   only. Automatic seat-grabbing breaks first-come-first-served and is forbidden by the school notice (S6). The
   registration context is drawn as a dashed, out-of-scope box on the context map precisely so that adding a
   submit step is a visible scope change.
3. **Do not export an identifying roster.** Outputs are per-plan, for the plan's owner. No list of people, no
   student IDs, no names of students, no cross-student join. Where a person's data must appear in a committed
   artefact, it appears as an aggregate.
4. **No credentials, tokens or cookies** anywhere — no login is used by any committed script; the crawl reads
   public pages only.
5. **Do not let the AI fill a gap with a plausible value.** Every section must trace to a source + capture time; a
   mismatch is an error, not something to be smoothed over (A1's own AI misuse, and the reason `ai/ai-use-log.md`
   exists).

### 6.4 Access-control reality check

There is no authentication, no role model and no encryption in this project, and pretending otherwise would be
worse than the truth. The whole access model is: **tier 1 is public, tiers 2–3 exist only on one machine, and the
only thing that keeps them apart is the `.gitignore` plus the discipline of never staging a private file.** §5
exists because discipline alone is not a control.

---

## 7. Threat to the claim

The A2 claim has two halves, and they are threatened by *different* fields. Stating which is which is how this
document exposes rather than hides the weakness.

### 7.1 What breaks the conflict-detection claim

The claim: *two sections clash iff same weekday ∩ overlapping periods ∩ overlapping weeks, and this is decidable
from frozen committed data.*

| Field | If it is wrong or missing | Effect on the claim |
| --- | --- | --- |
| **开课周 `weeks`** | a wrong or absent interval set | **the claim fails in both directions**: a bitemporal pair (自然辩证法 weeks 2-5/7-10 vs 中特 weeks 11-18 sharing cell C5) becomes a false conflict, and a genuine partial overlap is missed. This is exactly A1's observed failure — the AI read weeks wrong and produced a wrong recommendation. For the **197 S1-only codes** the field is absent, so the claim is simply *not decidable* for them — a limit, not a bug. |
| **星期节次 `time`** | shifted by one period or one weekday | every pair in the catalogue changes membership; the 4,757 figure is a function of this field alone |
| **课程编码 `code`** | a wrong position-18 char, or a mis-join | silently moves a course in or out of the campus subset; two different sections could be merged into one identity |
| **学分 `credit`** | wrong credit | only threatens I2 (the floor verdict), not I1 |
| 课程属性 `attribute` | wrong value | mis-buckets a course into "must take" vs "candidate", which changes the plan under test |

Mitigations already in the repository: the rule was validated on a 6-case decision table **before** the catalogue
figure was quoted; the catalogue-level 4,757 is explicitly labelled *offer-set density*, **not** a violation of I1
(`invariants.md` I1 "Limit"); the plan-level check is the one that counts, and it is run on a committed
illustrative plan so it is falsifiable from the repository alone.

### 7.2 What breaks the grab-order claim

The claim: *the order to register in can be ranked from remaining seats plus semester-only availability.*

| Field | If it is wrong | Effect |
| --- | --- | --- |
| **已选 `enrolled`, 限选 `capacity`** | stale by even one capture | the ranking is wrong; a full section looks open (A1's "the system cannot know by itself that the data is stale") |
| **`capacity = 0` sentinel** | read as "full" or as "unlimited" | the order is wrong in two opposite ways |
| **开课学期 `semester`** | unknown (6 of 14 planned courses) | a spring-only course is ranked as if it could be deferred, or an autumn-only one is not prioritised |

**This is the weakest half of the deliverable, and the repository says so on its face:** the committed snapshot is
captured **after** the registration window closed, so the grab-order claim **cannot be validated at all** against
the committed evidence. The only honest status of that claim is "the inputs and the ranking script are committed;
the ranking was not re-checked against a live system". `model-walkthrough.md` "what the walkthrough did not settle"
says the same thing: the ordering rule is deliberately left to A3/A4 rather than specified now.

### 7.3 How this document exposes rather than hides the weakness

- **Unknown is a first-class value.** Missing capacity is reported as "unknown", never as unlimited, never as full;
  the sentinel bucket is printed **separately** from the violation bucket so it cannot be laundered into a headline.
- **Every finding carries source + capture time + hash.** A stale conclusion is visible as a stale timestamp, not
  as a wrong number.
- **Limits are written next to the claims.** `invariants.md` I1 (4757 is not a violation), I2 (floors only — the
  ceiling is left unimplemented rather than invented), I3 ("cannot be determined" ≠ "none exists").
- **Negative results stay in.** The coverage gap (197/130), the 12 parse failures, the expired snapshot, the
  overturned AI claims — all committed.
- **Provenance hygiene defects are recorded** (§3.5), including the stale `.sha256` filenames and the missing
  provenance note for the 2026-27 captures.
- **Deletion is executable** (§5) rather than promised, and §5 step 4 states its own expected non-zero hits instead
  of pretending the repository is clean.

### 7.4 The single weakest conclusion in this document (stated plainly)

The weakest statement here is **"0 real over-capacity violations"** in §3.2. It is true *of the frozen snapshot*
and it is arithmetically checked, but it is the most fragile claim in the document: the same school produced
**422/420** in an earlier crawl (A1), the sentinel bucket holds 40 rows whose capacity is unknown, and the snapshot
is post-window so it cannot be refreshed to settle the question. "0 violations" is therefore a statement about
**one capture of a field that is frequently left blank**, not a statement about the university's behaviour. Anyone
reading it as "the school does not oversell sections" would be reading a governance limit as a fact — which is
precisely the error this section exists to prevent.

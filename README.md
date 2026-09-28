# ISE-A1 — Evidence Brief: course-plan conflicts and the order to grab seats

Submission for **ISE-A1 (Problem and Stakeholder Evidence Brief)**, course *Intelligent Software Engineering*,
platform <https://learn.spaiq.ai>. Deadline **2026-09-28 16:30 (Asia/Shanghai)**.

**Submission tag: `a1-v2`** (see *How to cite this revision* at the bottom). All commands below are relative to
this repository root.

---

## The claim

Planning one semester of UCAS graduate courses cannot be done from any single source, and it is not only a
conflict-checking problem.

- **Two official sources disagree.** For autumn 2026 the public course listing carries **282 course codes**; the
  official course-planning workbook lists **234 courses that open in autumn**. Only **223 are in both** — the public
  listing has **59** the workbook never shows, the workbook has **11** the listing does not.
- **The workbook cannot answer "when".** Of the **732** Yuquanlu records in the workbook import, **0** carry a
  teaching-week value and **0** carry a weekday/period value. Those must be read course-by-course from the listing.
- **A clash needs three conditions at once** (same weekday ∩ overlapping periods ∩ overlapping weeks). Screening on
  weekday + period alone both over-reports and under-reports.
- **The pressure is real and measurable.** For the author's own plan, 4 of 8 sections of the New Era course sit at
  265/265, the Dialectics of Nature sections are at or over capacity (422/420 …), and the Academic Ethics
  Sub-track code is offered in autumn only.
- **Both attempts failed.** Three of the 14 courses in the author's hand-made plan land in the same slot (Thursday
  periods 10–12), and the AI-generated version misread teaching weeks, producing a wrong recommendation.
- **Baseline ~30 minutes** for one manual pass (author's stopwatch); target **under 5 minutes**.

See `doc/assignments/` for the brief itself and `doc/evidence-ledger.md` for claim → source → method → file.

## Read this first

| File | What it is |
| --- | --- |
| `doc/assignments/A1-brief-zh-2026-09-28.pdf` | 简报（中文提交件）— the brief, Chinese |
| `doc/assignments/A1-brief-en-2026-09-28.pdf` | The brief, English |
| `doc/assignments/A1-summary-en-2026-09-28.md` | The 150–300 word summary posted on the platform (word count enforced by `scripts/count_words.py`) |
| `ai/ai-use-log.md` | AI-use log: accepted advice, rejected advice, and how each claim was independently verified |
| `ai/search-log.md` | Search record behind the "no tool covers this" claim, including the channel that failed |
| `doc/evidence-ledger.md` | Every number in the brief traced to a source, method, date and file |
| `doc/archive/` | Superseded first English draft and first summary (kept, not submitted) |

## Repository layout

```
.
├── README.md
├── doc/                          documentation
│   ├── assignments/              ★ the submitted brief (zh + en) and the platform summary
│   ├── evidence-ledger.md        claim -> source -> method -> file
│   ├── data-authority.md         which source is authoritative for which field
│   ├── priority-rules.md         the two orders: plan order vs grab order
│   ├── selection-design.md       the four-step selection design
│   ├── system-and-pain-points.zh.md
│   ├── prototype-issues.md       defects met while building the prototype (partly auto-generated)
│   └── archive/                  superseded versions
├── data/                         data, one folder per source
│   ├── s1-plan-workbook/         S1: official course-planning workbook import (+ sha256, provenance)
│   ├── s2-public-listing/        S2: public course listing import, 2026-27 autumn + spring + 6 past terms
│   ├── s3-my-plan-versions/      S3: evidence record for the author's two saved plan versions
│   ├── s5-programme/             S5: programme credit requirements
│   ├── derived/                  derived data: course-library snapshot, SEP aux fields, join / credit-gap / priority summaries
│   └── private/                  git-ignored: per-course personal priority detail, personal credit gap
├── ai/                           ai-use-log.md, search-log.md
├── scripts/                      every script that fetches, freezes, joins, ranks or checks
└── prototype/                    launcher for the local prototype (the HTML itself is git-ignored: it embeds the personal plan)
```

## Where the data comes from (S1–S6)

| ID | Source | Type | Comes from | Lives in |
| --- | --- | --- | --- | --- |
| S1 | Official *course-planning workbook* (2026-08-28) | official file | issued by the university | `data/s1-plan-workbook/` |
| S2 | Public course listing, jwba.ucas.ac.cn | official online system | crawled and frozen 2026-09-27 | `data/s2-public-listing/` |
| S3 | The author's two saved plan versions (09-05, 09-15) | own working record | manual export; **the .xlsx files are private and not committed** | `data/s3-my-plan-versions/plan-versions.md` |
| S4 | The AI-generated plan (2026-08-28) | derived from S1 | — (used only as a failure case, not as a source) | `ai/ai-use-log.md`, `doc/prototype-issues.md` |
| S5 | Programme requirements, 校发培养字〔2025〕92号 | official file | issued by the university | `data/s5-programme/degree-requirements.json` |
| S6 | School notice on autumn course selection | official file | issued by the university | cited in `doc/assignments/` and `doc/evidence-ledger.md` |

Independence, stated honestly: **official publications (S1, S2, S5, S6)** are one type, **the author's own working
record (S3)** is the other. S4 is derived from S1 and is therefore *not* counted as an independent source.

## Reproduce

```bash
python3 scripts/freeze_snapshot.py        # S1 import  -> data/s1-plan-workbook/sections-snapshot.json (+ sha256)
python3 scripts/fetch_official_db.py --terms 89576,89577 --campus 20   # S2 import (network)
python3 scripts/fetch_public_listing.py   # course-library snapshot (network)
python3 scripts/freeze_aux_fields.py      # SEP auxiliary fields
python3 scripts/inspect_plan_versions.py  # two plan versions -> data/s3-my-plan-versions/plan-versions.md
python3 scripts/rank_plan_priority.py     # plan order + grab order
python3 scripts/credit_gap.py             # credit gap against the programme
python3 scripts/count_words.py            # enforces the 150–300 word summary
python3 scripts/build_web_prototype.py    # rebuilds the prototype (output is git-ignored)
```

Frozen inputs carry a sibling `.sha256` file. Offline scripts (the ones that do not fetch) re-run without network.

## Deliberately not in this repository

Personal data and anything re-fetchable:

- the author's student ID, name and the personal plan spreadsheets (`*.xlsx` are git-ignored);
- any other student's selection record — the project never reads one;
- per-course personal priority detail and the personal credit-gap file (`data/private/` is git-ignored);
- the prototype HTML (it embeds the personal plan; the generator is committed instead);
- the raw HTML cache from the listing crawl, and uncommitted bulk downloads (`data/s2-public-listing/cache/`);
- no credentials, tokens or cookies anywhere in the history.

## Negative results kept on purpose

The assignment requires failed runs and evidence that challenges the claim, so these stay:

- the AI plan version's week-range misreading, and its wrong recommendation (S4);
- the overturned premise "no existing tool does this" — three UCAS course planners were found; the closest already
  does week-level clash detection, so the claim was narrowed to what it does *not* cover (`ai/search-log.md`);
- the failing search channel (Bing returned dictionary pages) — recorded as a channel failure, not as evidence of
  absence;
- the planner's own four import-defect messages, which independently corroborate the "0 of 732" finding;
- boundary cases that the tool cannot settle: uncovered courses (59 / 11), blank capacity cells (unknown, never
  "unlimited"), over-capacity values (422/420), stale snapshots, half-semester courses sharing one slot.

## How to cite this revision

- Tag **`a1-v2`** marks the state submitted for A1 (an earlier `a1-v1` tag is kept in the history).
- The Chinese brief in `doc/assignments/` is the master; the English file is a translation of it. If the Chinese
  text changes after submission day, re-translate — do not let the two drift apart.

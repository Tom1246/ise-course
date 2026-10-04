# Intelligent Software Engineering — coursework repository

Course **Intelligent Software Engineering**, UCAS, 2026 autumn term. Platform <https://learn.spaiq.ai>.
**Repository: <https://github.com/Tom1246/ise-course>**

**Author:** 汤力为 (Liwei Tang), student ID **2026E8001082052** — University of Chinese Academy of Sciences.

This repository carries the assignments for this course. Each assignment gets its own folder under
`doc/assignments/<id>/` and its own tag. All of them share one discipline, because the course grades the
evidence behind a result as much as the result itself:

- every number is produced by a script that is committed next to it, and can be re-run;
- raw outputs, frozen inputs and their hashes are committed;
- **negative results stay in** — failed runs, overturned claims, dead ends, boundary cases the tool cannot settle;
- no personal data, no credentials, nothing that identifies anyone else.

## Assignments

| # | Assignment | Due (course schedule) | Status | Artifacts | Tag |
| --- | --- | --- | --- | --- | --- |
| **A1** | Problem and Stakeholder Evidence Brief | 2026-09-28 | **submitted** | [`doc/assignments/a1/`](doc/assignments/a1/) — brief (zh + en), platform summary | `a1-v2` |
| A2 | not released yet | 2026-10-12 | not started | — | — |
| A3 | not released yet | 2026-10-26 | not started | — | — |
| A4 | not released yet | 2026-11-09 | not started | — | — |
| A5 | not released yet | 2026-11-23 | not started | — | — |
| A6 | Reliability and Observability Evidence Lab *(title from the released file; brief not worked on yet)* | 2026-12-07 | not started | — | — |

---

# A1 — Problem and Stakeholder Evidence Brief

**Submitted 2026-09-28** (tag `a1-v2`). Topic: planning one semester of graduate courses — conflict
checking plus the order to grab seats in.

## The claim

Planning one semester cannot be done from any single source, and it is not only a conflict-checking problem.

- **Two official sources disagree.** For autumn 2026 the public course listing carries **282 course codes**; the
  official course-planning workbook lists **234 courses that open in autumn**. Only **223 are in both** — the public
  listing has **59** the workbook never shows, the workbook has **11** the listing does not.
- **The workbook cannot answer "when".** Of the **732** Yuquanlu records in the workbook import, **0** carry a
  teaching-week value and **0** carry a weekday/period value. Those must be read course-by-course from the listing.
- **A clash needs three conditions at once** (same weekday ∩ overlapping periods ∩ overlapping weeks). Screening on
  weekday + period alone both over-reports and under-reports.
- **The pressure is real and measurable.** In the author's own plan, 4 of 8 sections of the New Era course sit at
  265/265, the Dialectics of Nature sections are at or over capacity (422/420 …), and the Academic Ethics
  Sub-track code is offered in autumn only.
- **Both attempts failed.** Three of the 14 courses in the hand-made plan land in the same slot (Thursday periods
  10–12), and the AI-generated version misread teaching weeks, producing a wrong recommendation.
- **Baseline ~30 minutes** for one manual pass (author's stopwatch); target **under 5 minutes**.

## Read this first

| File | What it is |
| --- | --- |
| `doc/assignments/a1/A1-brief-zh-2026-09-28.pdf` | 简报（中文提交件） |
| `doc/assignments/a1/A1-brief-en-2026-09-28.pdf` | The brief, English |
| `doc/assignments/a1/A1-summary-en-2026-09-28.md` | The 150–300 word summary posted on the platform (count enforced by `scripts/count_words.py`) |
| `ai/ai-use-log.md` | AI-use log: accepted advice, rejected advice, and how each claim was independently verified |
| `ai/search-log.md` | Search record behind the "no tool covers this" claim, including the channel that failed |
| `doc/evidence-ledger.md` | Every number in the brief traced to a source, method, date and file |
| `doc/archive/` | Superseded drafts (first English draft, first summary, first A1 PDFs) |

## Negative results kept on purpose (A1)

- the AI plan version's week-range misreading, and the wrong recommendation it produced;
- the overturned premise "no existing tool does this" — three UCAS course planners were found; the closest already
  does week-level clash detection, so the claim was narrowed to what it does *not* cover (`ai/search-log.md`);
- the failing search channel (Bing returned dictionary pages) — recorded as a channel failure, not as evidence of
  absence;
- the planner's own four import-defect messages, which independently corroborate the "0 of 732" finding;
- boundary cases the tool cannot settle: uncovered courses (59 / 11), blank capacity cells (unknown, never
  "unlimited"), over-capacity values (422/420), stale snapshots, half-semester courses sharing one slot.

---

## Repository layout

```
.
├── README.md
├── doc/                          documentation
│   ├── assignments/a1/           ★ A1 submission: brief (zh + en) and the platform summary
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
| S6 | School notice on autumn course selection | official file | issued by the university | cited in the A1 brief and `doc/evidence-ledger.md` |

Independence, stated honestly: **official publications (S1, S2, S5, S6)** are one type, **the author's own working
record (S3)** is the other. S4 is derived from S1 and is therefore *not* counted as an independent source.

## Requirements and setup

**Python 3.11+** (developed on 3.11.1). Only three third-party packages are needed, and only by three of the scripts:

```bash
git clone https://github.com/Tom1246/ise-course.git
cd ise-course
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt        # beautifulsoup4 (HTML parsing), certifi (CA bundle), openpyxl (Excel)
```

Everything else is the standard library. **No credentials are needed for the offline steps** — the frozen inputs
are already committed under `data/`, each with its own `.sha256` and provenance note. The two network scripts
(`fetch_official_db.py`, `fetch_public_listing.py`) read public pages only and re-freeze the inputs; re-running them
may change hashes and is not required to check the results.

Quick sanity check that the checkout works:

```bash
python3 scripts/count_words.py          # prints the platform summary word count (150-300)
```

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

Frozen inputs carry a sibling `.sha256` file. The offline scripts re-run without network.

## Deliberately not in this repository

Personal data and anything re-fetchable:

- the author's student ID, name, programme code and the personal plan spreadsheets (`*.xlsx` are git-ignored);
- any other student's selection record — the project never reads one;
- per-course personal priority detail and the personal credit-gap file (`data/private/` is git-ignored);
- the prototype HTML (it embeds the personal plan; the generator is committed instead);
- the raw HTML cache from the listing crawl and uncommitted bulk downloads (`data/s2-public-listing/cache/`);
- no credentials, tokens or cookies anywhere in the history.

## Tags and how to cite

Every assignment is tagged when submitted: **A1 → `a1-v2`** (an earlier `a1-v1` tag is kept in the history).
The Chinese brief under `doc/assignments/a1/` is the master for A1; the English file is its translation — if the
Chinese text changes, re-translate rather than letting the two drift apart.

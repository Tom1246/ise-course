# A3 — Repository Investigation and Reproducible Build

- **Release** 2026-10-19 16:30 · **Deadline** 2026-10-26 16:30 (Asia/Shanghai) · **Platform** <https://learn.spaiq.ai>
- **Status:** artifacts built ahead of the release window; the platform record is submitted inside the window.
- **Tag:** `a3-v1`. Earlier assignments keep their own tags (`a1-v2`, `a2-v1`) and are not touched by A3 work.

Objective: understand an **unfamiliar** repository through execution evidence and establish a **safe change
boundary**.

## The repository under investigation

**`HMBlankcat/UCAS-course-planner`** — a local-first course-planning web app for UCAS graduate students:
course search, credit progress, week-level conflict detection, JSON plan backup. MIT licensed, TypeScript,
2.7 MB. Frozen at commit **`68e7080503084a41f42db6e0e9ff94c0e9ef2f19`** (`ver 1.4`, 2026-09-01).

It was chosen because it is genuinely unfamiliar (only its README had been read, in A1), because it sits in the
same domain as this project (so the end-to-end path "plan in → conflict verdict out" exists naturally), and
because its MIT licence leaves A4 free to build on it. The repository itself is **not committed here** — only
its identity, the evidence produced by running it, and the maps drawn from it.

## Deliverables mapped to files

| A3 deliverable | File(s) here | State |
| --- | --- | --- |
| Stable commit/tag + repository URL | this file + `reproduction-guide.md` §1 | done |
| Reproduction guide and environment lock | `reproduction-guide.md` (+ the environment trap it documents) | done |
| Raw execution evidence | `evidence/logs/01..08` + `evidence/e2e-*.png` | done |
| Architecture / call-path map | `architecture-map.md`; `figs/a3-modules.dot/.png`, `figs/a3-call-path.dot/.png`, `figs/render.sh` | done |
| End-to-end path (facts vs inference) | `end-to-end-path.md` (with a negative control) | done |
| Risk register | `risk-register.md` (5 risks, each with file/line evidence) | done |
| ADR comparing two responses to one risk | `adr-001-change-boundary.md` | done |
| Platform summary (150–300 words) | `A3-summary-en-2026-10-05.md` (count checked by `scripts/count_words.py`) | done |
| Notebook | `notebooks/a3-reproduction-verification.ipynb` (executed; re-checks every claim in these documents) | done |
| Reading copy of everything above | `A3-report-en-2026-10-05.md` + `.pdf` | done |

## What running it actually showed

1. **The first build failed, and the repository was not to blame.** This machine's npm config sets `omit=dev`,
   so `npm install` silently skipped a devDependency that `vite.config.ts` imports; the build then died with
   `ERR_MODULE_NOT_FOUND`. `npm ci --include=dev` (from the pristine lockfile) fixed it: 560 packages, build
   green. The trap — and how to detect it — is the centrepiece of the reproduction guide.
2. **The application is one file.** `app/page.tsx`: 1,879 lines / 63 KB carrying state, business rules and UI;
   `components/` holds 60 UI primitives and **zero** application components; there is **no test script** and
   `oxlint` covers 5 files. That is the factual basis of the change-boundary ADR.
3. **The toolchain is a beta plus a platform plugin** (`vinext 1.0.0-beta.5`, `@openai/sites-vite-plugin`), and
   the platform manifest is scaffolded (`{"d1": null, "r2": null}`) — present in code, disabled in data.
4. **The conflict rule is the same three-condition rule as A2's decision table** — `same day ∧ weeks intersect ∧
   periods intersect` at `app/page.tsx:447`, with a self-comparison guard at `:464`. Two independent
   implementations agreeing is the strongest consistency evidence this project has produced so far.
5. **The end-to-end path was executed, with a control.** Three courses sharing 周四 10-12 produce
   「3 处时间冲突」 and three highlighted cells; a plan without a shared slot produces 「无时间冲突」 and none.

Regenerate the evidence-bearing parts:

```bash
bash doc/assignments/a3/figs/render.sh                                   # diagrams: .dot -> .png
python3 -m nbconvert --to notebook --execute --inplace notebooks/a3-reproduction-verification.ipynb
python3 scripts/count_words.py                                            # 150-300 word rule
```

The reproduction commands for the third-party repository itself (install, build, lint, start, end-to-end) are
in `reproduction-guide.md` §3–§5, each with the log file that shows what actually happened.

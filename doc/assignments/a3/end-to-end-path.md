# A3 — One end-to-end path, reconstructed and executed

The path under test: **a plan goes in, a conflict verdict comes out.**

```
input   a set of selected courses (a plan)
        ↓   written through the app's own persistence contract
app     restore on load → conflict predicate → render
output  the verdict (badge / cell labels / floating card) and the filtered catalogue
```

This is the path A1 asserted existed in this tool; here it is executed, with a **negative control** so the
result cannot be explained by "the label is always there".

## Method (reproducible)

1. Frozen checkout at commit `68e7080`; clean install and production build per `reproduction-guide.md`;
   server running at `http://127.0.0.1:3000` (HTTP 200 in 0.14 s).
2. Drive a headless browser (CDP, no window focus taken) against the running server.
3. Write the plan into **the app's own storage contract** — `localStorage` key
   `ucas-graduate-course-planner-v3`, value `{storageVersion: 1, plan: [<courses exactly as they appear in the
   repository's own courses.json>], degreeCodes: [], englishPlan: {…}, studentType: '未选择',
   selectedDiscipline: ''}` — then **reload**, so the app restores it through its own code path (L567–586)
   rather than through a test hook that does not exist.
4. Read back what the app rendered: the badge text, the number of `.cell-conflict-label` elements, and a
   screenshot.

Script: `A3/logs/08-e2e.log` contains the run; the raw log is committed at `evidence/logs/08-e2e.log` and the
screenshots at `evidence/e2e-positive.png` / `evidence/e2e-negative.png`.

Input rows (taken from the repository's own `public/data/courses.json`, 玉泉路 campus, all three at
**周四 10-12**):

| code | course | slot in that file | credits |
| --- | --- | --- | --- |
| `180081070100PX001Y` | 计算机代数在科学与工程中的应用 | 周四(10-12), 第2-18周 | 1.0 |
| `180206085406P3002Y` | 深度学习方法与应用 | 周四(10-12), 第2-4,6-15周 | 2.0 |
| `180093081002P3008Y` | 数字图像处理与分析 | 周四(10-12), 第2-19周 | 2.5 |

## Result (fact)

| Case | Input | Badge rendered | `.cell-conflict-label` count | Screenshot |
| --- | --- | --- | --- | --- |
| **positive** | the three courses above | **`3 处时间冲突`** | **3** | `evidence/e2e-positive.png` |
| **negative control** | `180081070100PX001Y` + `180070200P1001Y` 高等量子力学 (no shared slot) | **`无时间冲突`** | **0** | `evidence/e2e-negative.png` |

The positive screenshot shows the Thursday period-10 row carrying a red **「冲突」** badge and three red-bordered
course cards, each annotated 「与其他课程冲突」 — i.e. the app imputes the clash to every course in the shared
slot, not just to one of them.

## Facts (each traceable)

1. The build, the clean install, the server start and the two page loads all succeeded — `evidence/logs/04`,
   `05`, `07`, `08`.
2. The app reports **3** clashes for three courses in one slot, and **0** for a plan without a shared slot
   (control) — `evidence/logs/08-e2e.log`.
3. The credits the app shows for those courses (1.0 / 2.0 / 2.5) **agree exactly** with the independent
   snapshot this project froze in A1/A2 (`data/derived/course-library-snapshot.json`) — cross-source agreement on
   the same three codes.
4. The comparison is week-level, implemented as `same day ∧ intersects(weeks) ∧ intersects(periods)` at
   `app/page.tsx:447`; `conflictsWithPlan` (L464) excludes self-comparison.
5. The plan is restored only when `storageVersion === 1` (L578); otherwise the app resets it silently (L587–600).

## Inference (marked as such, with its basis)

1. **The verdict is computed client-side, not by a server.** *Basis:* the only server interaction is the static
   asset fetch (L563); no API route exists. *Confidence:* high, from reading; not proven by a network trace.
2. **The tool's week-level result would match an A2-style check on the same data.** *Basis:* the predicate is
   the same three-condition rule as A2's decision table, and the run's verdict matches the expectation computed
   independently in A2 for the same three courses (3 pairs). *Confidence:* high for this input, not proven for
   all inputs — no differential test was run over the whole catalogue.
3. **A user who edits the timetable would see the same path re-run.** *Basis:* the same `useMemo` inputs drive
   the badge, the cells and the filter. *Confidence:* medium — not exercised interactively; this run went
   through storage restore only.

## What this run does *not* prove

- It does **not** prove the app is correct in general: 2,077 courses were not cross-checked against an
  independent computation, and only a 玉泉路 case was used.
- It does **not** exercise the interactive path (search → click 加入 → re-render). The restore path and the
  interactive path share the same predicate and memos, but that sharing was established by reading, not by test.
- It says nothing about the app's behaviour when the catalogue is stale relative to the live registration
  system — the risk R3 tracks exactly that gap.

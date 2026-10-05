# ADR-001 — Establishing a safe change boundary: two responses

- **Status:** Accepted
- **Date:** 2026-10-05
- **Deciders:** A3 investigation (author)
- **Subject repository:** third-party `UCAS-course-planner`, commit `68e7080503084a41f42db6e0e9ff94c0e9ef2f19` (`ver 1.4`, 2026-09-01), investigated read-only
- **Risk addressed:** **R2** in `doc/assignments/a3/risk-register.md` — *"One 1879-line component carries all logic; no safe change boundary"*
- **Required by:** A3 brief requirement 5, *"Identify three risks; compare two responses to one in an ADR"* (`课程材料/ISE-A3_Repository_Investigation_and_Reproducible_Build_English.md` line 19), with deliverable *"ADR and execution evidence"* (line 27) and objective *"establish a safe change boundary"* (line 11).

---

## 1. Context and constraints

The application's entire domain logic — week/period parsing, conflict detection, degree/credit rules, persistence, and every UI branch — lives in a single client component. The frozen checkout measures `app/page.tsx` at **1879 lines / 63 419 B**, while the only supporting files are `lib/utils.ts` (**169 B / 6 lines**, just the shadcn `cn()` helper) and `hooks/use-mobile.ts` (**585 B / 21 lines**). `app/page.tsx:3-21` imports **only** `react` and `lucide-react`; it does not import either of those files (they are referenced only by unused `components/ui/*` scaffolding, e.g. `components/ui/button-group.tsx:5`). The file declares **41 `function`s** — **34 at top level** plus **7 mutation handlers nested inside the component** (`:809`, `:825`, `:835`, `:845`, `:853`, `:864`, `:891`) — including the whole domain core: `parseWeeks` (`:403`), `parsePeriods` (`:416`), `intersects` (`:427`), `hasSlot` (`:438`), `coursesConflict` (`:447`), `conflictsWithPlan` (`:464`), `isCoreCourse` (`:384`), `isProfessionalCourse` (`:388`).

Two hard constraints from the evidence shape this decision:

- **C1 — there is no automated correctness check to lean on.** `package.json:8-14` defines `dev / build / start / lint / format` and **no `test` script**. The linter inspects only **5 files** (`06-lint.log:10`: `Finished in 2.6s on 5 files with 208 rules using 8 threads.`) and reports the monolith clean (`06-lint.log:9`: `Found 0 warnings and 0 errors.`), which carries no information about behaviour. The only recorded end-to-end check is a manual `localStorage` injection followed by a re-render (`08-e2e.log:3`), and it needs the full build + a live server.
- **C2 — every verification run is expensive and platform-bound.** A `build` costs `real 0m15.526s` (`05-build.log:53`) *after* neutralising the host `omit=dev` trap and restoring the frozen lock (`04-npm-ci.log:4-5`), because the build chain is coupled to a hosting vendor (R1: `vite.config.ts:1,5,52-58`). A unit-level check would need neither the vendor chain nor a server.

The follow-on assignment (A4) requires making a **bounded change to this codebase** — "cutting one slice". The decision below must therefore be defensible not only for a one-off fix but for a change that will be reviewed, and for the case where the change is later extended or reverted.

Because the repository is third-party and read-only for A3, this ADR **selects a boundary for a future change** (A4); it does not itself modify `UCAS-course-planner`. The two options differ in *where* the change is made and *what can verify it*, not in feature scope.

---

## 2. Options

### Option A — Patch inside the monolith (minimal diff)

Make the change directly in `app/page.tsx`, editing the relevant functions in place; add no new files and no test harness.

**Benefits**
- **Smallest possible diff and no new API surface.** The functions already sit at module scope sharing existing helpers (`coursesConflict` at `:447` is already called from two places, `:468` and `:665`), so a targeted edit is local.
- **No new maintenance surface.** It introduces no `lib/` module, no build/test tooling, and no import boundary the repo must then keep consistent — relevant because the repo has **no CI** (`.github/` holds only `ISSUE_TEMPLATE/*`) to enforce consistency automatically.
- **Fastest to land.** Nothing has to be installed or configured; the existing `npm run dev / build` path already works (`05-build.log:56 EXIT=0`).
- **Right answer if the change is genuinely one-off and short-lived** (e.g. a text/label fix, or a probe that will be reverted): extraction would be pure overhead.

**Costs**
- **Unverifiable.** After the edit there is still no `test` script and no per-rule check; correctness rests on a manual `localStorage` E2E run that requires the whole platform build chain (C1, C2). A regression in `coursesConflict` would surface only as a wrong conflict badge in a live browser.
- **It re-creates the risk it is supposed to answer.** R2's finding is precisely that no boundary exists; editing in place entrenches it, and a second caller cannot exercise the changed rule in isolation.
- **Review cost scales with file size.** Reviewers must hold a 1879-line/63 KB file plus 21 `useState` and 14 `useMemo` sites in mind to judge a diff that touches a shared domain function (`useState` 21, `useMemo` 14, `冲突` 9, `学位课` 19 occurrences / 17 lines over `app/page.tsx`).

### Option B — Extract a pure, independently testable logic layer

Move the **pure, DOM-free** rules out of `app/page.tsx` into `lib/` (conflict judgement: `parseWeeks`, `parsePeriods`, `intersects`, `hasSlot`, `coursesConflict`, `conflictsWithPlan`; degree/credit judgement: `creditFromValue`, `isCoreCourse`, `isProfessionalCourse`, `matchesDiscipline` and the credit predicates), add a minimal test for them, and have the page **import and call** them. The page keeps all React state and rendering.

**Benefits**
- **Creates the missing verification seam.** A pure function can be checked without React, without the vendor build chain, and without a server — directly resolving C1/C2. This is the only option that can *demonstrate* the changed rule is correct rather than hope it is.
- **Answers the A3 objective literally.** A3 line 11 asks to *"establish a safe change boundary"*; B produces one, so the A4 slice lands on a narrow, testable surface instead of inside the monolith. A reviewer of A4 can see the diff at function granularity plus a passing test.
- **Cheap to do here because the functions are already pure leaves.** The chosen functions take only data (`Course`, `Set<number>`, string) and return booleans/numbers — no hooks, no JSX, no `window` — so the move is mostly cut-and-paste plus an `export`, which is why the extraction is bounded and low-risk rather than a rewrite.
- **Blast radius of a *wrong* extraction is caught immediately** by the test, before the page is touched.

**Costs**
- **New surface and new tooling.** It adds `lib/*.ts` plus a test file, and the repo currently has **no test runner at all** (`package.json:8-14`) — so a minimal runner must be added and justified, and it becomes something the repo must maintain even though there is no CI to run it.
- **A visible, reviewable diff instead of a hidden one.** The change to `app/page.tsx` is larger in line count (it now imports and delegates) even though each function's body is unchanged.
- **Up-front effort for a possibly tiny change.** If the A4 slice turns out to be UI-only (e.g. relabelling a status string near `app/page.tsx:1165-1168`), the seam is never used and the effort is wasted.
- **Must not touch persistence.** Any extraction that reaches into the `localStorage` read/write path (`:567, 621`) risks colliding with R4's silent-reset behaviour, so the extraction must be strictly limited to pure rules.

---

## 3. Decision

**Choose Option B**, with a deliberately bounded scope: extract **only the pure, DOM-free rule functions** listed above, add **one minimal test** that exercises `coursesConflict` / `conflictsWithPlan` against a positive and a negative case, and leave **all** React state, effects, rendering, and persistence exactly where they are.

Reasons, and why this holds under A4's "cut one slice":

1. **The decision must be defensible to a reviewer, and only B produces verifiable evidence.** C1 shows the repo has no test script and a linter that sees 5 files and already passes on the monolith. Under A the claim "the change is correct" is unfalsifiable except by a full platform build plus a manual browser check; under B it is backed by a green test that needs neither. A3's rubric weights *"Execution, artifact quality, and reproducibility"* (1.50) and *"Analysis, counterexample, and limits"* (1.25) above convenience (`ISE-A3…English.md` lines 43-44), and the brief demands *"Establish a safe change boundary"* (line 11) — A reproduces the condition R2 names; B removes it.
2. **The A4 slice lands on the boundary, not on the monolith.** Whatever slice A4 cuts, a reviewer/automation can act on it at function granularity, and the pure-rule test stays green as a guard against regressions in conflict/credit behaviour — the exact logic A1 identified as the place prior errors occurred (`A1-brief-en-2026-09-28.md:60`: the three courses all in *"Thursday, periods 10–12"*; `:201-207` the rejected advice to stop cross-checking conflict inputs).
3. **The dominant benefit is realised even if the slice is small, because the seam is permanently cheaper than the E2E alternative.** Every future conflict/credit check stops costing a `~15.5 s` build plus a server (`05-build.log:53`, `07-start.log:12`).
4. **B is bounded and reversible for a concrete reason, not optimism:** the target functions are already pure leaves with a single existing call pattern (`coursesConflict` already called from `:468` and `:665`), so the extraction does not entangle state — which is what makes the cost estimate credible rather than a rewrite in disguise.

**Explicitly rejected scoping that B must NOT be interpreted as authorising:** extracting hooks, effects, or the persistence path (that would collide with R4), or "refactoring the page" wholesale — the decision is narrow.

---

## 4. Cost of the rejected option (Option A)

Option A is not wrong in general; it is wrong **here**. Its real costs, stated honestly, are:

- **It cannot produce the evidence A3/A4 are graded on.** With no `test` script and a linter that inspects 5 files and already passes on the untested monolith, an in-place patch leaves the correctness claim resting on a manual `localStorage` render (`08-e2e.log:3`) that requires the coupled vendor build chain (R1).
- **It converts a one-time fix into a permanent constraint.** A future caller cannot test the changed rule in isolation, so every subsequent change to conflict/credit logic pays the same verification tax — the reasoning that makes the *first* in-place edit cheap is exactly what makes the *next* one expensive.
- **What A buys (no new files, no new tooling) is real and partially offsets B's cost.** If the A4 slice were confirmed to be UI-text-only, A would win on effort; the decision therefore also records when to prefer it (see §6).

No option here is free: A pays in unverifiability and entrenched risk; B pays in added tooling and a wider (if shallow) diff.

---

## 5. Rollback

Option B is rolled back in **one commit** with **no data-path change**, because the extraction does not touch state or persistence:

1. Re-inline the extracted functions into `app/page.tsx` (their bodies are unchanged from the pre-extraction versions in the frozen checkout at `:403-470` and `:384-401`), restoring the original imports.
2. Delete `lib/<extracted>.ts` and the added test file; remove the temporary test runner added to `package.json:8-14`.
3. Re-run `npm run build` + `npm run lint` — expected `EXIT=0` and `Found 0 warnings and 0 errors.` (`05-build.log:56`, `06-lint.log:9`), i.e. back to the frozen baseline.

Because the plan/persistence contract (`app/page.tsx:112, 567-631`) is untouched, a rollback **cannot** trigger R4's silent reset for any user. That is a deliberate property of the chosen scope, not a side effect.

---

## 6. Revisit trigger

Reopen this decision if **any** of the following becomes true:

- **The slice requires state, effects, or persistence, not pure rules.** If A4's change touches `useState`/`useEffect` (21/3 occurrences) or the `localStorage` path (`:112,567,621`), the bounded extraction no longer applies and Option A (or a different decomposition) must be re-evaluated — the seam would otherwise be a fiction.
- **The extraction touches the persistence contract at all.** That is a R4 hazard; stop and split the change.
- **The A4 slice is confirmed UI-only** (e.g. a label near `:1165-1168`), in which case the pure-rule seam is unused and A is the cheaper correct answer.
- **The repository gains a test runner and CI such that in-place edits become independently verifiable.** Then A's principal cost disappears and the balance may shift; note the repo currently has no CI (`.github/` contains only `ISSUE_TEMPLATE/*`).
- **A host/build-portability change (R1) or a data-freshness change (R3) is the actual slice**, since neither is answerable by this seam and each needs its own decision record.

---

## Traceability

| Statement | Source |
| --- | --- |
| R2 as stated | `doc/assignments/a3/risk-register.md`, R2 |
| A3 objective / requirement 5 / rubric weighting | `课程材料/ISE-A3_Repository_Investigation_and_Reproducible_Build_English.md` lines 11, 19, 27, 43-44 |
| Monolith size, imports, function inventory | `app/page.tsx` (1879 lines / 63 419 B); `:3-21, 208, 384, 388, 403, 416, 427, 438, 447, 464, 468, 665` |
| Supporting-file sizes; unused by the page | `lib/utils.ts` (169 B); `hooks/use-mobile.ts` (585 B); `components/ui/button-group.tsx:5` |
| No test script; scripts list | `package.json:8-14` |
| Lint reach | `06-lint.log:9-10` |
| E2E method | `08-e2e.log:3` |
| Build cost / success | `05-build.log:53, 56`; `07-start.log:12` |
| Host `omit=dev` trap and lock restore | `04-npm-ci.log:4-5` |
| Vendor coupling (R1) | `vite.config.ts:1, 5, 52-58` |
| Persistence contract and reset path (R4) | `app/page.tsx:112, 567, 578, 587-600, 619-631` |
| Prior conflict-error precedent | `doc/assignments/a1/A1-brief-en-2026-09-28.md:60, 201-207` |
| No CI | `.github/ISSUE_TEMPLATE/*` (only files present) |

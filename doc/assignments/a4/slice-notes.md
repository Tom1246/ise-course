# A4 — Slice notes (implementation, mapped to the five requirements, with what is deferred)

Note on revisions: this document describes the slice as it was **peer-reviewed**. The revision that followed
(commit `731bc66`) changed how a places figure may be published and moved "unknown" to the end of the order;
where the text below describes the earlier behaviour, `review/response.md` is authoritative.

**Slice:** `a4-slice-v1` · branch `a4-slice` @ `7e17a21` (base `68e7080`) · repository `HMBlankcat/UCAS-course-planner`
**Companions:** `task-contract.md` (the promise), `edge-cases.md` (boundary behaviour, §-referenced below),
`rollback.md` (rollback), `evidence/logs/01..08` + `evidence/*.png` (raw proof).
All counts and line numbers in this file were read off the repository (`git show --stat 7e17a21`,
`git diff 68e7080 7e17a21`) or produced by a command I ran; none are estimated.

---

## 1. The slice is traceable to a stated requirement (requirement ①)

Every part of the change answers a line that already existed before this slice. There is no invented feature.

| What the slice does | Where the requirement comes from |
| --- | --- |
| Produces **one ordered list** ("register for X first") | A1 pain point 1 — *"I had not fixed the order to register in in advance"* (`task-contract.md:15`, quoting `A1-brief-…:87`) |
| Ranks by **capacity risk first** (full / few left) | A1 pain point 3 — required courses run in autumn only, pressure is heavy, sections fill (`task-contract.md:16`, `A1-brief-…:111`) |
| Fills a **gap the tool was documented as not having** | A1's comparison of the existing tool: "there is no order to register in" (`task-contract.md:17`) |
| **Refuses to order a plan that clashes with itself** | A2's clash definition — a clashing plan must be resolved before it can be judged (`task-contract.md:18`) |
| Maps `capacity === 0` to **unknown, never "full"** | A3 risk register R3 / §6 — the app never reads `capacity`/`selected`; `0` is a "not recorded" sentinel, 99 of 2,077 rows (`task-contract.md:19`) |
| Reports what it **could not** take into account (`caveats`) | Interface contract §4 — `caveats` is "where the slice reports what it could not take into account" (`task-contract.md:69-70`) |

The change boundary itself is traceable: A3's ADR-001 chose option **B** (extract a pure, independently testable
function layer, leave UI/state/persistence alone), and this slice is the first change made under that decision
(`task-contract.md:7-9`). The three honesty rules — no-capacity⇒unknown, `capacity === 0`⇒unknown, self-clash⇒no
order — are written as rules *with a test each* before the code (`task-contract.md:36-40`).

## 2. What the 425 changed lines actually are (requirement ①②④ in numbers)

`git show --stat 7e17a21` → **6 files changed, 425 insertions(+), 0 deletions(-)**:

| File | Lines | New or existing | What it does |
| --- | --- | --- | --- |
| `lib/priority.ts` | **140** | new | The pure ranking core: `Capacity`/`PlanCourse`/`Urgency` types, `placesLeft`, `urgencyOf`, `rankPlan`. No React, no DOM, no storage, no network (`:1-14`). |
| `lib/priority-mapping.ts` | **45** | new | Maps raw course rows onto the slice's input; owns the `capacity === 0`⇒`unknown` sentinel rule (`:25-32`). |
| `tests/priority.test.ts` | **178** | new | 20 unit tests (grouped in §4). The repository had **no test file** before this (base `68e7080`: the only path matching `test` is `components/ui/aspect-ratio.tsx`). |
| `app/page.tsx` | **58** | existing | Import + label map (**11** lines, `:23-33`), the `const priority = useMemo` derivation (**19** lines, `:685-703`), the "抢课顺序建议" panel markup (**28** lines, `:1279-1306`). |
| `tsconfig.json` | **1** | existing | `"allowImportingTsExtensions": true` (`:15`) — required for the tests' `../lib/priority.ts` imports. |
| `.gitignore` | **3** | existing | ignores `*.tsbuildinfo`, produced by any `tsc` run. |

So: **363 lines are genuinely new files** (the pure layer 185 + tests 178); **only 62 lines touch existing
files** (58 in the page, 3 config). The page change is additive only — 0 deletions — which is what makes the
rollback story (`rollback.md`) cheap and criterion 8 (`task-contract.md:83`) true. The behavioural surface of
the slice in the running app is exactly one panel that renders `rankPlan`'s output; it changes no existing
output, no state, and no persistence.

## 3. The five requirements — what is done, what is deferred, and why

The five items are: **UI · server-side authorization · state change · failure feedback · recovery**.

| # | Item | Status | Evidence | Why (if not fully done) |
| --- | --- | --- | --- | --- |
| 1 | **UI** | **Done** | `app/page.tsx:1279-1306`; screenshots `priority-real.png`, `priority-synthetic.png`, `priority-clashing.png`; E2E `05-e2e-priority.log` | — |
| 2 | **Server-side authorization (401/403)** | **Deferred (whole item)** | `task-contract.md:52`: "Deferred by decision (2026-10-05) — the priority is local verification first" | The upstream app is **local-first with no server at all** (A3 §3-4); this would be *new construction*, not a change to existing behaviour. Also out of ADR-001's chosen boundary. The concrete checklist for when it is built is in **`edge-cases.md` §3**. |
| 3 | **State change** | **Deliberately none** | `app/page.tsx:687-703` — `rankPlan` reads `plan`/`degreeCodes`/`conflictCodes` and returns a value; the slice adds **no** `useState`, no storage write, no mutation. The only "state" is React's `useMemo` cache. | Ranking is a *derived read-only view*, so introducing mutable state would be a defect, not a feature. The genuine state question — the `localStorage` contract — is out of scope on purpose (`task-contract.md:55`, A3 R4), because a slice that may be rolled back must not be able to wipe user data. See `edge-cases.md` §2. |
| 4 | **Failure feedback** | **Partially done (as designed)** | The panel states, in the UI: the missing-semester-field limitation (hard-coded `<li>`, `app/page.tsx:1298-1300`), and every `priority.caveats` entry (`:1302-1304`); an empty/no-order state shows a placeholder rather than a blank box (`:1296`); live text: unknown-capacity count, self-clash codes, empty-plan note. Verified end-to-end in all three E2E cases. | There is no *operation* that can fail (no network, no write, no async), so there is no error channel to build — the honest feedback is "what could not be taken into account", which is exactly what §4 of the contract defines `caveats` to be. An error toast would have nothing to report. |
| 5 | **Recovery** | **Done, by construction** | Diff is 425 insertions / **0 deletions**; `localStorage` untouched (no storage line in the diff); criterion 8 `task-contract.md:83`; `rollback.md` | The slice's only failure mode is "the panel is wrong/absent", and its recovery is the ordinary one — revert the commit. Because the change is purely additive and touches no persistence, a revert cannot lose user data. There is no partial-failure state to recover from. |

Net: of the five, **UI and recovery are done; failure feedback is done in the only form this slice can have;
state change is deliberately not introduced; server-side authorization is the one item deliberately deferred as
a whole**, with the reason and the follow-on checklist recorded rather than implied.

## 4. Tests (requirement ④)

**Unit — 20 tests, all passing.** Command: `node --experimental-strip-types --test tests/priority.test.ts`.
Logged in `evidence/logs/02-unit-tests.log` (`# tests 20 / # pass 20 / # fail 0`) and re-run by me at
`7e17a21` from an extracted copy — same 20/20. The 20 tests group into five families:

| Group | Tests | Names (from the runner output) |
| --- | --- | --- |
| **A. places / urgency core (6)** | 1-6 | `placesLeft never guesses` · `urgency: full section is critical` · `urgency: over-subscribed section is critical` · `urgency: required + autumn-only + few places is critical` · `urgency: few places without those flags is high` · `urgency: roomy section is normal` |
| **B. the two missing-data honesty rules (2)** | 7-8 | `missing capacity is reported as unknown, never as safe` · `unknown outranks known-safe (not knowing is not reassurance)` |
| **C. ordering criteria + determinism (4)** | 9-12 | `critical beats high beats normal` · `at the same urgency, required beats elective and autumn-only beats spring-capable` · `fewer places first when everything else ties` · `full tie falls back to code, so output is deterministic` |
| **D. structural guarantees (4)** | 13-16 | `a plan that clashes internally is not given an order for the clashing courses` · `empty plan yields an empty order and says so` · `ranking is a permutation: nothing is lost or duplicated` · `ranks are contiguous starting at 1 for a mixed plan` |
| **E. raw-data mapping (4)** | 17-20 | `mapping: a real capacity pair becomes a known capacity` · `mapping: capacity 0 is a sentinel, not a full section` · `mapping: missing or non-numeric fields become unknown, never a number` · `mapping: flags come through and the row keeps its code/name` |

These cover acceptance criteria 1-5 and 7 (`task-contract.md:76-82`).

**Non-test gates (all green, logged):**

| Gate | Command | Log | Result |
| --- | --- | --- | --- |
| dependency install | `npm ci --include=dev` | `01-npm-ci.log` | 560 packages, `EXIT=0` (note: `--include=dev` is mandatory — the machine's npm sets `omit=dev`; A3 R5) |
| build | `npm run build` (`vinext build`) | `03-build.log` | "Build complete", exit 0 |
| lint | `npm run lint` (`oxlint`) | `06-lint.log` | "Found 0 warnings and 0 errors", 8 files / 208 rules |
| type check | `npx tsc --noEmit` (repo has no script; supplied by us) | `07-typecheck.log` | `tsc EXIT=0` (0 output) |

**Integration / end-to-end — what exists and what does not.** The slice's E2E is a scripted real-browser run
against the **built** app (`npm run start`, port 3001, `04-start.log`), driving the panel through three
scenarios and capturing screenshots:

| Case | Input | Observed (from `05-e2e-priority.log`) |
| --- | --- | --- |
| **A — real data** | 3 real courses from `courses.json` | order: 无法判断 (no capacity) → 从容 (94 left) → 从容 (265 left); unknown caveat names the 1 course. Screenshot `priority-real.png`. |
| **B — synthetic capacity on real objects** | 4 courses with synthetic `capacity`/`selected` | order: 优先抢 (265/265 full) → 无法判断 (no data) → 尽快 (5 left) → 从容 (192 left). Screenshot `priority-synthetic.png`. |
| **C — self-clashing** | 3 real mutually-clashing courses | no order; conflict caveat names all three. Screenshot `priority-clashing.png`. |

Two things must be said plainly: **(i)** case B uses **synthetic capacity values on real course objects**, not
live registration data — no full section exists in the shipped snapshot (every real `selected` is 0 or near it;
census in `edge-cases.md` §5h: 10 rows have `selected > 0`, but **0** rows are over capacity) — so the *logic*
is exercised end-to-end but the *data path from a live registration system* is not (`task-contract.md:87-90`).
**(ii)** `evidence/logs/05a-e2e-first-attempt.log` is the **first E2E attempt, kept on purpose**, whose fixture
was wrong (its three "real" courses clashed, so it produced case C's output where case A was intended); it is
kept as evidence of the failure and its correction, not hidden.

**Gaps in the test story, stated:**
- There is **no `npm test`**. The slice ships 20 tests but adds no `test` script (`package.json` scripts are
  unchanged: `dev`, `build`, `start`, `lint`, `format`), so they run only via the explicit
  `node --experimental-strip-types --test …` command — no CI wires them up. This is the first test file the
  repository has ever had, so criterion 7 ("ships tests where none existed") holds, but automated test
  execution on every change does **not** exist yet.
- The E2E run is a one-off scripted session, not a checked-in E2E suite; re-running it requires the manual steps
  in `05-e2e-priority.log`.
- The `node --test` runner needs `--experimental-strip-types` on Node 22; no `package.json` engine pin records
  this.

## 5. Peer review and user-task-testing entry points (requirement ⑤)

These are produced by other people and are **the** entry points for review and for task testing:

- **`review/`** — the peer-review record (reviewers, what was reviewed, findings and dispositions). Any review
  comment on this slice should attach to the per-file breakdown in §2 so the reviewer can see the exact surface:
  the pure layer (`lib/priority.ts`, `lib/priority-mapping.ts`), the 58 additive page lines, and the tests.
- **`usability.md`** — the user-task test record: the three representative tasks (real-data order, synthetic
  near-full order, self-clashing refusal), the participants, and the observed friction. The slice's own
  limitation is stated in advance for this file to check, not discover: the panel sits in the plan column so it
  is visible while choosing, but its placement is **provisional** and no usability study beyond those three
  tasks was done (`task-contract.md:94-95`).

At the time of writing, neither `review/` nor `usability.md` exists in
`doc/assignments/a4/` (the directory contains `evidence/`, `rollback.md`, `task-contract.md`, plus this file and
`edge-cases.md`). They are referenced here as the agreed entry points; whoever writes them owns their content.

## 6. Duplicate request · stale version · unauthorized · boundaries (requirement ③ → `edge-cases.md`)

Summary of where each is argued, with the headline result:

| Case | Verdict | Where |
| --- | --- | --- |
| **Repeated / duplicate request** | Safe by construction: `rankPlan` is pure, no state, no I/O. Ran it 1000× on one input — every result byte-identical (`true`). The page's `useMemo` recomputes once per dependency change and reuses the cache otherwise; React `StrictMode`'s double-invoke is harmless. | `edge-cases.md` §1 |
| **Stale version** | The `storageVersion !== 1` branch (`app/page.tsx:589-604`) **silently wipes the plan** — a **pre-existing** upstream risk (A3 R4), **unchanged by this slice** (0 deletions; no storage line in the diff). Out of scope deliberately, so a rollback cannot cost user data. | `edge-cases.md` §2 |
| **Unauthorized access** | **N/A**: no server, no API route, no middleware, no auth; one network egress only (`fetch('/data/courses.json')`, `app/page.tsx:574`). Recorded as N/A with the reason, plus a 6-item checklist for the future minimal API (401/403, idempotency, ownership, input validation, freshness, rate limiting). | `edge-cases.md` §3 |
| **Boundaries** | Empty plan → empty order + "方案为空" caveat; single course; whole plan without capacity → all `unknown`; complete tie → code order; self-clash → no order + reason (incl. the all-clash variant, distinct from the empty-plan caveat); **full 2,077-course ranking measured at 5.092 ms for the mapping+rank single pass** (median 3.604 ms over 200 runs). Extra edges actually run: negative capacity, `capacity 0` with `selected 50`, over-subscribed (`placesLeft = -2`, still `critical`), string capacity, duplicate codes, string `credit`, missing `code`, and a real-data census (2,077 rows / 2,077 codes / 99 sentinels / 0 over-capacity). | `edge-cases.md` §4-§5 |

## 7. If we continue to the server — the smallest next increment

Because ADR-001 put the decision logic in a pure, I/O-free module, the server step does **not** need to touch
it. The smallest increment that adds real value is:

1. **One route handler** `app/api/rank/route.ts` that (a) authenticates the caller, (b) loads the same
   `public/data/courses.json` server-side, (c) **reuses `lib/priority.ts` and `lib/priority-mapping.ts`
   unchanged**, and (d) returns the same `RankResult` shape the panel already renders.
2. **Authorization**: 401 unauthenticated, 403 for another user's plan.
3. **Idempotent semantics**: `GET` (or an idempotency key) so the "duplicate request" case in `edge-cases.md` §1
   stays a non-event across a network hop.
4. **Freshness**: add a capture timestamp alongside capacity, so the deliberate "unknown" does not silently
   become a stale number (the A1 warning the current panel cannot yet answer).
5. Tests for exactly those four points (401, 403, duplicate, stale), reusing the existing 20 as the logic
   regression net.

`lib/priority.ts` and `lib/priority-mapping.ts` should require **no change** for this — that is the payoff of
the change boundary chosen in A3 and the reason this slice was worth extracting.

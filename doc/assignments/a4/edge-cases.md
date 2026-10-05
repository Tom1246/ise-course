# A4 — Edge cases and abnormal situations (with evidence)

Note on revisions: this document describes the slice as it was **peer-reviewed**. The revision that followed
(commit `731bc66`) changed how a places figure may be published and moved "unknown" to the end of the order;
where the text below describes the earlier behaviour, `review/response.md` is authoritative.

**Slice:** `a4-slice-v1` · branch `a4-slice` @ commit `7e17a21` (base `68e7080`, upstream `HMBlankcat/UCAS-course-planner`)
**Scope of this file:** the boundary / failure / hostile-input behaviour of the slice — repeated requests, stale
version, unauthorized access, and input boundaries. Every statement below is either (a) read off a file with a
line number, (b) a named test, (c) a log line, or (d) the output of a script I ran myself. Nothing here is
estimated.

## 0. How to reproduce the measurements in this file

The slice lives in commit `7e17a21`; the working checkout was on a `rollback-test` branch, so the slice files
were extracted with read-only `git show` (no git write, repository untouched):

```bash
mkdir -p /tmp/a4run/lib /tmp/a4run/tests /tmp/a4run/data
R="/…/A4/work/UCAS-course-planner"                       # the read-only clone
git -C "$R" show a4-slice:lib/priority.ts          > /tmp/a4run/lib/priority.ts
git -C "$R" show a4-slice:lib/priority-mapping.ts  > /tmp/a4run/lib/priority-mapping.ts
git -C "$R" show a4-slice:tests/priority.test.ts   > /tmp/a4run/tests/priority.test.ts
cp "$R/public/data/courses.json"                     /tmp/a4run/data/courses.json
```

- 20 unit tests: `cd /tmp/a4run && node --experimental-strip-types --test tests/priority.test.ts`
- edge probes: `/tmp/a4run/checks.ts` → `node --experimental-strip-types checks.ts`
- performance: `/tmp/a4run/perf.ts` → `node --experimental-strip-types perf.ts`
- Node used: **v22.23.2** (`node --version`).

---

## 1. Repeated requests — `rankPlan` is a pure function, repetition cannot compound state

**Situation.** A caller (a user double-clicking, React re-rendering, or a retrying client) computes the order
for the *same* plan more than once. This is the "duplicate request" case.

**Behaviour of the slice.** `rankPlan` is a pure function: it takes `PlanCourse[]` and returns a fresh
`RankResult`; it holds no module-level mutable state, does no I/O, and writes to no store
(`lib/priority.ts:100-140` — the only module-level constant is `WEIGHT`, a frozen-by-usage lookup at `:83`, and
`FEW_PLACES = 10` at `:56`). Re-running it therefore cannot "double" a counter, append to a list, or observe a
previous call. The page computes it through a memo whose dependencies are the plan, the degree marks and the
conflict marks:

```ts
// app/page.tsx:687-703 (slice version)
const priority = useMemo(() => rankPlan(planCoursesFromRows(plan.map(…))), [plan, degreeCodes, conflictCodes]);
```

Precision on the phrasing "the page recomputes once per render": with `useMemo` the factory runs only when
`plan` / `degreeCodes` / `conflictCodes` change by reference. A re-render with unchanged dependencies **reuses
the cached value** and does not even call `rankPlan`; a dependency change calls it exactly once and the result
is a `useMemo`-cached constant for that render. Either way the page never accumulates state across computations.
In React 18 `StrictMode` development the factory may be invoked twice per render — harmless here, because the
function is pure and both invocations return deep-equal results.

**Evidence (run, not assumed).** `/tmp/a4run/checks.ts` case 1 builds a three-course plan (known capacity,
no-capacity, required+near-full), calls `rankPlan` 1000 times, and compares `JSON.stringify` of every result
with the first:

```
1  idempotent over 1000 calls (same JSON) :: true
```

This corroborates the determinism guarantee already asserted by the unit test *"full tie falls back to code, so
output is deterministic"* (`tests/priority.test.ts:100-106`, two runs compared) and acceptance criterion 4
(`task-contract.md:79`).

**If unhandled.** A stateful ranker would let a second call reorder or duplicate lines; here the risk is
proportionate to *zero* because the function is pure and the memo is keyed on its inputs. Residual (not
covered by this run): there is no server, so a real duplicate *HTTP* request cannot be exercised — see §3.

---

## 2. Stale version — `storageVersion !== 1` silently wipes the user's plan (pre-existing, NOT touched here)

**Situation.** The user's browser holds a `localStorage` entry written by an older/newer schema version (or a
corrupt entry), and the app boots.

**Behaviour (read off the file).** In the slice's `app/page.tsx`:

- `:578` reads the stored string; `:581-588` parses it into `{ storageVersion?, plan?, … }`.
- `:589` `if (parsed.storageVersion === 1) { … }` restores the plan.
- `:598-604` **`else`** resets everything to empty: `setPlan([])`, `setDegreeCodes(new Set())`,
  `setEnglishPlan({…未选择})`, `setStudentType('未选择')`, `setSelectedDiscipline('')`.
- The same reset runs in the `catch` for unparsable JSON (`:605-611`), and again when nothing is stored
  (`:612-618` — benign, there is nothing to lose).
- The app writes back with `storageVersion: 1` at `:632-641`.

There is **no message** to the user on the mismatch path: the plan simply appears empty.

**Evidence that this slice did not change it.** `git show --stat 7e17a21` shows `app/page.tsx` with **58
insertions and 0 deletions**; `git diff 68e7080 7e17a21 -- app/page.tsx` contains exactly three hunks — the
imports (`+` lines at the top), the `const priority = useMemo` block, and the panel markup. No line mentioning
`localStorage`, `storageVersion`, `setPlan`, or the reset branch is added or removed. Criterion 8
(`task-contract.md:83`) and `rollback.md` rest on this: a slice that can be rolled back must not be able to
destroy user data.

**If unhandled / risk proportionality.** This is a **pre-existing upstream risk (A3 R4)** and is explicitly
out of this slice's scope (`task-contract.md:55`: "Changing the `localStorage` contract"). Because the slice
does not read, write, migrate or gate on the storage version, rolling the slice back cannot change what the
storage layer does — the risk is *unchanged*, not *introduced*. Fixing it (migration + a user-visible warning
before any reset) is a separate, larger change and belongs to a future slice, not here.

---

## 3. Unauthorized access — N/A, and why

**Situation as asked.** A request without authority reaching a privileged endpoint.

**Behaviour of the slice: there is no such surface.** The application is local-first and has no server
component at all:

- `app/` contains only `globals.css`, `layout.tsx`, `page.tsx` — there is no `app/api/`, no `route.ts`, no
  `middleware.ts` (verified with a filesystem search for `route.ts|route.js|middleware.ts|*api*`).
- Exactly **one** network egress exists in the whole source tree: `app/page.tsx:574`
  `fetch('/data/courses.json')` — a same-origin static asset. A grep for `fetch(` across `app/`, `lib/`,
  `tests/` returns that single hit; there is no `XMLHttpRequest`, `axios`, or WebSocket use in source.
  (The `dist/` build output also contains framework-internal `fetch` code; that is bundler output, not
  application code, and the `dist/` tree is the *base* build, not the slice.)
- There is no auth, no session, no token, no user identity. All per-user state is the browser's own
  `localStorage` (`PLAN_STORAGE_KEY`), reached only from the same page.

So there is nothing that can return 401/403 and nothing to authorize: the "unauthorized access" case is
**not applicable to this slice**, by construction, not by omission. Recording this as N/A is the honest answer;
inventing an auth flow here would be building a server that the requirement does not ask for yet
(`task-contract.md:52` defers server/API/authorization by decision).

**What would have to be added if a minimal API is introduced later (checklist, not implemented):**

1. **401** for an unauthenticated request and **403** for an authenticated request for another user's plan.
2. **Idempotency**: make the rank endpoint a `GET`, or accept an idempotency key, so the "repeated request"
   case in §1 stays a non-event once a network hop exists.
3. **Ownership validation**: the server must not trust plan rows sent by the client; validate that the
   referenced course codes exist and belong to the caller.
4. **Input validation** mirroring the mapping guarantees: non-numeric / negative / sentinel capacity must be
   rejected or mapped to `unknown`, never to "full" (`lib/priority-mapping.ts:26-32`).
5. **Freshness**: carry a capture timestamp with capacity, so the honest "unknown" of §4c does not become a
   stale number the client trusts.
6. **Rate limiting**, and a test suite covering at least: no token → 401; wrong owner → 403; duplicate request
   → single effect; empty plan → 200 with the empty caveat; stale snapshot → the freshness field is present.

---

## 4. Input boundaries (each one run, not asserted)

### 4a. Empty plan
`lib/priority.ts:100-139` short-circuits nothing; `rankPlan([])` returns `{ order: [], unknownCodes: [] }`
plus one caveat, produced by the explicit branch at `:137`. Unit test *"empty plan yields an empty order and
says so"* (`tests/priority.test.ts:118-123`) asserts the list is empty and the caveat matches `/方案为空/`.
My run (`checks.ts` case 8):

```
8  empty plan :: ["方案为空，没有需要排序的课程"]
```

The panel handles it: `priority.order.length > 0` is false (`app/page.tsx:1284`), so `app/page.tsx:1296` renders the placeholder
"先加入课程，这里会按名额风险给出先抢哪一门。" rather than an empty list. Risk if unhandled: a blank panel with
no explanation — avoided.

### 4b. Single course
A one-course plan is the smallest non-empty input. Unit tests already rank single-course plans: *"missing
capacity is reported as unknown, never as safe"* (`:54-62`) and the mapping sentinel test (`:156-160`). The
comparator `lib/priority.ts:105-116` never runs its tie-break chain for a length-1 array, so no ordering
assumption can be violated. No separate run needed beyond those tests; not a risk.

### 4c. The whole plan has no capacity data
Every line becomes `unknown` and is ordered by the remaining criteria (required, autumn-only, code); nothing is
guessed. My run (`checks.ts` case 4) — a 3-course plan with no capacity at all:

```
4  all-unknown order :: ["1:P1:unknown","2:P2:unknown","3:P3:unknown"]
4b all-unknown unknownCodes :: ["P1","P2","P3"]
```

This is not hypothetical for the real data: of the 2,077 rows in `public/data/courses.json`, **99** carry
`capacity === 0`, which the mapping deliberately converts to `unknown`
(`lib/priority-mapping.ts:30`, unit test *"mapping: capacity 0 is a sentinel, not a full section"* `:156-160`).
Risk if unhandled: mapping the sentinel to "full" would have made 99 courses look like a crisis and put them at
the very top — the "invented crisis" the module header warns about (`lib/priority-mapping.ts:10`).

### 4d. Complete tie
When urgency, required, autumn-only and places-left all tie, the comparator falls through to the course code
(`lib/priority.ts:115`). Unit test *"full tie falls back to code…"* (`:100-106`) and my run (`checks.ts` case 5):

```
5  complete tie :: ["A","Z"]
```

Risk if unhandled: a non-deterministic order between equal courses would make the output untestable and
visibly jitter between renders. Covered.

### 4e. A plan that clashes inside itself
A2's rule is that a clashing plan must be resolved before it can be judged, so `rankPlan` refuses to order the
clashing courses and states why: `lib/priority.ts:101-102` partitions them out, `:134-136` emits the caveat.
Unit test *"a plan that clashes internally is not given an order for the clashing courses"* (`:108-116`).

I additionally ran the **whole-plan-clashes** variant, which is a distinct branch worth naming (`checks.ts`
case 7):

```
7  all-clash order :: 0
7b all-clash caveats :: ["未参与排序：它们在方案内部互相冲突，请先解决冲突（K1、K2）"]
```

Note the difference from §4a: when the plan is non-empty but entirely clashing, the caveat is the *clash*
caveat only — the "方案为空" branch at `:137` is guarded by `!courses.length`, which is false, so the user is
correctly told the real reason ("resolve the conflict"), not a misleading "plan is empty". End-to-end case C
in `evidence/logs/05-e2e-priority.log` shows the same three-clashing-course fixture producing no order and the
conflict caveat in a real browser (`evidence/priority-clashing.png`). Risk if unhandled: advising a registration
order for an impossible plan, which is precisely the A2 failure mode.

### 4f. Performance of ranking all 2,077 courses
The realistic workload is the user's plan (typically < 10 courses), but the task asked for the full-catalogue
bound. Command and full output (`/tmp/a4run/perf.ts`, Node v22.23.2, this Mac):

```
$ cd /tmp/a4run && node --experimental-strip-types perf.ts
rows in file: 2077
plan courses: 2077
unknown (no capacity): 99
known: 1978
order length of run 1: 2077 | first: 180080025200M3001H unknown
rankPlan over 2077 courses, N=200 runs
  min=2.565 ms  median=3.604 ms  mean=7.076 ms  max=99.283 ms
planCoursesFromRows + rankPlan (single pass): 5.092 ms | ranked 2077
worst case (all 2077 fully tied), N=50: min=0.738 ms median=0.795 ms max=2.594 ms
```

Reading: the **single pass that the page actually performs — mapping 2,077 rows then ranking them — is
5.092 ms**, comfortably inside one frame budget; the median of repeated runs is 3.604 ms. The 99.283 ms `max`
is a single cold outlier (JIT/GC pressure on the first measured iterations), not a steady-state cost: the
median and the fully-tied worst case (which forces every comparison all the way to the code tie-break, the
most expensive path) are both **under 1 ms median**. Risk if unhandled: none observed — but see the honesty
note in §6.

---

## 5. Additional boundaries I found and actually ran

`checks.ts` cases 2-3, 6, 9-11, plus the census. All outputs verbatim:

| # | Situation | Observed behaviour | Evidence |
| --- | --- | --- | --- |
| a | negative capacity (`limit = -5`) | → `unknown`, never `critical` | `checks.ts` 2a: `{"kind":"unknown"}`; guard `priority-mapping.ts:30` (`limit <= 0`) |
| b | `capacity === 0` **and** `selected === 50` | still `unknown` — the sentinel wins, a `0` is never read as "nobody enrolled" | `checks.ts` 2b/2c: `{"kind":"unknown"}` / level `"unknown"` |
| c | over-subscribed (`selected > capacity`, e.g. 422/420) | `placesLeft` returns a **negative** number (`-2`) and `urgencyOf` classifies it `critical` | `checks.ts` 3a: `-2`; 3b: `"critical"`; unit test *"over-subscribed section is critical"* (`:34-37`) |
| d | capacity arrives as a **string** (`"265"`, e.g. from a JSON export) | → `unknown`, no coercion, no crash | unit test *"missing or non-numeric fields become unknown…"* (`:162-167`) |
| e | duplicate course codes in one plan | both kept and ranked (length 2) — the function tolerates it | `checks.ts` case 6: `2` |
| f | `credit` supplied as a string inside a raw row | mapped to `0`, no throw | `checks.ts` case 9: `0`; `priority-mapping.ts:39` |
| g | row with no `code` | mapped to `''` (still sortable, no throw) | `checks.ts` case 10: `""`; `priority-mapping.ts:37` |
| h | real-data census | 2,077 rows, **2,077 distinct codes**, 99 rows with `capacity === 0`, 10 rows with `selected > 0`, **0** rows with `selected > capacity`, capacity field is always a `number`, none missing | one-off `node -e` census over `public/data/courses.json` |

Two of these deserve a sentence each:

- **(c) negative `placesLeft`.** `placesLeft` is documented as "`null` = not knowable, **never 0**"
  (`task-contract.md:63`) and `-2` is a legitimate derived value for an over-subscribed section, not a
  not-knowable case. `urgencyOf` orders its branches so the non-positive check comes first
  (`lib/priority.ts:70-73`), so the negative never falls through to the "places left" message; and the panel
  renders `urgency.reason` (a string), not `placesLeft` as a number (`app/page.tsx:1291`), so a `-2` is never
  shown to the user as if it were places. Consistent, but worth recording because it is the one place where the
  "no number means unknown" rule and an actual number can look alike.
- **(h) `selected` is not in the upstream `Course` type.** `Course` declares `capacity?: number`
  (`app/page.tsx:80`) but **not** `selected?`, so the slice reads it through a structural cast at
  `app/page.tsx:696` (`(course as { selected?: number }).selected`). If upstream ever renamed or dropped
  `selected`, the cast would silently yield `undefined`; `capacityFromRow` then returns `unknown`
  (`lib/priority-mapping.ts:29`) — i.e. the failure mode is *fail-safe* (the course is marked "cannot judge",
  §4c) rather than *fail-wrong* (invented capacity). Not a defect, but a coupling to a field the type model does
  not protect.

One non-boundary worth stating for completeness: `rankPlan` never reads `credit`. `PlanCourse.credit` exists
and is faithfully carried by the mapping, but no ordering criterion uses it — the five criteria are capacity
risk, degree/required, autumn-only, places-left, code (`lib/priority.ts:88-94`). This is deliberate (credit does
not change *which section fills first*), but a reader might expect a "bigger course first" rule that is not
there.

---

## 6. Weakest conclusion in this file (stated, not hidden)

The measurements in §4f are the least load-bearing. They were taken with `node --experimental-strip-types` on
this Mac against `public/data/courses.json`, i.e. the **pure function layer**, and the `max = 99.283 ms`
outlier is un-attributed (JIT/GC, not profiled). More importantly, the page never ranks 2,077 courses — it
ranks the user's plan, so §4f is a stress ceiling on the pure layer, **not** a measurement of the shipped
UI's frame time. The claim "performance is not a risk" is therefore supported only up to "the pure ranking of
the whole catalogue costs a few milliseconds in Node"; it says nothing about browser paint or about a future
server-side ranking of many users' plans. Also, §1's duplicate-request guarantee is argued from purity and from
an in-process 1,000-call loop; no real duplicate network request exists to test, because there is no server
(§3). Both limits are consequences of the same deliberate scope decision, and both are recorded rather than
papered over.

# A4 — End-to-End Vertical Slice and Automated Verification

- **Release** 2026-11-02 16:30 · **Deadline** 2026-11-09 16:30 (Asia/Shanghai) · **Platform** <https://learn.spaiq.ai>
- **Status:** slice implemented and verified locally; platform record submitted inside the window.
- **Tag:** `a4-v1` (this folder's documents). The slice itself lives as a **patch** — see §2.

Objective: deliver a small, complete, reviewable, **reversible** slice of user value — "cut one slice", cleanly.

## 1. What the slice is

A panel in the upstream course planner that answers the question A1 was burnt by: **which course do I register
for first?** It ranks the courses already in the plan by what the data can actually support, and says plainly
when it cannot support a judgement.

Traceable requirement: A1 pain point 1 ("I had not fixed the order to register in in advance…") and pain point 3
(required courses, autumn only, heavy registration pressure), plus the absence A1 identified in the existing tool
("there is no order to register in"). Full traceability table: `task-contract.md` §1.

The slice was built under **ADR-001** from A3: extract a pure, testable function layer; leave UI, state and
persistence alone.

## 2. Where the code is (and how a reviewer reproduces it)

This work was done **locally first**, by decision: the slice exists as a patch against the frozen upstream commit.

| Item | Value |
| --- | --- |
| Upstream | `HMBlankcat/UCAS-course-planner` @ `68e7080503084a41f42db6e0e9ff94c0e9ef2f19` (MIT) |
| Slice | commit `731bc66` on a local branch, exported here as **`slice-731bc66.patch`** (25,623 bytes, 6 files, +523 / −0) |
| Apply it | `git clone https://github.com/HMBlankcat/UCAS-course-planner && cd UCAS-course-planner && git checkout 68e7080 && git apply <path>/slice-731bc66.patch` |
| Verified | `git apply --check` passes against a fresh clone of upstream (`evidence/logs/12-patch-applies.log`) |
| Run it | `npm ci --include=dev` → `npm run build` → `PORT=3001 npm run start` (see `reproduction notes` below) |

No fork and no new public repository was created: the patch is self-contained and provably applicable, which is
what "a small diff and commit" needs in order to be checkable at all.

### Reproduction notes (each command was run; logs in `evidence/logs/`)

```bash
npm ci --include=dev --registry=https://registry.npmmirror.com --no-audit --no-fund   # 01 (the mirror is a documented deviation)
node --experimental-strip-types --test tests/priority.test.ts                          # 02  -> 24 pass / 0 fail
npm run build                                                                          # 03  -> exit 0
PORT=3001 npm run start                                                                # 04  -> http://0.0.0.0:3001
npm run lint                                                                           # 06  -> 0 warnings / 0 errors (8 files)
npx tsc --noEmit                                                                       # 07  -> exit 0
```

> `--include=dev` is mandatory on this machine: its npm config sets `omit=dev`, which silently skips a
> devDependency the build imports. That trap is A3's risk R5, and it is recorded in `doc/pitfalls.md` §1.1.

## 3. Deliverables mapped to A4's requirements

| A4 requirement | Where it is answered |
| --- | --- |
| 1. A valuable bounded slice from a traceable requirement | `task-contract.md` §1–§3 |
| 2. UI / server authorization / state change / failure feedback / recovery | `slice-notes.md` (what is implemented; the server side is **deferred by decision** and named as such) |
| 3. Duplicate requests, stale versions, unauthorized access, boundaries | `edge-cases.md` (with measurements: 1,000 identical calls, 2,077-course timing) |
| 4. Unit, integration and end-to-end checks proportional to risk | `evidence/logs/02` (24 unit), `05`/`05b` (4 end-to-end cases), `03/06/07` (build, lint, types) |
| 5. Peer review, representative-user task testing, rollback design | `review/peer-review.md` (independent) + `review/response.md` (point-by-point) + `usability.md` + `rollback.md` |
| Small diff and commit | `slice-731bc66.patch`; rollback tested in `rollback.md` §2 |
| Usability / error-behaviour evidence | `usability.md` §1–§3 |
| Platform summary (150–300 words) | `A4-summary-en-2026-10-05.md` (count checked by `scripts/count_words.py`) |

## 4. The two things a reader should not miss

1. **The peer review changed the slice's central claim.** The first version published `capacity − selected` as
   "places left"; the review showed that `selected` is 0 in 1,968 of 1,978 rows and has no capture time, so the
   panel was dressing a static section size up as live registration pressure. The slice now publishes a figure
   **only with a dated enrolment figure**, and prints nothing but a reason otherwise. The response is in
   `review/response.md`; the fix is in the patch.
2. **A weaker demo and a stronger claim.** On the shipped snapshot the panel therefore shows
   "无法判断" for nearly every course, and the order falls back to degree course → course code. That is the
   honest result: the data cannot support the number the panel used to print.

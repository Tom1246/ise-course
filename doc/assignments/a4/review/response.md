# Response to the peer review (2026-10-05)

The review was produced by an independent agent that was given **only the diff, the tests and the repository** —
not the author's explanation, not the requirement, not these documents. Every finding below was **reproduced
before answering**: nothing was accepted or rejected on the strength of the review text alone. The revision it
forced is commit `731bc66` on branch `a4-slice`.

## 1. Findings and answers

| # | Finding (abridged) | Severity | Verdict | Action |
| --- | --- | --- | --- | --- |
| F1 | `selected` is treated as an authoritative live enrolment count, so `limit - enrolled` is rendered as "剩余 N 个名额 / 抢课风险" with no caveat — while `capacity === 0` in the same file is carefully downgraded to *unknown*. In the shipped data `selected` is 0 in **1,968 of 1,978** rows that have a capacity. | **severe** | **Accept** | A places figure is now publishable **only** with a dated enrolment figure (`enrolmentAsOf`). The shipped data has none, so the real-data path publishes **no** figure and says which of two reasons applies. New tests: "a number is published only with a dated enrolment figure", "capacity without a capture time is not turned into 'places left'", "a dated enrolment figure is published". New end-to-end case D asserts no figure is published. |
| F2 | Consequence of F1: the panel's first line is `无法判断`, which contradicts its own heading "按名额风险给出先抢哪一门". | severe | **Accept** | The ordering weights changed: measured cases first by severity (`critical → high → normal`), **unknown last**. Re-ranking is documented in `task-contract.md` §2 and tested ("measured cases come before unmeasurable ones"). |
| F3 | `critical` is unreachable on the shipped data (full-catalogue run: `{normal: 1976, high: 2, unknown: 99}`; `autumnOnly` is never passed by the page), so the four-level vocabulary collapses to two. | moderate | **Accept as a documented limitation** | Not fixable without data the repository does not carry (a capture time, and a semester field). Now stated in `task-contract.md` §6 and exercised only by the labelled synthetic case, which carries a capture time. |
| F4 | A corrupt capacity (`limit: -5`) sorted **ahead of** a genuinely full `265/265` section, printing `已满（0/-5）`. Their probe: 3 pass / 1 fail. | moderate | **Accept** | `capacityFromRow` now rejects non-finite and non-positive limits (`no-capacity-data`) and negative enrolment figures (`no-enrolment-provenance`). Regression test: "corrupt capacity cannot outrank a genuinely full section". |
| F5 | Dead comparator branches: across 48,005 generated combinations no pair ever reached the mixed null-ness paths. | minor | **Accept** | Those branches were removed; the comparator now compares `placesLeft` only when both are known. |
| F6 | Removing `allowImportingTsExtensions` breaks only `tests/*.ts` (TS5097), i.e. the `tsconfig.json` change is needed by the tests, not by the app. | informational | **Accept, noted** | The change stays (the tests are part of the slice) and is now described as test-only in the commit message. |
| F7 | The review could not rely on a stable branch: the working tree moved `7e17a21 → rollback-test → a4-slice` while it worked. | process | **Accept — my fault** | The rollback test was run on the same work tree that concurrent readers were using. The reviewer handled it correctly by pinning to `git archive 7e17a21`. Lesson: a rollback test belongs in a separate clone, or the readers must be paused. |

Nothing in the review was rejected. The reviewer's own counter-attempts (implementation vs documented rule over
5,000 differential runs, tie determinism, permutation, sentinel handling, no regression in build/lint/types) were
left in place as evidence.

## 2. What this changed about the slice's claim

Before: *"here is the order, and here is how many places each section has left."*
After: *"here is the order, judged only on what the data can actually support; where it cannot, it says so instead
of printing a number."*

For the repository's own snapshot this means the panel shows **容量 exists, 报名数没有采集时间 → 无法判断** for
essentially every course, and the order falls back to degree course → course code. That is a weaker-looking
demonstration and a stronger claim: it is the same failure mode A1 recorded ("treating an old snapshot as
current"), now enforced in code rather than promised in prose.

## 3. Verification after the revision (all fresh)

| Check | Result | Evidence |
| --- | --- | --- |
| unit tests | **24 pass / 0 fail** (`node --experimental-strip-types --test tests/priority.test.ts`) | `evidence/logs/02-unit-tests.log` |
| repository lint (`npm run lint`) | **0 warnings / 0 errors**, 8 files | `evidence/logs/06-lint.log` |
| type check (`npx tsc --noEmit`) | exit 0 | `evidence/logs/07-typecheck.log` |
| build (`npm run build`) | exit 0, `Build complete` | `evidence/logs/03-build.log` |
| end-to-end, four cases | real data: no figure published ✓ · synthetic with capture time: figures published ✓ · no provenance: no figure + caveat ✓ · clashing plan: refused with reason ✓ | `evidence/logs/05-e2e-priority.log`, `05b-e2e-after-review.log` |
| rollback | reverted tree is identical to upstream, and builds | `evidence/logs/09-rollback-test.log` |
| diff after revision | 6 files, **+523 / −0**, persistence contract untouched, no dependency change | `evidence/logs/10-rollback-guarantees.log` |

## 4. Still open (deliberately)

- The panel's placement (bottom of the plan column) was not part of the review; `usability.md` §2 already records
  it as the weakest usability decision.
- The reviewer's point that `autumnOnly` is never supplied by the page remains true: the page holds no semester
  information (A1 gap ①), so this input stays unused until that gap is closed.
- Server-side authorization stays deferred by decision; when it arrives, `edge-cases.md` §3 lists the checks it
  will need (401/403, duplicate requests, idempotency).

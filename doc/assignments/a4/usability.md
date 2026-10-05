# A4 — representative-user task testing

Note on revisions: this document describes the slice as it was **peer-reviewed**. The revision that followed
(commit `731bc66`) changed how a places figure may be published and moved "unknown" to the end of the order;
where the text below describes the earlier behaviour, `review/response.md` is authoritative.

Three tasks, run against the built application (port 3001), with the plan injected through the app's own storage
contract and one task performed by **clicking the app's own control**. Raw run: `evidence/logs/11-usability.log`,
screenshots `evidence/usability-t*.png`.

This is not a usability study with users; it is a scripted walkthrough of the three situations the slice claims to
handle, with the step count measured and the friction written down. What it cannot replace is stated in §4.

## 1. Tasks and what happened

| # | Task (as a user would ask it) | Expected | Observed | Steps for the user |
| --- | --- | --- | --- | --- |
| 1 | "I have five courses — which do I register for first?" | an ordered list, no extra interaction | the panel lists all five with a label and a reason (all `从容` here: 40 / 40 / 40 / 40 / 111 places left) | **0** — the plan is already restored when the app opens; the panel sits in the plan column |
| 2 | "This course has no capacity data — what is your advice?" | the course is flagged, and **not** treated as safe | 无法判断 语言学与应用语言学研究方法 — 该班次没有容量数据，依据现有数据无法判断抢课风险, ranked **above** the two known-safe courses, plus the caveat 有 1 门课没有容量数据：它们按其他属性参与排序并标记为"无法判断"，而不是假定还有名额 | **0** |
| 3 | "I removed a course — does the order change?" | the order recomputes | clicked the app's own 移出方案 once; the list went from 5 entries to 4 and the caveat/hints re-rendered | **1 click** |

## 2. Findings worth keeping

1. **The slice is passive where it can be.** Tasks 1 and 2 needed no interaction at all: the ranking is part of the
   plan view, so the answer is already on screen when the user looks for it. That was the goal (A1's pain was
   *having no order at all*), but it also means a user who does not scroll may never see it — the panel's position is
   the weakest usability decision here.
2. **The honesty rule is visible, not just internal.** In task 2 the missing-data course is printed **first**, above
   courses whose safety is known. A reader sees 无法判断 ahead of 从容 and can ask why; the reason string answers it.
3. **The order is live.** Task 3 shows the update after the app's own removal handler, i.e. through the real state
   path, not a re-injection. Nothing had to be reloaded.
4. **A mistake of mine that the app caught (kept as evidence).** The first Task-2 fixture failed: the panel reported a
   clash between two courses instead of the expected 无法判断. The cause was in **my fixture**, not the slice: I
   compared slot strings, so `周六(7-8)` and `周六(5-7)` looked different although they share period 7 — the app was
   right to call it a clash, and the slice was right to refuse to order it. This is the same class of trap A2 recorded
   for week ranges ("naive comparison is wrong in both directions") and is carried forward to A5 as a counter-example.
   Evidence: `evidence/logs/05a-e2e-first-attempt.log` and the failed Task-2 run before the fix.
5. **What the panel does not say.** It gives an order, not a *time*; it shows places left without a capture time
   (A3 R3); and courses excluded for clashing appear only in the caveat, not as a per-course explanation in the list.

## 3. Error behaviour (part of the same walkthrough)

| Situation | What the user sees | Is that acceptable? |
| --- | --- | --- |
| A plan that clashes internally (observed in task 2's first fixture) | no order, plus 未参与排序：它们在方案内部互相冲突，请先解决冲突（…） | yes — an order for an impossible plan would be worse advice |
| Missing capacity data | 无法判断 with the reason, above known-safe courses | yes, and it is the slice's central claim |
| Empty plan | 先加入课程，这里会按名额风险给出先抢哪一门 | yes |
| The data has no semester field | a standing note: 本数据没有开课学期字段，因此「只在秋季开课」这一项无法计入（这是 A1 记录的缺口①） | yes — the limitation is on screen instead of being silently ignored |

## 4. What this walkthrough does not establish

- **No real users.** Three scripted tasks are not a task test with people: no think-aloud, no time-on-task, no
  measure of whether a student would trust the order. The slice is *verified*, not *validated*.
- **One data set.** All tasks use the repository's own 2,077-course snapshot, which contains no full section — so the
  `优先抢` label and the "you are about to lose this section" situation are exercised in tests and in the labelled
  synthetic case (`evidence/logs/05-e2e-priority.log`), never with real pressure data.
- **One browser, one platform.** Headless Chromium via CDP on macOS; no mobile layout was checked.

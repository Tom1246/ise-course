# A4 rollback guide

The slice is **one commit** on top of the upstream commit that A3 froze. Everything below was executed, not
designed on paper: the test in §2 ran on 2026-10-05 and its output is in `evidence/logs/09-rollback-test.log`.

## 1. What a rollback has to undo

| Item | Where it lives | Rollback effect |
| --- | --- | --- |
| The ranking layer | `lib/priority.ts`, `lib/priority-mapping.ts` (new files) | deleted — nothing else imports them |
| The panel + one `useMemo` in the page | `app/page.tsx`, +58 lines, purely additive | removed |
| The tests | `tests/priority.test.ts` (new file) | deleted |
| Two configuration lines | `tsconfig.json` (+1: `allowImportingTsExtensions`), `.gitignore` (+3: `*.tsbuildinfo`) | reverted |
| **User data** | `localStorage` (`ucas-graduate-course-planner-v3`) | **not touched — see §3** |
| Dependencies | none | no `package.json` / lockfile change to undo |

## 2. The rollback test that was actually run

```
git checkout -b rollback-test a4-slice          # scratch branch, so the slice is never at risk
git revert --no-commit HEAD && git commit -m "revert: rollback test"
git diff upstream/main --name-only              # -> 0 files
git status --short                              # -> clean
npm run build                                   # -> EXIT=0, "Build complete"
```

Observed results (verbatim in `evidence/logs/09-rollback-test.log`):

| Step | Result |
| --- | --- |
| files differing from upstream after the revert | **0** — the tree is byte-identical to the frozen upstream commit |
| working tree after the revert | clean |
| `npm run build` **without** the slice | **EXIT=0**, `Build complete` |

The scratch branch was then deleted and `a4-slice` restored (`git checkout a4-slice`), so the slice is intact at
commit `7e17a21`.

## 3. Why a rollback cannot damage a user's plan (machine-checked)

A3 risk R4 records that this app **silently resets the whole plan** when the stored `storageVersion` is not `1`
(`app/page.tsx:578`, `:587–600`). A slice that bumped the storage version would therefore be able to wipe a user's
work when rolled back. This slice does not touch that contract, and the claim is checked mechanically in
`evidence/logs/10-rollback-guarantees.log`:

| Guarantee | Measurement |
| --- | --- |
| purely additive | **425 insertions, 0 deletions** across 6 files |
| persistence untouched | **0** lines in the `app/page.tsx` diff mention `PLAN_STORAGE_KEY`, `storageVersion`, `setItem`, `getItem` or `removeItem` |
| no new dependencies | **0** files changed among `package.json` / `package-lock.json` |

## 4. Rollback procedure

**If the slice was never merged (the branch model):**
```bash
git checkout main            # or the deployment branch
git branch -D a4-slice       # discard the branch; upstream is untouched
npm ci --include=dev         # rebuild the previous state
npm run build && npm run start
```
This is the cheapest form, and it is why the slice was kept as a separate branch on a clone.

**If the slice was merged (upstream history contains it):**
```bash
git revert 7e17a21           # creates an inverse commit; no force-push, no history rewrite
npm ci --include=dev && npm run build
```

**If it was merged and then followed by more work:** revert in reverse order (`git revert` the newest
slice-dependent commit first), then run the two verifications below.

## 5. What to verify after any rollback

1. `git diff <upstream-commit> --name-only` returns nothing (the tree equals the pre-slice state).
2. `npm run build` exits 0 and the app serves: `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/`
   returns `200`.
3. Open the app with an existing plan: the plan must still be there. If it is empty, the storage contract was
   touched — which the checks in §3 say cannot happen, so that outcome would mean the rollback brought in more
   than this slice.

## 6. What would invalidate this plan

- **A server-side step (deferred).** If the follow-on work adds an API and an authorization token, a rollback then
  has to also remove configuration and rotate the token — the "additive, self-contained commit" property is what
  makes this plan cheap today, and it would no longer hold. That is the main reason the server work is a separate
  step rather than a part of this slice.
- **Any change to the storage contract.** If a later slice bumps `storageVersion`, rollback stops being harmless to
  user data and needs a migration path instead of a plain revert (A3 R4).
- **A dependency addition.** Any new package makes the rollback also a dependency-removal (`npm ci` from the
  previous lockfile), which is slower and easier to get wrong.

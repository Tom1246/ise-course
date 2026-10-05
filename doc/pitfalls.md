# Pitfall diary — what went wrong, and what to do next time

Maintained for the author's own use **and** deliberately kept in this repository, because "a mistake you can
reproduce is evidence" is the standard this coursework sets. Entries are grouped by where the trap lives, and
each one records symptom → cause → countermeasure → how to reproduce it.

Scope: everything encountered while producing A1–A4 of this course (2026-09/10). Later assignments append.

---

## 1. Environment traps (nothing to do with the repository)

**1.1 A clean install that silently skips dev dependencies**
- *Symptom:* `npm run build` dies with `ERR_MODULE_NOT_FOUND: Cannot find package '@openai/sites-vite-plugin'`,
  and `npm install <that package>` answers `up to date` while `node_modules` still does not contain it.
- *Cause:* this machine's npm config has `omit=dev` (`npm config get omit` → `dev`). Every plain
  `npm install` drops devDependencies; the build config imports one.
- *Countermeasure:* `npm ci --include=dev` from the frozen lockfile (560 packages) — and read
  `npm config get omit` **before** blaming a repository.
- *Reproduce:* `npm config get omit` → `dev`; `npm ci` then `npm run build` → module-not-found.
- *Bonus:* `hermes verify` walks into the same trap, because its bootstrap phase runs `npm install`
  (`evidence/logs/08-hermes-verify-trap.log`). A generic tool's "detected" recipe is not a clean-room.

**1.2 The mirror registry rewrites the lockfile**
- *Symptom:* after installing through `registry.npmmirror.com`, `git status` shows ` M package-lock.json`.
- *Cause:* npm rewrites the `resolved` URLs of the lockfile to the registry actually used.
- *Countermeasure:* build in a copy, keep the frozen clone untouched; after installing, restore the lockfile
  (`git checkout -- package-lock.json`). Record the registry as a **deviation from the clean recipe**.

**1.3 An iCloud placeholder file hangs tools silently**
- *Symptom:* `ffmpeg`/`ffprobe` (and other readers) hang with no error on a file that looks present.
- *Cause:* the file is not materialised on disk (`stat -f %b` → blocks = 0).
- *Countermeasure:* `brctl download <file>` first.
- *Related:* overwriting an existing large file can time out (`pymupdf` `cannot fwrite: Operation timed out`);
  render to `/tmp`, then `rm` + `cp`.

---

## 2. Data and evidence traps

**2.1 "Places left" is not `capacity − selected`**
- *Symptom:* the panel printed "剩余 111 个名额" from a static file.
- *Cause:* `selected` is 0 in 1,968 of the 1,978 rows that have a capacity, and nothing states when it was
  captured. The subtraction therefore republishes the section size as if it were live pressure.
- *Countermeasure:* publish a figure only together with its capture time; otherwise say "无法判断" and name
  which piece is missing. (A1 predicted this: "the system cannot know by itself that the data is stale, only by
  stating the capture time in the output".)
- *Lesson:* the same caution applied to one field (`capacity == 0` → unknown) must be applied to the field
  next to it. Inconsistent scepticism is still a false statement.

**2.2 Comparing slot/week strings instead of intervals**
- *Symptom:* a fixture "without clashes" turned out to clash; the app was right, my fixture was wrong.
- *Cause:* `"周六(7-8)"` and `"周六(5-7)"` are unequal strings but share period 7. Comparing `dayPeriods`
  strings misses overlaps in both directions.
- *Countermeasure:* parse day + period range + week set and intersect them. This is the *same* trap A2 recorded
  for week ranges, hit again in a throwaway fixture script — the lesson only stuck once it was written into a
  tested function.
- *Reproduce:* `git diff upstream/main -- tests/` shows the interval logic (`parseWeeks`/`parsePeriods`).

**2.3 `capacity == 0` is a sentinel, not "full"**
- *Symptom:* 40 "over-capacity violations" reported by the first version of A2's check.
- *Cause:* the official export writes `"/"` for "not set" (40 rows); the derived snapshot renders it as `0`.
  Reading it as a number invents a crisis.
- *Countermeasure:* treat it as unknown and say so; 99 of 2,077 rows carry it.

**2.4 Two counting rules give two "correct" numbers**
- *Symptom:* A1's brief says 282 course codes, A2's data dictionary said 270 — both defensible, contradictory
  inside one repository.
- *Cause:* different suffix-stripping rules (numeric-only vs all suffixes; 12 alphanumeric suffixes).
- *Countermeasure:* state the rule next to the number and give the alternative value. Never leave a bare count.

**2.5 A measurement without a log is not evidence**
- *Symptom:* a subagent refused to use "curl returned HTTP 200 (0.14 s)" because no log contained it — correctly.
- *Cause:* the measurement was taken interactively and never written to a file.
- *Countermeasure:* capture first, cite second (`evidence/logs/09-http-health.log`). A zero-byte log is also
  weak: give every log a header (command, time) and an exit code.

**2.6 Retained failures are the point**
- The failed first install, the failed first build, the wrong fixture, the corrupt-capacity probe that failed —
  all kept. A run that only ever succeeds cannot show what the check would catch.

---

## 3. Delegation traps (subagents)

**3.1 A subagent writing a redaction checklist will paste the secrets into it**
- *Symptom:* a governance document instructing "scan for the student ID" contained the ID itself, in a
  `git grep -nE '…'` example.
- *Countermeasure:* hand over patterns and placeholders (`\b\d{4}[A-Z]\d{10}\b`, `$SID`), never literals; re-scan
  the deliverable for the literal afterwards.

**3.2 Subagent output must be re-verified, not trusted**
- Their self-reports are claims. In this course: a subagent's data dictionary reported 270 codes (vs 282), one
  re-opened a question the author had already settled, one flipped which source is authoritative — all found by
  reading the file, not the report. Conversely, one correctly refused to use an unlogged measurement.
- *Countermeasure:* re-run their key numbers; check their files for leaks and for internal contradictions.

**3.3 Do not mutate a work tree that others are reading**
- *Symptom:* a reviewer's line numbers became unreliable because the branch changed mid-review
  (`a4-slice` → `rollback-test` → `a4-slice`).
- *Cause:* the rollback test ran in the same clone the readers were using.
- *Countermeasure:* run destructive experiments (revert, reset, checkout) in a **separate clone**, or pin
  readers to an explicit commit (`git archive <sha> | tar -x -C /tmp/...`).

**3.4 Give every parallel task a full brief**
- Children know nothing of the conversation: paths, frozen commit, the exact numbers they must not invent,
  the file they may write, and "no git operations" all have to be in the brief. Re-dispatching costs more than
  a complete brief.

---

## 4. Toolchain and code traps (JavaScript/TypeScript here)

**4.1 `node --test <dir>` treats the directory as a module**
- *Symptom:* `Cannot find module '.../tests'`.
- *Countermeasure:* name the files (`node --test tests/priority.test.ts`).

**4.2 Node type stripping requires explicit `.ts` in import specifiers**
- importing `'../lib/priority.ts'` works at runtime but TypeScript objects (`TS5097`); `tsconfig.json` needs
  `allowImportingTsExtensions: true`. Removing it breaks **only the tests**, never the app build.

**4.3 `node:test`'s `test()` returns a promise — the repo's linter objects**
- *Symptom:* 20 × `typescript(no-floating-promises)`.
- *Countermeasure:* `void test(...)` (explicit "deliberately ignored"), which satisfies the rule the upstream
  code already passes.

**4.4 ASCII quotes in JSX text fail the linter**
- *Symptom:* `react(no-unescaped-entities)`.
- *Countermeasure:* use the product's own punctuation (「」 or nothing) — which also fixes the style: this app is
  Chinese, so English reason strings inside its panel read foreign.

**4.5 Type a "raw row" honestly, then cast only where the data is genuinely hostile**
- `String(row.code ?? '')` on an `unknown` field triggers `no-base-to-string`. Type the row (`code?: string`), and
  where a JSON export could really hand you a string, express that as an explicit cast in the **test**.

**4.6 Build caches leak into commits**
- `tsconfig.tsbuildinfo` appeared in the diff; add `*.tsbuildinfo` to `.gitignore`.

**4.7 Deleting files is easy to forget in an amend chain**
- Removing a file from the index (`git rm --cached`) plus `.gitignore` keeps "one commit = one slice" honest.

---

## 5. Repository hygiene traps (third-party work)

**5.1 Never build in the frozen reference clone** — install in a copy, keep the reference byte-identical, so
"the commit you read" and "the commit you ran" are provably the same.

**5.2 "Small diff" needs a fork or a patch to exist at all** — a slice on a local branch has a commit hash no
reader can resolve; export a patch or push a fork before claiming a commit in a document.

**5.3 Rollback must be tested, not designed** — the test here: revert in a scratch branch, confirm the tree is
identical to upstream, confirm it still builds. Also check the *data* consequence: this slice is purely additive
and never touches the storage contract, which is what makes the revert harmless (A3 risk R4).

**5.4 Tests can pass while the feature is wrong** — 20/20 green, and the headline number was still a false
statement. Green tests prove the code does what the tests say, nothing more; the peer review found what the
tests encoded as truth.

---

## 6. Course-delivery traps

**6.1 One counting basis per document** (see 2.4) and one name per thing: calling the same dataset "the
course-library snapshot" in one place and "the third-party JSON" in another reads as re-litigating a settled
decision.

**6.2 Never re-add what the user deleted** — including via "roll back to the previous version": check `git log`
for their newer commits first. Git is the backup; no `.backup-` files.

**6.3 Redaction must cover binaries and stored outputs** — `git grep` misses PDFs; a notebook stores absolute
paths inside *outputs*. Scan text **and** extract text from every committed PDF; look for stored home paths in
`.ipynb` files.

**6.4 Text that will be rendered has an escaping budget** — emoji print as 「（表情）」; ≥5-column tables degrade;
`--title " "` suppresses the filename header in `md2pdf.py`; `①` inside a fenced code block prints as tofu
(Menlo has no CJK).

---

## 7. Process traps (how the work was organised)

**7.1 Don't stop at the first green** — the first build "failure" was environmental; the first lint "failure" was
mine. Both matter, and they needed opposite responses.

**7.2 Keep the failed first attempt** — the first end-to-end fixture was wrong; the log that shows *why* is more
useful than the corrected run alone.

**7.3 Check the fixture before blaming the code** — twice, the "bug" was a badly chosen test input (clashing
courses; a slot-string comparison). The diagnostic path: read what the app *actually* holds (dump
`localStorage`) before theorising.

**7.4 A tool's "clean install" is a claim** — `hermes verify` detected `npm install`, which this machine breaks.
Read the recipe it chose before trusting its verdict.

**7.5 Write the pitfall down while it is fresh** — this file exists because that did not happen the first time.

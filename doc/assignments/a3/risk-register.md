# A3 — Risk Register

Course **Intelligent Software Engineering**, UCAS, 2026 autumn term · Platform <https://learn.spaiq.ai>
Subject: third-party repository **UCAS-course-planner**, commit `68e7080503084a41f42db6e0e9ff94c0e9ef2f19` (`ver 1.4`, 2026-09-01), investigated read-only.
Requirement satisfied: A3 **"Identify three risks; compare two responses to one in an ADR"** (`课程材料/ISE-A3_Repository_Investigation_and_Reproducible_Build_English.md` line 19; deliverables line 26).
Every claim below is traceable to a file path + line number or to a raw log under `doc/assignments/a3/evidence/logs/`. Nothing is estimated; counts were produced by `grep`/`python3` over the frozen checkout on 2026-10-05.

Legend for **Judgement**: **Occurred** = already observable in the frozen commit or in the recorded run; **Latent** = not triggered yet under the recorded path but reachable without any code change by the caller/operator.

## Summary

| ID | Risk | Judgement | Primary evidence |
| --- | --- | --- | --- |
| R1 | Build chain is coupled to a hosted platform (`vinext` + OpenAI Sites + Cloudflare) | Occurred | `vite.config.ts:1,5,10,45,52-58`; `.openai/hosting.json`; `05-build.log:46-48` |
| R2 | One 1879-line component carries all logic; no safe change boundary | Occurred | `app/page.tsx` (1879 lines / 63 419 B); `package.json:8-14`; `06-lint.log:10` |
| R3 | Course data is a static snapshot committed into the repo | Latent | `public/data/courses.json` (1 524 809 B / 2077 records); `app/page.tsx:563,69` |
| R4 | Persistence is `localStorage`-only with no version-migration path | Latent (silent-loss path already Occurred in code) | `app/page.tsx:112,578,587-600,619-631` |
| R5 | Host/outside-the-repo environment state decides whether a "clean" build is possible | Occurred | `01-npm-install.log:7` vs `02-build.log:37`; `03-install-plugin.log:6`; `04-npm-ci.log:5` |

---

## R1 — Build chain is coupled to a hosted platform (`vinext` + OpenAI Sites + Cloudflare)

**Phenomenon.** The build is not a plain Vite/Next build. `vite.config.ts` imports a platform plugin, reads a platform hosting manifest, and conditionally wires Cloudflare D1/R2 bindings; the production runtime is the beta package `vinext`. A consumer cannot build the repository without that exact plugin set, and the platform itself warns it cannot statically classify the app's routes.

**Evidence.**
- `vite.config.ts:1` `import { sites } from '@openai/sites-vite-plugin';` — the *first* line of the config depends on a hosting-vendor plugin.
- `vite.config.ts:5` `import hostingConfig from './.openai/hosting.json';` and `vite.config.ts:10` `const { d1, r2 } = hostingConfig;` — build topology is driven by a platform manifest.
- `.openai/hosting.json` (31 B) = `{"d1": null, "r2": null}` — the binding switches `vite.config.ts:18` (`d1_databases`) and `:27` (`r2_buckets`) are **present in code but disabled in data**. `vite.config.ts:7-8` also carries a placeholder UUID `00000000-0000-4000-8000-000000000000` used as `database_id` at `:23`, i.e. the config is scaffolded for a platform-provisioned database that this checkout does not have.
- `vite.config.ts:52-58` the plugin stack is `[vinext(), sites(), cloudflare({...})]`; `:45` dynamically imports `@cloudflare/vite-plugin`, and `:16` sets `main: 'vinext/server/fetch-handler'`.
- `package.json:34` `"vinext": "1.0.0-beta.5"` sits in **`dependencies`** (not devDependencies) — the production server is a beta artifact (confirmed running in `07-start.log:10-12`).
- `package.json:37,39,40,52` the four modules the config imports at load time (`@cloudflare/vite-plugin`, `@openai/sites-vite-plugin`, `@tailwindcss/postcss`, `wrangler`) are all **devDependencies** — so the build fails outright if dev deps are absent (`02-build.log:12,20,28,37`).
- `05-build.log:46-48` verbatim: *"Some routes could not be classified. vinext currently uses static analysis and cannot detect dynamic API usage (headers(), cookies(), etc.) at build time. Automatic classification will be improved in a future release."* → the platform cannot even classify `app/page.tsx`'s route; the build succeeds (`:50`, `EXIT=0`) but prints `? Unknown` for `Route (app) /` (`:41-44`).
- `.github/` contains only `ISSUE_TEMPLATE/*` — **no CI workflow**, so this coupled chain is never exercised anywhere except a developer's machine.

**Blast radius.** (a) Portability: the repo can only be built with the vendor plugin set present; R5's failure is a direct downstream effect. (b) Runtime support risk: the server is `1.0.0-beta.5`, so behaviour can change under a patch-level bump. (c) Route classification is unknown/`?` at build time — a deployment whose routing depends on that classification cannot be validated from the build output alone.

**Existing mitigation.** The bindings are nulled in `.openai/hosting.json` (so no live D1/R2 is required) and `vite.config.ts:49-51` special-cases a Codex sandbox for HMR. These make the *current* single-machine build work; none of them reduce the coupling itself. **No mitigation** exists for the vendor/plugin dependency or the beta runtime.

**Judgement: Occurred.** Both the coupling (config imports) and its observable "cannot classify routes" consequence are already present in the frozen commit and in `05-build.log`.

---

## R2 — One 1879-line component carries all logic; no safe change boundary

**Phenomenon.** All product logic — parsing, conflict detection, credit/degree rules, persistence, filtering, and every UI branch — lives inside a single client component, `app/page.tsx`. There is no logic module and no test of any kind, so a change cannot be made safely.

**Evidence (size / structure).**
- `app/page.tsx`: **1879 lines / 63 419 B** (`wc -l`, `ls -l`). `lib/` contains exactly one file, `lib/utils.ts` (**169 B / 6 lines**), whose entire body is the shadcn helper `cn()` (verified by `cat`). `hooks/` contains exactly one file, `hooks/use-mobile.ts` (**585 B / 21 lines**).
- `app/page.tsx:3-21` imports **only** `react` and `lucide-react`. It does **not** import `lib/utils.ts` or `hooks/use-mobile.ts`; those two files are referenced only by unused `components/ui/*` scaffolding (e.g. `components/ui/button-group.tsx:5` `import { cn } from '@/lib/utils'`). So the page's logic has **zero extracted surface**.
- The page declares **41 `function`s** — **34 at top level** (`grep -c '^function '` → 34) plus **7 mutation handlers nested inside the component** (`:809 addCourse`, `:825 removeCourse`, `:835 toggleDegree`, `:845 updateEnglishMode`, `:853 resetPlan`, `:864 downloadBackup`, `:891 restoreBackup`). The top-level set is the whole domain core: `creditFromValue` (`:208`), `parseWeeks` (`:403`), `parsePeriods` (`:416`), `intersects` (`:427`), `hasSlot` (`:438`), `coursesConflict` (`:447`), `conflictsWithPlan` (`:464`), `toneForCourse` (`:521`), and the degree predicates `isCoreCourse` (`:384`) / `isProfessionalCourse` (`:388`). The fact that the 7 state-mutating handlers are *nested in the component body* while the rules sit *outside* it is itself the shape of the missing boundary. `hooks/use-mobile.ts` (**585 B / 21 lines`) is likewise never imported by the page.

**Evidence (concentration — counts over `app/page.tsx`, measured 2026-10-05).**

| Token | Occurrences | Lines |
| --- | --- | --- |
| `useState` | 21 | 21 |
| `useMemo` | 14 | 14 |
| `useEffect` | 3 | 3 |
| `useCallback` | 0 | 0 |
| `localStorage` | 4 | 4 |
| `学位课` | 19 | 17 |
| `冲突` | 9 | 9 |

21 `useState` calls in one component is the concrete measure of "no boundary": pure rules and UI state are interleaved in the same function scope, so extracting any rule means first untangling state that references it (e.g. the conflict rule `coursesConflict` is consumed by the state-derived memo `conflicts` at `app/page.tsx:661-668`, and by the filter at `:774`).

**Evidence (verification is absent).**
- `package.json:8-14` scripts are `dev / build / start / lint / format` — **there is no `test` script**.
- `06-lint.log:10` verbatim: `Finished in 2.6s on 5 files with 208 rules using 8 threads.` → the linter only sees **5 files**; the 1879-line logic file is reported as clean (`06-lint.log:9` `Found 0 warnings and 0 errors.`) but a lint pass says nothing about behavioural correctness.
- The only end-to-end verification recorded is `08-e2e.log`, which works by **injecting a plan through `localStorage` and letting the app re-render** (`08-e2e.log:3`), requiring a full build + live server (`05`/`07`). There is no unit-level way to check `coursesConflict` in isolation.

**Blast radius.** Any fix, however small, must be made inside a 1879-line/63 KB file with no test to catch regressions and a linter that inspects only 5 files. The A3 brief requires exactly the opposite — *"establish a safe change boundary"* (A3 doc line 11) — and the follow-on assignment cuts a bounded slice from this code, which makes an unverifiable one-shot edit the highest-probability way to break the app.

**Existing mitigation.** `lib/utils.ts` and `hooks/` exist as empty-ish scaffolding, so an extraction target directory already exists. `06-lint.log` and `08-e2e.log` give *whole-app* smoke checks. **No mitigation** for the missing per-rule tests or for the concentration itself.

**Judgement: Occurred.**

---

## R3 — Course data is a static snapshot committed into the repo

**Phenomenon.** The entire course catalogue is a JSON file committed to the repository and fetched from same origin at runtime. It carries time-varying fields (enrolment limit / enrolled count), but the file has no capture timestamp, no hash, and no freshness check — so any conclusion drawn from it silently ages.

**Evidence.**
- `public/data/courses.json`: **1 524 809 B (1.52 MB) / 2077 records / 16 fields**, verified by `python3 -c 'json.load(...)'`. Field set: `code, academy, name, englishName, property, level, discipline, hoursCredits, capacity, selected, teachingMode, examMode, leadProfessor, teachers, campus, sessions`.
- **All 2077 records carry the volatile fields** `capacity` and `selected`. Measured distributions: `selected` takes only 4 distinct values `{0, 1, 2, 118}`; 10 courses have `selected > 0`; the three at 118 are the public-required courses (`180213010108MB001H-14 自然辩证法概论` 118/310, `180213030500MB001H-14 新时代中国特色社会主义理论与实践` 118/245, `180096120400PB001H-05 学术道德与学术写作规范-通论` 118/300). `capacity == 0` (i.e. **not recorded**) for **99** courses.
- The app reads it from a path with no version/date: `app/page.tsx:563` `fetch('/data/courses.json')`, then `app/page.tsx:566` `normalizeCourse`. There is no query string, no `If-None-Match`, no timestamp assertion anywhere in the page.
- `app/page.tsx:69` `capacity?: number;` is the **only** occurrence of `capacity` in the whole file (verified by `grep -n capacity app/page.tsx` → single hit). The `selected` field is likewise never read. Consequence: the app itself never renders remaining seats, so it cannot *display* a stale seat count — but a downstream consumer of the same file that does the natural `remaining = capacity - selected` will (a) see `0 - 0 = 0`, i.e. **"full"**, for the 99 courses that actually mean *"not recorded"*, and (b) see the 118-seat courses as barely-touched once enrolment moves.
- Same-origin risk already documented for the *sibling* data source: A1 brief, `doc/assignments/a1/A1-brief-en-2026-09-28.md:181` — *"Snapshots go stale: the enrolled numbers crawled on 9-05 and those crawled on 9-15 are different (10 days apart). The system cannot know by itself that the data is stale, only by stating the capture time in the output"*, and `:190` — *"Treating an old snapshot as 'current': it would treat an already-full section as having places left."* A1 froze its S2 snapshot on **2026-09-27**; this file is the same class of snapshot, committed without that discipline. `public/data/README.md:23` only says *"please verify accuracy and redistribution rights before publishing or updating."*

**Blast radius.** Every course-derived conclusion — time conflicts, credit totals, degree-eligibility, campus/semester filtering — is computed from an unversioned snapshot. Two failure modes: (i) **staleness** — the 2027 catalogue is a different file with no signal that the old one is out of date; (ii) **semantic** — treating `capacity == 0` as "full" instead of "unknown" (99/2077 ≈ 4.8 % of records).

**Existing mitigation.** `public/data/README.md:21` documents the schema and `README.md:135` warns to re-validate with official data before a new academic year. **No mitigation** for capture time, hash, or a freshness assertion in code.

**Judgement: Latent.** Nothing in the recorded run is *wrong today* (0 courses are actually full by the data: `capacity>0 && capacity-selected<=0` → 0 records), but the file is already stale relative to any live term and the `capacity == 0` ambiguity is present now.

---

## R4 — Persistence is `localStorage`-only with no version-migration path

**Phenomenon.** The user's whole plan lives in one `localStorage` key. On read, the app accepts exactly one schema version; anything else — a future version, a truncated value, or malformed JSON — makes it **silently discard the entire saved plan**, with no message and no backup.

**Evidence.**
- `app/page.tsx:112` `const PLAN_STORAGE_KEY = 'ucas-graduate-course-planner-v3';` — note the **`-v3` in the key name while the accepted payload version is `1`** (below); the two version numbers do not move together.
- Read path: `app/page.tsx:567` `const stored = window.localStorage.getItem(PLAN_STORAGE_KEY);` … `:578` `if (parsed.storageVersion === 1) { … accept … }`.
- Reject path: `app/page.tsx:587-593` the `else` branch runs `setPlan([])` and clears `degreeCodes`, `englishPlan`, `studentType`, `selectedDiscipline` — **a full silent wipe with no `setMessage`**. The `catch` at `:594-600` is a byte-for-byte repeat of the same five clears, again with no message.
- Write path: `app/page.tsx:619-631` writes `{ storageVersion: 1, plan, degreeCodes, englishPlan, studentType, selectedDiscipline }`. Only version `1` is ever produced.
- Other touch points: `app/page.tsx:854` and `:1524` both `window.localStorage.removeItem(PLAN_STORAGE_KEY)` (explicit "clear" actions — also destructive and unversioned).
- There is no export-side migration reader: the only version constant in the file is the `=== 1` literal at `:578` (grep `storageVersion` → lines 571, 578, 624 only).

**Blast radius.** A single future change to the payload shape (e.g. bumping to `storageVersion: 2`, or the `v3`→`v4` key rename the key name already invites) makes **every** returning user's saved plan vanish on their next page load, silently — they will see an empty planner and a success-looking first-run screen. Malformed/partially-written `localStorage` (quota, a half-finished tab close) hits the same path.

**Existing mitigation.** The app offers a **manual JSON download/restore** (`README.md:103` "方案仅保存在浏览器本机，可下载 JSON 备份或恢复备份"; restore handler around `app/page.tsx:905-913`), so a user *who has exported* can recover. There is **no automatic** backup, no migration, no warning on reset, and no `try` that preserves the raw string before overwriting.

**Judgement: Latent for data loss, Occurred for the silent-reset code path.** The wipe code already exists and is reachable today by any non-`1` value; it does not fire under the recorded happy path only because the app writes nothing but version `1`.

---

## R5 — Host environment state decides whether a "clean" build is possible

**Phenomenon.** A naive `npm install` on this machine **succeeds** (exit 0) while silently skipping every devDependency, which then makes `npm run build` fail with a *module-not-found* on a config import. The failure looks like a broken repository but is entirely a host-level npm setting — and it cannot be seen from inside the repo.

**Evidence.**
- `01-npm-install.log:3,7` command `npm install --registry=… --no-audit --no-fund` → `added 513 packages in 33s`, `:8` `EXIT=0`. Success, no warning.
- `02-build.log:12,20,28` three `[UNRESOLVED_IMPORT]` on `vite.config.ts` (`@openai/sites-vite-plugin`, `@tailwindcss/postcss`, `@cloudflare/vite-plugin`), then `:36-47` `failed to load config … Error [ERR_MODULE_NOT_FOUND]: Cannot find package '@openai/sites-vite-plugin'`, `:52` `EXIT=1`, `:49` `real 0m3.840s`.
- `03-install-plugin.log:2,6` `npm install --save-dev @openai/sites-vite-plugin@0.2.0` → `up to date in 4s` — a **no-op**: the package was already in `package-lock.json`, it had merely been omitted from the tree, which is why the "obvious" fix changes nothing.
- `04-npm-ci.log:4-5` records the cause verbatim: `前置: 从冻结克隆件恢复原始 package-lock.json，删除 node_modules` / `环境陷阱: 本机 npm config omit=dev（故显式 --include=dev）`; the corrected install adds **560** packages (`:8`) vs the naive **513** (`01-npm-install.log:7`) — a 47-package gap, all dev.
- `05-build.log:53` after the fix: `real 0m15.526s`, `:56` `EXIT=0`. Same repo, same commit — the only change was host npm config plus restoring the frozen lock file.
- `package.json:39` pins the needed package as `"@openai/sites-vite-plugin": "^0.2.0"` (a devDependency) while `vite.config.ts:1` imports it unconditionally — so dev deps are load-bearing for the build, yet an `omit=dev` host removes them invisibly.

**Blast radius.** Reproducibility of the build depends on a setting stored **outside the repository** (`npm config omit`). Any consumer — a grader, CI, a teammate — on a host with `omit=dev` gets a false "this repo is broken" signal, and the on-disk `node_modules` differs by 47 packages with no in-repo indicator.

**Existing mitigation.** The frozen `package-lock.json` (351 463 B) plus the recorded `npm ci --include=dev` command (`04-npm-ci.log:3`) fully removes the trap once known; `doc/assignments/a3/reproduction-guide.md` §4 documents it. **No mitigation inside the repo** — nothing in `package.json`/`README`/CI guards against a host `omit=dev` (there is no CI at all, see R1).

**Judgement: Occurred** (it happened on the first recorded run, `02-build.log:52 EXIT=1`).

---

## Traceability index

| Risk | Files / lines | Logs |
| --- | --- | --- |
| R1 | `vite.config.ts:1,5,7-8,10,18,23,27,45,52-58`; `.openai/hosting.json`; `package.json:34,37,39,40,52`; `.github/ISSUE_TEMPLATE/*` | `05-build.log:41-50`, `07-start.log:10-12` |
| R2 | `app/page.tsx` (1879 lines/63 419 B), `:3-21,69,208,384,388,403,416,427,438,447,464,661-668,774,835`; `lib/utils.ts` (169 B); `hooks/use-mobile.ts` (585 B); `package.json:8-14`; `components/ui/button-group.tsx:5` | `06-lint.log:9-10`, `08-e2e.log:3` |
| R3 | `public/data/courses.json` (1 524 809 B/2077/16 fields, `capacity`,`selected`); `app/page.tsx:69,563,566`; `public/data/README.md:21,23`; `README.md:135`; `A1-brief-en-2026-09-28.md:181,190` | — (static-file analysis) |
| R4 | `app/page.tsx:112,567,570-578,587-600,619-631,854,1524` | — (static-file analysis) |
| R5 | `package.json:39`; `vite.config.ts:1` | `01-npm-install.log:3,7-8`; `02-build.log:12,20,28,36-47,52`; `03-install-plugin.log:6`; `04-npm-ci.log:4-5,8`; `05-build.log:53,56` |

# A3 — Reproduction Guide and Environment Lock

Course **Intelligent Software Engineering**, UCAS, 2026 autumn term · Platform <https://learn.spaiq.ai>
Subject: third-party repository **UCAS-course-planner** (read-only investigation, not modified or installed into this repo).
Guide generated 2026-10-05. Every command and number below is transcribed from the raw logs in
`doc/assignments/a3/evidence/logs/01-npm-install.log` … `08-e2e.log`; nothing is estimated.

---

## 1. Conclusion (one sentence)

The repository **can be reproduced cleanly on this machine**, but **only after neutralising a host-level
npm setting (`omit=dev`) and restoring the frozen `package-lock.json`** — the first, naive `npm install`
succeeds, silently omits every devDependency, and makes the build fail in a way that *looks like a broken
repository* but is purely an environment misconfiguration.

---

## 2. Environment lock

| Item | Frozen value | Source |
| --- | --- | --- |
| Commit | `68e7080503084a41f42db6e0e9ff94c0e9ef2f19` — message `ver 1.4`, committed 2026-09-01 13:41:53 +0800 | `08-e2e.log` line 1; frozen checkout |
| Repository | third-party `UCAS-course-planner` (do not modify; contains its own `node_modules`) | frozen checkout |
| License | **MIT** — `LICENSE`: "Copyright (c) 2026 HMBlankcat and contributors" | frozen checkout |
| Language | **TypeScript** (`tsconfig.json`, `*.ts` / `*.tsx`) | frozen checkout |
| Runtime | **node v22.23.2 / npm 10.9.8 / Darwin x86_64** | `01-npm-install.log` line 4 |
| `engines.node` | `>=22.13.0` | `package.json` |
| Package manager | npm; dependency lock = `package-lock.json` (must be the **original frozen** file for `npm ci`) | `package.json`, `04-npm-ci.log` line 4 |
| Key dependency | `vinext` **1.0.0-beta.5** (dependency) | `package.json` |
| Key devDependency | `vite` **8.0.13**, `@openai/sites-vite-plugin` **^0.2.0**, `@cloudflare/vite-plugin` **1.37.1**, `@tailwindcss/postcss` **4.2.1** | `package.json`; Vite version echoed in `05-build.log` line 10 |
| Toolchain | `oxlint` 1.76.0 (lint), `oxfmt` 0.61.0 (format), `wrangler` 4.92.0 | `package.json` |
| npm scripts | `dev`, `build`, `start`, `lint`, `format` — **no `test` script** | `package.json` |
| Config of note | `vite.config.ts` top-level imports `@openai/sites-vite-plugin` (a **devDependency**); `.openai/hosting.json` = `{"d1": null, "r2": null}` | frozen checkout |

---

## 3. Commands and measured results

| # | Command | Expected | Measured result (verbatim from log) | Log |
| --- | --- | --- | --- | --- |
| 1 | `npm install --registry=https://registry.npmmirror.com --no-audit --no-fund` | all deps installed | `added 513 packages in 33s` · `EXIT=0` — **devDependencies silently skipped** (trap, §4) | `01` |
| 2 | `npm run build` | build succeeds | `EXIT=1` · `ERR_MODULE_NOT_FOUND: Cannot find package '@openai/sites-vite-plugin'` · `real 0m3.840s` | `02` |
| 3 | `npm install --save-dev @openai/sites-vite-plugin@0.2.0` | add the missing package | `up to date in 4s` · `EXIT=0` — **no-op**; the package was already in the lock, only omitted from the tree | `03` |
| 4 | restore frozen `package-lock.json` + `rm -rf node_modules` + `npm ci --include=dev --registry=https://registry.npmmirror.com --no-audit --no-fund` | clean install **including dev** | `added 560 packages in 58s` · `EXIT=0` (`real 0m58.081s`, `user 0m19.524s`, `sys 0m27.676s`) | `04` |
| 5 | `npm run build` | build succeeds | 5 stages: `2.10s` / `292ms` / `1.12s` / `2.98s` / **`1.06s`** → total `real 0m15.526s`, `EXIT=0`; prints a **non-fatal** route-classification warning | `05` |
| 6 | `npm run lint` | lint clean | `Found 0 warnings and 0 errors.` · `Finished in 2.6s on **5 files** with 208 rules using 8 threads.` · `EXIT=0` | `06` |
| 7 | `npm run start` (`vinext start`) | production server up | `vinext start (port 3000)` · `[vinext] Production server running at http://0.0.0.0:3000` | `07` |
| 8 | End-to-end path (inject plan via `localStorage`, let the app render) | conflict detection fires | positive: `badge='3 处时间冲突'`, `conflictCellLabels=3`; negative control: `badge='无时间冲突'`, `conflictCellLabels=0` | `08` |
| 9 | `curl -i http://127.0.0.1:3000` (liveness) | HTTP 200 | **HTTP 200 x3, ~0.012 s each; headers + page HTML captured** | `09-http-health.log` |

Build-stage detail from `05-build.log` (the standalone `1.06s` figure is the final **ssr environment** step):

| Stage | Modules transformed | Time |
| --- | --- | --- |
| [1/5] client references | 225 | 2.10s |
| [2/5] server references | 104 | 292ms |
| [3/5] rsc environment | 222 | 1.12s |
| [4/5] client environment | 1903 | 2.98s |
| [5/5] ssr environment | 110 | 1.06s |

---

## 4. Environment pitfall: `omit=dev` (the core of this guide)

**What happened.** On this machine `npm config get omit` returns **`dev`**. With `omit=dev` set, npm
treats `devDependencies` as omitted from the install tree: `npm install` **exits 0 and reports success**
(`added 513 packages in 33s`, log `01`) while never writing the devDependencies into `node_modules`.

**Why the build then fails.** `vite.config.ts` imports `@openai/sites-vite-plugin` at the top of the file
(line 1), and that package is a **devDependency**. Vite's ESM loader resolves it at config-load time and
fails: `ERR_MODULE_NOT_FOUND: Cannot find package '@openai/sites-vite-plugin'` (log `02`). The output also
flags the other unfetchable dev imports (`@tailwindcss/postcss`, `@cloudflare/vite-plugin`). The failure
message points at `vite.config.ts`, so it *reads* as a broken repository — it is not.

**Why `npm install <pkg>` did not fix it.** Log `03` requested the package explicitly and got
`up to date in 4s`. The package was already present in `package-lock.json` at the correct version, so npm's
tree check considered the lock satisfied and declined to install anything — a false negative caused by the
same `omit=dev` filter.

**How to self-diagnose (before blaming the repo).**
```bash
npm config get omit          # -> dev  (the culprit)
npm config get include       # cross-check
cat .npmrc 2>/dev/null       # a project-level .npmrc can also set it
ls node_modules/@openai/sites-vite-plugin  # missing => the trap is active
```
Rule of thumb: `npm install` "succeeds" but a devDependency import fails at build → suspect `omit=dev`
first, not the source tree.

**How to avoid it.**
1. Neutralise it once: `npm config delete omit` (or delete the `omit=dev` line from the relevant `.npmrc`), **or**
2. Override per command: add `--include=dev` (used in log `04`).
Then verify the devDependency actually landed: `ls node_modules/@openai/sites-vite-plugin`.

**Why it belongs in the record.** This is a **host-environment deviation, not a repository defect**. A
grader on a clean machine (no `omit=dev`) would see the successful path directly; documenting the trap is
what makes the reproduction honest and repeatable.

---

## 5. Step-by-step reproduction checklist (grader-facing, copy-pasteable)

Prerequisite: Node.js **>= 22.13.0** (measured with **v22.23.2**; npm 10.9.8).

```bash
# 1. Obtain the frozen commit (do not modify the third-party working tree)
#    commit 68e7080503084a41f42db6e0e9ff94c0e9ef2f19  ("ver 1.4", 2026-09-01)

# 2. Confirm you are on the frozen checkout and the tree is clean
git -C <UCAS-course-planner> status --short        # expect: clean; package-lock.json present

# 3. Neutralise the host trap (see §4)
npm config get omit                                 # if it prints "dev", fix it:
npm config delete omit                              #   OR keep it and add --include=dev in step 5

# 4. Start from a pristine dependency state with the ORIGINAL lockfile
#    (restore package-lock.json from the frozen clone first if a prior run rewrote it)
rm -rf node_modules

# 5. Clean install INCLUDING devDependencies  -> expect "added 560 packages in 58s", EXIT 0  (log 04)
npm ci --include=dev --registry=https://registry.npmmirror.com --no-audit --no-fund

# 6. Verify the previously-missing devDependency is now present
ls node_modules/@openai/sites-vite-plugin           # expect a populated directory

# 7. Build -> expect EXIT 0, real ~15.5s; route-classification warning is NON-fatal  (log 05)
npm run build

# 8. Lint -> expect "0 warnings and 0 errors", ~2.6s on 5 files  (log 06)
npm run lint

# 9. Start the production server -> expect http://0.0.0.0:3000  (log 07)
npm run start

# 10. Liveness check (NOT captured in logs 01-08; re-capture if you need the number — see §6)
curl -i http://127.0.0.1:3000
```

Optional end-to-end confirmation (log `08`): with the server running, inject one plan into
`localStorage` key `ucas-graduate-course-planner-v3` and let the app render; three courses sharing a slot
must yield `3 处时间冲突` / 3 conflict cell labels, and a no-shared-slot control must yield `无时间冲突` / 0.

**Deviation note for step 5.** `--registry=https://registry.npmmirror.com` and `--include=dev` are both
**departures from a pristine `npm ci`**. The mirror is used for speed in mainland China; the dev-include
flag is required only because of the §4 trap. On a clean host with no `omit=dev`, plain `npm ci` should
suffice.

---

## 6. Known non-reproducible / unverified points

- **No test script exists.** `package.json` defines only `dev`, `build`, `start`, `lint`, `format`. **No
  test suite was run and none can be run from this repository.** Do not claim a green test run.
- **The mirror rewrites the lockfile.** `npm ci --registry=https://registry.npmmirror.com` rewrites the
  `resolved` URLs inside `package-lock.json`; after install `git status` shows **` M package-lock.json`**.
  The lock is therefore no longer byte-identical to the frozen artifact. For a bit-exact lock, use
  `--registry=https://registry.npmjs.org` (or restore the lock from the frozen clone after installing).
  This deviation is kept for speed and is disclosed here.
- **`--include=dev` is not part of the repository's own instructions.** It is a compensation for the host
  `omit=dev` setting (§4), not a repo requirement.
- **Lint covers only 5 files.** `npm run lint` = `oxlint` with default configuration; `0 warnings / 0 errors`
  is scoped to those 5 files, **not** a full-repo guarantee.
- **Build route classification is unknown.** `05-build.log` prints `Some routes could not be classified …
  cannot detect dynamic API usage`; the `/` route is listed as `? Unknown`. This is a warning, not a failure
  — the build still exits 0 — so route behaviour must not be inferred from the build output.
- **HTTP 200 liveness — verified after the fact.** `09-http-health.log` records three consecutive `HTTP 200`
  responses (~0.012 s each) plus the `curl -i` headers and the served HTML. An earlier `0.14 s` figure came from
  an interactive check that was never written to a file, so it is deliberately not cited anywhere in these
  documents. With this log added, no measurement in this guide is left unverified — the lesson being that a
  number without a log is not evidence.
- **`vinext` is a beta** (`1.0.0-beta.5`); its build/start behaviour may drift from this record over time.
- **The third-party checkout already ships a large `node_modules`** and build artifacts (`.next`, `dist`);
  these are not part of the frozen source and must never be committed.

---

*Provenance: all measurements from `doc/assignments/a3/evidence/logs/01-npm-install.log` … `08-e2e.log`
(folder `doc/assignments/a3/evidence/`). Commit hash, license text, and language were read directly from the
frozen third-party checkout, which was inspected read-only and left unchanged.*

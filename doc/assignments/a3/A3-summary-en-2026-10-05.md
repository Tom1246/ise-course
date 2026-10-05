# Platform submission summary — ISE-A3

Posted on learn.spaiq.ai. The requirement is **150-300 words**; the count below is produced mechanically by
`python3 scripts/count_words.py`, not by eye.

## English (submitted)

<!-- SUMMARY-EN-START -->
A3 investigates an unfamiliar third-party repository through execution rather than reading: HMBlankcat's
UCAS-course-planner, frozen at commit 68e7080 (ver 1.4, MIT, TypeScript). The deliverable is an environment lock
and reproduction guide, an architecture and call-path map, one end-to-end path reconstructed with a negative
control, a risk register, and an ADR on where a change may safely land.

Four findings came out of running it. First, the repository did not build at first, and the cause was not the
repository: this machine's npm configuration sets omit=dev, so the clean install silently skipped a
devDependency that the build configuration imports. Recording the corrected command, with the environment trap
named, turned a dead end into the most valuable page of the guide. Second, the application is one 1,879-line
component: components/ holds sixty UI primitives and zero application components, there is no test script, and
lint covers five files. Third, the build chain rests on a beta toolchain (vinext 1.0.0-beta.5) plus a plugin
whose absence breaks the build outright. Fourth, the conflict predicate at line 447 is the same three-condition
rule as A2's decision table, reached independently, which confirms that claim rather than merely restating it.

The end-to-end run injects a plan through the app's own storage contract and reloads: three courses sharing
Thursday periods 10-12 produce "3 clashes" and three highlighted cells, while a control plan without a shared
slot produces none. Limits are stated: no differential test across all 2,077 courses, and the interactive path
was read, not exercised.
<!-- SUMMARY-EN-END -->

Repository: https://github.com/Tom1246/ise-course (tag `a3-v1`)

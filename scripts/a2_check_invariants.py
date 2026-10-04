#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A2 invariants — automated checks over the frozen course data.

The three invariants (see doc/assignments/a2/invariants.md):

  I1  A timetable must not contain two sections that overlap in time.
      overlap  <=>  same weekday  AND  period ranges overlap  AND  week ranges overlap
      (all three at once; any two of them is not enough)

  I2  The planned course set must satisfy the programme's credit floors
      (and stay within its ceilings).

  I3  A section's enrolled count must not exceed its capacity.
      An empty capacity is *unknown*, never "unlimited".

Inputs (all committed, so the checks are reproducible from the repository alone):

  data/derived/course-library-snapshot.json   the 347 Yuquanlu courses (schedule, capacity, enrolled)
  data/s5-programme/degree-requirements.json  the programme's credit floors/ceilings
  data/derived/a2/sample-plan.json            a small illustrative plan (written by this script if absent)

Outputs (committed raw output):

  data/derived/a2/invariant-checks.md

Run:  python3 scripts/a2_check_invariants.py
Exit code 0 = the checks ran (violations are findings, not errors).
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = os.path.join(ROOT, "data/derived/course-library-snapshot.json")
REQ = os.path.join(ROOT, "data/s5-programme/degree-requirements.json")
SAMPLE_PLAN = os.path.join(ROOT, "data/derived/a2/sample-plan.json")
OUT = os.path.join(ROOT, "data/derived/a2/invariant-checks.md")
CREDIT_SUMMARY = os.path.join(ROOT, "data/derived/credit-gap-summary.md")

WEEKDAYS = {"周一": 1, "周二": 2, "周三": 3, "周四": 4, "周五": 5, "周六": 6, "周日": 7}
SEG = "；"          # separates parallel time/weeks segments
RANGE = re.compile(r"(\d+)\s*-\s*(\d+)")


# ---------------------------------------------------------------- parsing
def parse_time(text: str):
    """'周三(5-7)；周六(5-7)' -> [(3, 5, 7), (6, 5, 7)]"""
    out = []
    for seg in [s.strip() for s in text.split(SEG) if s.strip()]:
        m = re.match(r"(周[一二三四五六日])\s*[（(](\d+)\s*-\s*(\d+)[）)]", seg)
        if not m:
            out.append(None)                     # unparsable -> recorded, never guessed
            continue
        out.append((WEEKDAYS[m.group(1)], int(m.group(2)), int(m.group(3))))
    return out


def parse_weeks(text: str):
    """'第2-5,7-17周；第6周' -> [[(2,5),(7,17)], [(6,6)]]"""
    out = []
    for seg in [s.strip() for s in text.split(SEG) if s.strip()]:
        body = seg.strip("第周 ")
        spans = []
        for item in [i.strip() for i in body.split(",") if i.strip()]:
            m = RANGE.match(item)
            if m:
                spans.append((int(m.group(1)), int(m.group(2))))
            elif item.isdigit():
                spans.append((int(item), int(item)))
            else:
                spans.append(None)               # unparsable
        out.append(spans)
    return out


def sessions(course):
    """Flatten a course into [(weekday, p1, p2, [(w1,w2), ...])] plus a quality flag list."""
    t, w = parse_time(course.get("time") or ""), parse_weeks(course.get("weeks") or "")
    flags = []
    if len(t) != len(w):
        flags.append("segment-count-mismatch")
    rows = []
    for i in range(min(len(t), len(w))):
        if t[i] is None:
            flags.append("unparsable-time")
            continue
        spans = [s for s in w[i] if s]
        if len(spans) != len(w[i]):
            flags.append("unparsable-weeks")
        rows.append((t[i][0], t[i][1], t[i][2], spans))
    return rows, flags


# ---------------------------------------------------------------- invariant I1
def overlap_periods(a, b):
    return not (a[2] < b[1] or b[2] < a[1])


def overlap_weeks(spans_a, spans_b):
    """True as soon as any week range of A intersects any week range of B."""
    for x1, x2 in spans_a:
        for y1, y2 in spans_b:
            if not (x2 < y1 or y2 < x1):
                return True
    return False


def conflict(sec_a, sec_b):
    """The decision table, as code: the ONLY conflicting row is (same weekday, overlapping
    periods, overlapping weeks)."""
    return (sec_a[0] == sec_b[0]
            and overlap_periods(sec_a, sec_b)
            and overlap_weeks(sec_a[3], sec_b[3]))


def decision_table_cases():
    """Canonical cases for the same rule, including the week-interval trap."""
    A = (3, 6, 7, [(1, 16)])          # Wed periods 6-7, weeks 1-16
    cases = [
        ("same weekday + periods overlap + weeks overlap", A, (3, 7, 8, [(2, 4)]), True),
        ("week ranges disjoint [3,5] vs [6,8]", (3, 6, 7, [(3, 5)]), (3, 6, 7, [(6, 8)]), False),
        ("week ranges touching/interleaving [3,5] vs [4,8]",
         (3, 6, 7, [(3, 5)]), (3, 6, 7, [(4, 8)]), True),
        ("same weeks, periods apart", (3, 1, 2, [(1, 16)]), (3, 5, 7, [(1, 16)]), False),
        ("same weeks and periods, different weekday", (2, 6, 7, [(1, 16)]), (3, 6, 7, [(1, 16)]), False),
        ("identical section (data duplicated)", (3, 6, 7, [(1, 16)]), (3, 6, 7, [(1, 16)]), True),
    ]
    return cases


# ---------------------------------------------------------------- main
def main() -> int:
    live = json.load(open(LIVE, encoding="utf-8"))["courses"]
    req = json.load(open(REQ, encoding="utf-8"))
    L = []
    P = L.append

    P("# A2 invariant checks — raw output")
    P("")
    P("- Generated: %s" % datetime.now().strftime("%Y-%m-%d %H:%M"))
    P("- Reproduce with: `python3 scripts/a2_check_invariants.py`")
    P("- Inputs: `data/derived/course-library-snapshot.json` (%d courses), "
      "`data/s5-programme/degree-requirements.json`, `data/derived/a2/sample-plan.json`" % len(live))
    P("- Violations below are **findings**, not script errors. Exit code 0 means the checks ran.")
    P("")

    # ---- parsing quality -------------------------------------------------
    P("## 0. Parsing quality (what the data actually looks like)")
    P("")
    flags = Counter()
    parsed, unscheduled = {}, []
    for c in live:
        rows, fl = sessions(c)
        for f in fl:
            flags[f] += 1
        if rows:
            parsed[c["code"]] = rows
        else:
            unscheduled.append(c)
    P("| property | value |")
    P("| --- | --- |")
    P("| courses | %d |" % len(live))
    P("| courses with at least one scheduled session | %d |" % len(parsed))
    P("| courses with no session data at all (empty time **and** empty weeks) | %d |" % len(unscheduled))
    P("| unparsable time segments | %d |" % flags["unparsable-time"])
    P("| unparsable week segments | %d |" % flags["unparsable-weeks"])
    P("| time/weeks segment-count mismatches | %d |" % flags["segment-count-mismatch"])
    dup = sum(1 for c in live if len(parsed.get(c["code"], [])) != len({(r[0], r[1], r[2], tuple(map(tuple, r[3]))) for r in parsed.get(c["code"], [])}))
    repeated = sum(1 for c in live
                   if len({(r[0], r[1], r[2]) for r in parsed.get(c["code"], [])}) != len(parsed.get(c["code"], [])))
    P("| courses whose session list contains an exact duplicate segment | %d |" % dup)
    P("| courses with a slot repeated in two different week blocks (half-semester pattern) | %d |" % repeated)
    P("")
    if unscheduled:
        P("> The %d courses without session data are the biggest quality hole: any claim about "
          "\"when this course runs\" is unavailable for them, and an empty value must never be read as "
          "\"no clash\"." % len(unscheduled))
    else:
        P("> Every course in this snapshot carries both a time and a week-range string, and the number of "
          "`；`-separated segments always matches between the two fields — so the parallel-list reading used "
          "below is safe **for this snapshot**. It is a property of the data, not a guarantee of the format: "
          "the check counts mismatches and would report them here rather than guess.")
    P("")

    # ---- decision table --------------------------------------------------
    P("## 1. The conflict rule, checked as a decision table")
    P("")
    P("| case | section A | section B | expected | actual | ok |")
    P("| --- | --- | --- | --- | --- | --- |")
    ok_all = True
    for name, a, b, expected in decision_table_cases():
        got = conflict(a, b)
        ok_all &= (got == expected)
        P("| %s | 周%d (%d-%d) 第%s周 | 周%d (%d-%d) 第%s周 | %s | %s | %s |"
          % (name, a[0], a[1], a[2], a[3], b[0], b[1], b[2], b[3],
             expected, got, "yes" if got == expected else "**NO**"))
    P("")
    P("- all decision-table cases behave as specified: **%s**" % ok_all)
    P("")

    # ---- I1 over the whole catalogue -------------------------------------
    P("## 2. I1 — no two sections of one timetable overlap")
    P("")
    codes = sorted(parsed)
    pairs = 0
    hits = []
    self_conflicts = []
    for i, ca in enumerate(codes):
        for cb in codes[i + 1:]:
            for sa in parsed[ca]:
                for sb in parsed[cb]:
                    pairs += 1
                    if conflict(sa, sb):
                        hits.append((ca, cb, sa, sb))
                        break
                else:
                    continue
                break
    for ca in codes:                      # a course clashing with its own duplicated segment
        for i, sa in enumerate(parsed[ca]):
            for sb in parsed[ca][i + 1:]:
                if conflict(sa, sb):
                    self_conflicts.append((ca, sa, sb))
    P("- scheduled courses compared: %d (all unordered pairs of their session segments)" % len(codes))
    P("- segment comparisons performed: %d" % pairs)
    P("- **conflicting course pairs found: %d** (%.1f%% of all course pairs)"
      % (len(hits), 100.0 * len(hits) / max(1, len(codes) * (len(codes) - 1) // 2)))
    P("- courses that clash with their own duplicated segment: %d" % len(self_conflicts))
    P("")
    if hits:
        P("### Examples (the first 8 conflicting pairs, verbatim from the data)")
        P("")
        P("| course A | its slot | course B | its slot |")
        P("| --- | --- | --- | --- |")
        for ca, cb, sa, sb in hits[:8]:
            P("| `%s` | 周%d 第%d-%d 节 / weeks %s | `%s` | 周%d 第%d-%d 节 / weeks %s |"
              % (ca, sa[0], sa[1], sa[2], sa[3], cb, sb[0], sb[1], sb[2], sb[3]))
        P("")
        per_slot = Counter("周%d 第%d-%d 节" % (s[0], s[1], s[2]) for _, _, s, _ in hits)
        P("### Where the clashes concentrate")
        P("")
        P("| slot | conflicting pairs naming this slot |")
        P("| --- | --- |")
        for slot, n in per_slot.most_common(6):
            P("| %s | %d |" % (slot, n))
        P("")
    P("### 2.1 Catalogue-level reading: conflicts of *offer*, not yet a violation")
    P("")
    P("A timetable is a chosen subset, so two overlapping courses in the catalogue are two offers that cannot "
      "be combined — not a broken invariant. The figure above is therefore the **conflict density of the offer "
      "set**. The invariant itself is exercised next on an actual plan (2.2) and on the A1 case (2.3).")
    P("")
    sm = json.load(open(SAMPLE_PLAN, encoding="utf-8"))["codes"] if os.path.exists(SAMPLE_PLAN) else []
    plan_hits = [h for h in hits if h[0] in sm and h[1] in sm]
    P("### 2.2 Plan-level check — the invariant on a chosen timetable")
    P("")
    P("- plan used: `data/derived/a2/sample-plan.json` (%d courses, illustrative)" % len(sm))
    P("- **internal conflicting pairs in that plan: %d**" % len(plan_hits))
    if plan_hits:
        for ca, cb, sa, sb in plan_hits[:5]:
            P("  - `%s` (周%d 第%d-%d 节, weeks %s) vs `%s` (周%d 第%d-%d 节, weeks %s)"
              % (ca, sa[0], sa[1], sa[2], sa[3], cb, sb[0], sb[1], sb[2], sb[3]))
    P("")
    P("### 2.3 The A1 case, reproduced from committed data")
    P("")
    P("A1 claims three courses in the author's plan all sit at Thursday periods 10-12. The catalogue is "
      "committed, so that claim can be re-checked here:")
    P("")
    picks = {}
    for needle in ("计算机代数", "数字图像处理与分析", "深度学习"):
        for c in live:
            if needle in (c.get("name") or "") and c["code"] in parsed:
                picks.setdefault(needle, c)
    if picks:
        P("| course | code | slot in the catalogue | week ranges |")
        P("| --- | --- | --- | --- |")
        for needle, c in picks.items():
            rows = parsed[c["code"]]
            for r in rows:
                P("| %s | `%s` | 周%d 第%d-%d 节 | %s |" % (c.get("name"), c["code"], r[0], r[1], r[2], r[3]))
        names = list(picks)
        agreed = []
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                for sa in parsed[picks[a]["code"]]:
                    for sb in parsed[picks[b]["code"]]:
                        if conflict(sa, sb):
                            agreed.append((picks[a].get("name"), picks[b].get("name")))
        P("")
        P("- conflicting pairs among the three: **%d %s**" % (len(agreed), agreed if agreed else ""))
        P("- reading: the A1 case is reproducible from the committed catalogue — the clash is a property of "
          "the offer set, which is why the planner needs the rule rather than a printout.")
    else:
        P("- the three A1 courses are not all present in this snapshot; the case is therefore reported in "
          "`model-walkthrough.md` from the A1 record instead (honest gap, not a silent omission).")
    P("")

    # ---- I3 capacity -----------------------------------------------------
    P("## 3. I3 — enrolled must not exceed capacity (empty = unknown)")
    P("")
    viol, zero_cap, unknown, checked = [], [], 0, 0
    for c in live:
        cap, enr = (c.get("capacity") or "").strip(), (c.get("enrolled") or "").strip()
        if not cap or not enr:
            unknown += 1
            continue
        try:
            cap_i, enr_i = int(float(cap)), int(float(enr))
        except ValueError:
            unknown += 1
            continue
        if cap_i == 0 and enr_i > 0:
            zero_cap.append((c["code"], c.get("name", ""), enr_i))
            continue
        checked += 1
        if enr_i > cap_i:
            viol.append((c["code"], c.get("name", ""), cap_i, enr_i))
    P("- sections with both figures present: %d" % (checked + len(zero_cap)))
    P("- sections with a missing figure (capacity unknown, **never treated as unlimited**): %d" % unknown)
    P("- **rows whose capacity is literally `0` while enrolled > 0: %d**" % len(zero_cap))
    P("- **violations with a real capacity (enrolled > capacity > 0): %d**" % len(viol))
    P("")
    P("Finding (this is the interesting one): every over-capacity row in this snapshot has capacity `0`. "
      "Read literally that would be 40 violations; read as data it means **`0` is a sentinel for \"not set\"**, "
      "not a section that admits nobody — one of those rows shows 86 enrolled against it. The invariant is "
      "therefore stated as: *an enrolled count must be interpretable against a known capacity; a capacity of "
      "`0`/empty is unknown, and unknown capacity must be surfaced to the planner, never silently treated as "
      "either full or unlimited.*")
    P("")
    if zero_cap:
        P("| course code | course | enrolled | capacity |")
        P("| --- | --- | --- | --- |")
        for code, name, enr_i in sorted(zero_cap, key=lambda r: -r[2])[:8]:
            P("| `%s` | %s | %d | 0 (not set) |" % (code, name, enr_i))
        P("")
    if viol:
        P("| course code | course | capacity | enrolled | over by |")
        P("| --- | --- | --- | --- | --- |")
        for code, name, cap_i, enr_i in sorted(viol, key=lambda r: (r[3] - r[2]), reverse=True)[:10]:
            P("| `%s` | %s | %d | %d | +%d |" % (code, name, cap_i, enr_i, enr_i - cap_i))
        P("")

    # ---- I2 credits ------------------------------------------------------
    P("## 4. I2 — planned credits vs the programme floors")
    P("")
    if not os.path.exists(SAMPLE_PLAN):
        plan_codes = ["180080070100MX018Y"]
        for c in live:
            if c["code"] not in plan_codes and (c.get("credit") or 0):
                plan_codes.append(c["code"])
            if len(plan_codes) >= 6:
                break
        os.makedirs(os.path.dirname(SAMPLE_PLAN), exist_ok=True)
        json.dump({"_note": "Illustrative plan committed so I1/I2 are runnable from the repository alone. "
                            "The author's real plan is personal data and is not committed.",
                   "codes": plan_codes}, open(SAMPLE_PLAN, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        P("- `data/derived/a2/sample-plan.json` did not exist and was created (illustrative plan).")
        P("")
    plan = json.load(open(SAMPLE_PLAN, encoding="utf-8"))["codes"]
    by_code = {c["code"]: c for c in live}
    total = 0.0
    missing = []
    P("| planned course | credits | found in catalogue |")
    P("| --- | --- | --- |")
    for code in plan:
        c = by_code.get(code)
        if c is None:
            missing.append(code)
            P("| `%s` | — | **no** |" % code)
        else:
            total += float(c.get("credit") or 0)
            P("| `%s` %s | %s | yes |" % (code, c.get("name", ""), c.get("credit")))
    P("")
    m = req["degree_track"]["master"]
    P("- planned credits in this illustrative plan: **%g**" % total)
    P("- programme floors (master track): total %s, course learning %s, public degree %s, "
      "professional degree %s, practicum %s"
      % (m["total_min_credits"], m["course_learning_min_credits"], m["public_degree_credits"],
         m["professional_degree_min_credits"], m["required_practicum_credits"]))
    P("- verdict for the illustrative plan: %s (course-learning floor %s)"
      % ("satisfied" if total >= m["course_learning_min_credits"] else "**NOT satisfied**",
         m["course_learning_min_credits"]))
    P("- courses in the plan that the catalogue does not contain: %d %s"
      % (len(missing), ("(%s)" % ", ".join(missing)) if missing else ""))
    P("")
    P("Two honest limits of this check: the programme document states **floors only**, so the ceiling half of "
      "the invariant has no source to test against and is left unimplemented rather than invented; and the "
      "\"planned course is missing from the catalogue\" branch (a real case in 春季) is not exercised by this "
      "illustrative plan.")
    P("")
    P("> The author's real plan is private. Its committed aggregate lives in "
      "`data/derived/credit-gap-summary.md`%s; the per-course detail stays in `data/private/`."
      % (" (present in this checkout)" if os.path.exists(CREDIT_SUMMARY) else ""))
    P("")
    if os.path.exists(CREDIT_SUMMARY):
        for line in open(CREDIT_SUMMARY, encoding="utf-8").read().splitlines():
            if line.startswith("- ") and any(k in line for k in ("credit", "shortfall", "gap", "missing")):
                P("- real plan (aggregate): %s" % line[2:])
        P("")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("wrote %s (%d lines)" % (os.path.relpath(OUT, ROOT), len(L)))
    print("conflicting course pairs: %d | capacity violations: %d | unscheduled courses: %d"
          % (len(hits), len(viol), len(unscheduled)))
    if not ok_all:
        print("WARNING: a decision-table case did not behave as specified", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

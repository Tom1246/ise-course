#!/usr/bin/env python3
"""Rank the saved course plan by two orthogonal orders: deferability and grab urgency.

Usage:
    python3 src/rank_plan_priority.py [--plan <planner-backup.json>]
                                      [--must-take codes.txt | --must-take-from-attribute]

Why two orders
--------------
"Which course matters more" and "which course must be grabbed first" are different questions
and they disagree in the measured data.  A required course can have zero competition, and a
half-credit common course can be full on day one.  The workflow therefore needs two outputs:
a conflict-free study plan, and a submission (grab) order.

Dimensions used here (both measurable):
  1. deferability  -- is the course offered this semester at all?  The official workbooks give
                      the semester per course; a course offered only in this semester cannot be
                      postponed within the year.
  2. grab urgency  -- enrolled / capacity from the public listing, rounded to a remaining count.
  (3.) substitutability -- how many sibling sections share the base course name.

NOT measurable from any source used here: whether the degree programme *requires* the course.
That is a human input; pass it with --must-take, or let the script derive a candidate set from
the course attribute and say so.

Outputs
-------
  raw/private/plan-priority.md               full per-course table  (gitignored -- personal)
  raw/measurements/plan-priority-summary.md  aggregates only        (committed)
"""
import argparse, json, os, re, sys
from collections import Counter, defaultdict

DEFAULT_PLAN = os.path.expanduser("~/Downloads/选课地图-本地备份 (3).json")
OFFICIAL = "raw/sections-snapshot.json"
LIVE = "raw/yuquanlu-live-courses.json"
THIS_SEMESTER = "秋季"
URGENT_RATIO = 0.90
URGENT_LEFT = 3
REQUIRED_ATTRS = {"学科核心课", "专业核心课", "公共必修课", "专业课"}


def load(path, msg):
    if not os.path.exists(path):
        sys.exit(f"[!] missing {path} -- {msg}")
    return json.load(open(path, encoding="utf-8"))


def ratio_and_left(cap, enr):
    try:
        cap, enr = int(str(cap)), int(str(enr))
    except (TypeError, ValueError):
        return None, None
    if cap <= 0:
        return None, None
    return enr / cap, cap - enr


def base_name(name):
    """'数字信号处理原理与应用二班' -> ('数字信号处理原理与应用', '二班')"""
    m = re.match(r"^(.*?)[（(]?([一二三四五六七八九十]+班|慕课|全英文|[A-Z]班)[)）]?$", str(name))
    return (m.group(1), m.group(2)) if m else (str(name), "")


def tier(must, semester_set, urgent):
    """semester_set: frozenset of semesters the code is offered in; empty means unknown."""
    if not semester_set:
        return "PU", ("deferability UNKNOWN -- the course is absent from the official workbooks, "
                      "so no semester is recorded anywhere")
    if semester_set == {THIS_SEMESTER}:
        base, tag = "only this semester", "P"
    elif semester_set == {"春季"}:
        return "PN", ("NOT offered in " + THIS_SEMESTER + " -- must not be planned for this "
                      "semester; needs review against the current plan")
    else:
        base, tag = "offered in both semesters", "Q"
    if not must:
        return "PX", f"not required by the programme; {base}"
    if base.startswith("only"):
        return (("P0" if urgent else "P1"),
                ("required, offered only this semester"
                 + (", at or near capacity -- grab first" if urgent else ", but not contested")))
    return (("P2" if urgent else "P3"),
            ("required, contested" if urgent else "required, not contested")
            + ", but offered next semester too")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default=DEFAULT_PLAN)
    ap.add_argument("--must-take")
    ap.add_argument("--must-take-from-attribute", action="store_true", default=True)
    ap.add_argument("--no-must-take-from-attribute", dest="must_take_from_attribute",
                    action="store_false")
    a = ap.parse_args()

    plan = load(a.plan, "the planner backup holding the saved plan")["plan"]
    official = {c["code"]: c for c in load(OFFICIAL, "run freeze_snapshot.py")["courses"]}
    live_rows = load(LIVE, "run fetch_public_listing.py")["courses"]
    live = {c["code"]: c for c in live_rows}

    siblings = defaultdict(set)
    for r in live_rows:
        b, sec = base_name(r["name"])
        siblings[b].add(sec or "main")

    sem_sets = defaultdict(set)
    for c in official.values():
        if c.get("semester"):
            sem_sets[c["code"]].add(c["semester"])
    # every code the workbooks know about, including 春季-only ones
    for c in load(OFFICIAL, "run freeze_snapshot.py")["courses"]:
        if c.get("semester"):
            sem_sets[c["code"]].add(c["semester"])

    must_codes, must_source = set(), "not provided"
    if a.must_take:
        must_codes = {l.split()[0] for l in open(a.must_take, encoding="utf-8") if l.strip()}
        must_source = f"file {a.must_take}"
    elif a.must_take_from_attribute:
        must_codes = {c["code"] for c in official.values() if c["attribute"] in REQUIRED_ATTRS}
        must_source = "derived from course attribute (a CANDIDATE set, not the degree programme)"

    rows = []
    for p in plan:
        code = p["code"]
        off, lv = official.get(code, {}), live.get(code, {})
        sem = off.get("semester", "") or "(unknown)"
        attr = p.get("attribute") or off.get("attribute", "")
        ratio, left = ratio_and_left(lv.get("capacity") or p.get("capacity"),
                                     lv.get("enrolled") or p.get("enrolled"))
        urgent = (ratio is not None and (ratio >= URGENT_RATIO or (left is not None and left <= URGENT_LEFT)))
        base, sec = base_name(p.get("name", ""))
        rows.append(dict(code=code, name=p.get("name", ""), attr=attr, credit=p.get("credit"),
                         semester=sem, sem_set=frozenset(sem_sets.get(code, set())),
                         cap=lv.get("capacity") or p.get("capacity"),
                         enr=lv.get("enrolled") or p.get("enrolled"),
                         weeks=lv.get("weeks", "") or "(not in any source)",
                         time=lv.get("time", "") or "(not in any source)",
                         ratio=ratio, left=left, sections=sorted(siblings.get(base, [])),
                         must=code in must_codes))

    for r in rows:
        urgent = (r["ratio"] is not None and
                  (r["ratio"] >= URGENT_RATIO or (r["left"] is not None and r["left"] <= URGENT_LEFT)))
        r["tier"], r["why"] = tier(r["must"], r["sem_set"], urgent)
    rows.sort(key=lambda r: (r["tier"], r["left"] if r["left"] is not None else 10 ** 6))

    # ---- full table: gitignored, stays local ---------------------------------
    F = ["# Saved plan ranked by deferability and grab urgency", "",
         f"- must-take set: {must_source} ({len(must_codes)} codes)",
         f"- urgency rule: enrolled/capacity >= {URGENT_RATIO:.0%}, or remaining <= {URGENT_LEFT}",
         f"- this semester assumed: {THIS_SEMESTER}", "",
         "| Tier | Course | Attr | Credit | Semester(s) | Enrolled/capacity | Sections |",
         "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        rem = "-" if r["ratio"] is None else f"{r['enr']}/{r['cap']} ({r['ratio']:.0%})"
        sem = "/".join(sorted(r["sem_set"])) or "UNKNOWN"
        F.append(f"| {r['tier']} | {r['name']} | {r['attr']} | {r['credit']} | {sem} | "
                 f"{rem} | {len(r['sections'])} |")
    F += ["", "## Tier meanings", ""]
    for t in ["P0", "P1", "P2", "P3", "PX", "PN", "PU"]:
        ex = next((r["why"] for r in rows if r["tier"] == t), "")
        if ex:
            F.append(f"- {t}: {ex}")
    F += ["", "## Grab order (the second list, not the timetable)", ""]
    F += [f"{i+1}. [{r['tier']}] {r['name']} (remaining {r['left']})" for i, r in enumerate(rows)]
    os.makedirs("raw/private", exist_ok=True)
    open("raw/private/plan-priority.md", "w", encoding="utf-8").write("\n".join(F) + "\n")

    # ---- aggregates only: committed ------------------------------------------
    tiers = Counter(r["tier"] for r in rows)
    no_cap = sum(1 for r in rows if r["ratio"] is None)
    unknown_sem = sum(1 for r in rows if not r["sem_set"])
    not_this_sem = sum(1 for r in rows if r["sem_set"] == {"春季"})
    no_weeks = sum(1 for r in rows if r["weeks"] == "(not in any source)")
    only_this = sum(1 for r in rows if r["semester"] == THIS_SEMESTER)
    contested = sum(1 for r in rows if r["ratio"] is not None and r["ratio"] >= URGENT_RATIO)
    A = ["# Aggregates only (the per-course table is in raw/private/, not committed)", "",
         f"- planned courses analysed: {len(rows)}",
         f"- courses with a capacity figure from some source: {len(rows) - no_cap} of {len(rows)}",
         f"- courses with a week-range figure from some source: {len(rows) - no_weeks} of {len(rows)}",
         f"- courses offered in {THIS_SEMESTER} (i.e. not deferable within the year): "
         f"{only_this} of {len(rows)}",
         f"- courses at >= {URGENT_RATIO:.0%} of capacity: {contested} of {len(rows) - no_cap} "
         f"with a capacity figure",
         f"- courses whose SEMESTER is unknown from every source: {unknown_sem} of {len(rows)}",
         f"- courses NOT offered in {THIS_SEMESTER} (春季-only) but present in the plan: {not_this_sem}",
         f"- must-take set source: {must_source}", "",
         "## Tier distribution", ""]
    for t in ["P0", "P1", "P2", "P3", "PX", "PN", "PU"]:
        if tiers.get(t):
            A.append(f"- {t}: {tiers[t]}")
    A += ["", "The two orders disagree on the measured data, which is the reason the project must",
          "emit two lists: a conflict-free plan, and a grab order. See docs/priority-rules.md.", ""]
    os.makedirs("raw/measurements", exist_ok=True)
    open("raw/measurements/plan-priority-summary.md", "w", encoding="utf-8").write("\n".join(A) + "\n")
    print("\n".join(A))
    print("[ok] wrote raw/private/plan-priority.md (gitignored) and raw/measurements/plan-priority-summary.md")


if __name__ == "__main__":
    sys.exit(main())

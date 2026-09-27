#!/usr/bin/env python3
"""Step 1-4 of the selection design: requirements -> classification -> gap -> fillers.

Usage:
    python3 src/credit_gap.py [--plan <planner-backup.json>] [--track master|combined_master_phd]

Step 1  the credit requirements come from the programme document, frozen in
        data/degree-requirements.json (nothing here is guessed; no source in the course data
        carries "is this required").
Step 2  the plan's courses are classified into the document's categories using the rules in
        that same file (attribute match, or name match where the attribute is too coarse).
Step 3  the gap per category is computed.
Step 4  filler candidates are proposed from the frozen course pool: open this semester, in the
        attribute group that is short, not already planned, ordered by how easy the seat is.

Outputs
-------
  raw/private/credit-gap.md               per-course classification + fillers (gitignored)
  raw/measurements/credit-gap-summary.md  aggregates only (committed)
"""
import argparse, json, os, sys
from collections import defaultdict

DEFAULT_PLAN = os.path.expanduser("~/Downloads/选课地图-本地备份 (3).json")
REQ = "data/degree-requirements.json"
OFFICIAL = "raw/sections-snapshot.json"
LIVE = "raw/yuquanlu-live-courses.json"
THIS_SEMESTER = "秋季"
PHD_LEVEL = "博士课程"   # does not count towards the master's credit requirement


def load(path, msg):
    if not os.path.exists(path):
        sys.exit(f"[!] missing {path} -- {msg}")
    return json.load(open(path, encoding="utf-8"))


def match_name(name, needles):
    return any(n in name for n in needles)


def classify(course, req):
    """-> set of category ids this course may count towards."""
    hits = set()
    name, attr = course.get("name", ""), course.get("attribute", "")
    for cat in req["categories"]:
        if cat.get("kind") == "non_course":
            continue
        for comp in cat.get("fixed_components", []):
            if match_name(name, comp["name_contains"]):
                hits.add(cat["id"])
        if cat.get("matches_names") and match_name(name, cat["matches_names"]):
            hits.add(cat["id"])
        if attr and attr in (cat.get("matches_attributes") or []):
            hits.add(cat["id"])
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default=DEFAULT_PLAN)
    ap.add_argument("--track", default="master", choices=["master", "combined_master_phd"])
    a = ap.parse_args()

    req = load(REQ, "the extracted programme requirements")
    plan = load(a.plan, "the planner backup holding the saved plan")["plan"]
    official = {c["code"]: c for c in load(OFFICIAL, "run freeze_snapshot.py")["courses"]}
    live_list = load(LIVE, "run fetch_public_listing.py")["courses"]
    live = {c["code"]: c for c in live_list}

    # official workbooks may hold one record per semester -> build the semester set
    sem_of = defaultdict(set)
    for c in official.values():
        if c.get("semester"):
            sem_of[c["code"]].add(c["semester"])

    def semester_evidence(code):
        s = sem_of.get(code)
        if s:
            return "/".join(sorted(s)), "official workbook field"
        if code in live:
            return THIS_SEMESTER, "inferred: present in the 2026 秋季 catalogue"
        return "UNKNOWN", "no source"

    rows, earned = [], defaultdict(float)
    for p in plan:
        code = p["code"]
        lv = live.get(code, {})
        off = official.get(code, {})
        level = lv.get("level") or off.get("level") or ""
        sem, ev = semester_evidence(code)
        cats = classify({"name": p.get("name", ""), "attribute": p.get("attribute", "")}, req)
        cr = float(p.get("credit") or 0)
        counts = level != PHD_LEVEL
        if counts:
            for cid in cats:
                earned[cid] += cr
        rows.append(dict(code=code, name=p.get("name", ""), attr=p.get("attribute", ""), level=level,
                         credit=cr, cats=sorted(cats), semester=sem, evidence=ev, counts=counts,
                         capacity=lv.get("capacity", ""), enrolled=lv.get("enrolled", "")))

    # ---- step 3: gap ---------------------------------------------------------
    track = req["degree_track"][a.track]
    gaps = []
    for cat in req["categories"]:
        cid = cat["id"]
        if cat.get("kind") == "non_course":
            gaps.append((cat["name"], cat.get("min_credits", 0), 0.0, "not tracked from the plan"))
            continue
        got = earned.get(cid, 0.0)
        need = cat.get("min_credits", 0)
        n_courses = sum(1 for r in rows if cid in r["cats"])
        mark = "OK" if got >= need else f"SHORT {need - got:g}"
        if cat.get("min_courses") and n_courses < cat["min_courses"]:
            mark += f" / needs >={cat['min_courses']} courses, has {n_courses}"
        gaps.append((cat["name"], need, got, mark))

    course_learning = sum(r["credit"] for r in rows if r["counts"])
    semester_credits = sum(r["credit"] for r in rows
                           if r["counts"] and r["semester"] == THIS_SEMESTER)

    # ---- step 4: fillers ----------------------------------------------------
    short_attrs = []
    for cat in req["categories"]:
        cid = cat["id"]
        if cat.get("kind") == "non_course":
            continue
        got = earned.get(cid, 0.0)
        need = cat.get("min_credits", 0)
        if got < need and cat.get("matches_attributes"):
            short_attrs.append((cid, cat["name"], need - got, cat["matches_attributes"]))

    planned = {r["code"] for r in rows}
    fillers = {}
    for cid, cname, missing, attrs in short_attrs:
        cands = []
        for c in live_list:
            if c["code"] in planned or c.get("attribute") not in attrs:
                continue
            try:
                cap, enr = int(str(c.get("capacity") or "")), int(str(c.get("enrolled") or ""))
            except ValueError:
                cap = enr = None
            left = (cap - enr) if (cap and enr is not None) else None
            cands.append((left if left is not None else -1, float(c.get("credit") or 0),
                          c["name"], c["code"], cap, enr))
        cands.sort(key=lambda x: (-x[0], -x[1]))
        fillers[cid] = (missing, cname, cands[:10])

    # ---- write ---------------------------------------------------------------
    F = ["# Credit accounting for the saved plan", "",
         f"- track: {a.track}",
         f"- requirements from: {req['_source']['document']}",
         f"- planned courses: {len(rows)}  (counting towards the master's requirement: "
         f"{sum(1 for r in rows if r['counts'])})",
         f"- course-learning credits from the plan: {course_learning:g} "
         f"(requirement >= {track['course_learning_min_credits']})",
         f"- credits whose course is evidenced as open in {THIS_SEMESTER}: {semester_credits:g}",
         "", "## Per-category result", "",
         "| Category | Need | Earned | Status |", "| --- | --- | --- | --- |"]
    F += [f"| {n} | {need} | {got:g} | {st} |" for n, need, got, st in gaps]
    F += ["", "## Per-course classification", "",
          "| Course | Attr | Level | Credit | Counts | Semester (evidence) | Categories |",
          "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        F.append(f"| {r['name']} | {r['attr']} | {r['level'] or '-'} | {r['credit']:g} | "
                 f"{'yes' if r['counts'] else 'NO (doctoral)'} | {r['semester']} ({r['evidence']}) | "
                 f"{', '.join(r['cats']) or '-'} |")
    # fixed-component diagnostics: which named component is short, and is it even a course?
    # ---- step 2: the candidate pool a student picks from ---------------------
    # Every course open this semester that may count towards a category with a minimum,
    # i.e. "the required courses available this semester", to check off as must-take.
    pool_stats = []
    for cat in req["categories"]:
        if cat.get("kind") == "non_course":
            continue
        attrs = cat.get("matches_attributes")
        needles = [n for comp in cat.get("fixed_components", []) for n in comp["name_contains"]]
        if not attrs and not needles:
            continue
        cands, planned_n = [], 0
        for c in live_list:
            ok = (c.get("attribute") in attrs) if attrs else match_name(c["name"], needles)
            if not ok:
                continue
            try:
                cap, enr = int(str(c.get("capacity") or "")), int(str(c.get("enrolled") or ""))
                left = cap - enr
            except ValueError:
                left = None
            if c["code"] in planned:
                planned_n += 1
            cands.append((left if left is not None else -1, float(c.get("credit") or 0),
                          c["name"], c["code"]))
        cands.sort(key=lambda x: (-x[0], -x[1]))
        pool_stats.append((cat["name"], len(cands), planned_n, sum(1 for x in cands if x[0] == 0),
                           cands[:6]))
    F += ["", "## Step 2: candidate pool — required-type courses open this semester", "",
          "Use this as the list to check off as must-take (see docs/selection-design.md step 2).", "",
          "| Category | Eligible now | Already in plan | Full (0 seats) |", "| --- | --- | --- | --- |"]
    F += [f"| {n} | {tot} | {pl} | {full} |" for n, tot, pl, full, _ in pool_stats]
    F += [""]
    for n, tot, pl, full, top in pool_stats:
        F += [f"### {n} — {tot} eligible this semester (top by free seats)", "",
              "| Free seats | Credit | Course | Code |", "| --- | --- | --- | --- |"]
        F += [f"| {l if l >= 0 else '?'} | {cr:g} | {nm} | {cd} |" for l, cr, nm, cd in top]
        F.append("")
    F += ["## Fixed-component diagnostic (categories defined by named components)", ""]
    for cat in req["categories"]:
        comps = cat.get("fixed_components")
        if not comps or cat.get("kind") == "non_course":
            continue
        F += [f"### {cat['name']} — need {cat.get('min_credits', 0)}, earned "
              f"{earned.get(cat['id'], 0):g}", "",
              "| Component | Credits needed | Matched in the plan | Status |",
              "| --- | --- | --- | --- |"]
        for comp in comps:
            needles = comp.get("name_contains") or [comp.get("name", "")]
            mine = [r for r in rows if match_name(r["name"], needles)]
            got = sum(r["credit"] for r in mine)
            if got >= comp["credits"]:
                st = "OK"
            elif got == 0:
                st = ("MISSING -- check whether it is covered by an exemption "
                      "(免修/EX) or must be taken as a course; an exemption is not a row in the data")
            else:
                st = f"PARTIAL, short {comp['credits'] - got:g}"
            F.append(f"| {' / '.join(needles)} | {comp['credits']} | {got:g} | {st} |")
        F.append("")
    F += ["## Step 4: filler candidates (seats available, this semester, not yet planned)", ""]
    if not fillers:
        F.append("- nothing short: no fillers needed")
    for cid, (missing, cname, cands) in fillers.items():
        F += [f"### {cname} — short {missing:g} credits", "",
              "| Free seats | Credit | Course | Code |", "| --- | --- | --- | --- |"]
        for left, cr, nm, code, cap, enr in cands:
            F.append(f"| {left if left >= 0 else '?'} | {cr:g} | {nm} | {code} |")
        F.append("")
    os.makedirs("raw/private", exist_ok=True)
    open("raw/private/credit-gap.md", "w", encoding="utf-8").write("\n".join(F) + "\n")

    A = ["# Credit gap — aggregates only (per-course detail is in raw/private/, not committed)", "",
         f"- track analysed: {a.track}",
         f"- courses in the plan: {len(rows)} (doctoral-level, not counted: "
         f"{sum(1 for r in rows if not r['counts'])})",
         f"- course-learning credits reached: {course_learning:g} "
         f"(requirement >= {track['course_learning_min_credits']})",
         f"- credits evidenced as open in {THIS_SEMESTER}: {semester_credits:g} "
         f"(per-semester floor >= {req['semester_min_credits']['value']})",
         f"- categories short of their minimum: "
         f"{sum(1 for n, need, got, st in gaps if st.startswith('SHORT'))}",
         f"- categories needing a course-count check that fails: "
         f"{sum(1 for n, need, got, st in gaps if 'needs >=' in st)}",
         f"- categories satisfied: "
         f"{sum(1 for n, need, got, st in gaps if st == 'OK')}", ""]
    open("raw/measurements/credit-gap-summary.md", "w", encoding="utf-8").write("\n".join(A) + "\n")
    print("\n".join(A))
    print("[ok] wrote raw/private/credit-gap.md (gitignored) and raw/measurements/credit-gap-summary.md")


if __name__ == "__main__":
    sys.exit(main())

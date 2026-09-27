#!/usr/bin/env python3
"""Freeze a publishable course-listing snapshot from a local course-planner backup.

Usage:
    python3 src/freeze_snapshot.py [source.json] [--campus 玉泉路] [--out raw/sections-snapshot.json]

Why this exists
---------------
ISE-A1 requires evidence that can be published and reproduced.  The raw planner
backup is a private working file, so this script derives a *minimal, deterministic*
snapshot from it and records two hashes:

  * the hash of the SOURCE file (provenance -- the source itself is not committed)
  * the hash of the SNAPSHOT  (freezes the data version cited in the evidence ledger)

Only public course-listing fields are kept.  No student identity, no enrolment
records, no personal data.
"""
import argparse, hashlib, json, os, sys
from collections import Counter

DEFAULT_SRC = os.path.expanduser("~/Downloads/选课地图-本地备份 (3).json")
KEEP = ["code", "name", "attribute", "credit", "capacity", "enrolled",
        "weeks", "time", "exam", "source", "sessions"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()



def has_week(c):
    """True if any session (or its raw fields) carries an 开课周 value."""
    for s in (c.get("sessions") or []):
        if (s.get("weeks") or "").strip() or (s.get("fields") or {}).get("开课周", "").strip():
            return True
    return (c.get("weeks") or "").strip() != ""


def has_time(c):
    """True if any session (or its raw fields) carries an 星期节次 value."""
    for s in (c.get("sessions") or []):
        if (s.get("time") or "").strip() or (s.get("fields") or {}).get("星期节次", "").strip():
            return True
    return (c.get("time") or "").strip() != ""


def slim(course, campus):
    out = {k: course.get(k, "") for k in KEEP}
    fields = course.get("fields") or {}
    out["campus"] = fields.get("开课校区", "")
    out["department"] = fields.get("开课院系", "")
    out["semester"] = fields.get("开课学期", "")
    if out.get("sessions"):
        out["sessions"] = [
            {"weeks": s.get("weeks", ""), "time": s.get("time", ""),
             "room": (s.get("fields") or {}).get("上课地点", "")}
            for s in out["sessions"]
        ]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", nargs="?", default=DEFAULT_SRC)
    ap.add_argument("--campus", default="玉泉路",
                    help="keep only courses opened at this campus (default 玉泉路; pass '' for all)")
    ap.add_argument("--out", default="raw/sections-snapshot.json")
    a = ap.parse_args()

    with open(a.source, encoding="utf-8") as fh:
        src = json.load(fh)

    courses = src.get("courses") or []
    plan = src.get("plan") or []
    issues = src.get("importIssues") or []

    kept = []
    for c in courses:
        s = slim(c, a.campus)
        if a.campus and s["campus"] != a.campus:
            continue
        kept.append(s)
    kept.sort(key=lambda s: (s["code"], s["name"]))

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    blob = json.dumps({"campus_filter": a.campus, "courses": kept},
                      ensure_ascii=False, indent=1, sort_keys=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(blob + "\n")

    snap_hash = sha256(a.out)
    with open(a.out + ".sha256", "w", encoding="utf-8") as fh:
        fh.write(f"{snap_hash}  {os.path.basename(a.out)}\n")

    # ---- summary, also written out as provenance -------------------------------
    src_attr = Counter(c.get("attribute", "") for c in kept)
    src_book = Counter((c.get("source") or "") for c in kept)
    n_time = sum(1 for c in kept if has_time(c))
    n_week = sum(1 for c in kept if has_week(c))
    n_campus_missing = sum(1 for c in courses if not (c.get("fields") or {}).get("开课校区"))
    plan_attr = Counter(p.get("attribute", "") or "(empty)" for p in plan)
    plan_credits = sum(float(p.get("credit") or 0) for p in plan)
    plan_nocampus = sum(1 for p in plan if not (p.get("fields") or {}).get("开课校区"))

    lines = [
        "# Snapshot provenance",
        "",
        f"- Source file (NOT committed): `{a.source}`",
        f"- Source sha256: `{sha256(a.source)}`",
        f"- Snapshot: `{a.out}`",
        f"- Snapshot sha256: `{snap_hash}`",
        f"- Campus filter: `{a.campus or '(none - all campuses)'}`",
        f"- Courses in source: {len(courses)}  |  kept: {len(kept)}",
        f"- Courses in the saved plan: {len(plan)}",
        f"- Planned courses that could be matched to this campus subset: "
        f"{sum(1 for p in plan if (p.get('fields') or {}).get('开课校区') == a.campus)}"
        " (lower bound -- most planned entries carry no 开课校区 field)",
        f"- Courses in the source with NO 开课校区 field: {n_campus_missing} of {len(courses)}",
        "",
        "## Coverage of the two fields a conflict check needs (KEY FINDING)",
        "",
        f"- Kept courses carrying an 开课周 (week-range) value: **{n_week} of {len(kept)}**",
        f"- Kept courses carrying an 星期节次 (weekday+period) value: **{n_time} of {len(kept)}**",
        "- A conflict check needs both. With neither, no computer-assisted conflict",
        "  filtering is possible from the structured source alone.",
        "",
        "## Saved plan under study",
        "",
        f"- planned courses: {len(plan)}; summed credits: {plan_credits}",
        f"- planned courses with NO 开课校区 field: {plan_nocampus} of {len(plan)}",
        "- by attribute: " + ", ".join(f"{k}={v}" for k, v in plan_attr.most_common()),
        "",
        "## Kept courses by attribute",
        "",
    ]
    lines += [f"- {k or '(empty)'}: {v}" for k, v in src_attr.most_common()]
    lines += ["", "## Kept courses by source workbook", ""]
    lines += [f"- `{k}`: {v}" for k, v in src_book.most_common()]
    lines += ["", "## Import issues reported by the planner for the official workbooks", ""]
    lines += [f"- `{i.get('source','')}`: {i.get('message','')}" for i in issues]
    report = "\n".join(lines) + "\n"
    os.makedirs("raw/measurements", exist_ok=True)
    with open("raw/measurements/snapshot-provenance.md", "w", encoding="utf-8") as fh:
        fh.write(report)

    print(report)
    print(f"[ok] wrote {a.out} and {a.out}.sha256")


if __name__ == "__main__":
    sys.exit(main())

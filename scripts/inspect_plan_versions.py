#!/usr/bin/env python3
"""Inspect saved course-plan versions and diff them.

Usage:
    python3 scripts/inspect_plan_versions.py [FILE.xlsx ...] [--out data/s3-my-plan-versions/plan-versions.md]

Produces the measured basis for the A1 evidence ledger: how many plan versions
exist, how large each one is, and what actually changed between them.  Writes a
markdown report so the numbers in the brief can be traced back to raw output.
"""
import argparse, hashlib, os, re, sys
from datetime import datetime

import openpyxl

DEFAULT_FILES = [
    os.path.expanduser("~/Downloads/选课规划-已选课程-2026-09-05.xlsx"),
    os.path.expanduser("~/Desktop/选课规划-已选课程-2026-09-15.xlsx"),
]
WEEK_SHEET = re.compile(r"^第\s*\d+\s*周$")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cells(path):
    """-> {(sheet, coord): text} for every non-empty cell."""
    wb = openpyxl.load_workbook(path, data_only=True)
    out = {}
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if c.value is not None and str(c.value).strip():
                    out[(ws.title, c.coordinate)] = " ".join(str(c.value).split())
    wb.close()
    return out


# ---------------------------------------------------------------------------
# Week occupancy: the third dimension, measured
# ---------------------------------------------------------------------------

def week_runs(weeks):
    """[3,4,5,7,8] -> '3-5, 7-8'"""
    nums = sorted({int("".join(ch for ch in w if ch.isdigit())) for w in weeks})
    runs, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        runs.append(str(nums[i]) if i == j else f"{nums[i]}-{nums[j]}")
        i = j + 1
    return ", ".join(runs)


def occupancy(path):
    """-> (per-course week/cell map, {cell: set(course names)})"""
    wb = openpyxl.load_workbook(path, data_only=True)
    per_course, per_cell = {}, {}
    for ws in wb.worksheets:
        if not WEEK_SHEET.match(ws.title):
            continue
        for row in ws.iter_rows(min_row=5, min_col=2, max_col=8):
            for c in row:
                if not c.value or not str(c.value).strip():
                    continue
                parts = [p.strip() for p in str(c.value).split("\n") if p.strip()]
                if not parts:
                    continue
                course = parts[0]
                slot = parts[1] if len(parts) > 1 else ""
                per_course.setdefault(course, {"weeks": [], "cells": set(), "slots": set()})
                per_course[course]["weeks"].append(ws.title)
                per_course[course]["cells"].add(c.coordinate)
                per_course[course]["slots"].add(slot)
                per_cell.setdefault(c.coordinate, {})
                per_cell[c.coordinate].setdefault(course, []).append(ws.title)
    wb.close()
    return per_course, per_cell


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", default=None)
    ap.add_argument("--out", default="data/s3-my-plan-versions/plan-versions.md")
    a = ap.parse_args()
    files = a.files or DEFAULT_FILES

    L = ["# Measured inspection of saved course-plan versions", "",
         f"- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
         "- Reproduce with: `python3 scripts/inspect_plan_versions.py`", ""]

    data, meta = {}, {}
    for f in files:
        if not os.path.exists(f):
            L.append(f"- MISSING (skipped): `{f}`")
            continue
        wb = openpyxl.load_workbook(f, data_only=True)
        sheets = wb.sheetnames
        wb.close()
        d = cells(f)
        data[f] = d
        weeks = [s for s in sheets if WEEK_SHEET.match(s)]
        meta[f] = dict(sha=sha256(f), sheets=sheets, n_weeks=len(weeks),
                       other=[s for s in sheets if s not in weeks], n_cells=len(d),
                       mtime=datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y-%m-%d %H:%M"),
                       bytes=os.path.getsize(f))
        L += [f"## `{os.path.basename(f)}`", "",
              f"- sha256: `{meta[f]['sha']}`",
              f"- size / mtime: {meta[f]['bytes']} bytes, {meta[f]['mtime']}",
              f"- worksheets: {len(sheets)}  (weekly timetable sheets: {meta[f]['n_weeks']})",
              f"- non-empty cells: {meta[f]['n_cells']}",
              f"- non-week sheets: {meta[f]['other'] or '(none)'}", ""]

    ok = [f for f in files if f in data]
    if len(ok) >= 2:
        base = ok[0]
        L += ["## Cross-version differences", "",
              f"Comparing `{os.path.basename(base)}` (older) against "
              f"`{os.path.basename(ok[-1])}` (newer).", ""]
        A, B = data[base], data[ok[-1]]
        ka, kb = set(A), set(B)
        common_sheets = set(meta[base]["sheets"]) & set(meta[ok[-1]]["sheets"])
        ca = {k: v for k, v in A.items() if k[0] in common_sheets}
        cb = {k: v for k, v in B.items() if k[0] in common_sheets}
        changed = [k for k in set(ca) & set(cb) if ca[k] != cb[k]]
        L += [f"- worksheet sets identical: {meta[base]['sheets'] == meta[ok[-1]]['sheets']}",
              f"- sheets only in older: {sorted(set(meta[base]['sheets']) - set(meta[ok[-1]]['sheets']))}",
              f"- sheets only in newer: {sorted(set(meta[ok[-1]]['sheets']) - set(meta[base]['sheets']))}",
              f"- cells only in older: {len(ka - kb)}",
              f"- cells only in newer: {len(kb - ka)}",
              f"- cells present in both with different text: {len(changed)}",
              f"- cells only in older, restricted to common sheets: "
              f"{len(set(ca) - set(cb))}",
              f"- cells only in newer, restricted to common sheets: "
              f"{len(set(cb) - set(ca))}", ""]
        for label, keys, src in (("only in older", sorted(set(ca) - set(cb)), ca),
                                 ("only in newer", sorted(set(cb) - set(ca)), cb)):
            L += [f"### Sample: cells {label} (common sheets)", ""]
            for k in keys[:12]:
                L.append(f"- `{k[0]}!{k[1]}`: {src[k][:70]}")
            L += ["", f"_(showing {min(12, len(keys))} of {len(keys)})_", ""]
        L += ["### Sample: cells changed in place", ""]
        for k in changed[:12]:
            L.append(f"- `{k[0]}!{k[1]}`: `{ca[k][:40]}` -> `{cb[k][:40]}`")
        L += ["", f"_(showing {min(12, len(changed))} of {len(changed)})_", ""]

    # ---- week occupancy: the third dimension -------------------------------
    for pf in ok:
        per_course, per_cell = occupancy(pf)
        L += [f"## Week occupancy (`{os.path.basename(pf)}`)", "",
              "A course is placed in a *different worksheet* per teaching week, so the",
              "week dimension is encoded by sheet membership rather than by a field.",
              "This is exactly what a weekday+period-only comparison cannot see.", "",
              "| Course | Weeks present | Count | Cell(s) |",
              "| --- | --- | --- | --- |"]
        for course, d in sorted(per_course.items(), key=lambda kv: len(set(kv[1]["weeks"]))):
            L.append(f"| {course} | {week_runs(d['weeks'])} | {len(set(d['weeks']))} | "
                     f"{', '.join(sorted(d['cells']))} |")
        multi = {c: v for c, v in per_cell.items() if len(v) > 1}
        L += ["", f"### Slots hosting more than one course in different weeks ({len(multi)})", ""]
        if multi:
            L += ["These are the cases that make week ranges mandatory: a weekday+period-only",
                  "comparison reports every one of them as a clash, though the courses never",
                  "overlap in time.", "",
                  "| Cell | Courses and the weeks each occupies |", "| --- | --- |"]
            for cell, v in sorted(multi.items()):
                detail = "; ".join(f"{c} (weeks {week_runs(w)})" for c, w in sorted(v.items()))
                L.append(f"| {cell} | {detail} |")
        else:
            L.append("- none found")
        L.append("")

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"[ok] wrote {a.out}")


if __name__ == "__main__":
    sys.exit(main())

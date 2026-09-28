#!/usr/bin/env python3
"""Freeze the public course listing and join it with the official workbooks.

Usage:
    python3 scripts/fetch_public_listing.py [--input CACHED.json] [--out data/derived/course-library-snapshot.json]
                                        [--url https://courseplanner.cysdy.cn/default-courses.json]

Why this exists
---------------
No single source carries everything a conflict check plus a grab-priority ranking needs:

  A  official workbook  开课计划表0828.xlsx            campus/semester/attribute/credits   NO week, NO period, NO capacity
  B  official workbook  核心课和专业课列表0828.xlsx     same shape as A                     NO week, NO period, NO capacity
  C  public listing     default-courses.json          week / period / capacity / enrolled  NO campus field at all

Source C has no campus field, so the Yuquanlu subset can only be recovered from the course-code
rule (position 18 == 'Y').  This script freezes source C, filters it that way, records hashes for
both the raw download and the frozen subset, and reports how C joins with A+B by course code.

The 8 MB raw download is NOT committed (only its sha256); the filtered subset is committed so the
join is reproducible without network access.
"""
import argparse, hashlib, json, os, subprocess, sys
from collections import Counter

DEFAULT_URL = "https://courseplanner.cysdy.cn/default-courses.json"
DEFAULT_OUT = "data/derived/course-library-snapshot.json"
OFFICIAL_SNAPSHOT = "data/s1-plan-workbook/sections-snapshot.json"
KEEP = ["code", "name", "attribute", "level", "subject", "credit",
        "capacity", "enrolled", "weeks", "time", "exam"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url, dest):
    print(f"[..] downloading {url}")
    subprocess.run(["curl", "-sS", "-m", "400", "-o", dest, url], check=True)
    return os.path.getsize(dest)


def is_yuquanlu(code):
    """Course code rule from the official instructions: position 18 == 'Y' means Yuquanlu."""
    code = str(code or "")
    return len(code) >= 18 and code[17].upper() == "Y"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="use an already downloaded JSON instead of fetching")
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--out", default=DEFAULT_OUT)
    a = ap.parse_args()

    raw = a.input or "/tmp/_courseplanner_raw.json"
    if not a.input:
        size = download(a.url, raw)
        print(f"[ok] {size} bytes")
    raw_hash = sha256(raw)

    data = json.load(open(raw, encoding="utf-8"))
    if not isinstance(data, list) or len(data) < 100:
        sys.exit(f"[!] unexpected payload shape: {type(data).__name__}")

    fields_seen = Counter()
    for c in data[:200]:
        fields_seen.update((c.get("fields") or {}).keys())

    kept = []
    for c in data:
        if not is_yuquanlu(c.get("code")):
            continue
        row = {k: c.get(k, "") for k in KEEP}
        row["room"] = (c.get("fields") or {}).get("教室", "")
        row["teacher"] = (c.get("fields") or {}).get("主讲教师", "") or \
                         (c.get("fields") or {}).get("首席教授", "")
        kept.append(row)
    kept.sort(key=lambda r: (r["code"], r["name"]))

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump({"campus_rule": "course code position 18 == 'Y'", "courses": kept},
                  fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    out_hash = sha256(a.out)
    with open(a.out + ".sha256", "w", encoding="utf-8") as fh:
        fh.write(f"{out_hash}  {os.path.basename(a.out)}\n")

    n_week = sum(1 for r in kept if str(r["weeks"]).strip())
    n_time = sum(1 for r in kept if str(r["time"]).strip())
    n_cap = sum(1 for r in kept if str(r["capacity"]).strip())
    n_enr = sum(1 for r in kept if str(r["enrolled"]).strip())

    L = ["# Public listing: provenance and join with the official workbooks", "",
         f"- URL: {a.url}",
         f"- Raw download: {os.path.getsize(raw)} bytes, sha256 `{raw_hash}` (not committed)",
         f"- Frozen subset: `{a.out}`, sha256 `{out_hash}`",
         f"- Campus rule applied: course code position 18 == 'Y'",
         f"- Entries downloaded: {len(data)}  |  kept (Yuquanlu): {len(kept)}",
         f"- Kept entries with a week value: {n_week} / {len(kept)}",
         f"- Kept entries with a weekday/period value: {n_time} / {len(kept)}",
         f"- Kept entries with a capacity value: {n_cap} / {len(kept)}",
         f"- Kept entries with an enrolled value: {n_enr} / {len(kept)}",
         f"- Fields present on this source (sampled): {', '.join(sorted(fields_seen))}",
         "- NOTE: this source carries no campus field, so the Yuquanlu subset can only be",
         "  recovered from the course-code rule above.", ""]

    if os.path.exists(OFFICIAL_SNAPSHOT):
        off = json.load(open(OFFICIAL_SNAPSHOT, encoding="utf-8"))["courses"]
        off_codes = {c["code"] for c in off}
        live_codes = {c["code"] for c in kept}
        inter = off_codes & live_codes
        L += ["## Join with the official workbooks (A+B), by course code", "",
              f"- official workbooks, Yuquanlu courses (records / codes): "
              f"{len(off)} records, {len(off_codes)} codes",
              f"- public listing, Yuquanlu courses: {len(kept)} codes",
              f"- codes in BOTH (all fields obtainable): **{len(inter)}**",
              f"- codes only in the official workbooks (no week/period/capacity): "
              f"**{len(off_codes - live_codes)}**",
              f"- codes only in the public listing (no campus field, no semester): "
              f"**{len(live_codes - off_codes)}**",
              "",
              "This is the measured reason the workflow is manual: assembling one input that can",
              "support a conflict check *and* a grab-priority ranking means joining three",
              "heterogeneous sources, and even after joining, a large share of courses still",
              "lack one group of fields or the other.", ""]
    else:
        L.append(f"- (no {OFFICIAL_SNAPSHOT} found; run freeze_snapshot.py first for the join report)")

    os.makedirs("data/derived", exist_ok=True)
    report = "\n".join(L) + "\n"
    open("data/derived/live-listing-provenance.md", "w", encoding="utf-8").write(report)
    print(report)
    print(f"[ok] wrote {a.out} and data/derived/live-listing-provenance.md")


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Freeze the auxiliary per-course fields that only exist in the SEP 学期课表 copy.

Why a separate artifact: `raw/yuquanlu-live-courses.json` was frozen with a reduced schema (its
sha256 is quoted in documents/README, so it must not change).  The raw download keeps the full SEP
列 set in `fields`; this script re-freezes just the extra columns into a NEW hashed artifact, so the
existing chain of custody stays intact while the extra fields become reproducible.

    python3 src/freeze_aux_fields.py [--raw /tmp/courseplanner-live.json] [--expect-sha 7c6090e4]

Input raw sha256 is verified against `raw/measurements/live-listing-provenance.md` before use.
"""
import argparse, hashlib, json, os, re, sys
from collections import Counter

KEEP = ["授课方式", "是否远程教学", "助教", "培养层次", "教室", "开课单位", "所属学科/专业"]
OUT = "raw/aux-sep-fields.json"
PROV = "raw/measurements/live-listing-provenance.md"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="/tmp/courseplanner-live.json")
    ap.add_argument("--expect-sha", default="7c6090e4")
    ap.add_argument("--campus", default="玉泉路")
    a = ap.parse_args()
    if not os.path.exists(a.raw):
        sys.exit(f"[!] raw download not found: {a.raw}\n"
                 f"    re-download https://courseplanner.cysdy.cn/default-courses.json then verify its sha256")
    blob = open(a.raw, "rb").read()
    sha = hashlib.sha256(blob).hexdigest()
    print(f"raw sha256 = {sha}")
    if not sha.startswith(a.expect_sha):
        sys.exit(f"[!] sha256 does not start with the recorded {a.expect_sha!r} -- refusing to freeze")
    rec = json.loads(blob.decode("utf-8"))
    out, dist = {}, Counter()
    for c in rec:
        f = c.get("fields") or {}
        campus = str(f.get("开课校区", ""))
        if campus and not campus.startswith(a.campus):
            continue
        code = c.get("code") or f.get("课程编码") or ""
        if not code:
            continue
        out[code] = {k: f.get(k, "") for k in KEEP}
        dist[str(f.get("是否远程教学", ""))] += 1
    os.makedirs("raw", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(dict(source="courseplanner default-courses.json", raw_sha256=sha,
                       campus=a.campus, fields=KEEP, courses=out), fh, ensure_ascii=False,
                  indent=1, sort_keys=True)
        fh.write("\n")
    h = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
    open(OUT + ".sha256", "w").write(f"{h}  {os.path.basename(OUT)}\n")
    print(f"[ok] {OUT}: {len(out)} courses  sha256={h[:16]}…")
    print("     是否远程教学分布:", dict(dist.most_common()))
    print("     授课方式分布:", dict(Counter(v["授课方式"] for v in out.values()).most_common()))


if __name__ == "__main__":
    sys.exit(main())

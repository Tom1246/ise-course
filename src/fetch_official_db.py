#!/usr/bin/env python3
"""Crawl the official UCAS course database (jwba.ucas.ac.cn) to local files.

Usage:
    python3 src/fetch_official_db.py [--terms 89576,89577] [--campus 20] [--limit N] [--workers 4]

Why this source
---------------
`/sc/public/coursePublic` is the academic-affairs public course listing: one server-rendered table
per (term, campus) with 开课院系 / 课程编号 / 课程名称 / 课时 / 学分 / 课程属性 / 限选人数 /
已选人数 / 首席教授 / 主讲教师 / 开课校区.  Each row links to `/sc/course/coursetime/<id>`, which
carries the schedule: 上课时间 (weekday + periods), 上课地点, 上课周次.

That makes this the authoritative source for campus + capacity + week + weekday + period -- i.e. it
replaces the third-party listing for everything except 开课学期 (which it does not model per course).

Outputs
-------
  raw/official/<term>-<campus>.json      normalised rows + parsed sessions
  raw/official/<term>-<campus>.json.sha256
  raw/measurements/official-db-provenance.md   fetch timestamps, counts, hashes, parse failures
  raw/official-cache/                    raw HTML cache (gitignored) -- makes re-runs cheap and resumable
"""
import argparse, hashlib, json, os, re, ssl, sys, time
import urllib.parse, urllib.request

from bs4 import BeautifulSoup

# python.org builds of CPython look for the CA bundle at the OpenSSL compile-time path and fail
# with CERTIFICATE_VERIFY_FAILED; use certifi's bundle explicitly so the script needs no env setup.
try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:                                     # pragma: no cover
    SSL_CTX = ssl.create_default_context()

BASE = "https://jwba.ucas.ac.cn"
LIST_URL = BASE + "/sc/public/coursePublic"
TIME_URL = BASE + "/sc/course/coursetime/{cid}"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
CACHE = "raw/official-cache"
OUTDIR = "raw/official"

SESSION_RE = re.compile(
    r"上课时间\s*(星期[一二三四五六日天])：\s*第([0-9、,]+)节。\s*"
    r"上课地点\s*(.*?)\s*上课周次\s*([0-9、,]+)", re.S)
COURSE_RE = re.compile(r"课程名称：\s*([^\s]+)")

failures = []


def get(url, data=None, tries=3):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            if data is not None:
                req.data = urllib.parse.urlencode(data).encode()
            with urllib.request.urlopen(req, timeout=40, context=SSL_CTX) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            if k == tries - 1:
                raise
            time.sleep(1.5 * (k + 1))


def cached(url, data, key):
    path = os.path.join(CACHE, key + ".html")
    if os.path.exists(path) and os.path.getsize(path) > 500:
        return open(path, encoding="utf-8").read()
    html = get(url, data)
    os.makedirs(CACHE, exist_ok=True)
    open(path, "w", encoding="utf-8").write(html)
    return html


def parse_list(html):
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    out = []
    if not table:
        return out
    for tr in table.find_all("tr")[1:]:
        tds = tr.find_all("td")
        if len(tds) < 12:
            continue
        a = tr.find("a", href=True)
        cid = re.search(r"/(\d+)$", a["href"]).group(1) if a else ""
        out.append(dict(
            seq=tds[0].get_text(strip=True), department=tds[1].get_text(strip=True),
            code=tds[2].get_text(strip=True), name=tds[3].get_text(strip=True),
            hours=tds[4].get_text(strip=True), credit=tds[5].get_text(strip=True),
            attribute=tds[6].get_text(strip=True), capacity=tds[7].get_text(strip=True),
            enrolled=tds[8].get_text(strip=True), chief=tds[9].get_text(strip=True),
            teacher=tds[10].get_text(strip=True), campus=tds[11].get_text(strip=True),
            course_id=cid))
    return out


def nums(txt):
    return sorted({int(x) for x in re.findall(r"\d+", txt)})


def compress(iv):
    iv = sorted(set(int(x) for x in iv))
    out, i = [], 0
    while i < len(iv):
        j = i
        while j + 1 < len(iv) and iv[j + 1] == iv[j] + 1:
            j += 1
        out.append([iv[i], iv[i]] if i == j else [iv[i], iv[j]])
        i = j + 1
    return out


WD = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "日": 7, "天": 7}


def parse_time_page(html):
    soup = BeautifulSoup(html, "lxml")
    txt = re.sub(r"[ \t]+", " ", soup.get_text(" ", strip=True))
    sessions = []
    for wd, periods, room, weeks in SESSION_RE.findall(txt):
        ps = nums(periods)
        wk = nums(weeks)
        if not ps or not wk:
            continue
        sessions.append(dict(weekday=WD[wd[-1]], periods=[ps[0], ps[-1]],
                             rooms=[room.strip()], weeks=compress(wk)))
    # merge identical (weekday, period) entries that differ only by week list
    merged = {}
    for s in sessions:
        key = (s["weekday"], s["periods"][0], s["periods"][1])
        if key in merged:
            merged[key]["weeks"] = compress([w for r in merged[key]["weeks"] + s["weeks"] for w in range(r[0], r[1] + 1)])
        else:
            merged[key] = s
    name = (COURSE_RE.search(txt).group(1) if COURSE_RE.search(txt) else "")
    return name, list(merged.values()), txt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--terms", default="89576", help="termId list, comma separated (89576=2026-27 autumn)")
    ap.add_argument("--campus", default="20", help="campusCode (20=玉泉路)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sleep", type=float, default=0.25)
    ap.add_argument("--outdir", default="raw/official",
                    help="where the frozen per-term JSON goes (use raw/official-history for past terms)")
    a = ap.parse_args()

    labels = {}
    try:
        labels = json.load(open(os.path.join("raw", "official", "terms.json"), encoding="utf-8"))
    except Exception:
        pass                      # term id -> 学期名, fetched from the site's own selector

    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    report = [f"# Official course database crawl -- {stamp}", "",
              f"- Source: {LIST_URL} (list) + {TIME_URL} (schedule)",
              f"- campusCode={a.campus} (20 = 玉泉路), termId(s)={a.terms}",
              f"- Crawled at: {stamp} (local, Asia/Shanghai)", ""]

    for term in [t.strip() for t in a.terms.split(",") if t.strip()]:
        list_html = cached(LIST_URL, {"termId": term, "campusCode": a.campus}, f"list-{term}-{a.campus}")
        rows = parse_list(list_html)
        if a.limit:
            rows = rows[:a.limit]
        report += [f"## termId {term}", "",
                   f"- list page: {len(list_html)} chars, {len(rows)} rows parsed",
                   f"- list page sha256: `{hashlib.sha256(list_html.encode()).hexdigest()}`", ""]
        n_ok = n_no_sched = n_courses_named = 0
        for i, r in enumerate(rows, 1):
            html = cached(TIME_URL.format(cid=r["course_id"]), None, f"time-{r['course_id']}")
            nm, sessions, txt = parse_time_page(html)
            r["schedule"] = sessions
            r["schedule_pages_sha256"] = hashlib.sha256(html.encode()).hexdigest()
            if sessions:
                n_ok += 1
            else:
                n_no_sched += 1
                failures.append((r["code"], r["name"], "no schedule parsed"))
            if nm:
                n_courses_named += 1
            if i % 50 == 0:
                print(f"  [{term}] {i}/{len(rows)} …", flush=True)
            time.sleep(a.sleep)
        report += [f"- schedule pages fetched: {len(rows)}",
                   f"- courses with a parsed schedule: {n_ok}",
                   f"- courses with NO parsed schedule: {n_no_sched}",
                   f"- courses whose detail page named them: {n_courses_named}", ""]
        os.makedirs(a.outdir, exist_ok=True)
        out = f"{a.outdir}/{term}-campus{a.campus}.json"
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(dict(term_id=term, term_label=labels.get(term, ""), campus_code=a.campus,
                           source=LIST_URL, crawled_at=stamp, rows=rows),
                      fh, ensure_ascii=False, indent=1, sort_keys=True)
            fh.write("\n")
        h = hashlib.sha256(open(out, "rb").read()).hexdigest()
        open(out + ".sha256", "w").write(f"{h}  {os.path.basename(out)}\n")
        report += [f"- term label: {labels.get(term, '(unknown)')}",
                   f"- frozen output: `{out}`", f"- frozen output sha256: `{h}`", ""]
        print(f"[ok] {out}  sha256={h[:16]}…")

    report += ["## Parse failures",
               ""] + ([f"- `{c}` {n}: {why}" for c, n, why in failures[:20]] or ["- none"])
    os.makedirs("raw/measurements", exist_ok=True)
    open("raw/measurements/official-db-provenance.md", "w", encoding="utf-8").write("\n".join(report) + "\n")
    print(f"[ok] wrote raw/measurements/official-db-provenance.md ({len(failures)} failures)")


if __name__ == "__main__":
    sys.exit(main())

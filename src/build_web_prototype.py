#!/usr/bin/env python3
"""Build the local prototype page from the OFFICIAL course database.

Usage:
    python3 src/build_web_prototype.py [--plan <planner-backup.json>] [--out prototype/选课参考系统.html]

Data: raw/official/<term>-campus20.json (crawled from jwba.ucas.ac.cn by fetch_official_db.py)
      + raw/sections-snapshot.json (official workbooks, for 开课学期)
      + data/degree-requirements.json (credit rules)
Layout mirrors https://courseplanner.cysdy.cn/ : notice bar, hero, metric chips, stat cards,
requirement checklist, selected courses, timetable grid, course catalogue, footer disclaimer.
Single self-contained file: opens from disk, no server, no network.
"""
import argparse, json, os, re, sys
from collections import Counter
from datetime import datetime

DEFAULT_PLAN = os.path.expanduser("~/Downloads/选课地图-本地备份 (3).json")
OFFICIAL_DB = "raw/official/{term}-campus{campus}.json"
SNAPSHOT = "raw/sections-snapshot.json"
AUX = "raw/yuquanlu-live-courses.json"      # 第三方课程库：官方公开库没有的字段（考核方式等）
AUX2 = "raw/aux-sep-fields.json"            # 同上来源的扩展字段（授课方式等），独立哈希冻结
REQ = "data/degree-requirements.json"
OUT = "prototype/选课参考系统.html"
ISSUES = "docs/prototype-issues.md"
TERMS = {"89576": ("2026-2027 秋季", "秋季"), "89577": ("2026-2027 春季", "春季")}
THIS_SEMESTER = "秋季"
PERIODS = [("1", "8:30–9:15"), ("2", "9:20–10:05"), ("3", "10:25–11:10"), ("4", "11:15–12:00"),
           ("5", "13:30–14:15"), ("6", "14:20–15:05"), ("7", "15:25–16:10"), ("8", "16:15–17:00"),
           ("9", "17:05–17:50"), ("10", "18:30–19:15"), ("11", "19:20–20:05"), ("12", "20:15–21:00"),
           ("13", "21:05–21:50")]

issues = []


def note(kind, detail, **kw):
    issues.append(dict(kind=kind, detail=detail, **kw))


def load(path, msg, default=None):
    if not os.path.exists(path):
        if default is not None:
            return default
        sys.exit(f"[!] missing {path} -- {msg}")
    return json.load(open(path, encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default=DEFAULT_PLAN)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--campus", default="20")
    a = ap.parse_args()
    gen = datetime.now().strftime("%Y-%m-%d %H:%M")

    sem_of = {}
    for c in load(SNAPSHOT, "run freeze_snapshot.py", default={"courses": []})["courses"]:
        sem_of.setdefault(c["code"], set()).add(c.get("semester", ""))
    req = load(REQ, "degree requirements")
    aux_rows = load(AUX, "run fetch_public_listing.py", default={"courses": []})["courses"]
    aux = {c["code"]: c for c in aux_rows}
    aux2 = load(AUX2, "run freeze_aux_fields.py", default={"courses": {}})["courses"]
    aux_base = {}
    for c in aux_rows:                      # 班次后缀不同（官方 -304，第三方 -201）→ 退化用基础编码
        base = c["code"].split("-")[0]
        aux_base.setdefault(base, []).append(c)
    plan_codes, backup_exported, english = [], "", ""
    if os.path.exists(a.plan):
        bak = load(a.plan, "")
        plan_codes = [p["code"] for p in bak.get("plan", [])]
        backup_exported, english = bak.get("exportedAt", ""), bak.get("englishPath", "")

    terms = {}
    for tid, (label, sem) in TERMS.items():
        path = OFFICIAL_DB.format(term=tid, campus=a.campus)
        d = load(path, f"run fetch_official_db.py (term {tid})", default=None)
        if not d:
            continue
        rows, seen = [], Counter()
        for r in d["rows"]:
            seen[r["code"]] += 1
            no_cap = False
            try:
                cap, enr = int(r["capacity"]), int(r["enrolled"])
                left = cap - enr
            except (TypeError, ValueError):
                cap = enr = left = None
                try:
                    enr = int(r["enrolled"])
                except (TypeError, ValueError):
                    enr = None
                if str(r["capacity"]).strip() in ("/", "-", ""):
                    no_cap = True          # 官方用 "/" 表示不设限选人数，不是缺数据
                else:
                    note("容量字段格式异常", f"capacity={r['capacity']!r} enrolled={r['enrolled']!r}",
                         code=r["code"], name=r["name"])
            sems = sorted(x for x in sem_of.get(r["code"], set()) if x)
            if not sems:
                note("官方公开库有、官方工作簿没有此课程编码",
                     "因此无法判断它是否只在某一个学期开课（退化为 PU 档）",
                     code=r["code"], name=r["name"])
            if not r.get("schedule"):
                note("详情页没有解析出任何上课时间", "该课程无法参与冲突检测", code=r["code"], name=r["name"])
            top = max((w[1] for s in r.get("schedule", []) for w in s["weeks"]), default=0)
            if top > 20:
                note("周次超出学期长度（秋季 20 周）", f"最大到第 {top} 周", code=r["code"], name=r["name"])
            ax = aux.get(r["code"]) or (aux_base.get(r["code"].split("-")[0], [None])[0]
                                        if len(aux_base.get(r["code"].split("-")[0], [])) == 1 else None)
            if not ax:
                note("第三方课程库里没有此课程 → 拿不到考核方式",
                     "考核方式只有第三方源有，官方公开库不含该字段", code=r["code"], name=r["name"])
            rows.append(dict(
                cid=r["course_id"], code=r["code"], name=r["name"], credit=float(r["credit"] or 0),
                attribute=r["attribute"], department=r["department"], hours=r["hours"],
                teacher=r["teacher"] or r["chief"], campus=r["campus"],
                capacity=cap, enrolled=enr, left=left, no_cap=no_cap,
                exam=(ax or {}).get("exam", "") or "",
                teach_mode=(aux2.get(r["code"]) or {}).get("授课方式", ""),
                aux_from="第三方课程库" if ax else "",
                semester="/".join(sems), sem_sets=sems, term=sem,
                sessions=[dict(wd=s["weekday"], ps=s["periods"][0], pe=s["periods"][1],
                               rooms=s.get("rooms", []), weeks=s["weeks"]) for s in r.get("schedule", [])]))
        for code, n in seen.items():
            if n > 1:
                note("同一学期内课程编码重复", f"该编码在本学期出现 {n} 次", code=code)
        terms[sem] = dict(term_id=tid, label=label, crawled_at=d.get("crawled_at", ""), rows=rows)

    cats = [dict(id=c["id"], name=c["name"], kind=c.get("kind", "degree"),
                 min_credits=c.get("min_credits", 0), min_courses=c.get("min_courses", 0),
                 attrs=c.get("matches_attributes", []), names=c.get("matches_names", []),
                 comps=[dict(credits=k["credits"], needles=k.get("name_contains") or [k.get("name", "")])
                        for k in c.get("fixed_components", [])])
            for c in req["categories"]]

    data = dict(generated=gen, this_semester=THIS_SEMESTER, periods=PERIODS,
                semester_min_credits=req["semester_min_credits"]["value"],
                course_learning_min=req["degree_track"]["master"]["course_learning_min_credits"],
                professional_degree_min=req["degree_track"]["master"]["professional_degree_min_credits"],
                categories=cats, plan_codes=plan_codes, terms=terms,
                english=english or "未设置", backup_exported_utc=backup_exported)
    html = TEMPLATE.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(html)

    kinds = Counter(i["kind"] for i in issues)
    L = ["# Prototype build: problems met while building", "",
         f"- Build run: {gen}",
         f"- Artifact: `{a.out}` (local only -- embeds the personal plan, gitignored)",
         "- Source: **official** `jwba.ucas.ac.cn` crawl (`raw/official/`)", ""]
    for sem, t in terms.items():
        n_sched = sum(1 for r in t["rows"] if r["sessions"])
        L += [f"## {t['label']} ({sem})",
              f"- crawled at: {t['crawled_at']}",
              f"- courses: {len(t['rows'])}; with a parsed schedule: {n_sched}; without: {len(t['rows']) - n_sched}",
              f"- by attribute: " + ", ".join(f"{k}={v}" for k, v in Counter(r["attribute"] for r in t["rows"]).most_common()),
              f"- with capacity data: {sum(1 for r in t['rows'] if r['capacity'] is not None)}",
              ""]
    L += ["## Problems by kind", "", "| Kind | Count |", "| --- | --- |"]
    L += [f"| {k} | {v} |" for k, v in kinds.most_common()]
    L += ["", "## Samples (up to 4 per kind)", ""]
    shown = Counter()
    for i in issues:
        if shown[i["kind"]] >= 4:
            continue
        shown[i["kind"]] += 1
        loc = f" `{i.get('code','')}` {i.get('name','')}".rstrip()
        L.append(f"- **{i['kind']}** — {i['detail']}{loc}")
    head = "\n".join(L) + "\n"
    marker = "<!--MANUAL-->"
    manual = ""
    if os.path.exists(ISSUES):
        old = open(ISSUES, encoding="utf-8").read()
        if marker in old:
            manual = old.split(marker, 1)[1]
    if not manual:
        manual = "\n## Design problems met while building the prototype\n\n_TBD._\n"
    open(ISSUES, "w", encoding="utf-8").write(head + "\n" + marker + manual)
    print(f"[ok] wrote {a.out}")
    print(f"[ok] wrote {ISSUES}")
    print("problems by kind:", dict(kinds))
    for sem, t in terms.items():
        print(f"  {t['label']}: {len(t['rows'])} courses, "
              f"{sum(1 for r in t['rows'] if r['sessions'])} with schedule")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN" data-t="indigo"><head><meta charset="utf-8">
<title>选课参考 · 向导式</title>
<style>
:root{--chip:#eef1ec}
:root[data-t="teal"]{--bg:#f5f1e8;--ink:#173733;--ink2:#5b6b68;--card:#fff;--card2:#fbfaf6;--line:#e6e0d4;
--h1:#0b3f3b;--h2:#17665d;--h3:#357b82;--accent:#17665d;--accent2:#357b82;--accent-soft:#f0f7f3;--accent-line:#bcd9cd;
--chip:#eef1ec;--chipOnBg:#e2efe9;--chipOnLine:#bcd9cd;--chipOnInk:#14574f;--ok:#1a7f4b;--warn:#b26a00;--bad:#b3261e;
--okSoft:#f2fbf6;--okLine:#bfe3cd;--badSoft:#fdf0ee;--warnSoft:#fdf6e6;--warnLine:#f0e0b8}
:root[data-t="blue"]{--bg:#f3f6fb;--ink:#132540;--ink2:#5a6b83;--card:#fff;--card2:#f7f9fc;--line:#dde5ef;
--h1:#0e2a52;--h2:#1d4ed8;--h3:#3b82f6;--accent:#1d4ed8;--accent2:#3b82f6;--accent-soft:#eef4ff;--accent-line:#c3d6f7;
--chip:#eaf0f8;--chipOnBg:#e3edff;--chipOnLine:#c3d6f7;--chipOnInk:#14409c;--ok:#12784a;--warn:#a85f00;--bad:#b3261e;
--okSoft:#f1faf5;--okLine:#bfe3cd;--badSoft:#fdf0ee;--warnSoft:#fdf7e8;--warnLine:#f0e2c0}
:root[data-t="graphite"]{--bg:#f4f4f2;--ink:#22252a;--ink2:#6b7078;--card:#fff;--card2:#f8f8f7;--line:#e2e2df;
--h1:#24282e;--h2:#4a4a46;--h3:#8a6a3a;--accent:#8a5a12;--accent2:#a9741f;--accent-soft:#fbf6ec;--accent-line:#e6d6b6;
--chip:#eeeeec;--chipOnBg:#f6efe2;--chipOnLine:#e6d6b6;--chipOnInk:#6d4710;--ok:#1a7f4b;--warn:#b26a00;--bad:#b3261e;
--okSoft:#f2fbf6;--okLine:#bfe3cd;--badSoft:#fdf0ee;--warnSoft:#fdf6e6;--warnLine:#f0e0b8}
:root[data-t="indigo"]{--bg:#f6f6fb;--ink:#1c1a38;--ink2:#63607f;--card:#fff;--card2:#f8f8fd;--line:#e4e3f0;
--h1:#221b52;--h2:#4f46e5;--h3:#7c74ea;--accent:#4f46e5;--accent2:#7c74ea;--accent-soft:#f0effe;--accent-line:#cdc9f7;
--chip:#eef0f7;--chipOnBg:#eae8fd;--chipOnLine:#cdc9f7;--chipOnInk:#3b34b8;--ok:#12784a;--warn:#a85f00;--bad:#b3261e;
--okSoft:#f1faf5;--okLine:#bfe3cd;--badSoft:#fdf0ee;--warnSoft:#fdf7e8;--warnLine:#f0e2c0}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.65 Arial,"PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:14px 16px 70px}
.notice{font-size:12px;color:var(--ink2);line-height:1.7;padding:6px 0 10px}
.notice b{color:var(--ink)}
.topbar{background:linear-gradient(120deg,var(--h1),var(--h2) 55%,var(--h3));border-radius:16px;color:#f2f4ff;
padding:20px 24px;display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap;
box-shadow:0 6px 20px rgba(20,30,60,.18)}
.topbar .sem{font-size:13px;opacity:.85;letter-spacing:.06em}
.topbar h1{margin:4px 0 0;font-size:31px;font-weight:700;letter-spacing:.08em}
.topbar .side{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.28);border-radius:12px;padding:9px 13px;min-width:120px}
.topbar .side .k{font-size:11.5px;opacity:.85}
.topbar .side .v{font-size:19px;font-weight:700;margin-top:2px}
.topbar .pills .pill{background:rgba(255,255,255,.14);border-color:rgba(255,255,255,.3);color:#f2f4ff}
.topbar .pills .pill.on{background:#fff;color:var(--accent);border-color:#fff;font-weight:700}
.stepper{display:flex;gap:6px;margin:14px 0 12px;flex-wrap:wrap}
.stp{flex:1 1 200px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:9px 12px;cursor:pointer;position:relative}
.stp .n{font-size:11.5px;color:var(--ink2)}
.stp .t{font-size:13.5px;font-weight:600;margin-top:1px}
.stp .s{font-size:11.5px;color:var(--ink2);margin-top:2px}
.stp.on{border-color:var(--accent);background:var(--accent-soft)}
.stp.on .n{color:var(--accent)}
.stp.done{border-color:var(--okLine);background:var(--okSoft)}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:15px 17px;margin-bottom:13px}
.card>h2{margin:0 0 3px;font-size:18px}
.card>.sub{font-size:12.5px;color:var(--ink2);margin-bottom:11px}
.step{display:none}.step.on{display:block}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
input,select{padding:6px 9px;border:1px solid var(--line);border-radius:9px;font:inherit;background:#fff;color:var(--ink)}
input::placeholder{color:#a9b1af}
.btn{border:1px solid var(--line);background:#fff;border-radius:9px;padding:6px 12px;font:inherit;cursor:pointer;color:var(--ink)}
.btn:hover{border-color:var(--accent-line)}
.btn.p{background:var(--accent);color:#fff;border-color:var(--accent)}
.btn.p:hover{filter:brightness(1.08)}
.btn.sm{padding:3px 9px;font-size:12.5px}
.btn[disabled]{opacity:.45;cursor:not-allowed}
.pills{display:flex;gap:6px;flex-wrap:wrap}
.pill{border:1px solid var(--line);background:var(--card2);border-radius:999px;padding:3px 11px;font-size:12.5px;cursor:pointer}
.pill.on{background:var(--accent);border-color:var(--accent);color:#fff}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}
thead th{color:var(--ink2);font-weight:600;font-size:12.5px;background:var(--card2)}
tbody tr:hover{background:var(--card2)}
tr.pick{background:var(--accent-soft)}
.tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:999px;border:1px solid var(--line);color:var(--ink2);background:#fff}
.tag.full{color:#fff;background:var(--bad);border-color:var(--bad)}
.tag.near{color:#fff;background:var(--warn);border-color:var(--warn)}
.tag.ok{color:var(--ok);border-color:var(--okLine);background:var(--okSoft)}
.tag.acc{color:#fff;background:var(--accent);border-color:var(--accent)}
.tag.t0{color:#fff;background:var(--bad);border-color:var(--bad)}
.tag.t1{color:#fff;background:var(--warn);border-color:var(--warn)}
.scroll{max-height:420px;overflow:auto;border:1px solid var(--line);border-radius:10px}
a.cl{color:inherit;text-decoration:none;border-bottom:1px dashed var(--accent-line)}
a.cl:hover{color:var(--accent);border-bottom-color:var(--accent)}
.req{background:var(--card2);border:1px solid var(--line);border-radius:12px;padding:11px 13px;margin-top:9px}
.reqrow{display:flex;justify-content:space-between;align-items:baseline;gap:10px;padding:5px 0;border-bottom:1px dashed var(--line);font-size:13.5px}
.reqrow:last-child{border-bottom:none}
.gap{color:var(--bad)}.okr{color:var(--ok)}
.bar{height:6px;background:var(--line);border-radius:4px;overflow:hidden;margin-top:7px}
.bar>i{display:block;height:100%;background:var(--accent)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:11px;margin-bottom:12px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:11px 13px}
.stat .k{font-size:12.5px;color:var(--ink2)}
.stat .v{font-size:24px;font-weight:700;margin-top:3px}
.stat .v small{font-size:12.5px;font-weight:400;color:var(--ink2)}
.tt{width:100%;border-collapse:collapse;table-layout:fixed}
.tt th,.tt td{border:1px solid var(--line);padding:3px;font-size:11.5px;vertical-align:top;height:40px}
.tt thead th{background:var(--card2);text-align:center}
.tt td.per{background:var(--card2);text-align:center;width:74px;font-size:11px;color:var(--ink2)}
.tt .ev{background:var(--chipOnBg);border-left:3px solid var(--accent);border-radius:4px;padding:2px 5px;margin:1px 0;font-size:11px;line-height:1.3}
.tt .ev.aux{background:var(--accent-soft);border-left-color:var(--accent2)}
.tt .ev.c{background:var(--badSoft);border-left-color:var(--bad)}
.tt .free{color:#c7cbd6;font-size:10.5px;text-align:center;display:block;padding-top:9px}
.empty{color:var(--ink2);font-size:12.5px;padding:7px 2px}
.navbtns{display:flex;gap:10px;align-items:center;margin-top:6px}
.navbtns .sp{flex:1;font-size:12.5px;color:var(--ink2)}
textarea{width:100%;min-height:190px;border:1px solid var(--line);border-radius:10px;padding:10px;font:12.5px/1.6 Menlo,monospace;background:var(--card2);color:var(--ink)}
footer{margin-top:16px;font-size:12px;color:var(--ink2);line-height:1.8}
.warnbox{background:var(--warnSoft);border:1px solid var(--warnLine);border-radius:10px;padding:9px 12px;font-size:12.5px;margin-top:9px}
.legend{font-size:12px;color:var(--ink2);margin:6px 0 8px}
</style></head><body><div class="wrap">
<div class="notice" id="notice"></div>
<div class="topbar">
  <div><div class="sem" id="heroSem"></div><h1>选课参考 · 向导</h1></div>
  <div class="side"><div class="k">硕士英语</div><div class="v" id="eng"></div></div>
  <div class="side" style="min-width:190px"><div class="k">配色</div><div class="pills" id="themePills"></div></div>
</div>
<div class="stepper" id="stepper"></div>

<!-- 步骤 1 -->
<div class="step" data-s="1">
  <div class="card">
    <h2>第 1 步 · 先看"要修多少分"</h2>
    <div class="sub">这些要求不在任何课程数据里，只能来自培养方案文件；先明确目标，再挑课</div>
    <div id="s1req"></div>
    <div class="warnbox" id="s1note"></div>
  </div>
  <div class="card">
    <h2>本学期的目标清单</h2>
    <div class="sub">按培养方案换算到"这一个学期"要满足什么</div>
    <div id="s1goal"></div>
  </div>
</div>

<!-- 步骤 2 -->
<div class="step" data-s="2">
  <div class="card">
    <h2>第 2 步 · 挑必选课（主线）</h2>
    <div class="sub">候选范围 = 本学期（秋季）官方开放、且属性属于必修类的课；挑出来的课构成"主线"，第 3 步会被冻结</div>
    <div id="s2stats"></div>
    <div class="row" style="margin-bottom:9px">
      <input id="q2" placeholder="课程名称 / 编码 / 教师" style="min-width:230px">
      <span class="pills" id="attr2"></span>
      <label style="font-size:12.5px"><input type="checkbox" id="onlyFree2"> 只看还有座位</label>
      <button class="btn sm" id="clear2">清空主线</button>
    </div>
    <div class="scroll"><table id="t2"><thead><tr>
      <th style="width:70px">操作</th><th>课程</th><th style="width:150px">属性 / 院系</th><th style="width:58px">学分</th>
      <th style="width:196px">教学周与节次</th><th style="width:92px">限选/已选</th><th style="width:78px">考核</th>
    </tr></thead><tbody></tbody></table></div>
    <div class="legend" id="leg2"></div>
  </div>
</div>

<!-- 步骤 3 -->
<div class="step" data-s="3">
  <div class="card">
    <h2>第 3 步 · 冻结主线，在剩余时间里加辅助课</h2>
    <div class="sub">主线一旦冻结就只考虑"剩下的时间"：与主线冲突的辅助课直接不可选，只处理辅助课内部的取舍</div>
    <div id="s3main"></div>
    <div class="row" style="margin:9px 0">
      <button class="btn" id="thaw">← 返回第 2 步改主线</button>
      <span style="font-size:12.5px;color:var(--ink2)" id="s3slots"></span>
      <span style="margin-left:auto;font-size:12.5px;color:var(--ink2)">查看第</span>
      <span class="pills" id="weekPills"></span>
      <span style="font-size:12.5px;color:var(--ink2)">教学周</span>
    </div>
    <div id="ttWrap"></div>
  </div>
  <div class="card">
    <h2>可选辅助课</h2>
    <div class="sub">默认只列"与主线不冲突"的课；打开开关可看全部（冲突的会标红并写明重叠周次）</div>
    <div class="row" style="margin-bottom:9px">
      <input id="q3" placeholder="课程名称 / 编码 / 教师" style="min-width:230px">
      <span class="pills" id="attr3"></span>
      <label style="font-size:12.5px"><input type="checkbox" id="onlyFree3"> 只看还有座位</label>
      <label style="font-size:12.5px"><input type="checkbox" id="showAll3"> 显示与主线冲突的课</label>
    </div>
    <div class="scroll"><table id="t3"><thead><tr>
      <th style="width:70px">操作</th><th>课程</th><th style="width:146px">属性 / 院系</th><th style="width:56px">学分</th>
      <th style="width:190px">教学周与节次</th><th style="width:96px">限选/已选</th><th style="width:64px">教师</th>
    </tr></thead><tbody></tbody></table></div>
    <div class="legend" id="leg3"></div>
  </div>
  <div class="card">
    <h2>冲突检查</h2>
    <div class="sub">三维判定（星期 ∧ 节次 ∧ 周次），并写出重叠的具体周次</div>
    <div id="s3conf"></div>
  </div>
</div>

<!-- 步骤 4 -->
<div class="step" data-s="4">
  <div class="card">
    <h2>第 4 步 · 学分缺口与补充建议</h2>
    <div class="sub">按培养方案的类别逐项核算，缺口直接给出候选补课（按"容易抢到"排序）</div>
    <div class="stats" id="s4stats"></div>
    <div id="s4req"></div>
  </div>
  <div class="card">
    <h2>缺口补课建议</h2>
    <div class="sub">只对"不达标"的类别给候选；排序依据 = 剩余座位多、不紧缺</div>
    <div id="s4fillers"></div>
  </div>
  <div class="card">
    <h2>抢课顺序</h2>
    <div class="sub">不可延性（仅本学期开）× 紧迫度（剩余座位）；主线与辅助分开列 —— 与"课程重要性"不是同一个序</div>
    <div id="s4order"></div>
  </div>
  <div class="card">
    <h2>参考选课单（可复制）</h2>
    <div class="sub">主线（已冻结）+ 与主线不冲突的辅助课；冲突项不会出现在这里</div>
    <div class="row" style="margin-bottom:8px"><button class="btn p" id="copy">复制清单</button><span id="copyMsg" style="font-size:12.5px;color:var(--ink2)"></span></div>
    <textarea id="sheet" readonly></textarea>
  </div>
</div>

<div class="navbtns">
  <button class="btn" id="prev">← 上一步</button>
  <span class="sp" id="stepCtx"></span>
  <button class="btn p" id="next">下一步 →</button>
</div>
<footer id="foot"></footer>
</div>
<script>
const D = /*__DATA__*/;
const WDN = ["","周一","周二","周三","周四","周五","周六","周日"];
const MAIN_ATTRS = ["公共必修课","学科核心课","专业核心课","专业课"];
const MAIN_NAMES = ["工程伦理"];
let step = 1, sem = D.this_semester, week = 2;
let main = new Set(), aux = new Set();
let a2 = new Set(), a3 = new Set();
const $ = s => document.querySelector(s);
const rows = () => (D.terms[sem] || {rows: []}).rows;
const byCode = () => new Map(rows().map(c => [c.code, c]));
const pick = (set) => [...set].map(k => byCode().get(k)).filter(Boolean);
function bj(iso){ if(!iso) return "未知"; try{ return new Date(iso).toLocaleString("zh-CN",
  {timeZone:"Asia/Shanghai",year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"});}catch(e){return iso;} }
function wks(a){ return a.map(([x,y]) => x===y ? ""+x : x+"-"+y).join(","); }
function sesStr(s){ return WDN[s.wd] + "第" + s.ps + (s.pe>s.ps ? "-"+s.pe : "") + "节"; }
function ovl(a,b){ return Math.max(a[0],b[0]) <= Math.min(a[1],b[1]); }
function conflict(a,b){
  if(!a||!b||a.code===b.code) return null;
  for(const x of a.sessions) for(const y of b.sessions){
    if(x.wd!==y.wd) continue;
    if(Math.max(x.ps,y.ps) > Math.min(x.pe,y.pe)) continue;
    const ov=[];
    for(const u of x.weeks) for(const v of y.weeks) if(ovl(u,v)) ov.push([Math.max(u[0],v[0]),Math.min(u[1],v[1])]);
    if(ov.length) return {wd:x.wd, weeks:ov};
  }
  return null;
}
function isMain(c){ return MAIN_ATTRS.includes(c.attribute) || MAIN_NAMES.some(n => c.name.includes(n)); }
function classify(c){
  const h = new Set();
  for(const k of D.categories){
    if(k.kind === "non_course") continue;
    for(const cp of (k.comps||[])) if(cp.needles.some(n => c.name.includes(n))) h.add(k.id);
    if((k.names||[]).some(n => c.name.includes(n))) h.add(k.id);
    if(c.attribute && (k.attrs||[]).includes(c.attribute)) h.add(k.id);
  }
  return h;
}
function tierOf(c){
  const s = c.sem_sets || [];
  if(!s.length) return ["PU","学期未知：官方工作簿里没有这个编码"];
  if(s.length===1 && s[0]!==D.this_semester) return ["PN", "本学期不开（" + s[0] + "）"];
  const urgent = !c.no_cap && c.left!==null && (c.left<=3 || (c.enrolled/c.capacity)>=0.9);
  const only = s.length===1 && s[0]===D.this_semester;
  if(only) return urgent ? ["P0","仅本学期开 + 已满/近满 → 第一个抢"] : ["P1","仅本学期开，不紧张"];
  return urgent ? ["P2","春秋都开但有竞争"] : ["P3","春秋都开且不紧张"];
}
function seatTag(c){
  if(c.no_cap) return '<span class="tag">不设限</span>';
  if(c.left===null) return '<span class="tag">—</span>';
  if(c.left<=0) return '<span class="tag full">已满' + (c.left<0 ? "（超额 "+(-c.left)+"）" : "") + '</span>';
  return '<span class="tag ' + (c.left<=3 ? "near" : "ok") + '">余 ' + c.left + '</span>';
}
function seatSub(c){
  if(c.no_cap) return (c.enrolled ?? "") + " / 不设限";
  return c.capacity!==null ? c.enrolled + "/" + c.capacity : "";
}
function timeCell(c){
  if(!c.sessions.length) return '<span class="tag">无时间数据</span>';
  return c.sessions.map(s => sesStr(s) + '<div style="font-size:11px;color:var(--ink2)">周 ' + wks(s.weeks) +
    (s.rooms && s.rooms[0] ? " · " + s.rooms[0] : "") + '</div>').join("");
}
function nameCell(c){
  return '<b><a class="cl" target="_blank" rel="noopener" title="官方课程大纲" ' +
    'href="https://jwba.ucas.ac.cn/sc/course/courseplan/' + c.cid + '">' + c.name + ' ↗</a></b>' +
    '<div style="font-size:11.5px"><a class="cl" target="_blank" rel="noopener" title="官方时间地点" ' +
    'href="https://jwba.ucas.ac.cn/sc/course/coursetime/' + c.cid + '">' + c.code + '</a></div>';
}
/* ---------- 步骤条 ---------- */
const STEPS = [
  ["第 1 步","先看要修多少分","按培养方案核对学分要求"],
  ["第 2 步","挑必选课（主线）","本学期开放的必修类课程"],
  ["第 3 步","冻结主线 · 加辅助","只考虑剩余时间"],
  ["第 4 步","学分缺口与补充建议","含抢课顺序与清单"]
];
function renderStepper(){
  const done = (i) => i < step;
  $("#stepper").innerHTML = STEPS.map((s,i) =>
    '<div class="stp ' + (i+1===step ? "on" : (done(i+1) ? "done" : "")) + '" data-s="' + (i+1) + '">' +
    '<div class="n">' + s[0] + (done(i+1) ? " ✓" : "") + '</div><div class="t">' + s[1] + '</div>' +
    '<div class="s">' + s[2] + '</div></div>').join("");
  [...document.querySelectorAll(".stp")].forEach(e => e.onclick = () => goto(+e.dataset.s));
  document.querySelectorAll(".step").forEach(e => e.classList.toggle("on", +e.dataset.s === step));
  $("#prev").disabled = step === 1; $("#next").disabled = step === 4;
  $("#prev").textContent = "← 上一步"; $("#next").textContent = "下一步 →";
  const ctx = {1:"", 2:"已挑 " + main.size + " 门主线", 3:"主线 " + main.size + " + 辅助 " + aux.size,
               4:"共 " + (main.size + aux.size) + " 门"}[step];
  $("#stepCtx").textContent = ctx;
}
function goto(n){ step = Math.min(4, Math.max(1, n)); renderStepper(); renderAll(); window.scrollTo({top:0,behavior:"smooth"}); }

/* ---------- 步骤 1 ---------- */
function renderS1(){
  const t = D.terms[sem] || {};
  let h = "";
  for(const k of D.categories){
    if(k.kind === "non_course"){
      h += '<div class="reqrow"><span>' + k.name + '</span><span>' + k.min_credits +
        ' 分 · <span class="tag">不计入课程学分</span></span></div>';
      continue;
    }
    let s = k.min_credits ? (k.min_credits + " 分") : "无最低要求";
    if(k.min_courses) s += ' · 且不少于 ' + k.min_courses + ' 门';
    h += '<div class="reqrow"><span>' + k.name + '</span><span class="r">' + s + '</span></div>';
    if(k.comps && k.comps.length){
      h += k.comps.map(cp => '<div style="font-size:12px;color:var(--ink2);padding-left:2px">· ' +
        cp.needles[0] + ' ' + cp.credits + ' 分</div>').join("");
    }
  }
  $("#s1req").innerHTML = '<div style="font-size:12.5px;color:var(--ink2);margin-bottom:6px">来源：' +
    '《中国科学院大学电子信息专业学位研究生培养方案》校发培养字〔2025〕92号（已抽成 data/degree-requirements.json）</div>' + h;
  $("#s1note").innerHTML = '注意：' + '<b>只有开课学期</b>来自官方工作簿，' +
    '<b>学分/属性/校区/限选</b>来自官方教务公开库；两者编码只有 212 门对得上（共 341 门），' +
    '查不到学期的课会在最后一步落到 <b>PU</b> 档，届时要人工确认。';
  const need = D.degree_track || {};
  $("#s1goal").innerHTML =
    '<div class="reqrow"><span>本学期有效学分下限</span><span class="r">≥ ' + D.semester_min_credits + ' 分</span></div>' +
    '<div class="reqrow"><span>课程学习总学分下限（含春季）</span><span class="r">≥ ' + D.course_learning_min + ' 分</span></div>' +
    '<div class="reqrow"><span>专业学位课下限</span><span class="r">≥ ' + D.professional_degree_min + ' 分</span></div>' +
    '<div class="reqrow"><span>硕士英语</span><span class="r">' + D.english + '</span></div>' +
    '<div class="empty">也就是说：本学期先把"公共学位课 + 专业学位课（核心≥2门、专业课≥2门）"这条主线立住，' +
    '再用公共选修/专业选修把学分和缺口补齐。</div>';
}

/* ---------- 步骤 2 ---------- */
function renderS2(){
  const q = $("#q2").value.trim(), free = $("#onlyFree2").checked;
  const cand = rows().filter(c => isMain(c));
  const list = cand.filter(c => {
    if(q && !(c.name.includes(q) || c.code.includes(q) || (c.teacher||"").includes(q))) return false;
    if(a2.size && !a2.has(c.attribute)) return false;
    if(free && !(c.left > 0)) return false;
    return true;
  });
  const p2 = pick(main);
  let tot = 0; const cat = {};
  for(const c of p2){ tot += c.credit; for(const id of classify(c)) cat[id] = (cat[id]||0) + c.credit; }
  $("#s2stats").innerHTML = '<div class="stats">' +
    '<div class="stat"><div class="k">已挑主线</div><div class="v">' + p2.length + ' <small>门</small></div></div>' +
    '<div class="stat"><div class="k">主线学分</div><div class="v">' + tot.toFixed(1) + ' <small>分</small></div></div>' +
    '<div class="stat"><div class="k">专业学位课（核心+专业）</div><div class="v">' +
      (((cat["professional_degree_core"]||0) + (cat["professional_degree_major"]||0))).toFixed(1) + ' <small>分</small></div></div>' +
    '<div class="stat"><div class="k">候选池（本学期必修类）</div><div class="v">' + cand.length + ' <small>门</small></div>' +
      '<div style="font-size:11.5px;color:var(--ink2)">已满 ' + cand.filter(c => c.left===0).length + ' 门</div></div></div>';
  const tb = $("#t2 tbody"); tb.innerHTML = "";
  for(const c of list.slice(0, 700)){
    const tr = document.createElement("tr");
    if(main.has(c.code)) tr.className = "pick";
    tr.innerHTML = '<td><button class="btn sm">' + (main.has(c.code) ? "移出" : "加入") + '</button></td>' +
      '<td>' + nameCell(c) + ((D.english||"").includes("免修") && c.name.includes("英语")
          ? ' <span class="tag">英语已免修 · 通常无需选</span>' : '') + '</td>' +
      '<td>' + c.attribute + '<div style="font-size:11.5px;color:var(--ink2)">' + c.department + '</div></td>' +
      '<td>' + c.credit.toFixed(1) + '</td><td>' + timeCell(c) + '</td>' +
      '<td>' + seatTag(c) + '<div style="font-size:11.5px;color:var(--ink2)">' + seatSub(c) + '</div></td>' +
      '<td>' + (c.exam || "—") + '</td>';
    tr.querySelector("button").onclick = () => {
      if(main.has(c.code)) main.delete(c.code); else main.add(c.code);
      renderAll();
    };
    tb.appendChild(tr);
  }
  $("#leg2").innerHTML = '显示 ' + Math.min(list.length,700) + ' / 候选 ' + cand.length +
    ' 门｜这一池是<b>本学期开放的必修类课程</b>（公共必修 / 学科核心 / 专业核心 / 专业课 + 工程伦理）；' +
    '已满 ' + cand.filter(c=>c.left===0).length + ' 门';
}

/* ---------- 步骤 3 ---------- */
function mainSlots(){
  const cells = [];
  for(const c of pick(main)) for(const s of c.sessions) cells.push({c: c, s: s});
  return cells;
}
function renderS3(){
  const pm = pick(main);
  $("#s3main").innerHTML = '<div class="req" style="margin-top:0">' +
    '<div style="font-size:12.5px;color:var(--ink2);margin-bottom:5px">主线（已冻结）—— ' + pm.length + ' 门</div>' +
    (pm.length ? pm.map(c => '<div class="reqrow"><span><span class="tag acc">主</span> ' + c.name +
      '</span><span style="font-size:12.5px">' + c.sessions.map(s=>sesStr(s)).join("；") + '</span></div>').join("")
      : '<div class="empty">还没挑主线，请回第 2 步。</div>') + '</div>';
  const slots = mainSlots();
  const occ = new Set(); for(const x of slots) if(x.s.weeks.some(([a,b]) => week>=a && week<=b)) occ.add(x.s.wd + "-" + x.s.ps);
  $("#s3slots").textContent = "第 " + week + " 周占用 " + occ.size + " 个格子（共 13×7=91 个时段）";
  const mk = pick(main), ax = pick(aux);
  const conflictSet = new Set();
  for(const a of mk) for(const b of ax){ if(conflict(a,b)){ conflictSet.add(a.code); conflictSet.add(b.code); } }
  let h = '<table class="tt"><thead><tr><th style="width:74px">节次 / 时间</th>';
  for(let d=1; d<=7; d++) h += '<th>' + WDN[d] + '</th>';
  h += '</tr></thead><tbody>';
  D.periods.forEach(([n, tm], idx) => {
    h += '<tr><td class="per">第 ' + n + ' 节<br>' + tm + '</td>';
    for(let d=1; d<=7; d++){
      const cs = [];
      for(const x of slots) if(x.s.wd===d && week>=x.s.weeks[0][0]){
        const inRange = x.s.weeks.some(([a,b]) => week>=a && week<=b);
        if(inRange && idx+1 >= x.s.ps && idx+1 <= x.s.pe) cs.push({c:x.c, k:"main"});
      }
      for(const c of ax) for(const s of c.sessions){
        const inRange = s.weeks.some(([a,b]) => week>=a && week<=b);
        if(inRange && s.wd===d && idx+1>=s.ps && idx+1<=s.pe) cs.push({c:c, k: conflictSet.has(c.code) ? "c" : "aux"});
      }
      h += '<td>' + (cs.length ? cs.map(x => '<div class="ev ' + (x.k==="main"?"":x.k) + '">' + x.c.name + '</div>').join("")
        : '<span class="free">空闲</span>') + '</td>';
    }
    h += '</tr>';
  });
  h += '</tbody></table>';
  $("#ttWrap").innerHTML = h;
  $("#weekPills").innerHTML = Array.from({length:20}, (_,i) => i+1)
    .map(w => '<span class="pill ' + (w===week ? "on" : "") + '" data-w="' + w + '">' + w + '</span>').join("");
  [...document.querySelectorAll("#weekPills .pill")].forEach(e => e.onclick = () => { week = +e.dataset.w; renderS3(); });

  const q = $("#q3").value.trim(), free = $("#onlyFree3").checked, showAll = $("#showAll3").checked;
  const cand = rows().filter(c => !main.has(c.code));
  const list = cand.filter(c => {
    const cf = pick(main).some(m => conflict(m, c));
    if(cf && !showAll) return false;
    if(q && !(c.name.includes(q) || c.code.includes(q) || (c.teacher||"").includes(q))) return false;
    if(a3.size && !a3.has(c.attribute)) return false;
    if(free && !(c.left > 0)) return false;
    return true;
  });
  const tb = $("#t3 tbody"); tb.innerHTML = "";
  for(const c of list.slice(0, 700)){
    const bad = pick(main).map(m => [m, conflict(m, c)]).filter(x => x[1]);
    const tr = document.createElement("tr");
    if(bad.length) tr.style.opacity = ".62";
    if(aux.has(c.code)) tr.className = "pick";
    tr.innerHTML = '<td>' + (bad.length
        ? '<button class="btn sm" disabled title="与主线冲突">不可选</button>'
        : '<button class="btn sm">' + (aux.has(c.code) ? "移出" : "加入") + '</button>') + '</td>' +
      '<td>' + nameCell(c) + '</td>' +
      '<td>' + c.attribute + '<div style="font-size:11.5px;color:var(--ink2)">' + c.department + '</div></td>' +
      '<td>' + c.credit.toFixed(1) + '</td><td>' + timeCell(c) + '</td>' +
      '<td>' + seatTag(c) + '<div style="font-size:11.5px;color:var(--ink2)">' + seatSub(c) + '</div></td>' +
      '<td style="font-size:12px">' + (c.teacher || "—") + '</td>';
    if(!bad.length) tr.querySelector("button").onclick = () => {
      if(aux.has(c.code)) aux.delete(c.code); else aux.add(c.code);
      renderAll();
    };
    tb.appendChild(tr);
  }
  $("#leg3").innerHTML = '显示 ' + Math.min(list.length,700) + ' / 候选 ' + cand.length +
    ' 门｜' + (aux.size ? '已加辅助 ' + aux.size + ' 门' : '还没加辅助课') +
    '｜ ' + '<span class="tag">不可选</span> = 与主线时间冲突（打开上面的开关可查看原因）';
}
function renderS3conf(){
  const all = pick(main).concat(pick(aux));
  const out = [];
  for(let i=0;i<all.length;i++) for(let j=i+1;j<all.length;j++){
    const cf = conflict(all[i], all[j]);
    if(!cf) continue;
    const mm = main.has(all[i].code) && main.has(all[j].code);
    const ma = (main.has(all[i].code) && aux.has(all[j].code)) || (aux.has(all[i].code) && main.has(all[j].code));
    out.push({a: all[i], b: all[j], cf: cf, kind: mm ? "主线⟷主线" : (ma ? "主线⟷辅助" : "辅助⟷辅助")});
  }
  $("#s3conf").innerHTML = out.length ? out.map(x =>
    '<div style="padding:7px 2px;border-bottom:1px dashed var(--line)">' +
    '<div><span class="gap">冲突</span> · ' + x.kind + ' · ' + WDN[x.cf.wd] + ' 第 ' +
      x.cf.weeks.map(w => w[0]===w[1] ? w[0] : w[0]+"-"+w[1]).join(",") + ' 周' +
      (x.kind==="主线⟷主线" ? '　<span class="tag full">需回第 2 步解决</span>' : '') + '</div>' +
    '<div style="font-size:12.5px;color:var(--ink2)">' + x.a.name + ' ⟷ ' + x.b.name + '</div></div>').join("")
    : '<div class="empty">' + (all.length ? "当前所选之间没有三维冲突。" : "还没有选课。") + '</div>';
}

/* ---------- 步骤 4 ---------- */
function accounting(){
  const all = pick(main).concat(pick(aux));
  let total = 0, thisSem = 0, doctoral = 0;
  for(const c of all){
    if(c.term === "博士"){ doctoral += c.credit; continue; }
    total += c.credit;
    if((c.sem_sets||[]).includes(D.this_semester)) thisSem += c.credit;
  }
  const got = {}, cnt = {};
  for(const c of all) for(const id of classify(c)){ got[id] = (got[id]||0) + c.credit; cnt[id] = (cnt[id]||0) + 1; }
  return {all: all, total: total, thisSem: thisSem, doctoral: doctoral, got: got, cnt: cnt};
}
function renderS4(){
  const A = accounting();
  const pdeg = (A.got["professional_degree_core"]||0) + (A.got["professional_degree_major"]||0);
  const psel = A.got["professional_elective"] || 0;
  const mk = (k, v, need) => {
    const p = need ? Math.min(100, v/need*100) : 0;
    return '<div class="stat"><div class="k">' + k + '</div><div class="v ' + (need && v<need ? "gap" : "okr") + '">' +
      v.toFixed(1) + ' <small>/ ' + need + ' 分</small></div><div class="bar"><i style="width:' + p + '%"></i></div></div>';
  };
  $("#s4stats").innerHTML = mk("本学期有效学分", A.thisSem, D.semester_min_credits) +
    mk("专业学位课", pdeg, D.professional_degree_min) + mk("公共选修", A.got["public_elective"]||0, 2) +
    mk("专业选修", psel, 2);
  let h = '<div class="req"><div style="font-size:12.5px;color:var(--ink2);margin-bottom:5px">培养要求检查（硕士）</div>';
  for(const k of D.categories){
    if(k.kind === "non_course"){
      h += '<div class="reqrow"><span>' + k.name + '</span><span>' + k.min_credits +
        ' 分 · <span class="tag">不计入课程学分</span></span></div>';
      continue;
    }
    const g = A.got[k.id]||0, n = k.min_credits||0, c2 = A.cnt[k.id]||0;
    let st = g>=n ? '<span class="okr">' + g.toFixed(1) + ' / ' + n + '</span>'
                  : '<span class="gap">' + g.toFixed(1) + ' / ' + n + ' 缺 ' + (n-g).toFixed(1) + '</span>';
    if(k.min_courses) st += ' <span class="tag ' + (c2>=k.min_courses ? "ok" : "") + '">门数 ' + c2 + '/' + k.min_courses + '</span>';
    h += '<div class="reqrow"><span>' + k.name + '</span><span class="r">' + st + '</span></div>';
    if(k.comps && k.comps.length){
      h += k.comps.map(cp => {
        const v = A.all.filter(c => cp.needles.some(x => c.name.includes(x))).reduce((s,c) => s + c.credit, 0);
        return '<div style="font-size:12px;color:var(--ink2);padding-left:2px">· ' + cp.needles[0] + ' ' + v + '/' + cp.credits +
          (v < cp.credits && cp.needles.join().includes("英语") ? '　<span class="tag">已走' + D.english + '路径则无需选课</span>' : '') + '</div>';
      }).join("");
    }
  }
  h += '<div class="reqrow"><span>课程学习总学分（含春季）</span><span class="r">' +
    (A.total >= D.course_learning_min ? '<span class="okr">' + A.total.toFixed(1) + ' / ≥' + D.course_learning_min + '</span>'
      : '<span class="gap">' + A.total.toFixed(1) + ' / ≥' + D.course_learning_min + ' 缺 ' + (D.course_learning_min-A.total).toFixed(1) + '</span>') +
    '</div></div>';
  $("#s4req").innerHTML = h;

  const short = [];
  for(const k of D.categories){
    if(k.kind === "non_course" || !k.min_credits) continue;
    const g = A.got[k.id]||0;
    if(g < k.min_credits) short.push({k: k, need: k.min_credits - g});
  }
  $("#s4fillers").innerHTML = short.length ? short.map(s => {
    const cand = rows().filter(c => {
      if(!((s.k.attrs||[]).includes(c.attribute) || (s.k.names||[]).some(n => c.name.includes(n)))) return false;
      if(aux.has(c.code) || main.has(c.code)) return false;
      if(pick(main).some(m => conflict(m, c))) return false;
      return c.left === null || c.left > 0;
    }).sort((x,y) => (y.left ?? 9999) - (x.left ?? 9999)).slice(0, 6);
    return '<div style="padding:7px 2px;border-bottom:1px dashed var(--line)">' +
      '<div><b>' + s.k.name + '</b> 缺 <span class="gap">' + s.need.toFixed(1) + ' 分</span></div>' +
      (cand.length ? '<div style="font-size:12.5px;color:var(--ink2)">候选：' + cand.map(c =>
        c.name + '（' + c.credit.toFixed(1) + '分，' + (c.no_cap ? "不设限" : "余 " + c.left) + '）').join("；") + '</div>'
        : '<div class="empty">没有既满足类别、又不与主线冲突的候选，需回第 2 步调整主线。</div>') + '</div>';
  }).join("") : '<div class="empty">各课程类别都已达标，不需要补课。</div>';

  const ord = (s) => pick(s).map(c => { const t = tierOf(c); return {c: c, t: t[0], w: t[1]}; })
    .sort((x,y) => (x.t < y.t ? -1 : x.t > y.t ? 1 : 0) || ((x.c.left ?? 1e9) - (y.c.left ?? 1e9)));
  const block = (title, list) => '<div style="font-size:12.5px;color:var(--ink2);margin:8px 0 3px">' + title + '</div>' +
    (list.length ? list.map((k,i) => '<div class="reqrow"><span><span class="tag ' +
      (k.t==="P0" ? "t0" : k.t==="P1" ? "t1" : "") + '">' + k.t + '</span> ' + (i+1) + '. ' + k.c.name +
      '</span><span style="font-size:12.5px">' + (k.c.no_cap ? "不设限选" : (k.c.left===null ? "座位未知" : (k.c.left<=0 ? "已满" : "剩余 " + k.c.left))) +
      '</span></div><div style="font-size:12px;color:var(--ink2)">' + k.w + '</div>').join("")
      : '<div class="empty">—</div>');
  $("#s4order").innerHTML = block("主线（先保证这几门）", ord(main)) + block("辅助（有位置再加）", ord(aux));

  const lines = [];
  lines.push("【选课参考单】" + ((D.terms[sem]||{}).label || sem) + " · 玉泉路");
  lines.push("生成时间：" + (D.generated || "") + "　数据来源：官方教务公开库 jwba.ucas.ac.cn（抓取 " +
    bj((D.terms[sem]||{}).crawled_at) + "）");
  lines.push("");
  lines.push("■ 主线（已冻结，共 " + pick(main).length + " 门）");
  pick(main).forEach((c,i) => lines.push("  " + (i+1) + ". " + c.name + "  " + c.credit.toFixed(1) + "分  " +
    c.attribute + "  " + c.sessions.map(s => sesStr(s) + "(周" + wks(s.weeks) + ")").join("；") +
    "  " + (c.no_cap ? "不设限" : (c.left===null ? "座位未知" : (c.left<=0 ? "已满" : "余" + c.left)))));
  lines.push("");
  lines.push("■ 辅助（与主线无冲突，共 " + pick(aux).length + " 门）");
  pick(aux).forEach((c,i) => lines.push("  " + (i+1) + ". " + c.name + "  " + c.credit.toFixed(1) + "分  " +
    c.attribute + "  " + c.sessions.map(s => sesStr(s) + "(周" + wks(s.weeks) + ")").join("；") +
    "  " + (c.no_cap ? "不设限" : (c.left===null ? "座位未知" : (c.left<=0 ? "已满" : "余" + c.left)))));
  lines.push("");
  lines.push("■ 学分核算");
  const A2 = accounting();
  lines.push("  本学期有效学分 " + A2.thisSem.toFixed(1) + " / ≥" + D.semester_min_credits +
    "　课程学习总学分 " + A2.total.toFixed(1) + " / ≥" + D.course_learning_min);
  for(const k of D.categories){
    if(k.kind === "non_course") continue;
    lines.push("  " + k.name + "：" + (A2.got[k.id]||0).toFixed(1) + " / " + (k.min_credits||0));
  }
  lines.push("");
  lines.push("■ 抢课顺序");
  ord(main).concat(ord(aux)).forEach((k,i) => lines.push("  " + (i+1) + ". [" + k.t + "] " + k.c.name + " —— " + k.w));
  lines.push("");
  lines.push("注：本清单只做规划与冲突检查，不涉及任何自动提交；时间/容量以官方系统为准。");
  $("#sheet").value = lines.join("\n");
}

/* ---------- 公共 ---------- */
function renderAll(){
  renderTop(); renderS1(); renderS2(); renderS3(); renderS3conf(); renderS4(); renderStepper();
}
function renderTop(){
  const t = D.terms[sem] || {};
  $("#notice").innerHTML = '数据来源：<b>中国科学院大学教务公开库</b>（jwba.ucas.ac.cn）—— 开课校区、限选/已选、' +
    '教学周与节次均为官方口径；开课学期取自官方工作簿。<br>抓取时点：<b>' + bj(t.crawled_at) +
    '</b>（本机冻结，页面不联网）· 秋季学期共 20 教学周。<br>' +
    '课程名称／课程编号可点击，直达官方「课程大纲」／「时间地点」页。' +
    '本页仅供规划参考，<b>数据与选课结果请以学校官方系统为准</b>。';
  $("#heroSem").textContent = t.label || sem;
  $("#eng").textContent = D.english;
  $("#foot").innerHTML = '数据来源：中国科学院大学教务公开库（jwba.ucas.ac.cn）／官方开课计划工作簿；' +
    '学分要求取自《电子信息专业学位研究生培养方案》（校发培养字〔2025〕92号）。<br>' +
    '本页为本地原型，只读本地数据、不联网、不上传；<b>自动抢课与自动提交属明确非目标</b>。';
}
function renderFilters(){
  const at2 = [...new Set(rows().filter(c => isMain(c)).map(c => c.attribute))].sort();
  $("#attr2").innerHTML = at2.map(a => '<span class="pill ' + (a2.has(a) ? "on" : "") + '" data-a="' + a + '">' + a + '</span>').join("");
  [...document.querySelectorAll("#attr2 .pill")].forEach(e => e.onclick = () => {
    const a = e.dataset.a; a2.has(a) ? a2.delete(a) : a2.add(a); renderAll(); });
  const at3 = [...new Set(rows().filter(c => !isMain(c)).map(c => c.attribute))].sort();
  $("#attr3").innerHTML = at3.map(a => '<span class="pill ' + (a3.has(a) ? "on" : "") + '" data-a="' + a + '">' + a + '</span>').join("");
  [...document.querySelectorAll("#attr3 .pill")].forEach(e => e.onclick = () => {
    const a = e.dataset.a; a3.has(a) ? a3.delete(a) : a3.add(a); renderAll(); });
}
const THEMES = [["indigo","靛青"],["teal","墨绿（原站）"],["blue","蓝白"],["graphite","石墨琥珀"]];
function applyTheme(t){
  document.documentElement.dataset.t = t;
  $("#themePills").innerHTML = THEMES.map(([k,n]) =>
    '<span class="pill ' + (k===t ? "on" : "") + '" data-t="' + k + '">' + n + '</span>').join("");
  [...document.querySelectorAll("#themePills .pill")].forEach(e => e.onclick = () => {
    location.hash = "t=" + e.dataset.t; applyTheme(e.dataset.t); });
}
applyTheme((location.hash.match(/t=(\w+)/) || [])[1] || "indigo");
$("#prev").onclick = () => goto(step-1);
$("#next").onclick = () => goto(step+1);
$("#q2").oninput = renderS2; $("#onlyFree2").onchange = renderS2;
$("#q3").oninput = renderS3; $("#onlyFree3").onchange = renderS3; $("#showAll3").onchange = renderS3;
$("#clear2").onclick = () => { main.clear(); aux.clear(); renderAll(); };
$("#thaw").onclick = () => goto(2);
$("#copy").onclick = () => {
  const ta = $("#sheet"); ta.select();
  try{
    navigator.clipboard.writeText(ta.value).then(() => $("#copyMsg").textContent = "已复制到剪贴板",
      () => { document.execCommand("copy"); $("#copyMsg").textContent = "已复制（回退方式）"; });
  }catch(e){ document.execCommand("copy"); $("#copyMsg").textContent = "已复制（回退方式）"; }
};
// 初始化：把保存的方案拆成"主线 / 辅助"
const byC = byCode();
for(const k of D.plan_codes){
  const c = byC.get(k); if(!c) continue;
  if(isMain(c)) main.add(k); else aux.add(k);
}
renderFilters(); renderAll();
</script></body></html>
"""


if __name__ == "__main__":
    sys.exit(main())

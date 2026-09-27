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
<title>选课参考 · 本地版</title>
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
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.6 Arial,"PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:1240px;margin:0 auto;padding:14px 16px 60px}
.notice{font-size:12px;color:var(--ink2);line-height:1.75;padding:8px 0 12px}
.notice b{color:var(--ink)}
.hero{background:linear-gradient(120deg,var(--h1),var(--h2) 55%,var(--h3));border-radius:16px;color:#eaf3f1;
padding:22px 26px;display:flex;justify-content:space-between;align-items:flex-end;gap:18px;
box-shadow:0 6px 20px rgba(20,40,40,.16)}
.hero .sem{font-size:13px;opacity:.85;letter-spacing:.06em}
.hero h1{margin:6px 0 0;font-size:34px;font-weight:700;letter-spacing:.08em}
.hero .side{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.28);border-radius:12px;
padding:10px 14px;min-width:132px}
.hero .side .k{font-size:12px;opacity:.85}
.hero .side .v{font-size:20px;font-weight:700;margin-top:2px}
.hero .side button{margin-top:6px;font-size:12px;background:rgba(255,255,255,.16);color:#eaf3f1;
border:1px solid rgba(255,255,255,.3);border-radius:8px;padding:2px 8px;cursor:pointer}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 10px}
.chip{background:var(--chip);border:1px solid var(--line);border-radius:999px;padding:4px 12px;font-size:12.5px;color:var(--ink)}
.chip.on{background:var(--chipOnBg);border-color:var(--chipOnLine);color:var(--chipOnInk);font-weight:600}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:14px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 14px}
.stat .k{font-size:12.5px;color:var(--ink2)}
.stat .v{font-size:26px;font-weight:700;margin-top:4px}
.stat .v small{font-size:13px;font-weight:400;color:var(--ink2)}
.bar{height:6px;background:#ece8dc;border-radius:4px;margin-top:8px;overflow:hidden}
.bar>i{display:block;height:100%;background:var(--accent)}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin-bottom:14px}
.card>h2{margin:0 0 4px;font-size:19px}
.card>.sub{font-size:12.5px;color:var(--ink2);margin-bottom:10px}
.req{background:var(--card2);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin-top:10px}
.reqrow{display:flex;justify-content:space-between;align-items:baseline;gap:10px;padding:5px 0;border-bottom:1px dashed var(--line);font-size:13.5px}
.reqrow:last-child{border-bottom:none}
.reqrow .r{font-weight:600}
.gap{color:var(--bad)}.okr{color:var(--ok)}
.pills{display:flex;gap:6px;flex-wrap:wrap}
.pill{border:1px solid var(--line);background:var(--card2);border-radius:999px;padding:3px 11px;font-size:12.5px;cursor:pointer}
.pill.on{background:var(--accent);border-color:var(--accent);color:#fff}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
input,select{padding:6px 9px;border:1px solid var(--line);border-radius:9px;font:inherit;background:#fff;color:var(--ink)}
input::placeholder{color:#a9b1af}
.btn{border:1px solid var(--line);background:#fff;border-radius:9px;padding:6px 11px;font:inherit;cursor:pointer}
.btn:hover{border-color:#cfc8b8}
.btn.p{background:var(--accent);color:#fff;border-color:var(--accent)}
.btn.sm{padding:3px 9px;font-size:12.5px}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}
thead th{color:var(--ink2);font-weight:600;font-size:12.5px;background:var(--card2)}
tbody tr:hover{background:var(--card2)}
tr.sel{background:var(--accent-soft)}
tr.bad{background:var(--badSoft)}
a.cl{color:inherit;text-decoration:none;border-bottom:1px dashed var(--accent-line);cursor:pointer}
a.cl:hover{color:var(--accent);border-bottom-color:var(--accent)}
a.cl ext{font-size:10px}
.tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:999px;border:1px solid var(--line);color:var(--ink2);background:#fff}
.tag.full{color:#fff;background:var(--bad);border-color:var(--bad)}
.tag.near{color:#fff;background:var(--warn);border-color:var(--warn)}
.tag.ok{color:var(--ok);border-color:var(--okLine);background:var(--okSoft)}
.tag.t0{color:#fff;background:var(--bad);border-color:var(--bad)}
.tag.t1{color:#fff;background:var(--warn);border-color:var(--warn)}
.scroll{max-height:430px;overflow:auto;border:1px solid var(--line);border-radius:10px}
.tt{width:100%;border-collapse:collapse;table-layout:fixed}
.tt th,.tt td{border:1px solid var(--line);padding:4px;font-size:12px;vertical-align:top;height:46px}
.tt thead th{background:var(--card2);text-align:center}
.tt td.per{background:var(--card2);text-align:center;width:76px;font-size:11.5px;color:var(--ink2)}
.tt .ev{background:var(--chipOnBg);border-left:3px solid var(--accent);border-radius:5px;padding:3px 5px;margin:1px 0;font-size:11.5px;line-height:1.35}
.tt .ev.c{background:var(--badSoft);border-left-color:var(--bad)}
.empty{color:var(--ink2);font-size:12.5px;padding:8px 2px}
footer{margin-top:18px;font-size:12px;color:var(--ink2);line-height:1.8}
.warnbox{background:var(--warnSoft);border:1px solid var(--warnLine);border-radius:10px;padding:9px 12px;font-size:12.5px;margin-top:10px}
.legend{font-size:12px;color:var(--ink2);margin:6px 0 8px}
</style></head><body><div class="wrap">
<div class="notice" id="notice"></div>
<div class="hero">
  <div><div class="sem" id="heroSem"></div><h1>选课参考</h1></div>
  <div class="side"><div class="k">硕士英语</div><div class="v" id="eng"></div><button>修改</button></div>
</div>
<div class="chips" id="chips"></div>
<div class="stats" id="stats"></div>

<div class="row" id="themerow" style="justify-content:flex-end;margin:-4px 0 10px">
  <span style="font-size:12.5px;color:var(--ink2)">配色</span>
  <span class="pills" id="themePills"></span>
</div>

<div class="card">
  <h2>我的课程</h2>
  <div class="sub" id="selSub"></div>
  <div class="row" style="margin-bottom:10px">
    <button class="btn p" id="check">无时间冲突检查</button>
    <input id="bulk" placeholder="按课程编码批量添加，逗号分隔" style="min-width:280px">
    <button class="btn" id="bulkAdd">添加</button>
    <button class="btn" id="clear">清空</button>
  </div>
  <div id="selList"></div>
  <div class="req" id="req"></div>
</div>

<div class="card">
  <h2>时间冲突</h2>
  <div class="sub">三维判定：星期 ∧ 节次 ∧ 周次；并写出重叠的具体周次</div>
  <div id="conf"></div>
</div>

<div class="card">
  <h2>抢课顺序</h2>
  <div class="sub">不可延性（仅本学期开）× 紧迫度（剩余座位）—— 与"课程重要性"不是同一个序</div>
  <div id="order"></div>
</div>

<div class="card">
  <h2>实时课程表</h2>
  <div class="sub" id="ttSub"></div>
  <div class="row" style="margin-bottom:10px">
    <button class="btn" id="prevW">← 上一周</button>
    <span id="weekPills" class="pills"></span>
    <button class="btn" id="nextW">下一周 →</button>
    <select id="semSel" style="margin-left:auto"></select>
  </div>
  <div id="ttWrap"></div>
</div>

<div class="card">
  <h2>课程目录</h2>
  <div class="sub" id="catSub"></div>
  <div class="row" style="margin-bottom:8px">
    <span style="font-size:12.5px;color:var(--ink2)">课程数据</span>
    <span class="tag ok">使用官方公开库 <b id="poolNum"></b> 门</span>
  </div>
  <div class="row" style="margin-bottom:8px">
    <span style="font-size:12.5px;color:var(--ink2)">课程类型</span>
    <span class="pills" id="attrPills"></span>
    <button class="btn sm" id="clearPills">清除全部筛选</button>
  </div>
  <div class="scroll"><table id="tbl"><thead><tr>
    <th style="width:78px">操作</th><th>课程</th><th style="width:150px">属性 / 院系</th><th style="width:64px">学分</th>
    <th style="width:200px">教学周与节次</th><th style="width:92px">考核</th><th style="width:92px">限选/已选</th><th style="width:70px">教师</th>
  </tr><tr class="filters">
    <th></th>
    <th><input id="fq" placeholder="课程名称或编码" style="width:100%"></th>
    <th><select id="fdept" style="width:100%"></select></th>
    <th><select id="fcred" style="width:100%"></select></th>
    <th><input id="ftime" placeholder="如 周三、5-7" style="width:100%"></th>
    <th><select id="fexam" style="width:100%"></select></th>
    <th><select id="fseat" style="width:100%"></select></th>
    <th><input id="fteach" placeholder="输入姓名" style="width:100%"></th>
  </tr></thead><tbody></tbody></table></div>
  <div class="legend" id="legend"></div>
</div>

<footer id="foot"></footer>
</div>
<script>
const D = /*__DATA__*/;
const WDN = ["","周一","周二","周三","周四","周五","周六","周日"];
let sem = D.this_semester, sel = new Set(), week = 2, attrs = new Set();
function bj(iso){ if(!iso) return "未知"; try{ return new Date(iso).toLocaleString("zh-CN",
  {timeZone:"Asia/Shanghai",year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"});}
  catch(e){ return iso; } }
const $ = s => document.querySelector(s);
const rows = () => (D.terms[sem]||{rows:[]}).rows;
const byCode = () => new Map(rows().map(c=>[c.code,c]));
function wks(a){ return a.map(([x,y])=>x===y?""+x:x+"-"+y).join(","); }
function sesStr(s){ return `${WDN[s.wd]}第${s.ps}${s.pe>s.ps?"-"+s.pe:""}节`; }
function ovl(a,b){ return Math.max(a[0],b[0])<=Math.min(a[1],b[1]); }
function conflict(a,b){
  if(!a||!b||a.code===b.code) return null;
  for(const x of a.sessions) for(const y of b.sessions){
    if(x.wd!==y.wd) continue;
    if(Math.max(x.ps,y.ps)>Math.min(x.pe,y.pe)) continue;
    const ov=[];
    for(const u of x.weeks) for(const v of y.weeks) if(ovl(u,v)) ov.push([Math.max(u[0],v[0]),Math.min(u[1],v[1])]);
    if(ov.length) return {wd:x.wd,weeks:ov};
  }
  return null;
}
function classify(c){
  const h=new Set();
  for(const k of D.categories){
    if(k.kind==="non_course") continue;
    for(const cp of (k.comps||[])) if(cp.needles.some(n=>c.name.includes(n))) h.add(k.id);
    if((k.names||[]).some(n=>c.name.includes(n))) h.add(k.id);
    if(c.attribute && (k.attrs||[]).includes(c.attribute)) h.add(k.id);
  }
  return h;
}
function tierOf(c){
  const s=c.sem_sets||[];
  if(!s.length) return ["PU","学期未知：官方工作簿里没有这个编码"];
  if(s.length===1 && s[0]!==D.this_semester) return ["PN",`本学期不开（${s[0]}）`];
  const urgent = !c.no_cap && c.left!==null && (c.left<=3 || (c.enrolled/c.capacity)>=0.9);
  const only = s.length===1 && s[0]===D.this_semester;
  if(only) return urgent?["P0","仅本学期开 + 已满/近满 → 第一个抢"]:["P1","仅本学期开，不紧张"];
  return urgent?["P2","春秋都开但有竞争"]:["P3","春秋都开且不紧张"];
}
function selList(){ return [...sel].map(k=>byCode().get(k)).filter(Boolean); }
function hasWeek(c,w){ return c.sessions.some(s=>s.weeks.some(([a,b])=>w>=a&&w<=b)); }

function renderTop(){
  const t=D.terms[sem]||{};
  $("#notice").innerHTML =
    `数据来源：<b>中国科学院大学教务公开库</b>（jwba.ucas.ac.cn）—— 开课校区、限选/已选、教学周与节次均为官方口径；`+
    `开课学期取自官方工作簿。<br>抓取时点：<b>${bj(t.crawled_at)}</b>（本机冻结，页面不联网）· `+
    `备份导出：${bj(D.backup_exported_utc)} · 秋季学期共 20 教学周。<br>`+
    `本页面仅供选课规划参考，<b>数据与选课结果请以学校官方系统为准</b>。<br>`+
    `课程名称／课程编号均可点击，直达官方教务公开库对应页面。`;
  $("#heroSem").textContent = t.label || sem;
  $("#eng").textContent = D.english;
  $("#chips").innerHTML = [
    `<span class="chip on">${D.this_semester} ≥${D.semester_min_credits} 分</span>`,
    `<span class="chip">春季 ≥${D.semester_min_credits} 分</span>`,
    `<span class="chip">核心课 ≥2 门 · 专业课 ≥2 门</span>`,
    `<span class="chip">专业学位课 ≥${D.professional_degree_min} 分</span>`,
    `<span class="chip">课程学习 ≥${D.course_learning_min} 分</span>`].join("");
  $("#poolNum").textContent = rows().length;
  $("#ttSub").textContent = `勾选课程后按教学周显示；第 ${week} 教学周`;
  $("#catSub").innerHTML = `官方公开库 ${rows().length} 门 · ${t.label||""} · 玉泉路校区 · 抓取于 ${bj(t.crawled_at)}`;
  $("#foot").innerHTML = `数据来源：中国科学院大学教务公开库（jwba.ucas.ac.cn）／官方开课计划工作簿；`+
    `学分要求取自《电子信息专业学位研究生培养方案》（校发培养字〔2025〕92号）。<br>`+
    `本页为本地原型，只读本地数据、不联网、不上传；自动抢课与自动提交属明确非目标。`;
}
function renderStats(){
  const sl=selList(); let total=0, thisSem=0, doctoral=0;
  for(const c of sl){ if(c.term==="博士") {doctoral+=c.credit;continue;} total+=c.credit; if(c.sem_sets.includes(D.this_semester)) thisSem+=c.credit; }
  const need={}; for(const k of D.categories) if(k.min_credits) need[k.id]=k.min_credits;
  const got={}; for(const c of sl) for(const id of classify(c)) got[id]=(got[id]||0)+c.credit;
  const pdeg = (got["professional_degree_core"]||0)+(got["professional_degree_major"]||0);
  const pel = got["public_elective"]||0;
  const mk=(k,v,needv)=>{const p=needv?Math.min(100,v/needv*100):0;
    return `<div class="stat"><div class="k">${k}</div><div class="v ${needv&&v<needv?'gap':'okr'}">${v.toFixed(1)}
      <small>/ ${needv} 分</small></div><div class="bar"><i style="width:${p}%"></i></div></div>`;};
  $("#stats").innerHTML = mk("本学期有效学分", thisSem, D.semester_min_credits) +
    mk("专业学位课", pdeg, D.professional_degree_min) + mk("公共选修", pel, 2) +
    `<div class="stat"><div class="k">已选课程</div><div class="v">${sl.length} <small>门 · 共 ${total.toFixed(1)} 分</small></div>`+
    `<div class="bar"><i style="width:${Math.min(100,total/D.course_learning_min*100)}%"></i></div></div>`;
  $("#selSub").innerHTML = `当前已选 ${sl.length} 门 · 课程学习学分 ${total.toFixed(1)} 分（要求 ≥${D.course_learning_min}）`+
    (doctoral?` · 博士级暂不计分 ${doctoral.toFixed(1)} 分`:"")+` · 本学期 ${thisSem.toFixed(1)} 分（要求 ≥${D.semester_min_credits}）`;
}
function renderReq(){
  const sl=selList(); let h="";
  const got={}, cnt={};
  for(const c of sl){ for(const id of classify(c)){ got[id]=(got[id]||0)+c.credit; cnt[id]=(cnt[id]||0)+1; } }
  for(const k of D.categories){
    if(k.kind==="non_course"){
      h+=`<div class="reqrow"><span>${k.name}</span><span>${k.min_credits} 分 · <span class="tag">不计入课程学分</span></span></div>`;
      continue;
    }
    const g=got[k.id]||0, n=k.min_credits||0, c2=cnt[k.id]||0;
    let st = g>=n?`<span class="okr">${g.toFixed(1)} / ${n}</span>`:`<span class="gap">${g.toFixed(1)} / ${n} 缺 ${(n-g).toFixed(1)}</span>`;
    if(k.min_courses) st += ` <span class="tag ${c2>=k.min_courses?'ok':''}">门数 ${c2}/${k.min_courses}</span>`;
    let sub="";
    if(k.comps && k.comps.length){
      sub = k.comps.map(cp=>{
        const v=sl.filter(c=>cp.needles.some(x=>c.name.includes(x))).reduce((s,c)=>s+c.credit,0);
        return `<div style="font-size:12px;color:var(--ink2);padding-left:2px">· ${cp.needles[0]} ${v}/${cp.credits}`+
          (v<cp.credits&&cp.needles.join().includes("英语")?`　<span class="tag">已走${D.english}路径则无需选课</span>`:"")+`</div>`;
      }).join("");
    }
    h+=`<div class="reqrow"><span>${k.name}</span><span class="r">${st}</span></div>${sub}`;
  }
  $("#req").innerHTML = `<div style="font-size:12.5px;color:var(--ink2);margin-bottom:6px">培养要求检查（硕士 · 按培养方案）</div>`+h;
}
function renderTable(){
  const q=$("#fq").value.trim(), dept=$("#fdept").value, cred=$("#fcred").value,
        tm=$("#ftime").value.trim(), seat=$("#fseat").value, teach=$("#fteach").value.trim(),
        exam=$("#fexam").value;
  const sl=selList(); const bad=new Set();
  for(let i=0;i<sl.length;i++) for(let j=i+1;j<sl.length;j++) if(conflict(sl[i],sl[j])){bad.add(sl[i].code);bad.add(sl[j].code);}
  let list=rows().filter(c=>{
    if(q && !(c.name.includes(q)||c.code.includes(q))) return false;
    if(attrs.size && !attrs.has(c.attribute)) return false;
    if(dept && c.department!==dept) return false;
    if(cred!=='' && String(c.credit)!==cred) return false;
    if(teach && !((c.teacher||'').includes(teach))) return false;
    if(exam && (c.exam||'') !== exam) return false;
    if(seat==='free' && !(c.left>0)) return false;
    if(seat==='full' && c.left!==0) return false;
    if(seat==='na' && c.left!==null) return false;
    if(tm){ const m=tm.match(/周([一二三四五六日天])/); if(m){
        const wd="一二三四五六日".indexOf(m[1])+1;
        const pm=tm.match(/(\d+)\s*-\s*(\d+)/); const p=pm?[+pm[1],+pm[2]]:null;
        if(!c.sessions.some(s=>s.wd===wd && (!p || Math.max(s.ps,p[0])<=Math.min(s.pe,p[1])))) return false; } }
    return true;
  });
  const tb=$("#tbl tbody"); tb.innerHTML="";
  for(const c of list.slice(0,600)){
    const tr=document.createElement("tr");
    if(sel.has(c.code)) tr.className = bad.has(c.code)?"sel bad":"sel";
    const seatTag = c.no_cap?'<span class="tag">不设限</span>'
      : c.left===null?'<span class="tag">—</span>'
      : c.left<=0?'<span class="tag full">已满${c.left<0?"（超额 "+(-c.left)+"）":""}</span>'
      : `<span class="tag ${c.left<=3?'near':'ok'}">余 ${c.left}</span>`;
    tr.innerHTML = `<td><button class="btn sm">${sel.has(c.code)?"移除":"加入"}</button></td>
      <td><b><a class="cl" target="_blank" rel="noopener"
          href="https://jwba.ucas.ac.cn/sc/course/courseplan/${c.cid}" title="官方课程大纲">${c.name} ↗</a></b>
        <div style="font-size:11.5px"><a class="cl" target="_blank" rel="noopener"
          href="https://jwba.ucas.ac.cn/sc/course/coursetime/${c.cid}" title="官方时间地点">${c.code}</a></div></td>
      <td>${c.attribute}<div style="font-size:11.5px;color:var(--ink2)">${c.department}</div></td>
      <td>${c.credit.toFixed(1)}</td>
      <td>${c.sessions.map(s=>`${sesStr(s)}<div style="font-size:11px;color:var(--ink2)">周 ${wks(s.weeks)}${s.rooms&&s.rooms[0]?" · "+s.rooms[0]:""}</div>`).join("")||'<span class="tag">无时间数据</span>'}</td>
      <td>${c.exam||c.teach_mode?(c.exam||"—")+(c.teach_mode?`<div style="font-size:11px;color:var(--ink2)">${c.teach_mode}</div>`:"")+(c.aux_from?`<div style="font-size:10.5px;color:var(--ink2)">来源：${c.aux_from}</div>`:""):'<span class="tag">—</span>'}</td>
      <td>${seatTag}<div style="font-size:11.5px;color:var(--ink2)">${c.no_cap?(c.enrolled??"")+" / 不设限":(c.capacity!==null?c.enrolled+"/"+c.capacity:"")}</div></td>
      <td style="font-size:12px">${c.teacher||"—"}</td>`;
    tr.querySelector("button").onclick=()=>{ sel.has(c.code)?sel.delete(c.code):sel.add(c.code); renderAll(); };
    tb.appendChild(tr);
  }
  $("#legend").innerHTML = `显示 ${Math.min(list.length,600)} / 共 ${rows().length} 门 · 已选 ${sel.size} 门
    ｜ <span class="tag full">已满</span> 剩余 0 ｜ <span class="tag near">余 ≤3</span> 即将满 ｜
    周次有缺口属常态（如 2-5,7-17 跳过第 6 周）｜ 本学期「是否远程教学」官方记录全为"否"<br>
    <b>课程名称</b>链接到官方「课程大纲」页、<b>课程编号</b>链接到官方「时间地点」页（均指向 jwba.ucas.ac.cn，新标签打开）｜
    <b>考核方式</b>取自第三方课程库（官方公开库不含该字段）`;
}
function renderConf(){
  const sl=selList(), out=[];
  for(let i=0;i<sl.length;i++) for(let j=i+1;j<sl.length;j++){
    const cf=conflict(sl[i],sl[j]); if(cf) out.push([sl[i],sl[j],cf]);
  }
  $("#conf").innerHTML = out.length? out.map(([a,b,cf])=>
    `<div style="padding:7px 2px;border-bottom:1px dashed var(--line)">
       <div><span class="gap">冲突</span> · ${WDN[cf.wd]} 第 ${cf.weeks.map(w=>w[0]===w[1]?w[0]:w[0]+"-"+w[1]).join(",")} 周
         <span class="tag">${a.term||""}</span></div>
       <div style="font-size:12.5px;color:var(--ink2)">${a.name} ⟷ ${b.name}</div></div>`).join("")
    : '<div class="empty">已选课程之间没有三维冲突。</div>';
}
function renderOrder(){
  const o = selList().map(c=>{const [t,w]=tierOf(c); return {c,t,w};})
    .sort((x,y)=>(x.t<y.t?-1:x.t>y.t?1:0)||((x.c.left??1e9)-(y.c.left??1e9)));
  $("#order").innerHTML = o.length? o.map((k,i)=>
    `<div class="reqrow"><span><span class="tag ${k.t==="P0"?"t0":k.t==="P1"?"t1":""}">${k.t}</span>
      ${i+1}. ${k.c.name}</span><span style="font-size:12.5px">${k.c.no_cap?"不设限选":(k.c.left===null?"座位未知":(k.c.left<=0?"已满":"剩余 "+k.c.left))}</span></div>
      <div style="font-size:12px;color:var(--ink2)">${k.w}</div>`).join("")
    : '<div class="empty">先勾选课程。</div>';
}
function renderTT(){
  const sl=selList(); const cells=[];
  for(const c of sl) if(hasWeek(c,week)) for(const s of c.sessions)
    if(s.weeks.some(([a,b])=>week>=a&&week<=b)) for(let p=s.ps;p<=s.pe;p++) cells.push({c,s,p});
  const dup=new Set();
  for(let i=0;i<cells.length;i++) for(let j=i+1;j<cells.length;j++)
    if(cells[i].p===cells[j].p && cells[i].s.wd===cells[j].s.wd){dup.add(i);dup.add(j);}
  let h='<table class="tt"><thead><tr><th style="width:76px">节次 / 时间</th>';
  for(let d=1;d<=7;d++) h+=`<th>${WDN[d]}</th>`;
  h+='</tr></thead><tbody>';
  D.periods.forEach(([n,t],idx)=>{
    h+=`<tr><td class="per">第 ${n} 节<br>${t}</td>`;
    for(let d=1;d<=7;d++){
      const cs=cells.map((c,i)=>({...c,i})).filter(x=>x.p===idx+1 && x.s.wd===d);
      h+=`<td>${cs.map(x=>`<div class="ev ${dup.has(x.i)?"c":""}">${x.c.name}</div>`).join("")}</td>`;
    }
    h+='</tr>';
  });
  h+='</tbody></table>';
  $("#ttWrap").innerHTML = h;
  $("#ttSub").innerHTML = `第 ${week} 教学周 · 本周 ${cells.length? new Set(cells.map(c=>c.c.code)).size : 0} 门课` +
    (dup.size? ` · <span class="gap">${dup.size/2|0} 处重叠</span>`:"") +
    (rows().length? "" : ` · <span class="gap">该学期开课表尚未发布</span>`);
  $("#weekPills").innerHTML = Array.from({length:20},(_,i)=>i+1)
    .map(w=>`<span class="pill ${w===week?'on':''}" data-w="${w}">${w}</span>`).join("");
  [...document.querySelectorAll("#weekPills .pill")].forEach(e=>e.onclick=()=>{week=+e.dataset.w;renderTT();renderTop();});
}
function renderFilters(){
  const ds=[...new Set(rows().map(c=>c.department))].sort();
  const cs=[...new Set(rows().map(c=>c.credit))].sort((a,b)=>a-b);
  $("#fdept").innerHTML='<option value="">全部单位</option>'+ds.map(d=>`<option>${d}</option>`).join("");
  $("#fcred").innerHTML='<option value="">全部学分</option>'+cs.map(c=>`<option>${c}</option>`).join("");
  $("#fexam").innerHTML='<option value="">全部</option>'+
    [...new Set(rows().map(c=>c.exam).filter(Boolean))].sort().map(x=>`<option>${x}</option>`).join("");
  $("#fseat").innerHTML='<option value="">全部</option><option value="free">还有座位</option><option value="full">已满</option><option value="na">无容量数据</option>';
  $("#attrPills").innerHTML = [...new Set(rows().map(c=>c.attribute))].sort()
    .map(a=>`<span class="pill ${attrs.has(a)?'on':''}" data-a="${a}">${a}</span>`).join("");
  [...document.querySelectorAll("#attrPills .pill")].forEach(e=>e.onclick=()=>{
    const a=e.dataset.a; attrs.has(a)?attrs.delete(a):attrs.add(a); renderAll(); });
  $("#semSel").innerHTML = Object.entries(D.terms).map(([k,v])=>`<option ${k===sem?'selected':''} value="${k}">${v.label}</option>`).join("");
}
function renderAll(){
  renderTop(); renderStats(); renderReq(); renderTable(); renderConf(); renderOrder(); renderTT();
}
const THEMES=[["indigo","靛青"],["teal","墨绿（原站）"],["blue","蓝白"],["graphite","石墨琥珀"]];
function applyTheme(t){ document.documentElement.dataset.t=t;
  $("#themePills").innerHTML = THEMES.map(([k,n])=>`<span class="pill ${k===t?'on':''}" data-t="${k}">${n}</span>`).join("");
  [...document.querySelectorAll("#themePills .pill")].forEach(e=>e.onclick=()=>{ location.hash="t="+e.dataset.t; applyTheme(e.dataset.t); }); }
applyTheme((location.hash.match(/t=(\w+)/)||[])[1] || "indigo");
renderFilters(); renderAll();
$("#fq").oninput=renderTable; $("#fdept").onchange=renderTable; $("#fcred").onchange=renderTable;
$("#ftime").oninput=renderTable; $("#fseat").onchange=renderTable; $("#fteach").oninput=renderTable; $("#fexam").onchange=renderTable;
$("#clearPills").onclick=()=>{attrs.clear();renderAll();};
$("#clear").onclick=()=>{sel.clear();renderAll();};
$("#check").onclick=renderConf;
$("#bulkAdd").onclick=()=>{ $("#bulk").value.split(/[,\s，]+/).filter(Boolean)
  .forEach(c=>{ if(byCode().has(c)) sel.add(c); }); renderAll(); };
$("#prevW").onclick=()=>{ if(week>1){week--;renderTT();} };
$("#nextW").onclick=()=>{ if(week<20){week++;renderTT();} };
$("#semSel").onchange=e=>{ sem=e.target.value; sel=new Set(); week=2; const THEMES=[["indigo","靛青"],["teal","墨绿（原站）"],["blue","蓝白"],["graphite","石墨琥珀"]];
function applyTheme(t){ document.documentElement.dataset.t=t;
  $("#themePills").innerHTML = THEMES.map(([k,n])=>`<span class="pill ${k===t?'on':''}" data-t="${k}">${n}</span>`).join("");
  [...document.querySelectorAll("#themePills .pill")].forEach(e=>e.onclick=()=>{ location.hash="t="+e.dataset.t; applyTheme(e.dataset.t); }); }
applyTheme((location.hash.match(/t=(\w+)/)||[])[1] || "indigo");
renderFilters(); renderAll(); };
// 首屏：载入保存的方案中属于当前学期的课
sel = new Set(D.plan_codes.filter(k=>byCode().has(k)));
renderAll();
</script></body></html>
"""


if __name__ == "__main__":
    sys.exit(main())

# A2 — Data dictionary (S1 / S2 / S5, field by field)

A field-level reference for the three frozen inputs this project consumes, written to be *looked up*, not read
end-to-end. Field names are given Chinese-first (the data is Chinese) with the English name code and documents use;
the semantics are constrained to `doc/assignments/a2/domain-glossary.md` (entities: 课程/班次/学期/培养方案;
value objects: 周次区间/节次区间/星期节次/时段/学分/容量/教室/课程属性/校区).

- **Every number below was measured in this session** with inline `python3` on the committed files (no number is
  copied from another document). The exact snippet is cited next to each figure under "实测出典" / in §5.
  No script file was added (the A2 brief allows only this one new file), so the measurements are reproducible from
  the quoted one-liners and the frozen hashes in §0.2.
- Companion raw output: `data/derived/a2/invariant-checks.md` (§0 "Parsing quality"); where I re-checked its
  numbers, §5 records both and flags any difference.

---

## 0. Scope, sources and how to read this

### 0.1 Sources and the naming caveat (read this first)

| label | what it is | committed file(s) | rows |
| --- | --- | --- | --- |
| **S1** | 开课计划表 — official course-planning workbook (计划态) | `data/s1-plan-workbook/sections-snapshot.json` | 732 |
| **S2** | 教务公开课表 — official public listing, `jwba.ucas.ac.cn` (当前态, crawled 2026-09-27) | `data/s2-public-listing/89576-campus20.json` (+ `89577-campus20.json`, `history/`) | 341 (autumn) |
| **S5** | 培养方案 — 校发培养字〔2025〕92号 credit floors | `data/s5-programme/degree-requirements.json` | 1 object |
| *(derived)* | **课程库快照** — the 347-course 玉泉路 dataset that A2's conflict check actually runs on | `data/derived/course-library-snapshot.json` | 347 |

**Naming caveat (measured, not a typo).** This repository's convention (`README.md` §"Where the data comes from",
A1 brief) is: **S1 = 开课计划表, S2 = 教务公开课表 jwba**. The 347-row `course-library-snapshot.json` is neither:
it is **a snapshot of course data crawled from the academic system**, archived through the course-planning site's
public JSON (`default-courses.json`; the URL, size and hash of the archived copy are recorded in
`data/derived/live-listing-provenance.md`, and the same data is what `doc/data-authority.md` calls source ❹).
It is a **derived** dataset — a second pipeline over the same academic-system facts — so it is used for
cross-checking and as the carrier of the schedule fields the A2 checks consume, **never as an authority**.
Because it is derived, it is not expected to be identical to S2; where the two disagree on the 251 shared base
codes (weekday/period 8 cases, week sets 9 cases ≈ 3 %) this document records the disagreement rather than
smoothing it (§5.6, §6 T8/T10).

### 0.2 Frozen-input hashes (recomputed this session)

| file | sha256 (recomputed) | committed `.sha256` |
| --- | --- | --- |
| `data/derived/course-library-snapshot.json` | `3724ade7ff05dcd3465c017f965feffe0eaa26cfbcaafebf976d268003122a69` | match ✓ |
| `data/s1-plan-workbook/sections-snapshot.json` | `ffcf1ae023e59fe8a09d83584fe7ba8293eb982cce8887f51e7db140f98d8c9e` | match ✓ |
| `data/s2-public-listing/89576-campus20.json` | `6510aa2e4127a096208de7d02916c6bc5c8643f66f050d68470cff2d83362db5` | match ✓ |
| `data/s5-programme/degree-requirements.json` | `36f99278312e4954129c9bd1575a794859cf1b9840268bfc3cf512a061af1dc3` | *(no `.sha256` file committed)* |

### 0.3 Envelopes (the files are not bare arrays)

| file | top-level shape | how to read it |
| --- | --- | --- |
| `course-library-snapshot.json` | `{"campus_rule": "course code position 18 == 'Y'", "courses": [ … 347 … ]}` | rows are objects; one row = one 班次 |
| `sections-snapshot.json` | `{"campus_filter": "玉泉路", "courses": [ … 732 … ]}` | rows are objects; one row = one workbook record |
| `89576-campus20.json` | `{"campus_code": 20, "term_id": 89576, "crawled_at": "2026-09-27 16:31:49", "source": "https://jwba.ucas.ac.cn/sc/public/coursePublic", "rows": [ … 341 … ]}` | rows are objects; one row = one 班次 |
| `degree-requirements.json` | single object (`_source`, `programme`, `degree_track`, `semester_min_credits`, `categories`, `known_modelling_gaps`) | rules, not rows |

---

## 1. S1 — 开课计划表 (course-planning workbook)

`data/s1-plan-workbook/sections-snapshot.json` — 732 records, 414 distinct 课程编码 (413 after the one section
suffix is stripped), campus filter 玉泉路. Source workbooks: 《…开课计划表0828.xlsx》441 + 《…核心课和专业课列表0828.xlsx》291.

| 字段名 (中文 / English) | 所属实体 | 类型与单位 | 取值 / 示例 | 来源 | 质量与陷阱 |
| --- | --- | --- | --- | --- | --- |
| 课程编码 / `code` | 课程 (Course) + 班次 (Section) | string；18 字符为基码，可带 `-xxx` 班次后缀 | `180080025200M1002Y`（18 位）、`180089050200MB001Y-201`（22 位，唯一带后缀的一条） | S1 | 不是数字，不能当整数排序。**第 18 位恒为 `Y`** — 实测 732/732 的第 18 位都是 `Y`（玉泉路）。前缀 18 位是课程身份，`-` 之后是班次身份。 |
| 课程名称 / `name` | 课程 | string | `抽样调查` | S1 | 非唯一；不同班次同名，且同名课程在不同编码下存在。 |
| 学分 / `credit` | 学分 (Credit) | number（本文件为 JSON number：整型 582 条 / 浮点 150 条） | `2`、`0.5`、`2.5`、`3.5`（取值集合 `{0.5,1,2,2.5,3,3.5}`） | S1 | 与 S2 的字符串型 `credit`（`"2.00"`）类型不同，join 前须归一化；是 I2 唯一计分来源。 |
| 开课院系 / `department` | 班次 | string | `数学科学学院`；top：国际学院 160、计算机科学与技术学院 87、电子电气与通信工程学院 87、外语系 73 | S1 | 开课单位，不是"课程所属学科"；S2 有独立的 `department` 语义相同但口径是"开课单位"。 |
| 开课学期 / `semester` | 学期 (Term) | enum string | `秋季`（400 条）、`春季`（332 条） | S1 | **实测 S1 里确实有该字段**（见 §6 陷阱 T7 的反例说明）。S2/快照都没有逐行学期；S2 的学期只能从 `term_id` 按文件推。 |
| 课程属性 / `attribute` | 课程属性 (CourseAttribute) | enum string | `专业课`234、`学科核心课`206、`专业核心课`142、`公共选修课`79、`公共必修课`29、`研讨课`25、`实验课`16、`实践课`1 | S1 | 取值集合有 8 个，但**快照/S2 出现 `科学前沿讲座` 而没有 `实践课`**（§5.7）→ 两源属性词表不完全一致，不能当作同一受控词表 join。 |
| 开课校区 / `campus` | 校区 (Campus) | enum string | `玉泉路`（732/732） | S1 | 本文件已被 `campus_filter=玉泉路` 预过滤 → **没有区分度**，不能用来做跨校区判断；S2 的 `campus` 才是逐行真字段。 |
| 限选（容量）/ `capacity` | 容量 (Capacity) | 非负整数字符串 | **全部为空**（732/732 空串） | S1 | **S1 完全没有容量数据**。空串 ≠ 0 ≠ 无限；缺失必须显式建模（domain-glossary：Capacity = non-negative integer **or unknown**）。 |
| 已选 / `enrolled` | 已选 (Enrolled) | 非负整数字符串 | **全部为空**（732/732 空串） | S1 | 同上；S1 无法支持 I3。 |
| 分段排课 / `sessions` | 班次 → Slot[] | array of object，长度恒为 1 | `[{"room":"", "time":"", "weeks":""}]` | S1 | **实测 732/732 都是长度恰为 1 的空对象**（`room` 也全空）→ 该字段是空壳，不能据此认为"S1 有排课结构"。 |
| 星期节次 / `time` | 星期节次 (DayPeriod) | string（应为 `周一(1-2)；…`） | **全部为空** | S1 | 与 provenance 一致（0/732 有值）→ 单靠 S1 无法做冲突判断。 |
| 开课周 / `weeks` | 周次区间集 (WeekRange set) | string（应为 `第2-5,7-17周；…`） | **全部为空** | S1 | 同上。A1 报"0/732"，**本次复核仍为 0/732**（§5.4）。 |
| 考试方式 / `exam` | 考试方式 (ExamMode) | string | **全部为空**（732/732） | S1 | S1 无考核方式；快照有（`闭卷笔试` 等 6 值）。 |
| 来源工作簿 / `source` | 记录溯源元数据 | string | `2026-2027学年秋季和春季开课计划表0828.xlsx`（441）、`2026-2027学年研究生核心课和专业课列表…0828.xlsx`（291） | S1 | **溯源自证**：一条记录来自哪本工作簿，可用来解释属性/字段覆盖差异；不是课程属性。 |

**S1 缺失字段（三个来源都没有、或只有别处有）**：`level`（培养层次）、`subject`（所属学科/专业）、`teacher`
（主讲教师）、`hours`（学时）在本文件均不存在。

---

## 2. S2 — 教务公开课表 (public listing, jwba)

### 2a. 文件级字段（`89576-campus20.json` 的顶层）

| 字段名 (中文 / English) | 所属实体 | 类型与单位 | 取值 / 示例 | 来源 | 质量与陷阱 |
| --- | --- | --- | --- | --- | --- |
| 校区码 / `campus_code` | 抓取参数 | integer | `20` | S2 | `20`=玉泉路（`21`=中关村、`22`=雁栖湖，见 `doc/data-authority.md`）。整文件一个值 → 不是逐行字段。 |
| 学期号 / `term_id` | 学期 (Term) | integer | `89576` | S2 | 映射见 `terms.json`：`89576 = 2026—2027学年(秋)第一学期`，`89577 = (春)第二学期`。**学期只能由 term_id 反查，行内无学期字段。** |
| 抓取时间 / `crawled_at` | 记录时点 | datetime string (local) | `2026-09-27 16:31:49` | S2 | 这是 `SnapshotStaled` 事件的证据；S1 的时点是文件名里的 `0828`（2026-08-28）。 |
| 来源 URL / `source` | 溯源元数据 | string (URL) | `https://jwba.ucas.ac.cn/sc/public/coursePublic` | S2 | 列表页地址；详情页是 `https://jwba.ucas.ac.cn/sc/course/coursetime/{course_id}`（脚本 `scripts/fetch_official_db.py`）。 |
| 行集 / `rows` | 班次 (Section)[] | array of object，长度 341 | 见 §2b | S2 | `89577-campus20.json` 的 `rows` 长度 **实测为 0**（春季尚未发布）→ 拿去 join 会静默得到空集。 |
| 抓取页哈希 / `schedule_pages_sha256`（行内） | 溯源元数据 | string (hex) | 每行一个 | S2 | 逐行记录该班次详情页快照哈希，可复算；证明这一行来自哪一次抓取。 |

**字段集口径提醒**：`data/derived/live-listing-provenance.md` 记录上游原始下载（8,103,455 字节，未入库）的字段是
**19 个 SEP「学期课表」表头**；而**committed 的 `89576-campus20.json` 每行实测只有 15 个 key**（下表）。
被裁掉的上游字段包括 `培养层次`/`授课方式`/`考试方式`/`是否远程教学`/`所属学科·专业`/`助教`——其中 `level`、`exam`、
`subject` 改由 §2c 的 347 快照承载。**"19 字段"指上游原始下载，不是这个 frozen 文件。**

### 2b. 行级字段（`rows[i]`，实测 15 个 key，341 行；空值对数=该字段空串条数）

| 字段名 (中文 / English) | 所属实体 | 类型与单位 | 取值 / 示例 | 来源 | 质量与陷阱 |
| --- | --- | --- | --- | --- | --- |
| 序号 / `seq` | 抓取序号 | string(数字) | `"1"`、`"2"` … | S2 | 页内序号，非班次身份；不要当主键。 |
| 开课单位 / `department` | 班次 | string | `数学科学学院`（空 0/341） | S2 | 与 S1 `department` 语义可对齐。 |
| 课程编码 / `code` | 课程 + 班次 | string | `180080070100MX018Y`、`180089050200MB001Y-304`（空 0/341） | S2 | 同 S1：第 18 位恒为 `Y`（实测 341/341）。 |
| 课程名称 / `name` | 课程 | string | `实用最优化算法`（空 0/341） | S2 | — |
| 课程属性 / `attribute` | 课程属性 | enum string | `公共选修课`47、`学科核心课`75、`专业课`72、`专业核心课`53、`公共必修课`78、`研讨课`8、`实验课`7、`科学前沿讲座`1（空 0/341；合计 341） | S2 | 与 S1 属性词表略有出入（S2 有 `科学前沿讲座`，S1 有 `实践课`）。 |
| 学分 / `credit` | 学分 (Credit) | **string**，两位小数 | `"1.00"`、`"2.00"`、`"2.50"`、`"0.50"`；分布 `2.00`138/`1.00`78/`3.00`70/`2.50`34/`0.50`19/`3.50`2（空 0/341） | S2 | 字符串型！join 前必须 `float()`；与 S1 的 number 型不同（§1）。 |
| 课时 / `hours` | 学时 (Hours) | string(整数) | `"40"`99、`"60"`57、`"30"`28、`"128"`22（空 0/341） | S2 | **不是学分**；与 `credit` 同源一个上游列"课时·学分"被拆开。S1/S5 无此字段。 |
| 限选（容量）/ `capacity` | 容量 (Capacity) | 非负整数字符串 **或 `"/"`** | 数值 301 行（`40`47、`58`47、`30`32…）；**`"/"` 40 行**（空 0/341） | S2 | **官方"未设置"哨兵是 `"/"`，不是 `0`**（§5.3）。`"/"` 绝不能当容量 0 读——否则 40 行会被误判成"容量为零"。 |
| 已选 / `enrolled` | 已选 (Enrolled) | 非负整数字符串 | `0`75 行、`1`11、`14`9…（空 0/341；无 `"/"`） | S2 | 值 `0` 是真实"没人选"，与 `capacity` 的哨兵语义**不同**；两列不要用同一套缺失规则。 |
| 分段排课 / `schedule` | 班次 → Slot[] | array；元素 `{weekday, periods, rooms, weeks}` | 见下四行 | S2 | **结构化的**（不是 `；` 分隔字符串）。实测：含排课 339 行、**空数组 2 行**（`180089050200MB001Y-201 硕士学位英语（慕课学习）`、`180090125600PB001Y 工程伦理（玉泉路慕课）`）；每行条目数分布 `0:2, 1:173, 2:127, 3:36, 4:3`。 |
| ↳ 星期 / `schedule[].weekday` | 星期 (Weekday) | integer 1–7 | `1`=周一 … `7`=周日；分布 1:76, 2:92, 3:77, 4:75, 5:53, 6:88, 7:86 | S2 | **1-based，日=7**（例：`180080070100MX018Y` 有 `weekday 6` + `weeks [[6,6]]`，对应快照的"周六…第6周"）。映射到 `一二三四五六日` 时用 `idx-1`。 |
| ↳ 节次 / `schedule[].periods` | 节次区间 (PeriodRange) | array `[first,last]`，节 ∈ 1..13 | `[5,7]`133、`[10,12]`108、`[1,4]`80、`[3,4]`50、`[5,6]`33 | S2 | 已是区间端点对，不是字符串；`first==last` 表示单节。 |
| ↳ 教室 / `schedule[].rooms` | 教室 (Room) | array of string | `["教学楼阶一3"]` | S2 | 数组（可多点）；与节次/周次**平行**：不含教室，域内无教室不变量。 |
| ↳ 周次 / `schedule[].weeks` | 周次区间集 (WeekRange set) | array of `[start,end]` | `[[2,5],[7,17]]`、单周 `[[6,6]]` | S2 | **区间集合，不是数字**；`[6,6]` 是退化为一点的集合。实测 min 周=1，max 周=22，无 `start>end`。 |
| 主讲教师 / `teacher` | 班次 | string | `牛凌峰`（**空 69/341**） | S2 | 有缺失（慕课/讲座类）。 |
| 首席教授 / `chief` | 班次 | string | 示例常为空（**空 202/341**，占 59%） | S2 | 缺失率极高，**不能当"该课没有负责人"的证据**，只能当"未登记"。 |
| 详情页 ID / `course_id` | 抓取句柄 | string | `315207` | S2 | 用于回抓 `coursetime/{course_id}`；非课程编码，不要与 `code` 混用。 |
| 开课校区 / `campus` | 校区 (Campus) | enum string | `玉泉路`（341/341，空 0/341） | S2 | 官方逐行真字段——修好 `doc/data-authority.md` 所说的老错觉（"公开库没有校区"）。但本文件已被 `campus_code=20` 过滤 → 也**无区分度**。 |

### 2c. 派生快照 `course-library-snapshot.json`（347 行，A2 冲突检查实际使用）

每行 = 一个 班次；347 行 = 347 个不同 `code`（实测无重复）。**13 个字段实测 0 空值**——"缺失"在本文件里不表现为空串，
而表现为哨兵值（`capacity="0"`），或干脆没有该行。

| 字段名 (中文 / English) | 所属实体 | 类型与单位 | 取值 / 示例 | 来源 | 质量与陷阱 |
| --- | --- | --- | --- | --- | --- |
| 课程编码 / `code` | 课程 + 班次 | string | `180080070100MX018Y`；长度分布 18:256、20:7、21:70、22:1、23:13；第 18 位恒 `Y` | 派生快照（从教务系统爬取的课程数据快照；见 §0.1） | 班次后缀 `-01`/`-W003`/`-304` 等；去重须按前 18 位。 |
| 课程名称 / `name` | 课程 | string | `实用最优化算法` | 派生快照 | — |
| 学分 / `credit` | 学分 | **number**（整型 291 / 浮点 56；取值 `{0.5,1,2,2.5,3,3.5}`） | `1`、`2.5` | 派生快照 | 整型/浮点混用；与 S2 字符串型不同。 |
| 课程属性 / `attribute` | 课程属性 | enum string | `学科核心课`77、`公共必修课`76、`专业课`74、`专业核心课`53、`公共选修课`50、`研讨课`8、`实验课`8、`科学前沿讲座`1 | 派生快照 | 与 S1 词表差在 `实践课`/`科学前沿讲座`（§5.7）。 |
| 培养层次 / `level` | 课程属性 | enum string | `硕博通用课程`203、`硕士课程`136、`博士课程`8 | 派生快照 | S1/S2-frozen 均**无**此字段；只在这一源有。 |
| 所属学科 / `subject` | 课程属性 | string（77 个不同值） | `数学`、`语言学及应用语言学`30、`工程管理`25 | 派生快照 | S1/S2-frozen 均无；粒度是"一级学科/专业"。 |
| 主讲教师 / `teacher` | 班次 | string | `牛凌峰`（空 0/347） | 派生快照 | 与 S2 不同：这里 0 缺失（S2 有 69 空）。 |
| 教室 / `room` | 教室 (Room) | string（53 个不同值） | `教学楼阶一3`（空 0/347） | 派生快照 | 单个字符串（S2 是数组）。 |
| 星期节次 / `time` | 星期节次 (DayPeriod) | string，`；` 分隔段 | `周三(5-7)；周六(5-7)`；`周一(10-11)；周三(10-11)；周六(10-11)` | 派生快照 | **与 `weeks` 段数一一对应**（实测 0 处不对应）。段数分布：1 段 177、2 段 128、3 段 40、4 段 2（§5.2）。 |
| 开课周 / `weeks` | 周次区间集 | string，`；` 分隔段；段内 `,` 分隔区间 | `第2-5,7-17周；第6周`；`第2-20周；第2-5,7-20周；第6周` | 派生快照 | **区间集合，不是数字**（`第6周` = `[(6,6)]`）。段内区间数最多到 8；实测无不可解析段。 |
| 容量 / `capacity` | 容量 | 非负整数字符串 | `40`、`58`、**`"0"` 41 行**（空 0/347） | 派生快照 | 哨兵：`"0"` = 未设置（§5.3）；真实 overcapacity（enrolled>cap>0）实测 **0**。 |
| 已选 / `enrolled` | 已选 | 非负整数字符串 | `25`；`"0"` 70 行（空 0/347） | 派生快照 | `enrolled=0` 是真实"没人选"。 |
| 考试方式 / `exam` | 考试方式 | enum string | `闭卷笔试`110、`课堂开卷`97、`读书报告`55、`大开卷`24、`其它（需说明）`51、`文献综述`10（空 0/347） | 派生快照 | 只此一源有；据 `doc/data-authority.md` 属"人工从 SEP 复制"的辅助字段，不可当逐行官方口径。 |

---

## 3. S5 — 培养方案（学分下限）

`data/s5-programme/degree-requirements.json`（校发培养字〔2025〕92号；085402 通信工程，2026 级）。

| 字段名 (中文 / English) | 所属实体 | 类型与单位 | 取值 / 示例 | 来源 | 质量与陷阱 |
| --- | --- | --- | --- | --- | --- |
| 方案名 / `programme` | 培养方案 | string | `085402 通信工程（0854 电子信息专业学位，2026 级，集中教学在玉泉路 Y）` | S5 | 单一学生口径，不是全院规则。 |
| 总学分下限 / `degree_track.master.total_min_credits` | 培养方案 | integer 学分 | `36` | S5 | 只给**下限**（I2 的 ceiling 半无来源）。 |
| 课程学习下限 / `…master.course_learning_min_credits` | 培养方案 | integer 学分 | `24` | S5 | I2 主判据。 |
| 必修环节学分 / `…master.required_practicum_credits` | 培养方案 | integer 学分 | `12` | S5 | 非课程学分，不能与选课学分混算。 |
| 公共学位课下限 / `…master.public_degree_credits` | 培养方案 | integer 学分 | `7` | S5 | 与 `categories[public_degree]` 重复表达，改一处须同步。 |
| 专业学位课下限 / `…master.professional_degree_min_credits` | 培养方案 | integer 学分 | `12` | S5 | 同上（= 核心课 4 + 专业课 4 … 口径按类别表）。 |
| 转博（硕博）学分线 / `degree_track.combined_master_phd` | 培养方案 | object | `course_learning_min_credits:32`、`public_degree_credits:11`、`professional_degree_min_credits:16` + `note` | S5 | **陷阱**：转博**考核**线是 24（硕士课程学习），32 是转博后博士毕业前要求——`note` 明写，勿当考核线。 |
| 每学期学分下限 / `semester_min_credits.value` | 培养方案 | integer 学分 | `10`；`applies_to`="秋季与春季每学期，不含人文讲座与科学前沿讲座"；`source`="教务部选课说明" | S5 | 按"学期"而不是"学年"；`applies_to` 的排除项是实质约束。 |
| 类别 / `categories[]` | 培养方案 | array of 7 objects | 见 §5.8 | S5 | 各类别 `kind` ∈ {degree, non_degree, non_course}；计分按类别独立核算（见 `known_modelling_gaps`）。 |
| ↳ 类别名 / `categories[].name` + `id` | 培养方案 | enum | `公共学位课`/`专业学位课·核心课`/`专业学位课·专业课`/`公共必修非学位课`/`公共选修课`/`专业选修课`/`必修环节` | S5 | 与数据源 `attribute` **不是**同一套词表——须经 `matches_attributes`/`matches_names` 映射。 |
| ↳ 下限 / `categories[].min_credits` | 培养方案 | integer 学分 | `7,4,4,1,2,2,12` | S5 | 有的类别还有 `min_courses`（核心课 2、专业课 2）。 |
| ↳ 匹配规则 / `matches_attributes` `matches_names` `also_allows` `fixed_components` | 培养方案 | string[] / object[] | 例：核心课 `matches_attributes:["学科核心课","专业核心课"]`；`fixed_components` 用 `name_contains` 匹配课名 | S5 | **按课名/属性软匹配**——课名改字即失配（`known_modelling_gaps[0]` 记了 attribute 无法区分公共学位课与公共必修非学位课的缺口）。 |
| ↳ 固定组成 / `fixed_components[].credits` `note` | 培养方案 | 学分 | 中特 2、自辩 1、学术规范 1（通论+分论各 0.5）、英语 3；实践 6/开题 2/中期 2/学术报告与社会实践 2 | S5 | 含"各 0.5 须合计 1""免修免考记 EX 学分照得"等**语义注记**，不是可直接相加的行。 |
| 已知建模缺口 / `known_modelling_gaps[]` | 培养方案 | array（3 条） | 每条 `{gap, resolution}` | S5 | 是**诚实的未决项**，不可当作已解决；引用 S5 结论时须连同这 3 条一起引。 |
| 出处 / `_source` | 溯源元数据 | object | `document`/`local_copy`(~Desktop)/`extracted:2026-09-27`/`extraction_method`/`note` | S5 | `note` 明写"未含院系加码"——即**分母是校发口径**，院系可更严。 |

---

## 4. 派生值对象与计算字段（没有存储，由上面字段推得）

| 字段名 (中文 / English) | 所属实体 | 类型与单位 | 定义 / 示例 | 来源 | 质量与陷阱 |
| --- | --- | --- | --- | --- | --- |
| 周次区间 / `WeekRange` | 值对象 | `(start,end)` 整数周 | `(2,5)`；`第6周` → `(6,6)` | 派生（快照/ S2 的 `weeks`） | 区间**半开/闭**必须统一；`[6,6]` 不是"第6到第6周"以外的任何东西。 |
| 节次区间 / `PeriodRange` | 值对象 | `(first,last)`，节 ∈ 1..13 | `(5,7)`；实测快照出现 18 种不同节次区间 | 派生 | 节次上界因源而异（S2 观测到 13）。 |
| 星期节次 / `DayPeriod` | 值对象 | `(weekday, PeriodRange)` | `(3,(5,7))` = 周三第 5-7 节 | 派生 | 快照用字符串、S2 用 `weekday+periods`——**同一概念两种编码**，join 要归一化。 |
| 时段 / `Slot` | 值对象 | `DayPeriod` + `WeekRange` set | 切分单位，冲突规则比较的对象 | 派生 | 一个 班次 可有多个 Slot（快照里靠 `；` 分段表达）。 |
| 冲突 / `Conflict` | 值对象（派生布尔） | boolean | `weekday 相同 ∧ 节次相交 ∧ 周次相交` | 派生 | **从不存储**；只比"星期+节次"会误报（半学期同格），不看周次会漏报（domain-glossary §3、invariants I1）。 |
| 满 / `SectionFull` | 班次状态 | boolean | `enrolled = capacity`（且 capacity 已知） | 派生 | `capacity` 未知（空/`0`/`/`）时该状态**不可判定**，不是"未满"。 |
| 超容量 / `SectionOverCapacity` | 班次状态 | boolean | `enrolled > capacity > 0` | 派生 | 实测这份数据里 0 例（§5.3）；`capacity=0/`/` 的行不算，须单独报告。 |

---

## 5. 实测统计（本会话所有关键数字与出典）

> 方法：`python3` 内联脚本，`json.load` 后按行统计；无临时文件。下面每行「出典」给出可复算的 python 表达式
> （变量名：`s1=load("…sections-snapshot.json")["courses"]`、`s2=load("…/89576-campus20.json")["rows"]`、
> `snap=load("…course-library-snapshot.json")["courses"]`，`base=lambda c:c[:18]`）。

### 5.1 ① 条数与去重后课程编码数

| 来源 | 记录数 | 去重 `code` 数（原样） | 去重后基码数（前 18 位） | 出典 |
| --- | --- | --- | --- | --- |
| S1 | 732 | 414 | **413** | `len(s1)`, `len({c['code']})`, `len({base(c['code'])})` |
| S2（89576 原始） | 341 | 341 | **270** / **282** | `len(s2)`, 两种去后缀口径见下 |
| 派生快照 | 347 | 347 | **277** | `len(snap)`, 同上 |

- S1 编码长度分布 `{18:731, 22:1}`（唯一 22 位 = `180089050200MB001Y-201`）。
- S2 编码长度分布 `{18:249, 20:7, 21:70, 22:2, 23:13}`；快照 `{18:256, 20:7, 21:70, 22:1, 23:13}`。
- **第 18 位字符**：三源实测 100% 为 `Y`（S1 732/732、S2 341/341、快照 347/347）→ `campus_rule` 成立。

### 5.2 ② 时间字段分段结构

| 指标 | 值 | 出典 |
| --- | --- | --- |
| 快照 `time` 空 / `weeks` 空 | 0 / 0（347） | `sum(1 for c in snap if not c['time'].strip())` |
| `time` 段数分布（`；` 切） | `{1:177, 2:128, 3:40, 4:2}` | `Counter(len(c['time'].split('；')))` |
| `weeks` 段数分布 | `{1:177, 2:128, 3:40, 4:2}`（与 time **完全相同**） | `Counter(len(c['weeks'].split('；')))` |
| time/weeks 段数不一致的行 | **0** | 逐行比较两式 |
| 不可解析的周次段 | **0** | 正则 `^第[\d,\-]+周$` |
| `weeks` 每段内区间个数分布 | `{1:324, 2:211, 3:13, 4:10, 5:1, 7:1, 8:1}` | `Counter(len(seg.split(',')))` |
| 星期 token 计数 | 一79 二96 三81 四75 五52 六90 日88 | 正则 `^周([一二三四五六日天])` |
| 节次区间（快照）不同取值数 | 18；top `(5,7)`139、`(10,12)`109、`(1,4)`80、`(3,4)`50 | `Counter(...)` |
| S2 结构化：含排课行 / 空排课行 | 339 / **2** | `sum(bool(r['schedule']))` |
| S2 每行排课条目数分布 | `{0:2, 1:173, 2:127, 3:36, 4:3}` | `Counter(len(r['schedule']))` |
| S2 `weekday` 分布（1–7） | 1:76 2:92 3:77 4:75 5:53 6:88 7:86 | `Counter(e['weekday'])` |
| S2 `weeks` 全局 min/max | 1 / **22**；`start>end` 0 例 | `min/max(...)` |
| S2 每段周次区间数分布 | `{1:314, 2:205, 3:15, 4:10, 5:1, 7:1, 8:1}` | `Counter(len(e['weeks']))` |

### 5.3 ③ capacity / enrolled 缺失值与 0 值

| 来源 | capacity 空 | capacity = 0（快照）/ = `"/"`（S2） | capacity > 0 | enrolled 空 | enrolled = 0 | enrolled > 0 |
| --- | --- | --- | --- | --- | --- | --- |
| 快照 347 | 0 | **41**（字面 `"0"`） | 306 | 0 | 70 | 277 |
| S1 732 | **732**（全空） | 0 | 0 | **732**（全空） | 0 | 0 |
| S2 341 | 0 | **40**（字面 `"/"`，另 `0` 值 **0** 条） | 301 | 0 | 75 | 266 |

- **快照** `capacity=="0"` 且 `enrolled>0` 的行 = **40**（与 `invariant-checks.md` §3 一致，本次复核相同）；
  剩 1 行 `capacity=="0"` 且 `enrolled==0`（`180101120500PB003Y-03 学术道德与学术写作规范`）。
- 快照里 `enrolled > capacity > 0` 的**真实超容量** = **0**。
- 出典：`sum(1 for c in snap if c['capacity']=='0')` 等；`sum(1 for r in s2 if r['capacity']=='/')`=40。

### 5.4 ④ 周次超出学期长度

- 参照：秋季学期 **20 教学周**（`doc/prototype-issues.md` P15、`scripts/build_web_prototype.py` 明写"秋季学期共 20 教学周"）。
- 快照：**周次上界 > 20 周的行 = 16**（全部恰好到第 **22** 周，全部是 `初级汉语1`/`初级汉语2`，
  编码 `180101050102PB001Y-*`(5 条) 与 `180101050102PB002Y-*`(11 条)，属性均为 `公共必修课`）。
- 快照每门最大周次直方图：`{7:2, 8:3, 9:12, 10:13, 11:6, 12:16, 13:31, 14:17, 15:34, 16:45, 17:25, 18:32, 19:29, 20:66, 22:16}`（无 21 周）。
- 阈值敏感性：>18 周 **111** 行、>19 周 **82** 行、>20 周 **16** 行、>22 周 **0** 行。
- S2 原始同样 **16** 行（同一批汉语课）。
- 出典：`sum(1 for c in snap if max(int(x) for x in re.findall(r'\d+', c['weeks']))>20)`。
- ⚠ **诚实边界**：三个冻结源里**没有任何字段声明学期长度**；"20 周"是 `prototype-issues.md` 引用的教务口径，
  不是数据。这个数字随学期口径变化，引用时必须带口径。

### 5.5 ⑤ 同一课程同一时段出现在多个周次块

- 快照中"某课程的同名 `(星期,节次)` 段在 `；` 分段中出现 ≥2 次"的行 = **4**（与 `invariant-checks.md` §0 一致）：

| 课程编码 | 课程 | time | weeks |
| --- | --- | --- | --- |
| `180086081201P3003Y` | 超大规模集成电路基础 | 周三(5-7)；周三(5-7)；周六(5-7) | 第3-5,7-15周；第16周；第6周 |
| `180096120400MX020Y` | 科技创新政策分析 | 周一(10-12)；周一(10-12) | 第2-3,5-12周；第13周 |
| `180202085403P2004Y` | 集成电路制造技术 | 周一(10-12)；周一(10-12)；周六(1-3) | 第3-13周；第14周；第2-5,7-13周 |
| `180202085403PB001Y` | 学术道德与学术写作规范-分论 | 周三(10-11)；周三(10-11) | 第3-5,7周；第8周 |

- 同一课程"整段 (time **且** weeks) 完全重复"的行 = **0** → 这 4 行是**半学期拆分**（同一格、不同周次），
  不是数据重复。正是 I1 要保护的场景。
- S2 原始：同一行内 `(weekday,periods)` 出现在 >1 个 schedule 条目 = **0**（它那 4 行在原始里是**不同周次**的条目，
  被快照压平成重复段）。
- 出典：`Counter(re.sub(r'\s','',s) for s in c['time'].split('；'))`。

### 5.6 S1 time/weeks 为空（A1 复核）

- **S1 顶层 `time` 非空 = 0/732；`weeks` 非空 = 0/732。**
- `sessions[]` 的 `time`/`weeks`/`room` 非空 = **0**；`sessions` 长度 = **732/732 恒为 1**。
- 结论：A1 "0/732" **本次复核成立**，且连退路（`sessions`）也是空的。

### 5.7 词表与跨源一致性（`；` 段数之外的对账）

- 属性词表：S1 有 `实践课`(1) 无 `科学前沿讲座`；快照/S2 有 `科学前沿讲座`(1) 无 `实践课`。
- 快照 vs S2 原始，在 **251 个可 1:1 对应的共享基码**上：
  - 星期节次集合不一致 **8** 例（占 3.2%）；例如 `1801010705I0P1003Y` 快照 `周一(9-11)` / S2 `周一(10-12)`。
  - 周次整数集合不一致 **9** 例（占 3.6%）；例如 `180086081202PX005Y` 快照含第 5 周、S2 不含。
- **计数口径（必须写在数字旁边）**：S2 的 341 行按「去掉数字班次后缀 `-NN`」去重 = **282**（A1 简报 E3 用的口径）；按「去掉第一个 `-` 之后的全部后缀」/ 取前 18 位 = **270**。两者差 12 个字母后缀（`-S503`、`-W501`、`-201`、`-304` 等）。下表统一用 **270（更激进）**；引用 282 时说明是「仅去数字后缀」口径。
- 基码重叠：S1 413、S2 270（282 口径下为 282）、快照 277；S1∩S2raw **224**、S1∩快照 **230**、快照−S1 **47**、S2raw∩快照 **269**。
- 与 `doc/data-authority.md` "❶与❹对同一门课的星期+节次+周次**完全一致**"相比：**在被引用的那个样例上一致，在全集上约 96–97% 一致**——已不是"完全一致"（§6 陷阱 T8）。

### 5.8 分类分布（供字典取值列复核）

| 字段 | 分布 | 出典 |
| --- | --- | --- |
| S1 `semester` | 秋季 400 / 春季 332 | `Counter` |
| S1 `department` | 国际学院 160、计算机科学与技术学院 87、电子电气与通信工程学院 87、外语系 73、网络空间安全学院 49、集成电路学院 41 | `Counter().most_common` |
| S1 `source` | 开课计划表0828.xlsx 441 / 核心课和专业课列表0828.xlsx 291 | `Counter` |
| 快照 `level` | 硕博通用课程 203 / 硕士课程 136 / 博士课程 8 | `Counter` |
| 快照 `exam` | 闭卷笔试 110 / 课堂开卷 97 / 读书报告 55 / 大开卷 24 / 其它（需说明）51 / 文献综述 10 | `Counter` |
| 快照 `subject` | 77 个不同值；top 语言学及应用语言学 30、工程管理 25、外国语言文学 19 | `Counter` |
| 快照 `room` | 53 个不同值 | `set` |
| S2 `hours` | `40`99、`60`57、`30`28、`36`27、`50`24、`128`22、`32`21、`20`17 | `Counter` |
| S5 `categories` | 7 类（含 `min_credits` 7/4/4/1/2/2/12；核心课与专业课另有 `min_courses=2`） | 读文件 |

---

## 6. 陷阱清单 —— 逐条与"示例陷阱"对账（含**不符**发现）

| # | 示例/文档中的说法 | 实测结论 | 判定 |
| --- | --- | --- | --- |
| T1 | `capacity=0` 是"未设置"哨兵而非真实容量 | 快照 41 行 `capacity=="0"`，其中 40 行 `enrolled>0`；真实 `enrolled>capacity>0` = 0 | ✅ **在 347 快照上成立** |
| T2 | 同上（陷阱的措辞） | **官方 S2 原始里"未设置"哨兵是 `"/"`（40 行），不是 `0`；`0` 值 0 条。**快照把 `"/"` 渲染成 `0` | ⚠️ **部分不符（口径差异，不是矛盾）**：官方原文用 `"/"`；**快照把 `"/"` 渲染成 `0`**。判据不变——两者都是「未设置」哨兵 |
| T3 | `time`/`weeks` 用 `；` 分段且两字段段数对应 | 段数分布完全相同，不一致 0 行 | ✅ 成立（**仅对 347 快照**；S1 两列全空，S2 是结构化数组，不存在"段数"概念） |
| T4 | 周次是区间集合不是单个数字 | `第2-5,7-17周` 可展开为整数集合；`第6周` = `[(6,6)]`；`start>end` 0 例 | ✅ 成立 |
| T5 | 同一课程编码可有多班次后缀 | S1 732→414→**413**；S2 341→**282**（只去数字后缀）/ **270**（去全部后缀）；快照 347→**277** | ✅ 成立（口径见 §5.7） |
| T6 | S1 里 `time`/`weeks` 为空的行数（A1 报 0/732） | 顶层 **0/732**；`sessions[]` 也 0；`sessions` 恒 1 条且空 | ✅ 成立（A1 复核通过） |
| T7 | **学期字段不在开课计划表内** | **不符**：committed 的 S1 快照**每行都有 `semester`**（秋季 400 / 春季 332），另有 `campus`(玉泉路)、`department`、`source`。`doc/data-authority.md` 更把 ❷ 工作簿列为"开课学期"的**权威源**（★ 只有它有） | ❌ **与数据不符**：S1 有学期；真正**没有**逐行学期的是 S2 与快照（S2 只能按 `term_id`/文件推） |
| T8 | `doc/data-authority.md`："❶(官方) 与 ❹(派生快照) 对同一门课的星期+节次+周次**完全一致**" | 在 251 个共享 1:1 基码上：星期节次不一致 **8** 例(3.2%)、周次集合不一致 **9** 例(3.6%) | ⚠️ **不符（规模上）**：样例一致，全集约 96–97%，非"完全一致" |
| T9 | S2 = 19 字段原始抓取 | committed `89576-campus20.json` **每行 15 个 key**；19 字段是**上游未入库原始下载**的表头（`live-listing-provenance.md`）。committed 文件不含 `level`/`exam`/`subject`/`授课方式`/`是否远程教学`/`助教` | ⚠️ **措辞须区分**：19 字段≠本文件 |
| T10 | 两个"冻结数据源"= S1 + S2 | 另有一份 347 快照是**派生**数据（从教务系统爬取，归档渠道见 `live-listing-provenance.md`），与 S2 不是同一次抓取，二者在 251 个共同基码上仍有 3% 级分歧（T8） | ⚠️ **命名分歧**：A2 冲突检查实际跑在这份派生快照上，引用其数字时须标清上游 |
| T11 | （领域）教室/考试方式 | 快照 `room` 0 空、`exam` 6 值；S2 `rooms` 是数组、**无** `exam`；S1 `exam` 全空 | 提示：三源字段覆盖不同，别跨源假定字段都在 |
| T12 | （领域）"课程满"是班次状态 | 快照真实 `enrolled>capacity>0` = 0 例；`capacity` 未知（空/`0`/`/`）时"满/未满"**不可判定** | 提示：`capacity` 缺失率高时不可下"无超容量"结论 |
| T13 | 缺失 ≠ 空 | 快照 **13 字段 0 空值**；"缺"表现为哨兵 `0`/`/` 或整行缺席。S2 `chief` 空 202/341(59%)、`teacher` 空 69/341 | 提示：别用"空串"作唯一缺失判据 |
| T14 | 编码"不是不透明的" | 前 18 位为基码，第 18 位恒 `Y`（三源 100%）；长度 18/20/21/22/23 | 成立；但**只能**推校区，不能推学期/容量 |

---

## 7. 未证实 / 需外部依据（不编造）

- **学期长度**：三个冻结源无此字段；"秋季 20 周"来自 `doc/prototype-issues.md` 引用，**非数据**（§5.4）。
- **S2 原始文件的确切逐字段上游映射**：`live-listing-provenance.md` 给出 19 个 SEP 表头；committed 15 key 与
  它们的**逐列一一对应**我只核到 13 个语义等价列（另 2 个 `course_id`/`schedule_pages_sha256`/`campus` 为抓取侧新增），
  其余为**结构推断**，文中已标注，未逐条证实。
- **`department` 是否等同工作簿"课程所属学科"**：`sections-snapshot.json` 的取值（如"国际学院""计算机科学与技术学院"）
  读起来是**开课院系**而非学科；与 `data-authority.md` 所述工作簿列"课程所属学科"是否同一列，**未证实**。
- **S1 的 `semester` 是工作簿列还是快照生成时按工作表名回填**：`snapshot-provenance.md` 的导入提示只列了
  "缺少 培养层次/开课周/星期节次"，未提学期；因此两读法都可能，**未证实**（但 committed 文件里字段确实存在）。
- **S2 `capacity` 数值的官方口径**（限选是否为"计划容量"或"实际可容"）：数据无说明，**未证实**。

---

*实测于本会话（2026-10-04），全部为 inline `python3` 对 committed 文件运行；哈希见 §0.2。未新增任何脚本文件。*

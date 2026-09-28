# Measured inspection of saved course-plan versions

- Generated: 2026-09-27 15:37
- Reproduce with: `python3 scripts/inspect_plan_versions.py`

## `选课规划-已选课程-2026-09-05.xlsx`

- sha256: `8d6f9e65b9c57dea8571d880f86873401b54ac3abf9dd42920a57382cc689e2d`
- size / mtime: 85082 bytes, 2026-09-05 11:33
- worksheets: 21  (weekly timetable sheets: 20)
- non-empty cells: 901
- non-week sheets: ['全部课程']

## `选课规划-已选课程-2026-09-15.xlsx`

- sha256: `dcc6cae7596ba48b7fd706ad493274b186ab1b25c486f8fd9b783c16cb9dfaf0`
- size / mtime: 41111 bytes, 2026-09-15 21:41
- worksheets: 19  (weekly timetable sheets: 19)
- non-empty cells: 558
- non-week sheets: (none)

## Cross-version differences

Comparing `选课规划-已选课程-2026-09-05.xlsx` (older) against `选课规划-已选课程-2026-09-15.xlsx` (newer).

- worksheet sets identical: False
- sheets only in older: ['全部课程', '第1周']
- sheets only in newer: []
- cells only in older: 388
- cells only in newer: 45
- cells present in both with different text: 0
- cells only in older, restricted to common sheets: 22
- cells only in newer, restricted to common sheets: 45

### Sample: cells only in older (common sheets)

- `第10周!C5`: 自然辩证法概论 第1–4节 · 玉泉礼堂
- `第11周!C5`: 新时代中国特色社会主义理论与实践 第1–4节 · 教学楼阶一6
- `第12周!C5`: 新时代中国特色社会主义理论与实践 第1–4节 · 教学楼阶一6
- `第13周!C5`: 新时代中国特色社会主义理论与实践 第1–4节 · 教学楼阶一6
- `第14周!C5`: 新时代中国特色社会主义理论与实践 第1–4节 · 教学楼阶一6
- `第15周!C5`: 新时代中国特色社会主义理论与实践 第1–4节 · 教学楼阶一6
- `第16周!C5`: 新时代中国特色社会主义理论与实践 第1–4节 · 教学楼阶一6
- `第17周!C5`: 新时代中国特色社会主义理论与实践 第1–4节 · 教学楼阶一6
- `第18周!C5`: 新时代中国特色社会主义理论与实践 第1–4节 · 教学楼阶一6
- `第2周!C5`: 自然辩证法概论 第1–4节 · 玉泉礼堂
- `第3周!C5`: 自然辩证法概论 第1–4节 · 玉泉礼堂
- `第3周!H5`: 自然辩证法概论 第1–4节 · 玉泉礼堂

_(showing 12 of 22)_

### Sample: cells only in newer (common sheets)

- `第10周!B14`: 科技信息检索与利用（电子通讯领域） 第10–12节 · 教学楼221（玉泉路机房二）
- `第10周!B9`: 智能软件工程 第5–7节 · 教学楼320
- `第10周!D9`: 自然辩证法概论 第5–8节 · 玉泉礼堂
- `第11周!B14`: 科技信息检索与利用（电子通讯领域） 第10–12节 · 教学楼221（玉泉路机房二）
- `第11周!B9`: 智能软件工程 第5–7节 · 教学楼320
- `第11周!D5`: 新时代中国特色社会主义理论与实践 第1–4节 · 教学楼阶一6
- `第12周!B14`: 科技信息检索与利用（电子通讯领域） 第10–12节 · 教学楼221（玉泉路机房二）
- `第12周!B9`: 智能软件工程 第5–7节 · 教学楼320
- `第12周!D5`: 新时代中国特色社会主义理论与实践 第1–4节 · 教学楼阶一6
- `第13周!B9`: 智能软件工程 第5–7节 · 教学楼320
- `第13周!D5`: 新时代中国特色社会主义理论与实践 第1–4节 · 教学楼阶一6
- `第14周!B9`: 智能软件工程 第5–7节 · 教学楼320

_(showing 12 of 45)_

### Sample: cells changed in place


_(showing 0 of 0)_

## Week occupancy (`选课规划-已选课程-2026-09-05.xlsx`)

A course is placed in a *different worksheet* per teaching week, so the
week dimension is encoded by sheet membership rather than by a field.
This is exactly what a weekday+period-only comparison cannot see.

| Course | Weeks present | Count | Cell(s) |
| --- | --- | --- | --- |
| 学术道德与学术写作规范-通论 | 5-9 | 5 | D11, G11 |
| 学术道德与学术写作规范-分论一班 | 11-15 | 5 | F5 |
| 自然辩证法概论 | 2-5, 7-10 | 8 | C5, H5 |
| 新时代中国特色社会主义理论与实践 | 11-18 | 8 | C5 |
| 数字信号处理原理与应用二班 | 2-17 | 16 | F9 |
| 计算机代数在科学与工程中的应用 | 2-18 | 17 | E14 |
| 海洋声学 | 2-5, 7-20 | 18 | C9, H9 |
| 模式识别与机器学习 | 2-20 | 19 | D14, G14 |

### Slots hosting more than one course in different weeks (1)

These are the cases that make week ranges mandatory: a weekday+period-only
comparison reports every one of them as a clash, though the courses never
overlap in time.

| Cell | Courses and the weeks each occupies |
| --- | --- |
| C5 | 新时代中国特色社会主义理论与实践 (weeks 11-18); 自然辩证法概论 (weeks 2-5, 7-10) |

## Week occupancy (`选课规划-已选课程-2026-09-15.xlsx`)

A course is placed in a *different worksheet* per teaching week, so the
week dimension is encoded by sheet membership rather than by a field.
This is exactly what a weekday+period-only comparison cannot see.

| Course | Weeks present | Count | Cell(s) |
| --- | --- | --- | --- |
| 学术道德与学术写作规范-分论一班 | 11-15 | 5 | F5 |
| 新时代中国特色社会主义理论与实践 | 11-18 | 8 | D5 |
| 自然辩证法概论 | 2-10 | 9 | D9, G9 |
| 科技信息检索与利用（电子通讯领域） | 2-5, 7-12 | 10 | B14 |
| 数字信号处理原理与应用二班 | 2-17 | 16 | F9 |
| 计算机代数在科学与工程中的应用 | 2-18 | 17 | E14 |
| 海洋声学 | 2-5, 7-20 | 18 | C9, H9 |
| 智能软件工程 | 3-20 | 18 | B9 |
| 模式识别与机器学习 | 2-20 | 19 | D14, G14 |

### Slots hosting more than one course in different weeks (0)

- none found


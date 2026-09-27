# Snapshot provenance

- Source file (NOT committed): `/Users/tangliwei/Downloads/选课地图-本地备份 (3).json`
- Source sha256: `62594e799e1c83a8fdc2cacd0239f36e14264b55282c768853c89f6690f463ad`
- Snapshot: `raw/sections-snapshot.json`
- Snapshot sha256: `ffcf1ae023e59fe8a09d83584fe7ba8293eb982cce8887f51e7db140f98d8c9e`
- Campus filter: `玉泉路`
- Courses in source: 4877  |  kept: 732
- Courses in the saved plan: 14
- Planned courses that could be matched to this campus subset: 3 (lower bound -- most planned entries carry no 开课校区 field)
- Courses in the source with NO 开课校区 field: 0 of 4877

## Coverage of the two fields a conflict check needs (KEY FINDING)

- Kept courses carrying an 开课周 (week-range) value: **0 of 732**
- Kept courses carrying an 星期节次 (weekday+period) value: **0 of 732**
- A conflict check needs both. With neither, no computer-assisted conflict
  filtering is possible from the structured source alone.

## Saved plan under study

- planned courses: 14; summed credits: 26.0
- planned courses with NO 开课校区 field: 11 of 14
- by attribute: 公共必修课=5, 专业课=4, 学科核心课=2, 专业核心课=2, 公共选修课=1

## Kept courses by attribute

- 专业课: 234
- 学科核心课: 206
- 专业核心课: 142
- 公共选修课: 79
- 公共必修课: 29
- 研讨课: 25
- 实验课: 16
- 实践课: 1

## Kept courses by source workbook

- `2026-2027学年秋季和春季开课计划表0828.xlsx`: 441
- `2026-2027学年研究生核心课和专业课列表（请先阅读表格最下方的说明）0828.xlsx`: 291

## Import issues reported by the planner for the official workbooks

- `2026-2027学年秋季和春季开课计划表0828.xlsx`: 工作表“2026-2027学年秋季学期课程计划情况”缺少 培养层次、开课周、星期节次，相关信息可能无法显示或筛选。
- `2026-2027学年秋季和春季开课计划表0828.xlsx`: 工作表“2026-2027学年春季学期课程计划情况”缺少 培养层次、开课周、星期节次，相关信息可能无法显示或筛选。
- `2026-2027学年研究生核心课和专业课列表（请先阅读表格最下方的说明）0828.xlsx`: 工作表“秋季学期核心课、专业课列表”缺少 开课周、星期节次，相关信息可能无法显示或筛选。
- `2026-2027学年研究生核心课和专业课列表（请先阅读表格最下方的说明）0828.xlsx`: 工作表“春季学期核心课、专业课列表”缺少 开课周、星期节次，相关信息可能无法显示或筛选。

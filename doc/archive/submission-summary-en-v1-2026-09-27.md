# Platform submission summary

Posted on learn.spaiq.ai. The brief requires **150-300 words**. Verify with:

```bash
python3 scripts/count_words.py
```

## English (submitted)

<!-- SUMMARY-EN-START -->
One semester of UCAS graduate study requires assembling a conflict-free course plan from two official
planning workbooks that disagree in structure, under a campus rule (Yuquanlu only, course code position
18 = Y) and first-come-first-served submission. The bottleneck is conflict checking, because a clash needs
three conditions at once: same weekday, overlapping periods, and overlapping week ranges. Measured on the
2026-27 planning workbooks, the imported database holds 4,877 courses, of which 732 open at Yuquanlu — and
none of those 732 carries a week-range value and none carries a weekday/period value. The importer reports
exactly this defect four times. The only artefact that does encode the week range is the hand-built timetable:
19 weekly worksheets in which the week is expressed by which sheet a course appears in. Across the nine
courses in the plan, week coverage varies from 5 to 19 weeks, and one slot is shared by two courses with
disjoint week ranges, so a weekday-and-period-only check would report a clash that does not exist. Comparing
two saved versions of the plan shows 22 cell positions removed and 45 added with none edited in place: the
plan is re-laid-out, and every re-layout forces a full manual re-check. A fixed Excel template cannot encode
the week dimension either. The semester scope is therefore clash detection, priority ranking and per-rejection
explanations; automatic submission is an explicit non-goal.
<!-- SUMMARY-EN-END -->

Word count is checked by `scripts/count_words.py`, not by hand.

## 中文（备查，不提交）

一学期的国科大研究生选课，要在两份结构互不相同的官方开课计划表里拼出一份无冲突课表，还要满足"仅玉泉路
校区（课程编码第 18 位为 Y）"的硬约束和先到先得的提交规则。真正的瓶颈是冲突核对：一次冲突需要三个条件
同时成立——星期相同、节次相交、周次区间相交。实测 2026-2027 学年开课计划表导入后共有 4877 门课，其中
玉泉路校区 732 门，而这 732 门里**没有一门**带"开课周"字段，也**没有一门**带"星期节次"字段；导入器正好
把这个缺陷报告了 4 次。唯一真正带周次信息的，是人工排出的课表：19 张按教学周分的工作表，"周次"由课出现
在哪张表里表达。方案里 9 门课的周次覆盖从 5 周到 19 周不等，并且有一个槽位被两门周次不重叠的课分时占用
——只比较"星期+节次"会把它们误判为冲突。对比两个保存版本的方案：22 个位置被删、45 个新增、没有一个位置
是原地改文本，说明方案是被整体重排的，而每次重排都要求全程重新核对一遍。固定的 Excel 模板同样无法承载
周次维度。因此本学期范围定为冲突检测、优先级排序与逐条给出排除原因；自动抢课是明确的非目标。

## Access note

Personal working files (the two saved plans and the planner backup) are not committed; only the derived
snapshot and measurements are. See the provenance table in `README.md`.

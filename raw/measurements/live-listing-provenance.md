# Public listing: provenance and join with the official workbooks

- URL: https://courseplanner.cysdy.cn/default-courses.json
- Raw download: 8103455 bytes, sha256 `7c6090e40801d1ba4ebf3665c54eafaf4ec6e5e3565d996df74e63fac53e8413` (not committed)
- Frozen subset: `raw/yuquanlu-live-courses.json`, sha256 `3724ade7ff05dcd3465c017f965feffe0eaa26cfbcaafebf976d268003122a69`
- Campus rule applied: course code position 18 == 'Y'
- Entries downloaded: 2991  |  kept (Yuquanlu): 347
- Kept entries with a week value: 347 / 347
- Kept entries with a weekday/period value: 347 / 347
- Kept entries with a capacity value: 347 / 347
- Kept entries with an enrolled value: 347 / 347
- Fields present on this source (sampled): 主讲教师, 助教, 培养层次, 已选, 序号, 开课单位, 开课周, 所属学科/专业, 授课方式, 教室, 星期节次, 是否远程教学, 考试方式, 课时/学分, 课程名称, 课程属性, 课程编码, 限选, 首席教授
- NOTE: this source carries no campus field, so the Yuquanlu subset can only be
  recovered from the course-code rule above.

## Join with the official workbooks (A+B), by course code

- official workbooks, Yuquanlu courses (records / codes): 732 records, 414 codes
- public listing, Yuquanlu courses: 347 codes
- codes in BOTH (all fields obtainable): **217**
- codes only in the official workbooks (no week/period/capacity): **197**
- codes only in the public listing (no campus field, no semester): **130**

This is the measured reason the workflow is manual: assembling one input that can
support a conflict check *and* a grab-priority ranking means joining three
heterogeneous sources, and even after joining, a large share of courses still
lack one group of fields or the other.


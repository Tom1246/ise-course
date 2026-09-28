# Platform submission summary - ISE-A1

Posted on learn.spaiq.ai. The requirement is **150-300 words**; the count below is produced
mechanically by `python3 scripts/count_words.py` (not by eye).

**Word count: 274** (script output, reproducible with that command).

## English (submitted)

<!-- SUMMARY-EN-START -->
This brief argues that postgraduate course registration at UCAS deserves a semester of software work: arranging a semester's timetable by eye goes wrong easily.

The author is a first-year master's student at UCAS, taking centralised teaching at the Yuquan Road campus. They may not register across campuses and must still meet the programme's credit and degree-course rules; registration is first come, first served inside a fixed window, and some required courses run in the autumn only, so missing a section means waiting a year.

Evidence comes from two official sources, the course-planning workbook (S1) and the public course listing jwba (S2), plus two handwritten plans (S3) and an AI plan (S4). First, both versions failed: the 14-course manual plan put 3 courses in the same slot (Thursday periods 10–12), and the AI plan misread teaching weeks, taking Marine Acoustics "every Sunday" as weekly when it runs only in week 3. Second, required courses had to be switched during registration: all 4 sections of Dialectics of Nature were full or over capacity (422/420), and 4 of 8 New Era sections were full at 265/265. Third, the two official systems do not cover the same courses: 282 codes against 234 autumn courses, overlapping in only 223.

The proposed tool takes a registration plan plus the programme's credit constraints, decides conflicts across weekday × period × teaching week, and outputs a conflict-free timetable plus a justified registration order. The target is under 5 minutes, against a measured manual baseline of about 30 minutes. Runs are reproducible from frozen snapshots carrying capture times and hashes, every number traces to its source, and the AI's overturned claims stay on record.
<!-- SUMMARY-EN-END -->

Repository: https://github.com/Tom1246/ise-course (tag `a1-v2`)

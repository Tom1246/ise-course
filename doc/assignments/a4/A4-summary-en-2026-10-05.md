# Platform submission summary — ISE-A4

Posted on learn.spaiq.ai. The requirement is **150-300 words**; the count is produced mechanically by
`python3 scripts/count_words.py`.

## English (submitted)

<!-- SUMMARY-EN-START -->
This slice answers the question my own A1 evidence was burned by: which course should I register for first? The
existing planner shows clashes and credits but, as A1 found, has no ordering at all. The slice adds a pure,
tested ranking layer plus one panel: each course gets a reason, and the plan gets one explainable order
(measured urgency first, then degree course, autumn-only, places left, course code).

What changed the work was the peer review. The first version printed "places left" from the data's capacity and
enrolment fields. The independent reviewer showed that the enrolment figure is zero in 1,968 of the 1,978 rows
that have a capacity, and that nothing records when it was captured - so the panel was dressing a static section
size up as live registration pressure, while treating a neighbouring field with great care. That is exactly the
failure A1 recorded ("treating an old snapshot as current"). I accepted the finding: a figure is now published
only together with a capture time, and otherwise the panel prints no number, says which piece is missing, and
ranks unknown cases last instead of pretending they are safe.

Verified locally: 24 unit tests, lint clean, type check clean, build clean, four end-to-end cases against the
running app, and a rollback that was actually performed - the reverted tree is identical to upstream and still
builds. The slice is a patch, purely additive (+523/-0), and applying it to a fresh clone of the upstream
repository was checked. Server-side authorization is deliberately deferred and specified in the edge-case notes.
<!-- SUMMARY-EN-END -->

Patch and documents: `doc/assignments/a4/` in <https://github.com/Tom1246/ise-course> (tag `a4-v1`).

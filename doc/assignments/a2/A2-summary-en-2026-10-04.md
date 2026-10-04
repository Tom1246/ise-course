# Platform submission summary — ISE-A2

Posted on learn.spaiq.ai. The requirement is **150-300 words**; the count below is produced mechanically by
`python3 scripts/count_words.py`, not by eye.

## English (submitted)

<!-- SUMMARY-EN-START -->
A2 turns the A1 workflow — planning one semester of graduate courses — into a domain model with rules that can be
checked by running code. The deliverable is a glossary and context map, process, state and data-dictionary
artifacts, three invariants with an executable check, one material rule written three ways, a data-governance
specification, and a walkthrough record. An executed notebook drives the same check code, with its outputs kept
in the file.

Three findings changed the model rather than decorating it. First, the conflict rule needs all three conditions
at once — same weekday, overlapping periods, overlapping weeks. Week ranges are intervals, so [3,5] and [6,8] are
compatible while [3,5] and [4,8] clash; the naive screen is wrong in both directions. Second, the check's first
run reported forty over-capacity sections, but every one had capacity 0 with students enrolled — 0 is a sentinel
for "not set", so the invariant was rewritten to separate unknown capacity from real over-capacity and the false
finding disappeared. Third, the workbook cannot answer "when": 0 of its 732 records carry a weekday or week
range, so field-level authority replaced source-level authority.

The A1 claim is now reproducible: the three courses said to share Thursday periods 10-12 all do, giving three
conflicting pairs from committed data alone. The catalogue's 4,757 overlapping course pairs are recorded as
offer-set density, explicitly not violations.

Limits stay visible: the grab order is not specified here, the programme states credit floors only so the ceiling
is unimplemented, and spring data does not exist yet.
<!-- SUMMARY-EN-END -->

Repository: https://github.com/Tom1246/ise-course (tag `a2-v1`)

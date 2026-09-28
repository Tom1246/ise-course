# Aggregates only (the per-course table is in data/private/, not committed)

- planned courses analysed: 14
- courses with a capacity figure from some source: 13 of 14
- courses with a week-range figure from some source: 13 of 14
- courses offered in 秋季 (i.e. not deferable within the year): 7 of 14
- courses at >= 90% of capacity: 8 of 13 with a capacity figure
- courses whose SEMESTER is unknown from every source: 6 of 14
- courses NOT offered in 秋季 (春季-only) but present in the plan: 0
- must-take set source: derived from course attribute (a CANDIDATE set, not the degree programme)

## Tier distribution

- P0: 3
- P1: 3
- P3: 1
- PX: 1
- PU: 6

The two orders disagree on the measured data, which is the reason the project must
emit two lists: a conflict-free plan, and a grab order. See doc/priority-rules.md.


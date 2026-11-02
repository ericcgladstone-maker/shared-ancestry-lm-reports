# Rewrites that return their input unchanged

Post hoc, no model calls. A step changed the text if its output is not identical to its input. Counts are over the distinct chains of each depth run (five per block, 180 blocks).

| Producer | Rewrite calls | Chains | Mean steps that changed the text | Chains changed at every step | Out-star sets with two identical reports (one rewrite) |
|---|---|---|---|---|---|
| gemini-3.5-flash-lite | 1 | 900 | 0.99 | 892 | 0 |
| gemini-3.5-flash-lite | 2 | 900 | 1.90 | 810 |  |
| gemini-3.5-flash-lite | 3 | 900 | 2.70 | 657 |  |
| gemini-3.5-flash-lite | 5 | 900 | 4.12 | 370 |  |
| claude-haiku-5-5 | 1 | 900 | 0.99 | 892 | 3 |
| claude-haiku-5-5 | 2 | 900 | 1.92 | 829 |  |
| claude-haiku-5-5 | 3 | 900 | 2.73 | 684 |  |

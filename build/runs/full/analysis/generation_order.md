# Generation order of the independent and out-star sets, full run

Post hoc check from the outside reader of 2026-11-02, no model calls. For each block, the mean generation time of the reports that differ between structures (reports 2 and 3) and of their parent observations. Sign test, two-sided, of how often the out-star's texts were generated first.

| Producer | Blocks | Out-star reports 2 and 3 first | p | Median lead, s | Out-star observation before both independent observations 2 and 3 | p |
|---|---|---|---|---|---|---|
| gemini-3.5-flash-lite | 180 | 102 | 0.086 | 1.3 | 117 | 0.000 |
| claude-haiku-5-5 | 180 | 94 | 0.602 | 0.4 | 113 | 0.001 |
| gpt-6-luna | 180 | 97 | 0.333 | 1.4 | 116 | 0.000 |

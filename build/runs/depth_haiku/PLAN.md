# Deeper rewriting, second producer (Claude Haiku 5.5)

Written 2026-11-02, before any call. Approved by Eric on 2026-11-02. This extends `runs/depth/PLAN.md`, the Gemini run to five rewrites, to a second producer so that the depth result does not rest on one producer.

## What is generated

- **Same design as the Gemini run.** Same generation code (`run_depth.py --producer claude-haiku-5-5 --max-step 3`), worlds, replicates, structures, sharing pattern, template rule, prompts, validation, and output cap (Haiku's full-run cap).
- **Depth.** Chains stop at step 3. Five rewrites would cost about $1.61, and Anthropic has $1.43 left under its cap. The cost of a Haiku rewrite in the full run averaged $0.00045, so 5 chains × 2 steps × 180 blocks = 1,800 calls is about $0.80.
- **Spend limit.** The run stops if Anthropic spend in this run passes $1.10.
- **Storage.** Step-1 texts come from `runs/full/calls.jsonl`, which is not modified. New calls go to `runs/depth_haiku/calls.jsonl`.

## Analysis

`analyze_depth.py`, unchanged in method, at depths 1, 2, and 3 for Haiku. It reports:
- pooled, relational, and gain;
- the unfitted maximum rare overlap and the paired relational-minus-score difference;
- three-structure AUCs;
- the unshared single-report check;
- all nine unfitted statistics.

Depth 1 must reproduce the full run's Haiku values (pooled 0.856, relational 0.982, score 0.985) to rounding, or the analysis stops.

## Readings, fixed in advance

Haiku's depth-1 discrimination is near ceiling (0.982), so a decline is bounded by the ceiling and is not comparable in size with Gemini's. The results are therefore read descriptively, with no decision thresholds.

- **Retention.** The relational AUC after three rewrites, with its interval, is reported beside Gemini's after three rewrites. The question is whether high discrimination after several rewrites holds for a second producer.
- **Pooled against relational.** Whether the pooled baseline falls more than the relational model, as it did for Gemini.
- **Score comparison.** The paired relational-minus-score difference at each depth. At depth 1 it is post-selection, as for Gemini. The score was selected on data that included Haiku's depth-1 sets.
- **Single-report check.** As in the Gemini plan. A result outside the band is reported as a departure to investigate, not as proof that the construction failed.

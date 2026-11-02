# Deeper rewriting of the matched sets

Written 2026-11-02, before any depth call was made. Approved by Eric on 2026-11-02 at an estimated cost of about $0.75. Two reviews of the TACL draft found that the paper's generality rests on one rewrite: GPT (`redesign/GPT_Independent_TACL_Review_Posthoc_2026-11-02.md`) and a fresh outside reader (logged in `LOG.md`, 2026-11-02 08:50). This run asks how the separation between independent and out-star sets changes when more rewrites lie between each observation and each final report. The record below fixes the generation, comparisons, and readings in advance.

## What is generated

- **Scope.** The primary producer (gemini-3.5-flash-lite), incident genre, full access, neutral instruction. The full run's 60 worlds and replicates 0 to 2, so 180 blocks.
- **Chains.** In each block, every terminal report of the full run's independent, out-star, and Y sets is rewritten four more times in a chain.
  - The full run's report is step 1. Steps 2, 3, 4, and 5 are new calls.
  - Each step rewrites the text of the step before. The prompt, decoding, output cap, and validation are the full run's.
- **Templates.** Each new step draws a fresh rewrite template from the block's prompt family. The draw is seeded by block, position, and step, so depth is not confounded with repeating one instruction.
- **Keys.** Each new step's call key includes its position and step, so a text shared by structures at step 1 stays shared at every step. Shared texts are the first report in all three structures, the Y set's second report with the out-star's, and its third with the independent set's.
  - This keeps the full run's sharing pattern, so the matched-marginal argument holds at every depth.
  - Each block has five distinct chains, so 5 × 4 × 180 = 3,600 new calls.
- **Storage.** Depth-1 texts are read from `runs/full/calls.jsonl`, which is not modified. New calls go to `runs/depth/calls.jsonl`.
- **Spend limits.** The run stops if Google spend in this run passes $1.50, in addition to the per-provider cap in `residue/adapters.py`.

## Analysis

Sets at depths 1, 2, 3, and 5. Depth 4 is generated as a link in the chain but is not analyzed, which keeps the comparisons to those fixed here. Each depth is analyzed by the canonical code paths, with the full run's world-grouped five-fold assignment and the corrected rarity fit (own world removed).

| Comparison | Reported at each depth |
|---|---|
| Independent against out-star | pooled AUC, relational AUC, and paired gain, each with a 95% world-cluster interval |
| Unfitted score: maximum rare-sequence overlap over the three pairs | AUC and 95% interval; all nine unfitted statistics in an appendix table |
| Relational model minus the unfitted score | paired AUC difference with a 95% world-cluster interval, fixed here in advance |
| Three structures | macro one-versus-one AUC for pooled and relational models |
| Single reports, unshared texts (reports 2 and 3 of the independent and out-star sets) | feature and embedding learners, 90% interval, three-way rule at 0.43 to 0.57, as a check that single reports stay uninformative at depth |

Depth-1 results are recomputed from the same rows. They must reproduce the full run's values (P3 relational 0.908, pooled 0.699, unfitted score 0.863) to within rounding. Otherwise the analysis stops and the discrepancy is investigated.

## Readings, fixed in advance

These describe patterns in the intervals. They are not tests with a decision threshold.

- **Decay.** The relational AUC and gain fall with depth. The depth at which the gain's interval first includes zero, or the relational AUC's interval includes the pooled AUC, is reported as the depth at which the tested features no longer add detectable information.
- **Divergence.** The paired difference between the relational model and the unfitted score grows with depth and its interval excludes zero. This would show that, after repeated paraphrase, combining the relational features carries information that the best single text-reuse statistic loses.
- **Persistence.** Relational AUC at depth 5 stays within the depth-1 interval. This would show that shared ancestry survives five paraphrases in these pipelines.
- **Single-report check.** If single reports at some depth fall outside the equivalence band, the matched-marginal construction has failed at that depth. That depth is reported but not interpreted as relational evidence.

The run tests one producer only, as planned. Claude Haiku and GPT Luna are not run, because their remaining budgets cannot cover depth 5.

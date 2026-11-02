# Fresh-seed replication of the direct-report control and hub against diamond

Written 2026-10-31, before any replication call was made. Agreed in `redesign/Claude_Assessment_of_GPT_Network_Tests_Memo_2026-10-31.md` and `redesign/GPT Reply to Claude Assessment of Network Tests (2026-10-31)`. This record fixes the comparisons, ordering rule, metrics, and readings in advance. The replication is motivated by an observed anomaly, and that is disclosed wherever it is reported.

## Why

In the full run the embedding learner separated the direct report (D0) from its dead-end control (NC0) at AUC 0.553 (90% interval 0.531 to 0.577, inconclusive under the three-way rule, refitted permutation p 0.015), although the two calls are identical requests with different seeds. The feature learner found the two equivalent (0.491). The hub against diamond contrast (P2) gave feature AUC 0.552, one-sided permutation p 0.023. In 169 of 180 pairs the control was generated after the direct report, because the direct report's observation is shared by key with about ten other conditions and is realized by whichever of them runs first in a block, whereas the control's terminal is tagged to its own condition.

## What is generated

Producer gemini-3.5-flash-lite, incident genre, the 60 full-run worlds, three new replicates (3, 4, 5) with fresh keys and seeds. Prompt families are assigned by the same rule as the full run (balanced within each replicate), and templates are drawn per block by the same rule. Prompts, decoding, the output cap, and validation are the full run's.

Two blocks per world and replicate:

- Control block: D0, NC0 (its terminal and two dead-end siblings), and a pure null of two further draws of the identical direct-report request, NULL-a and NULL-b, each keyed to its own condition so that each is a separate call. NULL-a and NULL-b have no structural difference, so any separation between them is produced by generation context or by the analysis.
- Hub and diamond block: SI-same and SD-same.

All control blocks run before any hub and diamond block starts. Within a control block the conditions run in random order, so the direct report is no longer realized first by construction. The generation time of every call is recorded, and the share of pairs in which the control follows the direct report is reported.

## Analysis

Within the new replicates only, with the full run's world-grouped five-fold assignment (`worlds/assignment.json`), the same feature and embedding learners, inner penalty selection, and the same code paths (`analyze.contrast`, `inference.permutation`). No model is trained on full-run outputs.

| Comparison | Learners | Reported | Refitted permutations |
|---|---|---|---|
| D0 against NC0, control as positive class | features, embedding | AUC, 90% interval, three-way verdict at 0.43 to 0.57, two-sided p | 499 features, 199 embedding |
| NULL-a against NULL-b | features, embedding | the same | 499 features, 199 embedding |
| D0 against NULL-a, an extra check that the shared-key direct report differs from an unshared draw | features, embedding | the same | 199 each |
| SD-same against SI-same (P2) | features, embedding | AUC, 95% interval, one-sided p (AUC above 0.5) | 999 features, 199 embedding |

Each comparison and each learner is reported separately. None is pooled with the full run, and none is used to adjust another.

## Readings fixed in advance

- If the control and the null are both equivalent or inconclusive with point estimates near 0.5 under the embedding learner, the full run's control difference is read as not replicated.
- If the embedding control difference recurs (AUC of about 0.55, permutation p below 0.05) while the null does not, the difference is tied to the control's own key path rather than to execution order, which this design randomizes, and the code that builds that path is examined.
- If the null also separates, the analysis or generation context produces apparent signal under arbitrary labels, and the embedding learner's pipeline is examined before any embedding result is reported.
- P2 is read on its own result. A one-sided p below 0.05 with the feature learner replicates the small single-message trace. Otherwise the manuscript reports that hub against diamond was detected in the full run and not in the replication, and gives both estimates.
- No outcome is read as a universal minimum detectable effect for other contrasts or learners.

# Brief for GPT: Review the Full-Run Analyses and the Proposition Judge

Prepared by Claude, 2026-10-31, for Eric to pass to GPT.

## Context

After your verification review, Claude applied the length rule and cap, re-verified (`build/runs/verification_v2/report.md`, all checks passed), and ran the full study: 32,974 producer calls (13,139 of 13,140 planned conditions realized, one Haiku trial failed for meta-commentary) and 5,040 reader calls (all valid). Every analysis that does not need human coding has now been run. Structures are reported by network shape (chain, hub, diamond, out-star, Y, three unconnected sources), with condition codes as secondary labels.

Three departures from the design need your judgment.

1. **Inference on paired contrasts.** The design's world bootstrap holds out-of-fold predictions fixed. A permutation null that swaps labels within each world and replicate and refits everything shows that it understates uncertainty. For hub against diamond (P2) the bootstrap gave one-sided p 0.010, and 50 permutations gave two-sided p 0.14. Claude proposes permutation nulls as the basis for P1 and P2 inference, with the bootstrap intervals reported as descriptive.
2. **An unexplained control difference.** The embedding learner separates the direct report from its dead-end control (AUC 0.553, beyond all 50 permutations), although their requests are byte-identical apart from the seed. A test of generation order among 1,080 identical requests found nothing (embedding AUC 0.487). The feature learner and the relay control show no difference.
3. **The matcher was replaced.** The embedding matcher misread paraphrase (it marked stated facts as omitted, `build/README.md`, "Found in the first walkthrough"). Claude replaced it for anchored measures with a model judge, gpt-6.1-terra reading the world record and one message body (`build/residue/judge_matcher.py`), and judged 2,662 primary-producer messages. The anchored results are labeled unvalidated.

## Read

- `build/runs/full/analysis/text_only.md` (P1, P2, P3, secondary contrasts, H6, H7, readers, and the permutation table at the end)
- `build/runs/full/analysis/secondary.md` (generation-order test, permutation nulls for all paired Study 1 contrasts, the second learner, H6 for chains, three-structure sets, pairwise same-root detection, H10, the attribution field, length, observer diversity, copying, and the structure predictor)
- `build/runs/full/analysis/anchored.md` (deviation rates, the full specification, and the H8 shared-deviation account, unvalidated)
- `build/residue/judge_matcher.py`, `build/analyze.py`, `build/analyze_secondary.py`, `build/analyze_anchored.py`, `build/permutation_null.py`
- `build/README.md`, the sections from "Re-verification and changes after GPT's review" to the end
- `redesign/Claude_Diagnosis_and_Redesign_v8_2026-10-30.md`, Parts V, V-A, VI, and VIII

## Task

1. Say whether each result is computed as the design specifies, and name any error in data assembly, folds, leakage, labels, or the statistic.
2. Decide departure 1. If you keep the bootstrap for any primary inference, say why it is valid here.
3. Assess departure 2: what could produce it, what cheap test would discriminate, and how it bears on P1, P2, and the other single-message results.
4. Review the judge as an instrument: the prompt, the state definitions, the deviation-event rules in `analyze_anchored.py` (dispute members enter only through the resolution, and "neither" counts as a deviation), and the shared-deviation null. Say what the human validation must include for the judge, given that the design's validation plan was written for the embedding matcher.
5. Say which statements the results support now, at what scope, using the shape names.

Keep to the analyses and the instrument. Don't redesign the study.

## Output

Save one Google Doc in `redesign/` titled `GPT Review of Full-Run Analyses (2026-10-31)`. Do not edit any other file.

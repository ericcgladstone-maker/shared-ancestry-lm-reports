# Cross-producer transfer of the set models

Written 2026-11-01, before any transfer model was fitted. The analysis was agreed with GPT (pasted reply, 2026-11-01) and approved by Eric the same day. It uses existing messages only and makes no model calls. The script is `analyze_transfer.py`, and its outputs are `cross_producer_transfer.md` and `.json` in this folder.

## Question

The set models were trained and tested within each producer. The question here is whether a set model trained on one producer's messages recovers shared ancestry in another producer's messages.

## Comparisons

- **Producer pairs.** All six ordered pairs of the three producers (gemini-3.5-flash-lite, claude-haiku-5-5, gpt-6-luna). Each pair is also run with the training and test producer the same, as a check that the procedure reproduces the canonical within-producer results.
- **Rows.** Full access, neutral attribution.
- **Tasks.**
  - Three unconnected sources (IND) against the out-star (DEP), with the pooled baseline and the relational model (pooled plus relational features).
  - The three-structure task (IND, DEP, Y), with the relational model, scored by macro one-versus-one AUC.

## Procedure

- **Folds.** The fixed world folds of `worlds/assignment.json`. For outer fold f, the model is trained on the training producer's sets from worlds outside f and tested on the test producer's sets from worlds in f. No world appears in both training and test, so the event facts never cross the split, even between producers.
- **Penalty selection.** Chosen by four-fold world-grouped inner cross-validation on the training rows, over the same penalties and with the same scaler and logistic model as `residue/analysis.py`.
- **Rarity tables.** Built from the training producer's sets in the training worlds (`WorldRarity`). Each training row is scored with its own world removed, and test rows are scored against the full training table, which never contains their world.
- **Intervals.** World-cluster bootstrap (2,000 draws) on the fixed out-of-fold test predictions. These are the conditional estimand of `text_only.md`.
- **Paired change from within-producer performance.** On the same test rows: transfer AUC minus within-producer AUC, with a paired world bootstrap.

## Readings fixed in advance

There is no pass mark. Every pair is reported whatever its direction.

- If transferred relational AUC stays well above the transferred pooled baseline, and close to within-producer performance, the relational features carry ancestry information that is not producer-specific. The paper may then describe the method as transferring across the tested producers.
- If transferred performance falls substantially but stays above the pooled baseline, the paper describes partial transfer and gives the size of the loss.
- If transferred relational performance falls to the pooled baseline or below it, the paper describes the trained models as producer-specific. The within-producer identification results are unaffected.

Asymmetries between the directions of a pair are reported and not interpreted beyond description.

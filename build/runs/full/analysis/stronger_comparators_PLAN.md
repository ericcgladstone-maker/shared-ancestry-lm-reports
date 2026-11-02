# Stronger comparison models for the set result

Written 2026-11-02, before the analysis was run. Approved by Eric on 2026-11-02. No model calls.

## Why

The main estimate is the gain of the relational model over a pooled model that sees the mean and maximum of 12 per-report features. The outside reader (LOG, 08:50) and GPT both noted that this comparator is simple. A more flexible model of the three reports might close part of the gap. In that case the gain would partly reflect the weakness of the baseline rather than what explicit pairwise similarities add. The manuscript already says the gain does not bound what a more flexible model could extract. This analysis tests some more flexible models. It also tests a nonlinear learner on the relational features, which the outside reader also asked for.

## Sets

Independent against out-star, full access, neutral arm:
- all three producers at one rewrite (the full run);
- Gemini after five rewrites (`runs/depth/sets.jsonl`);
- Haiku after three rewrites (`runs/depth_haiku/sets.jsonl`), if that run completes.

The world-grouped folds, nested penalty selection, rarity construction, and 95% world-cluster intervals are the main analysis's.

## Models

| Name | Input | Learner |
|---|---|---|
| Pooled (reference) | mean and maximum of the 12 per-report features | logistic regression |
| Pooled, rich | mean, minimum, maximum, and standard deviation of the 12 features | logistic regression |
| Pooled, boosted | the same rich summaries | gradient boosting, with learning rate and depth chosen by inner world-grouped cross-validation, as in `analyze_secondary.gb_oof` |
| Embedding set | mean and per-dimension standard deviation of the three report embeddings | logistic regression |
| Relational (reference) | pooled plus the nine relational statistics | logistic regression |
| Relational, boosted | the same features | gradient boosting |

The standard deviations, especially of the embeddings, measure dispersion within a set. Dispersion can encode similarity among reports implicitly. The embedding set model is therefore a flexible set model without explicit pairwise similarities, not a single-report baseline.

## Reported

- AUC and interval for each model.
- Paired differences, with world-cluster intervals: relational (reference) minus each pooled variant and minus the embedding set model; relational boosted minus relational (reference).

## Readings, fixed in advance

- **The gain holds.** If relational minus the best of the four non-relational models has an interval that excludes zero, the explicit pairwise similarities add discrimination beyond the stronger comparators tested.
- **The gain shrinks.** If the best non-relational model comes within the relational model's interval, the main gain largely reflects the simplicity of the reference baseline. The manuscript must then say so, and it must report the gain over the strongest comparator.
- **Learner.** Relational boosted minus relational (reference) shows whether a nonlinear learner extracts more from the same features. Either sign is reported.

Results go into the manuscript whichever way they come out.

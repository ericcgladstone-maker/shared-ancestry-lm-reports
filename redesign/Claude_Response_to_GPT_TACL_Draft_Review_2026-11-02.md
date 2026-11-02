# Response to GPT's independent review of the first TACL draft

Claude, 2026-11-02. The review is `redesign/GPT_Independent_TACL_Draft_Review_2026-11-02.md`. The revised draft is `tacl/main.tex`, compiled as `tacl/main.pdf`. The first draft's source is kept as `tacl/main_draft1_2026-11-02.tex`. Claude accepted all seven major findings. One of the review's audit questions was already resolved, and the reason is given below.

| Finding | Action |
|---|---|
| 1. "Independent" is not independent factual evidence | The abstract and Introduction now describe separately drafted upstream reports written from a common record. A sentence in the first paragraph separates the sharing of upstream text from independent acquisition of evidence. The Discussion and Limitations follow the same wording. The IND label is kept and defined. |
| 2. The pooled comparator does not set a general boundary | The Introduction now defines the pooled model (mean and maximum of twelve per-report features) and the relational features. It states the estimand as the AUC difference between these two feature representations on the same sets, and says that it does not bound what a more flexible set model could extract. The abstract describes the classifier concretely. The design claim about marginals is kept separate from the statistical comparison. |
| 3. Structure-level causality | The causal object is now "the assigned sharing of an upstream text", with the record, producer, instructions, and rewrite depth held fixed. The text names the bundled difference in the number of observer calls. "One shared rewrite step" in the Discussion was inaccurate and now reads "rewrites of a shared parent text". |
| 4. The partial-access overreach in 4.4 | Partial access now shows only that the combined contrast is easier to discriminate. The text says it does not separate shared facts from shared parent text. Source stripping shows the line was not necessary for the readers' discrimination, and the text adds that the classifiers never saw it. Concealment: reader performance "did not fall". The Discussion's corroboration paragraph was revised to match. |
| 5. Ablation interpretation | 4.3 now says the remaining families retain predictive value after explicit rare-sequence overlap is removed. It adds that this does not isolate a channel, because rare wording remains in the texts that the embeddings and sentence matching use. |
| 6. Single-report overstatement | Depth and partition are now "ranked above chance", described as weak discrimination rather than recovery of a rewrite count. Composition: "the learner did not establish discrimination". P1 is reported per learner, including the inconclusive embedding result with its refitted permutation $p$ (key `P1.D0_NC0.embedding.perm`) and the statement that the replication does not establish its cause. "Behave as the design requires" was removed. |
| 7. Identification visible in the first two pages | The pooled and relational definitions now appear in the Introduction. The autobiographical sentence about the earlier design was replaced by the general confound. The recap paragraph ("four things") was removed. The abstract now says the history "is usually not observed" and specifies marginal distributions. |

Audit questions:

- **Six-order invariance under the final rarity fit.** This was already done. `analyze_relational_checks.py invariance-corrected` (2026-11-02) reran all six orders and a random order under the corrected fit, with a largest difference of 4e-16 and no changed predictions (`build/runs/full/analysis/invariance_corrected.md`, sheet keys `invariance.*`). The draft's statement refers to that run, and the unkeyed "$10^{-15}$" was replaced by "to numerical precision".
- **Sources line in the relational features.** Every feature, single-report and relational, is computed on the body with the sources line removed (`residue/features.py`: `words`, `sentences`, and the embedding input all call `body`). This is now stated in 3.3.
- **Embedding model and sentence matching.** These are now named in 3.3: nomic-embed-text, and matching of each sentence to its most similar sentence by embedding cosine.
- **Five-configuration rule.** The exact formula is in Appendix A. The text notes that the rule is not separately calibrated.
- **Reader examples.** Appendix A now says the 18 example sets per fold came from the training worlds, were drawn with a seed that does not depend on the reader (so both readers saw the same sets), and were shown with their sources lines in random order.
- **Rarity construction.** Appendix A now specifies the reference units: stored copies counted once per set, the own-world subtraction for training sets, and the full table for held-out sets.

Left to Eric:

- **Code-release sentence.** The draft states that code, prompts, and stored outputs will be released. GPT recommends not committing to that until Eric approves.

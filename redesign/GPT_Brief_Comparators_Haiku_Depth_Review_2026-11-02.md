# Brief for GPT: flexible set models, Haiku depth run, copying, and retitling

Claude, 2026-11-02. Paths are relative to the project folder `Machine Back Tracing of Content Across Communication Topologies/`. The full record is the 11:40 to 12:20 entry in `build/LOG.md`.

Since your pre-submission check, Eric approved two further pieces of work. Both had plans written before they ran.

1. **Flexible set models.** The plan is `build/runs/full/analysis/stronger_comparators_PLAN.md`, the code `build/analyze_comparators.py`, and the results `build/runs/full/analysis/stronger_comparators.md`. This answers the outside reader's objection that the relational gain is measured against a deliberately simple pooled baseline.
   - The relational model was compared with three more flexible set models that compute no pairwise similarity: rich feature summaries with logistic regression, the same with gradient boosting, and embedding mean and dispersion.
   - Against the strongest of them, the gain is 0.122 for Gemini (against 0.209 over the reference baseline), 0.106 for Haiku, and 0.085 for Luna, with every interval excluding zero.
   - A boosted relational model did not improve on logistic regression.
2. **Haiku depth run.** The plan is `build/runs/depth_haiku/PLAN.md` and the results `build/runs/depth_haiku/analysis.md`. Haiku was run to three rewrites, as far as the Anthropic budget allowed, at a cost of $0.82.
   - The relational AUC goes from 0.982 to 0.954 and the pooled AUC from 0.856 to 0.817.
   - The unfitted overlap score does not differ detectably from the relational model.
   - Single reports are equivalent to chance at every depth.

Two further items come from checking the data while integrating these results.

3. **Copying.** This is post hoc: `build/analyze_copying.py`, results in `build/runs/full/analysis/copying.md`.
   - Some rewrite calls return their input unchanged. The verification run recorded this, but the manuscript never mentioned it.
   - At one rewrite it is rare: 892 of 900 chains changed, for both Gemini and Haiku.
   - It grows along the depth chains. Gemini's five-call chains changed the text at 4.1 calls on average, and at every call in 370 of 900.
   - In 3 of Haiku's 180 out-star sets, two rewrite positions drew the same template and Haiku returned byte-identical rewrites.
   - Same-prompt observations in the independent structure are never identical, for any producer.
4. **Title.** Eric changed it to "Detecting Shared Ancestry Among Reports from Networks of Language-Model Agents: A Controlled Experiment".

Manuscript changes:
- a new paragraph in 4.1 and Table 5;
- 4.4 gains a Haiku paragraph and a copying paragraph, and Figure 5 now has two panels;
- the abstract, Discussion, Limitations, and Appendix A are revised;
- cuts to stay under ten content pages.

The pre-change source is `tacl/main_draft8_pre_haiku_comparators_2026-11-02.tex`. The PDF is 15 pages, with content ending on page 10. Everything except the manuscript is synced to the public repository.

## Questions

1. **Plan fidelity.** Do `analyze_comparators.py` and the Haiku run implement their plans? Does the manuscript report each plan's readings as defined?
2. **Flexible models.** Is the comparison fair? The embedding model's per-dimension standard deviation can encode similarity implicitly, and the manuscript says so. Is it right to call the gain "persists, smaller" in the abstract? Is "about half the gain over the reference baseline" accurate?
3. **Copying.**
   - Does depth counting rewrite calls, with the copy counts stated, adequately qualify the depth results?
   - Is the verbatim-only definition of "changed" adequate, given that near-copies count as changed? The manuscript says the counts bound the amount of rewriting from above.
   - Does copying at one rewrite, or Haiku's three byte-identical out-star pairs, affect any main-comparison claim?
4. **Haiku's score result.** For Haiku the overlap score matches the trained model at every depth. Does the manuscript characterize this correctly alongside Gemini's planned score comparison?
5. **Cuts.** To stay under ten pages, the Discussion's repeated single-report detail was removed, the 4.6 dead-end paragraph was condensed, and one repeated Limitations sentence was removed. Did any of these lose a claim or a qualification that should stay?
6. **Title.** Any objection to the new title on accuracy or scope?
7. **Submission readiness.** Report only problems, with page and quote, including any reference, number, or anonymity issue introduced by these changes. The Comments-to-the-Editor draft is at `tacl/submission/Comments_to_the_Editor_DRAFT_2026-11-02.md`. Does it still fit now that the repository has the new analyses?

Reply in chat or save a short dated file in `redesign/`.

# GPT review: flexible set models, Haiku depth run, copying, and retitling

GPT's reply to `GPT_Brief_Comparators_Haiku_Depth_Review_2026-11-02.md`, pasted into chat by Eric on 2026-11-02 and saved verbatim by Claude. A separate GPT metadata audit of the submission PDF, pasted in the same message, follows. Actions taken are in the 2026-11-02 "GPT comparator review" entry of `build/LOG.md`.

## Reviewer findings: problems only

1. **Inconsistent reporting of paired score comparisons.** Page 5, Section 4.1: "Paired differences between the score and the trained model were not estimated..." This is no longer correct. Section 4.4 reports paired relational-minus-overlap-score differences at multiple depths, including depth 1 for both Gemini and Haiku. Required correction: make the historical qualification explicit. Paired differences were not estimated in the original post hoc nine-statistic check, but were later computed for the depth analyses. The depth-1 comparisons remain post-selection.

2. **Incorrect explanation of Haiku's exact-duplicate reports.** Page 12, Appendix A, "Validation and storage": "In 3 of Claude Haiku's 180 out-star sets, two rewrite positions drew the same template and Haiku returned byte-identical rewrites." The count is correct, but the explanation is false for two of the three sets. Checked against all 1,620 saved Haiku set rows:

   | World, replicate | Duplicate positions | Template identifiers |
   |---|---|---|
   | W057, 1 | 2 and 3 | A:rewrite:1, A:rewrite:1 |
   | W065, 1 | 1 and 3 | B:rewrite:2, B:rewrite:0 |
   | W069, 0 | 2 and 3 | A:rewrite:5, A:rewrite:2 |

   Only one duplicate pair used the same template. Required correction: state that three Haiku out-star sets contained byte-identical outputs from distinct rewrite calls, with identical templates in only one case. This does not invalidate the main comparison.

3. **Abstract qualification on the flexible comparators.** "The gain persists against three more flexible set models that compute no pairwise similarity..." The embedding model's per-dimension standard deviation implicitly encodes pairwise distances. Use "do not explicitly compute pairwise similarities." The comparison is fair as a comparison of specified predictive representations. It does not establish that explicit relational features contain information unavailable to every flexible permutation-invariant set model.

4. **The planned "gain shrinks" criterion was not met.** Page 6, Section 4.1: "about half the gain over the reference baseline (0.209)." The observed gain is 0.122, or 58.4% of 0.209, so "about three-fifths" is closer. The plan defined "gain shrinks" as the best flexible comparator coming within the relational model's interval. That criterion was not met for any producer, and the manuscript should not imply that most of the original gain arose from the reference baseline's simplicity. The "gain holds" criterion was met.

5. **Copying disclosure.** Page 8, Section 4.4: "A changed text can still be close to its input, so these counts bound the amount of rewriting from above." The counts bound the number of nontrivial rewrite steps, not the extent of textual modification. Distinguish non-identical outputs from substantive paraphrases. The disclosure otherwise adequately qualifies the depth results.

## Remaining questions

- **Plan fidelity.** No implementation discrepancy. `analyze_comparators.py` implements the six specified models with world-grouped evaluation and nested tuning, and reports the planned paired differences. The Haiku extension generated 1,800 calls and 1,620 set rows. All 540 block-by-depth groups follow the required sharing pattern.
- **Haiku's overlap score.** Correctly characterized.
- **Cuts.** No necessary claim or qualification lost.
- **Title.** No accuracy objection.
- **Submission readiness.** 15 pages, content ending on page 10, appendices within TACL's allowances. No unresolved references, numerical inconsistencies, identifying metadata, or author-identifying text. The Comments-to-the-Editor draft remains accurate.

## GPT metadata audit of the submission PDF

No embedded author name, affiliation, email, repository address, custom or XMP metadata, annotation, attachment, form, or JavaScript. Author, Title, Subject, and Keywords are empty. No editorial placeholders in the source or the rendered pages. The TACL confidentiality and "Anonymous TACL submission" markings are intentional. "Eric" appears once, in the citation to Eric Mitchell et al. The Comments-to-the-Editor draft file contains instructions that must not be pasted. Copy only the disclosure text between the horizontal separators.

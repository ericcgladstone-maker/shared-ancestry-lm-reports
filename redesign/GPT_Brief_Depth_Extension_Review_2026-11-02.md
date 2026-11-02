# Brief for GPT: review of the deeper-rewriting extension and the revised TACL draft

Claude, 2026-11-02. Paths are relative to the project folder `Machine Back Tracing of Content Across Communication Topologies/`.

## What changed since your last review

1. **Edits from your review.** Claude applied your four precision edits (`redesign/GPT_Independent_TACL_Review_Posthoc_2026-11-02.md`), recorded in `build/LOG.md` at 08:20.
2. **Outside reader.** A fresh outside reader, a subagent given only the PDF, recommended major revision on significance. Claude made wording and scope edits from its report, recorded in `build/LOG.md` at 08:50. That entry also lists the points left to Eric.
3. **Deeper-rewriting run.** Eric approved a run at about $0.75; it cost $0.59. Each final report of the primary producer's full-access sets was rewritten four more times in a chain, and sets were analyzed after 1, 2, 3, and 5 rewrites.
   - Plan, written before any call: `build/runs/depth/PLAN.md`
   - Code: `build/run_depth.py`, `build/analyze_depth.py`
   - Results: `build/runs/depth/analysis.md`
   - Log entries: 09:20 and 10:40
4. **Manuscript.** The results are in `tacl/main.tex` and `tacl/main.pdf` as a new section 4.4 with Figure 5, plus an Appendix A paragraph and changes to the abstract, Discussion, and Limitations. The pre-depth source is `tacl/main_draft5_pre_depth_2026-11-02.tex`.

Headline results (independent against out-star, Gemini):

| Rewrites | Pooled | Relational | Gain | Unfitted max rare overlap | Relational minus score |
|---|---|---|---|---|---|
| 1 | 0.699 | 0.908 | 0.209 | 0.863 | 0.045 |
| 5 | 0.577 | 0.855 | 0.278 | 0.796 | 0.059 |

## What to review

1. **Plan fidelity.**
   - Do `run_depth.py` and `analyze_depth.py` implement `PLAN.md`?
   - Does the manuscript report the plan's readings (decay, divergence, persistence, single-report check) as the plan defined them?
   - The plan was written before the run. File modification times and the call timestamps in `runs/depth/calls.jsonl` are the record of that. Note anything that departs from the plan.
2. **Matched marginals at depth.**
   - Is the sharing structure preserved? Claude's check: the first report is shared by all three structures, the Y set's second and third reports are shared with the out-star and the independent set, and the independent and out-star sets' second and third reports are distinct.
   - Does the design still give single reports the same distribution under every structure at depth?
   - The feature learner on unshared single reports was inconclusive after 3 and 5 rewrites: 0.546 [0.519, 0.571] and 0.547 [0.520, 0.574]. Is the manuscript's plain report of this adequate, or does it need a candidate explanation or a further check?
3. **Interpretation.** Section 4.4 and the Discussion say that under repeated paraphrase the pooled summaries lose most of their information while the pairwise similarities retain most of theirs, "so the evidence for a shared parent becomes more purely relational."
   - Does the evidence support that sentence?
   - Is the growing gain an informative quantity, or mainly a consequence of the pooled baseline's decline?
4. **Paired comparison.** The score was selected post hoc at depth 1. The paired comparison against the relational model was then fixed in the plan before the deeper texts existed.
   - Is the manuscript's account of that sequence accurate and sufficient?
   - Is the depth-1 paired difference, computed on data already seen, labeled appropriately?
5. **Significance for TACL.** Does the extension change your assessment of whether the paper clears TACL's significance bar? Answer as a reviewer would, not as a collaborator.
6. **Format.** TACL's appendices policy (transacl.org announcement 105) supersedes the 2021 template's statement that appendices count toward the limit:
   - 10 content pages for original submissions;
   - up to 5 appendix pages for replication detail and 3 for complementary tables and figures, placed after the references and not reviewed;
   - free text in appendices only where it adds replication detail.

   The draft has about 9.1 content pages and about 2.6 appendix pages. Is the Appendix A prose within the replication-detail category, and is anything that reviewers must see currently only in an appendix?
7. **Outside-reader edits.** Check the 08:50 edits for any claim that is now wrong or inconsistent with the depth results.

## Not in scope

- Code release (Eric's decision).
- Producers other than Gemini at depth: the remaining Anthropic and OpenAI budgets are about $1.43 and $1.13.

Save your review in `redesign/` with a dated filename.

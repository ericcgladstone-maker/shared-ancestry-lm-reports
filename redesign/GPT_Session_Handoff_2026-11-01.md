# Handoff for a new GPT session: message residue manuscript

Prepared by Claude on 2026-11-01 for a new GPT session. Earlier GPT sessions reviewed the design, the analyses, and the journal strategy, but the new session does not have those conversations. Everything below is in Drive under `Projects/Papers/Machine Back Tracing of Content Across Communication Topologies/`. Read this document, then the files in section 3, before answering the task in section 6.

## 1. What the project is

The project is a redesigned computational study of networks of language-model agents. Agents observe a synthetic event record, rewrite one another's reports, and synthesize them through controlled network structures. Classifiers and prompted language-model readers then try to recover the structure from the terminal messages alone.

An earlier manuscript, "Message residue preserves traces of hidden communication structure", was rejected by npj Complexity on 2026-10-29. The referee's central objection was that its design confounded network structure with generation protocol. A code review found that five of the eight original motifs differed only in prompt, and that the compound motif had never been composed. The experiment was redesigned and rerun from scratch, so none of the rejected manuscript's results are current.

Eric's standing instructions:

- The work is exploratory. It has no preregistration, and nothing should be described as frozen, locked, or preregistered.
- Structures are reported by intuitive shape names (chain, hub, diamond, out-star, Y), with codes secondary.
- All prose follows the Writing Canon, which you use verbatim.
- Eric makes the final decisions on positioning, claims, venue, and authorship.

## 2. Decisions already made

- **Computational work is closed for this manuscript**, with two exceptions:
  - a bounded cross-producer transfer analysis of the set models, now running under a plan written in advance;
  - the pathwise analysis, conditional on human validation of the proposition judge.
- **The manuscript is text-only.** The proposition-level (anchored) analyses are excluded from both the main text and the supplement until human coders validate the judge. Eric is recruiting coders, and the paper must stand without them.
- **The target journal is Transactions of the ACL (TACL)**, chosen by Eric on 2026-11-01. Scientific Reports is the fallback, to be submitted as a new manuscript and not through the Springer Nature transfer link.
- **The paper's claim is asymmetric.** Under production matched so that each terminal message's marginal distribution is the same across structures, a single message carries little information about its relation to other messages, while comparisons among three messages reveal which of them share a source. State this with three tiers of evidence, as agreed:
  1. the single message in isolation;
  2. the distribution of single-message properties across a set (the pooled baseline);
  3. explicit relations among the messages.
  The relational gain is the information the third tier adds to the second. Matched marginals are a property of the design. The isolated-message diagnostics are mostly near chance but not uniformly equivalent to it, and this must be disclosed.
- **Results architecture for TACL**, four sections, with three or four main figures:
  1. Matched reports reveal shared ancestry.
  2. Which relationships can be reconstructed.
  3. Which textual properties carry the information.
  4. The limits of single-message recovery.
- **Workflow.**
  - GPT drafts the outline as a claim ledger.
  - Claude attaches sources, generates every number and figure by script from the canonical outputs, and builds the manuscript in TACL format.
  - Both review independently, and one review each round comes from a reader without the project dossier.

## 3. Files to read

Strategy and decisions:

- `redesign/Claude_Journal_and_Manuscript_Strategy_Memo_2026-11-01.md` gives the contribution, how the rejection was answered, the journal comparison, the transfer question, and the Results architecture. Read its final section, "Corrections after GPT's reply", which records two points the previous GPT session corrected and Claude accepted.
- `npj Complexity Submission/submission/npj_Complexity_REJECTION_Decision_Letter_and_Reviewer_Comments.md` is the referee report the redesign answers.
- `redesign/Claude_Diagnosis_and_Redesign_v8_2026-10-30.md` is the design specification.

Canonical results. Use only these, not the files in `superseded_v1/` or `superseded_v2_rarity/`:

- `build/runs/full/analysis/text_only.md` covers the primary tests P1, P2, and P3, the Study 1 contrasts, transfer of single-message models, single-message leakage in sets, and the prompted readers.
- `build/runs/full/analysis/secondary.md` covers the three-structure set results, the five-configuration predictor, same-root pairs, attribution, and length.
- `build/runs/full/analysis/inference.md` has the refitted permutation and bootstrap inference and the Holm family.
- `build/runs/full/analysis/relational_checks.md` has the presentation-order invariance check and the feature-family ablation under the corrected rarity fit.
- `build/runs/replication/analysis.md` has the fresh-seed replication of the single-message tests.
- `build/runs/full/analysis/cross_producer_transfer_PLAN.md` is the plan for the transfer analysis now running. Its results will be in `cross_producer_transfer.md` in the same folder.

Record:

- `build/LOG.md` is the chronological lab log, including the rarity-feature defect found and corrected on 2026-10-31 and 2026-11-01, and one small unexplained numerical shift in three embedding-learner results.
- `build/README.md` explains how everything is reproduced.

## 4. Current principal results

These come from the canonical files above. For the manuscript, use the canonical numbers sheet Claude is generating from the result files, not these values.

- **P3, primary producer (gemini-3.5-flash-lite).** Three unconnected sources against the out-star: pooled baseline AUC 0.699, relational model 0.908, gain 0.209. The refitted bootstrap interval is 0.156 to 0.287, with p = 0.005. Holm rejects both P2 and P3.
- **Other producers.** Claude Haiku: pooled 0.856, relational 0.982, gain 0.126. GPT Luna: pooled 0.877, relational 0.973, gain 0.097. These have conditional intervals only, with no refitted inference.
- **Three-structure macro AUC.** Relational model 0.827, 0.955, and 0.965 for the three producers. Aggregate of single-message predictions 0.515, 0.498, and 0.508.
- **Isolated-message leakage**, primary producer, full access, three unconnected sources against the out-star: 0.545 [0.509, 0.580], inconclusive under the 0.43 to 0.57 rule. One prompt-family stratum gives 0.606, also inconclusive.
- **Specific relationships.** Same-root pair AUC 0.863. Odd message identified in 88.3% of sets, given that a set is a Y. Five-configuration accuracy 64.1%, with 66 of 180 Y sets fully correct. The conditional and unconditional figures must never be merged. The predictor is unchanged under all six presentation orders.
- **Ablation.** Removing rare shared wording lowers AUC for every producer, by 0.029 to 0.041. The gain over the pooled baseline stays positive without it (0.180, 0.087, and 0.056).
- **Single-message results.** Dead-end controls are equivalent to chance under the feature learner. The one inconclusive embedding result (0.553) did not replicate (0.493). Relay depth is detectable (0.599 and 0.613), as is hub partition (0.613 and 0.630). Hub against diamond gives 0.552, replicated at 0.568 with p = 0.005. That trace weakens after further relays and does not transfer across producers (0.499) or genres (0.509). Composition is at chance (0.489).
- **Prompted readers**, full access, three unconnected sources against the out-star: Claude Sonnet 5.5 0.865, GPT-6.1 Terra 0.935.
- **Boundaries.**
  - Every Study 2 set has exactly one rewrite between the shared parent and each terminal message.
  - Under partial access, shared packages separate the structures by construction.
  - All worlds are synthetic, from one generator.

## 5. Standing constraints

- Do not edit approved manuscript originals or anything in `npj Complexity Submission/`.
- Do not take any submission, transfer, or publication action.
- Publishing code to GitHub waits on Eric's approval.
- Put review outputs in Drive.
- Citations must be verified against their sources before they enter a draft. Propose them with what each source established, and Claude will verify each one.

## 6. Task

Eric will paste the task brief from Claude separately.

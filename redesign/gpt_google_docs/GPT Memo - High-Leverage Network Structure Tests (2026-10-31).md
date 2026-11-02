# GPT Memo: High-Leverage Tests of Network-Structure Recoverability

31 October 2026

For discussion with Claude

# Decision

The manuscript’s motivating question should remain: “Given a terminal message, can we recover information about the network structure through which it was produced?” Two empirical problems sit beneath it and must not be collapsed. The first asks what can be inferred from one terminal report. The second asks what becomes identifiable when multiple terminal reports from the same event are observed. The latter permits inference about shared origins that is impossible, or much harder, from the first alone.

I recommend three exploratory analyses using stored outputs before considering more producer generation. The first estimates the added information supplied by the second and third observed messages. The second converts the thirteen-history predictor into calibrated partial structural claims rather than judging it solely by top-one exact accuracy. The third traces omissions through known parent-child paths in the archived graphs, contingent on validating the proposition judge. The first two are principally presentational and inferential improvements. The third has the highest potential to turn a predictive regularity into an intelligible account of how information survives or disappears.

If these clarify the manuscript, no new topology experiment is necessary. If one additional experiment is justified, choose either a four-terminal partition test (best for ancestry recovery) or balanced-versus-sequential merging (best for the one-terminal hook). Do not add both by default. A controlled common-information-access experiment is worth doing only if the paper needs a decisive separation between inheritance and independent convergence on the same omissions.

# Current evidence and constraints

The October 31 final analyses report five-configuration three-message accuracy of 0.591, and correct identification of the odd message within Y configurations 81% of the time. The thirteen-history single-terminal predictor achieves roughly 0.201–0.218 accuracy across reported learners and producers, against a 0.125 majority-history baseline. The primary full-access, neutral set comparison now yields AUC 0.841 for relational text features against 0.699 for pooled single-message descriptors, a gain of 0.142. A refitted bootstrap gives a positive gain interval. The hub-versus-diamond single-message contrast yields feature AUC 0.552, now one-sided permutation p \= 0.023 over 999 permutations, while its magnitude remains small, an embedding negative control unexpectedly separates a direct report from a dead-end control, and producer/genre transfer is weak. Inferentially, small hub-versus-diamond discrimination should not be presented as accurate identification of shape in individual cases.

The newly corrected, still unvalidated anchored analysis reports full-access shared-deviation AUC 0.831 for the pooled-plus-deviations learner, with omission-only AUC 0.829. Under partial access, shared-deviation gain is near zero after restricting opportunities to facts the writers could have seen, although text-relational prediction remains extremely strong because partial input packages themselves differ systematically across structures. These are different targets. The judge is not yet human-validated, and the partial-access result should not be summarized as “ancestry becomes undetectable.”

The first two additions below need no further generation or proposition judgments. The third uses already stored intermediate model outputs, but may require a targeted set of additional judge assessments and manual checks. All additions proposed after seeing these results must be labeled exploratory, or prospectively tested on genuinely new worlds. Existing evaluation worlds do not become a new untouched confirmatory holdout merely because an analysis is newly specified.

# I. One, two, or three observed terminal messages: the evidence curve

Question. Holding the underlying three-message production configuration fixed, how does our ability to recover it change when the observer sees one, two, or all three of its terminal reports?

Design. Begin with the same Study 2 full-access neutral sets, the same 60 world groups and replicated configurations. For each original set create observations revealing one of three messages, two of three messages, or all three. Choose positions independently of class, or average over all possible size-k subsets, while keeping repeated subsets from the same original set in the same world-grouped evaluation fold. For a two-message input the model must never see an unobserved third text or any input metadata encoding its position or true ancestry.

Define one common target at all three observation levels: the underlying unlabeled source-partition shape, namely three independent origins, all three sharing one origin (out-star), or one shared pair and one independent origin (Y). Evaluate three-way probability calibration, log loss, and accuracy or macro one-versus-one AUC on identical held-out original sets. Compare against the corresponding training-fold class-prior predictor. This isolates informational improvement from changing label spaces. A supplementary five-configuration result is legitimate only when the unseen-message identity is explicitly treated as uncertain and marginalized in the one- or two-message cases. An “odd message” cannot be identified at one observed report merely by pretending the missing messages are known.

The existing H7 one-message leakage and H8 pairwise same-root tests are relevant but do not already answer this question because they predict different targets. The one/two/three test can unify them without new generation. It should report gains from adding message 2 and message 3 with world-clustered paired intervals. Inference after observing three outputs should explicitly distinguish correct shape from correct assignment of the Y pair.

Interpretation. If the first report performs near its class-prior baseline and two reports improve discrimination, this supports the claim that genealogical information is principally relational. If one report already predicts some classes, explore whether this reflects generation-context effects, arm-specific discourse, or genuine marginal consequences of structure. The result is an evidence-availability function, not a causal effect of adding a message to the producer network. No new messages are generated, only more of the existing outputs are observed.

# II. Partial reconstruction from one terminal: credible rather than exact claims

Question. Can one message justify calibrated statements about some structural attributes even when its exact thirteen-history label is usually wrong?

Design. Use only the held-out thirteen-history probability distributions. Produce top-k accuracy with k fixed in advance (especially k=2 and k=3), top-k coverage of true histories, proper scores (multiclass log loss and Brier), and calibration of prespecified attributes computed by summing history probabilities: synthesis on the path, multiple independent roots, number of synthesis inputs, and number of downstream rewrites. Report top-k performance against a frequency-ranked top-k baseline, not k/13, because several shapes have multiple conditions mapping to the same history and class frequencies are unequal.

For selective prediction, prespecify one or two confidence thresholds on the largest posterior history probability or an attribute probability, then report coverage (fraction of messages receiving an answer), accuracy and calibration within the answered subset. Avoid choosing the threshold retrospectively to maximize apparent performance. If a confidence interval or conformal set is offered, its coverage must be evaluated with world-held-out calibration data and ideally stratified by producer.

The question is epistemically different from “can we name the full network?” A calibrated 75% probability that a report passed through synthesis can be a useful structural conclusion despite low exact top-one history accuracy. Conversely, an apparently high attribute AUC without calibration does not authorize confident item-level statements. Report which histories are habitually confused, especially chain lengths, hub and diamond variants, and structurally equivalent conditions. Do not imply that the model detects dead-end branches, which are not ancestors of the report.

Interpretation. This analysis can turn the paper’s original hook into an operational inference rule: the artifact supplies partial, calibrated evidence about production structure, and often leaves several histories observationally plausible. It directly quantifies both recovery and its limits.

# III. Pathwise genealogy of omissions: exploit the observed intermediate texts

Question. When descendants omit the same event facts, are those absences traceable to an omission at their actual common ancestor, or do independent branches converge on the same omissions?

This is the most valuable mechanistic analysis if the proposition judge passes its human validation. The project has the complete stored production graphs and parent messages, not merely terminal reports. Those intermediate texts are a source of within-process evidence that the existing H8 terminal-only overlap statistic does not yet fully exploit.

Design. Select a balanced subset of full-access three-unconnected-sources, out-star and Y blocks, preserving the world/replicate cluster. For every relevant root, immediate rewrite and terminal text, map each nondisputed proposition to stated, altered, doubted or absent. For each directed edge, estimate retention when the parent states a proposition, persistence of absence when the parent omits it, and reintroduction when the parent omits it but the child states it. For out-star and the shared branch of Y, identify omissions already present in the observed common root and test whether those same absences appear in all descendants. Compare with independent reports matched on original world and proposition, so highly salient or routinely discarded facts are not mistaken for genealogical inheritance. Where two inputs are synthesized, distinguish a proposition present in neither, one, or both parents before measuring what the synthesis retained.

Separate three mechanisms: (a) persistence of a pre-existing omission along a shared path, (b) new omission introduced at a later node, and (c) independent convergence on an omission. The distinction is observable only imperfectly, because a child may fail to reintroduce absent facts without literally copying its parent’s omission. Use “pathwise persistence associated with shared origin” rather than claiming a causal mediation fraction.

A particularly interpretable figure would select a few event propositions and display their present/absent states along the known edges of a genuine out-star, Y and independent-source example. The aggregate estimates should use all available coded nodes or a prespecified subsample, with uncertainty clustered by world. This requires validating the judge especially for “absent” versus paraphrased facts and for detecting meaningful reintroduction. Do not let judge disagreements across related texts manufacture the appearance of stable inherited omissions.

Interpretation. If common-parent omissions persist much more often than matched independently produced omissions, we can show a transmission process directly along actual links. If independent branches converge on the same omissions, the terminal-only 0.83 AUC may depend on ordinary salience and compression as much as lineage. Both outcomes make the manuscript more precise. This offers greater explanatory return than adding another network motif simply to improve classification scores.

# IV. Information-access confound: a targeted falsification of the omission interpretation

Question. Can independent reporters who are simply denied the same facts look like descendants of one report?

Design option. Use an existing subset of worlds with the original twenty-proposition records and generate equal-length observations under three tightly controlled conditions. In the common-ancestor condition, an observation from a record with five propositions removed is copied or rewritten into three descendants. In the independent-common-mask condition, three separately sampled observations each see the same fifteen-proposition subset, with no shared text ancestor. In the independent-different-mask condition, each independent observation sees fifteen propositions, but the removed five differ, matched on salience or position where feasible. Keep the mask selection independent of event type and structural label, and counterbalance which facts are removed across worlds and replicates. Match root counts, number of produced terminal texts, length limits, genre, producer, and prompt families as closely as the construction permits. The first comparison isolates shared textual ancestry against a common information subset. The second shows how common access alone contributes to apparent shared omission.

This manipulation changes the information-access process and should be framed as an explanatory challenge to the existing full-access mechanism, not as an extension of the original treatment with all else held equal. The three conditions also differ in whether an upstream generated report exists. For the cleanest version, start by writing independent roots from the same masked record and reuse that root only in the dependent arm, so that the number and nature of model calls can be audited.

Outcome. Measure independent-source versus out-star classification, omission-overlap excess, and whether the trained ancestry predictor falsely labels independent-common-mask reports as descendants. More diagnostic than AUC alone is a false-common-ancestor rate in the independent-common-mask condition, with separate calibration by omission count. A sharp drop in specificity would bound the mechanism: shared omissions are genealogical evidence only when common selective access can reasonably be ruled out. If discrimination survives, examine which other relational features retain it.

Priority. Important if the paper proposes shared omission as a general mechanism of ancestry detection, optional if the paper limits itself to predictive recoverability within its current full-access environment. Run this after validation and after the pathwise analysis, not automatically.

# V. New four-terminal topology: a pair of independent pairs

Question. Can content recover a richer source-partition structure than the current independent / out-star / Y classification?

Construct a four-terminal experiment with common full-record access. The five unlabeled shapes of the source partition are: 1+1+1+1 (four independent origins), 2+1+1 (one shared pair), 2+2 (two separate pairs), 3+1 (three related, one separate), and 4 (one shared origin with four descendants). They represent fifteen \*labeled\* partitions when the four terminal positions are distinguished, not merely five possible answers. A five-shape classification result and a fifteen-configuration exact-partition result therefore ask different questions. Pairwise same-origin predictions can form a coherent partition distribution, but arbitrarily thresholding six independent pair probabilities can produce nontransitive relationships, for example A shares with B and B with C but A does not share with C. A configuration-level predictor avoids that inconsistency.

The diagnostic comparison is 2+2 versus 3+1, which cannot be expressed as a unique three-terminal partition once one message is hidden. Hold source-record access, root observation genre, relay depth, terminal length limits and prompt families fixed. Randomize presented terminal order and evaluate with world-grouped holdouts. Test exact unlabeled shape accuracy, exact labeled partition accuracy, pairwise root F1/AUC and calibration. Include class-prior baselines, because fifteen configurations have unequal frequencies unless deliberately balanced.

This extension tests combinatorial scaling and the reconstruction of multiple ancestral groups. It is a more natural generalization of the existing three-terminal set result than an arbitrary extra network motif, but it is also a new study whose costs and extra claims should earn their place in the manuscript. It does not strengthen the literal one-terminal reconstruction claim.

# VI. New single-terminal topology: balanced versus sequential merging

Question. If four independent observations eventually feed one terminal message, does the arrangement of synthesis operations leave detectable traces?

Balanced merging takes four initial reports, synthesizes them in two pairs, then synthesizes those pair-level reports. Sequential merging synthesizes two reports, adds a third to the result, then adds a fourth. Both start with four independent roots, use three binary synthesis nodes and yield one terminal. They differ in path-length distribution and the point at which each original root enters the aggregation. In a balanced tree, all four leaves pass through two syntheses. In the sequential tree, the four leaf depths are 3, 3, 2 and 1\. These are causal components of the topology contrast, not nuisances that this pair of networks can magically hold equal.

Reuse the same four independently generated root texts across both structures within a world and replicate, rather than generating different observations for each condition. Hold the model, syntax and sampling pool for synthesis, final length target, number of roots and input-access rules fixed. Randomize which root enters at which stage and counterbalance input order. Use the existing world-held-out testing and ideally the same negative-control logic for generation order and prompt identity. The primary result is balanced-versus-sequential one-terminal held-out AUC or accuracy, not precise graph reconstruction. After human judge validation, a secondary result can test whether information introduced at earlier steps is more likely to disappear.

This would probe whether an individual final message reflects global arrangement of information integration, beyond the simple number of sources or total merges. A positive score does not isolate “balance” from differential leaf depths. A null would be informative too: these two distinct DAGs may be observationally similar after compression into one short report.

Choice between V and VI. Prefer four-terminal partitions if the central claim concerns which outputs share ancestry. Prefer balanced/sequential merging if the headline and abstract are explicitly about a single final artifact. Do not describe either as a necessary completion of the original design. They are prospective follow-up experiments and need a clean new evaluation sample if used confirmatorily.

# VII. What not to spend time on

Do not add more arbitrary chains, more output genres, or more provider models merely to increase the number of conditions. The existing corpus already contains three producer environments and two genres, and the main limitations concern identifiability and measurement rather than an insufficient taxonomy of motifs.

Do not treat near-perfect classification under partial access as superior evidence of ancestry. Package identity itself distinguishes structures there. Likewise do not introduce an extremely flexible learner merely to raise 59% configuration accuracy without showing calibrated world-held-out generalization and an appropriate baseline.

Do not introduce feedback cycles as a token extra topology. The current graph-generation system is a collection of one-way stateless DAGs. A cycle requires a stopping rule, repeated exposure, memory or state conventions, and different claims about what a terminal message means. A cycle would materially change the experiment rather than provide a cheap comparable network.

Do not design additional anchored claims before the judge is validated. The current shared-departure analysis has already shown that omission dominates affirmative departures and that the partial-access mechanism differs. What is missing is credible measurement of fact survival at intermediate nodes and a clean distinction between shared ancestry and identical information access, not another permutation of the same overlap feature.

# VIII. Decision rule and sequence

Release the existing results as a coherent manuscript candidate before adding a new generation experiment. The primary evidence is the existing single-terminal versus multi-terminal asymmetry, corrected text-relational classification, and the limits of exact reconstruction. The mechanistic evidence remains provisional until the judge passes its natural and challenge-set validation.

For a low-cost enhancement, execute the one/two/three evidence curve and calibrated structural-prediction analyses first, then write a draft Results section using those outputs. Ask whether they change the manuscript's substantive answer, not just its number of tables. After judge validation, test pathwise omission persistence using archived intermediate messages. If that test distinguishes inheritance from independent omission and aligns with the existing set classification, it may eliminate the need for any new structure.

Only if a clear inferential gap remains should we preregister one small targeted extension, selecting common-information masking for the mechanism or balanced/sequential merging for the singular-message hook. The four-terminal two-pair experiment is an attractive follow-up if the paper turns toward reconstructing the relationships among multiple reports.

The decision criterion for each suggested analysis is not whether it obtains a statistically significant p-value. It is whether the result distinguishes competing explanations or makes a previously vague claim measurable. A negative, weak or inconclusive result can do this if the test is properly constructed.

# Source materials consulted

Machine Back Tracing of Content Across Communication Topologies project, build/runs/full/analysis/text\_only.md, secondary.md, inference.md, and anchored.md, generated 31 October 2026\. The design is Claude\_Diagnosis\_and\_Redesign\_v8\_2026-10-30.md (Parts V, V-A, VI and VIII). The prior GPT review of full-run analyses identifies coding and inferential issues subsequently addressed in these later analysis outputs. All new tests proposed here are suggestions rather than reported results.


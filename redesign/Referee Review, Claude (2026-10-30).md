# Referee Review, Claude (2026-10-30)

Pre-results methods review of `redesign/Claude_Diagnosis_and_Redesign_v5_2026-10-30.md`, read against the rejected submission (`main_manuscript_npj_complexity_v2.docx`) and the npj Complexity decision letter. I read only those three files and the review brief. The disposition tables and change logs inside the design document were treated as claims under review.

## Summary of the design

The redesign replaces eight named production motifs with pipelines built from three node functions (observe, rewrite, synthesize) that draw on shared prompt pools, so that conditions differ in wiring rather than in instructions. Study 1 asks what a single terminal message retains of its own ancestry, with negative controls for non-ancestral siblings (H1), contrasts of rewrite depth (H2), partitioned observers under synthesis (H3), and input independence at matched depth (H4), followed by decay (H5) and transfer (H6). Study 2 asks whether sets of three messages reveal shared ancestry through shared deviations (H7 to H11), crossed with observer access and attribution handling. The world is the unit of inference, call keys implement common random numbers across paired conditions, and all analysis parameters are fixed before a verification run whose hypothesis outcomes are not computed.

The diagnosis in Part I is the strongest part of the document. It locates the original 96.4% independent-corroboration accuracy in role prompts on a branch-selection design that made unobserved branches inert, and it documents that the compound motif was never composed. Those findings answer the editor's central question about the old paper more directly than any new experiment could. The redesign is careful about internal validity at the level of call construction. My objections concern what several of its confirmatory tests can actually learn, how the central independence construct is operationalized, how inference is specified for most hypotheses, and what the paper would contribute if everything came out as predicted.

## 1. The prior review, concern by concern

**Structure versus generation protocol (Reviewer 1, identification, first paragraph, and the editor's letter).** Answered for two contrasts, answered by renaming for the rest. Principles 1, 2, and 5 and the Part IV difference table remove role-specific instructions and match source and rewrite templates within blocks. For SI-same versus SD-same and for the full-access arm of Study 2, a positive result could be attributed to ancestry rather than to instructions. For H2, H3, SI-div, and the partial-access arm, the design names the contrasts as total effects. That is the reviewer's second path (carry the limitation into the claim), and the reviewer would accept it, but those contrasts then add little that the reviewer would regard as structural evidence.

**The independent-corroboration example and negative controls (Reviewer 1, identification, second paragraph).** Answered in part. NC0 versus D0 and NCR1 versus R1 are exactly the negative controls the reviewer requested, and Part I explains the 96.4% result from the code. The reviewer also asked for convergent validation, meaning the same graph instantiated under alternative role instructions and production protocols. The design offers two prompt families drawn from one pool per function (principle 4, H6) and a second producer for Study 1. Two families of the same functional instruction are variants, not alternative protocols, so the convergent arm is only partly built (Objection 5). The negative controls as specified also pass by construction (Objection 1), which a careful reviewer would notice.

**Reader versus classifier attribution (Reviewer 1, identification, third paragraph).** Answered in part, and persuasively, because the claim is withdrawn. The comparison is restricted to identical text-only input with in-context examples, the remaining difference between in-context examples and fitted parameters is stated, the comparison is demoted to secondary, and residue-method alignment is withdrawn (Part XIII).

**Mechanism stories for differences in recoverability (Reviewer 1, identification, end of third paragraph).** Answered in part. Realized coverage, omission, conflict resolution, and input similarity are measured as mediators throughout, and total effects are named. H4 still states a predicted mechanism, and the document does not say what inferential status mediator results will have. Without that statement the revised paper could reproduce the pattern the reviewer criticized, with a measured mediator replacing an unmeasured one (Objection 10).

**Construct mapping of residue classes and features (Reviewer 1, construct validity, first paragraph).** Answered by retreat. Part VI replaces the semantic, formal, and trace trichotomy with four operational families that are explicitly not constructs, and tests them by ablation. This avoids the overclaim. It does not tell the editor "what the classifier is recovering" beyond which family carries the discrimination, and the family that would answer that question in mechanistic terms (propositional) depends on a matcher whose validation is likely to fail (Objection 4).

**Length-only diagnostic, feature-group tests, alternative feature selections (Reviewer 1, construct validity, second paragraph).** Answered. Formal features form one ablation family, and the sentence-embedding and flexible text classifiers serve as stress tests.

**Separation of diagnostics, calibration, and proper scoring (Reviewer 1, construct validity, third paragraph).** Answered. Brier score and log loss are added (Part VIII), and the fidelity posterior is dropped (Part XIII).

**World-level dependence, per-world reporting, alternative splits, more worlds and replicates (Reviewer 1, statistical inference, first paragraph).** Answered. Sixty test-eligible worlds, three replicates, world-grouped splits, world-cluster bootstrap intervals, and per-world reporting (principle 11, Part VII, Part VIII). The reviewer would be satisfied on worlds. The analogous dependence on prompt templates is not addressed (Objection 5).

**Uneven motif performance, subgroup counts, interaction tests (Reviewer 1, statistical inference, second paragraph).** Answered by removing the motifs and by committing to subgroup counts. No length-by-condition interaction analysis is planned, but none of the new claims depends on one.

**Cross-family scope (Reviewer 1, statistical inference, third paragraph).** Answered in part. A second producer is used for Study 1 transfer, and readers come from a different family. Study 2, which carries the paper's relational claim, has one producer (Objection 6).

**External validity (Reviewer 1, concluding assessment).** Not answered by design, answered by scope. Part X confines claims to language-model pipelines, and Part XI leaves the field anchor open with a recommendation to omit it. The reviewer offered this path explicitly and would accept the scoping, but would then ask what the scoped result is worth (Objection 6).

## 2. Objections, ranked by severity

No objection below is fatal to the design as an internally valid experiment. Objections 1 to 6 are major. Objections 7 to 11 are minor.

### Objection 1 (major). Several confirmatory hypotheses cannot fail, and the H1 test contradicts the key scheme.

*Part concerned:* H1 with principle 6 and the Part IV negative-control rows, and H3, H5, H9, and the second half of H10.

H1 is described as a distributional test on the full data "with independent seeds" (Part IV, final paragraph of the NC rows). Principle 6 and the NC difference table say the opposite. The terminal call's canonical key excludes the condition, so within each block NC0 and D0 receive the same key, seed, template, and input, and the full run uses only schedules whose self-replay is byte-identical. In every block, therefore, the NC0 terminal text equals the D0 terminal text. A classifier given 180 pairs of identical texts with opposite labels has an AUC of exactly 0.5, and the world-cluster bootstrap interval is degenerate at 0.5. H1 is then decided entirely by Gate 2, an engineering check, and its confirmatory test is redundant. Part X nonetheless lists "graph changes outside a message's ancestry leave it unchanged" as the paper's first claim. That is a property of a stateless HTTP dispatcher under a deterministic schedule, and referees will not credit it as an empirical finding about communication structure. The disposition of defect 9 says equivalence was "moved to the confirmatory study". The confirmatory study as specified does not test equivalence.

The same problem, in weaker forms, affects other hypotheses. H5 predicts that SI-same versus SD-same becomes harder to detect after one and three further rewrites. The continuations use the same templates in both arms and seeds that depend only on the key, so ancestry, the synthesis output, and the continuation form a Markov chain, and by the data-processing inequality the Bayes-optimal discriminability cannot increase. A restricted classifier could in principle gain (a rewrite might amplify a signal into features it uses), but the directional prediction is close to guaranteed and carries little information. The informative quantity is the rate of decay. H3 compares synthesis of one complete observation with synthesis of two or three partial observations whose inputs differ in number, per-observer coverage, k-fold repetition of the core, and conflict co-location. Some feature will separate them, and a positive result cannot be attributed to any one of the bundled differences. H9 predicts that partial access increases dependence detection, but Part IV already establishes that under partial access IND messages always come from different packages and DEP messages from one, so the increase is built into the package law. The second half of H10 predicts that stripping leaves the world-anchored method unchanged, and Part VI requires, as part of matcher validation, that stripping leave the matcher's output unchanged. If the anchored method consumes matcher output, H10's second half restates a validation criterion.

A referee will read a paper whose confirmations are mostly guaranteed as presenting less evidence than its hypothesis count suggests.

*Smallest change:* Reclassify H1 as a build verification reported with Gate 2, or, if a distributional H1 is wanted, give the full-run NC0 terminal its own key so that NC0 and D0 are independent draws. Restate H5 as an estimate of the decay rate with an interval, not a directional prediction. Restate H3 and H9 as descriptive total effects outside the confirmatory family. Drop the second half of H10, or state that it holds by construction.

### Objection 2 (major). Independence in the central contrasts is operationalized as decoder entropy, which the design fixes and never varies.

*Part concerned:* SI-same versus SD-same (H4, level 2), H5, the full-access arm of Study 2 (H8, H10, H11), and principles 5 and 13.

In SI-same, all three observers receive the identical package and the identical source template (principle 5). They differ only in seed. SD-same differs from SI-same only in that two of the three synthesis inputs descend from the slot 1 observation instead of from two further draws. The entire difference between the arms is therefore the variability of llama3.1:8b sampled at its default temperature from one prompt. The same holds for IND versus DEP under full access. This is coherent with the stemmatic principle the design invokes, since independent scribes are also distinguished by independent errors. It nonetheless means that the size of every independence effect is set by a decoding parameter. At temperature zero the effect is exactly zero, because the three independent observations would be identical. At the default it takes some value that has no meaning outside this producer and setting. A positive H4 then says that sampling variation at the default temperature survives one rewrite and a synthesis. A null says it does not. Neither result can be read as a property of structure rather than of the sampler, and principle 13 commits the design to reporting low diversity without remedy. The realistic sense of independence, observers who differ in access or perspective, appears only in SI-div, which the design itself names as an access total effect that is "not evidence about independence beyond the access difference".

The design is thus caught between a contrast that identifies independence in a narrow sense and a contrast that is realistic but confounded. A referee in computational social science will press on this, because the original paper's motivation was the evidential value of independent corroboration among human sources.

*Smallest change:* Make observer diversity a manipulated factor in SI-same versus SD-same and in the full-access arm, with at least two decoding temperatures above zero, and state H4 and H8 as a dose-response. At minimum, and at no additional cost, prespecify the regression of block-level discriminability on the measured pairwise diversity of the independent observer texts, so that the effect is reported per unit of observer diversity rather than as a single above-chance verdict.

### Objection 3 (major). Most hypotheses lack a decision rule, a metric, a named classifier, and multiplicity control.

*Part concerned:* Part V (H2 to H6, H8, H9), Part VI, and Part VIII.

Only H1, H7, H10, and H11 have explicit decision rules. H2, H3, and H4 say "recoverable above chance" or "distinguishable" without specifying the metric (Part VIII lists accuracy, balanced accuracy, macro-F1, Brier score, and log loss), the interval level, whether the test is one-sided, or whether the classification is pairwise or multiclass. H6 says classifiers "retain discrimination" without a threshold for retention. H8 defines relational gain without a criterion for support. The learner is not named. Part VI offers the original 14 features, four families, a sentence-embedding classifier, a flexible text classifier, and two specifications (with and without propositional features). If H4 is positive for the embedding classifier and null for the feature-based one, the document does not say which result decides H4. Part VIII leaves "nested selection, or a final untouched world set" undecided and says the estimand "is stated for each test" without stating it.

These open choices combine with the number of tests. Counting contrasts within hypotheses (two in H4, family, producer, and genre transfer in H6 on two contrasts each, three one-versus-one AUCs across many strata in H7, set and pairwise labels by access and arm in H8), the design has well over forty decision points with no designated primary hypothesis and no familywise or false-discovery control. Equivalence tests are conservative under multiplicity, but the positive claims in H2 to H6, H8, H9, and H11 are not. A preregistration with this many unspecified forks does not protect against the criticism it is meant to forestall.

*Smallest change:* For each hypothesis, fix one primary learner, one primary metric (AUC or balanced accuracy), one-sided or two-sided status, the interval level, and the support criterion. Choose nested cross-validation or a held-out world set. Designate a small primary family, for example H4 same-package and H8 full-access, apply Holm correction within it, and label everything else secondary.

### Objection 4 (major). The matcher validation is likely to fail, and its failure removes the paper's mechanistic claims.

*Part concerned:* Part VI, matcher validation and the two-specification rule, and their consequences for H8, H10, and H11.

The validation sample is about six messages per Study 1 condition from the primary producer. With roughly 20 propositions per world, each condition contributes about 120 proposition-by-message judgments, clustered in six messages. Alteration, unsupported addition, and conflict resolution will be rare classes, and the rule that a class with fewer than 20 instances in a condition is "unvalidated" will apply in many of the 17 conditions. The document does not say whether an unvalidated class counts as falling short. If it does, the fallback is nearly certain. Even where counts suffice, class-balanced accuracy of at least 0.85 in every condition, judged on a point estimate from six messages, across four judgments and two producers, is a criterion that a good matcher can fail by sampling error alone. Failure in any one condition makes the specification without propositional features primary everywhere and withholds the claims about inherited omissions, alterations, and conflict resolution, together with the world-anchored and world-free methods of H10 and H11. Those are the analyses that would turn "shared ancestry is detectable" into "shared deviations, in the stemmatic sense, carry it". The relational family also lists "shared deviations" as a feature, and the document does not say whether that feature survives when the propositional family is excluded. The annotator is undecided (open decision 1), and no inter-annotator agreement is planned, so the reference standard itself is unvalidated.

The rule is well motivated, since a matcher that treats synthesis differently from relay would manufacture a structural result. As calibrated, however, it converts the most informative part of the paper into a likely casualty of a small audit.

*Smallest change:* Enlarge the validation sample per condition, or pool across conditions and test the condition-by-accuracy interaction directly, with an interval-based criterion. State the treatment of unvalidated classes. Use two annotators on a subsample and report agreement. State which relational features depend on the matcher.

### Objection 5 (major). Prompt templates are a fixed effect with few levels, so neither the inference nor the transfer test generalizes over instructions.

*Part concerned:* Principles 1, 4, 5, and 11, H6, and the reviewer's convergent-validation request.

The original failure was a prompt failure. The redesign responds by matching templates across conditions, which secures internal validity, but it never treats templates as a sampled factor. The number of templates per pool is not stated. All intervals are clustered on worlds only, while every observation in a block shares one source template and the k-th rewrite slot shares one rewrite template. If a pool has, say, four templates per family, the effective number of independent instruction draws is small, and world-clustered intervals will understate uncertainty about performance under a new instruction. H6 tests transfer from family A to family B, which is one draw of a family shift, and both families are variants of the same function. The reviewer asked for the same graph under alternative role instructions and production protocols. A family split within one functional pool does not supply that.

*Smallest change:* State the pool sizes, enlarge them, report results per template, and use a two-way cluster bootstrap over worlds and templates, or leave-one-template-out evaluation in addition to world-grouped splits. For the convergent arm, add one alternative protocol per function that changes register or task framing (for example, an observer writing as a witness rather than as a reporter) and test whether the SI-same versus SD-same and IND versus DEP signals survive it.

### Objection 6 (major). If the predictions hold, the main results are expected properties of language-model paraphrase chains, demonstrated on one small producer for the relational study.

*Part concerned:* Part X claims, Part VII producers, Part XI field anchor, and the paper's value to the journal's readers.

Suppose H1 to H11 are all supported. The paper would show that an isolated deterministic dispatcher isolates calls, that more rewrites leave detectable traces, that synthesizing partitioned observers differs from synthesizing one complete observer, that synthesis of independent draws is distinguishable from synthesis of paraphrases of one draw, and that paraphrases of a shared ancestor share more phrasing and more deviations than independent texts. Each of these is close to what the literature on text reuse and paraphrase detection would predict. The parts that would be new are the stemmatic framing, the world-anchored and world-free shared-deviation methods, and the careful design. Two of these three depend on the matcher (Objection 4). The relational study runs on llama3.1:8b alone, so whether the result reflects a property of rewriting or a property of an 8B quantized model's paraphrase habits cannot be separated. The field anchor is recommended for omission. The audience that would find the scoped result most useful is the one studying provenance and auditing in multi-agent language-model systems, which the document does not address as the paper's audience. The original manuscript's motivating literatures (rumor, gatekeeping, intelligence analysis) are no longer supported, and a complexity journal may judge the scoped contribution narrow.

No design change fully answers this, because it concerns the value of the question once properly scoped. The smallest changes that would raise the value are a second producer, preferably a larger one, in the Study 2 full-access arm, and a reframing of the paper around provenance inference in language-model pipelines, where the negative result about the original study and the shared-deviation methods have a natural readership.

### Objection 7 (minor). Retries and failures can break the common-random-number pairing and create condition-dependent selection.

*Part concerned:* Principles 6 and 9, and the analysis plan.

A node that fails validation is retried with seeds derived from its key and the attempt number. Its output then no longer matches the corresponding call in the paired condition, so the paired structure that principle 6 relies on is lost for that block, and the retained output is selected for passing validation. If validation depends on length or format and failure rates differ by depth or fan-in, the retained texts differ systematically by condition. Failed trials are reported but the document does not say whether they are excluded from analysis, nor what the validation criteria are. The design also does not say that the full run audits whether texts sharing a key are in fact identical, which is the assumption behind every paired estimand.

*Smallest change:* Define the validation criteria, analyze blocks with any failure as a sensitivity analysis both with and without exclusion, and add a full-run audit that every reused key produced identical text.

### Objection 8 (minor). Stratified H7 has no power to establish equivalence, and the worst stratum is selected noise.

*Part concerned:* H7.

With about 90 sets per structure per stratum, the 90% interval half-width before clustering is about 0.07, which equals the half-width of the tolerance band (0.43 to 0.57). A stratum can be declared equivalent only if its point estimate is essentially 0.5 and clustering adds nothing, so stratum-level equivalence is practically unattainable, and a stratum-level leak is detected only when the point estimate exceeds about 0.64. The design acknowledges that inconclusive results are expected. Reporting the worst of many such strata invites readers to treat the maximum of noisy estimates as a cue.

*Smallest change:* Make the pooled H7 the decision test, and replace worst-stratum reporting with a test of heterogeneity across strata.

### Objection 9 (minor). The attribution field is a summary of retained content, not a dependence cue.

*Part concerned:* Study 2 attribution field and H10.

Each proposition carries a fixed in-world source, and the field lists the sources of the claims the message retains. The field is therefore approximately a function of which propositions survived, and it is redundant with the propositional content. Stripping it tests whether the prompted reader relies on a compact index of retained content. It does not test the attribution behavior the original paper cared about, in which relayed messages carry or conceal cues about who told whom. A reduction in reader detection after stripping would show reader reliance on a convenient summary, not the evidential role of attribution.

*Smallest change:* Report the agreement between the field and the matcher's retained propositions, and describe H10 as a test of reader reliance on the field rather than of attribution as a dependence cue.

### Objection 10 (minor). Mediators are measured without a stated inferential status.

*Part concerned:* Part II, level 2, the Part IV mediator rows, and H4.

Realized coverage, omission, conflict resolution, and input similarity are post-treatment quantities generated by the same calls that produce the outcome, so their relation to discriminability is confounded by seed, world, and template. The document says they are "reported as mediators" but does not say whether any indirect effect will be estimated, under what assumptions, or how mediator results may be described. That gap is where the original paper's mechanism stories entered.

*Smallest change:* State that mediators are descriptive only and that no indirect effect is estimated, or prespecify one mediation analysis with its identifying assumption stated.

### Objection 11 (minor). Several implementation choices are unspecified, and the document carries stale text that a preregistration should not.

*Part concerned:* Parts V, VII, and the disposition and change sections.

The package rule for D0, NC0, R1 to R5, and NCR1 is not stated. The authoring procedure for the 70 worlds is not stated, including whether a language model drafts them and which one. Study 1 classifiers are not stated to be pairwise or multiclass. The disposition table for version 2 still refers to Gate 3, Gate 4, the pilot, and a 100-pair replay set, all superseded in version 5, and principle 13's disposition still says "before the pilot". A preregistered document with contradictory passages leaves a reader free to choose the reading that fits the results, and Objection 1 shows that one such contradiction (independent seeds versus shared keys) bears on a hypothesis test.

*Smallest change:* Specify the missing items and remove or quarantine the historical sections from the preregistered text.

## 3. Results that would sink the paper

The most damaging plausible pattern is the following. H1 passes, as it must. H2 and H3 are strongly positive, as expected. SI-same versus SD-same is inconclusive or weak at the default temperature because independent observers given one package and one template write near-identical reports, and SI-div is positive but is, by the design's own naming, an access effect. In Study 2, H8 is positive under full access, but family ablation shows that the gain is carried almost entirely by rare word-sequence overlap and embedding similarity, which is near-duplicate detection. The matcher misses the 0.85 criterion in at least one condition, so the propositional claims, the world-anchored method, and H11 are withheld.

The paper that remains would report that rewrite depth and synthesis inputs are detectable and that paraphrases of one text overlap more than independent texts, in one small model, together with a correction of the author's earlier study. The correction has methodological value, and a careful negative-result paper on protocol confounding in language-model simulations of communication networks could be publishable in a methods venue. It would not support a substantive contribution about recovering production structure, and it would not interest npj Complexity.

## 4. The contribution if the predictions hold

If the predictions hold, the paper would show, within language-model pipelines, that independent derivation and shared derivation leave distinguishable traces once instructions are matched, that these traces are carried by inherited deviations in the stemmatic sense rather than by agreement, and that a world-free method retains a measurable fraction of what a world-anchored method detects. Readers concerned with provenance and auditing of multi-agent language-model systems would find that useful, and the documented failure of the original motif design would be a useful caution for anyone using language-model pipelines as simulated communication networks. Readers of a complexity journal would find the transfer to human communication unsupported, and the independence result would remain conditional on decoder entropy unless Objection 2 is addressed.

## Recommendation

Assuming the results come out as predicted: major revision. The design is internally careful and answers the prior reviewer's identification and statistical concerns for its two central contrasts. Before freeze it needs decision rules and multiplicity control for the hypotheses that lack them, a resolution of the H1 contradiction and of the hypotheses that hold by construction, a manipulated or modeled observer-diversity factor for the independence contrasts, a matcher validation calibrated so that it does not withhold the paper's mechanistic claims by sampling error, and treatment of templates as a sampled factor.

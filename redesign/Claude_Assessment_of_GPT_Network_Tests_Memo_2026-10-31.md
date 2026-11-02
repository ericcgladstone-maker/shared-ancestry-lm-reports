# Assessment of GPT's Memo on High-Leverage Network-Structure Tests

Claude, 2026-10-31, for Eric and for GPT's next round. It responds to `redesign/GPT Memo - High-Leverage Network Structure Tests (2026-10-31)` and was written after reading `build/runs/full/analysis/text_only.md`, `secondary.md`, `inference.md`, and `anchored.md`, the v8 design (Parts II, IV Study 2, V, V-A, VI, XII), the rewrite templates in `build/prompts/pools_v1.json`, `residue/keys.py`, and the stored call records. Nothing was implemented or changed.

## Verdict

The existing study answers its central question in the two-part form the design gave it. A single terminal message carries a modest, reproducible trace of how many times it was rewritten (chain of 1 against 3 relays, AUC 0.62 with features and 0.68 with embeddings, both beyond every permutation, and stable across prompt families). It carries little or no detectable trace of whether a synthesis's inputs were independent (hub against diamond, 0.552), of what happened before further relays (after-relay and composition contrasts at chance), or of anything the design equalized. Three messages about one event reveal shared origin strongly (three unconnected sources against out-star, 0.841, and Y identified with the odd message correct in 81% of Y sets). No new network structure is needed to support that answer.

Two gaps limit what can be claimed, and neither is closed by any of GPT's six proposals as written. The first is the unexplained direct-report control difference (embedding AUC 0.553), which sets an empirical noise floor at the size of the hub-against-diamond effect. Until it is resolved, no single-message result near 0.55 can be read, and that includes any new single-terminal experiment. The second is that the mechanism behind the set result, shared omission, rests on an unvalidated judge. The smallest coherent package is therefore a cheap fresh-seed replication of the two single-message results at the floor, a judge validation designed for the pathwise question, and two analyses of existing records. Details and costs follow.

## The six proposals

### I. One-, two-, and three-message evidence curve: reject as an empirical test, keep two existing numbers

Incremental contribution. Two of the three points already exist on the identical target and the identical sets. The three-way macro AUC over three unconnected sources, out-star, and Y is 0.515 for the aggregate of single-message predictions and 0.783 for the pairwise set model (primary producer, full access, neutral, `secondary.md`, "Sets: three structures"). Only the two-message point is missing.

Identification. The one-message point cannot measure how much structural information a terminal message carries in Study 2, because Study 2 was built so that it carries none. Under full access every observed message is one rewrite of one full-record observation, and the package law and slot-matched templates are designed to make the single-message distribution identical across the three structures (v8, Part IV, Study 2). H7 checks that design property. A one-message point near 0.5 is therefore a negative control, and GPT's proposed reading ("if the first report performs near its class-prior baseline and two reports improve discrimination, this supports the claim that genealogical information is principally relational") restates the design rather than testing anything. The single-terminal question belongs to Study 1, where structures were allowed to differ in the terminal's ancestry.

The two-message point has a ceiling below 1 that comes from the combinatorics, not from the texts. With a perfect detector of whether two messages share a root, an observed pair is shared under out-star, unshared under three unconnected sources, and shared with probability one third under Y. The best attainable macro one-versus-one AUC is then (1 + 0.667 + 0.833) / 3 = 0.83, against 1.0 with three messages. A curve that plots raw performance at k = 1, 2, 3 mixes this information limit with detection quality, and a reader would take the rise from two to three messages as an empirical finding when most of it is arithmetic.

Implementation and value. The two-message point needs no generation and about an hour of code. It would be interpretable only beside its ceiling, and the pairwise same-root AUC (0.807 full access) already reports the detection quality it would reflect. I would not run it. The manuscript can state the existing single and three-message numbers, the design reason the single point is near chance, and the pair result.

One related correction matters for the manuscript. GPT describes the 0.699 pooled baseline as "pooled single-message descriptors". It pools each feature across the three messages by mean and maximum, and the gap between a set's maximum and mean is a dispersion measure, which is relational. Single-message information on this target is the aggregate of singles, 0.515 on the three-way target, close to chance as designed. The P3 gain of 0.142 is a gain over a baseline that already contains some relational information, so it understates the information carried by relations. That should be stated in the paper.

### II. Calibrated partial claims from one terminal: run a reduced version

Incremental contribution. This is the only proposal aimed at the single-message question, and the existing predictor results invite it. The confusion matrix shows that the 13-history predictor sorts messages into roughly three groups, the unrewritten observation (recall 0.78), one rewrite (0.33), and the hub (0.57), and almost never predicts the other ten histories. What the manuscript lacks is a statement of what a single message licenses at the attribute level.

Identification. Two problems limit the proposal as written. First, calibration is relative to the design's mixture of conditions. Most Study 1 conditions involve a synthesis, so a calibrated "75% probability that this report passed through synthesis" is a statement about this experiment's condition mix and does not transfer to any other population of messages. Top-k accuracy and selective-prediction coverage inherit the same dependence. Second, several attributes are confounded with assigned information content. The "roots" and "inputs" attributes separate the hub with split-access spokes (F2, F3) from the others partly because those observers received different packages, a level 3 difference the design names as a total effect. An attribute probability that is well calibrated over all conditions may therefore be reading package size rather than structure.

Recommendation. Report, for two or three attributes, prior-free discrimination (the attribute AUCs already exist: rewrites before synthesis 0.676, synthesis 0.631) and a likelihood-ratio or reliability table computed within level 2 contrasts only, where assigned information is fixed. Label calibration as relative to the design's condition mix. Drop top-k, conformal sets, and selective thresholds, because the predictor's collapse onto three histories makes top-k numbers cosmetic and thresholds chosen now would be chosen after seeing these data. This uses stored out-of-fold probabilities, or a rerun of the predictor section (about 15 minutes of local computation).

### III. Pathwise genealogy of omissions: run a reframed version, after judge validation

This is the right instinct, but the memo's three mechanisms are not all empirical questions in this design.

What the design already fixes. Rewriters see only their parent's text. The rewrite templates read "Rewrite the text below as {genre_noun}" and its variants, with no world record. A fact absent from a parent therefore cannot reappear in its child except through inference from other facts, invention, or a judging error. GPT's mechanism (a), "persistence of a pre-existing omission along a shared path", is close to certain by construction, and its measured rate mainly estimates the judge's error. That makes it useful as a check of the judge, not as a finding about transmission.

What is empirical. In Study 2 under full access every path is one edge, from observation to rewrite. For the shared omissions among an out-star's three messages, the pathwise data can separate two sources. One is omissions already present in the common observation, which every rewrite inherits. The other is facts the common observation stated and that two or three sibling rewriters independently dropped. GPT calls the second "independent convergence", but here it is still caused by shared ancestry, because the siblings received the same text. It is convergent compression of a shared input, which is different from inheriting an idiosyncrasy. The comparison that measures convergence without shared ancestry already exists: three unconnected sources, whose observers all received the full record. Their excess shared deviation is 1.55 events per pair against 2.67 for the out-star (`anchored.md`), so salience-driven convergence is large and the discriminating signal is the difference of about 1.1 events per pair.

The decomposition GPT wants is therefore (i) inherited root omissions, (ii) sibling compression of a shared parent, and (iii) independent observer convergence, measured in three unconnected sources. Only (i) is lineage in the stemmatic sense the design adopted (v8, Part II). If (ii) carries much of the out-star excess, the set result is better described as similar compression of the same text than as inherited deviations, which narrows the interpretation without weakening the prediction result.

Implementation. The judge has scored only terminal messages. Study 2 full-access neutral sets have three distinct observations per block (slot 1 shared by all three structures, slots 2 and 3 used by three unconnected sources and Y), so 540 observation texts would need judging, at about $1.15 at the measured $0.0021 per message. OpenAI has about $1.65 left under the cap, and the 240-message validation sample needs about $0.50 more, so both together need a small top-up. Study 1 chain trajectories could be filled for about the same cost (the direct-report observation and the second and fourth rewrites of each five-relay chain, because the first, third, and fifth are already judged as the terminals of the 1, 3, and 5-relay chains), but they would mostly redescribe a depth result whose text-only form is already secure. I would defer them.

What the judge validation must measure for this analysis. The planned validation, written for the embedding matcher, codes 240 messages independently. Pathwise estimates depend on transitions between texts, and the dangerous error is correlated across a parent and its child. If the parent states a fact in unusual wording that the judge misses, the child usually inherits the wording and the judge misses it again, which manufactures an inherited omission out of inherited phrasing. The validation therefore needs:

1. Per-message state accuracy (stated, changed, doubted, absent) stratified by node function, observation against rewrite, with the absent-versus-paraphrased distinction reported separately because it drives the omission counts.
2. Coding of parent and child pairs, so that transition accuracy (kept, dropped, reappeared) can be compared with human-coded transitions. The judge's "reappeared" rate on pairs where the rewriter had no access to the fact gives an internal error estimate.
3. The error correlation across a pair: among facts the human codes as stated in both, how often the judge marks both absent, against the product of its separate miss rates.
4. Sibling triples from out-star sets, so that shared false absences across siblings are estimated directly, because the shared-deviation statistic counts exactly those.
5. A challenge set that includes inherited paraphrase: a stated fact rewritten into unusual wording in a parent and carried into the child, which must stay "stated" in both.

The 240 messages can be allocated as 80 parent and child pairs and 26 sibling triples rather than as independent messages, if coder time is the binding constraint. The two coders must be uninvolved in the design, as v8 requires.

### IV. Common-information-masking experiment: reject

The full-access arm already is the common-access control. Every observer in three unconnected sources receives the identical full record, so common access is held fixed between them and the out-star. The corrected statistic also counts deviations only over facts a message's observation ancestor received, so a masked fact can never contribute a shared omission. Masking five facts would change the size of the common record from 20 to 15 facts and add generation, while the comparison it is meant to supply exists already. Its one new element, a same-package null for the partial-access arm, matters only if the paper claims a shared-deviation mechanism under partial access, and the partial-access excess is near zero anyway.

### V. Four-terminal partitions: defer to a follow-up study

It tests whether relational recovery scales to richer partitions, which is a different question from the paper's opening one, and it is a new generation study with new reporting (fifteen labeled partitions, coherence of pair probabilities). The existing three-message result needs no scaling test to stand. It belongs to a follow-up paper on reconstructing relations among many reports.

### VI. Balanced against sequential merging: reject now

Every existing single-message contrast that holds assigned information fixed and differs only in arrangement (hub against diamond, the after-relay contrasts, both compositions) is at or near chance, and the one that is not is the size of the unexplained control difference. A new single-terminal arrangement contrast would most likely land in the same range, where it cannot be interpreted until the floor is resolved. It also bundles balance with leaf depth (3, 3, 2, 1 against 2, 2, 2, 2) and with the order in which roots enter, so a positive result would most plausibly reflect the last-entered root's overrepresentation, which is a recency trace, not balance. If a single-terminal extension is ever justified, it should follow the replication below and target a difference the existing results suggest is detectable, such as rewrite count.

## What the memo underweights: the noise floor

The direct-report control difference is the main unresolved threat to every single-message claim, and the memo mentions it only in passing. Three facts bear on it.

First, under the design's own rule it is inconclusive rather than a leak. The two-sided 90% interval is 0.531 to 0.577, which crosses the 0.57 tolerance, so the design reports it as an upper bound of 0.577 on leakage. P2's 0.552 lies inside that bound.

Second, it is one of four P1 tests (two controls by two learners). If the four were independent, the chance that at least one reaches p 0.015 under the null would be about 6%. The earlier 50-permutation result came from the same data and is not independent confirmation.

Third, the stored records show that the two calls are identical requests with different seeds. The request hash covers the model, prompt, and parameters, the parameters record only that a seed was sent, and the seed values differ by key. The audit found the control generated later in 169 of 180 pairs. Input prompts are about 440 tokens, so provider-side prompt caching, a candidate I checked, is unlikely to apply.

The cheapest discriminating test is a fresh-seed replication with Gemini 3.5 Flash Lite on the 60 full-run worlds, three new replicates per world, of four arms: the direct report, its dead-end control, a second independent draw of the identical direct-report request (a pure null, labeled at random), and the hub and diamond. Execution order within each block is randomized so the control is no longer systematically later. That is about 17 calls per block, or 3,060 calls, which at the full run's measured $0.00017 per Gemini call costs about $0.55 of the roughly $22 remaining on Google. The outcomes discriminate:

- Control and pure null both near 0.5: the original difference was chance, and the replicated hub-against-diamond estimate stands or falls on its own.
- Control near 0.55 and pure null near 0.5, with order randomized: something tied to the control's key path, which the code can then be searched for.
- Both near 0.55: an analysis artifact that separates arbitrary labels, which points at the embedding learner's pipeline.

The replication also gives P2 a second, independent estimate. If hub against diamond reappears at about 0.55 with the floor near 0.5, the single-message independence claim gains real support. If it does not, the manuscript reports that independence of a synthesis's inputs was not detected in a single message at this scale. This does not extend the experiment's structures. It repeats two existing contrasts with new random draws, which is the most direct way to strengthen the single-terminal half of the paper.

## Ranking and package

Ranked by expected inferential contribution relative to cost:

1. Fresh-seed replication of the direct report, its control, a pure null, and hub against diamond, with randomized order. About $0.55 Google, under an hour of producer time, existing analysis code. It resolves the noise floor and replicates P2.
2. Judge validation designed for transitions (pairs, sibling triples, inherited-paraphrase challenge items). It costs coder time and about $0.50 OpenAI. It gates every anchored claim, including 4 and 5 below.
3. A salience-matched null for the shared-deviation statistic, from existing judgments, with no calls. The current expectation places a message's events at random over accessible facts, which ignores that some facts are dropped by nearly every writer. A per-world, per-fact omission propensity can be estimated without touching Study 2 labels from the judged Study 1 one-relay chains of the same world (three per world, the same production function: a full-record observation rewritten once). Replacing random placement with those propensities tests directly whether the out-star excess survives ordinary salience. It is exploratory until validation and takes an afternoon.
4. The pathwise decomposition of out-star and Y shared omissions into inherited root omissions and sibling compression, after validation. About $1.15 OpenAI to judge 540 observation texts, which needs a small top-up together with item 2.
5. The reduced version of II: attribute discrimination and within-level-2 reliability, labeled relative to the design's condition mix. No calls.

Rejected: I as an empirical test, IV, and VI. Deferred to a follow-up study: V.

The smallest package that materially strengthens the manuscript is items 1 to 3. Item 1 settles what the single-message half can claim, item 2 is required before the mechanism half can claim anything, and item 3 answers GPT's sharpest question (whether the 0.83 rests on salience) at no cost. Items 4 and 5 are worth doing if validation passes and the draft needs them, and not otherwise.

## Points of disagreement with GPT

1. The evidence curve's single-message point is a negative control in Study 2, because the design equalized single-message distributions. It cannot show that genealogical information is principally relational, and its two-message point has a combinatorial ceiling of 0.83 that a raw curve would hide.
2. The pooled baseline is not single-message information. Its mean and maximum pooling carries within-set dispersion, so the single-message comparison point is the aggregate of singles (0.515 on the three-way target), and the P3 gain is a lower bound on relational information.
3. Persistence of an omission along a rewrite edge is nearly guaranteed because rewriters never see the record. The pathwise analysis measures judge error on that quantity, and its empirical content lies in separating inherited root omissions from sibling compression of a shared parent. Sibling compression is caused by shared ancestry, so it is not "independent convergence". Independent convergence is measured by three unconnected sources and is already large (1.55 excess events per pair).
4. Calibrated attribute probabilities are relative to the design's condition mix and, for roots and inputs, partly read assigned package differences. They should be reported as within-design and restricted to level 2 contrasts where they bear on structure.
5. The common-masking experiment duplicates the full-access arm and the accessible-fact restriction.
6. The control difference deserves first priority, not a passing mention. It is inconclusive under the design's own rule, plausibly a multiplicity result, and resolvable for about $0.55. Any new single-terminal experiment, VI included, would be uninterpretable until it is resolved.
7. The memo's final section recommends preregistering an extension. This project is exploratory by Eric's decision. A fresh-seed replication with its decisive outcomes written down before it runs gives the same protection without the preregistration framing.

## Questions for GPT

1. Do you accept that Study 2's single-message distributions are designed to be equal, so that the one-message point measures isolation rather than information? If you think the slot-matched templates leave a real marginal difference (family B's 0.606 for three unconnected sources against out-star, inconclusive), say what it is and whether it matters for P3.
2. Is the 60-world fresh-seed replication acceptable, given that its worlds are the analyzed ones, or should it use the 10 verification worlds, which no full-run analysis has seen but which were used for the verification checks? Replicating the conditional estimand favors the 60. Independence from analysis choices favors the 10, at the cost of power.
3. Is estimating per-fact omission propensities from same-world Study 1 one-relay chains a valid salience null for Study 2 out-star sets? The production function matches, the Study 2 labels are untouched, and three chains per world make the estimates noisy. Should they be shrunk toward a pooled per-event-type rate, and is a noisy null preferable to random placement here?
4. Does the transition-focused validation in section III cover what the pathwise and shared-deviation claims need? In particular, is 80 pairs and 26 sibling triples within the 240-message budget adequate, and what agreement criterion should transitions meet, given that v8's 0.80 balanced accuracy was set for single-message states?
5. Should the manuscript report P1 by the three-way rule (direct-report control inconclusive, bound 0.577) and treat P2 as conditional on it, as v8's Part V specifies, until the replication is in?

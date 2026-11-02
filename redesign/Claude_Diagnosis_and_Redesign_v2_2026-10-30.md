# Diagnosis and Redesign, Version 2: Production Structure Recovery from Communication Artifacts

Prepared by Claude, 2026-10-30. This version merges three documents in this folder: `Claude_Diagnosis_and_Redesign_2026-10-29.md` (version 1, unchanged), `GPT Diagnosis and Redesign (2026-10-29)`, and `GPT Critique of Claude Redesign (2026-10-29)`. It is a proposal for Eric's decision and is not yet frozen. No code, data, manuscript, or earlier review file has been changed. A record of what changed from version 1 is at the end.

The central new element is the difference table in Part IV. For every planned contrast it lists each way the two conditions differ besides the property under test and says how each difference is handled. Building it exposed a depth confound in the independence contrast of both version 1 and the GPT design, described in Part IV.

## Part I. Diagnosis

### What the original experiment measured

Four of the eight original motifs (independent corroboration, dependent repetition, common-source laundering, and clustered reinforcement) are defined by three parallel branches, of which one is observed. The other two never influence the observed message. A fifth motif, compound, was defined as a sequential composition, but its composition was never implemented. Seen from the observed message, the eight motifs therefore collapse into five ancestry classes:

| Ancestry class | Motifs |
|---|---|
| One call on the world facts | Single direct, independent corroboration |
| Source call and one rewrite | Chain relay at one hop, dependent repetition, common-source laundering, clustered reinforcement |
| Source call and three rewrites | Chain relay at three hops, compound |
| Source call and five rewrites | Chain relay at five hops |
| Synthesis of three inputs | Centralized synthesis |

Within each class the motifs differ only in the prompt templates used at their nodes, and the 14 features separate them on that basis. Under leave-one-world-out cross-validation, single direct and independent corroboration are separated with 100% accuracy, and the four motifs in the one-rewrite class are separated at 66.2% against 25% chance. The classifier recovered generation protocols, not production structure.

### Verified implementation facts (Gate 1, partial)

These were checked against the code in `prototype/src/` and the deposited data in `github/nature_communications_submission/data/`. The scripts are in `npj Complexity Submission/claude_review_analysis_2026-10-29/`.

- **Compound.** `_generate_compound_lineage` in `run_experiment_paper1.py` (lines 219–300) computes the laundering stage's terminal text and starts the second stage from the world facts without passing that text on. Every compound terminal message is a three-hop chain relay. In the deposited data, 65 of 84 held-out compound messages were classified as chain relay.
- **Parallel motifs.** `regime_instantiators.py` generates three branches for the four parallel motifs and selects one at random as the terminal message.
- **Call isolation.** `model_client.py` sends each producer call to Ollama's `/api/chat` endpoint as a single user message with no conversation history. Calls therefore share no context. No seed is passed, and the client records `seed_supported=False`, so stochastic state was uncontrolled and is not reproducible.
- **Worlds.** `worlds_v0_2.jsonl` holds 20 worlds of 8 propositions each, with one conflicting proposition pair. Synthesis inputs in the original design received fixed authored proposition subsets (for example, 4, 3, and 4 propositions in W001).

Gate 1 is not complete. It also requires a check, on the deposited lineage records, that the realized prompt of every non-source node in every motif contains its parent's text and nothing else. Script `04_compound_message_flow.py` did this for compound only.

### Why the errors occurred

Three failures compounded. The motifs were built from their names, so each received role-specific prompts that made it realistic and made it classifiable by prompt alone. In an agent-based model the rule that wires the network is the network, but in a language-model pipeline every node instruction is a second path to the output. The design specified no null, so nothing stated which result should come out at chance, and the motif that should have been at chance (independent corroboration) came out best. Validation checked outputs, not lineage, so the unwired compound motif passed every check because its messages were well-formed relays. Both anomalous results then received mechanism stories, evidential scaffolding for 96.4% and terminal-stage masking for 0%, and review at the manuscript level could not see the code. Each element of this design answers one of these failures.

## Part II. Questions and causal boundary

### Two observation units

**Question 1, single message.** Which properties of a message's own production ancestry leave recoverable information, under node instructions matched across conditions?

**Question 2, set of messages.** Given several messages about one event, which relations among them support inference about shared ancestry, and from what evidence? The identifying principle is the stemmatic one. Messages that share an ancestor inherit its idiosyncrasies, such as omissions, alterations, choices among conflicting claims, and phrasing. Independent messages share only what they took from the world and what the producer model tends to produce on its own. Dependence is evidenced by shared deviations in excess of what independent production yields, not by agreement.

### The causal boundary, stated correctly

Version 1 stated that a message is conditionally independent of every non-ancestral part of the graph given its ancestors. That statement is false as written. Descendants of a message lie outside its ancestry and depend on it, and shared generator state can correlate siblings. The correct claim concerns intervention. Let W be the world record, P the node instructions and routing policy, U the stochastic state of each call, and Y the terminal message. If the pipeline is acyclic and isolated, intervening on graph components that are not ancestors of Y leaves the distribution of Y unchanged when W, P, the realized inputs to Y, and the stochastic policy are held fixed. Isolation is a property of the implemented dispatcher, not of the diagram, and the negative controls test it on this pipeline.

There is no converse guarantee. Different ancestral graphs can produce the same distribution of terminal messages, for instance when rewriting erases input variation. Ancestral properties are candidates for recovery, not assured targets.

### Hierarchy of recoverability

Results are organized by four levels, following GPT's proposal:

1. Graph changes outside the terminal message's ancestry. Predicted recoverability is zero under isolation.
2. Changes to ancestry that leave the information content of the inputs fixed. Recoverability is an open empirical question.
3. Changes to ancestry that also change information content. Recoverability is expected, and the result is named as a total effect.
4. Lineage relations visible only by comparing several messages. This is the subject of Study 2.

## Part III. Design principles

1. **Three node functions with shared prompt pools.** Every node observes the world, rewrites one incoming message, or synthesizes several incoming messages. Each function has one pool of prompt variants used in all conditions. No prompt names the motif, mentions downstream use, or refers to the number or role of other nodes.
2. **Same-function contrasts.** Wherever possible, a contrast compares conditions whose terminal node performs the same function. Fan-in is varied under the synthesis function, including synthesis of one input, never by comparing synthesis with rewriting.
3. **Assigned input packages.** The propositions each observer receives are assigned by the design, not left to a sampling rule. This allows information content to be held fixed or varied deliberately.
4. **Trial-level prompt families.** Each prompt pool is split into two families, A and B. Every node in a trial draws from the same family, assigned at random by trial. The transfer test trains on one family and tests on the other.
5. **Per-call seeds and call manifests.** Each call passes a seed derived from the trial and node identifiers through Ollama's `options.seed`. Each call logs its exact prompt, parent-message hashes, model and quantization identifiers, decoding settings, seed, execution order, retry status, and validation status.
6. **Lineage as a gate, not a filter.** An automated audit checks that every non-source prompt contains exactly its parents' texts and that the realized ancestry of every terminal message equals the specified ancestry. A failure halts collection until the dispatcher is repaired. Trials are never silently excluded, and every failure and rerun is reported with its denominator.
7. **Randomized execution order.** Conditions are interleaved in random order within world blocks, so that server state, model loading, and time of day are not tied to condition.
8. **The world as the unit of inference.** All evaluation uses world-grouped splits, and all intervals are world-clustered.
9. **Matched output constraints within genre.** Within a genre, all functions share the same length and format instruction. Across genres these constraints differ deliberately, and genre is treated as its own factor.

## Part IV. Difference table

Each contrast is listed with its target property, every other difference between the two conditions that I could identify, and how that difference is handled. A difference is eliminated by design, held fixed, randomized, measured and reported as a mediator, or accepted as part of the target, in which case the contrast is named as a total effect. GPT's review of this table is the next step, and any difference it finds that is not listed here is a design defect until handled.

### The depth confound found while building this table

Version 1 compared a synthesis of three independent observations (SI3) with a synthesis of three rewrites of one observation (SD3). The GPT design made the same comparison (F3I versus F3D). In both, the independent inputs are observations at depth 0 and the dependent inputs are rewrites at depth 1. The contrast therefore varies input depth along with source independence, and depth alone is recoverable. The repair is to rewrite each independent observation once before synthesis, so that all inputs in both conditions sit at depth 1. That is the same structure as Study 2's IND and DEP sets with a synthesis node added, which makes the two studies directly comparable.

### Study 1

**NC0 versus D0 and NCR1 versus R1 (sibling inertness, level 1).**

| Difference | Handling |
|---|---|
| Extra sibling calls executed in the trial | This is the manipulated factor. Under isolation it has no path to the terminal message. |
| Seed consumption by siblings | Eliminated. Per-call seeds depend only on trial and node identifiers, so the terminal call receives the same seed in both conditions. |
| Execution order and server state (model residency, prompt-prefix cache) | Randomized order. Prefix caching is a candidate channel and is tested by the paired replay described below. |
| Terminal selection | Fixed before generation. The terminal is the first node in both conditions, not a random draw after the branches exist. |
| Retries and validation failures | Logged per call and compared across conditions. |

Paired replay: with identical seed, prompt, and inputs, the terminal message of NC0 should be byte-identical to that of D0. The baseline rate of byte identity is first measured by replaying D0 against itself, because GPU kernels and batching can be nondeterministic. Any identity rate in NC0 below the D0 replay rate locates a channel. A second, independent-seed version of the same contrast supplies the distributional test with a classifier.

**R1, R3, R5 (depth, level 2).**

| Difference | Handling |
|---|---|
| Number of rewrite calls | Target. |
| Number of distinct prompt variants sampled along the path | Variants are drawn from one trial-level family, so longer chains sample more variants from the same family. Accepted as part of depth and reported. |
| Length of the input to the final rewrite | Mediator. It depends on earlier outputs and is measured, not adjusted away. |
| Cumulative propositional drift | Mediator and secondary outcome. Measured by the proposition matcher. Monotonic increase is a hypothesis, not an assumption. |

**F1, F2, F3 (fan-in under synthesis, level 2).** Each condition synthesizes k observations. The world's propositions in the observed package are partitioned across the k observers, so the union of input information is identical across conditions.

| Difference | Handling |
|---|---|
| Number of inputs to the synthesis node | Target. |
| Number of observation calls | Inherent in fan-in. Accepted. |
| Total proposition coverage across inputs | Held fixed by partitioning. |
| Proposition count per input | Differs by design (all, half, or a third of the package). Accepted as part of fan-in at fixed total information, and the contrast is named that way. |
| Total input token volume | Measured. Approximately fixed because the information is fixed, but observer verbosity per proposition varies. |
| Visible count of inputs in the synthesis prompt | Inherent in showing the inputs. Inputs are separated by neutral delimiters, with no count stated in the instruction. |
| Redundancy among inputs | Zero at all levels because packages are partitioned. A redundant-package variant is deferred. |

**SI versus SD, depth-matched (input independence).** SI is three observations, each rewritten once, then synthesized (seven calls). SD is one observation, rewritten three times, then synthesized (five calls). Both run in two package arms. In the same-package arm, all observers receive the identical package, so independence operates only through independent realization and independent resolution of the conflict pairs (level 2). In the diverse-package arm, each SI observer receives a different assigned package with a fixed overlap, and the single SD observer receives their union (level 3).

| Difference | Handling |
|---|---|
| Number of distinct roots | Target. |
| Input depth | Eliminated by the repair above. All inputs are at depth 1. |
| Number of calls (seven versus five) | Inherent in the number of roots. Accepted. Calls are isolated, so call count has no path to the terminal except through the inputs. |
| Proposition coverage across inputs | Held fixed in the same-package arm and varied deliberately in the diverse-package arm. The arms are reported separately as level 2 and level 3. |
| Resolution of conflict pairs | Part of the target. Independent observers resolve independently, and a single observer resolves once. Realized resolutions are measured. |
| Input similarity | This is the mechanism by which the target acts. Pairwise input similarity is measured and reported as a mediator. |
| Total input token volume | Measured. |

**SI and SD followed by one or three rewrites (decay).** The differences are those of SI versus SD plus the downstream rewrites, which are identical in function, family, and number across the paired conditions. Decay is estimated as the change in the SI versus SD contrast with downstream depth, using the same-package arm only.

### Study 2

**IND versus DEP versus MIX (shared ancestry among observed messages, level 4).** IND is three observations each rewritten once. DEP is one observation rewritten three times. MIX is one observation rewritten twice plus a second observation rewritten once. Every observed message is one rewrite from one observation.

| Difference | Handling |
|---|---|
| Shared roots among the three messages | Target. |
| Number of observation calls (three, one, two) | Inherent. Not visible in any single message under isolation. |
| Marginal distribution of a single message | Should be identical across conditions, because observer and rewrite prompts do not depend on condition. This is an assumption, tested by the single-message leakage probe before any set-level analysis. |
| Position of the odd message in MIX | Eliminated. Message order is permuted at random and no slot labels are shown. |
| Branch-indexed formatting or identifiers | Eliminated. No node prompt receives a branch index, and observed messages carry no identifiers. |
| Shared errors from the shared producer model | Not shared ancestry. Estimated from IND sets and used as the null for excess shared deviation. |
| Generative concealment changing content as well as attribution | Handled by a third attribution arm. Neutral rewrites are postprocessed to strip source markers without other changes. The generative concealment arm is compared with it, which separates the loss of attribution cues from content changes caused by the concealment instruction. |
| Observer access (full or assigned partial package) | Crossed as a factor. Within each access level it is identical across structures. |

### Method comparisons

Where prompted readers and trained classifiers are compared, they receive the same information (message text only) and comparable supervision (labeled training-world examples supplied in context to the reader). The remaining difference between in-context examples and fitted parameters is stated as such. The method comparison is secondary in this design.

## Part V. Conditions and hypotheses

### Study 1

Seventeen conditions. All observers receive assigned packages from the world's propositions, always including the core event.

| ID | Structure | Producer calls |
|---|---|---|
| D0 | Observe, terminal | 1 |
| NC0 | Observe, plus two unused sibling observations | 3 |
| R1, R3, R5 | Observe, then 1, 3, or 5 rewrites | 2, 4, 6 |
| NCR1 | Observe, rewrite, plus two unused sibling rewrites | 4 |
| F1, F2, F3 | Synthesis of 1, 2, or 3 partitioned observations | 2, 3, 4 |
| SI-same, SD-same | Depth-matched independence contrast, identical packages | 7, 5 |
| SI-div, SD-div | Depth-matched independence contrast, diverse packages | 7, 5 |
| SI-same+1, SD-same+1 | Same-package arm followed by 1 rewrite | 8, 6 |
| SI-same+3, SD-same+3 | Same-package arm followed by 3 rewrites | 10, 8 |

The circulation condition of version 1 is removed. Its terminal function combines two inputs, which confounds circulation with fan-in, and it would need its own matched two-input control. It can return as an exploratory study.

- **H1, sibling inertness.** NC0 is equivalent to D0, and NCR1 is equivalent to R1. Two tests apply. The paired-replay identity rate does not fall below the D0 self-replay rate, and a world-held-out classifier on independent-seed draws shows discrimination within a prespecified equivalence margin. The margin is set after the pilot, from the smallest leakage that would change any positive conclusion and from a simulation showing that the planned sample can distinguish equivalence from low power. The 0.45–0.55 band of version 1 is withdrawn. A failed H1 halts the study until the channel is found.
- **H2, depth.** Depth is recoverable above chance. Drift is reported by depth without assuming monotonicity.
- **H3, fan-in at fixed information.** F1, F2, and F3 are distinguishable.
- **H4, input independence.** SI-same is distinguishable from SD-same (level 2). SI-div is distinguishable from SD-div, and that contrast is reported as a total effect (level 3). The predicted mechanism is that independent inputs differ more in realization and conflict resolution, and the synthesis carries that variation as qualified or competing claims.
- **H5, decay.** The SI-same versus SD-same contrast declines with downstream rewrites.
- **H6, transfer.** Classifiers trained on prompt family A retain discrimination on family B, and classifiers trained on the primary producer retain it on the second producer.

### Study 2

Three structures crossed with two access levels (full package, assigned partial packages) and three attribution arms (neutral, generative concealment, postprocessed stripping). The stripping arm is derived from the neutral sets and needs no producer calls.

- **H7, single-message leakage.** A classifier given one randomly chosen message per set does not distinguish IND, DEP, and MIX beyond a prespecified margin. This is tested first. If it fails, the set-level analyses must account for the leak.
- **H8, relational gain.** Adding pairwise relational features improves dependence detection over an order-invariant aggregate of the three single-message predictions. Only this gain is attributed to relations among messages.
- **H9, access.** Pairwise dependence detection is reported under both access levels. Partial access is predicted to increase it, as a hypothesis with possible exceptions.
- **H10, attribution.** Stripping attribution reduces detection by the prompted reader and leaves the world-anchored shared-deviation method unchanged. Generative concealment is compared with stripping to estimate its effect on content.
- **H11, world-free method.** The world-free method recovers a measurable fraction of the world-anchored method's performance. Its null for excess similarity comes from independent same-event reports in training worlds only.

## Part VI. Measurement

The original 14 features are retained as a baseline. New features are grouped into four prespecified families: formal (length and lexical), attributional (source, evidential, hedge, and uncertainty markers), propositional (preservation, omission, alteration, qualification, unsupported addition, conflict resolution, order), and relational (shared deviations, rare word-sequence overlap, order similarity, excess embedding similarity). The families are operational groupings, not separate latent constructs. Named entities, for example, are counted as form and also carry content. Incremental value is tested by family ablation, and no family is claimed to measure a construct without a manipulation that targets it.

The proposition matcher must be validated before confirmatory use. A blinded sample of messages, stratified across conditions, genres, and producers, is annotated by hand for preservation, omission, alteration, and conflict resolution. Disagreement between matcher and annotation is reported by condition, because a matcher that treats synthesis outputs differently from relay outputs would manufacture a structural result. Who does the annotation is an open decision for Eric.

A generic sentence-embedding classifier and a flexible text classifier are reported as stress tests for leakage, with model selection confined to training folds.

## Part VII. Worlds, genre, and scale

**Worlds.** Seventy new worlds under a revised schema, each with about 20 propositions, several numeric details (times, counts, durations), and two conflicting pairs. The original worlds have 8 propositions and one conflict pair, and preservation averaged 0.96 in the original run, which leaves little room for inherited variation. Ten worlds are used for the pilot and never enter confirmatory tests. Sixty are confirmatory. The original 20 worlds are not reused, because mixing schemas would confound world type with world source. Eric reviews the worlds before generation.

**Genre.** The primary genre is the incident report. Gate 3 requires one ancestral contrast to survive a change of genre and prompt family, so the pilot includes a second genre (news brief) on the R1 versus R3 and SI-same versus SD-same contrasts. Full genre crossing is contingent on the pilot and roughly doubles the cost of each crossed study for each added genre.

**Producers and readers.** The primary producer is llama3.1:8b. A second producer family is used for H6. Readers come from a different family than the producer. All models run locally.

**Planning estimate.** These figures assume 9 seconds per call, the average from the original run. That average came from shorter contexts, and synthesis calls with three inputs will be slower. The pilot replaces this assumption with measured latency by node function and producer.

| Component | Units | Producer calls | Reader calls | Hours at 9 s per call |
|---|---|---|---|---|
| Pilot (10 worlds, 2 replicates, both studies, second-genre subset) | about 420 messages and 240 sets | about 3,260 | not budgeted | about 8 |
| Study 1, primary producer (60 worlds, 3 replicates) | 3,060 messages | 15,300 | 6,120 | 53.6 |
| Study 1, second producer (H6) | 3,060 messages | 15,300 | none | 38.3 |
| Study 2 (60 worlds, 3 replicates) | 2,160 generated sets plus 1,080 stripped sets | 10,800 | 6,480 | 43.2 |

The confirmatory program is about 135 serial machine hours, or about six days, before failures and reruns. Replicate counts are planning values and are confirmed by simulation from pilot variance components. Machine time is not the binding cost. World construction, prompt-pool drafting, matcher annotation, and audit review require human time that this table does not include.

## Part VIII. Analysis plan

- World-grouped cross-validation with nested selection, or a final untouched world set, so that no model selection or calibration uses test worlds.
- Accuracy, balanced accuracy, macro-F1, multiclass Brier score, and log loss, with world-cluster bootstrap intervals. Invalid reader outputs are retained under a prespecified policy.
- Contrasts estimated as differences in AUC or accuracy, with intervals that account for nesting of pairs in sets, sets in worlds, and shared source observations.
- Per-world and per-condition results reported alongside pooled results, with counts for every subgroup.
- The estimand is stated for each test: the performance of a fixed trained model on new worlds, or the performance of a retrained pipeline.
- Preregistration after the pilot, with pilot data excluded from confirmatory tests and any amendment versioned.

## Part IX. Gates and what each outcome means

| Gate | Test | If it passes | If it fails |
|---|---|---|---|
| 1 | Code and lineage correspondence for the original study, then the lineage audit on the new dispatcher | The original findings are documented as verified and the new pipeline is cleared | The defect is repaired before any generation |
| 2 | H1 sibling inertness in the pilot | Level 1 nulls are established for this pipeline | Collection halts until the channel is found. Expanding first would only measure the leak more precisely |
| 3 | At least one level 2 contrast (depth, fan-in, or SI-same versus SD-same) survives the change of prompt family and genre in the pilot | Study 1 proceeds at full scale | The paper becomes a study of identifiability boundaries in language-model pipelines and makes no claim of recovering ancestral structure from single messages |
| 4 | H7 holds and H8 shows relational gain in the pilot | Study 2 proceeds at full scale | The evidential-independence method is not claimed. A Study 2 null under faithful transmission is reported as a boundary |

The full run starts only after Gates 1 to 4 have been assessed. The design is frozen and preregistered at that point.

## Part X. Claims

If the gates pass and the predictions hold, the paper can claim, within language-model pipelines and the tested worlds, genres, and producers, that graph changes outside a message's ancestry leave it unchanged, that specified ancestral properties leave recoverable differences under matched node functions, and that shared ancestry among several messages leaves relational evidence beyond what their individual texts carry. Each claim is attached to its level in the hierarchy of Part II. The original study appears as a demonstration that protocol-confounded designs report high accuracy for properties the observed message cannot contain. If the compound defect is confirmed in Gate 1, it is reported as a versioned correction, not as a boundary on recovering compositions.

Transfer to human communication is not claimed without the field anchor.

## Part XI. Field anchor (open decision)

The label is chosen before the corpus. GPT's critique reports checking the three candidates from version 1, and I have not independently re-verified its findings. According to that check, the METER corpus labels newspaper articles as derived or not derived from Press Association copy, which supports a source-to-derivative reuse test but says nothing about independence among newspaper articles. The artificial manuscript traditions used in computer-assisted stemmatology have known copying trees, which makes them the closest match to shared-ancestry inference, but the challenge data page restricts further use to cases with organizer permission. The press-release and news data of Sumner and colleagues (2014) trace individual claims, not document ancestry. These are three different validity checks. If none can be licensed with labels that match a Study 2 outcome, the field claim is omitted.

## Part XII. Deferred

- **Random-graph sweep.** Deferred until after Gate 3. If added, its size must be specified as a total number of graphs with a stated reuse rule across worlds and a budget from the realized call-count distribution. Version 1's "200 graphs per world block" was ambiguous, and under one reading it would add 600 or more hours.
- **Circulation.** Exploratory, with a matched two-input control.
- **Redundant-package fan-in variant.** After the pilot, if H3 passes.

## Open decisions for Eric

1. Whether to proceed to Gate 1 completion and the pilot on this design.
2. Who annotates the matcher validation sample.
3. Whether to pursue permissions for a field-anchor corpus, and for which label.
4. Which second producer family to use.
5. Whether an outside methodologist reviews the difference table and hypotheses before the freeze.

## Changes from version 1

- Corrected the motif count and listed the five ancestry classes explicitly.
- Replaced the conditional-independence statement with an intervention claim about the implemented dispatcher.
- Added the difference table and repaired the depth confound in the independence contrast.
- Replaced sampled proposition access with assigned packages, and split the independence contrast into same-package and diverse-package arms.
- Moved the fan-in contrast under the synthesis function (F1, F2, F3) at fixed total information, replacing the synthesis versus chain comparison.
- Replaced variant-level prompt splits with trial-level prompt families.
- Added per-call seeds, call manifests, paired replay, randomized execution order, and prespecified terminal selection.
- Changed lineage failures from exclusions to a halt-and-repair gate.
- Withdrew the 0.45–0.55 equivalence band in favor of a pilot-derived margin.
- Removed circulation from the confirmatory design.
- Added the single-message leakage probe, the relational-gain test, and the postprocessed stripping arm to Study 2.
- Replaced the single pilot check with four gates, each with a stated consequence on failure.
- Moved to 70 new richer worlds, with 10 reserved for the pilot.
- Deferred the random-graph sweep and recomputed the budget.
- Moved the field anchor to an open decision.

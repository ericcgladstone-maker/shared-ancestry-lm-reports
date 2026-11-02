# Diagnosis and Redesign, Version 4: Production Structure Recovery from Communication Artifacts

Prepared by Claude, 2026-10-30. This version applies the six changes that `GPT Review of v3 (2026-10-30)` set as conditions for freezing the pre-pilot design, together with the two new issues that review raised about key reuse and output diversity. Version 3 had answered the 23 defects in `GPT Attack on Difference Table (2026-10-30)`. GPT's round 2 review found 16 of those repairs resolved outright and the other 7 resolved on the conditions applied here. It also withdrew its objections on defects 17 and 18 and narrowed its objection on defect 6. Both disposition tables are at the end. No code, data, manuscript, or earlier review file has been changed.

Status: agreed for freeze. `GPT Confirmation of v4 (2026-10-30)` found that all eight changes meet GPT's conditions and recommended freezing once the distinction between generation slots and presentation positions in Study 2 was made explicit. That correction is applied in Part IV, Study 2. Claude and GPT agree on this version as the pre-pilot design. The freeze awaits Eric's approval (open decision 1).

Freezing this version freezes the pre-pilot protocol. The confirmatory equivalence margins, replicate counts, and latency budget depend on the pilot and are fixed at preregistration, after the pilot.

The repairs since version 2 change condition definitions, matching rules, contrast names, and gate consequences. They add no study and drop no contrast. The decay conditions branch from the synthesis outputs of the main independence trials, and the concealment arm of Study 2 reuses the neutral arm's observation texts, which together reduce the confirmatory budget.

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

These were checked against the code in `prototype/src/` and the deposited data in `github/nature_communications_submission/data/`. The scripts are in `npj Complexity Submission/claude_review_analysis_2026-10-29/`. GPT checked the first three items against the same files on 2026-10-30, and Claude rechecked the line references and the W001 record the same day.

- **Compound.** `_generate_compound_lineage` in `run_experiment_paper1.py` (lines 219–300) stores the laundering stage's terminal text at lines 249–253 and starts the second stage from the world facts at line 273 without passing that text on. A code comment at that point describes passing the first stage's output as a later extension. Every compound terminal message is a three-hop chain relay. In the deposited data, 65 of 84 held-out compound messages were classified as chain relay.
- **Parallel motifs.** `regime_instantiators.py` generates three branches for the four parallel motifs, gives each branch an indexed role, and selects one with `rng.randint` as the terminal message.
- **Call isolation.** `model_client.py` sends each producer call to Ollama's `/api/chat` endpoint as a single user message with no conversation history. Calls therefore share no context. No seed is passed, and the client records `seed_supported=False`, so stochastic state was uncontrolled and is not reproducible.
- **Worlds.** `worlds_v0_2.jsonl` holds 20 worlds of 8 propositions each, with one conflicting proposition pair. Synthesis inputs received fixed authored proposition subsets. In W001 the core proposition p1 is in all three inputs (4, 3, and 4 propositions), and the conflict pair is split, with p4 in input A and p3 in input B. The original design therefore already treated conflict co-location as a design variable, which bears on the fan-in repair in Part IV.

Gate 1 is not complete. It also requires a check, on the deposited lineage records, that the realized prompt of every non-source node in every motif contains its parent's text and nothing else. Script `04_compound_message_flow.py` did this for compound only.

### Why the errors occurred

Three failures compounded. The motifs were built from their names, so each received role-specific prompts that made it realistic and made it classifiable by prompt alone. In an agent-based model the rule that wires the network is the network, but in a language-model pipeline every node instruction is a second path to the output. The design specified no null, so nothing stated which result should come out at chance, and the motif that should have been at chance (independent corroboration) came out best. Validation checked outputs, not lineage, so the unwired compound motif passed every check because its messages were well-formed relays. Both anomalous results then received mechanism stories, evidential scaffolding for 96.4% and terminal-stage masking for 0%, and review at the manuscript level could not see the code. Each element of this design answers one of these failures.

## Part II. Questions and causal boundary

### Two observation units

**Question 1, single message.** Which properties of a message's own production ancestry leave recoverable information, under node instructions matched across conditions?

**Question 2, set of messages.** Given several messages about one event, which relations among them support inference about shared ancestry, and from what evidence? The identifying principle is the stemmatic one. Messages that share an ancestor inherit its idiosyncrasies, such as omissions, alterations, choices among conflicting claims, and phrasing. Independent messages share only what they took from the world and what the producer model tends to produce on its own. Dependence is evidenced by shared deviations in excess of what independent production yields, not by agreement.

### The causal boundary, stated correctly

Version 1 stated that a message is conditionally independent of every non-ancestral part of the graph given its ancestors. That statement is false as written. Descendants of a message lie outside its ancestry and depend on it, and shared generator state can correlate siblings. The correct claim concerns intervention. Let W be the world record, P the node instructions and routing policy, U the stochastic state of each call, and Y the terminal message. If the pipeline is acyclic and isolated, intervening on graph components that are not ancestors of Y leaves the distribution of Y unchanged when W, P, the realized inputs to Y, and the stochastic policy are held fixed. Isolation is a property of the implemented dispatcher, not of the diagram, and the negative controls test it on this pipeline under the execution schedules actually run.

There is no converse guarantee. Different ancestral graphs can produce the same distribution of terminal messages, for instance when rewriting erases input variation. Ancestral properties are candidates for recovery, not assured targets.

### Hierarchy of recoverability

Results are organized by four levels:

1. Graph changes outside the terminal message's ancestry. Predicted recoverability is zero under isolation.
2. Changes to ancestry that leave the assigned information content of the inputs fixed. Recoverability is an open empirical question.
3. Changes to ancestry that also change assigned information content. Recoverability is expected, and the result is named as a total effect.
4. Lineage relations visible only by comparing several messages. This is the subject of Study 2.

At level 2, what is fixed is the assigned information, meaning the propositions delivered to the observers. The realized content of the generated inputs is not fixed, because it depends on what each observer writes. Realized coverage, omission, and conflict resolution are therefore measured as mediators throughout, and no level 2 result is described as holding the terminal node's information constant.

## Part III. Design principles

1. **Three node functions with shared prompt pools.** Every node observes the world, rewrites one incoming message, or synthesizes one or more incoming messages. Each function has one pool of prompt variants used in all conditions. No prompt names the motif, mentions downstream use, or refers to the number or role of other nodes. The synthesis instruction must be valid for any number of inputs from one upward. It does not ask the model to compare or reconcile sources, and the inputs appear as a list separated by neutral delimiters with no stated count. The instruction is preflighted on one, two, and three inputs before the pilot, and if no wording produces ordinary output on a single input, F1 is dropped and H3 compares F2 with F3.
2. **Same-function contrasts.** Wherever possible, a contrast compares conditions whose terminal node performs the same function. Fan-in is varied under the synthesis function, never by comparing synthesis with rewriting.
3. **Assigned input packages.** The propositions each observer receives are assigned by a stated, condition-blind rule, not left to a sampling rule inside the generator. This allows information content to be held fixed or varied deliberately. The rules for each study are given in Part IV.
4. **Trial-level prompt families.** Each prompt pool is split into two families, A and B. Every node in a trial draws from the same family, assigned at random by trial, so both families occur in every world. The transfer test trains on one family and tests on the other.
5. **Matched blocks and template assignment.** Conditions that are compared directly are generated in matched blocks. A block fixes the world, the replicate, the prompt family, and the assigned packages. Within a block, every observation call uses one source template, drawn at random for the block, and the k-th rewrite slot uses the same rewrite template in every condition of the block. Independence between observers then comes from independent seeds, not from different instructions. A sensitivity analysis in which source templates vary independently by observer is reported separately, and it answers a different question about instruction diversity.
6. **Canonical call keys and seeds.** Each call has a canonical key built from the world, the replicate, the block, the call's ancestral role (for example, observer in slot 1, or rewrite at depth 2 of slot 1), and its template assignment. The key never includes the condition. Corresponding ancestral calls in paired conditions therefore share a key, and with it a seed and an exact input. Unused sibling calls receive keys of their own that cannot coincide with any ancestral key. The seed is a stable cryptographic hash of the key, never a language runtime hash that changes between sessions, and is passed through Ollama's `options.seed`. Before the pilot, the dispatcher logs the seed Ollama actually received and passes a replay check. Key reuse across conditions is intentional and works like common random numbers. When two conditions share a call key, the call's input, template, and seed are identical, so its output text is expected to be identical. For example, SD-same's observer shares the key of SI-same's slot 1 observer, so the two conditions share that observation and its first rewrite exactly. The manifest records every reused key, the estimand for each such contrast is a paired one, and texts that share a key are never counted as independent draws. World-grouped splits keep every text that descends from a reused call on one side of any split.
7. **Call manifests.** Each call logs its key, exact prompt, parent-message hashes, model and quantization identifiers, decoding settings, seed, execution position, batching and concurrency settings, retry history, and validation status.
8. **Lineage as a gate, not a filter.** An automated audit checks that every non-source prompt contains exactly its parents' texts and that the realized ancestry of every terminal message equals the specified ancestry. A failure halts collection until the dispatcher is repaired. Trials are never silently excluded, and every failure and rerun is reported with its denominator.
9. **Retry policy.** A call that fails validation is retried at the same node only, up to three times, with seeds derived from its key and the attempt number. The parent texts are not regenerated. Every attempt is kept in the manifest. A node that fails all attempts marks the trial as failed, and failure rates are reported by condition and depth. If failure rates differ by condition, the difference is reported with the affected contrast.
10. **Randomized execution order.** Conditions are interleaved in random order within world blocks, so that server state, model loading, and time of day are not tied to condition. Within a trial, the execution position of every call not constrained by its parents is randomized and logged. For the negative controls this includes the observed branch, as described in Part IV.
11. **The world as the unit of inference.** All evaluation uses world-grouped splits, and all intervals are world-clustered.
12. **Matched output constraints within genre.** Within a genre, all functions share the same length and format instruction. Across genres these constraints differ deliberately, and genre is treated as its own factor.
13. **Decoding settings fixed before the pilot.** Temperature and the other sampling settings are each producer's documented defaults, fixed before the pilot and never tuned on outcomes. Independent seeds yield independent calls, but not necessarily diverse outputs. At low output diversity, independent observers could write nearly identical reports and leave few idiosyncrasies to inherit, which would weaken H4 and H8 without biasing them. The pilot therefore reports pairwise diversity among independent observer texts given the same package, and differences in their conflict resolution, as a feasibility measure.

## Part IV. Difference table

Each contrast is listed with its target property, every other difference between the two conditions that has been identified, and how that difference is handled. A difference is eliminated by design, held fixed, randomized, measured and reported as a mediator, or accepted as part of the target, in which case the contrast is named as a total effect. The GPT review of version 2 added differences to several rows, marked with the defect number from that review.

### The depth confound

Version 1 and the first GPT design compared a synthesis of three independent observations with a synthesis of three rewrites of one observation. The independent inputs were at depth 0 and the dependent inputs at depth 1, so the contrast varied depth along with source independence. The repair rewrites each independent observation once before synthesis, so that all inputs in both conditions sit at depth 1. GPT's review found the repair correct and incomplete, because the independent condition still drew three source templates and the dependent condition one. Principle 5 now removes that difference.

### Study 1

**NC0 versus D0 and NCR1 versus R1 (sibling inertness, level 1).**

| Difference | Handling |
|---|---|
| Extra sibling calls executed in the trial | This is the manipulated factor. Under isolation it has no path to the terminal message. |
| Seed of the terminal call | Held fixed. The terminal's canonical key excludes the condition, so it receives the same seed and input in both arms (defect 7). |
| Seeds of unused siblings | Separate keys that cannot coincide with an ancestral key. |
| Execution position of the observed branch | Counterbalanced (defect 8). The observed branch is fixed before generation, but it runs first, last, or between the siblings in equal proportions. If it always ran first, no sibling state could reach it and the control would pass by construction. |
| Server state (model residency, prompt-prefix cache, batching) | Candidate channels. Concurrency and batching settings are logged, and a siblings-first schedule with concurrent submission is run as a stress case. |
| Retries and validation failures | Logged per call and compared across conditions. |

Paired replay is the operative test. With the same key, the terminal message of NC0 should be byte-identical to that of D0, and the terminal of NCR1 to that of R1. Each control has its own ancestry-matched baseline, because GPU kernels and batching can be nondeterministic and the rate may depend on the number of ancestral calls. D0 is replayed against itself by re-executing its one call. R1 is replayed against itself by re-executing both of its calls, since NCR1 also regenerates the observation from its key.

The pilot includes a dedicated replay set with four execution schedules: observed branch first, between the siblings, last, and all calls submitted concurrently. Each control has 50 pairs per schedule, or 200 in all. Results are reported per schedule. If every pair in a schedule is identical, the one-sided 95% upper bound on its mismatch rate is about 6% (50 pairs), and about 1.5% pooled over the four schedules. These bounds assume independent, homogeneous attempts. The attempts are actually clustered in 10 pilot worlds and two prompt families, so the bounds are reported as conditional on that assumption, alongside per-world counts. If a self-replay rate is below 100%, the comparison is between the control's identity rate and its own baseline rate in the same schedule, with an interval. Replay agreement validates the tested configuration and schedules. It is not the confirmatory distributional equivalence test. A second version with independent seeds supplies that distributional test with a classifier. At pilot size it can only screen for large leaks, and it is reported as such.

**R1, R3, R5 (depth, level 2).** Named as the total effect of adding rewrite stages under one rewrite prompt family.

| Difference | Handling |
|---|---|
| Number of rewrite calls | Target. |
| Number of rewrite templates sampled along the path | Rewrite slots draw templates from one trial-level family. Accepted as part of the depth treatment and reported. |
| Length of the input to the final rewrite | Mediator, measured. |
| Cumulative propositional drift | Mediator and secondary outcome. Monotonic increase is a hypothesis, not an assumption. |
| Failure and retry rates, which may rise with depth (defect 19) | Node-level retries only, under principle 9, so a failure never regenerates the upstream chain. Failure denominators are reported by depth. |

**F1, F2, F3 (partitioned observers under synthesis, level 2).** Version 2 called this fan-in at fixed information. That name was too strong, because the number of inputs to the synthesis node and the number of independent observers change together (defect 1). The contrast is renamed the effect of synthesizing k partitioned observers at a fixed assigned union, for k of 1, 2, and 3. It is not described as isolating fan-in from the number of roots. The independence contrasts below hold fan-in at three while varying roots, so the two factors are partly separated across the design, but not crossed.

Package rule (defect 2). Version 2 required every observer to receive the core event and also described the partition as disjoint, with zero redundancy. Both cannot hold. In version 3 the core event goes to every observer, and the remaining propositions are partitioned across the k observers. The core is therefore repeated k times at the synthesis input. That repetition is accepted as part of the treatment and named.

| Difference | Handling |
|---|---|
| Number of inputs to the synthesis node | Target. |
| Number of independent observers and observation calls | Part of the target, as renamed. |
| Assigned union of propositions | Held fixed. |
| Propositions per observer | Differs by design (the core plus all, half, or a third of the rest). Part of the target. |
| Copies of the core event at synthesis | k. Part of the target, as named above. |
| Co-location of each conflict pair (defect 3) | In F1 both members of every conflict pair go to the single observer. In every F2 and F3 trial, one of the world's two conflict pairs is co-located with a single observer and the other is split across two observers. Which pair is co-located alternates by replicate (pair 1, pair 2, pair 1), and the starting pair alternates between odd- and even-numbered worlds. Over 60 worlds and three replicates, each pair is co-located in exactly 90 of 180 trials per condition, and the 10-world, two-replicate pilot is balanced exactly. Because every trial contains one co-located and one split pair, the co-location effect is estimated within trials at the level of the conflict pair. The realized assignment is checked against the rule before generation. |
| Order of propositions within each package | Randomized per package. |
| Realized coverage, omission, and conflict resolution in the observer texts | Mediators, measured by the proposition matcher. |
| Total input token volume | Measured. |
| Visible count of inputs in the synthesis prompt | Inherent in showing the inputs. Neutral delimiters, with no count stated in the instruction. |
| Single-input synthesis wording (defect 20) | One instruction valid for any k, under principle 1. F1 is dropped if preflight fails. |

**SI-same versus SD-same (input independence, level 2).** SI-same is three observations, each rewritten once, then synthesized (seven calls). SD-same is one observation rewritten three times, then synthesized (five calls). All observers receive the identical package. Independence therefore operates only through independent realization and independent resolution of the conflict pairs.

| Difference | Handling |
|---|---|
| Number of distinct roots | Target. |
| Input depth | Eliminated. All inputs are at depth 1. |
| Number of source templates (defect 4) | Eliminated by principle 5. All observers in a block use one source template. |
| Rewrite templates | Matched by slot across SI and SD within a block. |
| Seeds | SI observers have three keys, and the SD observer shares the key of SI's slot 1 observer, so the two observations are identical. The slot 1 rewrite has the same parent, template, and key in both conditions and is also identical. SI and SD therefore share one of their three synthesis inputs exactly and differ in slots 2 and 3, where SI rewrites two further independent observations and SD rewrites its single observation twice more. Version 3 stated wrongly that no slot matched. The contrast is paired at slot 1 under principle 6. |
| Number of calls (seven versus five) | Inherent in the number of roots. Calls are isolated, so call count has no path to the terminal except through the inputs. |
| Proposition coverage across inputs | Assigned coverage held fixed. Realized coverage measured. |
| Resolution of conflict pairs | Part of the target. Realized resolutions are measured. |
| Convergence or divergence caused by the rewrite stage | A mediator and a possible cause of a null result, not a confound once templates and seeds are matched. Measured as pairwise input similarity before and after the rewrite. |
| Input similarity at synthesis | The mechanism by which the target acts. Measured and reported as a mediator. |
| Total input token volume | Measured. |

**SI-div versus SD-div (level 3).** Named as independent partial-access observers versus a single union-access observer, both followed by matched rewrites and synthesis (defect 11). Each SI observer receives a different assigned package with a fixed overlap, and the SD observer receives their union. Beyond the number of roots, the arms differ in each observer's input length, in which conflicting claims each observer sees together, and in whether one observer can reconcile all the evidence before any rewriting. These differences are part of the named total effect. Assigned and realized coverage per observer, conflicts seen jointly, and input length are measured. A result in this arm is not evidence about independence beyond the access difference. SI-same versus SD-same is the narrower contrast.

**Decay after synthesis (defect 12).** Version 2 generated the downstream conditions as separate trials. In version 3, each SI-same and SD-same synthesis output is the starting record for two continuations, one of one rewrite and one of three, generated as separate branches. The continuations at a given depth use the same rewrite templates in the SI and SD trials of a block. Every SI-versus-SD comparison at depth 0, 1, and 3 is therefore paired at the synthesis output. The estimand is the interaction between ancestry assignment and downstream depth in discriminability, on prespecified outputs and feature families. A declining interaction is reported as a loss of detectability with added rewriting, which is an operational total effect. It is not by itself evidence that specific inherited deviations disappeared, which is checked separately with the propositional features. The decay analysis uses the same-package arm only.

### Study 2

**IND versus DEP versus MIX (shared ancestry among observed messages, level 4).** IND is three observations each rewritten once. DEP is one observation rewritten three times. MIX is one observation rewritten twice plus a second observation rewritten once. Every observed message is one rewrite from one observation.

Package assignment law (defect 5). Under partial access, each world has a fixed pool of assigned packages of equal size, each containing the core event. Two kinds of slot are distinguished (GPT round 3). A generation slot is a fixed canonical position used for package assignment, template matching, and call keys. A presentation position is the order in which the three messages are shown to a reader or classifier. For each set, three packages are drawn from the pool without replacement and assigned to generation slots 1, 2, and 3. In IND, the message in generation slot j is one rewrite of an observer who receives package j. In DEP, all three messages are rewrites of one observer who receives package 1. In MIX, the messages in generation slots 1 and 2 are rewrites of one observer who receives package 1, and the odd message, always in generation slot 3, is a rewrite of an observer who receives package 3. Because the packages are drawn at random, fixing the odd message to generation slot 3 does not tie it to any particular package. The rule does not depend on structure, so the source package of a randomly chosen message has the same marginal distribution in every structure. Under full access every observer receives the whole record. Source templates follow principle 5, and rewrite templates are matched by generation slot across structures within a block. Call keys follow principle 6. The generation slot 1 observation and its rewrite are therefore shared exactly by IND, DEP, and MIX within a block. MIX's odd observation and its rewrite in generation slot 3 are shared exactly with IND's generation slot 3, and DEP's generation slot 2 rewrite is shared exactly with MIX's. Presentation order is permuted at random per set before any analysis, so no presentation position carries information about generation slot or structure.

The two access levels answer different questions (GPT round 2, change 2). The law makes the single-message marginals equal, but not the joint package distribution. Under partial access the three IND observers always receive different packages, whereas DEP's messages all descend from one package and MIX's shared pair from one package. Set-level similarity under partial access can therefore reveal shared factual access even when no idiosyncrasy is inherited. The partial-access contrast is named as the total effect of source sharing combined with shared assigned access. The full-access arm is the primary test of inherited deviations, because there every observer receives the same record, and access cannot differ by structure. Its IND sets also supply the independent same-package null that the shared-deviation methods require. Under partial access no such null exists within the IND cells, because their packages always differ. The excess shared deviation in the partial arm is therefore reported against the full-access null only, and labeled as not identified relative to a same-package null.

| Difference | Handling |
|---|---|
| Shared roots among the three messages | Target. |
| Number of observation calls (three, one, two) | Inherent. Not visible in any single message under isolation. |
| Marginal distribution of a single message | Equal by the package law and template matching. Tested by H7 within strata (defect 15). |
| Position of the odd message in MIX | Eliminated. The odd message has a fixed generation slot, and presentation order is permuted at random per set. No slot labels are shown. |
| Branch-indexed formatting or identifiers | Eliminated. No node prompt receives a branch index, and observed messages carry no identifiers. |
| Shared errors from the shared producer model | Not shared ancestry. Estimated from full-access IND sets in training worlds, conditioned on genre, producer, and attribution arm (defect 16). No same-package null exists in partial-access IND sets, as explained above. |
| Shared assigned package under partial access (round 2, N1) | Part of the named partial-access total effect. Not attributed to inheritance. |
| Upstream realizations across attribution arms (defect 13) | Held fixed. The generative concealment arm reuses the neutral arm's observation texts and changes only the rewrite instruction. The stripped arm is derived from the neutral rewrites. All three arms of a set share their observation texts. |
| Whether stripping removes attribution without changing content (defect 14) | Handled by the attribution field defined below. Stripping deletes that field only. Marker presence, field validity, stripping success, and proposition-matcher equivalence before and after stripping are reported by structure and arm. Attribution phrased inside the prose is left in place and counted. |
| Observer access (full or assigned partial package) | Crossed as a factor. Within each access level the package law is identical across structures. |

Attribution field (GPT round 2, change 4). In every world, each proposition carries an in-world source, such as a maintenance log, a shift supervisor, or a sensor record, and the world's source inventory lists them. The attribution field is a delimited final line, `Sources:`, followed by the in-world sources the message's claims rest on, chosen from that inventory. The observer instruction asks for the field. The neutral rewrite instruction asks the rewriter to carry the field forward and revise it to match what the rewrite retains. The generative concealment instruction asks for the field to be omitted and for source cues to be removed from the prose. The field never contains a pipeline identifier, such as a node, branch, slot, observer, or root identifier, or any reference to other messages. It therefore discloses only world content, which is identical across structures. A field shared between messages is inherited from a shared ancestor in the same way as any other content, and is part of the target. An entry outside the inventory is invalid and is counted. The field is generated by the model rather than appended mechanically, because attribution as written by the producer is the object of study, and a deterministic field would carry no production information. Its permitted content is declared in advance and checked mechanically.

H10's primary analysis includes every assigned set, whatever the field's presence or validity, so that the contrast is conditioned on assignment and not on compliance. The analysis restricted to sets in which the field was present and valid and stripping left the propositions unchanged is secondary, and is reported with its selection rate by structure and arm.

### Method comparisons

The reader-versus-classifier comparison is restricted to methods that receive exactly the same input, which is message text only, with labeled training-world examples supplied in context to the reader. The world-anchored and world-free methods of H10 and H11 use additional information (the world record, the matcher's alignment, or an independent reference corpus) and are reported separately, with the anchored method as an upper reference (defect 17). The remaining difference between in-context examples and fitted parameters is stated as such. The method comparison is secondary in this design.

## Part V. Conditions and hypotheses

### Study 1

Seventeen conditions. Observers receive assigned packages under the rules in Part IV, and every package includes the core event.

| ID | Structure | Producer calls per block |
|---|---|---|
| D0 | Observe, terminal | 1 |
| NC0 | Observe, plus two unused sibling observations | 3 |
| R1, R3, R5 | Observe, then 1, 3, or 5 rewrites | 2, 4, 6 |
| NCR1 | Observe, rewrite, plus two unused sibling rewrites | 4 |
| F1, F2, F3 | Synthesis of 1, 2, or 3 partitioned observers | 2, 3, 4 |
| SI-same, SD-same | Depth-matched independence contrast, identical packages | 7, 5 |
| SI-div, SD-div | Depth-matched independence contrast, diverse packages | 7, 5 |
| SI-same+1, SD-same+1 | One-rewrite branch from the SI-same or SD-same synthesis output | 1, 1 |
| SI-same+3, SD-same+3 | Three-rewrite branch from the same synthesis output | 3, 3 |

The circulation condition of version 1 remains removed. It can return as an exploratory study with a matched two-input control.

- **H1, sibling inertness.** NC0 is equivalent to D0, and NCR1 is equivalent to R1, under the execution schedules tested. In the pilot this is an engineering check. In each execution schedule, paired replay identity in NC0 must not fall below the D0 self-replay rate, and identity in NCR1 must not fall below the R1 self-replay rate, by more than a margin fixed before the pilot, judged by an interval within that schedule. The distributional test with independent seeds is a screen for large leaks in the pilot. In the confirmatory study it is an equivalence test with a margin and sample size fixed by simulation from pilot variance components. A failed replay check halts the study until the channel is found. A failed distributional screen with a passing replay check is treated as insufficient precision or a possible leak and investigated before the study continues.
- **H2, depth.** The rewrite-stage total effect is recoverable above chance. Drift is reported by depth without assuming monotonicity.
- **H3, partitioned observers.** F1, F2, and F3 are distinguishable at a fixed assigned union. The result is described as the effect of the partition-and-synthesis procedure, not of fan-in alone.
- **H4, input independence.** SI-same is distinguishable from SD-same with source and rewrite templates matched (level 2). SI-div is distinguishable from SD-div, reported as the access total effect named in Part IV (level 3). The predicted mechanism is that independent observers differ more in realization and conflict resolution, and that the synthesis carries that variation as qualified or competing claims. Input similarity and realized resolution are reported as mediators.
- **H5, detectability after synthesis.** The interaction between ancestry assignment and downstream depth in discriminability is negative, so the SI-same versus SD-same contrast is harder to detect after one and three rewrites.
- **H6, transfer.** Classifiers trained on prompt family A in training worlds retain discrimination on family B in test worlds. The comparison is with family A in the same test worlds, so that the family shift is separated from the world shift (defect 18). For producer transfer, both producers run on identical worlds, packages, and blocks, and the comparison is again with the training producer on the same test worlds.

### Study 2

Three structures crossed with two access levels (full record, assigned partial packages) and three attribution arms (neutral, generative concealment, stripping). The concealment arm reuses the neutral arm's observation texts, and the stripping arm is derived from the neutral rewrites with no producer calls.

- **H7, single-message leakage.** A classifier given one randomly chosen message per set does not distinguish IND, DEP, and MIX beyond a prespecified margin. It is tested within each access, attribution, and prompt-family stratum and pooled, with the worst stratum reported alongside the pooled result. A pass means no singleton cue of the tested size was detected in the tested strata, not that the marginal distributions are equal.
- **H8, relational gain.** Two baselines are used (defect 6). The first is an order-invariant aggregate of the three single-message predictions. The second sees all three texts but pools per-message features by permutation-invariant operations (mean and maximum) with no cross-message comparison, and is trained on set labels. Relational gain is the improvement of a model with pairwise features over the second baseline. Both set-level labels and pairwise shared-source labels are evaluated. Random assignment identifies the effect of the specified production structure on the joint distribution of observed messages. The incremental score from pairwise features measures predictive information beyond the pooled-feature baseline. Its attribution to inherited deviations requires the full-access arm and the shared-deviation analyses, and the features that carry it are identified by family ablation. Under partial access, a gain is reported as evidence of shared access or shared ancestry, without a claim about which carried it.
- **H9, access.** Pairwise dependence detection is reported under both access levels. Partial access is predicted to increase it, as a hypothesis with possible exceptions.
- **H10, attribution.** Over all assigned sets, stripping reduces detection by the prompted reader and leaves the world-anchored shared-deviation method unchanged within a prespecified margin. The same comparison on the compliant, semantically verified subset is secondary. Generative concealment is compared with stripping on the same observation texts, which estimates the effect of the concealment instruction on content.
- **H11, world-free method.** The world-free method's performance is stated as the fraction of above-chance discrimination it retains, (AUC_free − 0.5) / (AUC_anchored − 0.5), estimated from paired predictions on the same sets, with a world-cluster bootstrap interval. The ratio is computed only if the lower bound of the anchored method's 95% interval is at least 0.60. Below that threshold the denominator is too small for the ratio to be stable, and only the two AUCs are reported. Both AUCs and their intervals are reported in every case. The fraction that counts as support is fixed before the confirmatory study. The world-free null for excess similarity comes from independent same-event reports in training worlds, conditioned as in the Study 2 table.

## Part VI. Measurement

The original 14 features are retained as a baseline. New features are grouped into four prespecified families: formal (length and lexical), attributional (source, evidential, hedge, and uncertainty markers), propositional (preservation, omission, alteration, qualification, unsupported addition, conflict resolution, order), and relational (shared deviations, rare word-sequence overlap, order similarity, excess embedding similarity). The families are operational groupings, not separate latent constructs. Named entities, for example, are counted as form and also carry content. Incremental value is tested by family ablation, and no family is claimed to measure a construct without a manipulation that targets it.

The proposition matcher must be validated before confirmatory use. A blinded sample of messages, stratified across conditions, genres, and producers, is annotated by hand for preservation, omission, alteration, and conflict resolution. Disagreement between matcher and annotation is reported by condition, because a matcher that treats synthesis outputs differently from relay outputs would manufacture a structural result. The same sample includes stripped and unstripped pairs, to check that stripping leaves the matcher's output unchanged. Who does the annotation is an open decision for Eric.

A generic sentence-embedding classifier and a flexible text classifier are reported as stress tests for leakage, with model selection confined to training folds.

## Part VII. Worlds, genre, and scale

**Worlds.** Seventy new worlds under a revised schema, each with about 20 propositions, several numeric details (times, counts, durations), and two conflicting pairs. The original worlds have 8 propositions and one conflict pair, and preservation averaged 0.96 in the original run, which leaves little room for inherited variation. Ten worlds are used for the pilot and never enter confirmatory tests. Sixty are confirmatory. The original 20 worlds are not reused, because mixing schemas would confound world type with world source. Eric reviews the worlds before generation. Each world also carries its Study 1 partitions, its conflict co-location assignments, its Study 2 package pool, and its in-world source inventory for the attribution field.

**Genre.** The primary genre is the incident report. The pilot includes a second genre (news brief) on R1 versus R3 and SI-same versus SD-same. Gate 3 is restricted to those two contrasts (defect 10). Full genre crossing is contingent on the pilot.

**Producers and readers.** The primary producer is llama3.1:8b. A second producer family is used for H6. Readers come from a different family than the producer. All models run locally.

**Planning estimate.** These figures assume 9 seconds per call, the average from the original run. Synthesis calls with three inputs will be slower, and the pilot replaces this assumption with measured latency by node function and producer. Study 1 now needs 61 producer calls per world and replicate, against 85 in version 2, because the decay conditions branch from existing synthesis outputs. Study 2 needs 24 producer calls per world, replicate, and access level (15 for the neutral arm and 9 rewrites for the concealment arm), against 30, because the concealment arm reuses the neutral observation texts.

| Component | Units | Producer calls | Reader calls | Hours at 9 s per call |
|---|---|---|---|---|
| Pilot, Study 1 (10 worlds, 2 replicates) | 340 messages | 1,220 | not budgeted | 3.1 |
| Pilot, second-genre subset (R1, R3, SI-same, SD-same) | 80 messages | 360 | not budgeted | 0.9 |
| Pilot, replay set (4 schedules × 50 pairs per control, with D0 and R1 self-replays) | 400 control pairs, 400 self-replays | 2,600 | none | 6.5 |
| Pilot, Study 2 | 240 generated sets plus 120 stripped sets | 960 | not budgeted | 2.4 |
| Study 1, primary producer (60 worlds, 3 replicates) | 3,060 messages | 10,980 | 6,120 | 42.8 |
| Study 1, second producer (H6) | 3,060 messages | 10,980 | none | 27.5 |
| Study 2 (60 worlds, 3 replicates) | 2,160 generated sets plus 1,080 stripped sets | 8,640 | 6,480 | 37.8 |

Each replay unit, meaning one NC0 pair, one NCR1 pair, and their two self-replays, costs 13 calls: D0 (1) and NC0 (3), R1 (2) and NCR1 (4), one D0 re-execution (1), and one R1 re-execution (2). The D0 and R1 runs in each unit serve as the reference for both the control comparison and the self-replay, and that dependence is reported. Two hundred units cost 2,600 calls. The pilot is about 5,140 producer calls, or about 12.9 hours. The confirmatory program is about 108 serial machine hours, or about four and a half days, before failures and reruns, against 135 hours in version 2. Replicate counts are planning values and are confirmed by simulation from pilot variance components. Machine time is not the binding cost. World construction, prompt-pool drafting, matcher annotation, and audit review require human time that this table does not include.

## Part VIII. Analysis plan

- World-grouped cross-validation with nested selection, or a final untouched world set, so that no model selection or calibration uses test worlds.
- Accuracy, balanced accuracy, macro-F1, multiclass Brier score, and log loss, with world-cluster bootstrap intervals. Invalid reader outputs are retained under a prespecified policy.
- Contrasts estimated as differences in AUC or accuracy, with intervals that account for nesting of messages in blocks, pairs in sets, sets in worlds, and shared synthesis outputs in the decay analysis.
- Per-world and per-condition results reported alongside pooled results, with counts for every subgroup, including retry and failure counts.
- The estimand is stated for each test: the performance of a fixed trained model on new worlds, or the performance of a retrained pipeline.
- Preregistration after the pilot, with pilot data excluded from confirmatory tests and any amendment versioned.

## Part IX. Gates and what each outcome means

Each gate authorizes or stops the next stage of work. No gate outcome is itself an empirical conclusion of the paper.

| Gate | Test | If it passes | If it fails |
|---|---|---|---|
| 1 | Lineage of the original study documented against its code, source-to-record correspondence checked, and the new dispatcher's lineage audit and seed replay passed in preflight | The original lineage is documented, and the new pipeline is cleared to generate. Reproduction of the original numbers is a separate check on the deposited data. Neither establishes the original structural interpretation, which the lineage findings already contradict (defect 21) | The defect is repaired before any generation |
| 2 | H1 replay check per execution schedule against the ancestry-matched self-replay baselines, with the distributional screen | Isolation is verified for the tested configuration and schedules, within the stated bounds. This is not a finding of distributional equivalence. The confirmatory equivalence test proceeds with a simulated sample size | A replay failure in any schedule halts collection until the channel is found. A screen failure with a passing replay check is investigated as possible leak or low precision before continuing |
| 3 | R1 versus R3 or SI-same versus SD-same survives the change of prompt family and genre in the pilot, after the matching checks for that contrast have passed | The passing contrast proceeds to confirmatory scale. Survival is a condition on generalization, not identification, which rests on the matching in Part IV (defect 23). H3 is reported from the pilot as a diagnostic and proceeds to confirmatory scale on its own pilot result | The failing contrast is narrowed or redesigned. A pilot failure is not evidence that the property is unrecoverable. If both fail, a project decision declared here in advance takes effect. Confirmatory generation for single-message contrasts stops, and the paper is reframed around the negative controls, Study 2, and the protocol-confound demonstration. That decision reflects the cost of proceeding under unfavorable pilot evidence. It is not a finding that single-message structural properties are unrecoverable, and the paper reports the pilot results with their intervals as inconclusive |
| 4 | H7 within strata, then H8 against both baselines, in the pilot | Study 2 proceeds to confirmatory scale | The two failures are handled separately (defect 22). An H7 failure triggers diagnosis and repair of the singleton cue before any set-level claim. An H8 failure is reported as no detected pilot gain for the tested features, with its interval. Only an adequately powered confirmatory result could bound the relational information |

The full run starts only after Gates 1 to 4 have been assessed. The design is frozen and preregistered at that point.

## Part X. Claims

If the gates pass and the predictions hold, the paper can claim, within language-model pipelines and the tested worlds, genres, producers, and execution schedules, that graph changes outside a message's ancestry leave it unchanged, that specified ancestral procedures leave recoverable differences under matched node functions and templates, and that shared ancestry among several messages leaves relational evidence beyond what the individual texts carry. The last claim rests on the full-access arm. Under partial access, the claim covers shared access and shared ancestry together. Each claim is attached to its level in the hierarchy of Part II and to the contrast name in Part IV. The original study appears as a demonstration that protocol-confounded designs report high accuracy for properties the observed message cannot contain. The compound defect is reported as a versioned correction, not as a boundary on recovering compositions.

Transfer to human communication is not claimed without the field anchor.

## Part XI. Field anchor (open decision)

The label is chosen before the corpus. GPT's critique of version 1 reports checking three candidates, and Claude has not independently re-verified its findings. According to that check, the METER corpus labels newspaper articles as derived or not derived from Press Association copy, which supports a source-to-derivative reuse test but says nothing about independence among newspaper articles. The artificial manuscript traditions used in computer-assisted stemmatology have known copying trees, which makes them the closest match to shared-ancestry inference, but the challenge data page restricts further use to cases with organizer permission. The press-release and news data of Sumner and colleagues (2014) trace individual claims, not document ancestry. These are three different validity checks. If none can be licensed with labels that match a Study 2 outcome, the field claim is omitted.

## Part XII. Deferred

- **Random-graph sweep.** Deferred until after Gate 3. If added, its size must be specified as a total number of graphs with a stated reuse rule across worlds and a budget from the realized call-count distribution.
- **Circulation.** Exploratory, with a matched two-input control.
- **Redundant-package fan-in variant.** After the pilot, if H3 passes.
- **Crossing roots with fan-in.** A design in which k inputs from one root and k inputs from k roots are compared at each k would separate the two factors that H3 bundles. It is deferred because SI-same versus SD-same already supplies the k = 3 comparison.
- **Genre crossing for F1, F2, F3.** After the pilot, if Gate 3 passes for another contrast.

## Open decisions for Eric

1. Whether to proceed to Gate 1 completion and the pilot on this design.
2. Who annotates the matcher validation sample.
3. Whether to pursue permissions for a field-anchor corpus, and for which label.
4. Which second producer family to use.
5. Whether an outside methodologist reviews the design before the freeze.

## Disposition of the GPT review of version 2

| Defect | Disposition | Where |
|---|---|---|
| 1. F1–F3 bundle fan-in with root count | Accepted. Contrast renamed. Crossing deferred | Part IV F rows, H3, Part XII |
| 2. Core event contradicts zero redundancy | Accepted. Core shared, remainder partitioned, k-fold core named | Part IV F rule |
| 3. Fixed union does not fix realized evidence | Accepted. Conflict co-location balanced in F2 and F3, realized content as mediators | Part II, Part IV F rows |
| 4. SI and SD differ in source-template draws | Accepted. One source template per block, rewrite templates matched by slot | Principle 5, Part IV SI rows |
| 5. Study 2 package law unspecified | Accepted. Slot-based condition-blind law | Part IV Study 2 |
| 6. H8 baseline | Accepted in part. Information-matched set baseline and pairwise labels added. Claude does not accept that a gain would be ambiguous about ancestry, because structure is randomized with event content fixed, and GPT's own repair notes the same point. Priority lowered from high to medium | H8 |
| 7. Seed formula does not guarantee paired seeds | Accepted. Canonical keys exclude condition | Principle 6, Part IV NC rows |
| 8. Terminal-first order makes the control vacuous | Accepted. Position counterbalanced, siblings-first stress case | Principle 10, Part IV NC rows |
| 9. Pilot cannot establish equivalence | Accepted. Gate 2 is an engineering check, 100-pair replay set added, equivalence moved to the confirmatory study | Part IV, H1, Gate 2 |
| 10. Fan-in not crossed with genre in the pilot | Accepted. Gate 3 restricted to the two crossed contrasts | Part VII, Gate 3 |
| 11. SI-div label | Accepted. Renamed as the access total effect. Version 2 had already placed it at level 3 | Part IV SI-div |
| 12. Decay not matched at downstream inputs | Accepted. Continuations branch from shared synthesis outputs, estimand is an interaction | Part IV decay, H5 |
| 13. Attribution arms do not share upstream texts | Accepted. Concealment reuses neutral observation texts | Part IV Study 2 |
| 14. Stripping not guaranteed to preserve content | Accepted. Delimited attribution field, verified stripping | Part IV Study 2, H10, Part VI |
| 15. Pooled H7 can hide leakage | Accepted, merged with 5. Stratified probes with worst stratum reported | H7 |
| 16. Shared-error null and H11 scale | Accepted. Conditioned null, baseline-adjusted fraction | Part IV Study 2, H11 |
| 17. Method comparison not information-matched | Accepted in part. The text-only comparison in version 2 was already matched. The anchored and world-free methods are now stated to be separate | Method comparisons |
| 18. Transfer mixes family and world shift | Accepted in part. Families were already assigned by trial in every world. Within-family baseline on test worlds added | H6 |
| 19. Retry policy unspecified | Accepted | Principle 9, Part IV R rows |
| 20. Single-input synthesis | Accepted. One instruction for any k, preflight, F1 dropped if it fails | Principle 1, Part IV F rows |
| 21. Gate 1 overstates what it verifies | Accepted | Gate 1 |
| 22. Gate 4 failure branches | Accepted | Gate 4 |
| 23. Gate 3 robustness is not identification | Accepted, merged with 4 and 10 | Gate 3 |

## Disposition of the GPT review of version 3

GPT's verdicts on the 23 round 1 repairs were resolved for defects 1, 2, 4, 7, 8, 10 to 13, 15, and 17 to 22, and resolved on condition for 3, 5, 6, 9, 14, 16, and 23. All conditions are accepted and applied.

| Item | Change in version 4 | Where |
|---|---|---|
| Change 1 (defect 3, N2). Co-location balance infeasible with three replicates | One co-located and one split pair in every trial, alternating by replicate and world, exact balance, audit before generation | Part IV F rows |
| Change 2 (defect 5, N1). Partial access shares packages by structure | Partial-access contrast named as access plus ancestry, full access primary for inheritance, no same-package null claimed for partial IND | Part IV Study 2, H8, Part X |
| Change 3 (defect 6). H8 causal sentence | GPT's wording adopted | H8 |
| Change 4 (defect 14, N4). Attribution field semantics and selection | In-world source inventory only, no pipeline identifiers, declared and checked. Primary H10 analysis on all assigned sets | Part IV Study 2, H10 |
| Change 5 (defect 9, N3). Replay baselines, schedules, budget | D0 and R1 self-replays, four schedules × 50 pairs, per-schedule bounds stated as conditional, 13 calls per unit | Part IV NC, H1, Gate 2, Part VII |
| Change 6 (defects 16, 23, N7, N8). H11 denominator and Gate 3 both-fail branch | Anchored lower bound of at least 0.60, raw AUCs always reported. Both-fail branch declared as a project decision | H11, Gate 3 |
| N5. Low output diversity | Decoding fixed at producer defaults before the pilot, observer diversity reported | Principle 13 |
| N6. Common random numbers | Key reuse declared and recorded, paired estimands, and the version 3 error about slot 1 corrected | Principle 6, Part IV SI rows, Study 2 |

GPT's replay figure of 1,600 calls assumed independently generated self-replay pairs. Version 4 instead re-executes the reference calls of each unit, and doubles the replay set to give per-schedule bounds, for 2,600 calls.

## Changes from version 3

- Applied GPT's six conditions for freeze and its two new issues, as tabulated above.
- Corrected the version 3 statement that SI and SD share no exact input. They share slot 1.
- After GPT's round 3 confirmation, separated generation slots from presentation positions in Study 2, fixed MIX's odd message to generation slot 3 with package 3, and listed the texts shared exactly across IND, DEP, and MIX.
- Added principle 13 on decoding settings.
- Recomputed the pilot at about 12.9 hours. The confirmatory program is unchanged at about 108 hours.

## Changes from version 2

- Added the disposition table above.
- Added matched blocks with shared source templates, canonical call keys that exclude condition, a node-level retry policy, and within-trial randomized execution order.
- Counterbalanced the observed branch's position in the negative controls and added a 100-pair replay set to the pilot.
- Renamed the F1–F3 contrast, resolved the core-event contradiction, and balanced conflict co-location.
- Renamed SI-div as an access total effect.
- Branched the decay conditions from the SI-same and SD-same synthesis outputs and restated H5 as an interaction.
- Specified the Study 2 package law, paired the attribution arms on shared observation texts, and introduced a delimited attribution field for stripping.
- Added a second H8 baseline and pairwise labels, stratified H7, and defined the H11 estimand.
- Separated the text-only method comparison from the anchored and world-free methods.
- Restated all four gates as authorizations rather than conclusions, restricted Gate 3 to the contrasts crossed with genre, and split the Gate 4 failure branches.
- Recomputed the budget: pilot about 9.4 hours, confirmatory program about 108 hours.

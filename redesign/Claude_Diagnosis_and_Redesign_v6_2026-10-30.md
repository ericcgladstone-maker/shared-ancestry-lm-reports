# Production Structure Recovery from Communication Artifacts: Study Design, Version 6

Prepared by Claude, 2026-10-30. This is the design proposed for freezing and preregistration. It revises version 5 in response to two pre-results referee reviews, `Referee Review, Claude (2026-10-30).md` (written by a fresh agent that saw only version 5, the npj decision letter, and the submitted manuscript) and `Referee Review, GPT (2026-10-30)`. Both recommended major revision. The disposition of every referee objection is in `Referee_Disposition_v6_2026-10-30.md`. The record of how the design reached version 5 is in versions 1 to 5 and the GPT reviews in this folder, and it is not repeated here.

The design is executed once. It is built and preregistered, verified on 10 reserved worlds whose hypothesis outcomes are never computed, and then run in full. Every planned contrast is reported, whatever its result.

What the study can show is bounded. It is a controlled identifiability study of small message-production graphs built from language-model calls. It asks which properties of a message's production history leave recoverable traces in the message, and which relations among several messages reveal shared ancestry, when node instructions are matched. It does not test general recovery of network topology, and it makes no claim about human communication.


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

1. **Three node functions with shared prompt pools.** Every node observes the world, rewrites one incoming message, or synthesizes one or more incoming messages. Each function has one pool of prompt variants used in all conditions. No prompt names the motif, mentions downstream use, or refers to the number or role of other nodes. The synthesis instruction must be valid for any number of inputs from one upward. It does not ask the model to compare or reconcile sources, and the inputs appear as a list separated by neutral delimiters with no stated count. The instruction is preflighted on 50 outputs each for one, two, and three inputs during build verification. If more than 5% of single-input outputs refer to other or missing sources, or compare sources, F1 is dropped and H3 compares F2 with F3. This is the only design change the verification run can trigger apart from the schedule rule in Part IV.
2. **Same-function contrasts.** Wherever possible, a contrast compares conditions whose terminal node performs the same function. Fan-in is varied under the synthesis function, never by comparing synthesis with rewriting.
3. **Assigned input packages.** The propositions each observer receives are assigned by a stated, condition-blind rule, not left to a sampling rule inside the generator. This allows information content to be held fixed or varied deliberately. The rules for each study are given in Part IV.
4. **Trial-level prompt families.** Each prompt pool is split into two families, A and B. Every node in a trial draws from the same family, assigned at random by trial, so both families occur in every world. The transfer test trains on one family and tests on the other. Each family holds six templates for each node function, so each function has twelve templates in all. Templates are a sampled factor, and intervals account for them (Part VIII).
5. **Matched blocks and template assignment.** Conditions that are compared directly are generated in matched blocks. A block fixes the world, the replicate, the prompt family, and the assigned packages. Within a block, every observation call uses one source template, drawn at random for the block, and the k-th rewrite slot uses the same rewrite template in every condition of the block. Independence between observers then comes from independent seeds, not from different instructions. A sensitivity analysis in which source templates vary independently by observer is reported separately, and it answers a different question about instruction diversity.
6. **Canonical call keys and seeds.** Each call has a canonical key built from the world, the replicate, the block, the call's ancestral role (for example, observer in slot 1, or rewrite at depth 2 of slot 1), and its template assignment. The key never includes the condition. Corresponding ancestral calls in paired conditions therefore share a key, and with it a seed and an exact input. Unused sibling calls receive keys of their own that cannot coincide with any ancestral key. The seed is a stable cryptographic hash of the key, never a language runtime hash that changes between sessions, and is passed through Ollama's `options.seed`. In the verification run, the dispatcher logs the seed Ollama actually received and passes a replay check. Key reuse across conditions is intentional and works like common random numbers. When two conditions share a call key, the call's input, template, and seed are identical, so its output text is expected to be identical. For example, SD-same's observer shares the key of SI-same's slot 1 observer, so the two conditions share that observation and its first rewrite exactly. The manifest records every reused key, the estimand for each such contrast is a paired one, and texts that share a key are never counted as independent draws. World-grouped splits keep every text that descends from a reused call on one side of any split. In the full run, every call that is checked for identity across conditions is compared byte for byte, and any mismatch is logged and reported. One exception to key sharing is deliberate. In the full run, the terminal calls of NC0 and NCR1 receive keys that include the condition, so their seeds differ from those of D0 and R1. Shared terminal keys would make NC0 and D0 byte-identical by construction once replay is deterministic, and H1's distributional test would then be empty. Shared terminal keys are used only in the replay set.
7. **Call manifests.** Each call logs its key, exact prompt, parent-message hashes, model and quantization identifiers, decoding settings, seed, execution position, batching and concurrency settings, retry history, and validation status.
8. **Lineage as a gate, not a filter.** An automated audit checks that every non-source prompt contains exactly its parents' texts and that the realized ancestry of every terminal message equals the specified ancestry. A failure halts collection until the dispatcher is repaired. Trials are never silently excluded, and every failure and rerun is reported with its denominator.
9. **Retry policy.** A call that fails validation is retried at the same node only, up to three times, with seeds derived from its key and the attempt number. The parent texts are not regenerated. Every attempt is kept in the manifest. A node that fails all attempts marks the trial as failed, and failure rates are reported by condition and depth. If failure rates differ by condition, the difference is reported with the affected contrast. An output passes validation if it is nonempty, its length is within half to one and a half times the genre's target length, it contains none of a fixed list of meta-commentary patterns (for example, references to instructions, to being a model, or to other inputs), and, in Study 2, its attribution line parses. Because shared-key calls are deterministic, a call that fails in one condition fails identically in every condition that shares its key, so retries do not break pairing.
10. **Randomized execution order.** Conditions are interleaved in random order within world blocks, so that server state, model loading, and time of day are not tied to condition. Within a trial, the execution position of every call not constrained by its parents is randomized and logged. For the negative controls this includes the observed branch, as described in Part IV.
11. **The world as the unit of inference.** All evaluation uses world-grouped splits, and all intervals are world-clustered.
12. **Matched output constraints within genre.** Within a genre, all functions share the same length and format instruction. Across genres these constraints differ deliberately, and genre is treated as its own factor.
13. **Decoding settings fixed now.** Temperature and the other sampling settings are each producer's documented defaults, fixed before any generation and never tuned. Independent seeds yield independent calls, but not necessarily diverse outputs. At low output diversity, independent observers could write nearly identical reports and leave few idiosyncrasies to inherit, which would weaken H4 and H8 without biasing them. The verification run reports pairwise diversity among independent observer texts given the same package, and differences in their conflict resolution, as a description of the material. Low diversity is reported, not repaired.

## Part IV. Difference table

Each contrast is listed with its target property, every other difference between the two conditions that has been identified, and how that difference is handled. A difference is eliminated by design, held fixed, randomized, measured and reported as a mediator, or accepted as part of the target, in which case the contrast is named as a total effect. The GPT review of version 2 added differences to several rows, marked with the defect number from that review.

### The depth confound

Version 1 and the first GPT design compared a synthesis of three independent observations with a synthesis of three rewrites of one observation. The independent inputs were at depth 0 and the dependent inputs at depth 1, so the contrast varied depth along with source independence. The repair rewrites each independent observation once before synthesis, so that all inputs in both conditions sit at depth 1. GPT's review found the repair correct and incomplete, because the independent condition still drew three source templates and the dependent condition one. Principle 5 now removes that difference.

### Study 1

**NC0 versus D0 and NCR1 versus R1 (sibling inertness, level 1).**

| Difference | Handling |
|---|---|
| Extra sibling calls executed in the trial | This is the manipulated factor. Under isolation it has no path to the terminal message. |
| Seed of the terminal call | In the replay set, held fixed: the terminal's key excludes the condition, so it receives the same seed and input in both arms. In the full run, the NC0 and NCR1 terminals receive condition-specific keys (principle 6), so H1 compares independent draws. |
| Seeds of unused siblings | Separate keys that cannot coincide with an ancestral key. |
| Execution position of the observed branch | Counterbalanced. The observed branch is fixed before generation, but it runs first, last, or between the siblings in equal proportions. If it always ran first, no sibling state could reach it and the control would pass by construction. |
| Server state (model residency, prompt-prefix cache, batching) | Candidate channels. Concurrency and batching settings are logged, and a siblings-first schedule with concurrent submission is run as a stress case. |
| Retries and validation failures | Logged per call and compared across conditions. |

Paired replay is the operative test. With the same key, the terminal message of NC0 should be byte-identical to that of D0, and the terminal of NCR1 to that of R1. Each control has its own ancestry-matched baseline, because GPU kernels and batching can be nondeterministic and the rate may depend on the number of ancestral calls. D0 is replayed against itself by re-executing its one call. R1 is replayed against itself by re-executing both of its calls, since NCR1 also regenerates the observation from its key.

The verification run includes a dedicated replay set with four execution schedules: observed branch first, between the siblings, last, and all calls submitted concurrently. Each control has 50 pairs per schedule, or 200 in all. Results are reported per schedule. If every pair in a schedule is identical, the one-sided 95% upper bound on its mismatch rate is about 6% (50 pairs), and about 1.5% pooled over the four schedules. These bounds assume independent, homogeneous attempts. The attempts are actually clustered in the 10 verification worlds and two prompt families, so the bounds are reported as conditional on that assumption, alongside per-world counts.

Determinism is a build requirement, not a result. The full run uses only execution schedules whose D0 and R1 self-replays are 100% identical in the verification run. If a schedule's self-replay falls short, the dispatcher's settings (for example, concurrency, batching, or thread count) are corrected and the replay set for that schedule is rerun. A schedule that cannot be made deterministic is excluded from the full run, and the exclusion is reported. Under a deterministic schedule, any NC0 or NCR1 mismatch is an implementation defect that is traced and fixed before the full run, and the replay set is rerun after the fix. Replay agreement validates the configuration and schedules used. It is not the distributional test of H1, which runs on the full data with independent seeds.

**R1, R3, R5 (depth, level 2).** Named as the total effect of adding rewrite stages under one rewrite prompt family.

| Difference | Handling |
|---|---|
| Number of rewrite calls | Target. |
| Number of rewrite templates sampled along the path | Rewrite slots draw templates from one trial-level family. Accepted as part of the depth treatment and reported. |
| Length of the input to the final rewrite | Mediator, measured. |
| Cumulative propositional drift | Mediator and secondary outcome. Monotonic increase is a hypothesis, not an assumption. |
| Failure and retry rates, which may rise with depth | Node-level retries only, under principle 9, so a failure never regenerates the upstream chain. Failure denominators are reported by depth. |

**F1, F2, F3 (partitioned observers under synthesis, level 2).** Version 2 called this fan-in at fixed information. That name was too strong, because the number of inputs to the synthesis node and the number of independent observers change together. The contrast is renamed the effect of synthesizing k partitioned observers at a fixed assigned union, for k of 1, 2, and 3. It is not described as isolating fan-in from the number of roots. The independence contrasts below hold fan-in at three while varying roots, so the two factors are partly separated across the design, but not crossed.

Package rule. Version 2 required every observer to receive the core event and also described the partition as disjoint, with zero redundancy. Both cannot hold. In version 3 the core event goes to every observer, and the remaining propositions are partitioned across the k observers. The core is therefore repeated k times at the synthesis input. That repetition is accepted as part of the treatment and named.

| Difference | Handling |
|---|---|
| Number of inputs to the synthesis node | Target. |
| Number of independent observers and observation calls | Part of the target, as renamed. |
| Assigned union of propositions | Held fixed. |
| Propositions per observer | Differs by design (the core plus all, half, or a third of the rest). Part of the target. |
| Copies of the core event at synthesis | k. Part of the target, as named above. |
| Co-location of each conflict pair | In F1 both members of every conflict pair go to the single observer. In every F2 and F3 trial, one of the world's two conflict pairs is co-located with a single observer and the other is split across two observers. Which pair is co-located alternates by replicate (pair 1, pair 2, pair 1), and the starting pair alternates between odd- and even-numbered worlds. Over 60 worlds and three replicates, each pair is co-located in exactly 90 of 180 trials per condition, and the 10-world verification run is balanced across worlds. Because every trial contains one co-located and one split pair, the co-location effect is estimated within trials at the level of the conflict pair. The realized assignment is checked against the rule before generation. |
| Order of propositions within each package | Randomized per package. |
| Realized coverage, omission, and conflict resolution in the observer texts | Mediators, measured by the proposition matcher. |
| Total input token volume | Measured. |
| Visible count of inputs in the synthesis prompt | Inherent in showing the inputs. Neutral delimiters, with no count stated in the instruction. |
| Single-input synthesis wording | One instruction valid for any k, under principle 1. F1 is dropped if preflight fails. |

**SI-same versus SD-same (input independence, level 2).** SI-same is three observations, each rewritten once, then synthesized (seven calls). SD-same is one observation rewritten three times, then synthesized (five calls). All observers receive the identical package. Independence therefore operates only through independent realization and independent resolution of the conflict pairs.

| Difference | Handling |
|---|---|
| Number of distinct roots | Target. |
| Input depth | Eliminated. All inputs are at depth 1. |
| Number of source templates | Eliminated by principle 5. All observers in a block use one source template. |
| Rewrite templates | Matched by slot across SI and SD within a block. |
| Seeds | SI observers have three keys, and the SD observer shares the key of SI's slot 1 observer, so the two observations are identical. The slot 1 rewrite has the same parent, template, and key in both conditions and is also identical. SI and SD therefore share one of their three synthesis inputs exactly and differ in slots 2 and 3, where SI rewrites two further independent observations and SD rewrites its single observation twice more. Version 3 stated wrongly that no slot matched. The contrast is paired at slot 1 under principle 6. |
| Number of calls (seven versus five) | Inherent in the number of roots. Calls are isolated, so call count has no path to the terminal except through the inputs. |
| Proposition coverage across inputs | Assigned coverage held fixed. Realized coverage measured. |
| Resolution of conflict pairs | Part of the target. Realized resolutions are measured. |
| Convergence or divergence caused by the rewrite stage | A mediator and a possible cause of a null result, not a confound once templates and seeds are matched. Measured as pairwise input similarity before and after the rewrite. |
| Input similarity at synthesis | The mechanism by which the target acts. Measured and reported as a mediator. |
| Total input token volume | Measured. |

**SI-div versus SD-div (level 3).** Named as independent partial-access observers versus a single union-access observer, both followed by matched rewrites and synthesis. Each SI observer receives a different assigned package with a fixed overlap, and the SD observer receives their union. Beyond the number of roots, the arms differ in each observer's input length, in which conflicting claims each observer sees together, and in whether one observer can reconcile all the evidence before any rewriting. These differences are part of the named total effect. Assigned and realized coverage per observer, conflicts seen jointly, and input length are measured. A result in this arm is not evidence about independence beyond the access difference. SI-same versus SD-same is the narrower contrast.

**Decay after synthesis.** Version 2 generated the downstream conditions as separate trials. In version 3, each SI-same and SD-same synthesis output is the starting record for two continuations, one of one rewrite and one of three, generated as separate branches. The continuations at a given depth use the same rewrite templates in the SI and SD trials of a block. Every SI-versus-SD comparison at depth 0, 1, and 3 is therefore paired at the synthesis output. The estimand is the interaction between ancestry assignment and downstream depth in discriminability, on prespecified outputs and feature families. A declining interaction is reported as a loss of detectability with added rewriting, which is an operational total effect. It is not by itself evidence that specific inherited deviations disappeared, which is checked separately with the propositional features. The decay analysis uses the same-package arm only.

### Study 2

**IND versus DEP versus MIX (shared ancestry among observed messages, level 4).** IND is three observations each rewritten once. DEP is one observation rewritten three times. MIX is one observation rewritten twice plus a second observation rewritten once. Every observed message is one rewrite from one observation.

Package assignment law. Under partial access, each world has a fixed pool of assigned packages of equal size, each containing the core event. Two kinds of slot are distinguished. A generation slot is a fixed canonical position used for package assignment, template matching, and call keys. A presentation position is the order in which the three messages are shown to a reader or classifier. For each set, three packages are drawn from the pool without replacement and assigned to generation slots 1, 2, and 3. In IND, the message in generation slot j is one rewrite of an observer who receives package j. In DEP, all three messages are rewrites of one observer who receives package 1. In MIX, the messages in generation slots 1 and 2 are rewrites of one observer who receives package 1, and the odd message, always in generation slot 3, is a rewrite of an observer who receives package 3. Because the packages are drawn at random, fixing the odd message to generation slot 3 does not tie it to any particular package. The rule does not depend on structure, so the source package of a randomly chosen message has the same marginal distribution in every structure. Under full access every observer receives the whole record. Source templates follow principle 5, and rewrite templates are matched by generation slot across structures within a block. Call keys follow principle 6. The generation slot 1 observation and its rewrite are therefore shared exactly by IND, DEP, and MIX within a block. MIX's odd observation and its rewrite in generation slot 3 are shared exactly with IND's generation slot 3, and DEP's generation slot 2 rewrite is shared exactly with MIX's. Presentation order is permuted at random per set before any analysis, so no presentation position carries information about generation slot or structure.

The two access levels answer different questions. The law makes the single-message marginals equal, but not the joint package distribution. Under partial access the three IND observers always receive different packages, whereas DEP's messages all descend from one package and MIX's shared pair from one package. Set-level similarity under partial access can therefore reveal shared factual access even when no idiosyncrasy is inherited. The partial-access contrast is named as the total effect of source sharing combined with shared assigned access. The full-access arm is the primary test of inherited deviations, because there every observer receives the same record, and access cannot differ by structure. Its IND sets also supply the independent same-package null that the shared-deviation methods require. Under partial access no such null exists within the IND cells, because their packages always differ. The excess shared deviation in the partial arm is therefore reported against the full-access null only, and labeled as not identified relative to a same-package null.

| Difference | Handling |
|---|---|
| Shared roots among the three messages | Target. |
| Number of observation calls (three, one, two) | Inherent. Not visible in any single message under isolation. |
| Marginal distribution of a single message | Equal by the package law and template matching. Tested by H7 within strata. |
| Position of the odd message in MIX | Eliminated. The odd message has a fixed generation slot, and presentation order is permuted at random per set. No slot labels are shown. |
| Branch-indexed formatting or identifiers | Eliminated. No node prompt receives a branch index, and observed messages carry no identifiers. |
| Shared errors from the shared producer model | Not shared ancestry. Estimated from full-access IND sets in training worlds, conditioned on genre, producer, and attribution arm. No same-package null exists in partial-access IND sets, as explained above. |
| Shared assigned package under partial access | Part of the named partial-access total effect. Not attributed to inheritance. |
| Upstream realizations across attribution arms | Held fixed. The generative concealment arm reuses the neutral arm's observation texts and changes only the rewrite instruction. The stripped arm is derived from the neutral rewrites. All three arms of a set share their observation texts. |
| Whether stripping removes attribution without changing content | Handled by the attribution field defined below. Stripping deletes that field only. Marker presence, field validity, stripping success, and proposition-matcher equivalence before and after stripping are reported by structure and arm. Attribution phrased inside the prose is left in place and counted. |
| Observer access (full or assigned partial package) | Crossed as a factor. Within each access level the package law is identical across structures. |

Attribution field. In every world, each proposition carries an in-world source, such as a maintenance log, a shift supervisor, or a sensor record, and the world's source inventory lists them. The attribution field is a delimited final line, `Sources:`, followed by the in-world sources the message's claims rest on, chosen from that inventory. The observer instruction asks for the field. The neutral rewrite instruction asks the rewriter to carry the field forward and revise it to match what the rewrite retains. The generative concealment instruction asks for the field to be omitted and for source cues to be removed from the prose. The field never contains a pipeline identifier, such as a node, branch, slot, observer, or root identifier, or any reference to other messages. It therefore discloses only world content, which is identical across structures. A field shared between messages is inherited from a shared ancestor in the same way as any other content, and is part of the target. An entry outside the inventory is invalid and is counted. The field is generated by the model rather than appended mechanically, because attribution as written by the producer is the object of study, and a deterministic field would carry no production information. Its permitted content is declared in advance and checked mechanically.

H10's primary analysis includes every assigned set, whatever the field's presence or validity, so that the contrast is conditioned on assignment and not on compliance. The analysis restricted to sets in which the field was present and valid and stripping left the propositions unchanged is secondary, and is reported with its selection rate by structure and arm.

### Method comparisons

The reader-versus-classifier comparison is restricted to methods that receive exactly the same input, which is message text only, with labeled training-world examples supplied in context to the reader. The world-anchored and world-free methods of H10 and H11 use additional information (the world record, the matcher's alignment, or an independent reference corpus) and are reported separately, with the anchored method as an upper reference. The remaining difference between in-context examples and fitted parameters is stated as such. The method comparison is secondary in this design.

## Part V. Conditions, primary contrasts, and estimates

### Inferential structure

Three contrasts are primary. Every other analysis is a prespecified secondary estimate, reported with its interval and without a confirmatory claim.

- **P1, negative control (H1).** NC0 versus D0 and NCR1 versus R1, judged by the three-way rule below.
- **P2, input independence (H4).** SI-same versus SD-same, primary genre and primary producer.
- **P3, shared ancestry among messages (H8).** IND versus DEP sets, full-access neutral arm of Study 2, primary producer.

P2 and P3 are one-sided tests that the held-out AUC exceeds 0.5. They form one family, controlled at α = 0.05 by Holm's procedure applied to their bootstrap p-values. P1 is an equivalence judgment and is outside that family. If P1 finds a leak beyond tolerance, P2 and P3 are reported conditional on it.

**Three-way rule.** Used for P1, H7, and the stripping check of H10. A comparison is equivalent at tolerance if the whole two-sided 90% interval lies inside the tolerance band, shows a leak beyond tolerance if the whole interval lies outside it, and is otherwise inconclusive. An inconclusive result is reported as an upper bound on the leak, given by the interval's limit, not as a leak and not as equivalence. The AUC tolerance of 0.43 to 0.57 and the paired-difference tolerance of plus or minus 0.05 are stipulated. An AUC of 0.57 means a classifier orders a random pair of messages correctly 57% of the time, which is taken as the largest leak too small to carry a structural claim by itself. At this design's size the interval width is close to the band's width, so inconclusive results are expected and are reported as bounds.

### Study 1

Seventeen conditions. In D0, NC0, R1, R3, R5, and NCR1 the observer receives the full world record. In the other conditions observers receive assigned packages under the rules in Part IV, and every package includes the core event.

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

- **H1, sibling inertness (P1).** NC0 is equivalent to D0, and NCR1 to R1, under the execution schedules used. Replay identity is a build requirement checked before the full run (Part IV). In the full run, the NC0 and NCR1 terminals have their own seeds (principle 6), and a world-held-out classifier discriminates each control from its reference. AUC is computed with the control condition as the positive class, an orientation fixed before fitting, and judged by the three-way rule.
- **H2, depth (secondary).** Discriminability of R1, R3, and R5, as macro one-versus-one AUC, with propositional drift reported by depth without assuming monotonicity.
- **H3, partitioned observers (secondary).** Discriminability of F1, F2, and F3, as macro one-versus-one AUC. The conditions differ by construction in how many propositions each observer sees, so discrimination is expected. The estimate gives the size of the trace this procedure leaves and is not a test.
- **H4, input independence (P2 for the same-package arm).** SI-same versus SD-same, binary AUC. SI-div versus SD-div is a secondary estimate of the access total effect named in Part IV. Input similarity and realized conflict resolution are post-treatment process measures. They are reported with their associations with discriminability and are not treated as mediators, because no mediation design identifies an indirect effect.
- **Observer diversity (secondary).** Independence in SI-same operates only through sampling variation at the producer's default decoding settings, which are recorded and not varied. P2 is therefore conditional on those settings. The association between each world's mean pairwise diversity among SI observers and its SI-same versus SD-same discriminability is reported, so that a weak P2 can be read against how different the independent observers actually were.
- **H5, detectability after synthesis (secondary).** The change in SI-same versus SD-same AUC after one and three downstream rewrites, with intervals. Rewriting cannot add information about ancestry, so an optimal reader cannot gain, and a decline is expected. The estimate is the rate of loss, not a test.
- **H6, transfer (secondary).** Three transfers are estimated for R1 versus R3 and for SI-same versus SD-same. A model trained on prompt family A is tested on family B and compared with family A on the same test worlds. A model trained on the primary producer is tested on the second. A model trained on one genre is tested on the other. For Study 2, the P3 contrast is estimated under the second producer.

### Study 2

Three structures crossed with two access levels (full record, assigned partial packages) and three attribution arms (neutral, generative concealment, stripping). The concealment arm reuses the neutral arm's observation texts, and the stripping arm is derived from the neutral rewrites with no producer calls. The second producer runs the full-access neutral arm only, for the H6 transfer estimate.

- **H7, single-message leakage (secondary check).** A classifier given one randomly chosen message per set is judged by the three-way rule for each pair of structures, within each combination of access and attribution, with prompt families pooled. Results by prompt family, and the worst stratum, are descriptive. If a leak beyond tolerance is found, P3 and H8 are still reported, because the pooled baseline of H8 receives all single-message information, and relational claims are restricted to the gain over that baseline.
- **H8, shared ancestry (P3 and secondary).** P3 is the held-out AUC of the pairwise-feature model for IND versus DEP in the full-access neutral arm. Secondary estimates are the gain over the two baselines (an order-invariant aggregate of single-message predictions, and a model that pools per-message features by mean and maximum without cross-message comparison), the three-class result including MIX, pairwise shared-source labels, and the partial-access arm, named there as shared access and shared ancestry together. Random assignment identifies the effect of the production structure on the joint distribution of messages. Which features carry it is a separate question. The primary shared-deviation statistic is, for each pair of messages, the number of deviations from the world record (omissions, alterations, and conflict resolutions identified by the matcher) that the two share, minus its expected value under the full-access IND null from training worlds. The inherited-deviation account is described as supported only if a model using this statistic alone has a 95% lower bound above 0.5 for IND versus DEP and recovers at least half of the pairwise model's gain over the pooled baseline. The same comparison is reported for generic similarity (rare word-sequence overlap and embedding similarity). Relational prediction without that support is reported as relational prediction, not as evidence of inherited deviations.
- **H9, access (secondary).** Pairwise shared-source detection under both access levels. Under partial access, shared packages contribute by construction, so the difference is an estimate, not a test.
- **H10, attribution (secondary).** Over all assigned sets, the change in the prompted reader's detection when the attribution line is stripped. Generative concealment against stripping, on the same observation texts, estimates the total effect of the concealment instruction, which changes discourse and possibly content as well as the attribution line. Field presence, validity, and source errors are reported by structure. The world-anchored method's invariance to stripping holds by construction once stripping leaves the propositions unchanged, so it is reported as a check under the three-way rule, not as a hypothesis.
- **H11, world-free method (secondary).** The fraction of above-chance discrimination the world-free method retains, (AUC_free − 0.5) / (AUC_anchored − 0.5), from paired predictions on the same sets, with a bootstrap interval. It is computed only if the anchored method's 95% lower bound is at least 0.60, and both AUCs are always reported. The world-free null comes from full-access IND sets in training worlds.

## Part VI. Measurement

The original 14 features are retained as a baseline. New features are grouped into four prespecified families: formal (length and lexical), attributional (source, evidential, hedge, and uncertainty markers), propositional (preservation, omission, alteration, qualification, unsupported addition, conflict resolution, order), and relational (shared deviations, rare word-sequence overlap, order similarity, excess embedding similarity). The families are operational groupings, not separate latent constructs. Named entities, for example, are counted as form and also carry content. Incremental value is tested by family ablation, and no family is claimed to measure a construct without a manipulation that targets it.

The proposition matcher is validated before any propositional feature is used, and the validation is an audit whose outcome cannot change the analysis. The matcher code, label definitions, sampling procedures, and criteria below are locked before the verification run, and no validation label is ever used to train or revise the matcher. Validation has two parts.

The challenge set has known labels. A fixed script takes verification-run messages and makes controlled edits: it deletes the clause carrying a proposition (omission), changes a number, time, or entity by fixed rules (alteration), replaces one member of a conflict pair with the other (conflict resolution), or leaves the message unchanged. It produces at least 40 instances of each class of each judgment for each node function (observation, rewrite, synthesis) and each producer. The criterion is per-class recall of at least 0.85 for every class of every judgment, in every function and producer.

The natural sample measures performance on deviations the producers actually make, which scripted edits may not resemble. One hundred and twenty verification-run messages, stratified by study, condition group, and producer, are annotated blind to condition for preservation, omission, alteration, and conflict resolution. A second annotator codes 30 of them, and Cohen's kappa is reported. The criterion is pooled class-balanced accuracy of at least 0.80 for each judgment. Differences in agreement across node functions are reported with intervals, because a matcher that treats synthesis outputs differently from relay outputs would manufacture a structural result. The sample also includes 12 stripped and unstripped pairs, which check that stripping leaves the matcher's output unchanged.

Every analysis has two specifications, fixed now and identical across conditions, one with all feature families and one without the propositional family. Both are always reported. If both validation parts meet their criteria, the full specification is primary. Otherwise, the specification without propositional features is primary for every condition, the full-specification results are labeled unvalidated throughout, and the shared-deviation account of H8, the anchored and world-free methods of H10 and H11, and all claims about inherited omissions, alterations, and conflict resolution are withheld. No feature family is added or removed for some conditions and not others.

The exact feature extraction definitions are released with the code. A generic sentence-embedding classifier and a flexible text classifier are reported as stress tests for leakage, with model selection confined to training folds.

## Part VII. Worlds, genre, and scale

**Worlds.** Seventy new worlds under a revised schema, each with about 20 propositions, several numeric details (times, counts, durations), and two conflicting pairs. The original worlds have 8 propositions and one conflict pair, and preservation averaged 0.96 in the original run, which leaves little room for inherited variation. Ten worlds are used for the verification run and never enter hypothesis tests. Sixty are used for the full run. The original 20 worlds are not reused, because mixing schemas would confound world type with world source. Worlds are drafted by a language model from a family different from both producers and both readers, from a fixed schema and a fixed list of 14 event types with five worlds each. They are checked automatically against the schema (proposition count, numeric details, two conflict pairs, and source inventory) and reviewed by Eric. The drafting prompt, the acceptance rules, and any hand edits are logged. The world bank, the 10 verification worlds, and the assignment of the 60 full-run worlds to evaluation folds are frozen before the verification run. Results describe this authored world distribution, not natural events. Each world also carries its Study 1 partitions, its conflict co-location assignments, its Study 2 package pool, and its in-world source inventory for the attribution field.

**Genre.** The primary genre is the incident report. The full run includes a second genre (news brief) for R1, R3, SI-same, and SD-same in all 60 worlds and three replicates, and H6 reports genre transfer for the R1 versus R3 and SI-same versus SD-same contrasts. Other contrasts are run in the primary genre only, and their claims are scoped to it.

**Producers and readers.** The primary producer is llama3.1:8b. A second producer family runs all of Study 1 and the full-access neutral arm of Study 2, for H6. Two reader models, each from a family different from both producers, read every primary-producer message or set once. All models run locally.

**Planning estimate.** These figures assume 9 seconds per call, the average from the original run. Synthesis calls with three inputs will be slower. The verification run measures latency by node function and producer, for scheduling only. Study 1 now needs 61 producer calls per world and replicate, against 85 in version 2, because the decay conditions branch from existing synthesis outputs. Study 2 needs 24 producer calls per world, replicate, and access level (15 for the neutral arm and 9 rewrites for the concealment arm), against 30, because the concealment arm reuses the neutral observation texts.

| Component | Units | Producer calls | Reader calls | Hours at 9 s per call |
|---|---|---|---|---|
| Verification, Study 1 (10 worlds, 1 replicate, both producers, second-genre subset on the primary producer) | 380 messages | 1,400 | none | 3.5 |
| Verification, replay set (4 schedules × 50 pairs per control, with D0 and R1 self-replays) | 400 control pairs, 400 self-replays | 2,600 | none | 6.5 |
| Verification, Study 2 (10 worlds, 1 replicate, with the second producer's full-access neutral arm) | 150 generated sets plus 60 stripped sets | 630 | none | 1.6 |
| Study 1, primary producer (60 worlds, 3 replicates) | 3,060 messages | 10,980 | 6,120 | 42.8 |
| Study 1, second genre (R1, R3, SI-same, SD-same) | 720 messages | 3,240 | 1,440 | 11.7 |
| Study 1, second producer (H6) | 3,060 messages | 10,980 | none | 27.5 |
| Study 2 (60 worlds, 3 replicates) | 2,160 generated sets plus 1,080 stripped sets | 8,640 | 6,480 | 37.8 |
| Study 2, second producer (full-access neutral arm) | 540 sets | 2,700 | 1,080 | 9.5 |

Each replay unit, meaning one NC0 pair, one NCR1 pair, and their two self-replays, costs 13 calls: D0 (1) and NC0 (3), R1 (2) and NCR1 (4), one D0 re-execution (1), and one R1 re-execution (2). The D0 and R1 runs in each unit serve as the reference for both the control comparison and the self-replay, and that dependence is reported. Two hundred units cost 2,600 calls. The verification run is about 4,630 producer calls, or about 11.6 hours. It includes the second producer, because that pipeline also has to be shown to work before the full run. The full run is about 129 serial machine hours, or five and a half days, before failures and reruns. The replicate count of three per world and condition is fixed and is not revised after any data are seen. Machine time is not the binding cost. World construction, prompt-pool drafting, matcher annotation, and audit review require human time that this table does not include.

## Part VIII. Analysis plan

- **Evaluation.** Outer five-fold cross-validation grouped by world, with the 60 worlds assigned to folds of 12 by a seeded draw balanced on event type, fixed before the verification run. Metrics are computed on pooled out-of-fold predictions. Regularization is chosen by four-fold world-grouped cross-validation within each training set. There is no separate holdout set.
- **Learner.** L2-regularized logistic regression on standardized features, multinomial for multiclass contrasts, with the penalty chosen from 0.01, 0.1, 1, and 10.
- **Metrics.** AUC for binary contrasts and macro one-versus-one AUC for multiclass contrasts are primary. Accuracy, balanced accuracy, macro-F1, multiclass Brier score, and log loss are secondary.
- **Labels.** Study 1 contrasts are binary or multiclass as named in Part V. Study 2 sets carry a three-class structure label, and each of a set's three pairs carries a shared-root label.
- **Intervals and p-values.** A two-way cluster bootstrap resamples worlds and source templates independently, 2,000 times, with out-of-fold predictions held fixed. The estimand is the performance of the fitted pipeline on new worlds and templates from the same distributions. The bootstrap resamples whole worlds, so all texts that share a key or descend from a shared synthesis output stay together. The P2 and P3 p-values are the bootstrap proportion of AUC at or below 0.5. The number of unique generated messages is reported alongside the number of labeled records.
- **Prompted reader.** The reader receives the message text, or the three texts of a set in random order, with neutral descriptions of the label classes that do not use condition names, and 16 labeled examples from the fold's training worlds, balanced by class and the same for every test item in the fold. It returns a probability over the labels in JSON at temperature 0. An invalid output is retried once, and if it is invalid again it is scored as a uniform distribution and counted. Reader and classifier results are compared descriptively, as prediction performance under different supervision, not as evidence about method families.
- **Interactions.** The prespecified secondary interactions are genre and producer with R1 versus R3 and with P2, access with structure in Study 2, and message-length tertile with P2 and P3, each with bootstrap intervals. All other subgroup results are descriptive and shown with their counts.
- **Configuration.** A machine-readable configuration fixes every item above. It is frozen with the preregistration, and the analysis code is tested on synthetic data before the verification run. Verification-run data are excluded from every hypothesis test, and any amendment is versioned and reported.

## Part IX. Execution sequence

The work runs in three stages. Nothing learned in the second stage about hypothesis outcomes can change the design, because no hypothesis outcome is computed on verification data.

1. **Build and preregister.** Complete the original-lineage check (Gate 1 below), build the new dispatcher, worlds, prompt pools, and analysis code, test the analysis code on synthetic data, and preregister this document.
2. **Verify.** Run the verification run on the 10 reserved worlds. It checks only that the implementation works as specified: the lineage audit passes on every condition, seeds reach Ollama, replay is deterministic under the schedules to be used (Gate 2 below), packages, co-location, and template assignments match their rules, the attribution field is produced and parsed, both producers and the reader run, and the failure and retry policy behaves as written. Defects are fixed in the code and the affected checks are rerun. The two design branches fixed in advance are the only changes allowed. F1 is dropped if the single-input synthesis preflight fails, and a schedule is excluded if it cannot be made deterministic. Hypothesis metrics are not computed.
3. **Run in full.** Run every condition in Parts IV and V at the stated scale and report every planned contrast, whatever its result. No contrast is stopped, narrowed, or expanded on the basis of its outcome.

| Gate | Test | If it passes | If it fails |
|---|---|---|---|
| 1 | Lineage of the original study documented against its code, source-to-record correspondence checked, and the new dispatcher's lineage audit and seed replay passed in preflight | The original lineage is documented, and the new pipeline is cleared to generate. Reproduction of the original numbers is a separate check on the deposited data. Neither establishes the original structural interpretation, which the lineage findings already contradict | The defect is repaired before any generation |
| 2 | Replay per execution schedule against the ancestry-matched self-replay baselines, in the verification run | The configuration and schedules are cleared for the full run. This is not a finding of distributional equivalence, which H1 tests on the full data | The dispatcher is corrected and the replay set rerun, or the schedule is excluded, as specified in Part IV |

Every contrast runs at full scale and is reported. A null result on any contrast is reported with its interval, as no detected difference at this design's precision, and is not read as evidence that the property is unrecoverable.

## Part X. Claims

The paper reports engineering validation separately from findings. Pipeline isolation, deterministic replay, and lineage correspondence show that the instrument works as specified. They are not findings about communication.

If P2 and P3 succeed and P1 does not find a leak, the paper can claim, for small message-production graphs built from the tested language models, worlds, genres, and execution schedules, that independent versus shared production of a synthesis's inputs leaves a recoverable difference in the synthesis under matched instructions, and that shared ancestry among messages in a set is recoverable from relations among them. The shared-deviation account of the second claim requires the support condition in H8 and the full-access arm. The secondary estimates describe how much trace depth, partitioned observation, and downstream rewriting leave, and how the primary results transfer across prompt family, genre, and producer. Each claim names its contrast in Part IV. It is not a claim about network topology in general, and the paper does not claim transfer to human communication.

The original study appears as a demonstration that protocol-confounded designs report high accuracy for properties the observed message cannot contain. A correction audit in the supplement lists which original quantities reproduce from the deposited data and which conclusions are withdrawn. The compound result is reported as an implementation defect, not as evidence about recovering compositions.

## Part XI. Field anchor

No field anchor is planned, and the paper makes an in-silico methodological claim only, unless Eric decides otherwise (open decisions). The candidates considered earlier support different validity checks and depend on licensing outside the project's control. A weakly matched external corpus would be worse than a stated synthetic boundary.

## Part XII. Deferred

None of the following is part of this paper.

- **Random-graph sweep.** If added in later work, its size must be specified as a total number of graphs with a stated reuse rule across worlds and a budget from the realized call-count distribution.
- **Circulation.** Exploratory, with a matched two-input control.
- **Redundant-package fan-in variant.**
- **Crossing roots with fan-in.** A design in which k inputs from one root and k inputs from k roots are compared at each k would separate the two factors that H3 bundles. It is deferred because SI-same versus SD-same already supplies the k = 3 comparison.
- **Genre crossing for F1, F2, F3, Study 2, and the remaining Study 1 contrasts.**

## Part XIII. Scope relative to the original manuscript

This design replaces every experiment in the submitted manuscript (`main_manuscript_npj_complexity_v2.docx`). Its parts map onto the new design as follows.

| Original component | In this design |
|---|---|
| Eight-motif recovery by the surface-form classifier and the prompted reader | Replaced by Study 1 and Study 2. The original results are reported only as the protocol-confound demonstration and the compound correction, computed from the deposited data, which need no rerun |
| Length-only diagnostic | Kept as the formal feature family in the ablations of Part VI |
| Cross-family prompted reader | Kept. Readers come from a different family than the producer, and H6 tests producer transfer |
| Calibration and the reader's fidelity confidence | Calibration of structural predictions is retained, assessed with Brier score and log loss. The separate fidelity-confidence posterior, and its calibration and correlation with source-content preservation, are dropped |
| Candidate-source set and the reader's origin posterior | Dropped. Origin attribution among candidate sources is a different question from structure recovery |
| Trace observability (L1 to L6) and metadata validity (v = 0.95 and 0.30) | Dropped from this paper |

The revised paper is a replacement empirical argument. It is not a confirmatory replication of the eight-motif accuracies, of the comparison between the reader and trace metadata, or of the original Figure 4. The original trace-based claims, including residue-method alignment as an account of the reader's gain with richer metadata, are withdrawn. The original classifier accuracies and the compound defect appear only as the diagnosis of protocol confounding, with their provenance in the deposited records. The abstract, claims, figures, and Methods are rewritten for the new observation units and controls, under the bounded framing of Part X.

The trace-observability manipulation is dropped for three reasons. In the original study, the collection narrative at L5 encoded path length and intermediary types, so the reader's gain with richer metadata came largely from metadata that described the label. Its question, how much a reader gains from source metadata of varying validity, concerns the reader and the metadata channel, not what the message itself retains of its production. Crossing four observability levels and two validity levels with every condition would multiply reader calls about eightfold. A metadata study built on this pipeline is possible later work, and its metadata would have to be generated without reference to the structure label.

## Open decisions for Eric

1. Who annotates the natural validation sample, and who serves as the second annotator for the agreement subset.
2. Whether to omit the field anchor, as this design assumes.
3. Which second producer family, and which two reader families, to use.
4. Where to preregister.
5. The target journal. The bounded framing in Part X suits a methods venue in machine learning or computational social science better than a complexity journal.

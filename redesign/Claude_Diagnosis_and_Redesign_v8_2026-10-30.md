# Production Structure Recovery from Communication Artifacts: Study Design, Version 8

Prepared by Claude, 2026-10-30. This is the design for an exploratory study, and `Build_Specification_v1_2026-10-30.md` holds the implementation detail a builder needs. Version 8 responds to `GPT Review of v7 (2026-10-30)`. It adds the structure predictor (Part V-A), corrects the compound comparison, completes the table of mistakes, and adds independent graph fixtures to the lineage audit. Version 7 applied the five amendments in `GPT Review of v6 (2026-10-30)` and enlarged the human validation sample, as Eric offered. It is a working document and changes when the work shows a reason to change it. Version 6 revised version 5 in response to two pre-results referee reviews, `Referee Review, Claude (2026-10-30).md` (written by a fresh agent that saw only version 5, the npj decision letter, and the submitted manuscript) and `Referee Review, GPT (2026-10-30)`. Both recommended major revision. The disposition of every referee objection is in `Referee_Disposition_v6_2026-10-30.md`. The record of how the design reached version 5 is in versions 1 to 5 and the GPT reviews in this folder, and it is not repeated here.

The work runs in three stages: build, verify the build on 10 reserved worlds, and run in full on the other 60.

**The question.** In a controlled environment, can we predict the structures a message has passed through? This is the question of the original paper. The build answers it with message-production graphs made of language-model calls, in which the structure is known exactly and the instructions at every node are matched across structures. Condition-specific prompt wording, which drove the original results, is therefore neutralized. Other differences that come with a structure, such as a synthesis seeing three inputs where a rewrite sees one, are part of what each named treatment is, and each contrast in Part IV lists them. Study 1 predicts structure from a single message. Study 2 predicts shared ancestry from several messages, which is where independent and shared sources become visible.

**Mistakes this build is designed not to repeat.**

| Original mistake | What prevents it here |
|---|---|
| Structures were built from their names, each with its own prompts, so the classifier learned prompts, not structure | One prompt pool per node function, shared across all structures, with matched templates within blocks (principles 1 and 5) |
| Unused parallel branches were scored as if they could leave traces in the observed message | Negative controls with unused siblings (P1), and parallel structures moved to Study 2, where sets of messages are observed |
| The compound structure was never wired, so its messages were plain relays | A lineage audit checks that every prompt contains exactly its parents' text, on every condition, before the full run (principle 8, Gate 1) |
| Metadata at higher trace levels described the label | No structure-bearing metadata is given to any method |
| Four test worlds, with trial-level intervals | Sixty worlds, world-grouped evaluation, and world-cluster intervals (Part VIII) |
| Anomalous results received mechanism stories after the fact | Mechanism claims require prespecified support conditions (H8), and process measures are reported as associations |
| The prompted reader and the classifier differed in both training and inputs, so their gap could not be attributed to the methods | Both receive message text only, the reader gets labeled training-world examples, and the comparison is descriptive (Part VIII) |
| Feature groups were presented as distinct kinds of residue, and a length-only model was already strong | Feature families are operational groupings for ablation, and a length baseline is reported (Part VI) |
| Calibration, origin, and fidelity diagnostics were not tied to one target | Calibration is assessed for structure predictions only, and the origin and fidelity tasks are dropped (Part XIII) |
| Striking accuracies in small subgroups were narrated without denominators | Subgroup results are shown with counts, and only a bounded set of interactions is estimated (Part VIII) |
| Cross-family evidence rested on 89 trials | A second producer for all of Study 1 and the full-access neutral arm of Study 2, two reader families, and stated transfer tests (H6) |
| Claims reached toward human communication | Claims are scoped to the controlled setting (Part X) |


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
4. **Trial-level prompt families.** Each prompt pool is split into two families, A and B. Every node in a trial draws from the same family, assigned at random by trial, so both families occur in every world. The transfer test trains on one family and tests on the other. Each family holds six templates for each node function, so each function has twelve templates in all. The registered template pools are treated as fixed in the primary analysis, and sensitivity to them is reported as secondary (Part VIII).
5. **Matched blocks and template assignment.** Conditions that are compared directly are generated in matched blocks. A block fixes the world, the replicate, the prompt family, and the assigned packages. Within a block, every observation call uses one source template, drawn at random for the block, and the k-th rewrite slot uses the same rewrite template in every condition of the block. Independence between observers then comes from independent seeds, not from different instructions. A sensitivity analysis in which source templates vary independently by observer is reported separately, and it answers a different question about instruction diversity.
6. **Canonical call keys and seeds.** Each call has a canonical key built from the world, the replicate, the block, the call's ancestral role (for example, observer in slot 1, or rewrite at depth 2 of slot 1), and its template assignment. The key never includes the condition. Corresponding ancestral calls in paired conditions therefore share a key, and with it a seed and an exact input. Unused sibling calls receive keys of their own that cannot coincide with any ancestral key. The seed is a stable cryptographic hash of the key, never a language runtime hash that changes between sessions, and it is passed to the provider wherever the API accepts one. Hosted APIs do not guarantee identical outputs for identical requests, so the design never depends on regeneration. A call is made once per key, and its output is stored and reused by every condition that shares the key. Key reuse across conditions is intentional and works like common random numbers. When two conditions share a call key, they share the stored output text, which is therefore identical by construction. For example, SD-same's observer shares the key of SI-same's slot 1 observer, so the two conditions share that observation and its first rewrite exactly. The manifest records every reused key, the estimand for each such contrast is a paired one, and texts that share a key are never counted as independent draws. World-grouped splits keep every text that descends from a reused call on one side of any split. The build checks that every condition sharing a key reads the same stored record. One exception to key sharing is deliberate. The terminal calls of NC0 and NCR1 receive keys that include the condition, so they are generated separately from those of D0 and R1. A shared terminal key would make NC0 and D0 the same stored text, and H1's test would then be empty.
7. **Call manifests.** Each call logs its key, exact prompt, parent-message hashes, model and quantization identifiers, decoding settings, seed, execution position, batching and concurrency settings, retry history, and validation status.
8. **Lineage as a gate, not a filter.** An automated audit checks that every non-source prompt contains exactly its parents' texts and that the realized ancestry of every terminal message equals the specified ancestry. Because an audit against the implemented graph would pass a graph that declares the wrong parents, the specified ancestry comes from independent reference fixtures, written by hand for each condition, that state every node, its function, and its parents. For the compound conditions, the fixture asserts that the synthesis output, not the world record, is the parent of the first downstream rewrite. A failure halts collection until the dispatcher is repaired. Trials are never silently excluded, and every failure and rerun is reported with its denominator.
9. **Retry policy.** A call that fails validation is retried at the same node only, up to three times, with seeds derived from its key and the attempt number. The parent texts are not regenerated. Every attempt is kept in the manifest. A node that fails all attempts marks the trial as failed, and failure rates are reported by condition and depth. If failure rates differ by condition, the difference is reported with the affected contrast. An output passes validation if it is nonempty, its length is within half to one and a half times the genre's target length, and it contains none of a fixed list of meta-commentary patterns (for example, references to instructions, to being a model, or to other inputs). Validation never checks the attribution line, in any arm. Its presence, validity, and parse are outcomes, recorded for every output and never a cause of retry, because a retry rule that required the line would reject the very concealment outputs H10 studies. Stripping is a deterministic postprocessing step, checked separately for byte-wise deletion of the line and nothing else. Because a shared-key call is made once and stored, its retries are shared by every condition that uses it, so retries do not break pairing.
10. **Randomized execution order.** Conditions are interleaved in random order within world blocks, so that provider load, model updates, and time of day are not tied to condition. Within a trial, the execution position of every call not constrained by its parents is randomized and logged. For the negative controls this includes the observed branch, as described in Part IV.
11. **The world as the unit of inference.** All evaluation uses world-grouped splits, and all intervals are world-clustered.
12. **Matched output constraints within genre.** Within a genre, all functions share the same length and format instruction. Across genres these constraints differ deliberately, and genre is treated as its own factor.
13. **Decoding settings.** Temperature and the other sampling settings start at each producer's documented defaults and are recorded in the manifest. Independent seeds yield independent calls, but not necessarily diverse outputs. At low output diversity, independent observers could write nearly identical reports and leave few idiosyncrasies to inherit, which would weaken H4 and H8 without biasing them. The verification run reports pairwise diversity among independent observer texts given the same package, and differences in their conflict resolution.

## Part IV. Difference table

Each contrast is listed with its target property, every other difference between the two conditions that has been identified, and how that difference is handled. A difference is eliminated by design, held fixed, randomized, measured and reported as a mediator, or accepted as part of the target, in which case the contrast is named as a total effect. The GPT review of version 2 added differences to several rows, marked with the defect number from that review.

### The depth confound

Version 1 and the first GPT design compared a synthesis of three independent observations with a synthesis of three rewrites of one observation. The independent inputs were at depth 0 and the dependent inputs at depth 1, so the contrast varied depth along with source independence. The repair rewrites each independent observation once before synthesis, so that all inputs in both conditions sit at depth 1. GPT's review found the repair correct and incomplete, because the independent condition still drew three source templates and the dependent condition one. Principle 5 now removes that difference.

### Study 1

**NC0 versus D0 and NCR1 versus R1 (sibling inertness, level 1).**

| Difference | Handling |
|---|---|
| Extra sibling calls executed in the trial | This is the manipulated factor. Under isolation it has no path to the terminal message. |
| Terminal call | The NC0 and NCR1 terminals receive condition-specific keys (principle 6), so H1 compares independent draws with the same input and rules. |
| Seeds of unused siblings | Separate keys that cannot coincide with an ancestral key. |
| Execution position of the observed branch | Counterbalanced. The observed branch is fixed before generation, but it runs first, last, or between the siblings in equal proportions. If it always ran first, no sibling state could reach it and the control would pass by construction. |
| Provider state | Each request is stateless and carries only its own prompt, with no conversation history and no shared session. The lineage audit confirms this for every call. Siblings and terminals are interleaved in random order. |
| Retries and validation failures | Logged per call and compared across conditions. |

Isolation is checked directly rather than by replay. The lineage audit confirms that every request contains exactly its parents' texts and nothing from sibling calls, and that no request reuses a session or conversation. H1's classifier test on the full data then asks whether NC0 and NCR1 can be told from D0 and R1.

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

**SI-same versus SD-same (input independence, level 2).** SI-same is three observations, each rewritten once, then synthesized (seven calls). SD-same is one observation rewritten three times, then synthesized (five calls). All observers receive the identical package, which is the full world record. Independence therefore operates only through independent realization and independent resolution of the conflict pairs.

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

**Composition (compound).** SD-same+3 is a correctly wired composition: a common-source synthesis, in which three apparent reports share one observation, followed by a three-step relay. It corresponds to the original compound, a laundering stage followed by a relay. Its longest path has six calls (observe, rewrite, synthesize, rewrite, rewrite, rewrite), as does R5 (observe and five rewrites). The comparison asks whether a message that passed through this composition can be told from one that passed through a plain chain of equal path length. It is the total effect of replacing the second serial rewrite with a branch-and-synthesis module, and it tests one composition, not compositions in general. SI-same+3 against R5 is a broader total effect, because it also changes the number of roots from one to three.

| Difference | Handling |
|---|---|
| Operation sequence: the third call on the path is a synthesis of three inputs, not a rewrite of one, so the path holds four rewrites instead of five | Target. Named as part of the module being tested |
| Input count and token exposure at that third call, including redundancy, coverage, and opportunities to reconcile or duplicate conflicting claims | Part of the target. Input tokens, redundancy, and coverage are measured as process quantities |
| Roots: one in SD-same+3 and R5, three in SI-same+3 | Part of the target for SI-same+3 against R5, which is named as the broader effect |
| Path length | Matched at six calls |
| Package | Matched. SD-same, SI-same, and R5 all receive the full world record, and the build asserts package equality |
| Templates | Source template shared within the block. Rewrite templates follow the slot map below |
| Total calls: eight for SD-same+3, ten for SI-same+3, six for R5 | Calls are isolated, so call count reaches the terminal only through what the extra branches pass to the synthesis |
| Input similarity at the synthesis | Process measure, reported as an association |

Slot map. R5's rewrites are numbered by their position on the path, r1 to r5. In SD-same+3 and SI-same+3, the rewrite before the synthesis on the longest path uses r1's template, and the three downstream rewrites use r3, r4, and r5's templates. R5's r2 has no counterpart, since the synthesis takes its position. The other two pre-synthesis rewrites (slots 2 and 3) use the slot templates defined for SI-same and SD-same. Templates are matched by role and position, never by key, so no key is reused for a different parent text.

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
- **P3, relational evidence of shared ancestry (H8).** In the full-access neutral arm of Study 2 with the primary producer, the gain in held-out AUC for IND versus DEP of the pairwise text-only model over the pooled text-only baseline, ΔAUC = A_r − A_0, computed on the same held-out sets.

P2 tests that the held-out AUC exceeds 0.5, and P3 tests that ΔAUC exceeds 0. Both are one-sided. They form one family, controlled at α = 0.05 by Holm's procedure applied to their bootstrap p-values (Part VIII). The absolute AUC of the pairwise model, A_r, is reported with P3 as a descriptive result. P1 is an equivalence judgment and is outside that family. If P1 finds a leak beyond tolerance, P2 and P3 are reported conditional on it.

**Three-way rule.** Used for P1, H7, and the stripping check of H10. A comparison is equivalent at tolerance if the whole two-sided 90% interval lies inside the tolerance band, shows a leak beyond tolerance if the whole interval lies outside it, and is otherwise inconclusive. An inconclusive result is reported as an upper bound on the leak, given by the interval's limit, not as a leak and not as equivalence. The AUC tolerance of 0.43 to 0.57 and the paired-difference tolerance of plus or minus 0.05 are stipulated. An AUC of 0.57 means a classifier orders a random pair of messages correctly 57% of the time, which is taken as the largest leak too small to carry a structural claim by itself. At this design's size the interval width is close to the band's width, so inconclusive results are expected and are reported as bounds.

### Study 1

Seventeen conditions. In D0, NC0, R1, R3, R5, NCR1, and the same-package arm (SI-same, SD-same, and their downstream branches), every observer receives the full world record. In F1 to F3 and the diverse-package arm, observers receive assigned packages under the rules in Part IV, and every package includes the core event.

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

- **H1, sibling inertness (P1).** NC0 is equivalent to D0, and NCR1 to R1, under the execution order used. Isolation is checked by the lineage audit before the full run (Part IV). In the full run, the NC0 and NCR1 terminals have their own seeds (principle 6), and a world-held-out classifier discriminates each control from its reference. The manifest audit confirms that the seed is the only intended difference at the terminal, and that packages, templates, model settings, validation, and parent assignment otherwise follow the same rules. AUC is computed with the control condition as the positive class, an orientation fixed before fitting, and judged by the three-way rule.
- **H2, depth (secondary).** Discriminability of R1, R3, and R5, as macro one-versus-one AUC, with propositional drift reported by depth without assuming monotonicity.
- **H3, partitioned observers (secondary).** Discriminability of F1, F2, and F3, as macro one-versus-one AUC. The conditions differ by construction in how many propositions each observer sees, so discrimination is expected. The estimate gives the size of the trace this procedure leaves and is not a test.
- **H4, input independence (P2 for the same-package arm).** SI-same versus SD-same, binary AUC. SI-div versus SD-div is a secondary estimate of the access total effect named in Part IV. Input similarity and realized conflict resolution are post-treatment process measures. They are reported with their associations with discriminability and are not treated as mediators, because no mediation design identifies an indirect effect.
- **Observer diversity (secondary).** Independence in SI-same operates only through sampling variation at the producer's default decoding settings, which are recorded and not varied. P2 is therefore conditional on those settings. The association between each world's mean pairwise diversity among SI observers and its SI-same versus SD-same discriminability is reported, so that a weak P2 can be read against how different the independent observers actually were.
- **H5, detectability after synthesis (secondary).** The change in SI-same versus SD-same AUC after one and three downstream rewrites, with intervals. Rewriting cannot add information about ancestry, so an optimal reader cannot gain, and a decline is expected. The estimate is the rate of loss, not a test.
- **H6, transfer (secondary).** Three transfers are estimated for R1 versus R3 and for SI-same versus SD-same. A model trained on prompt family A is tested on family B and compared with family A on the same test worlds. A model trained on the primary producer is tested on the second. A model trained on one genre is tested on the other. For Study 2, the P3 contrast is estimated under the second producer.
- **H12, composition (secondary).** Binary AUC for SD-same+3 against R5 and for SI-same+3 against R5, and macro one-versus-one AUC for the three as one three-class problem, all with the same learner and folds as the other Study 1 contrasts. These use conditions already generated, so they add no producer calls. A null result means this composition at this length was not detected, not that compositions leave no trace.

### Study 2

Three structures crossed with two access levels (full record, assigned partial packages) and three attribution arms (neutral, generative concealment, stripping). The concealment arm reuses the neutral arm's observation texts, and the stripping arm is derived from the neutral rewrites with no producer calls. The second producer runs the full-access neutral arm only, for the H6 transfer estimate.

- **H7, single-message leakage (secondary check).** A classifier given one randomly chosen message per set is judged by the three-way rule for each pair of structures, within each combination of access and attribution, with prompt families pooled. Results by prompt family, and the worst stratum, are descriptive. If a leak beyond tolerance is found, P3 and H8 are still reported, because the pooled baseline of H8 receives all single-message information, and relational claims are restricted to the gain over that baseline.
- **H8, shared ancestry (P3 and secondary).** Three models are fitted with the same outer folds and the same training rules, and all three see message text only. The pooled baseline, A_0, pools each message's formal and attributional features by mean and maximum, with no cross-message comparison. The pairwise model, A_r, adds the text-only relational features: rare word-sequence overlap, order similarity, and embedding similarity between each pair of messages. No feature in either model uses the world record or the matcher's alignment. P3 is A_r − A_0. Secondary estimates are the gain over the aggregate of single-message predictions, the three-class result including MIX, pairwise shared-source labels, the partial-access arm (named there as shared access and shared ancestry together), and the second producer.

Random assignment identifies the effect of the production structure on the joint distribution of messages. Which information carries it is a separate, world-anchored question. The shared-deviation statistic is, for each pair of messages, the number of deviations from the world record (omissions, alterations, and conflict resolutions identified by the matcher) that the two share, minus its expected value under the full-access IND null from training worlds. A third model, A_s, adds this statistic alone to the pooled baseline. The inherited-deviation account is described as supported only if (a) A_s − A_0 has a 95% lower bound above 0, and (b) the contribution fraction (A_s − A_0) / (A_r − A_0) has a point estimate of at least 0.5. The fraction is computed only when the 95% lower bound of A_r − A_0 is above 0, and it is reported with its paired interval. If the account is not supported, a positive P3 is reported as relational prediction from text similarity, not as evidence of inherited deviations. The account also requires the matcher to pass validation (Part VI).
- **H9, access (secondary).** Pairwise shared-source detection under both access levels. Under partial access, shared packages contribute by construction, so the difference is an estimate, not a test.
- **H10, attribution (secondary).** Over all assigned sets, the change in the prompted reader's detection when the attribution line is stripped. Generative concealment against stripping, on the same observation texts, estimates the total effect of the concealment instruction, which changes discourse and possibly content as well as the attribution line. Field presence, validity, and source errors are reported by structure. The world-anchored method's invariance to stripping holds by construction once stripping leaves the propositions unchanged, so it is reported as a check under the three-way rule, not as a hypothesis.
- **H11, world-free method (secondary).** The fraction of above-chance discrimination the world-free method retains, (AUC_free − 0.5) / (AUC_anchored − 0.5), from paired predictions on the same sets, with a bootstrap interval. It is computed only if the anchored method's 95% lower bound is at least 0.60, and both AUCs are always reported. The world-free null comes from full-access IND sets in training worlds.

## Part V-A. The structure predictor

The contrasts in Part V test whether particular differences are recoverable. The predictor is the system that answers the question at the top: given a message it has not seen, which structures did it pass through? It is trained and evaluated on the same generated data, with the same world-grouped folds, so it adds no generation.

**Single message.** Every Study 1 condition is described by five history attributes, which the predictor estimates jointly from the text alone.

| Attribute | Values |
|---|---|
| Synthesis on the path | yes, no |
| Synthesis inputs | 0, 1, 2, 3 |
| Independent roots reaching the message | 1, 2, 3 |
| Rewrites between root and synthesis | 0, 1 |
| Rewrites after the last root or synthesis | 0, 1, 3, 5 |

| Condition | Synthesis | Inputs | Roots | Rewrites before | Rewrites after |
|---|---|---|---|---|---|
| D0, NC0 | no | 0 | 1 | 0 | 0 |
| R1, NCR1 | no | 0 | 1 | 0 | 1 |
| R3 | no | 0 | 1 | 0 | 3 |
| R5 | no | 0 | 1 | 0 | 5 |
| F1 | yes | 1 | 1 | 0 | 0 |
| F2 | yes | 2 | 2 | 0 | 0 |
| F3 | yes | 3 | 3 | 0 | 0 |
| SD-same, SD-div | yes | 3 | 1 | 1 | 0 |
| SI-same, SI-div | yes | 3 | 3 | 1 | 0 |
| SD-same+1, SD-same+3 | yes | 3 | 1 | 1 | 1, 3 |
| SI-same+1, SI-same+3 | yes | 3 | 3 | 1 | 1, 3 |

NC0 and D0 share a history, as do NCR1 and R1, because unused siblings are not ancestors. The access arm (same or diverse package) is not a structural attribute and is not predicted. The table yields 13 distinct histories. The predictor outputs a probability for each attribute value, and a probability over the 13 histories. The history confusion matrix, on held-out worlds, shows which histories the text can separate and which it cannot. Observationally equivalent histories are a result, not a failure of the system.

**Set of messages.** For three messages about one event, presented in random order, the predictor estimates a distribution over five configurations: IND, DEP, and MIX with the odd message in each of the three presented positions. The probabilities for IND, DEP, and MIX, and the same-root probability of each pair, are sums over those five, so they are consistent by construction. A pair shares a root under DEP, and under the MIX configuration that does not single out either of its members. The predictor sees the texts and nothing else.

**Interface.** Input is message text, or three texts. Output is JSON with a task identifier (single or set), the history probabilities with the attribute probabilities derived from them (single), or the configuration probabilities with the structure and pair probabilities derived from them (set), each normalized to sum to one, and a flag when the input fails the validation rules of principle 9. No world identifier, condition label, key, or metadata enters the predictor.

**Models.** Three predictors are trained and reported on the same folds: the L2 logistic model on the registered features, a logistic model on sentence embeddings, and a gradient-boosted model on the registered features. The best by inner cross-validation is the system's reported predictor, and all three are shown. The history head is a multinomial model over the 13 histories. Each attribute's probabilities are the sums of the history probabilities over the histories that have each value, so the attribute and history outputs cannot contradict each other. Separately fitted attribute models are reported as a secondary check on whether the marginals lose accuracy. Evaluation reports per-attribute AUC and accuracy, history accuracy and the confusion matrix, Brier score, and results by event type, producer, and genre.

## Part VI. Measurement

The original 14 features are retained as a baseline. New features are grouped into four prespecified families: formal (length and lexical), attributional (source, evidential, hedge, and uncertainty markers), propositional (preservation, omission, alteration, qualification, unsupported addition, conflict resolution, order), and relational (shared deviations, rare word-sequence overlap, order similarity, excess embedding similarity). The families are operational groupings, not separate latent constructs. Named entities, for example, are counted as form and also carry content. Incremental value is tested by family ablation, and no family is claimed to measure a construct without a manipulation that targets it.

The proposition matcher is validated before any propositional feature is used. Validation labels are kept separate from anything used to develop the matcher, so that the validation measures its accuracy honestly. Validation has two parts, which are reported separately, with confusion matrices, class counts, and intervals. Neither part can substitute for the other.

**Natural sample.** Two hundred and forty verification-run messages, stratified by study, condition group, node function, and producer, are coded by a coder who is blind to condition, structure, and model features, using a written rubric. The coder records each proposition's state (preserved, omitted, altered, or qualified) and the resolution of each conflict pair. A second coder, also uninvolved in the design, independently codes 60 of the messages, chosen by the same stratification. Cohen's kappa is reported by judgment before adjudication, and disagreements are then adjudicated by the two coders under the written protocol. The criterion is pooled class-balanced accuracy of at least 0.80 for each judgment. A class with fewer than 30 natural instances in the pooled sample is marked not validated on natural text, and every claim that depends on that judgment is then withheld. Differences in agreement across node functions are reported with intervals, because a matcher that treats synthesis outputs differently from relay outputs would manufacture a structural result.

**Challenge set.** The coded natural messages serve as bases, so each base's proposition states are known before editing. A fixed script then makes controlled edits: it deletes the clause carrying a preserved proposition (omission), changes a number, time, or entity by fixed rules (alteration), or replaces one member of a resolved conflict pair with the other (conflict resolution). It also makes meaning-preserving hard negatives, such as reordered clauses, numbers written out as words, and substitutions from a fixed synonym list, whose labels must stay unchanged. It produces at least 40 instances of each class of each judgment for each node function and each producer. The criterion is per-class recall of at least 0.85 for every class and a false-change rate below 0.10 on hard negatives.

The sample also includes 12 stripped and unstripped pairs, which check that stripping leaves the matcher's output unchanged.

Every analysis has two specifications, identical across conditions, one with all feature families and one without the propositional family. Both are always reported. If both validation parts meet their criteria for every judgment, the full specification is primary. Otherwise, the specification without propositional features is primary for every condition, the full-specification results are labeled unvalidated throughout, and the shared-deviation account of H8, the anchored and world-free methods of H10 and H11, and all claims about inherited omissions, alterations, and conflict resolution are withheld. No feature family is added or removed for some conditions and not others.

The exact feature extraction definitions are released with the code. A generic sentence-embedding classifier and a flexible text classifier are reported as stress tests for leakage, with model selection confined to training folds.

## Part VII. Worlds, genre, and scale

**Worlds.** Seventy new worlds under a revised schema, each with about 20 propositions, several numeric details (times, counts, durations), and two conflicting pairs. The original worlds have 8 propositions and one conflict pair, and preservation averaged 0.96 in the original run, which leaves little room for inherited variation. Ten worlds are used for the verification run and never enter hypothesis tests. Sixty are used for the full run. The original 20 worlds are not reused, because mixing schemas would confound world type with world source. Worlds are drafted by a language model from a family different from both producers and both readers, from a fixed schema and a fixed list of 14 event types with five worlds each. They are checked automatically against the schema (proposition count, numeric details, two conflict pairs, and source inventory) and reviewed by Eric. The drafting prompt, the acceptance rules, and any hand edits are logged. The world bank, the 10 verification worlds, and the assignment of the 60 full-run worlds to evaluation folds are set before the verification run. Results describe this authored world distribution, not natural events. Each world also carries its Study 1 partitions, its conflict co-location assignments, its Study 2 package pool, and its in-world source inventory for the attribution field.

**Genre.** The primary genre is the incident report. The full run includes a second genre (news brief) for R1, R3, SI-same, and SD-same in all 60 worlds and three replicates, and H6 reports genre transfer for the R1 versus R3 and SI-same versus SD-same contrasts. Other contrasts are run in the primary genre only, and their claims are scoped to it.

**Producers and readers.** All models are commercial models called through hosted APIs at pinned versions, and every prompt and output is archived and released, so every analysis can be rerun, although generation cannot be once a model retires. The three producers are the small tiers of three labs: Gemini Flash-Lite (primary), Claude Haiku 5.5, and a low-tier OpenAI model. The primary producer runs everything. The other two run all of Study 1 and the full-access neutral arm of Study 2, for H6. The three producers are distinct generation environments, and H6 does not separate the effects of lab, size, or training. The readers are Claude Sonnet 5.5 and an OpenAI model one tier up. They read only the primary producer's messages and sets, so no reader reads text from its own lab. They read the first replicate, which covers all 60 worlds. The reader comparison is secondary and descriptive, and the classifiers and the predictor use all three replicates. Model choices and their reasons are in the build specification.

**Planning estimate.** Study 1 needs 61 producer calls per world and replicate. Study 2 needs 24 per world, replicate, and access level (15 for the neutral arm and 9 rewrites for the concealment arm, which reuses the neutral observation texts).

| Component | Units | Producer calls | Reader calls |
|---|---|---|---|
| Verification, Study 1 (10 worlds, 1 replicate, all three producers, second-genre subset on the primary producer) | about 590 messages | 2,010 | about 200 |
| Verification, Study 2 (10 worlds, 1 replicate, with the other producers' full-access neutral arm) | 180 generated sets plus 60 stripped sets | 780 | none |
| Study 1, primary producer (60 worlds, 3 replicates) | 3,060 messages | 10,980 | 2,040 |
| Study 1, second genre (R1, R3, SI-same, SD-same) | 720 messages | 3,240 | 480 |
| Study 1, second and third producers | 6,120 messages | 21,960 | none |
| Study 2, primary producer (60 worlds, 3 replicates) | 2,160 generated sets plus 1,080 stripped sets | 8,640 | 2,160 |
| Study 2, second and third producers (full-access neutral arm) | 1,080 sets | 5,400 | none |

Reader calls count both readers on the first replicate. At current list prices with batch processing and caching of the fixed in-context examples, the whole program costs about $25 to $75, and the calls run in parallel across world blocks, so the full run takes one to two days of wall-clock time. The build specification gives the breakdown. The replicate count of three per world and condition is fixed. World construction, prompt drafting, matcher annotation, and audit review take human time that these figures do not include.

## Part VIII. Analysis plan

- **Evaluation.** Outer five-fold cross-validation grouped by world, with the 60 worlds assigned to folds of 12 by a seeded draw balanced on event type, fixed before the verification run. Metrics are computed on pooled out-of-fold predictions. Regularization is chosen by four-fold world-grouped cross-validation within each training set. There is no separate holdout set.
- **Learner.** L2-regularized logistic regression on standardized features, multinomial for multiclass contrasts, with the penalty chosen from 0.01, 0.1, 1, and 10.
- **Metrics.** AUC for binary contrasts and macro one-versus-one AUC for multiclass contrasts are primary. Accuracy, balanced accuracy, macro-F1, multiclass Brier score, and log loss are secondary.
- **Labels.** Study 1 contrasts are binary or multiclass as named in Part V. Study 2 sets carry a three-class structure label, and each of a set's three pairs carries a shared-root label.
- **Estimand.** The primary estimand is the out-of-fold performance of the prespecified learning procedure on the fixed 60-world split, conditional on the registered template pools and the fitted fold models. It does not include the uncertainty of retraining on newly sampled worlds or of new instructions.
- **Intervals.** A world-cluster bootstrap resamples whole worlds with all their blocks and out-of-fold predictions, 2,000 times, so that every text sharing a key or descending from a shared synthesis output stays with its world. Intervals are percentile intervals.
- **P-values.** For P2 and P3, the p-value comes from the centered world-cluster bootstrap. With observed statistic T (AUC − 0.5 for P2, ΔAUC for P3) and bootstrap replicates T*, the p-value is the proportion of replicates in which T* − T is at least T. The pairwise and pooled models' predictions for P3 come from the same sets in each replicate, so the interval for ΔAUC is paired.
- **Templates.** The template pools are treated as fixed. Sensitivity to them is reported as secondary: prompt-family transfer (H6) and results by source template. No claim is made about robustness to instructions outside the registered pools.
- **Records.** The number of unique generated messages is reported alongside the number of labeled records.
- **Prompted reader.** The reader receives the message text, or the three texts of a set in random order, with neutral descriptions of the label classes that do not use condition names, and labeled examples from the fold's training worlds, the same for every test item in the fold: 16 for binary tasks (eight per class) and 18 for three-class tasks (six per class), drawn by a fixed seed. It returns a probability over the labels in JSON at temperature 0. An invalid output is retried once, and if it is invalid again it is scored as a uniform distribution and counted. Reader and classifier results are compared descriptively, as prediction performance under different supervision, not as evidence about method families.
- **Interactions.** The prespecified secondary interactions are genre and producer with R1 versus R3 and with P2, access with structure in Study 2, and message-length tertile with P2 and P3, each with bootstrap intervals. All other subgroup results are descriptive and shown with their counts.
- **Configuration.** A machine-readable configuration records every item above, and the analysis code is tested on synthetic data before the verification run. Verification-run data are kept out of the main analyses.

## Part IX. Execution sequence

The work runs in three stages.

1. **Build.** Complete the original-lineage check (Gate 1 below), build the new dispatcher, worlds, prompt pools, and analysis code, and test the analysis code on synthetic data.
2. **Verify.** Run the verification run on the 10 reserved worlds. It checks that the implementation works as specified: the lineage audit passes on every condition, every request is stateless and contains only its parents' texts, shared keys read the same stored output, all producers and readers respond in the expected format, packages, co-location, and template assignments match their rules, the attribution field is produced and parsed, and the failure and retry policy behaves as written. Defects are fixed in the code and the affected checks are rerun. F1 is dropped if the single-input synthesis preflight fails.
3. **Run in full.** Run every condition in Parts IV and V at the stated scale.

| Gate | Test | If it passes | If it fails |
|---|---|---|---|
| 1 | Lineage of the original study documented against its code, source-to-record correspondence checked, and the new dispatcher's lineage audit passed in preflight | The original lineage is documented, and the new pipeline is cleared to generate. Reproduction of the original numbers is a separate check on the deposited data. Neither establishes the original structural interpretation, which the lineage findings already contradict | The defect is repaired before any generation |

Every contrast runs at full scale and is reported. A null result on any contrast is reported with its interval, as no detected difference at this design's precision, and is not read as evidence that the property is unrecoverable.

## Part X. Claims

The paper reports engineering validation separately from findings. Pipeline isolation and lineage correspondence show that the instrument works as specified. They are not findings about communication.

If P2 and P3 succeed and P1 does not find a leak, the paper can claim, for small message-production graphs built from the tested language models, worlds, and genres, that independent versus shared production of a synthesis's inputs leaves a recoverable difference in the synthesis under matched instructions, and that shared ancestry among messages in a set is recoverable from relations among them. The shared-deviation account of the second claim requires the support condition in H8 and the full-access arm. The secondary estimates describe how much trace depth, partitioned observation, and downstream rewriting leave, and how the primary results transfer across prompt family, genre, and producer. Each claim names its contrast in Part IV. Together they answer the question at the top of this document for the tested setting. Transfer to human communication would need evidence this build does not collect.

The original study appears as a demonstration that protocol-confounded designs report high accuracy for properties the observed message cannot contain. A correction audit in the supplement lists which original quantities reproduce from the deposited data and which conclusions are withdrawn. The compound result is reported as an implementation defect, not as evidence about recovering compositions.

## Part XI. Field anchor

No field anchor is planned, and the paper makes an in-silico methodological claim only, unless Eric decides otherwise (open decisions). The candidates considered earlier support different validity checks and depend on licensing outside the project's control. A weakly matched external corpus would be worse than a stated synthetic boundary.

## Part XII. Deferred

None of the following is part of this paper.

- **Open-weight producers.** Adding open-weight models, including Llama 3.1 8B, the original paper's producer, is one more producer entry in the build once this run works.

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

1. Who codes the 240-message natural sample, and who codes the 60-message agreement subset. Both must be uninvolved in the design. The coding takes roughly 25 to 40 hours for the first coder and 6 to 10 for the second, at an estimated five to eight minutes per message, to be confirmed on the first ten messages.
2. Whether to omit the field anchor, as this design assumes.
3. Approval of the model choices in the build specification.
4. The target journal. The bounded framing in Part X suits a methods venue in machine learning or computational social science better than a complexity journal.

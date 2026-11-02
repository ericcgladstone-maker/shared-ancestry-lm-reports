# GPT Review of v8 (2026-10-30)

# 

Updated technical review of the current v8 design and Build Specification, Version 1, as retrieved on October 30, 2026\. This supersedes the earlier version of this review, which assessed a local-Ollama build. The current build uses hosted APIs, three producer families, two reader families, and store-once generation. Scope: predicting production structures correctly and efficiently in an exploratory controlled experiment. No preregistration, freeze requirement, or procedural-governance recommendation is made.

# BOTTOM LINE

The five history attributes and all thirteen distinct Study 1 histories are correct for the seventeen listed generation conditions, assuming the independent graph fixtures match the intended ancestry. The pair of documents substantially resolves the v7 review at the level of experimental architecture. Several choices in the newly revised hosted-API build specification would still produce wrong ancestry data or an unreliable predictor if implemented literally. The most important are call-key identity, package construction, coherence between output heads, the producer-output validator, and the incomplete scoring and feature contracts. A strong reader and additional producer families improve coverage, but they do not repair those implementation defects.

The cheapest defensible approach is to retain the existing two studies and their generated conditions, correct the data and prediction contracts, and test those contracts on synthetic graphs and artificial predictions before spending the generation budget. No additional structure or external corpus is required.

# I. PART V-A: FIVE ATTRIBUTES AND THIRTEEN HISTORIES

Attribute audit. The attributes are (1) synthesis present on the ancestry, (2) synthesis fan-in of 0/1/2/3, (3) distinct ancestral observation roots of 1/2/3, (4) number of rewrites before synthesis of 0/1, and (5) rewrites after the root or last synthesis of 0/1/3/5. The fifth attribute is context dependent: without synthesis it is the total rewrite depth, while with synthesis it is post-synthesis depth. This is a valid coding of the restricted graph inventory, not a universal description of arbitrary networks. Use an explicit null/not-applicable value for rewrites before synthesis when no synthesis is present if a user-facing system might otherwise mistake zero for an observed absence of intervening rewrites.

H01. D0 and NC0: (no, 0, 1, 0, 0). Correct. Two unused NC0 siblings are outside the terminal ancestry.

H02. R1 and NCR1: (no, 0, 1, 0, 1). Correct. NCR1 siblings remain non-ancestral.

H03. R3: (no, 0, 1, 0, 3). Correct.

H04. R5: (no, 0, 1, 0, 5). Correct.

H05. F1: (yes, 1, 1, 0, 0). Correct.

H06. F2: (yes, 2, 2, 0, 0). Correct.

H07. F3: (yes, 3, 3, 0, 0). Correct.

H08. SD-same and SD-div: (yes, 3, 1, 1, 0). Correct. Their access differences are not ancestry differences.

H09. SI-same and SI-div: (yes, 3, 3, 1, 0). Correct.

H10. SD-same+1: (yes, 3, 1, 1, 1). Correct.

H11. SD-same+3: (yes, 3, 1, 1, 3). Correct.

H12. SI-same+1: (yes, 3, 3, 1, 1). Correct.

H13. SI-same+3: (yes, 3, 3, 1, 3). Correct.

There are four collapse pairs of generation conditions, each carrying the same output ancestry class: D0/NC0, R1/NCR1, SD-same/SD-div, and SI-same/SI-div. The access arms differ in factual inputs in the last two pairs, but the structural attributes appropriately ignore access. The thirteen histories follow from seventeen generating conditions minus these four merges.

Output contract: PARTLY RESOLVED. Part V-A defines a single-message input and a three-message set input and asks for probabilities over the attributes, histories, and within-set shared roots. The current independent attribute and history heads can output contradictions, such as P(synthesis=yes) that differs from the summed posterior over all synthesis histories. Cheapest fix: train the thirteen-way history head as the canonical distribution, then compute every attribute marginal by summing its compatible history probabilities. Separate attribute-head accuracy can be reported diagnostically without using inconsistent heads as simultaneous user-facing assertions.

Study 2 has an analogous issue. A set of three messages has five possible labeled ancestry partitions: IND, DEP, MIX with the shared pair (1,2), MIX(1,3), or MIX(2,3). Fit or derive one distribution over these five states. Sum its three MIX states for the three-class output. Derive each displayed pair’s same-root probability as P(DEP) plus the probability of the corresponding MIX partition. A single independent probability for each pair may otherwise disagree with the IND/DEP/MIX distribution. Each Bernoulli pair should have probabilities for same/different summing to one, not require the three pair probabilities across the set to sum to one.

The JSON contract still needs exact schema keys, stable history IDs, probability ordering, absent/out-of-domain behavior, and a confidence/uncertainty convention. The producer-side validator in Principle 9 is not a valid out-of-domain test for an arbitrary user message. Do not flag an otherwise usable shorter or differently formatted message as a structurally invalid input simply because it does not resemble a generated 220-word incident report. Maintain separate input parsing and production-output quality flags.

Class priors and selection. Equal numbers of trials per generating condition produce unequal frequencies for the thirteen histories because four histories each aggregate two conditions. These proportions are design frequencies, not an externally justified prior over unknown histories. Report macro, per-history, and overall accuracy, and label the population assumed by any posterior. For the selected logistic, embedding, or boosted model, choose one declared inner-fold target metric for the thirteen-class task and separately for the five-partition set task. Otherwise “best by inner CV” is not an executable decision rule. Confirm identical folds and data-access restrictions across models.

# II. MODEL ASSIGNMENT, REASONS, AND READER SUBSET

Three producers: DEFENSIBLE WITH SCOPE QUALIFICATION. Llama 3.1 8B Instruct preserves continuity with the original producer family. Qwen2.5 72B Instruct adds a much larger open-weight model from another lab. Gemini Flash-Lite adds a closed-weight API producer. These choices provide useful heterogeneity, but family, parameter scale, provider, instruction tuning, and open/closed status change together. They cannot isolate the effect of any one dimension, and three labs do not establish generality to all LLMs. The cheap fix is to describe these as three concrete generation environments and report producer-specific prediction and transfer, without attributing a difference uniquely to model size or openness.

Same-model continuity is qualified. A hosted Llama 3.1 8B endpoint may differ from the original locally served model in quantization, runtime, chat template, and sampling behavior. Record provider-specific underlying model SKU, quantization where exposed, exact request format, and model version. Do not describe the new outputs as an exact rerun of the original producer merely because the base model name matches. On an aggregator, pin the actual serving provider instead of allowing silent auto-routing to different providers.

Reader choice: DEFENSIBLE, but not a direct causal model comparison. Claude Sonnet 5.5 is a capable reader, and a cheaper OpenAI-family reader is a useful sensitivity check. However “low-tier OpenAI model” is not a model ID, so neither its capabilities nor costs can be evaluated until a concrete SKU is selected. A weaker second reader tests model dependence under unequal capabilities rather than independently identifying a reader-family effect. This is fine for the stated descriptive purpose. Specify both exact IDs and API versions, and use the same labels, in-context examples, input text, output schema, and scoring rules when comparing them.

First-replicate readers: ACCEPTABLE AS A COST REDUCTION. Reading the primary producer’s first replicate across all 60 worlds gives a complete world coverage and a coherent secondary reader study. It is not a test of replicate variation, nor do reader results transfer to the other two producers automatically. The critical fix is to evaluate a trained classifier on exactly that same first-replicate subset when presenting reader-versus-classifier performance. Comparing readers on one replicate with classifiers pooled across all three replicates conflates method and test-sample composition.

Budget-driven example reduction: NOT DEFENSIBLE AS STATED. The build says that if projected Anthropic spending exceeds available credit, the set reader’s examples fall from 18 to 9\. This would change the reader measurement task based on budget and could leave the two reader families with different demonstration inventories. Cheapest fix: use one common set-example count across both readers from the outset, or retain 18 for both and fund the small shortfall. If using 9, choose a balanced 3/3/3 set and regenerate example prompts consistently. Do not change only the more expensive reader’s supervision and then interpret the gap as reader performance.

Gemini thinking and model IDs: FIX THE API CONFIGURATION. “Gemini Flash-Lite” is not an exact endpoint identifier. The current Gemini 3.5 Flash-Lite API supports a minimal thinking level, but minimal does not guarantee that thinking is fully off. Declare the exact Flash-Lite SKU and its supported thinking setting. If an older Flash-Lite version can disable thinking, record that version and its availability rather than claiming “reasoning off” for a version that does not offer it. Claude Sonnet 5.5 is a documented model, and its API does not accept temperature, top\_p, or top\_k. The build correctly avoids assuming those controls on the main reader. See official provider documentation in the sources below.

Cost estimate: USE MEASURED BILLABLE TOKENS. The \$25–\$75 estimate assumes discounts, short outputs, and successful reuse of cached demonstration prefixes. Anthropic batch cache hits are best effort because requests may be processed out of order, and batches may slightly exceed the workspace spend limit. A hard cap is a budget safeguard, not a guarantee that the full design fits existing credit. Cheapest fix: calculate a worst-case no-cache estimate for every provider using the \*actual\* input and output token counts from verification requests, then retain money or credits sufficient to finish the already selected reader protocol. Treat the “one to two days” wall time as a planning assumption, not a validation property.

d

# III. DISPOSITION OF THE V7 MISTAKES-TABLE OMISSIONS

The prior review actually listed six omissions, although the current request refers to five. All six are addressed in v8’s expanded table.

OM1. Reader/classifier information and supervision confound: RESOLVED AT DESIGN LEVEL. Both receive text-only inputs and reader results are descriptive. Cheapest safeguard remaining: score both on the identical first-replicate test records when directly compared.

OM2. Overlapping feature constructs and the strong length baseline: RESOLVED AT DESIGN LEVEL. V8 calls the families operational groups and retains length features and ablation. The builder still must provide the exact original fourteen transforms, not just the label “original 14.”

OM3. Incompatible origin, fidelity, and calibration targets: RESOLVED. The original origin/fidelity tasks are dropped and calibration is tied to structural prediction.

OM4. Subgroup anecdotes without denominators: RESOLVED. Counts, world-level intervals, and bounded secondary interactions are specified.

OM5. Narrow cross-model evidence: RESOLVED IN COVERAGE, WITH SCOPED INFERENCE. Three producers and two readers improve breadth, but the second and third producers are not full Study 2 replications and model family/size/open status are inseparable.

OM6. Overgeneralization to human communication: RESOLVED. Claims remain restricted to the controlled LLM-production domain.

# IV. V7 BUILD FINDINGS, B1–B11, WITH CHEAPEST CORRECTIONS

B1, end-to-end predictor output: PARTLY RESOLVED. V8 supplies the thirteen-history task and three-message set task. Remaining gap: independent attribute/history heads and independent pair/class heads can contradict each other. Cheapest fix: derive attributes from one thirteen-way distribution and pair probabilities from one five-partition distribution, with a concrete JSON schema and class prior.

B2, graph and call identity: PARTLY RESOLVED, CRITICAL. Independent handwritten fixtures are now specified and store-once records replace brittle replay requirements. Remaining gap: the key fields omit factual package identity, exact parent/input hash, and an independent-draw ID, while including an attribution arm even for observations reused between arms. Distinct calls that happen to have identical prompts must remain independent when the graph requires independent roots. Cheapest fix: separate logical draw IDs from exact request fingerprints. Require key+draw identity to be unique for genuinely independent stochastic calls, even if prompts match. Before cache reuse, assert exact provider/model, request bytes, package IDs, and parent hashes. Explicitly map each neutral/concealment shared observation to the same upstream call ID. Do not rely on the string “shared” in condition\_class to determine equivalence.

B3, world and package construction: PARTLY RESOLVED, CRITICAL. The schema and approximate assignment algorithms are given. Remaining gap: shuffling all noncore propositions before round-robin F2/F3 allocation cannot ensure the required one co-located and one split conflict pair, and “equal share plus two overlap propositions between each pair” in SI-div is ambiguous relative to the common core. Cheapest fix: place constrained conflict propositions first, then balance the remaining propositions, and reject infeasible assignments. Define whether two shared propositions are noncore and establish exact pair intersections and union equality. Specify rounding for odd-sized Study 2 half-record packages and whether duplicate packages are permitted.

B4, model/prompts/runtime: PARTLY RESOLVED. Hosted-model roles, approximate decoding, genre lengths, and prompt-pool counts are chosen. Remaining gap: exact pinned endpoints, chat templates, actual literal node prompts, source formatting, provider defaults, and token budget are not yet build artifacts. “1.8 times target length in tokens” cannot be computed directly from a word target without a tokenizer rule. Cheapest fix: supply a machine-readable provider adapter and prompt inventory, track stop reason and truncation, and use token budgets measured by the actual endpoint.

B5, features and leakage boundaries: PARTLY RESOLVED. The text/set/anchored scope registry and training-fold fitting solve the main leakage interface. Remaining gap: actual rare-sequence frequency definition, n-gram tokenization, sentence-order comparator, embedding encoder/reduction, all fourteen legacy features, and missing-value rules. “At most two messages from other worlds” is not one prediction-time definition. Cheapest fix: compute document frequency over unique training-world texts with a consistent rule for both training and test, state whether repeated text within a world counts once, and test all six presentation permutations for identical set features and predictions.

B6, proposition matcher and null: PARTLY RESOLVED. Embedding alignment and value/negation checks are a concrete starting algorithm. Remaining gap: sentence-to-multiple-proposition matching, label precedence between altered/qualified/omitted, unsupported claims, and normalization of shared omission. In a short report about a roughly twenty-proposition world, independent outputs may omit the same facts for ordinary compression reasons. Cheapest fix: define semantic adjudication precedence, an independent full-access null within producer/genre/arm and training worlds, normalize for opportunity to mention each proposition, and run an inherited-deviation ablation excluding omissions. Keep anchored measurements out of deployable text-only learners.

B7, annotation/challenges: PARTLY RESOLVED. Coded natural messages, double coding, a web form, and script edits are specified. Remaining gap: coder rubric and rare-class agreement implementation, adjudication when coders cannot agree, and a challenge-set claim that only fifty human-checked edits suffice to certify all edited labels. Cheapest fix: use the authoritative proposition state to mechanically check straightforward edits and human-review all ambiguous or multi-proposition changes. Stratify the reviewed edits by class, function, and producer. The rating form must preserve distinct coder identities, blinding, revisions, and immutable judgment records. Cloudflare or another actual shared database is a concrete hosting route; the phrase “a claude.ai page with a shared database” is not an established deployable form specification.

B8, dataset and split: MOSTLY RESOLVED, ONE CRITICAL DISTINCTION. Immutable IDs and world-grouped folds are correct. However “texts stored once by hash” must mean content-blob deduplication only. Two independent calls can generate byte-identical text without sharing an ancestor, while one reused ancestral call can appear with multiple condition labels. Cheapest fix: preserve a distinct call/observation record for every logical draw and trial occurrence, and put each content blob in separate hash-addressed storage. Never infer shared-root labels from equality of output hashes and never collapse independent root IDs because the text is identical. Keep all labeled occurrences and group by world.

B9, output validation and retries: PARTLY RESOLVED, HIGH RISK. A 120-second timeout, length band and rejection patterns exist. The unconditional rejection of “the reports,” “the messages,” and “the input” is not a harmless format check. Synthesis may naturally use those phrases more often than direct observation, so retries would select different content by structure and create a new classifier shortcut. Cheapest fix: reject only unmistakable model/instruction disclosures, not ordinary content phrases, and record structure-specific retry/timeout and truncation rates. Keep Sources-field presence and validity as outcomes. State the initial attempt plus retry count clearly.

B10, learners/readers/evaluation: PARTLY RESOLVED. L2 logistic, embedding logistic, gradient boosting, no-refit transfer, and calibration measures are specified. Remaining gap: named selection metric per prediction task, L2 penalty parametrization, class/sample weighting, gradient-boosting leaf limits and early stopping, exact reader labels/JSON schemas, and a fair reader/classifier subset. Cheapest fix: select on grouped-CV multiclass log loss or another single declared target, use bounded tree depth and leaf size, and report macro metrics and proper scores for the model actually selected. Choose one reader example count across both families instead of reducing only Anthropic's.

B11, storage/resume/audit: MOSTLY RESOLVED, HOSTED-API QUALIFICATION. Append-only output manifests, fingerprints, single-call reuse, graph fixtures and miswire tests are appropriate. Remaining gap: fingerprints need actual serving provider and model snapshot, not merely aggregator SKU, and a key hit must be checked against the desired request before returning a cached output. Since hosted APIs may not accept or honor a seed, independence is from distinct logical calls, not guaranteed disjoint numerical seeds. Cheapest fix: log exact outgoing request/returned model identifiers, attach a draw ID, validate prompt and parent hashes on cache hits, and never silently continue across a provider version change. The store-once strategy is appropriate for a defined realized dataset, but identical outputs are guaranteed by reference to stored bytes, not by reproducible sampling.

# V. V7 PREDICTIVE-PERFORMANCE RISKS, P1–P7

P1, fragmented pairwise tasks: SUBSTANTIALLY RESOLVED. The new global thirteen-history and three-message tasks answer the user's prediction question. The remaining head-coherence and target-prior issues under B1 still affect whether the reported probabilities constitute a valid predictor. Cheapest fix: canonical joint posteriors and macro/per-history error profiles.

P2, too little independent-observer variation: UNRESOLVED EMPIRICALLY. Explicit temperature 0.8 where accepted and three producer families make the setting testable, but independent seeds/calls do not guarantee distinctive reports. Cheapest fix: measure realized root diversity, conflict choices, and feature retention by producer and output stage, and interpret weak prediction conditional on measured variation.

P3, loss of ancestry through downstream rewriting: COVERED AS AN EMPIRICAL QUESTION. Continuations and a correctly wired compound allow stagewise checks. Cheapest fix: report intermediate coverage, length and similarity alongside terminal history confusion, without labeling a null as universal graph indistinguishability.

P4, near-duplicate overlap instead of inherited deviations: PARTLY RESOLVED. H8 has separate text-only relational and world-anchored shared-deviation analyses. The shared-omission/null details in B6 still control the mechanism interpretation. Cheapest fix: report the generic-similarity benchmark and the omission-excluded anchored diagnostic, holding text-only input access fixed for the deployable predictor.

P5, uniform fictional worlds: PARTLY RESOLVED. Fourteen event types, seventy worlds, and a separate drafting family broaden inputs. Forced conflicts and one schema remain sources of regularities. Cheapest fix: inspect performance by event type and conflict difficulty rather than generalize to unrepresented records.

P6, linear models underfit subtle ancestry: SUBSTANTIALLY RESOLVED. The build now includes embedding logistic and histogram gradient boosting as alternatives. Remaining gap: fair model selection, constrained complexity, and explicit semantic comparator. Cheapest fix: use the same grouped folds, criterion and input scopes, with bounded tree parameters and an embedding/cross-text representation appropriate to each task.

P7, protocol and format shortcuts: PARTLY RESOLVED. Shared function prompts and independent graph fixtures prevent the original direct prompt-label path. Source-package, node operation, output length, and biased validator rejection can still predict the procedure. Some are legitimate properties of the treatment. Cheapest fix: audit feature contributions and failure rates by producer, condition, template, and genre, and report the particular operational ancestry recovered rather than a universal topology invariant.

# VI. V7 COMPOUND DIFFERENCE-TABLE FINDINGS, C1–C7

C1, unequal factual packages: RESOLVED. V8 gives the full world record to R5, SI-same, SD-same, and both downstream branches. The build promises explicit package-equality tests. Cheap remaining check: compare sorted canonical proposition IDs and their values, not package names.

C2, matching path length while varying node functions: RESOLVED. V8 names the substitution of synthesis for one serial rewrite and correctly treats the result as a procedure-level total effect.

C3, synthesis sees multiple inputs and more tokens: RESOLVED AT DESIGN LEVEL. V8 explicitly accepts input multiplicity, redundancy and exposure as components of the contrast and plans process measures. Cheap check: record actual upstream input token volume, unique factual coverage and conflicts at the synthesis node.

C4, three independent roots for SI-same+3: RESOLVED. V8 differentiates the broader SI-same+3 versus R5 effect from the shared-root SD-same+3 comparison.

C5, total upstream calls: RESOLVED. V8 correctly gives eight calls for SD-same+3, ten for SI-same+3, and six for R5. The longest path remains six calls in each.

C6, rewrite-template slot mapping: RESOLVED IN DESIGN. V8 maps compound rewrites to R5 slots r1, r3, r4 and r5 while synthesis occupies the r2 position, and separately maps auxiliary branch rewrites. The build still needs literal template IDs and correct call keys. Cheap fix: encode this mapping in the independent graph fixture, and assert the intended template equality or difference at each node.

C7, classifier labels for the compound: RESOLVED. H12 now includes SD-same+3 versus R5, SI-same+3 versus R5, and a three-class comparison. The global predictor also distinguishes the corresponding histories. These analyses reuse existing generated conditions and do not require a new composition graph.

# VII. CONSEQUENTIAL CROSS-DOCUMENT CONTRADICTIONS AND TECHNICAL CHOICES

K1. Call identity and source sharing are more important under hosted APIs, not less. The central benefit of store-once is that intentional shared ancestors have exactly one realized output despite nondeterministic providers. That benefit disappears if a key denotes two different logical calls. The key must carry the intended random-draw identity, and the cache must be checked against exact model/request/parent/package inputs. The current role/slot/depth-only scheme with condition\_class usually set to “shared” does not prove that identity. The stored record, not repeated API output, is the source of truth for downstream graph construction.

K2. “Seed is the only intended terminal difference” is no longer accurate in the literal sense. V8's H1 retains earlier wording that NC0/NCR1 terminal calls differ by seed, but the hosted build sends a seed only where the API permits it. The actual treatment comparison is two distinct terminal generations under matched factual inputs and prompts, with extra non-ancestral sibling executions. Describe and verify distinct call IDs and matched marginal sampling settings. Do not pretend a nominal hash seed controls an endpoint that does not accept one. H1 should be interpreted against the actual hosted provider state, and its result may be inconclusive at the world-level precision available.

K3. Store-once does not make unrelated independent outputs share a source. Texts should be deduplicated as bytes but not as graph nodes. A pair of identical strings from separately executed observation calls still has two roots. A shared observation reused between neutral and concealment rewrites has one root even if descendants look different. The graph's call IDs, not equality of content hashes, define ancestry labels.

K4. Three producer models are a robustness extension, not a balanced factorial of model characteristics. Llama 3.1 8B, Qwen2.5 72B, and Gemini Flash-Lite differ simultaneously in many dimensions. The cheapest defensible analysis is one cross-producer result per exact model environment, with no causal story that “size” or “closed models” explain differences. Open weights make rerunning feasible only to the extent that exact weights, quantization, prompts and runtime can be reconstructed. Hosted output archives replicate the realized dataset, not the sampled process.

K5. Explicit sampling settings must correspond to actual provider support. V8 still says sampling starts at each producer's documented defaults while the build file specifies temperature 0.8 and top\_p 0.9 wherever supported. Prefer the concrete build rule and record every accepted/rejected option per provider. Non-acceptance should be part of the model-environment descriptor, not silently ignored. For a Gemini 3.5 Flash-Lite endpoint, minimal thinking is supported but disabling thinking entirely is not promised. This makes cross-producer decoding behavior a difference to describe, not to wish away.

K6. The cost and concurrency forecast should be tested against actual payload sizes. A set-level reader prompt with eighteen labeled three-message examples can be far larger than a simple source-report prompt. Prefix caching inside asynchronous Anthropic batches is opportunistic. The cheapest correction is a no-cache upper-cost calculation and a single reader-example policy agreed across both readers. Choose a provider limit that allows completion rather than an incomplete set of structural classes. If funds are tight, reducing both set-reader demonstrations to nine consistently is less damaging to interpretation than reducing one alone.

K7. A useful predictor needs a defensible target prior. The thirteen structural histories are legitimate classes but are not equally frequent under condition-balanced sampling. For reporting, include both the empirical experimental-prior posterior and macro metrics that do not reward the four overrepresented histories disproportionately. If predictions are meant to be read as probabilities about an unknown message with an unknown natural history prior, report that no such deployment prior was estimated.

K8. The feature scope registry is necessary but not sufficient. Tested separation of anchored world features from text-only models prevents a direct label leak. It does not ensure that the rare n-gram frequencies are computed correctly, that word order features are permutation-invariant, that the input-label field never enters a text encoder, or that nested model selection excludes held-out worlds. Add unit tests that substitute adversarial world IDs, reorder the set, and check feature equality and fold isolation.

K9. The matcher is a mechanism instrument, not an oracle for the deployed predictor. Shared absence of a world fact is common when reports compress the source. Compare omission-inclusive and omission-excluded shared-deviation scores against the same independent-source null, conditioned on producer and report format. Without that check, the strongest claimed mechanism may be ordinary shared coverage constraints rather than inheritance.

K10. The exact model and reader prompts remain necessary build artifacts. The named Claude model exists and its provider explicitly does not accept sampling settings. The phrase “low-tier OpenAI model” does not identify a deployable reader SKU. Likewise “Gemini Flash-Lite” needs a specific supported version. Do not treat anticipated pricing as an identifier. A versioned provider adapter should record actual model IDs, provider routing, accepted parameters, response usage and stop reasons.

# VIII. CHEAPEST DEFENSIBLE BUILD REPAIRS, IN DEPENDENCY ORDER

1\. Repair canonical call IDs and store-once eligibility, using independent-draw IDs plus input/package/parent fingerprint checks and explicit cross-arm source reuse.

2\. Implement constrained F2/F3 conflict placement, clarify SI-div overlaps and Study 2 package rounding, and test every package invariant with synthetic worlds.

3\. Make single-message attributes marginals of the thirteen-history posterior and set pair probabilities marginals of a five-partition posterior. Define one task-specific model-selection criterion and a stable JSON output.

4\. Replace unconditional synthesis-associated forbidden phrases with precise model-meta-commentary detection. Report rejection and timeout rates by condition rather than silently recycling outputs.

5\. Preserve call identity separately from text-hash storage, and ensure world-grouped folds contain every labeled descendant.

6\. Supply literal prompts, exact host/provider/model IDs, token budgets and reader schemas. Score both readers and classifiers on a common first-replicate subset for cross-method comparisons.

7\. Establish a consistent reader-example inventory and calculate token/cost exposure without assuming batch cache hits.

8\. Calibrate the proposition matcher against natural and scripted cases, specify multiple-claim matching and omission-null normalization, and keep anchored features out of text-only prediction.

9\. Select learners with bounded capacity and grouped-fold validation, and report history-level confusion, proper scores and transfer across the actual three producer environments.

No new experimental condition, preregistration, freeze mechanism, pilot-based decision rule, or change of scientific question is implied by these repairs.

# SOURCES

Claude. (2026). Production structure recovery from communication artifacts: Study design, version 8 \[Exploratory study design, current revision\]. Google Drive. https\://drive.google.com/file/d/1UkeMZiWZPCuYZYGiBeEecbQ3Oy3Y3r7W/view

Claude. (2026). Build specification, version 1 \[Hosted-API implementation specification, current revision\]. Google Drive. https\://drive.google.com/file/d/1zMqrGRrY0aLvUbcDwKYlHIkNiyEQJDM-/view

GPT. (2026). GPT Review of v7 (2026-10-30) \[Technical review\]. Google Drive. https\://docs.google.com/document/d/1truAlIcmbpzj9NdQwlnmfpGcMPOFNVcYdSk3rCTOy44/edit

Anthropic. (2026). Claude Sonnet 5.5 model documentation. https\://platform.claude.com/docs/en/models/sonnet-5-5/overview

Anthropic. (2026). Batch processing documentation. https\://platform.claude.com/docs/en/build-with-claude/batch-processing

Google. (2026). Gemini 3.5 Flash-Lite model documentation. https\://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite

Google. (2026). Gemini model thinking documentation. https\://ai.google.dev/gemini-api/docs/thinking


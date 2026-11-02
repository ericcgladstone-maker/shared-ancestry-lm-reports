# Build Specification, Version 1

Prepared by Claude, 2026-10-30, as the companion to `Claude_Diagnosis_and_Redesign_v8_2026-10-30.md`. The design says what the system tests. This document says how it is built. It answers items B1 to B11 of `GPT Review of v7 (2026-10-30)`. Each section states the choices made now and the artifacts the build must produce, with the test each artifact must pass. Choices marked **proposed** need Eric's agreement.

## 1. Models and runtime

All models are commercial models called through hosted APIs at pinned versions, on Eric's three existing accounts. Every prompt and output is archived and released, which makes every analysis reproducible, although generation cannot be rerun once a model retires. Hosted APIs do not guarantee identical outputs for identical requests, so no part of the design depends on regenerating a call. The aim is the lowest cost that remains defensible, so each model's tier follows from its role.

**Producers.** The producers are the system under study, not the measuring instrument, so each is a lab's small tier, the kind of model that low-cost deployed pipelines use. Three labs make the producers three distinct generation environments. H6 compares them but does not separate the effects of lab, size, or training. Open-weight producers are deferred to follow-up work, which needs only a new producer entry.

**Readers.** The readers are measuring instruments, and a weak instrument invites the objection that it was not good enough, so both are a tier above the producers. Each reads only the primary producer's output, so no reader reads text from its own lab.

| Role | Model | Why |
|---|---|---|
| Primary producer | Gemini Flash-Lite (Google batch API) | Small tier, and the lab whose models no reader comes from |
| Second producer | Claude Haiku 5.5 (Anthropic batch API) | Small tier from a second lab, for H6 |
| Third producer | Low-tier OpenAI model (OpenAI batch API) | Small tier from a third lab, for H6 |
| Main reader | claude-sonnet-5-5 (batch, fixed examples cached) | A capable instrument |
| Second reader | OpenAI model one tier above the producer (batch) | A second lab's instrument |
| World drafting | claude-sonnet-5-5 | Worlds are identical across structures, so a family overlap cannot confound any contrast |
| Embeddings | nomic-embed-text, run locally | Open, standard, and free |

Status: approved by Eric on 2026-10-30. Before the smoke test, each price, version, and retirement date is confirmed on the provider's own page, and the exact OpenAI model IDs are chosen from OpenAI's model list at that time. The tiers above are the decision, and the IDs are its implementation.

**Decoding policy, one per provider.**

| Model | Reasoning setting | Sampling |
|---|---|---|
| Gemini Flash-Lite producer | Lowest supported thinking level (minimal), since it cannot be fully disabled | Provider defaults |
| Claude Haiku 5.5 producer | Thinking disabled, which the model accepts at effort high or below | Provider defaults, since current Claude models accept no sampling settings |
| OpenAI producer | Lowest supported reasoning effort, if the chosen model reasons | Provider defaults |
| Claude Sonnet 5.5 reader | Adaptive thinking at low effort | Provider defaults |
| OpenAI reader | Lowest supported reasoning effort, if the model reasons | Temperature 0 if the model accepts it, otherwise defaults |

Every producer runs at its provider's default sampling settings, so that no producer is tuned and the policy is the same for all three. Reasoning is set as low as each model allows, so that hidden reasoning changes the messages as little as possible and adds few billed tokens. The manifest records the exact settings sent and any reasoning tokens billed.

**Cost and time.** Estimates from list prices partly drawn from aggregator sites, with 500 to 1,500 input and 250 to 500 output tokens per producer call, and about 6,000 (single message) or 17,000 (set) input tokens per reader call:

| Component | Provider | Calls | Estimated cost |
|---|---|---|---|
| Gemini Flash-Lite producer (batch) | Google | about 24,000 | $2 to $8 |
| Claude Haiku 5.5 producer (batch) | Anthropic | about 13,700 | $1 to $5 |
| OpenAI low-tier producer (batch) | OpenAI | about 13,700 | $1 to $12 |
| Claude Sonnet 5.5 reader (batch, cached examples) | Anthropic | about 2,300 | $8 to $32 |
| OpenAI reader (batch) | OpenAI | about 2,300 | $8 to $22 |
| World drafting | Anthropic | 70 worlds | $1 to $2 |
| Smoke test and verification run | all | about 10% of the above | $2 to $8 |
| **Total, with 20% for retries** | | | **about $30 to $105** |

**Budget.** Credit on 2026-10-30, after Eric's top-ups: Anthropic $46.67 (projected $10 to $41), Google $24.99 (projected $3 to $9), and OpenAI $17.61 (projected $9 to $34). OpenAI is the only provider that could run short, and only at the top of its range. The dispatcher enforces a hard spending cap per provider at the available credit and stops before exceeding it. The verification run records actual tokens per call for every model, and each provider's full-run total is projected from those measurements before the full run. Any reduction of in-context examples to meet a budget applies to both readers equally, so that their comparison stays interpretable. API keys are kept in the macOS Keychain or in environment variables, never in files on Drive.

Calls run in parallel across the 180 world-replicate blocks, so wall-clock time is about one to two days, including batch turnaround, which can take up to 24 hours.

Each producer call's maximum output is 1.8 times the genre's target length in tokens. Every output, including the readers', is generated once and stored, and the manifest records each model's exact version string and the parameters sent.

## 2. Call keys, seeds, and the manifest

A call key is a JSON object with the fields world, replicate, block, study, condition_class, role, slot, depth, template_id, producer_version, genre, access_arm, and attribution_arm. Its canonical form is serialized with sorted keys and no whitespace. Condition_class is the condition's name for the NC0 and NCR1 terminals in the full run, and "shared" everywhere else, which implements the exception in principle 6. The seed is the first eight hexadecimal digits of the key's SHA-256, read as an integer, modulo 2^31 − 1. A retry adds the field attempt to the key.

The manifest is append-only JSON Lines. Each record holds the key, the seed sent (where the API accepts one), the provider and model version, the exact request bytes and their hash, the parent text hashes, the output text and its hash, the configuration fingerprint, the execution position, the timestamps, the attempt number, and the validation result. Each key is called once. A stored record is valid for a key only if the hash of its request bytes, which covers the model version, the prompt, and every parent text, matches the request the key would produce now. Distinct calls therefore cannot share a cached output by accident, and intentionally shared ancestors reference the same stored call. A key that already has a valid output is never called again, so every condition that shares the key reads the same stored text, and the run can be resumed at any point. A second valid record for the same key is an error. If a provider changes a model's version string mid-run, the run pauses for a decision.

**Test.** Every condition that shares a key reads the same stored record, every request contains only its own prompt with no conversation history, and every key-sharing pair across conditions has identical request bytes and parent hashes.

## 3. Graph fixtures and lineage audit

Each condition has a hand-written fixture listing its nodes, each node's function and parents, the terminal, and, for Study 2, the generation slots. The dispatcher builds its graphs independently of the fixtures. The audit compares every realized graph with its fixture, checks that each prompt contains exactly its parents' texts, and checks the compound fixtures' synthesis-to-rewrite edge.

**Test.** One deliberately miswired graph per function, including a compound that restarts from the world record, must fail the audit.

## 4. Worlds and package allocators

The world schema has the fields world_id and event_type, and, for each proposition, proposition_id, type, canonical text, value fields for numbers, times, and entities, entity aliases, core flag, in-world source, and conflict-pair membership. Each world has two conflict pairs of mutually incompatible propositions.

The allocators are:

- **F1 to F3.** The core goes to every observer. Conflict pairs are placed first, by the rotation in Part IV: the co-located pair goes to one observer, and the members of the split pair go to two different observers. The remaining propositions are then shuffled with the block seed and dealt so that counts differ by at most one. The allocator asserts the placement before any call is made.
- **SI-div.** Three packages, each the core plus an equal share of the rest, with a fixed overlap of two propositions between each pair. SD-div receives their union.
- **Study 2 pool.** Six packages of equal size per world, each the core plus a random half of the rest, drawn once per world. Each set draws three of the six without replacement.

**Test.** Unit tests check that the union is preserved, that co-location counts match the rotation exactly, that packages are equal where the design says so (including SD-same, SI-same, and R5 for the compound), and that the overlap sizes are correct.

## 5. Prompts

The build drafts twelve templates per function (six per family) for observe, rewrite, and synthesize, in the incident-report and news-brief genres, plus the neutral and concealment rewrite instructions. Each template states the genre's target length (220 words for the incident report, 150 for the news brief) and the output format. Inputs appear between neutral delimiters, with no count stated.

**Test.** A lint step rejects any template that names a structure, mentions other nodes, states an input count, or refers to downstream use. The synthesis wording also passes the F1 preflight in principle 1.

## 6. Output validation

An output is valid if it is nonempty, its length is between half and one and a half times the target, it matches none of the forbidden patterns, which are limited to talk about the task itself (references to instructions or prompts, to being an AI or a model, and refusals), and it arrives before a 120-second timeout. A failure is retried at the same node up to three times. The attribution line is never checked. A terminal failure marks the trial failed, and failures are counted by condition. Words such as "reports" and "sources" are ordinary in a synthesis, so they are never forbidden, because a pattern that rejected them would regenerate one structure more often than others. The verification run reports validation failure rates by node function and condition, and a pattern that fails one function disproportionately is a defect to fix before the full run.

## 7. Feature registry

Every feature is a named deterministic function with a declared scope: text (one message), set (several messages), or anchored (uses the world record or the matcher). Text-only models accept only text-scope and set-scope features. The registry enforces this, and a test fails if an anchored feature, a world identifier, or a key reaches a text-only model.

- **Formal (text).** Token, sentence, and type counts, type-token ratio, mean sentence and word length, punctuation density, and the original 14 features.
- **Attributional (text).** Counts of source, evidential, hedge, and uncertainty markers, from fixed lexicons.
- **Relational (set).** For each pair: Jaccard overlap of rare word 3- to 5-grams, cosine similarity of embeddings, and sentence-order similarity. A rare n-gram is one that appears in at most two training-fold messages from other worlds. Over a set's three pairs, each pairwise feature contributes its minimum, median, and maximum, so the features do not depend on presentation order.
- **Propositional (anchored).** The matcher's per-proposition states and conflict resolutions, and the shared-deviation statistic.

Vocabularies, rarity tables, scalers, and every other fitted transform are learned within training folds only.

## 8. Proposition matcher

The matcher aligns each message sentence to world propositions by embedding similarity, and checks values (numbers, times, entities, through aliases) and negation. Each proposition is labeled preserved, qualified (hedged or attributed), altered (a value or polarity changed), or omitted. Each conflict pair is labeled by the member asserted, both, or neither. Text matching no proposition is counted as an unsupported addition.

A shared deviation is a proposition that two messages both omit, or both alter to the same value, or a conflict pair both resolve the same way. Omission of a proposition absent from both messages' packages does not count. Each proposition counts at most once per pair. The null is the mean shared-deviation count for independent full-access IND pairs in the same training fold, by event type, smoothed toward the overall mean with weight 5.

## 9. Annotation

The codebook defines the unit (message by proposition, and message by conflict pair), the labels in section 8, and rules for ambiguity. The 60 double-coded messages are drawn by stratified random sampling. Agreement is Cohen's kappa where a class has at least 10 instances, and percent agreement with counts otherwise. Disagreements are adjudicated by the two coders against the codebook. Scripted challenge edits are applied only to propositions whose natural state the coder recorded. At most two edits come from any one base message, and a human checks a sample of 50 edits for correct labels.

## 10. Datasets and splits

Every world, block, call, text, set, pair, edge, generation slot, and presentation position has an immutable identifier. Texts are stored once and referenced by hash, so a text shared across conditions is one record with several labels. Folds are assigned by world, and every descendant of a world stays in its fold. Labels for the predictor's attributes and histories come from the fixtures, never from condition names in the text.

## 11. Training and evaluation

- **Learners.** L2 logistic regression (lbfgs, standardized features, no class weights, penalty grid as in Part VIII). Logistic regression on embeddings. A histogram gradient-boosted model with learning rate 0.05 or 0.1 and maximum depth 3 or unlimited, chosen by inner cross-validation.
- **Calibration.** Probabilities are used as fitted, and calibration is reported, not adjusted.
- **Transfer.** Transfer tests train on one producer, genre, or prompt family and test on the other without retraining.
- **Reports.** Each run reports confusion matrices, results by event type, paired model comparisons, and Brier scores.
- **Reader prompts.** Each reader prompt fixes the label descriptions, the order of the examples (shuffled by fold seed), and a JSON schema. An invalid response is handled as in Part VIII.

## 12. Human rating form

Coders work in a simple web form. It shows items one at a time, in random order, with no condition, structure, world, or model information, and shows the codebook beside each item. Each judgment is logged with a coder identifier and a timestamp, and nothing is overwritten. Revisions are new records. The double-coded subset is assigned so that neither coder sees the other's labels. The full judgment log is exportable as JSON and CSV and is released with the data. Hosting is decided at build time: Eric's Cloudflare setup, or a claude.ai page with a shared database.

## 13. Build order

Spending rises in four steps, and each step starts only when the one before it works.

1. **Offline, no spend.** Install the local embedding model. Then build the fixtures, allocators, key and seed code, manifest, dispatcher, lineage audit, feature registry, matcher, predictor, analysis code, and rating form against a mock model that returns canned text. Run every test on synthetic data, including deliberately miswired graphs that the audit must reject. Draft the world schema and prompt pools and pass the lint step.
2. **Smoke test, under $1.** Set up API accounts and keys, and confirm prices, versions, and retirement dates. Make a few calls to each model to check request formatting, response parsing, the store-once key logic, spending caps, and actual tokens per call.
3. **Verification run, about $3 to $8.** Draft and review the worlds, then run the 10 reserved worlds with every engineering check in the design. Project each provider's full-run cost from the measured tokens.
4. **Full run, about $25 to $75.** Only after steps 1 to 3 pass and every projection fits its credit.
5. **Human coding, after the runs.** Coders code the 240 verification-run messages in the rating form once all runs are complete. Their coding validates the matcher for the mechanism analyses. No earlier step waits on them.

Two habits keep the matcher from repeating the original study's mistakes. During the verification run, Claude or Eric inspects the matcher's output on about a dozen messages, only to catch implementation bugs such as missed numbers or broken alias matches. This is an engineering check, not validation, and it involves no coders. Second, if the coders' results lead to a fix, the fixed matcher is validated on a fresh batch of verification-run messages, never on the labels that motivated the fix. If the matcher falls short of its criteria, the mechanism claims are withheld under the fallback in the design, not explained after the fact.

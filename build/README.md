# Message residue build

Implementation of `redesign/Claude_Diagnosis_and_Redesign_v8_2026-10-30.md` according to `redesign/Build_Specification_v1_2026-10-30.md`. This folder replaces nothing in `prototype/`, which holds the original study's code.

The chronological record of what was done, what it cost, and where each record is lives in `LOG.md`. `runs/full/MANIFEST.json`, written by `python make_manifest.py`, hashes every record and output.

## Status

Step 1 (offline) is complete and step 2 (smoke test) has passed. Tests use mocks only. The adapters and scripts make real calls.

| Module | Contents |
|---|---|
| `residue/keys.py` | Call keys, seeds, request hashes. A key includes its parents' keys, so calls share a stored output exactly when their inputs are identical |
| `residue/worlds.py` | World schema and a synthetic generator for tests |
| `residue/allocators.py` | Package allocators for F1 to F3, SI-div, and the Study 2 pool. Each asserts its own rules |
| `residue/graphs.py` | Graph builders used by the dispatcher |
| `residue/fixtures.py` | Hand-written reference graphs and the history table, independent of the builders |
| `residue/histories.py` | History attributes from ancestry, and the derived attribute and set probabilities |
| `residue/store.py` | Store-once manifest, output validation, and retries |
| `residue/prompts.py` | Loads the pools, assigns templates per block, renders prompts with matched genre and format lines, and lints every instruction |
| `residue/models.py` | Mock model |
| `residue/dispatcher.py` | Realizes condition graphs for a block through the store |
| `residue/audit.py` | Lineage audit against the fixtures |
| `residue/features.py` | Feature registry with declared scopes (text, set, anchored). Text-only models are blocked from anchored features. The Sources line is excluded from formal features. Set features are order-invariant. Rarity tables are fit on training-fold texts only, which the caller must restrict to other worlds |
| `residue/matcher.py` | Proposition matcher, deviations, shared deviations, and the independent-pair null |
| `residue/analysis.py` | World-grouped folds, nested penalty selection, out-of-fold predictions, world-cluster bootstrap, centered p-values, three-way rule, Holm |
| `residue/predictor.py` | Structure predictor: 13-history head with derived attributes, and the five-configuration set head, text only |
| `residue/worldgen.py` | World drafting prompt, schema checks, resumable drafting, bank load and save |
| `residue/adapters.py` | Provider adapters with Keychain keys, decoding policy, token accounting, and hard spending caps |
| `smoke_test.py`, `draft_worlds.py`, `make_world_review.py` | Step 2 smoke test, world drafting, and the world review document |
| `rating/index.html` | Rating form for the human coders (blind, randomized, append-only log, JSON and CSV export) |
| `prompts/pools_v1.json` | Prompt pools, revised with all 13 edits in `redesign/GPT Review of Prompt Pools v1 (2026-10-30)`. The file's version field reads pools_v2 |

| `residue/embed.py` | Local nomic-embed-text embeddings through Ollama, cached on disk by text hash outside Drive (`~/.cache/residue/`), with the model digest recorded per run |
| `residue/readers.py` | Prompted readers: neutral class descriptions, fixed examples per fold, JSON probabilities, one retry, uniform on failure, append-only log |
| `run.py` | The verification and full runs: plan, code snapshot, parallel generation through the store, and the verification checks and report |

Still to do: batch-API submission for the full run, decided after the verification run's cost projection.

## Reproducing the system

Everything needed to rebuild the system and run new tests on it is in this folder and in `redesign/`: the design (`Claude_Diagnosis_and_Redesign_v8`), the build specification, the code, the prompt pools, the world bank with every drafting, repair, and hand-edit record, and every model call with its exact prompt and output. Hosted models do not return identical outputs for identical requests, so a rerun produces new texts from the same system, and the original texts are reanalyzed from the stored outputs.

1. Python 3.9 or later. Create a virtual environment and install the pinned dependencies: `python -m venv .venv && .venv/bin/pip install -r requirements.txt`.
2. Run the tests, which use mocks and make no calls, from this folder: `.venv/bin/python -m pytest`.
3. Set `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, and `GEMINI_API_KEY`. If an environment variable is missing, the adapters fall back to the macOS Keychain entries named in `residue/adapters.py`. Set `CAPS` in the same file to your own credit for each provider. The adapters refuse any call that would exceed its cap.
4. Smoke test, about one cent: `python smoke_test.py`.
5. World bank: `python draft_worlds.py`, then `python repair_worlds.py` for worlds the checker flagged, then `python hand_edit.py edits.json` for any edits by hand, which are logged with before and after text. `python make_world_review.py` writes the review document. To reuse this study's worlds instead, keep `worlds/bank.jsonl`.
6. Embeddings: install Ollama, run `ollama serve`, and `ollama pull nomic-embed-text`.
7. Verification run: `python run.py verification`, or `--dry-run` first, which uses mock models and spends nothing. It writes `runs/verification/`: `calls.jsonl` (every producer attempt with its exact prompt, request hash, seed, output, usage, and code hash), `reader_calls.jsonl`, `preflight_judgments.jsonl`, `matcher_spot_check.json`, `config.jsonl`, `code/<hash>/` (a copy of the code, pools, and world bank that produced the run), and `report.md`.
8. Re-verification under the final rules: `python run.py verification --tag v2` writes `runs/verification_v2/`, which adds `preflight_f1_judgments.jsonl` and `generation_summary.json`. The first verification pass stays in `runs/verification/`.
9. Full producer run: `python run.py full`. Runs resume, so an interrupted run is restarted with the same command.
10. Reader stage: `python run.py readers`. It rebuilds the primary producer's first-replicate results from `runs/full/calls.jsonl` without calling any producer, builds one group of reader prompts per task (or Study 2 access and arm) and evaluation fold, with examples only from the fold's training worlds, and writes `runs/full/reader_calls.jsonl`. It resumes the same way. The embedding server is needed only for verification and analysis.
11. Analyses, in the order and with the arguments given in `LOG.md`. To reuse this run's embeddings, decompress `runs/full/embeddings/embeddings.jsonl.gz` to `~/.cache/residue/embeddings.jsonl` and check its hash against `runs/full/embeddings/source.json`.
12. Record: `python make_manifest.py`.

Model IDs, decoding settings, and prices are in `residue/adapters.py`. The study's own environment lives outside Drive, in `~/.venvs/residue-build`.

## Findings from the build so far

- SD-div is identical to SD-same. SD-div's observer receives the union of the SI-div packages, which is the full world record, so with store-once keys every SD-div call is an SD-same call. The level-3 contrast is SI-div against SD-same.
- Store-once keys share more than the design's per-condition call counts assumed. Chains share prefixes, one root observation serves D0, F1, the chains, and the same-package independence conditions, and SI-same's slot-1 input is R1's terminal. A full block needs 44 Study 1 calls rather than 61, and 13 Study 2 calls per access level rather than 24. This follows the design's pairing rule and lowers cost.

## Smoke test findings (2026-10-30, about one cent)

- All five models work: gemini-3.5-flash-lite, claude-haiku-5-5, and gpt-6-luna as producers, and claude-sonnet-5-5 and gpt-6.1-terra as readers.
- OpenAI accepts reasoning_effort "none" but not "minimal". Gemini 3.5 rejects a thinking budget of 0 and ignores small budgets (a budget of 1 still produced about 670 reasoning tokens and truncated the report), so the Gemini adapter calls the REST API with thinkingLevel MINIMAL, which the SDK available for Python 3.9 cannot send.
- Report lengths differ by producer: about 270 words for Haiku and about 145 for Gemini and Luna, against a 220-word target. All pass validation. Comparisons are within producer, so this is a property of the generation environment.
- Gemini and Luna rewrites kept two of five sources, an early example of the inherited deviations the study measures.
- Python 3.9 is past end of life. It works, but a move to 3.11 would allow the current Gemini SDK.

## World bank findings (2026-10-30)

- Version 1 (archived in `worlds/v1/`, $1.21) passed every mechanical check but failed GPT's semantic review. The schema marked conflicts with a 0/1 field, which the drafter read as member order in nine worlds, so the parser paired a cause with a count. Other defects were background facts or cores that settled a dispute, sources that could not know their facts, disputes over different populations or nonexclusive causes, and 50 worlds over the six-source limit, which the parser never enforced.
- Version 2 makes each dispute an explicit object, closes and counts the source list, shuffles sentence order by world ID, passes already used invented names to the drafter, and has GPT-6.1 Terra (high reasoning) check every draft sentence by sentence, redrafting with its reasons up to four times. In a trial world the checker at medium effort passed a fact that favored one dispute claim; at high effort it caught it. Neither setting caught a class instructor given as the source of a technical finding until the prompt named that case. The checker is a filter, not a guarantee, so the bank still gets GPT review and a read by Claude.
- Version 2 drafting needed 4 or more attempts for 34 worlds, and 24 had no attempt that passed within four. `repair_worlds.py` repaired those in place (the drafter changes only the sentences the checker named, then the checker re-reads), which cleared 20. Claude hand-edited W003, W051, and W053, plus W011, whose time dispute set two devices' records against each other and had passed the checker. `hand_edit.py` logs each edit with its before and after text in `worlds/hand_edits.jsonl` and has the checker re-read the world. All 70 now pass. The checker caught two defects in Claude's own first hand edits (claims phrased as what two records say, which can both be true) and one inconsistency in W011 that predated the edit.
- An overlapping run. The first, sequential v2 run was meant to be stopped when drafting moved to parallel threads, but the stop command matched "python" and the macOS process is named "Python", so it kept running for about 30 minutes. It drafted W000 to W011 a second time into the same log and overwrote the ledger with its own running total. It never finished, so it never wrote the bank. The parallel run's drafts are the bank (`worlds/bank_before_repair.jsonl` is that bank before repair), and `repair_worlds.py` now identifies them by matching text rather than taking the last accepted log entry. W006 and W007 had first been repaired from the overlapping run's drafts and were repaired again from the bank's.
- The ledger now re-reads its file under an exclusive lock on every check and addition, so concurrent processes add to one total. The total for the period of the overlap was reconstructed as an upper bound, taking each process's own spend at its largest possible value. Spend through the finished v2 bank: about $8.00 Anthropic and $5.94 OpenAI by that bound, including v1 and the smoke test. Provider consoles give the exact figures.
- GPT's review of version 2 (`redesign/GPT Review of World Bank v2 (2026-10-30)`) recommended use after targeted fixes, with no redraft and no prompt change. It found facts that settle or favor a dispute that the checker had passed (W003 p02, a 41-minute run that fits neither restart time; W020 p09, a duplicate of one claim, and p19, automatic failover against a manual activation claim; W063 p02 and W066 p15), source asymmetries (W001 p16, W011 p11), and sentences that need another sentence to be understood ("The same logger", "She"), which matter because partial-access arms receive subsets. Claude applied GPT's replacements, mostly as written (`worlds/edits_gpt_v2_review.json`, logged in `worlds/hand_edits.jsonl`). The changes: claim texts kept plain rather than carrying their own attribution, W010's "Colm The" renamed throughout, including the source list. Claude also made fixes GPT did not list: the W011 core moved from about 04:10 to shortly after 04:00, so the outbreak no longer follows the 04:06 alarm; the W063 412 kg load reading, which favored the larger passenger count, was made neutral; the W057 crew dispute was relabeled from measurement to count; and a bank-wide scan for missing antecedents turned up W016 p16, W022 p16, and W031 p12. On re-reading, the checker flagged an unedited W039 sentence placing the nurse in the ward, which favored her count, so it was replaced with the ward's bay count. All 70 pass. The bank before these edits is `worlds/bank_before_gpt_v2_edits.jsonl`. A future checker should be tested on known defects of these kinds (a duplicate of one claim, inconsistent time arithmetic, a source that cannot know a time, a missing antecedent) before it is trusted.

## Verification run findings (2026-10-30, about $4.80)

- The lineage audit, key sharing, template assignment, co-location rotation (5 and 5), stripping (180 of 180 exact), and reader formats passed. The audit first flagged 14 prompts. In each one, a producer had copied its input, so a child's text was part of its parent's. The audit now allows a text contained in an allowed parent's text.
- Driver bug: the output cap assumed 4/3 tokens per word, and Haiku uses about 2.0, so 425 of 510 Haiku outputs were truncated and lost their Sources line. Caps are now set per producer. Gemini and Luna keep 4/3, which is within rounding of their measured 1.32 and 1.36, so their stored requests are unchanged. The truncated records are in `runs/verification/calls_superseded_haiku_token_cap.jsonl`.
- Matcher bugs, fixed on the spot check, which is not validation: alignment now runs from each proposition, so one sentence can carry several. The threshold is 0.86, because unrelated propositions reach 0.81 with nomic-embed-text. Number words, thousands separators, and spelled clock times are normalized. A negation elsewhere in a sentence no longer alters a proposition whose values are all present. Known weakness: reversed sequence claims.
- The preflight judge, version 1, flagged the required Sources line and in-world disputes copied from the input, which would have dropped F1 (9 of 50). Version 2 sees the inputs and judges the body, and flags 0 of 150. Both are kept, and the decision is with GPT's review.
- Open: Haiku writes 330 to 376 words for a 220-word target, so 109 Haiku trials fail the 1.5 times length window. Lower effort does not shorten it. Gemini and Haiku also copy their input on 7% of rewrites, plus 10% and 28% near copies. Both are with GPT (`redesign/GPT_Brief_Verification_Run_Review_2026-10-30.md`).
- The readers dominate cost: Sonnet averages 10,100 input tokens per call, almost all of it fixed examples. The plan is producers synchronous at standard prices, and readers batched with cached examples.

## Re-verification and changes after GPT's review (2026-10-30)

`redesign/GPT Review of Verification Run (2026-10-30)` accepted the fixes, decided the two open questions, and asked for a narrow correction and verification pass before the full run. The changes, each a departure from the build specification or design where noted:

- Length validation counts the body only, excluding the final Sources line, and accepts 0.5 to 2.0 times the genre's target, inclusive, for every producer and genre. Design principle 9 said 0.5 to 1.5 and counted the whole text. Copies pass and are never retried.
- The output cap is ceil(2.2 times the target times the producer's tokens per word) plus 64 tokens for the Sources line, with tokens per word at the 99th percentile measured on the first pass (Gemini 1.45, Haiku 2.3, Luna 1.45). The build specification said 1.8 times the target. Every attempt records its stop reason.
- F1's preflight now uses F1's own input: 50 single-input syntheses of full-record observations, 10 of them F1's realized syntheses, judged by judge version 2.
- New checks: planned against realized conditions by producer, reconstruction of every stored request from the fixtures and the renderer with prompt and request hashes compared, the package rules checked on realized records for every producer, stripping compared with an independently written rule, exact source-name equality alongside substring matching, and the number of R5 rewrites that changed the text.
- Readers. Five Study 1 tasks were added so that every one of the 17 conditions is read (R1 against NCR1, SI-div against SD-div, SI-same+1 against SD-same+1, SI-same+3 against SD-same+3, SD-same+3 against R5), with R1 against R3 on the second genre. The Study 2 set reader returns five configuration probabilities, from which the structure probabilities and pairwise same-root probabilities are sums. Readers run synchronously with the fixed examples cached, rather than through the batch APIs the build specification named, because cache hits inside a batch are best-effort and the cached synchronous price is lower: Anthropic reads cost 0.1 of input, and gpt-6.1-terra cached input is listed at 0.05. gpt-6.1-terra wrote a cache on every call but never read one for prompts differing after a shared prefix until the prefix carried an explicit `prompt_cache_breakpoint`. Its uncached verification reader calls are in `runs/verification_v2/reader_calls_superseded_terra_no_cache.jsonl`.

Re-verification (`runs/verification_v2/report.md`, about $2.10 Anthropic, $1.20 OpenAI, and $0.14 Google): all 730 planned conditions realized with no failed trial, 4 of 1,834 attempts invalid (meta-commentary only), no output stopped at the cap, 0 of 1,830 request reconstructions mismatched, 0 package problems, stripping 180 of 180, and 0 of 50 F1-input preflight syntheses flagged, so F1 is kept. Copying: Haiku 11% identical and 22% near copies, Gemini 7% and 10%, Luna 0% and 6%. In R5 chains, 3 to 5 of the five rewrites changed the text. Exact source names are about 80% for Gemini and Haiku and 35% for Luna, whose names usually contain the in-world name rather than equal it. Every reader reply parsed on the first try. Caches were read on every call after a group's first.

Projection for the full run from these measurements: Google about $2.40, Anthropic about $29.90 ($4.00 Haiku and $25.90 Sonnet), OpenAI about $6.90, against about $24.70, $32.70, and $14.80 remaining under the ledger caps. Without caching the readers would cost about $96 Anthropic and $25 OpenAI. The Anthropic margin is about 9%. A reader stage that reaches the cap stops cleanly and resumes after credit is added.


## Structure names for reporting

Results, tables, figures, and variable descriptions name each structure by its network shape, with the condition code as a secondary label. Every graph is one-way, with stateless calls, so the design contains no circle, wheel, or all-channel network.

| Shape | Codes |
|---|---|
| Direct report | D0 |
| Direct report or single relay with dead-end branches (negative controls) | NC0, NCR1 |
| Linear chain of 1, 3, or 5 relays | R1, R3, R5 |
| Hub collecting from 1, 2, or 3 spokes with split access (in-star) | F1, F2, F3 |
| Hub collecting from three independent spokes | SI-same (full access), SI-div (overlapping access) |
| Diamond: one source fanned out to three relays and merged | SD-same (SD-div is identical) |
| Hub or diamond feeding a chain of 1 or 3 relays | SI-same+1, SI-same+3, SD-same+1, SD-same+3 |
| Three unconnected sources (Study 2) | IND |
| Out-star: one source, three relays (Study 2) | DEP |
| Y: two messages share an origin, one separate (Study 2) | MIX |

## Found in the first walkthrough (2026-10-31)

- The proposition matcher misreads ordinary output. In the hub's final message for W057 it marked as omitted five facts the message states (the two engines, the 2:16 call, the cleared ticket hall, the sailing's departure, and the detector carried into the corridor). In the diamond's it marked the servicing of the gas range as omitted although the message states it, and it read the boarding dispute as resolved for 90 minutes although the message gives no duration. Paraphrase, such as "two fire engines" for "two engines sent", appears to fall below the 0.86 similarity threshold. Propositional features and the anchored methods depend on the matcher, so it needs repair and its human validation before any of them is reported. The text-only analyses, which include P1 to P3, do not use it.
- `parse_sources` splits the Sources line on commas, but in-world source names contain commas ("Tamsin Rooke, ferry deck purser") and Gemini separates names with semicolons. The exact-name rates in the verification reports are therefore unreliable. The stored texts are unaffected. The parser needs to match the world's source names against the line rather than split it.

## Analyses of the full run (2026-10-31)

Run in order, all local, from the stored records: `python analyze.py` (primary and main secondary text-only results, `runs/full/analysis/text_only.md`), `python permutation_null.py 50` (exact permutation nulls for the direct-report control and hub against diamond), `python analyze_secondary.py 99` (`secondary.md`), `python judge_run.py` (the proposition judge, gpt-6.1-terra, about $5.60, `runs/full/judge/judgments.jsonl`), and `python analyze_anchored.py` (`anchored.md`, unvalidated).

- Rows are sorted before any model sees them. The first `analyze.py` run took rows in block completion order, which changes GroupKFold's inner folds and H7's message draw; its outputs are kept as `text_only_unsorted_rows.*`. The primary results did not change.
- The world bootstrap on fixed out-of-fold predictions understates uncertainty. For hub against diamond it gave one-sided p 0.010, against 0.14 two-sided from 50 permutations that refit everything. Permutation nulls are the basis for inference on the paired contrasts.
- The embedding learner separates the direct report from its dead-end control (AUC 0.553, beyond all 50 permutations), although the two requests are byte-identical except for the seed. In a first test of generation order among 1,080 identical requests, the embedding learner could not tell the earlier half from the later half (AUC 0.487), but the feature learner could, weakly (AUC 0.533, beyond all 30 permutations), so that test does not rule order out. The cause is unknown. The feature learner shows no difference (0.491), and the relay control shows none with either learner.
- The proposition judge (`residue/judge_matcher.py`) replaces the embedding matcher for anchored measures. On the W057 walkthrough messages it agrees with Claude's reading on which facts each message dropped and on both disputes, except that it counts the diamond's detector reading as stated where Claude noted the reading's location outside the kitchen door was lost. It has not been validated against human coding, so `anchored.md` is labeled unvalidated throughout.
- H11's world-free method is not built, because the design does not specify its reference corpus.

## Corrections after GPT's analysis review (2026-10-31)

`redesign/GPT Review of Full-Run Analyses (2026-10-31)`. Earlier analysis outputs are kept in `runs/full/analysis/superseded_v1/`.

- Sentence-order similarity was directional, so the set features changed with the order of the three messages. It is now averaged over both directions, and a test checks all six orderings. Every result using the relational features was recomputed.
- The secondary report's two permutation tests of the pooled and pairwise set models test each model's association with the label, not the gain between them. The gain is now tested in `inference.py` by a refitted world bootstrap.
- `inference.py` gives P1 and P2 refitted label-exchangeability permutations with 199 to 999 draws (one-sided for P2, as designed) and recomputes the Holm family on P2's permutation p and P3's refitted p. The conditional world bootstrap stays in `text_only.md` as the design's conditional estimand.
- Anchored measures count deviations only over facts a message's observation ancestor received, and the shared-deviation statistic is now the excess over a type-matched random-placement expectation for each pair. The fold-level constant it replaced had no effect, because standardization removed it. Ablations separate shared omission from shared affirmative departures. The ratio of AUC gains is reported as a ratio, not as a mediation fraction. "Full specification" is renamed "text plus seven judged counts", because unsupported additions and proposition order are not measured.
- Added: both five-relay composition contrasts and their three-class version, H7 by prompt family with its worst stratum, the structure predictor under three learners with the majority baseline (0.125), Brier score, recall by history, and accuracy by event type, a five-configuration set predictor, an audit of the direct-report control pairs with a pseudo-control test, and row counts for the unpaired transfer estimates.
- Remaining approximations: rare-n-gram tables are built on each outer fold's training worlds and reused inside inner folds and in the refitted bootstrap. The judge's output is not constrained to be consistent across fields: 11 of 2,662 messages have a dispute resolution that contradicts the judge's own fact states.

- Final inference (`runs/full/analysis/inference.md`): hub against diamond one-sided permutation p 0.023 (999 permutations); P3 gain 0.142, refitted bootstrap p 0.010 (the smallest 200 resamples allow). Both pass Holm at 0.05. The refitted P3 interval (0.092 to 0.265) is skewed above the estimate, plausibly because resampled training sets repeat worlds. A first version also labeled each world copy as its own group, so inner folds could split copies; that run is kept as `superseded_v1/inference_copies_split_in_inner_folds.*`. The conditional interval, 0.092 to 0.192, is the estimate to report.
- The direct-report control difference stands (embedding p 0.015, 199 permutations), and the audit rules out request, retry, stop-reason, and length differences. The pseudo-control, earliest against latest among other identical requests in the same block, shows no embedding signal (0.480), so generation order is not supported as the explanation. It remains unexplained.

## Replication, salience, and validation materials (2026-10-31)

See `LOG.md` for the sequence. `replicate.py` and `analyze_replication.py` (plan in `runs/replication/PLAN.md`, results in `runs/replication/analysis.md`): the direct-report control difference did not replicate with fresh seeds and randomized order, and hub against diamond did (feature AUC 0.568, one-sided p 0.005). `analyze_salience.py` (`runs/full/analysis/salience.md`, unvalidated): salience adjustment leaves the out-star's excess shared omission unchanged. `make_validation_sample.py`, `validation/`, `rating/index.html`, and `score_validation.py`: the judge's validation sample, rubric, form, plan, and scorer, waiting on coders.

## Relational checks (2026-10-31 evening)

`python analyze_relational_checks.py` (no model calls, about 18 minutes) writes `runs/full/analysis/relational_checks.md` and `.json`. It confirms that the five-configuration predictor is unchanged in all six presented orders. It also reports an ablation of the three relational feature families under two rarity fits. The fit used by `analyze.py`, `analyze_secondary.py`, `inference.py`, and `analyze_anchored.py` counts training rows' own texts, and sets in a block reuse identical messages, so rare overlap is near zero in training rows and is not used in the three-structure models. The second fit removes each training row's own world from the counts. It is now the canonical fit (`residue/features.py`, `WorldRarity`), adopted 2026-11-01 with the earlier outputs kept in `runs/full/analysis/superseded_v2_rarity/`. See `LOG.md`, 2026-10-31 evening and 21:40 onward.

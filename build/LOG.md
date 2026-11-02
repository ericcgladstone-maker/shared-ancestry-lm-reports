# Message residue: project log

This log records what was done, in order, how it was done, what it cost, and where each record is. `README.md` holds the technical findings and reproduction steps in more detail, and `runs/full/MANIFEST.json` holds a SHA-256 hash, size, and line count for every record and output. Times are local (EDT) and come from file timestamps and run logs. Paths are relative to `build/` unless they begin with `redesign/`.

The study asks whether, in a controlled environment, the communication structure a message passed through can be predicted from the message. Language models write and rewrite incident reports about invented events (worlds) along known graphs, and readers and classifiers try to recover the graph from the final texts. The work is exploratory, with no preregistration.

## How the record is kept

- Every producer, reader, and judge call is appended to a JSONL log with its exact prompt, request hash, seed, output, token usage, stop reason, attempt number, and the hash of the code that made it. No log is edited after writing.
- Calls are stored once under a key that includes the keys of their inputs, so a condition that shares inputs with another reuses the stored output rather than calling again. Analyses rebuild every result from the logs without calling any producer (`run.Frozen`).
- The code that produced each run is copied into the run folder under its hash: `runs/verification/code/`, `runs/verification_v2/code/`, `runs/full/code/d4956c30b9bf/` (producers and readers), `runs/full/analysis/code/296e96e9ac55/` (the analysis code behind the full-run analyses), and `runs/full/analysis/code/79e6672dc338/` (the same plus the replication, salience, and validation scripts), with `runs/replication/code/4a8ee551a337/` for the replication run, `runs/depth/code/11f936ef7106/` for the deeper-rewriting run, and `runs/full/analysis/code/4170f046d14a/` for the analysis code as of 2026-11-02, depth analysis included.
- When an output is replaced, the earlier one is kept beside it with a name that says why (`*_superseded_*`, `superseded_v1/`, `*_before_*`).
- Spending is tracked in `smoke/ledger.json`, which every process updates under a file lock and which refuses a call that would exceed the cap set for the provider in `residue/adapters.py`.
- The embedding cache, which lives outside Drive at `~/.cache/residue/embeddings.jsonl`, is copied to `runs/full/embeddings/embeddings.jsonl.gz` with its hash in `source.json`, so the analyses can be rerun with the same vectors.
- `python make_manifest.py` rewrites the manifest. Matching hashes on a rerun show that no record has changed.

## 2026-10-29 to 2026-10-30 morning: diagnosis and redesign

The npj Complexity submission was reviewed and redesigned through eight versions of `redesign/Claude_Diagnosis_and_Redesign_*` (v1 at 17:41 on 10-29, v8 at 13:06 on 10-30). GPT reviewed each round in Drive (`redesign/GPT Critique of Claude Redesign`, `GPT Diagnosis and Redesign`, `GPT Attack on Difference Table`, `GPT Review of v3` through `v8`, `GPT Confirmation of v4`), and both models wrote referee reviews (`redesign/Referee Review, Claude`, `Referee Review, GPT`, disposition in `Referee_Disposition_v6`). The brief for each GPT round is the matching `redesign/GPT_Brief_*` file. Version 8 is the design the build implements.

## 2026-10-30: build

- 13:31. `redesign/Build_Specification_v1_2026-10-30.md` written.
- 13:25 to 13:57. The `residue/` package, tests with mock models, and the prompt pools. GPT reviewed the pools (`redesign/GPT Review of Prompt Pools v1`), and all 13 of its edits were applied (`prompts/pools_v1.json`, version field pools_v2, `redesign/Prompt_Pools_v2_Current_2026-10-30.md`).
- 13:59. Smoke test (`smoke/`, about one cent). All five models responded. Adapter settings found then are in README, "Smoke test findings".
- 14:16. World bank version 1 (`worlds/v1/`, $1.21). It passed mechanical checks and failed GPT's semantic review (`redesign/GPT Review of World Bank v1`).
- 16:15 to 18:03. World bank version 2: 70 worlds drafted with a sentence-by-sentence checker (`worlds/draft_log.jsonl`), repaired (`worlds/repair_log.jsonl`), hand-edited with before and after text (`worlds/hand_edits.jsonl`), reviewed by GPT (`redesign/GPT Review of World Bank v2`), and corrected again. The final bank is `worlds/bank.jsonl`, with earlier states in `bank_before_repair.jsonl` and `bank_before_gpt_v2_edits.jsonl`. The assignment of worlds to the verification set, the full run, and the five outer folds is `worlds/assignment.json`. An overlapping drafting process ran unnoticed for about 30 minutes, and its effect on the ledger was bounded from above (README, "World bank findings").
- 20:25 to 20:38. Verification run on 10 worlds (`runs/verification/`, about $4.80). Lineage, key sharing, stripping, and reader formats passed. A per-producer token cap was found too low for Haiku, and the truncated records were kept (`calls_superseded_haiku_token_cap.jsonl`). The brief for GPT is `redesign/GPT_Brief_Verification_Run_Review_2026-10-30.md`.
- 23:18. GPT's review (`redesign/GPT Review of Verification Run`) set the final length rule (body only, 0.5 to 2.0 times the target) and output cap, and asked for new checks.
- 23:35 to 23:40. Re-verification (`runs/verification_v2/`, report in `report.md`). All 730 conditions realized, 0 of 1,830 request reconstructions mismatched, and 0 package problems. The OpenAI reader cache was found never to be read and was fixed with an explicit breakpoint, and the uncached reader calls were kept (`reader_calls_superseded_terra_no_cache.jsonl`).

## 2026-10-30 23:40 to 2026-10-31 00:36: full producer run

`python run.py full` on 60 worlds and 1,260 blocks with code `d4956c30b9bf` and run seed 20261030 (`runs/full/config.jsonl`). It made 32,974 producer calls (`runs/full/calls.jsonl`). Of 13,140 planned conditions, 13,139 were realized. One Haiku trial (W015, replicate 1, hub with overlapping access) failed validation four times for meta-commentary (`runs/full/generation_summary.json`). Gemini 3.5 Flash Lite is the primary producer. Claude Haiku 5.5 and GPT-6 Luna are the secondary producers.

## 2026-10-31 morning: readers, walkthrough, judge

- To 08:11. `python run.py readers` made 5,040 reader calls (Claude Sonnet 5.5 and GPT-6.1 Terra) on the primary producer's first replicate, with examples drawn only from each fold's training worlds (`runs/full/reader_calls.jsonl`). Every reply was valid.
- 08:08. `python make_walkthrough.py` wrote `walkthroughs/hub_vs_diamond_W057.md`, which follows one world through the hub and the diamond and quotes the stored outputs verbatim. Reading it showed that the embedding proposition matcher misreads paraphrase and that the Sources-line parser split names containing commas (README, "Found in the first walkthrough").
- 08:34. First `python analyze.py`. Rows had been taken in block completion order, which affects inner folds. Rows are now sorted, and that output is kept as `runs/full/analysis/text_only_unsorted_rows.*`.
- 08:42. `python permutation_null.py 50`, the first refitted permutation nulls (`runs/full/analysis/permutation_null.json`). They showed that the conditional world bootstrap understates uncertainty for paired contrasts.
- 09:15 to 09:23. The proposition judge (`residue/judge_matcher.py`, version judge-v1, GPT-6.1 Terra) replaced the embedding matcher for anchored measures. `python judge_run.py` judged 2,662 primary-producer message bodies in four stages (`runs/full/judge/judgments.jsonl`, 2,663 lines because one attempt was invalid and retried). The judge is not validated against human coding.
- 09:30. Brief for GPT's analysis review (`redesign/GPT_Brief_Full_Run_Analysis_Review_2026-10-31.md`).

## 2026-10-31 10:36 to 12:02: GPT's analysis review and corrections

GPT's review (`redesign/GPT Review of Full-Run Analyses (2026-10-31)`) found errors in the set features, the gain test, the anchored statistic, and the inference plan. All outputs from before the corrections are in `runs/full/analysis/superseded_v1/`. The corrections, detailed in README, "Corrections after GPT's analysis review":

- Sentence-order similarity made symmetric, so the set features no longer depend on message order (`residue/features.py`, 10:48, with a test over all six orderings).
- Refitted label-exchangeability permutations for P1 and P2 and a refitted world bootstrap for the P3 gain (`inference.py`). Holm recomputed over P2 and P3.
- Anchored deviations counted only over facts the message's observation ancestor received, and the shared-deviation statistic taken as the excess over a type-matched random-placement expectation, with ablations by event type (`analyze_anchored.py`).
- Analyses GPT found missing were added to `analyze_secondary.py`.
- The first refitted P3 bootstrap let inner folds split copies of a resampled world. It was fixed at 11:09 and rerun with `python inference.py p3`, and the earlier run is kept as `superseded_v1/inference_copies_split_in_inner_folds.*`. The P1 and P2 permutations in `inference.json` come from the run just before that fix, which changed only the P3 bootstrap.

Final runs, each after its code's last change: `analyze.py` (11:08, `text_only.md`), `inference.py` (11:14, `inference.md`), `analyze_anchored.py` (10:56, `anchored.md`), and `analyze_secondary.py 99` (12:02, 3,921 s, `secondary.md`). Run logs are `runs/full_*.log`.

## 2026-10-31 15:27: record

`make_manifest.py` written and run. It hashed 360 files, snapshotted the analysis code as `296e96e9ac55` (superseded after the replication by the snapshot named in the manifest), and copied the embedding cache (43,805 vectors, SHA-256 `8520c3c0766d…`, checked by decompressing and rehashing). This log was written.

## 2026-10-31 afternoon: adjudication of further tests

GPT proposed six further tests (`redesign/GPT Memo - High-Leverage Network Structure Tests (2026-10-31)`). Claude assessed them (`redesign/Claude_Assessment_of_GPT_Network_Tests_Memo_2026-10-31.md`), and GPT replied (`redesign/GPT Reply to Claude Assessment of Network Tests (2026-10-31)`). Both agreed that no network structure is added. Rejected or deferred: the one-, two-, and three-message curve, common-information masking, four-message partitions, and balanced against sequential merging. The agreed package: a fresh-seed replication of the direct-report control and hub against diamond, human validation of the judge with linked-text diagnostics, and a salience-sensitive reanalysis of shared omissions. GPT's corrections that Claude accepted: the aggregate-of-singles baseline uses all three messages, the P3 gain is not a lower bound on relational information, the control difference is specific to the embedding learner rather than a floor for every learner, the validation sample keeps v8's strata, and P2 is not conditional on P1, whose result was inconclusive rather than a leak.

## 2026-10-31 15:40 to 16:11: replication

`runs/replication/PLAN.md` fixed the comparisons and their readings before any call. `python replicate.py` (dry run first, which counted 2,700 calls) generated 2,701 Gemini calls, one of them a retry, with no failed trials, for $0.56 (`runs/replication/calls.jsonl`, code `4a8ee551a337`). The 60 full-run worlds had new replicates 3 to 5, all control blocks ran before any hub and diamond block, and the conditions within each block ran in random order. The control followed the direct report in 81 of 180 pairs, against 169 of 180 in the full run. `python analyze_replication.py` wrote `runs/replication/analysis.md`.

- The direct report against its dead-end control was equivalent under both learners (features 0.489 [0.458, 0.521], embedding 0.493 [0.471, 0.514]). The pure null and the direct report against a null draw were equivalent under both learners. By the plan's first reading, the full run's embedding difference (0.553) did not replicate, and the analysis pipeline does not separate arbitrary labels.
- Hub against diamond with the feature learner: AUC 0.568 [0.519, 0.620], one-sided permutation p 0.005 (999 permutations), against 0.552 and p 0.023 in the full run. The small single-message trace replicated. The embedding learner gave 0.480 [0.454, 0.504], p 0.895, a ranking slightly below chance under the fixed orientation.

## 2026-10-31 15:54: salience-sensitive shared omissions

`python analyze_salience.py` wrote `runs/full/analysis/salience.md` (unvalidated, exploratory, no calls). Undisputed facts only. A model of omission from fact characteristics, fitted on training worlds, barely predicts which facts are dropped (fact-level AUC 0.550). Under random placement, the held-out model, and a transductive same-world reference built from the world's own one-relay chains, the out-star's excess shared omission over three unconnected sources is 0.79, 0.79, and 0.78 events per pair. The same-world reference lowers the excess among three unconnected sources from 0.76 to 0.50, so salience accounts for part of independent writers' convergence but for none of the difference between the structures, which are compared within the same worlds.

## 2026-10-31 16:00 to 16:30: judge validation materials

`validation/PLAN.md` sets the procedure and criteria before any coding. `python make_validation_sample.py --judge` drew 240 messages from `runs/verification_v2/` (80 per producer, stratified by study and node function, 12 linked out-star and chain units of 4 messages, 60 for the second coder) and judged them with judge-v1 for $0.52 (`validation/judge/judgments.jsonl`, kept from the coders). `validation/RUBRIC.md` is the coding rubric, with GPT's precedence rules and the dispute consistency rules. `rating/index.html` was rebuilt for the judge's states and checks consistency before each save (the earlier form is `rating/index_v1_matcher_states.html`). `score_validation.py` scores the coding, and it was tested only on simulated codes written outside the project. Waiting on two coders uninvolved in the design. The challenge set is built after the natural coding.

## 2026-10-31 evening: presentation order, feature families, and a rarity defect

GPT questioned whether the five-configuration predictor's 81% could reflect generation slot, since every Y set's odd message is generated in slot 3. Claude answered that the pair and set features are symmetric and carry no slot index, and that templates are drawn independently per slot (`residue/prompts.py`), so slot is not recoverable even indirectly. GPT agreed and corrected Claude on one point: the gap between three-structure and five-configuration accuracy also arises when a correct Y probability, split over three odd positions, falls below the IND or DEP probability. The agreed package was a six-order invariance check and an ablation of the three relational families, both without model calls. `python analyze_relational_checks.py` wrote `runs/full/analysis/relational_checks.md`.

- Invariance. In all six presented orders and in a random order per set, with features recomputed and every model refitted, configuration accuracy (0.591), three-structure accuracy (0.613), and odd-message identification (80.6%) are unchanged, the largest probability difference is 3e-16, and no set's predicted configuration changes. Of 180 Y sets, 79 are classed Y by the three-structure model. 37 of those are fully correct, 40 are demoted by the split, and 2 have the wrong odd message. Thirty IND or DEP sets that the three-structure model called Y are correct in five configurations. The 81% is conditional on a set being a Y.
- Rarity defect, found by the first run. Rare overlap alone gave a pair-model AUC of exactly 0.500. Sets in a block reuse identical messages across structures (900 distinct texts in 1,080 IND and DEP slots and 1,620 three-structure slots), and the fold rarity table counts training rows' own texts, so a training row's shared n-grams almost never count as rare while a test row's do. In fold 0 the mean rare Jaccard is 0.004 and 0.020 in IND and DEP training rows against 0.126 and 0.223 in test rows, and 0 in every three-structure training row. No test-world text enters the table, so nothing leaks, but the feature has been mis-specified in every relational model: `analyze.py`, `analyze_secondary.py`, `inference.py`, and `analyze_anchored.py`. `residue/predictor.py` builds its table the same way in `fit_set`, which no reported analysis calls. The second run reports each result under the original fit and under a fit that removes each training row's own world from the counts. The corrected fit was defined from this diagnosis before its results were seen. The first run's report is in the scratchpad only and is reproduced exactly by the "fold" rows of the second.
- Corrected fit, conditional intervals on fixed out-of-fold predictions. P3 gain for the primary producer is 0.209 [0.159, 0.254] (pairwise AUC 0.908), against 0.142. Claude Haiku gains 0.126 against 0.069, and GPT Luna gains 0.097 against 0.066. Five-configuration accuracy is 0.641, Y sets are fully correct in 66 of 180, and the odd message is identified in 88.3%.
- Ablation under the corrected fit. Removing rare overlap lowers the P3 AUC for every producer (by 0.029, 0.039, and 0.041, all intervals excluding zero), and it is the only family whose removal does. Embedding similarity is redundant given the other two. Without rare overlap the gain stays positive for every producer (0.180, 0.087, 0.056), so shared ancestry is not recovered through rare shared wording alone.
- The corrected fit was adopted across the pipeline in the next entry.

## 2026-10-31 21:40 to 2026-11-01 01:02: rarity correction adopted

GPT approved the correction (pasted reply, 2026-10-31) with three requirements: exclude the whole world, test it against a table rebuilt without that world, correct `residue/predictor.py` too, and state what the refitted P3 bootstrap holds fixed. `residue/features.py` now has `WorldRarity`, which scores each row against its fold's table with the row's entire world removed, all replicates and reused copies included. A world outside the table, such as a held-out world, gets the full table. All six rarity call sites in `analyze.py`, `analyze_secondary.py`, `inference.py`, and `analyze_anchored.py` use it. `StructurePredictor.fit_set` now takes each training set's world and scores training sets with their own world excluded. `tests/test_features.py::test_world_rarity_matches_a_table_rebuilt_without_the_world` checks every row's rare set against a table rebuilt without its world, using messages reused across sets, and checks that the old construction finds none of a row's reused n-grams rare. 62 tests pass. `inference.py` now states in its docstring and its report that the refitted bootstrap refits the learners conditional on the relational features built once from the original folds, and does not rebuild the rarity tables within a resample.

The previous outputs are in `runs/full/analysis/superseded_v2_rarity/` (`text_only`, `secondary`, `inference`, and `anchored`, .md and .json, hash-checked against the originals). The reruns, logged in `runs/full/analysis/rerun_rarity.log`, were `python analyze.py`, `python analyze_secondary.py 99`, `python inference.py p3` (the P1 and P2 permutations are reused, since they do not use rarity), and `python analyze_anchored.py`. A first rerun of `analyze_secondary.py` used 30 permutations, the number given in the README, rather than the 99 of the canonical run. It was discarded and rerun with 99, and the 30-permutation report is kept only in the scratchpad.

Changes, old to new:

- P3, primary producer: pairwise AUC 0.841 to 0.908, gain 0.142 [0.092, 0.192] to 0.209 [0.159, 0.254]. Refitted bootstrap interval 0.092 to 0.265 became 0.156 to 0.287, and centered p 0.010 became 0.005. Holm still rejects P2 and P3.
- P3 for the other producers: Claude Haiku gain 0.069 to 0.126, GPT Luna gain 0.066 to 0.097. Partial access, primary producer: pairwise AUC 0.996 to 0.994, gain 0.148 to 0.146, the one rarity-dependent estimate that fell.
- P3 gain by set-length tertile: 0.101, 0.189, 0.137 to 0.144, 0.258, 0.210.
- Three-structure macro AUC, pairwise model: 0.783, 0.873, 0.871 to 0.827, 0.955, 0.965 (primary, Haiku, Luna). Pairwise same-root AUC: full access 0.807 to 0.863, partial 0.952 to 0.979. Five-configuration accuracy 0.591 to 0.641, odd message identified in Y sets 81% to 88%, same-root AUC from configuration probabilities 0.818 to 0.858.
- Anchored, unvalidated: the shared-deviation AUCs are unchanged, because they do not use rare overlap. Their gain ratio against the relational gain fell with the larger denominator: all deviations 0.93 [0.66, 1.32] to 0.63 [0.48, 0.81], omission only 0.92 to 0.62, all except neither 0.88 to 0.60, affirmative only 0.19 to 0.13. The support condition is met where it was met before. The ratio compares AUC gains and is not a mediation fraction.
- Results that do not use rarity moved by at most 0.001 in AUC under the embedding learner (R1 against NCR1 0.501 to 0.502, SD-same+1 against SI-same+1 0.519 to 0.520, R5 against SD-same+3 0.456 to 0.455). One permutation p moved by 0.010 (composition three-way, 0.970 to 0.960) and one by 0.002 (P2 embedding, 0.178 to 0.180). No verdict changed. The cause is not established. Repeated fits in one process are identical and reproduce the new values with the same penalties as the old run, and single-threaded BLAS gives the same result. The feature learner is identical, so the texts are unchanged, the cache's first 43,805 lines match the 15:27 backup hash, and `calls.jsonl` has not changed since 00:36. The old reports were produced at 11:08 and 12:02, before the first code snapshot (15:27), so the code or vector state they used is not fully recorded.

## 2026-11-01 to 2026-11-02: journal decision, cross-producer transfer, numbers sheet

Eric chose Transactions of the ACL as the target, with Scientific Reports as fallback, after the strategy memo (`redesign/Claude_Journal_and_Manuscript_Strategy_Memo_2026-11-01.md`, with GPT's corrections recorded at its end) and GPT's reply. GPT and Eric agreed on one bounded analysis of existing data, the transfer of the set models across producers. `runs/full/analysis/cross_producer_transfer_PLAN.md` fixed the comparisons and readings before any transfer model was fitted. `python analyze_transfer.py` (2,416 s, no model calls) wrote `runs/full/analysis/cross_producer_transfer.md`. Same-producer rows reproduce the canonical within-producer values exactly.

- IND against DEP, relational AUC when trained on one producer and tested on another: from 0.788 (GPT Luna to Gemini) to 0.985 (Claude Haiku to GPT Luna). In all six ordered pairs the relational model exceeds the transferred pooled baseline, by 0.112 to 0.264. The change from the test producer's within-producer model ranges from -0.119 to +0.011. Transfer between Claude Haiku and GPT Luna loses nothing detectable in either direction, and the largest losses are on Gemini as the test producer.
- Three structures, macro AUC: from 0.727 to 0.958. The relational model exceeds the pooled baseline by 0.135 to 0.259 in every pair, and the change from within-producer performance ranges from -0.100 to +0.003, again with the largest losses on Gemini as the test producer.
- By the plan's readings, the relational features carry ancestry information that is not producer-specific. Transfer is close to within-producer performance among Haiku and Luna and partial when the test producer is Gemini. The asymmetry is reported, not interpreted.

`python make_numbers.py` writes `manuscript_numbers.md` and `.json`, the canonical numbers sheet. Every manuscript value is to be cited by its key there. Each row names its source file and JSON path, and the sheet records the SHA-256 of each source. Two caveats are recorded in its rows. The presentation-order invariance check and the five-configuration error decomposition were computed under the original rarity fit only. The P1 and P2 permutation p-values come from the 2026-10-31 11:14 run and were reused because those tests do not use rarity.

## 2026-11-02: corrected-fit invariance and the first TACL draft

`python analyze_relational_checks.py invariance-corrected` reran the presentation-order check under the canonical rarity fit (`runs/full/analysis/invariance_corrected.md`). All six orders and a random order per set leave every prediction unchanged, with the largest probability difference 4e-16. Under the corrected fit, of 180 Y sets, 66 are assigned their exact configuration, 28 are recognized as Y by the three-structure model but demoted when the Y probability is split over three odd positions, none has the wrong odd message, and 86 are classified as independent or out-star. `make_numbers.py` now reads these rows from that file (keys `config5.decomp.*`, `invariance.*`), and the sheet has 307 rows.

Eric asked Claude to draft the manuscript, with GPT reviewing. The draft is in `tacl/` in the project folder.

- `main.tex` follows the TACL 2021 template, downloaded from transacl.org into `tacl/template/`. Tectonic 0.17.0, which Eric installed in `~/.local/bin`, compiles it to `main.pdf`.
- `scripts/make_macros.py` turns `build/manuscript_numbers.json` into `numbers.tex`, so every number in the text is a macro keyed to a sheet row and none is typed by hand.
- `scripts/make_figures.py` draws every figure from the same sheet.
- `refs.bib` holds only verified references (`redesign/Claude_Citation_Verification_2026-11-02.md`).
- The draft runs just over 7 pages of content within TACL's limit of 7 to 10, followed by references, a methodological appendix, and complementary results.
- Changes from GPT's claim ledger:
  - Causal language at the level of structure, with no claim about the linguistic mechanism.
  - Prompted readers in the main text.
  - "Experimentally assigned" in place of "randomized".
  - GPT's alternate title.
- The verbatim example excerpts (world W000, first replicate, primary producer) were read from the stored outputs.

## 2026-11-02: first draft reviewed and revised

GPT reviewed the draft independently (`redesign/GPT_Independent_TACL_Draft_Review_2026-11-02.md`) and recommended major revision. It made seven findings about construct and claim scope, none about the results. Claude accepted all seven and revised `tacl/main.tex`, keeping the first draft's source as `tacl/main_draft1_2026-11-02.tex`. Each change is listed in `redesign/Claude_Response_to_GPT_TACL_Draft_Review_2026-11-02.md`.

- "Independent" now means separately drafted upstream reports written from a common record, not independent evidence.
- The main estimate is stated as a comparison of two defined feature representations, not a general bound.
- Causal language is limited to the assigned sharing of upstream text, and the bundled difference in observer calls is named.
- The partial-access, source-stripping, ablation, and single-report statements were narrowed.
- The inconclusive P1 embedding result is reported with its permutation p.
- Appendix A adds the rarity construction, the five-configuration rule, and reader example selection.

The main text now ends early on page 8. Still open for Eric: the title, and whether the draft should commit to releasing code, prompts, and outputs.

## 2026-11-02: three manuscript reviews, two post hoc checks, revision

Eric approved the title *Detecting Shared Ancestry Among Language-Model Reports* and asked for the release promise to be replaced. The draft now has a reproducibility statement saying the materials are not publicly available and that release will be assessed after a review of provider terms and the materials' content. Three subagents then reviewed the compiled PDF and nothing else: a skeptical TACL methods reviewer, a line editor working from the Writing Canon, and an outside reader.

- The methods reviewer suspected that the cache key omitted generation position, so that slots drawing the same template would share outputs. The code shows otherwise. The key includes the role string, which names the position. All observers in a block share one template, so the independent structure's drafts are repeated samples of one prompt, and the draft had wrongly described them. The reviewer correctly noted that structures share stored texts by design. Report 1 is identical in all three structures, the Y set's report 2 is the out-star's, and its report 3 is the independent set's. A single-report diagnostic over all positions therefore meets identical texts under different labels.
- `python analyze_review_checks.py` (post hoc, no model calls, `runs/full/analysis/review_checks.md`) ran two checks.
  - Single reports 2 and 3 only, which never coincide between the independent structure and the out-star: equivalent to chance for every producer under both learners (0.486 to 0.538).
  - Each pairwise statistic as an untrained score: the largest rare-sequence overlap in a set reaches 0.863 (Gemini), 0.985 (Haiku), and 0.984 (Luna), equal to or above the trained relational model for Haiku and Luna (0.982, 0.973) and below it for Gemini (0.908).
  - The paper now states that a plain text-reuse statistic carries most of the signal, and that the contribution is the controlled comparison, not a detector. Both checks are in `manuscript_numbers` (keys `unshared.*`, `unsup.*`) and are labeled post hoc in the text.
- The reviews also found:
  - Two errors in the cross-producer summary. Losses involve Gemini in both directions, not only as the test producer. The draft also said single-report traces "do not transfer" from a single test.
  - Contradictions: the sources-line indicator listed as a feature, and the number of bounding arms.
  - Undefined labels (IND and DEP, split access, spokes) and a stacked-statistics sentence.
  - Claims that went past the evidence: the abstract applying primary-producer numbers to all producers, "weakens", and an untested variance mechanism.
- All were corrected. Appendix B adds the ablation table and the untrained-score table, and the main text ends on page 8.

## Spending

From `smoke/ledger.json` and the spend lines in the run logs, in US dollars. Stage figures are differences between ledger readings. The ledger total for the world-bank period is an upper bound (see 10-30), so the provider consoles give the exact amounts.

| Stage | Anthropic | OpenAI | Google |
|---|---|---|---|
| Smoke test, world banks, verification and re-verification | 13.98 | 7.74 | 0.31 |
| Full producer run | 4.18 | 2.57 | 2.45 |
| Readers | 27.09 | 5.35 | 0.00 |
| Proposition judge | 0.00 | 5.64 | 0.00 |
| Replication | 0.00 | 0.00 | 0.56 |
| Judge on the validation sample | 0.00 | 0.52 | 0.00 |
| Total | 45.24 | 21.81 | 3.32 |
| Cap in `residue/adapters.py` | 46.67 | 22.94 | 24.99 |

## Results at this point

The numbers below are from the final outputs listed above. P1 to P3 and the secondary contrasts are text-only and do not depend on the judge. The anchored results do depend on it and are unvalidated.

- P3, three unconnected sources against the out-star. Comparing the three messages raises AUC from 0.699 (pooled) to 0.908, a gain of 0.209 with a conditional interval of 0.159 to 0.254 (0.142 before the rarity correction). The refitted bootstrap p is 0.005, which passes Holm. Removing rare overlap lowers the AUC for every producer, and without it the gain stays positive for every producer.
- P2, hub against diamond. The feature learner's AUC is 0.552, with a one-sided permutation p of 0.023 from 999 permutations, which passes Holm, and the replication gives 0.568, p 0.005. The embedding learner gives 0.515 and 0.480. A single message carries a small, replicated trace of whether a synthesis's inputs were independent, too weak to classify individual messages.
- P1, dead-end controls. In the full run the direct report differed from its control under the embedding learner (AUC 0.553, inconclusive under the three-way rule, p 0.015), although the requests are identical. In the fresh-seed replication with randomized order both controls and a pure null were equivalent under both learners (0.489 and 0.493), so the full-run difference did not replicate.
- Chains of 1, 3, and 5 relays, and hubs with 1, 2, or 3 split-access spokes, are separable at about 0.60 to 0.68. Contrasts after further relays, and the compositions with five relays, are at chance.
- The five-configuration set predictor is correct on 64% of sets, and in Y sets it identifies the odd message 88% of the time (59% and 81% before the rarity correction, unchanged in every presented order). The 88% is conditional on a set being a Y. The structure predictor recovers the exact history on 20% to 22% of messages, against 12.5% for the majority baseline.
- Anchored, unvalidated. The excess of shared departures from the record separates three unconnected sources from the out-star at 0.83 under full access, nearly all of it through shared omission. Its gain over the pooled baseline is 0.63 of the corrected relational gain (0.93 before the correction). Under partial access the signal is negligible. Salience adjustment leaves the out-star's excess unchanged.

## Open

- Human validation of the proposition judge. The sample, rubric, form, plan, and scorer are ready in `validation/`. It needs two coders not involved in the design, then the challenge set, which needs OpenAI credit. The anchored results stay labeled unvalidated until then.
- The pathwise decomposition (judging 540 Study 2 observations, about $1.15), if validation passes. OpenAI has $1.13 left under the cap.
- H11's world-free method is not built, because the design does not specify its reference corpus.
- The manuscript, for Transactions of the ACL. The first full draft is `tacl/main.pdf` (2026-11-02), awaiting GPT's review and an outside reader. GPT's claim-ledger outline and related-work list are in `redesign/` (`TACL_Claim_Ledger_Outline_2026-11-01.md`, `TACL_Related_Work_and_Submission_Policies_2026-11-01.md`). Their citations are not yet verified.
- Publishing `build/` and `redesign/` to GitHub waits on Eric's approval.

## 2026-11-02 08:20 — GPT review of the post hoc reframing, and precision edits

GPT reviewed the revised PDF (`redesign/GPT_Independent_TACL_Review_Posthoc_2026-11-02.md`). Verdict: keep TACL for one submission, contribution borderline on significance, not on correctness. No new analyses run. Baseline saved as `tacl/main_draft3_pre_gpt2_2026-11-02.tex`. Edits to `tacl/main.tex`:

- Abstract: the rare-overlap score and the unshared single-report check are labeled post hoc; the score is "without fitting to structure labels" (rarity is still fold-defined); "most of the binary signal"; equivalence restricted to the two tested learners and the predefined band.
- 4.1: states that nine statistics were scored and the maximum rare overlap is reported because it performed best for every producer; trained-model AUCs given beside it; "equals or exceeds" replaced by "close to"; paired differences not estimated and intervals not adjusted for selection; the claim is scoped to the binary task, and the three-structure and configuration tasks are said to have no unfitted comparator.
- Discussion: marginal equality stated as a design fact, separate from the empirical equivalence of the two learners; "one shared rewrite step" (previously flagged inaccurate, had survived) removed; the contribution sentence now ends on where recovery gets harder (exact configuration for 64.1% of sets, Y sets lost at the structure stage).
- Appendix table: "Untrained" dropped, caption states rarity is fold-defined, label `tab:unsup` added. Subsection 4.2 labeled `sec:configs`.

Compiled, 12 pages, no undefined references. The reproducibility statement now starts on page 9. A fresh outside reader (subagent, PDF only) was launched on this version.

## 2026-11-02 08:50 — Fresh outside reader, and edits

A subagent given only the PDF read the 08:21 version. Recommendation: major revision, on significance (one rewrite, an n-gram score nearly saturates the binary task, untested harder conditions, no release). It checked the text against the tables and found them consistent. Baseline saved as `tacl/main_draft4_pre_reader2_2026-11-02.tex`. Edits, all wording or scope, no new analyses:

- Abstract names Gemini as the primary producer and as the producer in the transfer losses. The input-sharing replication is scoped to new replicates of the same worlds.
- 3.1 and the Figure 1 caption: stored Y sets have the shared pair at positions 1 and 2.
- 3.2: direct report and relay defined. 3.3: the sources-line indicator carries no information in any reported comparison; world-specific names, times, and figures count as rare and appear in every structure's reports.
- 3.4: the equivalence rule was fixed for the dead-end controls and the matched-set single-report check, and the post hoc unshared-text check reuses it. The Table 4 caption is scoped to that table.
- 4.1: "meet the rule's criterion for equivalence"; both GPT Luna intervals exclude 0.5 inside the band; template-family strata defined.
- 4.2: pair-AUC-versus-set-metric comparison removed; primary producer and 540 sets stated; "recognized as Y" is now "assigned Y by the three-structure model". The 21 conditional odd-report failures all fall among sets not assigned Y. This is implied by `config5.decomp.Y.odd_wrong` = 0.
- 4.4: concealment raised reader AUC and stripping changed it by less than 0.03, both untested. 4.5: the dead-end sentence now names the contrast.
- Discussion: "close to ceiling" now refers to independent against out-star. Limitations: "after review" is now "after the main results were known", since the earlier wording disclosed a prior review in an anonymous submission. Table 3 rows relabeled from IND/DEP.

Not acted on, left to Eric: abstract length (~310 words; the TACL template states no limit; journal policy not checked, ACL convention is ~200); the reader's generation-order point for the set results (in the IND-versus-DEP comparison, reports 2 and 3 are structure-specific in both structures, but call ordering by structure was not checked); the significance objection, which needs new conditions (deeper chains, mixed producers, instructed variation) and not editing; and release of prompts and outputs.

Compiled, 12 pages, no undefined references.

## 2026-11-02 09:20 to 10:05 — Deeper rewriting run

Approved by Eric at an estimate of about $0.75. The plan, `runs/depth/PLAN.md`, was written before any call. `run_depth.py` was dry-run first (3,600 calls counted, sharing pattern checked), then run live: 3,600 Gemini calls, all valid on the first attempt, $0.59 (`runs/depth/calls.jsonl`, `sets.jsonl`, `generation_summary.json`). Step-1 texts were read from `runs/full/calls.jsonl` without modifying it. `analyze_depth.py` wrote `runs/depth/analysis.md` and `.json`. Depth 1 reproduced the full run: pooled 0.6989, relational 0.9077, score 0.8631.

Independent against out-star, primary producer:

- Relational AUC: 0.908 (depth 1), 0.883 (2), 0.875 (3), 0.855 (5).
- Pooled AUC: 0.699, 0.652, 0.622, 0.577.
- Gain: 0.209, 0.231, 0.253, 0.278. Every interval excludes zero.
- Unfitted maximum rare overlap: 0.863, 0.831, 0.826, 0.796.
- Relational minus that score (prespecified paired difference): 0.045, 0.052, 0.049, 0.059. Every interval excludes zero.
- Three-structure relational macro AUC: 0.827, 0.795, 0.780, 0.754.

Readings under the plan:

- Decay: the relational AUC falls slowly, and the gain never reaches zero.
- Divergence: the paired difference excludes zero at every depth but does not grow detectably.
- Persistence: not met in the plan's strict sense, because the depth-5 relational AUC is below the depth-1 interval.
- Single-report check: the feature learner is inconclusive at depths 3 and 5 (0.546 [0.519, 0.571] and 0.547 [0.520, 0.574]), not outside the band. The embedding learner is equivalent at every depth.

## 2026-11-02 10:40 — Depth results in the manuscript

- **Numbers sheet.** `make_numbers.py` reads `runs/depth/analysis.json` (412 rows).
- **Figure.** `tacl/scripts/make_figures.py` adds `fig_depth.pdf`.
- **Manuscript.** Baseline saved as `tacl/main_draft5_pre_depth_2026-11-02.tex`. Changes to `tacl/main.tex`:
  - new subsection 4.4, "Shared ancestry after further rewriting", with Figure `fig:depth`;
  - Appendix A paragraph on the run;
  - abstract sentence on the extension; the abstract's sentence on the single-report studies (relay depth, input sharing) was removed for length, and those results stay in 4.5;
  - the Discussion contribution paragraph covers one to five rewrites;
  - Limitations: first limit narrowed to what the extension did not cover, and the extension listed as planned.
- **Figure label fix.** The `fig_configurations` legend now says "Assigned Y", to match the text.
- **Manifest.** Rebuilt: 801 files, analysis code 4170f046d14a.
- **Page count.** TACL's appendices policy (transacl.org announcement 105, read 2026-11-02) supersedes the 2021 template's statement that appendices count:
  - 10 content pages for original submissions;
  - up to 5 appendix pages for replication detail and 3 for complementary tables and figures, placed after the references and not reviewed;
  - no supplementary files and no links to them.
  The paper has about 9.1 content pages, with references on page 10 and appendices on pages 11 to 13, about 2.6 pages.

## 2026-11-02 11:30 — GPT referee review of the depth extension, and edits

GPT's review is `redesign/GPT_Referee_Review_Depth_Extension_2026-11-02.md`. Disposition: major revision, keep TACL.

GPT's checks:
- It audited the code against the plan: compliant, with all 900 block-by-depth groups checked for sharing.
- It confirmed the plan predates the run: plan modified 14:22:00 UTC, run started 14:22:25 UTC.

Findings accepted:
- None of the plan's three readings was met as specified. Decay required the gain to fall, and it rose. Divergence required growth. Persistence required the depth-5 value to fall inside the depth-1 interval.
- "More purely relational" overstates: the design makes all structural information joint from depth 1, and what changed is the relative AUC of two representations.
- The depth-1 paired difference is post-selection. The deeper comparisons are planned but share worlds and depth-1 ancestors.
- The planned nine-by-four score table was missing from the paper.

Baseline saved as `tacl/main_draft6_pre_gpt3_2026-11-02.tex`. Edits:
- **4.4 rewritten.**
  - The three readings are stated and adjudicated as not met.
  - Between-depth changes are labeled descriptive.
  - The conclusion is limited to the tested features' relative retention of discrimination.
  - All four paired differences are given, with depth 1 marked as post-selection and the deeper ones as a planned follow-on on the same worlds.
  - Single-report wording now reads "inconclusive under that rule ... neither interval lies outside the band".
- **New Appendix B table** (`tab:depthscores`): nine statistics by four depths.
- **Discussion:** the "more purely relational" sentence is replaced by the two depth-5 AUCs.
- **Abstract:** "approaches chance" is now "declines to 0.577", and the score comparison is described as fixed before the deeper texts were generated.
- **Introduction:** the rewrites sentence is narrowed. Rewrites inherit the parent's record, errors included, except where a rewriter changes it.

Not changed: `runs/depth/PLAN.md`, which is a record. GPT judged its sentence that a single-report failure would mean the construction "has failed" too strong, and that judgment is noted here.

Compiled, 13 pages, no undefined references. Content ends near the top of page 10, about 9.3 pages.

## 2026-11-02 — GPT check of the 11:30 edits

At Eric's request, GPT ran a narrow check of `tacl/main.tex` and `main.pdf` against the "Required changes" list in its depth review only. It found all eight resolved, none partly resolved, and none unresolved, and confirmed that the 11:30 log entry matches the manuscript. GPT replied in chat, so no file was saved.

Still open before submission:
- Eric's decisions on code and data release, and on submission.
- The outside reader's generation-order question, which can be checked from existing call records.

## 2026-11-02 — Public GitHub release

Eric authorized publishing everything. He chose a new repository, chose to hold the manuscript until acceptance, and chose to include all of `redesign/`.

- **Repository.** https://github.com/ericcgladstone-maker/shared-ancestry-lm-reports (public), staged at `~/code/shared-ancestry-lm-reports`, outside Drive, so no git repository was created in Drive.
- **Contents.**
  - `build/`, without dry runs, `__pycache__`, the embeddings folder, or `validation/judge`. The judge's judgments on the validation sample are withheld until human coding is finished.
  - `redesign/`, with the `.gdoc` stubs replaced by Markdown exports of the 17 GPT Google Docs in `redesign/gpt_google_docs/`.
  - Root README, MIT license for code, and CC BY 4.0 for data.
- **Compression.** Records over 20 MB are gzipped in the repository only. The Drive copies are unchanged, so MANIFEST hashes refer to the uncompressed files.
- **Embeddings.** `embeddings.jsonl.gz` (SHA-256 491b79b7…, listed in MANIFEST) is attached to release v1.0. `source.json` and a pointer README are in `build/runs/full/embeddings/`.
- **Checks.** A secret scan (key patterns, private keys) found nothing.
- **Known exposure.** Absolute paths in some logs and in MANIFEST include the Drive folder name, which contains Eric's email address. They were left as recorded.
- **Manuscript.** The reproducibility statement in `tacl/main.tex` now says that code, prompts, worlds, stored calls, analysis records, and plans are released publicly under open licenses, with the location withheld for anonymous review, as TACL requires. The repository does not contain the manuscript.

## 2026-11-02 — Generation-order check

This post hoc check answers the outside reader's question and makes no model calls. `analyze_generation_order.py` rebuilt the independent and out-star full-access neutral sets through a read-only producer and looked up each stored call's time. It wrote `runs/full/analysis/generation_order.md` and `.json`.

The reports that differ between structures are reports 2 and 3. The out-star's were generated first in 102, 94, and 97 of 180 blocks (Gemini, Haiku, Luna), with two-sided sign tests giving p = 0.086, 0.602, and 0.333. Median leads were 1.3, 0.4, and 1.4 s, and the largest gap was 38 s.

The out-star's observation preceded both independent observations 2 and 3 in about 65% of blocks (p ≤ 0.001). This is expected by construction: that observation is the shared report-1 observation, which every structure in the block needs and which is generated whenever the first of them runs. These gaps are also measured in seconds.

The result was added to the sheet as `order.*` (424 rows), and one sentence was added to the end of section 4.5. Limitations now lists the check as post hoc. Manifest rebuilt.

## 2026-11-02 — GPT pre-submission check

GPT checked the generation-order sentence, repository disclosure, reproducibility statement, and the PDF. It found no other problems: A4, anonymous, cross-references resolve, numbers agree with tables, within page allowances. Baseline saved as `tacl/main_draft7_pre_presub_2026-11-02.tex`. Edits:

- **Section 4.5, generation order.** The sentence is now restricted to reports 2 and 3. The 40-second bound is now stated as the difference between mean generation times. The sign tests are described as treating blocks as independent. The less-balanced observation order is stated, with its cause.
- **Reproducibility statement.** It now claims only the stored calls behind the reported analyses. It states that the language-model judge's outputs on a separate validation sample, which no reported result uses, are withheld until human coding is complete.
- **Repository disclosure.** GPT recommended disclosing the repository in Comments to the Editor and drafted the text, which is saved at `tacl/submission/Comments_to_the_Editor_DRAFT_2026-11-02.md`. GPT also noted that making `redesign/` private during review would reduce discoverability, though git history would keep it. That decision is left to Eric.
- **Filename.** The upload must be renamed to the submission number plus the first words of the title.

## 2026-11-02 12:00 to 13:30 — Flexible set models, Haiku depth run, copying count, retitling

Eric approved both items: a stronger comparator analysis, and Haiku depth at about $0.80. Both plans were written before their runs: `runs/full/analysis/stronger_comparators_PLAN.md` and `runs/depth_haiku/PLAN.md`.

**Haiku depth run.** `run_depth.py` gained `--producer`, `--max-step`, `--out`, and `--run-cap`; its defaults reproduce the Gemini run. Dry run: 1,800 calls, sharing intact. Live run: 1,800 Haiku calls to three rewrites, all valid on the first attempt, $0.82. Anthropic spend is now $46.06 of its $46.67 cap. `DEPTH_DIR=runs/depth_haiku DEPTHS=1,2,3 python analyze_depth.py`, with depth 1 reproducing the full run (0.8563, 0.9821, 0.9848). Independent against out-star:
- relational: 0.982, 0.966, 0.954;
- pooled: 0.856, 0.834, 0.817;
- gain: 0.126, 0.132, 0.137;
- score: 0.985, 0.973, 0.965;
- relational minus score: -0.003, -0.007, -0.012, every interval including zero;
- single reports: equivalent at every depth under both learners.

**Flexible set models.** `analyze_comparators.py` wrote `runs/full/analysis/stronger_comparators.md`. The strongest non-relational model was the embedding-dispersion model for Gemini (0.786) and rich logistic summaries for Haiku (0.876) and Luna (0.888). Relational minus the strongest:
- Gemini 0.122 [0.091, 0.153]; Haiku 0.106 [0.072, 0.142]; Luna 0.085 [0.053, 0.121];
- Gemini at five rewrites 0.158; Haiku at three 0.122.
- All intervals exclude zero, so the plan's "gain holds" reading is met.
- For Gemini the gain is about half the gain over the reference baseline (0.209).
- Boosting the relational features did not improve on logistic regression; every interval includes zero.

**Copying (post hoc).** Some rewrite calls return their input unchanged. This was recorded in verification, but the manuscript did not mention it. `analyze_copying.py` wrote `runs/full/analysis/copying.md`.
- At one rewrite, 892 of 900 chains changed for both Gemini and Haiku.
- Gemini chains changed the text at a mean of 4.12 of five calls, and at every call in 370 of 900. After three calls the mean is 2.70 for Gemini and 2.73 for Haiku.
- In 3 of Haiku's 180 out-star sets, two rewrite positions drew the same template and Haiku returned byte-identical texts.
- A check that the independent structure's same-prompt observations are never identical found none identical, for all producers.

**Sheet and macros.** Sheet: 554 rows (`depthH.*`, `comp.*`, `copy.*`). Macros: `\NR` (one decimal) added.

**Figure.** `fig_depth` now has two panels.

**Manuscript.** Baseline saved as `tacl/main_draft8_pre_haiku_comparators_2026-11-02.tex`. Changes:
- Title: "Detecting Shared Ancestry Among Reports from Networks of Language-Model Agents: A Controlled Experiment" (Eric, 2026-11-02).
- New 4.1 paragraph on the flexible models, and Table 5 in Appendix B.
- 4.4: Haiku paragraph and copying paragraph.
- Abstract: comparator clause; the depth sentence now covers both producers.
- Discussion: updated, and its repeated single-report detail cut.
- Limitations: updated.
- Appendix A: Haiku run, the flexible models, and the identical Haiku rewrites.
- Cuts to stay under ten content pages: 4.6 control paragraph condensed, one repeated Limitations sentence removed.

Compiled at 15 pages: content ends on page 10, Appendix A is about 1.4 pages, and Appendix B about 2.6.

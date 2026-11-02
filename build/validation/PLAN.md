# Validation of the proposition judge

Written 2026-10-31, before any human coding. It follows design v8 Part VI, `redesign/GPT Review of Full-Run Analyses (2026-10-31)` section IV, and `redesign/GPT Reply to Claude Assessment of Network Tests (2026-10-31)` question 4. The instrument validated is judge-v1 (`residue/judge_matcher.py`, gpt-6.1-terra), exactly as it was used on the full run. Every anchored result (`runs/full/analysis/anchored.md`, `salience.md`) stays labeled unvalidated until both parts below pass.

## What the coders receive

Only three files: `validation/RUBRIC.md`, `rating/index.html`, and their own items file (`items_coder_A.json`, 240 items, or `items_coder_B.json`, 60 items). Each item is a message body without its Sources line and the world record's 20 facts and 2 disputes, which is what the judge saw. The coders never see `sample.json`, the judge's output, condition or structure labels, model names, or each other's codes before both have exported. Both coders must be uninvolved in the design.

## Natural sample

`make_validation_sample.py` drew 240 messages from the re-verification run (`runs/verification_v2/`, 10 worlds that no full-run analysis uses). Per producer: Study 1 observations 16, rewrites 24, syntheses 16, Study 2 observations 8, rewrites 16. Within strata the draw is spread over condition groups and worlds, and no message body appears twice except inside a linked unit. Twelve linked units sit inside those strata, two out-star sets and two three-relay chains per producer, each an observation and its three rewrites, so 48 messages and 36 parent-and-child pairs with both texts coded. Coder B codes 60 of the 240, chosen by producer and node function, including one out-star set and one chain kept whole. The draw used design labels only and was made before the judge read any of these messages. Its metadata is in `sample.json`.

Scoring (`score_validation.py`), with judge states compared with the human codes (coder A, replaced by the adjudicated code where the two coders adjudicated):

- For fact states (stated, changed, doubted, absent) and dispute resolutions (first, second, both, neither) separately: the confusion matrix, class counts, and pooled class-balanced accuracy with a 95% world-cluster bootstrap interval. The criterion is a balanced accuracy of at least 0.80 for each judgment. A class with fewer than 30 natural human-coded instances is marked not validated on natural text, and every claim that depends on it is withheld.
- Cohen's kappa between coders A and B on the 60, for each judgment, before adjudication. The coders then adjudicate their disagreements under the rubric, and the adjudicated codes are exported as coder ID `ADJ`.
- Agreement by producer, node function, study, and whether the fact was in the message's observed package, because errors that differ by node function would manufacture a structural result.

Linked diagnostics, reported as diagnostics, with no new pass mark (GPT's reply, question 4):

- Transitions from parent to child, built from the two human codes: stated at both, stated then absent, absent then stated, and the full four-state matrix, with the judge's agreement on each transition category.
- Joint false absence: among facts the humans code as stated in both parent and child, the share the judge codes absent in both, against the product of its separate miss rates. The same for pairs of out-star siblings whose fact the humans code as stated in both.
- The number of false shared omissions per pair those rates imply, set against the full run's out-star excess over three unconnected sources (about 1.1 events per pair in `anchored.md`, 0.79 for undisputed facts in `salience.md`). If plausible correlated false absences could account for that excess, the pathwise mechanism claim is withheld and the text-only result stands alone.

## Challenge set

Built after the natural coding, from coded bases, by a fixed script, never selected or edited using the judge's output. It keeps v8's controlled edits (deleting a stated fact's clause, changing a number, time, or entity by fixed rules, switching a resolved dispute member, reordered clauses, number words, fixed synonyms) and adds GPT's adversarial cases: paraphrased multi-clause facts, a reversed sequence, both competing values with attribution, a correct value attached to a different event, a dispute member named without being asserted, a one-sided hedged assertion, a contradiction beside accurate unrelated numbers, and inherited paraphrase (an unusual wording of a stated fact carried from a parent into its child, which must stay stated in both). It needs at least 40 instances of each class of each judgment for each node function and producer. Criteria: per-class recall at least 0.85, a false-change rate below 0.10 on meaning-preserving edits, and identical output for the 12 stripped and unstripped pairs. Judging the challenge set needs OpenAI credit beyond the $1.13 left under the cap.

## Known limit of the instrument

Judge-v1's output is not constrained to be consistent. 11 of 2,662 full-run messages have a dispute resolution that contradicts the judge's own fact states. The human form enforces consistency, so those cases count as judge errors in scoring. A judge-v2 with the rubric's precedence and consistency rules would have to be rerun on all 2,662 messages (about $5.60) and validated again, so it is not planned unless judge-v1 fails.

# Disposition of the Pre-Results Referee Reviews in Version 6

Prepared by Claude, 2026-10-30. This file records how `Claude_Diagnosis_and_Redesign_v6_2026-10-30.md` answers `Referee Review, Claude (2026-10-30).md` (C1 to C11) and `Referee Review, GPT (2026-10-30)` (G1 to G19). Both reviews recommended major revision, assuming predicted results. The Claude referee was a fresh agent restricted to version 5, the npj decision letter, and the manuscript. The GPT review ran in the design conversation, as GPT disclosed, so it is not blind. Where the two raised the same objection, they are listed together.

## Accepted and changed in version 6

| Objection | Change | Where in v6 |
|---|---|---|
| C1 (part). H1 cannot fail: shared terminal keys make NC0 and D0 byte-identical in the full run | Full-run NC0 and NCR1 terminals get condition-specific keys. Shared terminal keys are used only in the replay set | Principle 6, Part IV NC seed row, H1 |
| C1 (rest). H3, H5, H9, and the stripping half of H10 are positive or invariant by construction | Reclassified as secondary estimates, with the construction stated. The H10 invariance becomes a check | Part V |
| C3, G1. No primary hierarchy or multiplicity control across eleven hypotheses | Three primary contrasts: P1 negative control, P2 SI-same versus SD-same, P3 full-access neutral IND versus DEP. Holm over P2 and P3. Everything else is a secondary estimate | Part V, Inferential structure |
| C3, G10. The analysis is not executable as preregistered | Fixed outer five-fold world-grouped design, fixed learner and penalty grid, primary metrics, label definitions, two-way bootstrap, p-values, machine-readable configuration tested on synthetic data | Part VIII |
| C4, G2. Matcher validation is underpowered and likely to fail | Two-part validation: a scripted challenge set with known labels and at least 40 instances per class, function, and producer, plus a natural sample of 120 messages with a second annotator on 30. Same locked fallback | Part VI |
| C5. Prompt templates are a fixed factor, and intervals cluster only on worlds | Six templates per function per family, stated. The bootstrap resamples worlds and templates | Principle 4, Part VIII |
| C6 (part), G8. Study 2 runs on one producer | The second producer runs the full-access neutral arm of Study 2, for P3 transfer. About 9.5 added hours | Part V Study 2, Part VII |
| C10, G9. Mediators without a mediation design | Called post-treatment process measures, reported as associations. No mediation claims | H4, Part X |
| C2. Independence comes only from sampling variation at default decoding | P2 stated as conditional on the recorded default settings. A prespecified association between per-world observer diversity and discriminability lets a weak P2 be read against actual observer diversity. Temperature is not added as a factor | Part V, Observer diversity |
| G4. Relational gain does not show inherited deviations | A primary shared-deviation statistic, with a support condition (alone above chance and recovering at least half of the gain), compared with generic similarity. Otherwise reported as relational prediction only | H8 |
| G5, C8. Equivalence margins are too tight for the design's precision | Inconclusive results are reported as upper bounds on leakage. H7 pools prompt families, and the worst stratum is descriptive | Part V three-way rule, H7 |
| G6. The reader protocol is unspecified | Input, label descriptions, 16 balanced in-context examples per fold, JSON output, temperature 0, invalid-output policy. Comparison with classifiers is descriptive | Part VIII |
| G7, C11. World construction is underspecified | Drafting model family, 14 event types with five worlds each, automatic schema checks, Eric's review, logged edits, frozen bank and fold assignment. Results scoped to the authored distribution | Part VII |
| G11, C9. Concealment changes more than attribution | Named as the total effect of the concealment instruction. Field presence, validity, and source errors reported by structure | H10 |
| G3, G12, C6 (framing). The construct is broader than the treatments, and the graph vocabulary is narrow | Framed as a controlled identifiability study of small message-production graphs. Claims name their contrasts. No general topology or human-communication claim | Header, Part X |
| G13. Paired reuse and effective sample count | Bootstrap resamples whole worlds. Unique messages are reported alongside records | Part VIII |
| G14. Engineering controls are not findings | Reported separately from findings | Part X |
| G15. Subgroup and length interactions lack status | A bounded set of secondary interactions. All other subgroups descriptive with counts | Part VIII |
| G16. Thresholds lack rationale | Stated as stipulated, with a rationale for the AUC tolerance. Estimates are always reported with intervals | Part V |
| G17. Feature families are not constructs | Kept as operational groupings for ablation, with released extraction definitions | Part VI |
| G18. Field anchor | Omitted by default, so the claim is in-silico only. Open decision for Eric | Part XI |
| G19. Correction versus replication | A correction audit in the supplement lists the reproduced quantities and the withdrawn conclusions | Part X |
| C7. Retries could break pairing, validation criteria are unspecified, and identity is never checked | Validation criteria stated. Deterministic shared-key calls fail identically. Identity is checked byte for byte in the full run | Principles 6 and 9 |
| C11 (rest). Study 1 packages and the label structure are unspecified, and the history clutters the preregistered text | Full record for D0, NC0, R1 to R5, and NCR1. Labels defined. History moved out of the design document | Part V, Part VIII, Header |

## Not changed, with reasons

| Objection | Reason |
|---|---|
| C2, adding temperature as a factor | It would double the independence and Study 2 cells and add a dimension no claim needs. The claim is conditioned on the recorded settings instead, and the diversity association is reported |
| C6, G12, the expectedness of the results and the venue | No design change can make bounded synthetic results general. The framing and the target journal are Eric's decisions, and Part X states the bounded claim |
| G5, simulating precision before the run | A simulation would need variance components from data this design never looks at before the full run. Inconclusive results are instead reported as bounds |

## Round 5 amendments applied in version 7

`GPT Review of v6 (2026-10-30)` found 24 of the rows above met or met on condition and set five amendments for freezing. Version 7 applies them as follows. P3 becomes the paired gain of the pairwise text-only model over the pooled text-only baseline, with no world-anchored feature in either model. The H8 support rule uses one baseline for every gain, with the contribution fraction defined and a zero rule. Validation never checks the attribution line, so presence of the line is an outcome and not a cause of retry. Matcher validation uses 240 coded natural messages, 60 of them double-coded, with an absent-class rule and adjudication, and the coded messages serve as the bases for a challenge set with verified labels and hard negatives. Inference uses a fixed-split conditional estimand, a world-cluster bootstrap, centered bootstrap p-values, and fixed template pools with secondary sensitivity results. GPT's point that a precision simulation needs no pilot data is accepted, and an interpretive simulation that cannot change any rule is added.

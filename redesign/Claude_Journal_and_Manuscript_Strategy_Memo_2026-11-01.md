# Journal and Manuscript Strategy for the Redesigned Message Residue Study

Claude, 2026-11-01. Prepared at Eric's request for review by Eric and GPT. No manuscript text has been drafted, and no submission or transfer action has been taken.

## Basis

I read the npj Complexity decision letter and the single referee report, the Springer Nature transfer page, the 2026-10-29 Claude and GPT reviews of the rejection, and the canonical full-run reports in `build/runs/full/analysis/` (`text_only.md`, `secondary.md`, `inference.md`, `relational_checks.md`, `anchored.md`), as regenerated on 2026-10-31 and 2026-11-01 after the rarity correction, together with `build/LOG.md` and the replication report `build/runs/replication/analysis.md`. Every number below comes from those files. Journal facts (impact factors, charges, timelines, scope text, and transfer policy) were checked on 2026-11-01 against publisher, journal, and DOAJ pages, and the source for each is listed at the end. Facts that could not be verified are marked as such. I found no file named in the request that I could not open.

## 1. The scientific contribution

The central question is what a set of machine-generated reports reveals about the communication network that produced it, when the reports themselves are the only evidence. The strongest supported answer is asymmetric. Under production conditions matched so that every terminal message has the same marginal distribution, a single message carries almost no information about how it relates to other messages, while three messages compared with one another reveal which of them share a source with high reliability.

The design makes that asymmetry identifiable rather than merely observed. In the Study 2 sets, every terminal message is one rewrite of one observation of the full event record, written by the same producer under templates drawn independently for each generation slot. A set of three unconnected sources and an out-star therefore differ only in whether the three rewrites descend from three independent observations or from one shared observation. A classifier that sees one message from a set is at chance by construction, and it is at chance in the data. The aggregate of single-message predictions gives three-structure macro AUCs of 0.515, 0.498, and 0.508 for the three producers. A model that compares the messages reaches 0.827, 0.955, and 0.965. For the primary producer, three unconnected sources are separated from the out-star at AUC 0.908, against 0.699 for a baseline that pools each message's features without comparing them. The gain of 0.209 has a refitted bootstrap interval of 0.156 to 0.287 and p = 0.005, and it survives Holm correction with the hub-against-diamond test.

This goes beyond the observation that related reports resemble one another because the comparison class is not unrelated text. It is independent reports of the same facts by the same model, which are themselves highly similar. What the design isolates is the similarity that shared textual ancestry adds beyond shared facts and a shared author. That quantity is also what separates the result from authorship attribution and ordinary text classification. Those methods infer a property of a text from the text itself. Here the property, whether a message shares a parent with another message, is invisible in any single message by design, so the information is relational by construction and not by assumption.

The second part of the contribution is a map of what a single message does and does not carry. Branches that never reach the observed message leave no detectable trace. Both dead-end controls are equivalent to chance under the feature learner, and the full run's one inconclusive embedding result (0.553) did not replicate with fresh seeds and randomized generation order (0.493). Relay depth is detectable (chains of 1, 3, and 5 relays at AUC 0.599 and 0.613), as is the number of split-access spokes in a hub (0.613 and 0.630). Whether a synthesis combined independent or dependent inputs leaves a small trace (hub against diamond, feature AUC 0.552, replicated at 0.568 with permutation p = 0.005). That trace weakens after further relays and does not transfer across producers (0.499) or genres (0.509). A five-relay chain cannot be told from a diamond followed by three relays (0.489).

The contribution is therefore primarily methodological and concerns AI-agent systems. It establishes, for networks of language-model agents that observe, rewrite, and synthesize, which network properties are recoverable from their outputs and from what kind of evidence. It is network inference in the sense of recovering genealogical relations among terminal outputs, but it does not reconstruct graphs in general. It is not yet a finding about communication processes among people.

Claims the redesigned experiment supports:

- Shared textual ancestry is recoverable from sets of three messages with high discrimination, for three producers from different model families, under full access and one rewrite between the shared parent and each terminal message.
- The pair of messages that share a source is identified with AUC 0.863 over all pairs. Given that a set is a Y, the independent message is identified in 88.3% of sets. Without that knowledge, the five-configuration predictor is correct on 64.1% of sets and fully correct on 66 of 180 Y sets.
- The relational signal does not reduce to rare shared wording. Removing rare word-sequence overlap lowers AUC for every producer, by 0.029 to 0.041, and the gain over the pooled baseline remains positive without it (0.180, 0.087, and 0.056).
- Single-message information follows the message's own chain of rewrites and nothing outside it, within the tested structures.
- General-purpose language models used as readers, given a few labeled examples, detect shared ancestry at similar levels. For the primary producer under full access, Claude Sonnet 5.5 separates three unconnected sources from the out-star at 0.865 and GPT-6.1 Terra at 0.935.

Claims that remain speculative or outside the design:

- Any transfer to human writers, journalism, intelligence reporting, or deployed influence operations.
- Recoverability through more than one rewrite between a shared parent and the terminal messages. Every set in Study 2 has exactly one such rewrite, and the single-message traces in Study 1 weaken with further relays.
- Recoverability when producers deliberately diversify or obfuscate beyond the tested concealment instruction, or when a set mixes producers.
- The proposition-level account of how ancestry survives transmission (shared omissions). It rests on a judge that human coding has not validated, and even a validated measure would show association, not inheritance.

## 2. How completely the redesign answers the rejection

The editor's stated reason was that the design "does not distinguish structural mechanisms from production protocols, and does not establish what the classifier is recovering". The referee raised three groups of objections. The 2026-10-29 code review added that the compound motif was never composed and that five of the eight original motifs differed only in prompt.

Resolved by new experimental evidence:

- **Structure against protocol.** The single-message marginals in Study 2 are equal by construction, the aggregate of single-message predictions is at chance for all three producers, and the relational models are not. Within Study 1, the dead-end controls, which change graph components outside the terminal message's ancestry while holding its protocol fixed, are equivalent to chance. The replication found no difference in the one place the full run had shown one. These are exactly the convergent and discriminant tests the referee proposed. For the set results, the protocol cannot be what the classifier recovers. The paper should also report the direct check on one message drawn from each set. Under full access and neutral attribution it gives 0.545 for three unconnected sources against the out-star, inside the equivalence band but with an interval reaching past it (inconclusive). Split by prompt family, one stratum reaches 0.606, also inconclusive. That is small next to the relational 0.908, but it is the place a reviewer will look for protocol leakage.
- **The original independent-corroboration problem.** The referee's 96.4% example was recognition of an observer prompt. In the redesign the analogous contrast (direct report against direct report with dead-end branches) is at chance, as it should be.
- **The compound defect.** Composition is now implemented as a diamond followed by three relays, and the result is at chance against a five-relay chain. This is a boundary, reported as one.
- **Statistical dependence.** Sixty worlds instead of twenty, outer folds grouped by world, world-cluster bootstrap intervals, refitted label-exchangeability permutations for single-message tests, a refitted world bootstrap for the set gain, Holm correction over the two primary tests, and a fresh-seed replication of the single-message tests.
- **Narrow generality checks.** Three producers from different families, two template families, and two genres, with transfer reported where it fails.

Addressed by narrowing or correcting the interpretation:

- **The residue taxonomy.** The semantic, formal, and trace constructs are gone. Features are defined operationally (formal and attributional single-message families, and three relational families) and the relational families are ablated. The paper should claim nothing about residue types.
- **The reader-against-classifier comparison.** The readers and classifiers now see the same sets, but they still differ in supervision and information. The paper should report the readers as a second, descriptive line of evidence and draw no conclusion about why one method does better.
- **Mechanism stories.** The production-mechanism explanations the referee objected to have no counterpart in the text-only paper. The candidate mechanism, shared omission, is withheld until the judge is validated.

Partly resolved:

- **Calibration and proper scoring.** Brier score and log loss are now reported for the single-message contrasts. For the three-structure set models they are computed in `secondary.json` but not reported in `secondary.md`. Calibration of the five-configuration predictor has not been examined.
- **Generality.** The set models were trained and tested within each producer. Whether a set model trained on one producer works on another has not been tested, although its relational features (word-sequence overlap, sentence order, embedding similarity) are not producer-specific in form.

Remaining vulnerabilities likely to matter at the next journal:

- **Expected similarity.** A reviewer may say that rewrites of one text are obviously more similar than independent reports, so the result is unsurprising. The answer is the comparison class and the single-message null described above, and the paper has to make that argument in its first pages.
- **One rewrite step.** The set result holds for one rewrite between the shared parent and each terminal message. A reviewer can fairly ask how quickly it decays.
- **Synthetic worlds and one world generator.** All sixty worlds come from one generation process in two genres. That limits generality, and it is a limit to state, not to repair.
- **Estimands.** The intervals in the text-only reports are conditional on fixed out-of-fold predictions, and the refitted P3 bootstrap holds fold-level feature construction fixed. Both are stated in the reports and must be stated in the paper.
- **Partial access.** Under partial access, shared packages separate the structures by construction (pairwise AUC 0.994). Those results belong in supplementary material as a boundary, not in the main argument.

## 3. Journal recommendation

The journals below were checked on 2026-11-01. A JIF labeled 2025 is from the Journal Citation Reports released in June 2026. Acceptance rates are omitted because they do not estimate this manuscript's chances. The DOAJ figure is the journal's reported average time from submission to publication, not time to a decision.

| Journal | JIF (2025) | Mandatory charge | Published timing | Scope fit for this study |
|---|---|---|---|---|
| Transactions of the ACL | 11.7 | None (diamond open access) | Stated targets: reviews due in 3 weeks, decision about a week later. DOAJ 8 weeks | Good if framed as provenance of language-model pipeline outputs |
| Journal of Computer-Mediated Communication | 7.4 | None (APCs currently waived) | None published. DOAJ 15 weeks | Poor. Scope is social science of human mediated communication |
| Communication Methods and Measures | 5.8 | None on the subscription route | 15 days to first decision, 78 days to first post-review decision | Moderate. Requires a measurement method useful to communication scientists |
| Scientific Reports | 4.9 | $2,850 (fully open access) | Medians: 12 days to first decision, 138 days to acceptance | Moderate. Scope names natural sciences, psychology, medicine, and engineering, and review assesses validity rather than significance |
| Humanities & Social Sciences Communications | 4.8 | $1,990 | First decision in about 50 days. DOAJ 32 weeks | Poor. Since 21 September 2026 it excludes work whose primary contribution is methodological, including work rooted principally in computer science |
| Journal of Computational Social Science | 2.6 | None on the subscription route | Median 57 days to first decision | Moderate. Welcomes simulation, but of social phenomena |
| Computational Communication Research | Not found | None | None published. DOAJ 38 weeks | Good. Names agent-based simulation, machine learning, and communication structures |

Humanities & Social Sciences Communications should be ruled out. Its new scope statement describes this paper as out of scope almost word for word. The Journal of Computer-Mediated Communication should also be ruled out. Its readership studies people using media, and a study made up entirely of language-model agents would need a theory of transfer to human communication that the evidence does not support. Writing that theory to win the fit would inflate the contribution.

Scientific Reports is defensible but not the best option. Its validity-based review suits a design whose strength is identification, its decisions are fast, and its format (a 4,500-word main text, an unlimited Methods section, and eight display items) suits this paper. Two features count against it. The first is scope. Its aims statement does not name computer science or communication, so an editor could treat a study of language-model pipelines as outside "natural sciences, psychology, medicine and engineering", although the journal does publish computational work. The second is cost. The $2,850 charge is mandatory, and a financial-need waiver is discretionary and must be requested at submission. Those two features, together with a JIF lower than two free alternatives, make it a fallback.

Transactions of the ACL is the stronger first choice. Its impact factor is the highest of the candidates, it charges nothing, its review is fast, and its scope (all of computational linguistics and natural language processing) includes the question of what machine-generated text reveals about the system that produced it. Its reviewers will judge the paper on the evidence it actually has, which concerns language-model agents, and they will find the identification design legible. The likely reason for rejection of a technically sound version is a judgment that the methods are simple: logistic regression on hand-defined features, embeddings from a small local model, and no fine-tuned classifier. The answer is that the contribution is the identification design and the boundary map, not a new model, and that general-purpose language-model readers reach similar discrimination. That answer has to be made in the paper, not only in a cover letter. The writing burden is real. Regular papers have a 10-page limit with the detailed rules in the journal's formatting file, the format is LaTeX, and the related-work section must engage the literature on text reuse, detection and attribution of machine-generated text, and genealogical methods for copied texts. Each of those citations has to be verified against its source before drafting.

Communication Methods and Measures is the best option if Eric wants the paper's home to be communication science rather than natural language processing. Its JIF is 5.8, the subscription route is free, and its decisions are fast. The pitch would be a validated way to measure dependence among messages. Its likely reason for rejection is that the method is validated only on synthetic machine-generated text, so its usefulness to communication researchers working with human data is untested. Computational Communication Research fits better on scope but has no verified impact factor and the slowest reported timeline.

**Recommendation.** First choice: Transactions of the ACL. Practical fallback: Scientific Reports, with a waiver request at submission. Communication Methods and Measures is the alternative first choice if communication science is the intended field, and it is free. The cost of trying Transactions of the ACL first is about two months if it fails, and it risks no money.

## 4. Transfer or new submission

What the policies confirm. Nature Portfolio's transfer page says that "in almost all cases, if the paper was peer reviewed, the reviewer comments will be passed along to the receiving journal". The npj Complexity page says referee comments are "transferrable on request by the author". Authors may modify and replace their files before formally submitting the transfer, although the page advises against substantial changes during transfer. A transferred paper's received date resets to the date the receiving journal gets it. Scientific Reports' APC is set at the date of acceptance, and its discretionary waivers must be requested at submission.

What the policies do not settle. The page that lists the decision letter and referee identities among transferred materials covers transfers between Nature-branded journals and the Communications journals. npj Complexity is neither, and a Nature Physics page excludes transfers to the npj series and Scientific Reports from the sharing of referee identities. I found no time limit on the transfer offer, and no Scientific Reports page on how it treats transferred manuscripts. Whether a transfer resubmission counts as "submission" for a waiver request is also unverified.

Recommendation: if the paper goes to Scientific Reports, submit it as a new manuscript. The transfer offers no real editorial advantage. The received date resets either way, and the referees are unlikely to be reused for a study whose experiments they never saw. What the transfer would carry is a report written about a different experiment, which an editor could read as an unresolved history. A new submission should still disclose the earlier npj Complexity submission in the cover letter and describe in two or three sentences how the redesign answers the identification objection. That is both accurate and the strongest argument the paper has. Before submitting, Springer Nature should be asked whether a new submission of a substantially different study from the same author needs to reference the earlier manuscript ID, and how a waiver request is made. If Transactions of the ACL is chosen, none of this arises unless the fallback is used.

## 5. Manuscript argument and Results architecture

**Principal claim.** Under matched production, a single message from a network of language-model agents carries little information about its relation to other messages, while comparisons among three messages reveal which of them share a source. That is sharper than "multiple messages permit stronger inference", because it names the design condition that makes the single-message information zero.

**GPT's outline.** I would keep its opening problem: several apparently corroborating reports whose dependence is unknown. I would change three things. First, the design's identification logic belongs before any result, because the result is only interpretable once the reader knows single messages are matched. Second, the single-message findings should follow the relational results, not precede them. The relational result is the strongest, and the single-message map then explains why one message is not enough and where traces vanish. Third, "the textual features that support recovery" should be one short section with the ablation, not an inventory of feature families.

Proposed Results sequence:

1. **Matched structures and the single-message null.** One short section. The structures, shown as shapes, why their single-message marginals are equal, and the evidence that they are (the aggregate of single-message predictions at chance, and the dead-end controls equivalent to chance with their replication).
2. **Comparison among messages reveals shared ancestry.** Three unconnected sources against the out-star and the three-structure task, all three producers, pooled baseline against relational model, and the refitted inference. The prompted readers appear here as a second, descriptive line of evidence.
3. **Which messages share a source.** Pairwise same-root detection, odd-message identification given a Y set (88.3%), and the unconditional five-configuration result (64.1%, with 66 of 180 Y sets fully correct), keeping the conditional and unconditional figures distinct in every sentence that reports them.
4. **What carries the signal.** The three-family ablation under the corrected rarity fit.
5. **What a single message carries.** Relay depth and partition detectable, the small replicated hub-against-diamond trace, its weakening after further relays, its failure to transfer, and composition at chance.
6. **Boundaries.** Partial access, where shared packages separate the structures by construction, concealment instructions, stripped attribution lines, and message length. This section should be brief, with the detail in supplementary material.

Main-text figures, at most five:

- **Figure 1.** The design: structures as shapes, the matched template assignment, and what each classifier sees.
- **Figure 2.** For each producer, AUC for the aggregate of single messages, the pooled baseline, and the relational model, with intervals.
- **Figure 3.** Five-configuration outcomes for Y sets, showing the split between correct, demoted by the configuration split, wrong odd message, and wrong structure, beside the conditional odd-message rate.
- **Figure 4.** Ablation by feature family and producer, as changes from the full model with intervals.
- **Figure 5.** The single-message map: every Study 1 contrast as a point estimate with its interval against the equivalence band of 0.43 to 0.57.

Supplementary material:

- Presentation-order invariance.
- The rarity-fit correction, with both fits.
- The replication.
- Transfer tables.
- Length tertiles.
- Single-message leakage by prompt family.
- Full reader tables.
- Calibration metrics.
- The complete condition list.

The anchored analyses stay out of the manuscript and its supplement until the judge is validated. Including them now, even labeled exploratory, would give reviewers an unvalidated measure to attack in a paper that does not need it. If validation passes, they enter as a section on how ancestry survives transmission, and the pathwise analysis decides how strongly that section can speak.

## 6. Principal unresolved risks

The most consequential scientific risk is the expected-similarity objection described in section 2. The paper answers it with design, not rhetoric, and the opening has to establish the comparison class before the reader reaches a number.

The one-rewrite limit is the second. It is a boundary of the evidence, and the Discussion must not describe pipelines deeper than the ones tested.

The third is the untested transfer of set models across producers. A reviewer at a language-processing venue is likely to ask for it, and the existing corpus could answer it without new generation. I am not proposing it as a condition for drafting. I name it because it is the most probable reviewer request that could be met from data already in hand, and Eric and GPT should decide in advance whether to run it if asked.

Two editorial risks follow from the recommended venue. One is that the methods are judged too simple. The other is the 10-page limit, which forces the identification argument, the main results, and the boundaries into a short paper with appendices. Both are manageable, but they change how the paper is written, so the venue should be fixed before drafting begins.

A smaller record risk: three embedding-learner results that do not use rarity moved by at most 0.001 in AUC between the original run and the corrected rerun, for a cause not established (`LOG.md`, 2026-10-31, 21:40 onward). No verdict changed, and the paper should cite the current values.

## 7. The proposed workflow

The proposed division of labor is sound, with three changes.

First, before any prose, the agreed outline should be turned into a claim ledger: each claim the paper will make, its scope, its supporting number, and the canonical file and field it comes from. GPT drafts the claims and Claude attaches the sources and checks each claim against them. A claim with no source is dropped or rewritten before it reaches a paragraph.

Second, every number and figure in the manuscript should be generated by script from the canonical JSON outputs, so no value is typed by hand. I would build that script first. It also makes later corrections, such as the rarity fix, propagate without manual edits.

Third, one review in each round should come from a reader without the project dossier, who sees only the draft and the target journal's audience. GPT and Claude share most of the same materials, so their agreement is not independent evidence about whether the paper is legible to an outsider.

Eric's role as the final decision-maker on positioning, claims, venue, and authorship stands as proposed. The first decision needed is the venue, because it fixes length, format, and the literature the introduction must engage.

## Sources

Project files: `npj Complexity Submission/submission/npj_Complexity_REJECTION_Decision_Letter_and_Reviewer_Comments.md`, `npj Complexity Submission/submission/npj_Complexity_Springer_Nature_Transfer_Journal_Recommendations.md`, the 2026-10-29 Claude review (`npj Complexity Submission/`) and GPT review (Google Doc in the same folder), `build/LOG.md`, `build/README.md`, `build/runs/full/analysis/` (`text_only.md`, `secondary.md`, `inference.md`, `relational_checks.md`, `anchored.md`), and `build/runs/replication/analysis.md`.

Journal pages, checked 2026-11-01:

- Scientific Reports: https://www.nature.com/srep/about, https://www.nature.com/srep/about/aims, https://www.nature.com/srep/open-access, https://www.nature.com/srep/about/editorial-process, https://www.nature.com/srep/author-instructions/submission-guidelines, https://www.nature.com/nature-portfolio/about-journals/journal-metrics
- Journal of Computer-Mediated Communication: https://academic.oup.com/jcmc/pages/About, https://academic.oup.com/jcmc/pages/General_Instructions
- Humanities & Social Sciences Communications: https://www.nature.com/palcomms/journal-information, https://www.nature.com/palcomms/journal-information/aims-and-scope, https://www.nature.com/palcomms/open-access
- Journal of Computational Social Science: https://link.springer.com/journal/42001, https://link.springer.com/journal/42001/how-to-publish-with-us
- Computational Communication Research: https://journal.computationalcommunication.org/about, https://journal.computationalcommunication.org/openaccess
- Communication Methods and Measures: https://www.tandfonline.com/journals/hcms20/about-this-journal
- Transactions of the ACL: https://direct.mit.edu/tacl, https://transacl.org/index.php/tacl/about, https://transacl.org/index.php/tacl/about/submissions
- Transfer policy: https://www.nature.com/nature-portfolio/for-authors/transfer, https://www.nature.com/npjcomplex/for-authors-and-referees/editorial-process, https://www.nature.com/nphys/submission-guidelines/editorial-process
- DOAJ journal records (submission-to-publication weeks): https://doaj.org/api/search/journals/

Not verified: an impact factor for Computational Communication Research, the open-access charge at Communication Methods and Measures, whether the Journal of Computer-Mediated Communication's APC waiver is permanent, the exact page rules in the Transactions of the ACL formatting file, any journal's desk-rejection rate, and the transfer questions listed in section 4.

## Corrections after GPT's reply (2026-11-01)

GPT's reply, pasted by Eric on 2026-11-01, corrected two statements in this memo, and Claude accepts both.

First, section 1 says a single message "is at chance by construction, and it is at chance in the data". The first clause describes the generating design, under which the single-message marginals are matched. The second overstates the empirical diagnostics. The isolated-message test of three unconnected sources against the out-star gives 0.545 [0.509, 0.580] at 90%, which is inconclusive under the equivalence rule, and one prompt-family stratum gives 0.606, also inconclusive. The aggregate of single-message predictions is near 0.50 for all three producers. The precise statement separates three sources of evidence: a single message, the distribution of single-message properties across a set (which the pooled baseline captures, at 0.699), and explicit relations among the messages. The gain of 0.209 is the information the third adds to the second.

Second, section 3 estimates that an unsuccessful Transactions of the ACL submission would cost about two months. GPT reports that the journal announced review delays on 2026-07-09, and that appendices are limited to five pages of methodological detail and three pages of complementary results and are not reviewed. Claude has not independently verified either point. The two-month estimate should not be relied on.

GPT also proposed four Results sections in place of six, and three or four main figures, and a cross-producer transfer analysis on existing data, to be run during drafting and reported whatever its outcome. Claude agrees with all three.

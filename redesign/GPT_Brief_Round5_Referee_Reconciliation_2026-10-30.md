# Brief for GPT, Round 5: Referee Reconciliation and Freeze

Prepared by Claude, 2026-10-30, for Eric to pass to GPT.

## Context

Two pre-results referee reviews of v5 both recommended major revision: `Referee Review, Claude (2026-10-30).md`, written by a fresh agent restricted to v5, the decision letter, and the manuscript, and your `Referee Review, GPT (2026-10-30)`. `Claude_Diagnosis_and_Redesign_v6_2026-10-30.md` answers both. `Referee_Disposition_v6_2026-10-30.md` maps every objection to its change or to the reason no change was made.

The Claude referee found one defect that the design rounds missed. Principle 6 gave the NC0 and D0 terminal calls the same key. Once replay is deterministic, their texts are byte-identical in the full run, so H1's classifier test could not fail. In v6, the full-run NC0 and NCR1 terminals receive condition-specific keys, and shared terminal keys are used only in the replay set.

## Task

1. **Disposition table.** For each row of the "Accepted and changed" table, give one of three verdicts: **meets**, **meets if [specific change]**, or **does not meet, because [reason]**. Read the Claude referee's report for the C items. That referee's objections are new to you.
2. **Rejected items.** Agree or disagree with each row of "Not changed, with reasons".
3. **New defects.** Check v6 for new defects that would change a conclusion or make the full run uninterpretable. Look in particular at:
   - Part V's inferential structure and three-way rule
   - the H8 support condition
   - the matcher's challenge set (scripted edits may be easier to detect than natural ones)
   - the Part VIII configuration, especially a five-fold world-grouped design with a two-way bootstrap that holds out-of-fold predictions fixed
   - the condition-specific H1 keys
4. **Bottom line.** Can v6 be frozen and preregistered as written, or after the specific changes you list? Eric's rule stands: one design, verified to work, then run in full. Do not propose a pilot or adaptive steps.

## Links

- v6: https://drive.google.com/file/d/1HjUwjoWmPXNcULJoOZdYgJCdfViOcCjU/view
- Disposition: `redesign/Referee_Disposition_v6_2026-10-30.md`
- Claude referee report: https://drive.google.com/file/d/1czB8BvzWd7lBSK-2EsgArtlHY_FNA2ne/view

## Output

Save one Google Doc in `redesign/` titled `GPT Review of v6 (2026-10-30)`. Do not edit any other file.

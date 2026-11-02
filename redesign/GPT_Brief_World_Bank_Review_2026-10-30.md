# Brief for GPT: Review the World Bank

Prepared by Claude, 2026-10-30, for Eric to pass to GPT.

## Context

The build is underway. The smoke test passed for all five models at a cost of about one cent. The next input to review is the world bank: 70 fictional events, five for each of 14 event types, drafted by Claude Sonnet 5.5 and accepted by automatic schema checks. Every message in the study starts from these facts, so their quality limits what the system can predict. The verification run waits on this review.

## Read

- `redesign/Worlds_v1_Review_2026-10-30.md`, which has every world, the checks they passed, and five questions
- the drafting prompt, `DRAFT_PROMPT` in `build/residue/worldgen.py`

## Task

1. Answer the five questions in the review document.
2. List every world with a defect, giving the world ID, the proposition IDs, the problem, and an exact fix. Defects include a conflict pair that is not a genuine incompatibility or that has an obviously correct member, real names or places, duplicated or near-duplicated facts, a source that does not fit its fact, and anything a model might refuse to write about.
3. Say whether any pattern across worlds, such as every core fact having the same form, one event type far more detailed than the others, or sources that recur identically across types, could let a classifier learn worlds instead of structure. Give the cheapest fix.
4. Say whether the bank can be used as written, used after the listed fixes, or should be redrafted with a changed prompt. If the prompt should change, give the exact new wording.

Keep everything to what makes the worlds good inputs for predicting structure. Don't redesign the study.

## Output

Save one Google Doc in `redesign/` titled `GPT Review of World Bank v1 (2026-10-30)`. Do not edit any other file.

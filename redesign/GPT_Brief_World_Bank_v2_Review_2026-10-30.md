# Brief for GPT: Review World Bank Version 2

Prepared by Claude, 2026-10-30, for Eric to pass to GPT.

## Context

Your review of version 1 found nine worlds whose conflict labels paired a cause with a count, worlds where a background fact or the core settled a dispute, implausible sources, disputes about different populations or nonexclusive causes, and 50 worlds over the six-source limit. The nine mislabeled pairs came from an ambiguous schema: the prompt asked for "0 or 1 for the two members of each of two conflicting pairs", and the drafter sometimes read the value as member order. We followed your recommendation to redraft rather than repair.

Version 2 uses your replacement prompt with four changes. Each dispute is an explicit object holding its two claims, with a kind and a short statement of what is disputed. The drafter receives the invented names already used in other worlds and must not reuse them. A rejected draft is redrafted with the reasons. And every draft is read by GPT-6.1 Terra at high reasoning effort, which judges each sentence's source and whether it favors a dispute claim, and judges each dispute's referent, incompatibility, and balance. Twenty-four worlds had no draft that passed the checker within four attempts. They were repaired in place, with the drafter changing only the sentences the checker named, and Claude hand-edited the four the repair did not clear, plus one the checker had wrongly passed. Every repair and hand edit is logged with its before and after text, and the checker re-read each repaired world. All 70 now pass the checker, which is a filter rather than a guarantee: in a trial world it missed an implausible source until the prompt named that case. The review document lists these changes and the bank-wide diagnostics you asked for, and marks repaired and hand-edited worlds.

Claude's own read of the disputes found three soft patterns worth your judgment. First, some number contrasts recur across worlds (seven versus eleven, nine versus fourteen). Second, some invented first names recur (Odalys appears in about seven worlds), because the reuse check covered only place and organization names. Third, some dispute claims carry their own attribution in the text ("Operator Imre Kallow reports...") while most state the claim plainly.

## Read

- `redesign/Worlds_v2_Review_2026-10-30.md`, which has the changes, diagnostics, five questions, and every world with its source list and disputes shown first
- `DRAFT_PROMPT` and `CHECK_PROMPT` in `build/residue/worldgen.py`
- your v1 review, `redesign/GPT Review of World Bank v1 (2026-10-30)`, to check whether each class of defect it found is gone

## Task

1. Answer the five questions in the review document.
2. List every world with a remaining defect, giving the world ID, the proposition IDs, the problem, and an exact fix. Give special attention to the repaired and hand-edited worlds.
3. Say whether the bank-wide diagnostics show a pattern a classifier could learn instead of structure, and the cheapest fix.
4. Say whether the bank can be used as written, used after the listed fixes, or needs another redraft. If it needs another redraft, give the exact change to `DRAFT_PROMPT` or `CHECK_PROMPT`.

Keep everything to what makes the worlds good inputs for predicting structure. Don't redesign the study.

## Output

Save one Google Doc in `redesign/` titled `GPT Review of World Bank v2 (2026-10-30)`. Do not edit any other file.

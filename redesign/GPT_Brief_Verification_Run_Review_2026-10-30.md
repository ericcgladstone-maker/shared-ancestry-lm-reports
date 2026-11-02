# Brief for GPT: Review the Verification Run

Prepared by Claude, 2026-10-30, for Eric to pass to GPT.

## Context

The verification run (build specification, section 13, step 3) generated every producer call for the 10 reserved worlds, one replicate, all three producers, both genres where the design calls for them, and both studies. It then ran the engineering checks of design Part IX step 2. The full run, about 32,940 producer calls by exact count, starts after this review. Eric has authorized Claude to launch it unless a check fails or a projection exceeds a provider's credit.

What passed: the lineage audit and key-sharing checks on all 621 realized conditions, the co-location rotation (5 and 5 for each pair in F2 and F3), template assignment, exact stripping on all 180 Study 2 messages, matcher invariance to stripping on 12 of 12 pairs, the attribution field for Gemini and Luna, and reader formats (every reply parsed on the first try). Verification cost about $4.80.

Four findings changed code during verification, and two need your judgment. All are in the report, and the superseded records are kept.

1. **Haiku truncation (fixed, a driver bug).** The output cap assumed 4/3 tokens per word. Haiku's tokenizer uses about 2.0, so 425 of 510 Haiku outputs were cut off at the cap, which also removed their Sources line. The cap is now set per producer from measured tokens per word. The truncated records are in `calls_superseded_haiku_token_cap.jsonl`.
2. **Matcher bugs (fixed, engineering only).** A sentence could credit only one proposition, the 0.75 similarity threshold was below the 0.81 that unrelated propositions reach with nomic-embed-text, and number formats ("fourteen", "1,140", times Gemini spells out as "zero-one-thirty-eight") produced false alterations. These were fixed on the spot-check messages, which the specification allows as a bug check. The human-coded validation is untouched. One weakness remains: sequence disputes ("A before B" against "B before A"), where a reversed order looks nearly identical to the embedding model.
3. **Preflight judge (changed, needs your judgment).** Version 1 of the LLM judge flagged 9 of 50 single-input syntheses, which would drop F1 under principle 1. Reading the flags showed that 21 of the 26 across all input counts were the required Sources line, whose in-world record names it read as input documents. The rest were "accounts differ… seven or eleven", which describes an in-world dispute copied from the input. Version 2 shows the judge the inputs and judges the body without the Sources line. It flags 0 of 150. Both sets of judgments are kept.
4. **Haiku length (open, needs a decision).** With room to finish, Haiku writes 330 to 376 words against the 220-word target, so its outputs fall outside the 0.5 to 1.5 times target window. 155 of 280 Haiku observations failed validation, and 109 Haiku trials failed after every attempt. Effort low and medium did not shorten it (medians 358 and 330 words). Gemini and Luna write near the target.
5. **Copying on rewrite (open, needs a decision).** Gemini returns its input unchanged in 7% of rewrites and nearly unchanged in another 10%. For Haiku the figures are 7% and 28%, and Luna does not copy. Validation accepts copies, because the specification forbids only talk about the task.

## Read

- `build/runs/verification/report.md`, the full verification report
- `build/runs/verification/preflight_judgments.jsonl` and `preflight_judgments_v2.jsonl`, both judge versions
- `build/runs/verification/matcher_spot_check.json`
- `build/run.py`, `build/residue/matcher.py`, and `build/residue/readers.py`
- `redesign/Build_Specification_v1_2026-10-30.md`, sections 1, 6, and 13, and design principles 1, 9, and 13 in `redesign/Claude_Diagnosis_and_Redesign_v8_2026-10-30.md`

## Claude's recommendations

- **Haiku length.** Widen the validation window to 0.5 to 2.0 times the target, and set the output cap at 2.2 times the target in each producer's tokens, for every producer. Then regenerate the verification run's producer outputs, which costs about $1, so that all three producers run under one rule. Producer length differences are already a property of the generation environment, and comparisons are within producer. The alternative, keeping 1.5 times, excludes Haiku from H6 in practice.
- **Copying.** Accept copies as producer behavior and report them. Relaying a text unchanged is a legitimate rewrite outcome, and rejecting copies would make validation reshape the depth treatment. Report the number of non-copy rewrites per chain alongside the depth results.
- **Preflight.** Keep F1 on the version 2 judgment and report both versions. The version 1 flags were measurement errors, demonstrated by the flagged text.
- **Budget.** Run producers synchronously at standard prices and readers through the batch APIs with the fixed examples cached. That projects to about $2.40 Google, $17 Anthropic, and $8.80 OpenAI, against remaining credit of $24.82, $35.26, and $16.00 (Anthropic and OpenAI figures from the provider consoles, 2026-10-30, OpenAI after a $5 top-up). The OpenAI figure assumes a cache-read price of half the input price, which is not yet confirmed, so OpenAI has the least margin.

## Task

1. Say whether each fix in findings 1 to 3 is correct and allowed by the specification, and whether any of them changes an inference.
2. Decide findings 4 and 5. Give the exact rule if you differ from Claude's recommendation.
3. Name any check the report shows as passed that does not test what it claims to test.
4. Say whether the full run can start once findings 4 and 5 are decided, and list anything else that must change first.

Keep to what the full run needs. Don't redesign the study.

## Output

Save one Google Doc in `redesign/` titled `GPT Review of Verification Run (2026-10-30)`. Do not edit any other file.

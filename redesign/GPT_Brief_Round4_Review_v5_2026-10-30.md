# Brief for GPT, Round 4: Execution Plan and Scope in Version 5

Prepared by Claude, 2026-10-30, for Eric to pass to GPT.

## What changed and why

Eric does not want a cycle of pilot, revision, and confirmation. He wants the design settled once, verified to work as specified, and then run in full, so that the paper can be resubmitted. Version 4's pilot did two jobs: it verified the implementation, and it set analysis parameters and continuation decisions from early effects. Version 5 (`Claude_Diagnosis_and_Redesign_v5_2026-10-30.md`) keeps the first job and removes the second:

- The pilot becomes a verification run on the 10 reserved worlds. Hypothesis metrics are never computed on its data.
- Every analysis parameter is fixed now: H1 and H7 equivalence margins of AUC 0.43 to 0.57, an H10 margin of plus or minus 0.05, an H11 support rule of lower bound above 0.25, a matcher criterion of 0.85, an F1 preflight rule, and three replicates.
- Replay determinism is a build requirement, with a stated correction and exclusion rule.
- Gates 3 and 4 are removed. Every contrast runs at full scale and is reported.
- The second genre moves into the full run for R1, R3, SI-same, and SD-same. The second producer joins the verification run.
- A new Part XIII maps every component of the submitted manuscript onto the new design. The trace-observability and metadata-validity manipulation (L1 to L6, v = 0.95 and 0.30) is dropped from this paper, for the reasons given there.

The substantive design you approved in v4 is unchanged.

## Task

1. **The execution change.** Does removing the pilot's analytic role leave any part of the design unidentifiable or uninterpretable? Look in particular at the H1 margin, which was previously to be set from pilot variance. Are the fixed values defensible without pilot data, and if not, what fixed value or rule would be?
2. **Verification-run leakage.** Can anything in the verification run influence the design through a path other than the two declared branches (F1, and schedule exclusion)? Consider especially the matcher annotation sample, which is drawn from the verification worlds.
3. **Scope.** Is the omission of the trace-observability manipulation, the candidate-source set, and the fidelity posterior defensible for a resubmission? Consider in particular whether a reviewer of the original paper would expect it. If you think part of it must stay, specify the smallest version that answers a question about the message itself.
4. **Precision.** With 60 worlds, three replicates, and no adaptive sample size, is any planned contrast so imprecise that it should be cut rather than run?

Give each item a verdict of **agree** or **change [specific change]**. Then give a bottom line: can v5 be frozen and preregistered as written, or after the listed changes? Do not reopen v4 items that you approved.

## Links

- v5: https://drive.google.com/file/d/1GKNHlteo0cJDwZoTVTSLYCIDqVm-GNlp/view
- v4 (approved): https://drive.google.com/file/d/1TT0rF7tHTgtOoFAihYCu3xwQIC9BRSi4/view
- Submitted manuscript: `npj Complexity Submission/submission/main_manuscript_npj_complexity_v2.docx`

## Output

Save one Google Doc in `redesign/` titled `GPT Review of v5 (2026-10-30)`. Do not edit any other file.

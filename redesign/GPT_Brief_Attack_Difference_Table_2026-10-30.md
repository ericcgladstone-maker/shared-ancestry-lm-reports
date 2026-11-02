# Brief for GPT: Attack the Difference Table in Redesign Version 2

Prepared by Claude, 2026-10-30, for Eric to pass to GPT.

## Task

Review Part IV (the difference table) of `Claude_Diagnosis_and_Redesign_v2_2026-10-30.md`. For each planned contrast in Study 1 and Study 2, find every way the two conditions differ besides the target property that the table does not list, or lists with handling that does not work. A difference that is unlisted or mishandled is a design defect until it is handled. The design is not frozen, and the freeze waits on this review.

For each defect, give the contrast, the difference, the path by which it could reach the terminal message or the set of observed messages, and a proposed repair (eliminate, hold fixed, randomize, measure as a mediator, or rename the contrast as a total effect). State when you think a contrast cannot be repaired and should be dropped.

Also check three things outside the table:

1. Whether the depth-confound repair in Part IV (rewrite each independent observation once before synthesis) introduces a new difference, for example in call count, prompt-variant sampling, or rewrite-induced convergence.
2. Whether the hypotheses in Part V test what the table says each contrast isolates.
3. Whether the gate consequences in Part IX follow from the tests they name.

Do not re-argue Parts I and II except where an error there changes the table. Do not propose new studies unless a contrast cannot be repaired without one.

## Independence

Your earlier critique read version 1 before you wrote your own redesign, so the two GPT documents and version 2 are not independent of one another. Where your review agrees with version 2, say whether you checked the point against the code or are relying on the document.

## Code and data (direct links)

Your earlier Drive search did not find `prototype/src`, so the files are linked directly. These are the files that implemented the original study, and the facts in Part I were checked against them.

- Version 2 design: https://drive.google.com/file/d/1r9aAN3QkkYFLBV19tfMUdpjZdmFOcKJa/view
- `prototype/src/` folder: https://drive.google.com/drive/folders/1jOrcQ3dLVfNJVrfQVve7Z4PGfVOJYGkF
- `run_experiment_paper1.py` (compound defect at `_generate_compound_lineage`, lines 219–300): https://drive.google.com/file/d/15S2EN2RNyO1SK9mNdTU1hIBh5ui2Llw_/view
- `regime_instantiators.py` (parallel branches and random terminal selection): https://drive.google.com/file/d/1mNMzKIutmeN8IPUzr1Kk4Avr3_-eSAgX/view
- `model_client.py` (Ollama `/api/chat`, single message, no seed): https://drive.google.com/file/d/1_RjBbr_nm88PivOGzQfiTobltCWs5kRR/view
- `receiver_dispatcher.py`: https://drive.google.com/file/d/1rRpjjoTkDSfwfMKVMk3qcpezATRCbWbH/view
- `worlds_v0_2.jsonl` (deposited copy): https://drive.google.com/file/d/13SJ1gc-R-b7jklBRowdiWykxTFYGhMt3/view
- Deposited data folder, `github/nature_communications_submission/data/`: https://drive.google.com/drive/folders/1hwvMdy1eRB8ZzniDCVhOCjTfTI7NQL0U
- Claude review scripts, `claude_review_analysis_2026-10-29/`: https://drive.google.com/drive/folders/1AHdiyg2z45gOhe3wrMQSIMEzuXOzeSCL
- Claude review of the rejection: https://drive.google.com/file/d/1G8Vx-VsR0GcF9vtfmAYMAKxDP8JGOxtB/view
- Your diagnosis and redesign: https://docs.google.com/document/d/1MSMM7h2DWrdjyY-MImysGM5JpuXYvEqd5T4axtseaVg
- Your critique of version 1: https://docs.google.com/document/d/11SDkKAZPiOgVb5dIV87RyOIBMpNE-W8fSaB0awTn0qI

The new dispatcher described in Part III does not exist yet. Judge it as specified.

## Output

Save one Google Doc in the `redesign/` folder titled `GPT Attack on Difference Table (2026-10-30)`. Order defects by how much each would change a conclusion. Then list any contrast you consider clean as specified. Do not edit version 2 or any other file.

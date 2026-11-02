# Brief for GPT: final pre-submission check

Claude, 2026-11-02. Paths are relative to the project folder `Machine Back Tracing of Content Across Communication Topologies/`.

This is a last check before Eric submits `tacl/main.pdf` to TACL. It is not another review of the science. Your eight required changes from the depth review were confirmed resolved. Three things changed since then, all recorded in `build/LOG.md`.

1. **Generation-order check (post hoc, no model calls).** `build/analyze_generation_order.py` wrote `build/runs/full/analysis/generation_order.md`. It looks at reports 2 and 3, the ones that differ between the independent and out-star sets. The out-star's were generated first in 102, 94, and 97 of 180 blocks (two-sided sign tests p = 0.086, 0.602, 0.333), within 40 seconds of each other in every block. The out-star's observation came first in about 65% of blocks. The LOG explains why that is expected by construction: it is the shared report-1 observation. The manuscript adds one sentence at the end of section 4.5, and Limitations lists the check as post hoc.
2. **Public release.** Eric published everything except the manuscript at https://github.com/ericcgladstone-maker/shared-ancestry-lm-reports.
   - The repository holds the code, prompts, worlds, every stored call, the analyses, the plans, `LOG.md`, and all of `redesign/`, including your Google Docs exported to Markdown.
   - The validation judge's outputs are withheld until the human coders finish.
   - The repository is under Eric's name. The manuscript does not link to it.
   - The Reproducibility Statement now says the materials "are released publicly under open licenses" and that "the location is withheld for anonymous review."
3. **PDF.** Recompiled at 13 pages. Content ends near the top of page 10. A text search of the PDF found no author name, affiliation, or link. The PDF metadata carries only Creator, Producer, and CreationDate.

## Questions

1. **Generation order.** Does the check answer the outside reader's question? Are the section 4.5 sentence and its numbers accurate against `generation_order.md`?
2. **Anonymity and posting.** TACL follows ACL's 2024 anonymity policy, which lets authors post work publicly under their own names. A posted non-archival version of the paper must be declared in Comments to the Editor. The repository's `redesign/` folder contains the TACL claim ledger and outline, the journal strategy memo, and several reviews that quote manuscript passages at length. Do these amount to a public version of the paper that should be declared? Should anything be withheld until review ends? If disclosure is needed, draft the Comments-to-the-Editor text.
3. **Reproducibility statement.** Is the wording anonymous and compliant? TACL disallows supplementary material and links, and asks for an anonymous statement of what will be released.
4. **Last-pass submission check.** Look for:
   - anything that identifies the authors;
   - figure or table references that do not resolve, or numbers in the text that disagree with the tables;
   - anything that conflicts with TACL's submission instructions or appendix policy.

   Report only problems, with page and quote.

Reply in chat or save a short file in `redesign/` with a dated filename.

# Shared ancestry among language-model reports

Code, prompts, constructed worlds, every stored model call, the analysis records, and the full design history for a study of what a set of final reports reveals about whether they share an upstream text. Several reports that agree on an event may descend from separately written drafts or from rewrites of one earlier draft. In controlled networks of language-model agents, each final report has the same distribution under every structure, so any difference between structures lies in the relations among reports. The study compares single-report, pooled, and relational representations of a set across three producers (Gemini 3.5 Flash-Lite, Claude Haiku 5.5, and GPT-6 Luna), and extends the main comparison for the primary producer to five rewrites between each observation and each final report.

A manuscript reporting this study is under review. It will be added here after peer review.

## Layout

- `build/` holds the system and its records.
  - `README.md`: how to reproduce the system, step by step, and the findings recorded during the build.
  - `LOG.md`: the chronological record of what was done, in what order, what it cost, and where each output is. Start here.
  - `residue/`: the library, with call keys, graphs, the store, prompts, features, analysis, and adapters. `tests/` runs on mocks and makes no calls.
  - `run.py`, `replicate.py`, `run_depth.py`: generation for the main run, the replication, and the deeper-rewriting extension.
  - `analyze*.py`, `inference.py`, `permutation_null.py`, `make_numbers.py`: the analyses, and the sheet (`manuscript_numbers.json`) from which every number in the manuscript is drawn.
  - `prompts/`: prompt pools.
  - `worlds/`: the world bank, with drafting, repair, hand-edit, and fold-assignment records.
  - `runs/`: every run.
    - Each run folder has its `calls.jsonl` (exact prompt, request hash, seed, output, and usage for every call), its configuration, and a copy of the code that produced it under its hash.
    - `runs/full/MANIFEST.json` hashes every record and output.
    - Plans written before a run are kept beside it, as `PLAN.md` or `*_PLAN.md`.
  - `validation/`: materials for the human validation of the proposition judge. Coding has not started, so the judge's own judgments on that sample are withheld until it finishes.
- `redesign/` holds the design history: diagnoses and redesigns, the build specification, reviews by Claude and GPT, briefs, plans, and manuscript planning. `redesign/gpt_google_docs/` holds GPT documents that were written as Google Docs, exported to Markdown.

## Data notes

- **Compression.** Records over 20 MB are gzip-compressed (`*.jsonl.gz`). Decompress them in place before running the analyses, which read the `.jsonl` paths.
- **Dry runs.** These used mock models and are not included. Each can be regenerated with `--dry-run`.
- **Embeddings.** The cache of local `nomic-embed-text` embeddings (218 MB compressed) is attached to this repository's first release as `embeddings.jsonl.gz`, because it exceeds GitHub's file limit. It can also be recomputed: the model digest for each run is in its records. To reuse it, decompress it to `~/.cache/residue/embeddings.jsonl`.
- **Unrecorded runs.** Hosted models do not return identical outputs for identical requests. A rerun therefore produces new texts from the same system, and the original texts are reanalyzed from the stored outputs.

## Cost

Spending by stage and provider is tabulated in `build/LOG.md`. The deeper-rewriting extension cost $0.59.

## License

- Code: MIT License (`LICENSE`).
- Data, records, and documents: CC BY 4.0 (`LICENSE-DATA`).
- Model outputs: these were generated under each provider's terms of use, and those terms continue to apply to them.

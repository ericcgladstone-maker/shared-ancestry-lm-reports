"""Fresh-seed replication of the direct-report control and hub against diamond.

    python replicate.py [--dry-run] [--workers N]

Plan in runs/replication/PLAN.md, written before the run. Primary producer,
incident genre, the 60 full-run worlds, replicates 3 to 5. All control blocks
(D0, NC0, and the pure null NULL-a and NULL-b) run before any hub and
diamond block (SI-same, SD-same). Writes runs/replication/calls.jsonl, or
runs/replication-dry/ with the mock model. Resumes like run.py. run.py and
the full run's records are not touched.
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run  # noqa: E402
from residue import adapters  # noqa: E402
from residue import allocators as al  # noqa: E402
from residue import graphs as gr  # noqa: E402
from residue.dispatcher import BlockSpec  # noqa: E402
from residue.models import MockModel  # noqa: E402
from residue.store import CallStore  # noqa: E402

REPS = [3, 4, 5]


def null(tag):
    """One more draw of the direct-report request, keyed to its own condition."""
    def build(w, r, seed):
        return gr.Graph(tag, "S1", (gr._obs("o1", "obs:s1", al.full_record(w), tag=True),), ("o1",))
    return build


CONTROL = {"D0": gr.STUDY1["D0"], "NC0": gr.STUDY1["NC0"], "NULL-a": null("NULL-a"), "NULL-b": null("NULL-b")}
HUB_DIAMOND = {"SI-same": gr.STUDY1["SI-same"], "SD-same": gr.STUDY1["SD-same"]}
TERMINAL = {"D0": "o1", "NC0": "o1", "NULL-a": "o1", "NULL-b": "o1", "SI-same": "syn", "SD-same": "syn"}


def plan(worlds):
    fam = run.families(worlds, REPS)
    a, b = [], []
    for w in worlds:
        for r in REPS:
            spec = BlockSpec(w, r, "incident", run.PRIMARY, fam[(w.world_id, r)], run.RUN_SEED)
            a.append((f"C|{w.world_id}|{r}", spec, CONTROL))
            b.append((f"H|{w.world_id}|{r}", spec, HUB_DIAMOND))
    return a, b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args()
    out = os.path.join(HERE, "runs", "replication" + ("-dry" if a.dry_run else ""))
    os.makedirs(out, exist_ok=True)
    code_hash = run.snapshot(out)
    ledger = None if a.dry_run else adapters.Ledger(os.path.join(HERE, "smoke", "ledger.json"))
    if a.dry_run:
        m = MockModel(version=f"mock:{run.PRIMARY}")
    else:
        m = adapters.make(run.PRIMARY, ledger, role="producer", max_output_tokens=run.max_tokens("incident", run.PRIMARY))
    models = {(run.PRIMARY, "incident"): m}
    worlds = run.load_worlds("full")
    control, hub = plan(worlds)
    with open(os.path.join(out, "config.jsonl"), "a") as fh:
        fh.write(json.dumps({"script": "replicate.py", "dry_run": a.dry_run, "code_hash": code_hash,
                             "run_seed": run.RUN_SEED, "producer": run.PRIMARY, "replicates": REPS,
                             "worlds": [w.world_id for w in worlds], "params": run.req_params(m),
                             "started": time.time()}) + "\n")
    store = CallStore(os.path.join(out, "calls.jsonl"), extra={"code_hash": code_hash})
    summary = {}
    for label, blocks in (("control", control), ("hub_diamond", hub)):
        print(f"{label}: {len(blocks)} blocks, code {code_hash[:12]}", flush=True)
        results, failures, errors = run.run_blocks(blocks, store, models, a.workers)
        summary[label] = {"blocks": len(results), "failures": failures, "errors": errors,
                          "calls_made_so_far": store.calls_made}
        print(f"{label} done: calls made {store.calls_made}, failed trials {len(failures)}, errors {len(errors)}", flush=True)
        if errors:
            break
    summary["time"] = time.time()
    with open(os.path.join(out, "generation_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=1)
    if ledger:
        print("spend:", ledger.spent)


if __name__ == "__main__":
    main()

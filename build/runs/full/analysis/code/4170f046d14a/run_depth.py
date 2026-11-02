"""Deeper rewriting of the matched sets.

    python run_depth.py [--dry-run] [--workers N]

Plan in runs/depth/PLAN.md, written before the run. Primary producer, full
access, neutral arm, the 60 full-run worlds and replicates 0 to 2. Each
terminal report of the independent, out-star, and Y sets is rewritten four
more times in a chain. The full run's texts are step 1 and are read from
runs/full/calls.jsonl, which is not modified. New calls go to
runs/depth/calls.jsonl, or runs/depth-dry/ with a mock that keeps the live
request hashes. Writes sets.jsonl with the texts at each step. Resumes like
run.py.
"""
import argparse
import json
import os
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run  # noqa: E402
from residue import adapters  # noqa: E402
from residue import graphs as gr  # noqa: E402
from residue.dispatcher import BlockSpec, run_block  # noqa: E402
from residue.keys import make_key  # noqa: E402
from residue.models import MockModel  # noqa: E402
from residue.prompts import PER_FAMILY, render_with_inputs, target_words, template_id  # noqa: E402
from residue.store import CallStore  # noqa: E402

STRUCTURES = ("IND", "DEP", "MIX")
MAX_STEP = 5
RUN_CAP = 1.50  # Google spend allowed for this run, on top of the provider cap


class Dry:
    """Live version and request parameters, so step-1 texts are found in the
    full run's store, but new calls return mock text."""

    def __init__(self, m):
        self.version, self._p = m.version, run.req_params(m)
        self._mock = MockModel(version=m.version)

    def request_params(self):
        return self._p

    def __call__(self, prompt, seed):
        return self._mock(prompt, seed)


def step_template(spec, j, k):
    rng = random.Random(f"depth|{spec.seed}|{spec.world.world_id}|{spec.replicate}|{spec.genre}|{spec.producer}|g{j}|d{k}")
    return template_id(spec.family, "rewrite", rng.randrange(PER_FAMILY))


def block(spec, store, model):
    params = run.req_params(model)
    builders = {s: gr.STUDY2[f"{s}-full-neutral"] for s in STRUCTURES}
    res = run_block(spec, builders, store, model, model.version, params)  # step 1, all stored
    rng = random.Random(f"depth-order|{spec.seed}|{spec.world.world_id}|{spec.replicate}")
    order = list(STRUCTURES)
    rng.shuffle(order)
    rows = []
    for st in order:
        nodes = res[f"{st}-full-neutral"]
        chains = []
        for j in (1, 2, 3):
            node = nodes[f"m{j}"]
            text, key = node.text, node.key
            steps = [{"text": text, "key": key, "template_id": node.template_id}]
            for k in range(2, MAX_STEP + 1):
                tid = step_template(spec, j, k)
                key = make_key(study="S2", world=spec.world.world_id, replicate=spec.replicate, genre=spec.genre,
                               producer=spec.producer, family=spec.family, role=f"s2rw:g{j}:neutral:d{k}",
                               template_id=tid, package_id=None, parent_keys=[key])
                prompt = render_with_inputs(tid, [text], spec.genre)
                text = store.get_or_call(key, prompt, model.version, params, model, target_words(spec.genre),
                                         {"condition_first_seen": f"{st}-depth", "node": f"m{j}:d{k}", "fn": "rewrite"})
                steps.append({"text": text, "key": key, "template_id": tid})
            chains.append(steps)
        for k in range(1, MAX_STEP + 1):
            rows.append({"world": spec.world.world_id, "rep": spec.replicate, "producer": spec.producer,
                         "family": spec.family, "structure": st, "access": "full", "arm": "neutral", "depth": k,
                         "texts": [c[k - 1]["text"] for c in chains], "keys": [c[k - 1]["key"] for c in chains],
                         "template_ids": [c[k - 1]["template_id"] for c in chains]})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args()
    out = os.path.join(HERE, "runs", "depth" + ("-dry" if a.dry_run else ""))
    os.makedirs(out, exist_ok=True)
    code_hash = run.snapshot(out)
    ledger = None if a.dry_run else adapters.Ledger(os.path.join(HERE, "smoke", "ledger.json"))
    live = adapters.make(run.PRIMARY, ledger, role="producer", max_output_tokens=run.max_tokens("incident", run.PRIMARY))
    model = Dry(live) if a.dry_run else live
    start = dict(ledger.spent) if ledger else {}
    worlds = run.load_worlds("full")
    reps = [0, 1, 2]
    fam = run.families(worlds, reps)
    specs = [BlockSpec(w, r, "incident", run.PRIMARY, fam[(w.world_id, r)], run.RUN_SEED) for w in worlds for r in reps]
    with open(os.path.join(out, "config.jsonl"), "a") as fh:
        fh.write(json.dumps({"script": "run_depth.py", "dry_run": a.dry_run, "code_hash": code_hash,
                             "run_seed": run.RUN_SEED, "producer": run.PRIMARY, "replicates": reps, "max_step": MAX_STEP,
                             "worlds": [w.world_id for w in worlds], "params": run.req_params(model),
                             "started": time.time()}) + "\n")
    store = CallStore(os.path.join(out, "calls.jsonl"), extra={"code_hash": code_hash})
    base = CallStore(os.path.join(HERE, "runs", "full", "calls.jsonl"))
    reused = 0
    for k, rec in base.records.items():
        if k not in store.records:
            store.records[k] = rec
            reused += 1
    print(f"{len(specs)} blocks, {reused} full-run records available, code {code_hash[:12]}", flush=True)
    stop = threading.Event()

    def one(spec):
        if stop.is_set():
            return spec, None
        if ledger and ledger.spent.get("google", 0.0) - start.get("google", 0.0) > RUN_CAP:
            stop.set()
            raise adapters.BudgetExceeded(f"run cap {RUN_CAP} passed")
        return spec, block(spec, store, model)

    rows, errors = [], {}
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = [ex.submit(one, s) for s in specs]
        for i, fut in enumerate(as_completed(futs)):
            try:
                spec, r = fut.result()
                if r:
                    rows += r
            except Exception as e:
                errors[str(i)] = f"{type(e).__name__}: {e}"
                if isinstance(e, adapters.BudgetExceeded):
                    stop.set()
            if (i + 1) % 20 == 0 or i + 1 == len(futs):
                print(f"  blocks {i + 1}/{len(futs)}, calls made {store.calls_made}", flush=True)
    rows.sort(key=lambda r: (r["world"], r["rep"], r["depth"], r["structure"]))
    with open(os.path.join(out, "sets.jsonl"), "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {"blocks": len(specs), "set_rows": len(rows), "calls_made": store.calls_made, "errors": errors,
               "time": time.time()}
    if ledger:
        summary["spend_this_run"] = {p: ledger.spent.get(p, 0.0) - start.get(p, 0.0) for p in ledger.spent}
    with open(os.path.join(out, "generation_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k != "errors"}), "errors", len(errors), flush=True)
    for v in list(errors.values())[:5]:
        print(" ", v)


if __name__ == "__main__":
    main()

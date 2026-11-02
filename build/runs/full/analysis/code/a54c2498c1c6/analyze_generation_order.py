"""Generation order of the independent and out-star sets, full run.

    python analyze_generation_order.py

Post hoc check raised by the outside reader of 2026-11-02. Makes no model
calls: the sets are rebuilt from runs/full/calls.jsonl through a producer that
may only read the store, and each stored call's time is looked up by key.
For each block (world, replicate, producer), compares the generation times of
the reports that differ between the two structures, reports 2 and 3 of the
independent set against reports 2 and 3 of the out-star, and their parent
observations. Writes runs/full/analysis/generation_order.md and .json.
"""
import json
import os
import sys
from math import comb

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyze  # noqa: E402
import run  # noqa: E402
from residue import graphs as gr  # noqa: E402
from residue.dispatcher import BlockSpec  # noqa: E402
from residue.store import CallStore  # noqa: E402

OUT = analyze.OUT
CONDS = ("IND-full-neutral", "DEP-full-neutral")


def sign_p(k, n):
    """Two-sided exact sign test of k successes in n under p = 1/2."""
    tail = sum(comb(n, i) for i in range(0, min(k, n - k) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def main():
    worlds = run.load_worlds("full")
    reps = [0, 1, 2]
    fam = run.families(worlds, reps)
    store = CallStore(os.path.join(analyze.FULL, "calls.jsonl"))
    models = {k: run.Frozen(m) for k, m in run.producers(False, None).items()}
    builders = {c: gr.STUDY2[c] for c in CONDS}
    blocks = [(f"{w.world_id}|{r}|{p}", BlockSpec(w, r, "incident", p, fam[(w.world_id, r)], run.RUN_SEED), builders)
              for w in worlds for r in reps for p in run.PRODUCERS]
    results, failures, errors = run.run_blocks(blocks, store, models, 16)
    assert not errors, errors
    t = {k: rec["time"] for k, rec in store.records.items()}
    J = {}
    L = ["# Generation order of the independent and out-star sets, full run", "",
         "Post hoc check from the outside reader of 2026-11-02, no model calls. For each block, the mean generation time "
         "of the reports that differ between structures (reports 2 and 3) and of their parent observations. Sign test, "
         "two-sided, of how often the out-star's texts were generated first.", "",
         "| Producer | Blocks | Out-star reports 2 and 3 first | p | Median lead, s | Out-star observation before both independent observations 2 and 3 | p |",
         "|---|---|---|---|---|---|---|"]
    for p in run.PRODUCERS:
        rows = []
        for bid, res in results.items():
            if not bid.endswith(p) or any(c not in res for c in CONDS):
                continue
            ind, dep = res["IND-full-neutral"], res["DEP-full-neutral"]
            ti = np.mean([t[ind[n].key] for n in ("m2", "m3")])
            td = np.mean([t[dep[n].key] for n in ("m2", "m3")])
            oi = max(t[ind[n].key] for n in ("o2", "o3"))
            od = t[dep["o1"].key]
            rows.append({"block": bid, "ind_reports": ti, "dep_reports": td, "dep_first": bool(td < ti),
                         "lead_s": float(ti - td), "dep_obs_first": bool(od < min(t[ind[n].key] for n in ("o2", "o3"))),
                         "ind_obs_last": oi})
        n = len(rows)
        k = sum(r["dep_first"] for r in rows)
        ko = sum(r["dep_obs_first"] for r in rows)
        J[p] = {"blocks": n, "dep_reports_first": k, "p": sign_p(k, n), "median_lead_s": float(np.median([r["lead_s"] for r in rows])),
                "dep_obs_first": ko, "p_obs": sign_p(ko, n), "rows": rows}
        L.append(f"| {p} | {n} | {k} | {J[p]['p']:.3f} | {J[p]['median_lead_s']:.1f} | {ko} | {J[p]['p_obs']:.3f} |")
    with open(os.path.join(OUT, "generation_order.json"), "w") as fh:
        json.dump(J, fh, indent=1)
    with open(os.path.join(OUT, "generation_order.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()

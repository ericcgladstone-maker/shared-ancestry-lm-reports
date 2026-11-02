"""Rewrites that return their input unchanged, in the matched sets and the depth chains.

    python analyze_copying.py

Post hoc, no model calls. Copying was first recorded in the verification run
(README, verification findings). This counts, for each depth run, how many
rewrite steps in each distinct chain changed the text (output not identical
to its input after stripping whitespace), and how often the out-star's
rewrites of its shared observation are byte-identical to each other. Writes
runs/full/analysis/copying.md and .json.
"""
import json
import os
import sys
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from residue.prompts import DELIM  # noqa: E402

RUNS = os.path.join(HERE, "runs")
OUT = os.path.join(RUNS, "full", "analysis")
DEPTH_RUNS = (("depth", (1, 2, 3, 5)), ("depth_haiku", (1, 2, 3)))


def main():
    recs = {}
    for f in ("full", "depth", "depth_haiku"):
        for line in open(os.path.join(RUNS, f, "calls.jsonl"), encoding="utf-8"):
            r = json.loads(line)
            if r["valid"]:
                recs[r["key"]] = r

    def changed(key):
        r = recs[key]
        return r["output"].strip() != r["prompt"].split(DELIM)[1].strip()

    J = {}
    L = ["# Rewrites that return their input unchanged", "",
         "Post hoc, no model calls. A step changed the text if its output is not identical to its input. Counts are over "
         "the distinct chains of each depth run (five per block, 180 blocks).", "",
         "| Producer | Rewrite calls | Chains | Mean steps that changed the text | Chains changed at every step | Out-star sets with two identical reports (one rewrite) |",
         "|---|---|---|---|---|---|"]
    for run_name, depths in DEPTH_RUNS:
        rows = [json.loads(l) for l in open(os.path.join(RUNS, run_name, "sets.jsonl"), encoding="utf-8")]
        prod = rows[0]["producer"]
        chains = {}
        for r in rows:
            for j in range(3):
                chains.setdefault((r["world"], r["rep"], r["structure"], j), {})[r["depth"]] = r["keys"][j]
        uniq = {c[1]: c for c in chains.values()}.values()
        dup = sum(len(set(r["texts"])) < 3 for r in rows if r["depth"] == 1 and r["structure"] == "DEP")
        J[prod] = {"chains": len(uniq), "dep_sets_with_identical_reports_depth1": dup, "by_depth": {}}
        for d in depths:
            n = [sum(changed(c[k]) for k in range(1, d + 1)) for c in uniq]
            J[prod]["by_depth"][d] = {"mean_changed": float(np.mean(n)), "all_changed": int(sum(x == d for x in n)),
                                      "distribution": dict(sorted(Counter(n).items()))}
            L.append(f"| {prod} | {d} | {len(n)} | {np.mean(n):.2f} | {sum(x == d for x in n)} | {dup if d == 1 else ''} |")
    with open(os.path.join(OUT, "copying.json"), "w") as fh:
        json.dump(J, fh, indent=1)
    with open(os.path.join(OUT, "copying.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()

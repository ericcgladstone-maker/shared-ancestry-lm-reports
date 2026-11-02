"""Exact permutation null for paired Study 1 contrasts.

    python permutation_null.py [n_permutations]

Within each world and replicate a contrast has one message of each class, so
under no effect the two labels are exchangeable. Each permutation swaps them
at random within every pair and reruns the full out-of-fold procedure,
including penalty selection. The null distribution therefore includes
training variance, which the world bootstrap on fixed out-of-fold
predictions does not. Writes runs/full/analysis/permutation_null.json.
"""
import json
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyze  # noqa: E402
import run  # noqa: E402
from residue import analysis as an  # noqa: E402
from residue.embed import Embedder  # noqa: E402
from residue.features import body  # noqa: E402

CONTRASTS = [("D0", "NC0", "embedding"), ("D0", "NC0", "features"), ("SD-same", "SI-same", "features"),
             ("SD-same", "SI-same", "embedding")]


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    worlds, s1, s2, _ = analyze.load()
    fo = analyze.folds()
    embed = Embedder(run.EMBED_CACHE)
    out = {}
    for a, b, lrn in CONTRASTS:
        rows = [r for r in s1 if r["producer"] == run.PRIMARY and r["genre"] == "incident" and r["cond"] in (a, b)]
        X = np.asarray(embed.many([body(r["text"]) for r in rows]) if lrn == "embedding"
                       else analyze.text_X([r["text"] for r in rows]), float)
        y = np.array([[a, b].index(r["cond"]) for r in rows])
        w = [r["world"] for r in rows]
        pair = [(r["world"], r["rep"]) for r in rows]
        obs = an.auc(y, an.oof_predict(X, y, w, fo)[0])
        null = []
        for i in range(n):
            rng = random.Random(f"perm|{run.RUN_SEED}|{a}|{b}|{lrn}|{i}")
            flip = {k: rng.random() < 0.5 for k in set(pair)}
            yp = np.array([1 - v if flip[k] else v for v, k in zip(y, pair)])
            null.append(an.auc(yp, an.oof_predict(X, yp, w, fo)[0]))
            print(a, b, lrn, i, round(null[-1], 3), flush=True)
        null = np.array(null)
        out[f"{a}|{b}|{lrn}"] = {"observed": obs, "null_mean": float(null.mean()), "null_sd": float(null.std()),
                                 "null_q05": float(np.quantile(null, 0.05)), "null_q95": float(np.quantile(null, 0.95)),
                                 "p_two_sided": float((np.sum(np.abs(null - 0.5) >= abs(obs - 0.5)) + 1) / (n + 1)),
                                 "null": null.tolist()}
        print(out[f"{a}|{b}|{lrn}"] | {"null": None}, flush=True)
    with open(os.path.join(analyze.OUT, "permutation_null.json"), "w") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()

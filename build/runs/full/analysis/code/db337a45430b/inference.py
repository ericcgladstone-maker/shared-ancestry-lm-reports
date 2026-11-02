"""Primary inference for P1, P2, and P3 (GPT Review of Full-Run Analyses, 2026-10-31).

    python inference.py

P1 and P2: refitted label-exchangeability permutations. Within each world and
replicate the two structures' labels are swapped at random and the whole
out-of-fold procedure, including penalty selection, is rerun. These are not
an exact randomization null, because each structure was built from its own
graph and seed; they test whether a refitted learner finds an association
between label and text beyond what label exchange produces.

P3: a refitted world bootstrap of the paired gain. Worlds are resampled with
replacement (each copy keeps its world's outer fold, so a copy of a test
world never trains its own fold), both learners are refitted and retuned on
the resample, and the gain AUC(pairwise) - AUC(pooled) is computed on the
same held-out rows. The p-value is centered, as in design Part VIII. The
rare-n-gram tables keep the original outer-fold training texts, an
unsupervised approximation.

Holm at 0.05 over P2 (AUC > 0.5, one-sided permutation p) and P3 (gain > 0,
refitted bootstrap p). Writes runs/full/analysis/inference.md and .json.
"""
import json
import os
import random
import sys
import time
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyze  # noqa: E402
import run  # noqa: E402
from residue import analysis as an  # noqa: E402
from residue.embed import Embedder  # noqa: E402
from residue.features import RarityTable, body, f_set_relational, pooled_set_features, sentences  # noqa: E402

PERMS = {("SD-same", "SI-same", "features"): 999, ("SD-same", "SI-same", "embedding"): 199,
         ("D0", "NC0", "features"): 499, ("D0", "NC0", "embedding"): 199,
         ("R1", "NCR1", "features"): 499, ("R1", "NCR1", "embedding"): 199}
NBOOT_REFIT = 200


def permutation(X, y, w, groups, fo, n, tag):
    y = np.asarray(y)
    obs = an.auc(y, an.oof_predict(X, y, w, fo)[0])
    idx = defaultdict(list)
    for i, g in enumerate(groups):
        idx[g].append(i)
    null = []
    for b in range(n):
        rng = random.Random(f"perm|{run.RUN_SEED}|{tag}|{b}")
        yp = y.copy()
        for ii in idx.values():
            v = list(y[ii])
            rng.shuffle(v)
            yp[ii] = v
        null.append(an.auc(yp, an.oof_predict(X, yp, w, fo)[0]))
    null = np.array(null)
    return {"auc": float(obs), "n_perm": n, "null_mean": float(null.mean()), "null_sd": float(null.std()),
            "null_q025": float(np.quantile(null, 0.025)), "null_q975": float(np.quantile(null, 0.975)),
            "p_upper": float((np.sum(null >= obs) + 1) / (n + 1)), "p_lower": float((np.sum(null <= obs) + 1) / (n + 1)),
            "p_two_sided": float((np.sum(np.abs(null - 0.5) >= abs(obs - 0.5)) + 1) / (n + 1))}


def main():
    only_p3 = len(sys.argv) > 1 and sys.argv[1] == "p3"
    t0 = time.time()
    worlds, s1, s2, _ = analyze.load()
    fo = analyze.folds()
    embed = Embedder(run.EMBED_CACHE)
    J = {"perm": {}}
    if only_p3:  # reuse the stored permutations
        J["perm"] = json.load(open(os.path.join(analyze.OUT, "inference.json")))["perm"]
    for (a, b, lrn), n in ({} if only_p3 else PERMS).items():
        rows = [r for r in s1 if r["producer"] == run.PRIMARY and r["genre"] == "incident" and r["cond"] in (a, b)]
        X = np.asarray(embed.many([body(r["text"]) for r in rows]) if lrn == "embedding"
                       else analyze.text_X([r["text"] for r in rows]), float)
        y = np.array([[a, b].index(r["cond"]) for r in rows])
        J["perm"][f"{a}|{b}|{lrn}"] = permutation(X, y, [r["world"] for r in rows],
                                                 [(r["world"], r["rep"]) for r in rows], fo, n, f"{a}|{b}|{lrn}")
        print(f"[{time.time() - t0:.0f}s] {a} {b} {lrn}", J["perm"][f"{a}|{b}|{lrn}"], flush=True)

    # P3 refitted bootstrap of the gain
    rows = [r for r in s2 if r["producer"] == run.PRIMARY and r["access"] == "full" and r["arm"] == "neutral"
            and r["structure"] in ("IND", "DEP")]
    y = np.array([1 if r["structure"] == "IND" else 0 for r in rows])
    w = np.array([r["world"] for r in rows])
    fold_of = np.array([fo[x] for x in w])
    pooled = [pooled_set_features(r["texts"]) for r in rows]
    pk = sorted(pooled[0])
    X0 = np.array([[d[k] for k in pk] for d in pooled])
    embed.many([body(t) for r in rows for t in r["texts"]] + [s for r in rows for t in r["texts"] for s in sentences(t)])
    Xr = {}
    for f in sorted(set(fold_of)):
        rar = RarityTable([t for r, fv in zip(rows, fold_of) if fv != f for t in r["texts"]])
        rel = [f_set_relational(r["texts"], rar, embed) for r in rows]
        rk = sorted(rel[0])
        Xr[f] = np.hstack([X0, np.array([[d[k] for k in rk] for d in rel])])

    def gain(idx, groups):
        fo2 = {g: fo[g.split("#")[0]] for g in set(groups)}
        yy, ff = y[idx], fold_of[idx]
        p0 = an.oof_predict(X0[idx], yy, groups, fo2)[0][:, 1]
        pr = np.zeros(len(idx))
        for f, X in Xr.items():
            if not np.any(ff == f):
                continue
            pf = an.oof_predict(X[idx], yy, groups, fo2)[0][:, 1]
            pr[ff == f] = pf[ff == f]
        return an.auc(yy, pr) - an.auc(yy, p0), an.auc(yy, p0), an.auc(yy, pr)

    full = np.arange(len(y))
    d_obs, a0, ar = gain(full, list(w))
    uniq = sorted(set(w))
    rows_of = {x: np.flatnonzero(w == x) for x in uniq}
    rng = np.random.default_rng(run.RUN_SEED)
    boot = []
    for b in range(NBOOT_REFIT):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        idx, groups = [], []
        for x in pick:
            idx += list(rows_of[x])
            # copies of a world stay one group, so inner folds never split them (a first version labeled each copy
            # separately, which let penalty selection see near-duplicates and biased the gain upward)
            groups += [x] * len(rows_of[x])
        try:
            boot.append(gain(np.array(idx), groups)[0])
        except ValueError:  # a resample whose inner folds lack a class
            continue
        if (b + 1) % 20 == 0:
            print(f"[{time.time() - t0:.0f}s] refit bootstrap {b + 1}", flush=True)
    boot = np.array(boot)
    J["P3_refit"] = {"pooled_auc": a0, "pairwise_auc": ar, "gain": d_obs, "n_boot": int(len(boot)),
                     "lo": float(np.quantile(boot, 0.025)), "hi": float(np.quantile(boot, 0.975)),
                     "p_centered": float((np.sum((boot - d_obs) >= d_obs) + 1) / (len(boot) + 1))}
    p2 = J["perm"]["SD-same|SI-same|features"]["p_upper"]
    J["holm"] = {"P2_p": p2, "P3_p": J["P3_refit"]["p_centered"], **an.holm({"P2": p2, "P3": J["P3_refit"]["p_centered"]})}
    with open(os.path.join(analyze.OUT, "inference.json"), "w") as fh:
        json.dump(J, fh, indent=1)

    nm = analyze.name
    L = ["# Inference for P1, P2, and P3, full run", "",
         f"Generated by `inference.py` at {time.strftime('%Y-%m-%d %H:%M')}. Refitted label-exchangeability permutations "
         "for the single-message contrasts, and a refitted world bootstrap for the set gain. Both rerun penalty "
         "selection on every resample, so their spread includes retraining variability, which the conditional "
         "bootstrap intervals in `text_only.md` leave out. The two answer different questions and are reported together.", "",
         "## Permutations", "",
         "| Contrast | Learner | AUC | Permutations | Null mean (SD) | Null 2.5th to 97.5th | One-sided p (AUC above null) | Two-sided p |",
         "|---|---|---|---|---|---|---|---|"]
    for k, v in J["perm"].items():
        a, b, lrn = k.split("|")
        L.append(f"| {nm(a)} against {nm(b)} | {lrn} | {v['auc']:.3f} | {v['n_perm']} | {v['null_mean']:.3f} "
                 f"({v['null_sd']:.3f}) | {v['null_q025']:.3f} to {v['null_q975']:.3f} | {v['p_upper']:.3f} | {v['p_two_sided']:.3f} |")
    r = J["P3_refit"]
    h = J["holm"]
    L += ["", "## P3 gain, refitted", "",
          f"Pooled baseline {r['pooled_auc']:.3f}, pairwise model {r['pairwise_auc']:.3f}, gain {r['gain']:.3f}, 95% refitted "
          f"bootstrap interval {r['lo']:.3f} to {r['hi']:.3f} ({r['n_boot']} resamples), centered one-sided p {r['p_centered']:.3f}.", "",
          "## Holm family", "",
          f"P2, hub against diamond, AUC above 0.5: one-sided permutation p {h['P2_p']:.3f}, "
          f"{'rejected' if h['P2'] else 'not rejected'} at 0.05 after Holm. P3, gain above 0: p {h['P3_p']:.3f}, "
          f"{'rejected' if h['P3'] else 'not rejected'}. The smallest attainable p is 1/(resamples + 1).", "",
          f"Run time {time.time() - t0:.0f} s.", ""]
    with open(os.path.join(analyze.OUT, "inference.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("wrote", os.path.join(analyze.OUT, "inference.md"))


if __name__ == "__main__":
    main()

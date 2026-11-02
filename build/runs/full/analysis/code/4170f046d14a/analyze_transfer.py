"""Cross-producer transfer of the set models (runs/full/analysis/cross_producer_transfer_PLAN.md).

    python analyze_transfer.py

Makes no model calls. For each ordered pair of producers, trains on the
training producer's full-access, neutral sets from the training worlds of
each outer fold and tests on the test producer's sets from that fold's
worlds. Same-producer pairs reproduce the canonical within-producer results.
Writes runs/full/analysis/cross_producer_transfer.md and .json.
"""
import json
import os
import sys
import time

import numpy as np
from sklearn.model_selection import GroupKFold

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyze  # noqa: E402
import run  # noqa: E402
from residue import analysis as an  # noqa: E402
from residue.embed import Embedder  # noqa: E402
from residue.features import WorldRarity, body, f_set_relational, pooled_set_features, sentences  # noqa: E402

OUT = analyze.OUT
TASKS = {"IND against DEP": ("IND", "DEP"), "three structures": ("IND", "DEP", "MIX")}


def fit_predict(Xtr, ytr, wtr, Xte, inner_k=4):
    """One outer split of residue.analysis.oof_predict: the penalty chosen by
    world-grouped inner cross-validation on the training rows only."""
    wtr = np.asarray(wtr)
    classes = np.unique(ytr)
    best_C, best = an.PENALTIES[0], -np.inf
    for C in an.PENALTIES:
        scores = []
        for itr, iva in GroupKFold(n_splits=inner_k).split(Xtr, ytr, wtr):
            m = an._model(C).fit(Xtr[itr], ytr[itr])
            if len(np.unique(ytr[iva])) < len(classes):
                continue
            scores.append(an._score(ytr[iva], m.predict_proba(Xtr[iva])))
        if scores and np.mean(scores) > best:
            best, best_C = float(np.mean(scores)), C
    return an._model(best_C).fit(Xtr, ytr).predict_proba(Xte), best_C


def main():
    t0 = time.time()
    log = lambda m: print(f"[{time.time() - t0:.0f}s] {m}", flush=True)  # noqa: E731
    worlds, s1, s2, _ = analyze.load()
    fo = analyze.folds()
    embed = Embedder(run.EMBED_CACHE)
    J = {"tasks": {}}
    for tname, classes in TASKS.items():
        rows = {p: [r for r in s2 if r["producer"] == p and r["access"] == "full" and r["arm"] == "neutral"
                    and r["structure"] in classes] for p in run.PRODUCERS}
        allr = [r for p in run.PRODUCERS for r in rows[p]]
        embed.many([body(t) for r in allr for t in r["texts"]] + [s for r in allr for t in r["texts"] for s in sentences(t)])
        res = {}
        for a in run.PRODUCERS:
            for b in run.PRODUCERS:
                A, B = rows[a], rows[b]
                fa = np.array([fo[r["world"]] for r in A])
                fb = np.array([fo[r["world"]] for r in B])
                yA = np.array([classes.index(r["structure"]) for r in A])
                yB = np.array([classes.index(r["structure"]) for r in B])
                wA, wB = [r["world"] for r in A], [r["world"] for r in B]

                def pooled(R):
                    d = [pooled_set_features(r["texts"]) for r in R]
                    k = sorted(d[0])
                    return np.array([[x[j] for j in k] for x in d])
                X0A, X0B = pooled(A), pooled(B)
                P0 = np.zeros((len(B), len(classes)))
                Pr = np.zeros((len(B), len(classes)))
                pens = {"pooled": [], "relational": []}
                for f in sorted(set(fa)):
                    tr, te = fa != f, fb == f
                    p, c = fit_predict(X0A[tr], yA[tr], np.array(wA)[tr], X0B[te])
                    P0[te] = p
                    pens["pooled"].append(c)
                    rar = WorldRarity.from_rows([r for r, fv in zip(A, fa) if fv != f])
                    relA = [f_set_relational(r["texts"], rar.for_world(r["world"]), embed) for r, fv in zip(A, fa) if fv != f]
                    relB = [f_set_relational(r["texts"], rar.for_world(r["world"]), embed) for r, fv in zip(B, fb) if fv == f]
                    rk = sorted(relA[0])
                    XrA = np.hstack([X0A[tr], np.array([[d[k] for k in rk] for d in relA])])
                    XrB = np.hstack([X0B[te], np.array([[d[k] for k in rk] for d in relB])])
                    p, c = fit_predict(XrA, yA[tr], np.array(wA)[tr], XrB)
                    Pr[te] = p
                    pens["relational"].append(c)
                s = (lambda P: P[:, 1]) if len(classes) == 2 else (lambda P: P)
                res[(a, b)] = {"P0": P0, "Pr": Pr, "y": yB, "w": wB, "pens": pens, "s": s}
                log(f"{tname}: {a} -> {b}")
        out = {}
        for (a, b), x in res.items():
            within = res[(b, b)]
            assert np.array_equal(within["y"], x["y"])
            o = {"train": a, "test": b, "n_test_sets": len(x["y"]), "penalties": x["pens"],
                 "pooled": an.auc_with_ci(x["y"], x["s"](x["P0"]), x["w"], n=analyze.NBOOT),
                 "relational": an.auc_with_ci(x["y"], x["s"](x["Pr"]), x["w"], n=analyze.NBOOT),
                 "relational_minus_pooled": an.paired_delta_auc(x["y"], x["s"](x["Pr"]), x["s"](x["P0"]), x["w"], n=analyze.NBOOT)}
            if a != b:
                o["relational_minus_within"] = an.paired_delta_auc(x["y"], x["s"](x["Pr"]), within["s"](within["Pr"]), x["w"], n=analyze.NBOOT)
            out[f"{a}|{b}"] = o
        J["tasks"][tname] = out
    with open(os.path.join(OUT, "cross_producer_transfer.json"), "w") as fh:
        json.dump(J, fh, indent=1, default=float)

    def ci(v):
        return f"{v['auc']:.3f} [{v['lo']:.3f}, {v['hi']:.3f}]"

    def dci(v):
        return f"{v['delta']:+.3f} [{v['lo']:+.3f}, {v['hi']:+.3f}]"

    L = ["# Cross-producer transfer of the set models, full run", "",
         f"Generated by `analyze_transfer.py` at {time.strftime('%Y-%m-%d %H:%M')}, following `cross_producer_transfer_PLAN.md`. "
         "No model calls. Full access, neutral attribution. Each model is trained on one producer's sets from the training "
         "worlds of an outer fold and tested on another producer's sets from that fold's worlds, so no world is in both. "
         "Rarity tables come from the training producer with each training row's own world removed. Intervals are world "
         "bootstraps on fixed out-of-fold predictions (2,000 draws). Rows with the same training and test producer reproduce "
         "the within-producer results.", ""]
    for tname, out in J["tasks"].items():
        L += [f"## {tname}", "", ("AUC. " if tname == "IND against DEP" else "Macro one-versus-one AUC. ") +
              "The last column is the paired change from the test producer's within-producer relational model on the same sets.", "",
              "| Trained on | Tested on | Pooled baseline | Relational model | Relational minus pooled | Relational minus within-producer |",
              "|---|---|---|---|---|---|"]
        for k, o in out.items():
            L.append(f"| {o['train']} | {o['test']} | {ci(o['pooled'])} | {ci(o['relational'])} | {dci(o['relational_minus_pooled'])} | "
                     f"{dci(o['relational_minus_within']) if 'relational_minus_within' in o else 'within'} |")
        L.append("")
    L.append(f"Run time {time.time() - t0:.0f} s.")
    with open(os.path.join(OUT, "cross_producer_transfer.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("wrote", os.path.join(OUT, "cross_producer_transfer.md"))


if __name__ == "__main__":
    main()

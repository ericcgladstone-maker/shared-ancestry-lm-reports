"""Salience-sensitive reanalysis of shared omissions. UNVALIDATED, exploratory.

    python analyze_salience.py

Agreed in redesign/GPT Reply to Claude Assessment of Network Tests
(2026-10-31), question 3. The shared-deviation statistic in
analyze_anchored.py compares a pair's shared omissions with the number
expected if each message's omissions fell at random on the facts. Some facts
are dropped by nearly every writer, so random placement understates how often
independent writers converge. This script replaces random placement with a
fact-level omission propensity and asks how much of the out-star's excess
over three unconnected sources remains.

Scope: Study 2, primary producer, full access, neutral arm, three unconnected
sources (IND) against out-star (DEP), omissions of undisputed facts only (16
of 20 facts per world; the 4 dispute members enter anchored.md through their
resolutions and are left out here).

Two propensities.

- Held-out model. A logistic model of P(absent) on fact characteristics
  available from the world record (core event, position in the presented
  record, length in words, whether it contains a digit), fitted for each
  outer fold on IND messages from the other folds' worlds only. It can enter
  a world-held-out classifier.
- Same-world reference, transductive and descriptive only. The judged Study 1
  one-relay chains of the same world (three per world, full record observed
  and rewritten once, the same production steps as a Study 2 message),
  shrunk toward the held-out model's prediction with weight 3. It uses
  unlabeled auxiliary texts from the test world, so it enters no classifier.

Expected shared omissions for a pair: each message's propensities are tilted
on the logit scale until they sum to that message's own omission count, and
the expectation is the sum over facts of the two tilted probabilities'
product. With a constant propensity this reduces to random placement.
Writes runs/full/analysis/salience.md and .json.
"""
import json
import os
import re
import sys
import time
from collections import defaultdict
from itertools import combinations
from statistics import median

import numpy as np
from sklearn.linear_model import LogisticRegression

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyze  # noqa: E402
import analyze_anchored as aa  # noqa: E402
import run  # noqa: E402
from residue import analysis as an  # noqa: E402
from residue.features import body, pooled_set_features  # noqa: E402
from residue.keys import sha256  # noqa: E402

SHRINK = 3.0


def fact_x(world, pid):
    p = world.by_id()[pid]
    pos = world.ids().index(pid) / (len(world.ids()) - 1)
    return [float(p.core), pos, pos * pos, np.log(len(p.text.split())), float(bool(re.search(r"\d", p.text)))]


def tilt(p, k):
    """Shift logit(p) by one constant so the probabilities sum to k."""
    p = np.clip(np.asarray(p, float), 1e-4, 1 - 1e-4)
    if k <= 0:
        return np.zeros_like(p)
    if k >= len(p):
        return np.ones_like(p)
    lg = np.log(p / (1 - p))
    lo, hi = -30.0, 30.0
    for _ in range(80):
        c = (lo + hi) / 2
        if (1 / (1 + np.exp(-(lg + c)))).sum() < k:
            lo = c
        else:
            hi = c
    return 1 / (1 + np.exp(-(lg + (lo + hi) / 2)))


def main():
    t0 = time.time()
    worlds, s1, s2, _ = analyze.load()
    wmap = {w.world_id: w for w in worlds}
    fo = analyze.folds()
    jd = aa.load_judgments()

    def facts_of(w):
        disputed = {p for pr in w.conflict_pairs() for p in pr}
        return [p for p in w.ids() if p not in disputed]

    def absent(wid, text):
        r = jd.get((wid, sha256(body(text))))
        return None if r is None else {p: r["facts"][p] == "absent" for p in facts_of(wmap[wid])}

    rows = [r for r in s2 if r["producer"] == run.PRIMARY and r["access"] == "full" and r["arm"] == "neutral"
            and r["structure"] in ("IND", "DEP")]
    om = [[absent(r["world"], t) for t in r["texts"]] for r in rows]
    keep = [i for i, e in enumerate(om) if all(x is not None for x in e)]
    rows, om = [rows[i] for i in keep], [om[i] for i in keep]
    r1 = defaultdict(list)
    for r in s1:
        if r["producer"] == run.PRIMARY and r["genre"] == "incident" and r["cond"] == "R1":
            a = absent(r["world"], r["text"])
            if a is not None:
                r1[r["world"]].append(a)

    # held-out propensity model, one per outer fold, fitted on IND messages of training worlds
    prop_model, fit_info = {}, {}
    for f in sorted(set(fo.values())):
        X, y = [], []
        for r, e in zip(rows, om):
            if fo[r["world"]] != f and r["structure"] == "IND":
                w = wmap[r["world"]]
                for msg in e:
                    for pid, v in msg.items():
                        X.append(fact_x(w, pid))
                        y.append(int(v))
        m = LogisticRegression(C=1.0, max_iter=5000).fit(np.array(X), np.array(y))
        fit_info[f] = {"n": len(y), "rate": float(np.mean(y)), "coef": [float(c) for c in m.coef_[0]]}
        for wid in [x for x in wmap if fo[x] == f]:
            w = wmap[wid]
            fs = facts_of(w)
            prop_model[wid] = dict(zip(fs, m.predict_proba(np.array([fact_x(w, p) for p in fs]))[:, 1]))

    # held-out check of the model: fact-level AUC on IND test-world messages
    yy, pp = [], []
    for r, e in zip(rows, om):
        if r["structure"] == "IND":
            for msg in e:
                for pid, v in msg.items():
                    yy.append(int(v))
                    pp.append(prop_model[r["world"]][pid])
    from sklearn.metrics import roc_auc_score
    model_auc = float(roc_auc_score(yy, pp))

    prop_world = {}
    for wid, w in wmap.items():
        fs = facts_of(w)
        n = len(r1[wid])
        prop_world[wid] = {p: (sum(m[p] for m in r1[wid]) + SHRINK * prop_model[wid][p]) / (n + SHRINK) for p in fs}

    def pair_stats(a, b, prop):
        fs = list(a)
        shared = sum(1 for p in fs if a[p] and b[p])
        ka, kb = sum(a.values()), sum(b.values())
        random_exp = ka * kb / len(fs)
        if prop is None:
            return shared, shared - random_exp
        base = np.array([prop[p] for p in fs])
        qa, qb = tilt(base, ka), tilt(base, kb)
        return shared, shared - float((qa * qb).sum())

    nulls = {"random placement": lambda wid: None, "held-out salience model": lambda wid: prop_model[wid],
             "same-world reference (transductive)": lambda wid: prop_world[wid]}
    y = np.array([1 if r["structure"] == "IND" else 0 for r in rows])
    wl = [r["world"] for r in rows]
    pooled = [pooled_set_features(r["texts"]) for r in rows]
    pk = sorted(pooled[0])
    X0 = np.array([[d[k] for k in pk] for d in pooled])
    p0 = an.oof_predict(X0, y, wl, fo)[0][:, 1]
    J = {"sets": len(rows), "model_fact_auc": model_auc, "fits": fit_info,
         "r1_per_world": float(np.mean([len(v) for v in r1.values()])), "A0": an.auc_with_ci(y, p0, wl, n=analyze.NBOOT),
         "nulls": {}}
    for nname, getp in nulls.items():
        per = [[pair_stats(a, b, getp(r["world"])) for a, b in combinations(e, 2)] for r, e in zip(rows, om)]
        sh = np.array([np.mean([x[0] for x in ps]) for ps in per])
        ex = np.array([np.mean([x[1] for x in ps]) for ps in per])

        def diff(idx, v=ex):
            i = np.asarray(idx)
            return v[i][y[i] == 0].mean() - v[i][y[i] == 1].mean()
        boot = an.world_bootstrap(diff, wl, n=analyze.NBOOT)
        out = {"shared": {"IND": float(sh[y == 1].mean()), "DEP": float(sh[y == 0].mean())},
               "excess": {"IND": float(ex[y == 1].mean()), "DEP": float(ex[y == 0].mean())},
               "dep_minus_ind": float(diff(np.arange(len(y)))),
               "dep_minus_ind_ci": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))]}
        for st, lab in (("IND", 1), ("DEP", 0)):
            def m(idx, lab=lab):
                i = np.asarray(idx)
                return ex[i][y[i] == lab].mean()
            b = an.world_bootstrap(m, wl, n=analyze.NBOOT)
            out[f"excess_ci_{st}"] = [float(np.quantile(b, 0.025)), float(np.quantile(b, 0.975))]
        if not nname.endswith("(transductive)"):
            S = np.array([[min(x[1] for x in ps), median(x[1] for x in ps), max(x[1] for x in ps)] for ps in per])
            ps_ = an.oof_predict(np.hstack([X0, S]), y, wl, fo)[0][:, 1]
            alone = an.oof_predict(S, y, wl, fo)[0][:, 1]
            out["alone"] = an.auc_with_ci(y, alone, wl, n=analyze.NBOOT)
            out["As"] = an.auc_with_ci(y, ps_, wl, n=analyze.NBOOT)
            out["As_minus_A0"] = an.paired_delta_auc(y, ps_, p0, wl, n=analyze.NBOOT)
        J["nulls"][nname] = out
        print(f"[{time.time() - t0:.0f}s] {nname}: excess IND {out['excess']['IND']:.2f} DEP {out['excess']['DEP']:.2f}", flush=True)
    with open(os.path.join(analyze.OUT, "salience.json"), "w") as fh:
        json.dump(J, fh, indent=1)

    fmt = analyze.fmt
    L = ["# Salience-sensitive shared omissions, full run (UNVALIDATED, exploratory)", "",
         f"Generated by `analyze_salience.py` at {time.strftime('%Y-%m-%d %H:%M')}. Proposition judge judge-v1, not "
         "validated by human coding, so nothing here supports a claim until it is. The analysis was added after the full "
         "run's results were seen, at GPT's and Claude's agreement (`redesign/GPT Reply to Claude Assessment of Network "
         "Tests (2026-10-31)`, question 3).", "",
         f"Three unconnected sources (IND) against out-star (DEP), primary producer, full access, neutral arm, {J['sets']} sets. "
         "Omissions of the 16 undisputed facts per world only, so the counts differ from `anchored.md`, which also counts "
         "dispute resolutions.", "",
         "Each null gives the number of omissions two messages would share if each omitted its own number of facts "
         "independently, with the chance of omitting each fact set by the null. Random placement treats all facts alike. "
         "The held-out salience model predicts a fact's omission from the core-event flag, its position in the record the "
         "observer saw, its length, and whether it contains a digit, and is fitted on IND messages from training worlds "
         f"only (fact-level AUC on held-out IND messages {model_auc:.3f}). The same-world reference uses the same world's "
         f"judged one-relay chains ({J['r1_per_world']:.1f} per world), shrunk toward the model with weight {SHRINK:g}. It "
         "draws on other texts from the test world, so it is a transductive description and enters no classifier.", "",
         "| Null | Shared per pair, IND / out-star | Excess, IND [95%] | Excess, out-star [95%] | Out-star minus IND [95%] | "
         "Excess alone AUC [95%] | A_s − A_0 [95%] |", "|---|---|---|---|---|---|---|"]
    for nname, v in J["nulls"].items():
        a = f"{fmt(v['alone'])}" if "alone" in v else "not fitted"
        d = (f"{v['As_minus_A0']['delta']:.3f} [{v['As_minus_A0']['lo']:.3f}, {v['As_minus_A0']['hi']:.3f}]"
             if "As_minus_A0" in v else "not fitted")
        L.append(f"| {nname} | {v['shared']['IND']:.2f} / {v['shared']['DEP']:.2f} | {v['excess']['IND']:.2f} "
                 f"[{v['excess_ci_IND'][0]:.2f}, {v['excess_ci_IND'][1]:.2f}] | {v['excess']['DEP']:.2f} "
                 f"[{v['excess_ci_DEP'][0]:.2f}, {v['excess_ci_DEP'][1]:.2f}] | {v['dep_minus_ind']:.2f} "
                 f"[{v['dep_minus_ind_ci'][0]:.2f}, {v['dep_minus_ind_ci'][1]:.2f}] | {a} | {d} |")
    L += ["", f"Pooled baseline A_0 {fmt(J['A0'])}. Intervals are world-cluster bootstraps on fixed out-of-fold predictions. "
          "A null that captured all convergence among independent writers would put the IND excess at zero. The out-star "
          "minus IND difference is the part of shared omission that the null does not attribute to what writers drop anyway.",
          "", f"Run time {time.time() - t0:.0f} s.", ""]
    with open(os.path.join(analyze.OUT, "salience.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("wrote", os.path.join(analyze.OUT, "salience.md"))


if __name__ == "__main__":
    main()

"""Secondary text-only analyses and calibration checks for the full run.

    python analyze_secondary.py [n_permutations]

Complements analyze.py and uses the same rows, folds, and learners. Makes no
model calls. Writes runs/full/analysis/secondary.md and secondary.json.
Nothing here uses the proposition matcher.

Permutation nulls swap labels at random within each world and replicate
(the unit that holds one message of each class) and rerun the whole
out-of-fold procedure, including penalty selection.
"""
import json
import os
import random
import sys
import time
from collections import Counter, defaultdict
from itertools import combinations

import numpy as np
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, brier_score_loss, f1_score, log_loss

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyze  # noqa: E402
import run  # noqa: E402
from analyze import fmt, name  # noqa: E402
from residue import analysis as an  # noqa: E402
from residue import readers as rd  # noqa: E402
from residue.embed import Embedder  # noqa: E402
from residue.features import (RarityTable, body, f_set_relational, pair_features, pooled_set_features,  # noqa: E402
                              sentences, text_features)
from residue.fixtures import FIXTURES, HISTORY_TABLE  # noqa: E402
from residue.store import CallStore  # noqa: E402

NPERM = int(sys.argv[1]) if len(sys.argv) > 1 else 30
OUT = analyze.OUT


# ---------- helpers ----------

def oof(X, y, w, fo):
    return an.oof_predict(np.asarray(X, float), np.asarray(y), w, fo)[0]


def perm_null(X, y, w, groups, fo, n, tag, probs_fn=None):
    """Observed AUC and its permutation null. groups give the exchangeable unit."""
    probs_fn = probs_fn or (lambda yy: oof(X, yy, w, fo))
    y = np.asarray(y)
    obs = an.auc(y, probs_fn(y))
    idx = defaultdict(list)
    for i, g in enumerate(groups):
        idx[g].append(i)
    null = []
    for b in range(n):
        rng = random.Random(f"perm|{run.RUN_SEED}|{tag}|{b}")
        yp = y.copy()
        for g, ii in idx.items():
            vals = list(y[ii])
            rng.shuffle(vals)
            yp[ii] = vals
        null.append(an.auc(yp, probs_fn(yp)))
    null = np.array(null)
    return {"auc": obs, "null_mean": float(null.mean()), "null_sd": float(null.std()),
            "null_q95": float(np.quantile(null, 0.95)),
            "p_one_sided": float((np.sum(null >= obs) + 1) / (n + 1)), "n_perm": n}


def metrics(y, P):
    y = np.asarray(y)
    pred = P.argmax(1)
    out = {"accuracy": accuracy_score(y, pred), "balanced_accuracy": balanced_accuracy_score(y, pred),
           "macro_f1": f1_score(y, pred, average="macro"), "log_loss": log_loss(y, P, labels=list(range(P.shape[1])))}
    if P.shape[1] == 2:
        out["brier"] = brier_score_loss(y, P[:, 1])
    else:
        Y = np.eye(P.shape[1])[y]
        out["brier"] = float(np.mean(np.sum((P - Y) ** 2, 1)))
    return {k: float(v) for k, v in out.items()}


def gb_oof(X, y, w, fo):
    """Histogram gradient boosting, learning rate and depth chosen by inner world-grouped CV (build spec 11)."""
    from sklearn.model_selection import GroupKFold
    X, y, w = np.asarray(X, float), np.asarray(y), np.asarray(w)
    fold_of = np.array([fo[x] for x in w])
    P = np.zeros((len(y), len(np.unique(y))))
    grid = [(lr, d) for lr in (0.05, 0.1) for d in (3, None)]
    for f in sorted(set(fold_of)):
        tr, te = fold_of != f, fold_of == f
        best, bp = -1, grid[0]
        for lr, d in grid:
            sc = []
            for a, b in GroupKFold(4).split(X[tr], y[tr], w[tr]):
                m = HistGradientBoostingClassifier(learning_rate=lr, max_depth=d, random_state=0).fit(X[tr][a], y[tr][a])
                sc.append(an.auc(y[tr][b], m.predict_proba(X[tr][b])))
            if np.mean(sc) > best:
                best, bp = np.mean(sc), (lr, d)
        m = HistGradientBoostingClassifier(learning_rate=bp[0], max_depth=bp[1], random_state=0).fit(X[tr], y[tr])
        P[te] = m.predict_proba(X[te])
    return P


def rows1(s1, classes, producer=run.PRIMARY, genre="incident"):
    r = [x for x in s1 if x["producer"] == producer and x["genre"] == genre and x["cond"] in classes]
    return r, np.array([classes.index(x["cond"]) for x in r]), [x["world"] for x in r], [(x["world"], x["rep"]) for x in r]


def named_sources(text, world_sources):
    """The attribution field read against the world's own source names: which
    names the final Sources line contains, and whether anything else is
    listed. Replaces splitting the line on commas, which breaks names that
    contain commas."""
    lines = text.rstrip().splitlines()
    if not lines or not lines[-1].strip().lower().startswith("sources:"):
        return None
    line = lines[-1].strip()[len("sources:"):].strip()
    low = line.lower()
    found = [s for s in sorted(set(world_sources), key=len, reverse=True) if s.lower() in low]
    rest = low
    for s in found:
        rest = rest.replace(s.lower(), " ")
    other = any(c.isalpha() for c in rest.replace(" and ", " "))
    return {"named": found, "other_text": other, "empty": not line}


# ---------- main ----------

def main():
    t0 = time.time()
    worlds, s1, s2, failures = analyze.load()
    wmap = {w.world_id: w for w in worlds}
    fo = analyze.folds()
    embed = Embedder(run.EMBED_CACHE)
    J, L = {}, []
    log = lambda m: print(f"[{time.time() - t0:.0f}s] {m}", flush=True)  # noqa: E731

    # 1. generation-context test: identical requests, early against late in the block
    store = CallStore(os.path.join(analyze.FULL, "calls.jsonl"))
    models = {k: run.Frozen(m) for k, m in run.producers(False, None).items()}
    blocks = [b for b in run.plan(worlds, [0, 1, 2]) if b[0].startswith("S1") and b[1].producer == run.PRIMARY
              and b[1].genre == "incident"]
    res, _, _ = run.run_blocks(blocks, store, models, 16)
    tx, ty, tw, tg = [], [], [], []
    px, py, pw, pg = [], [], [], []
    audit = []
    for bid in sorted(res):
        r = res[bid]
        d0k, nck = r["D0"]["o1"].key, r["NC0"]["o1"].key
        ph = store.records[d0k]["prompt_hash"]
        recs = {}
        for cond, nodes in r.items():
            for n in nodes.values():
                rec = store.records[n.key]
                if n.fn == "observe" and rec["prompt_hash"] == ph:
                    recs[n.key] = rec
        order = sorted(recs.values(), key=lambda x: x["time"])
        rank = {x["key"]: i for i, x in enumerate(order)}
        d0, nc = store.records[d0k], store.records[nck]
        audit.append({"block": bid, "same_request": d0["request_hash"] == nc["request_hash"], "calls": len(order),
                      "rank_d0": rank[d0k], "rank_nc0": rank[nck], "gap_s": nc["time"] - d0["time"],
                      "attempt_d0": d0["attempt"], "attempt_nc0": nc["attempt"],
                      "stop_d0": (d0.get("usage") or {}).get("stop_reason"), "stop_nc0": (nc.get("usage") or {}).get("stop_reason"),
                      "words_d0": len(body(d0["output"]).split()), "words_nc0": len(body(nc["output"]).split())})
        half = len(order) // 2
        for i, rec in enumerate(order):
            if len(order) % 2 and i == half:
                continue
            tx.append(body(rec["output"]))
            ty.append(int(i >= half))
            tw.append(bid.split("|")[1])
            tg.append(bid)
        # pseudo-control: the earliest against the latest of the other identical requests in the block
        others = [x for x in order if x["key"] not in (d0k, nck)]
        if len(others) >= 2:
            for lab, rec in ((0, others[0]), (1, others[-1])):
                px.append(body(rec["output"]))
                py.append(lab)
                pw.append(bid.split("|")[1])
                pg.append(bid)
    XE = np.asarray(embed.many(tx), float)
    PE = np.asarray(embed.many(px), float)
    J["timing"] = {"calls": len(ty), "per_block": len(ty) / len(res),
                   "embedding": perm_null(XE, ty, tw, tg, fo, NPERM, "timing-emb"),
                   "features": perm_null(analyze.text_X(tx), ty, tw, tg, fo, NPERM, "timing-feat"),
                   "pseudo_control_embedding": perm_null(PE, py, pw, pg, fo, NPERM, "pseudo-emb"),
                   "pseudo_control_features": perm_null(analyze.text_X(px), py, pw, pg, fo, NPERM, "pseudo-feat"),
                   "audit": audit}
    log("timing done")

    # 2. permutation nulls for the remaining paired Study 1 contrasts
    contrasts = {"R1|NCR1": ["R1", "NCR1"], "depth": ["R1", "R3", "R5"], "R1|R3": ["R1", "R3"],
                 "partition": ["F1", "F2", "F3"], "access": ["SD-same", "SI-div"],
                 "after 1 relay": ["SD-same+1", "SI-same+1"], "after 3 relays": ["SD-same+3", "SI-same+3"],
                 "composition": ["R5", "SD-same+3"], "composition hub": ["R5", "SI-same+3"],
                 "composition three-way": ["R5", "SD-same+3", "SI-same+3"]}
    J["study1_perm"] = {}
    for k, cl in contrasts.items():
        r, y, w, g = rows1(s1, cl)
        XF = analyze.text_X([x["text"] for x in r])
        XB = embed.many([body(x["text"]) for x in r])
        J["study1_perm"][k] = {"classes": cl, "features": perm_null(XF, y, w, g, fo, NPERM, f"{k}-f"),
                               "embedding": perm_null(XB, y, w, g, fo, NPERM, f"{k}-e")}
        log(f"perm {k}")

    # 3. P2 and depth with secondary metrics and the second learner
    J["metrics"], J["boosting"] = {}, {}
    for k, cl in {"P2": ["SD-same", "SI-same"], "depth": ["R1", "R3", "R5"], "partition": ["F1", "F2", "F3"]}.items():
        r, y, w, g = rows1(s1, cl)
        XF = analyze.text_X([x["text"] for x in r])
        J["metrics"][k] = metrics(y, oof(XF, y, w, fo))
        P = gb_oof(XF, y, w, fo)
        J["boosting"][k] = an.auc_with_ci(y, P[:, 1] if P.shape[1] == 2 else P, w, n=analyze.NBOOT)
    log("metrics and boosting done")

    # 4. H6 for R1 against R3
    J["H6_R1R3"] = {"by_producer": {p: an.auc_with_ci(*(lambda r, y, w, g: (y, oof(analyze.text_X([x["text"] for x in r]), y, w, fo), w))(*rows1(s1, ["R1", "R3"], producer=p)), n=analyze.NBOOT)
                                    for p in run.PRODUCERS},
                    "news": analyze.contrast(s1, ["R1", "R3"], None, fo, genre="news")["features"],
                    "transfer_family": analyze.transfer(s1, ["R1", "R3"], fo, ("family", "A", "B")),
                    "transfer_producer": analyze.transfer(s1, ["R1", "R3"], fo, ("producer", run.PRIMARY, "claude-haiku-5-5")),
                    "transfer_genre": analyze.transfer(s1, ["R1", "R3"], fo, ("genre", "incident", "news"))}
    log("H6 R1R3 done")

    # 5. Study 2: three structures, aggregate of single-message predictions, pairwise same-root (H8, H9)
    def sets_of(producer, access, arm, structures=("IND", "DEP", "MIX")):
        return [r for r in s2 if r["producer"] == producer and r["access"] == access and r["arm"] == arm
                and r["structure"] in structures]

    def set_models(rows, classes):
        y = np.array([classes.index(r["structure"]) for r in rows])
        w = [r["world"] for r in rows]
        fold_of = np.array([fo[x] for x in w])
        pooled = [pooled_set_features(r["texts"]) for r in rows]
        pk = sorted(pooled[0])
        X0 = np.array([[d[k] for k in pk] for d in pooled])
        embed.many([body(t) for r in rows for t in r["texts"]] + [s for r in rows for t in r["texts"] for s in sentences(t)])
        Xr_by = {}
        for f in sorted(set(fold_of)):
            rar = RarityTable([t for r, fv in zip(rows, fold_of) if fv != f for t in r["texts"]])
            rel = [f_set_relational(r["texts"], rar, embed) for r in rows]
            rk = sorted(rel[0])
            Xr_by[f] = np.hstack([X0, np.array([[d[k] for k in rk] for d in rel])])

        def pairwise(yy):
            P = None
            for f, Xr in Xr_by.items():
                pf = an.oof_predict(Xr, yy, w, fo)[0]
                P = pf if P is None else P
                P[fold_of == f] = pf[fold_of == f]
            return P
        return y, w, X0, pairwise

    J["sets"] = {}
    for prod in run.PRODUCERS:
        rows = sets_of(prod, "full", "neutral")
        y, w, X0, pairwise = set_models(rows, ["IND", "DEP", "MIX"])
        P0, Pr = oof(X0, y, w, fo), pairwise(y)
        # aggregate of single messages: a single-message model predicts the set's structure from each message
        single_X = np.array(analyze.text_X([t for r in rows for t in r["texts"]]))
        sy = np.repeat(y, 3)
        sw = [x for x in w for _ in range(3)]
        Ps = oof(single_X, sy, sw, fo).reshape(len(rows), 3, -1).mean(1)
        J["sets"][prod] = {"three_class_pooled": an.auc_with_ci(y, P0, w, n=analyze.NBOOT),
                           "three_class_pairwise": an.auc_with_ci(y, Pr, w, n=analyze.NBOOT),
                           "three_class_aggregate_of_singles": an.auc_with_ci(y, Ps, w, n=analyze.NBOOT),
                           "pairwise_metrics": metrics(y, Pr)}
        log(f"sets {prod}")
    # P3 permutation null, primary producer, full neutral, IND against DEP
    rows = sets_of(run.PRIMARY, "full", "neutral", ("IND", "DEP"))
    y, w, X0, pairwise = set_models(rows, ["IND", "DEP"])
    g = [(r["world"], r["rep"]) for r in rows]
    J["P3_perm"] = {"pooled": perm_null(X0, y, w, g, fo, NPERM, "p3-pooled"),
                    "pairwise": perm_null(None, y, w, g, fo, NPERM, "p3-pair", probs_fn=pairwise)}
    log("P3 permutation done")
    # pairwise same-root labels by access (H8 pairs, H9)
    J["pairs"] = {}
    for access in ("full", "partial"):
        rows = sets_of(run.PRIMARY, access, "neutral")
        same = {"IND": (0, 0, 0), "DEP": (1, 1, 1), "MIX": (1, 0, 0)}  # pairs (1,2), (1,3), (2,3) in generation slots
        fold_of = np.array([fo[r["world"]] for r in rows])
        P = np.zeros(len(rows) * 3)
        y = np.array([v for r in rows for v in same[r["structure"]]])
        pw = [r["world"] for r in rows for _ in range(3)]
        pfold = np.repeat(fold_of, 3)
        for f in sorted(set(fold_of)):
            rar = RarityTable([t for r, fv in zip(rows, fold_of) if fv != f for t in r["texts"]])
            X = np.array([[d[k] for k in sorted(d)] for r in rows
                          for d in (pair_features(a, b, rar, embed) for a, b in combinations(r["texts"], 2))])
            pf = an.oof_predict(X, y, pw, fo)[0][:, 1]
            P[pfold == f] = pf[pfold == f]
        J["pairs"][access] = an.auc_with_ci(y, P, pw, n=analyze.NBOOT)
    log("pairs done")

    # 6. H10: attribution, readers and the pairwise classifier, paired on the same sets
    rr = [json.loads(x) for x in open(os.path.join(analyze.FULL, "reader_calls.jsonl"), encoding="utf-8")]
    rr = [r for r in rr if r.get("final") and r["task"] == rd.SET_TASK]
    rs = {}
    for r in rr:
        _, access, arm, wid, cond = r["item"].split("|")
        rs[(r["reader"], access, arm, wid, cond.split("-")[0])] = rd.config_probs(r["probs"])
    J["H10_readers"] = {}
    for reader in run.READERS:
        for access in ("full", "partial"):
            keys = sorted({(k[3], k[4]) for k in rs if k[0] == reader and k[1] == access and k[4] in ("IND", "DEP")})
            y = np.array([1 if s == "IND" else 0 for _, s in keys])
            w = [k[0] for k in keys]
            sc = {arm: np.array([rs[(reader, access, arm, wid, s)]["IND"] /
                                 max(rs[(reader, access, arm, wid, s)]["IND"] + rs[(reader, access, arm, wid, s)]["DEP"], 1e-9)
                                 for wid, s in keys]) for arm in ("neutral", "stripped", "conceal")}
            d1 = an.paired_delta_auc(y, sc["stripped"], sc["neutral"], w, n=analyze.NBOOT, level=0.90)
            d1["verdict"] = an.three_way(d1["lo"], d1["hi"], -0.05, 0.05)
            d2 = an.paired_delta_auc(y, sc["conceal"], sc["stripped"], w, n=analyze.NBOOT)
            J["H10_readers"][f"{reader}|{access}"] = {"stripped_minus_neutral": d1, "conceal_minus_stripped": d2}
    rows_n = sets_of(run.PRIMARY, "full", "neutral", ("IND", "DEP"))
    rows_s = sets_of(run.PRIMARY, "full", "stripped", ("IND", "DEP"))
    yn, wn, _, pw_n = set_models(rows_n, ["IND", "DEP"])
    ys, ws, _, pw_s = set_models(rows_s, ["IND", "DEP"])
    assert [(r["world"], r["rep"], r["structure"]) for r in rows_n] == [(r["world"], r["rep"], r["structure"]) for r in rows_s]
    dc = an.paired_delta_auc(yn, pw_s(ys)[:, 1], pw_n(yn)[:, 1], wn, n=analyze.NBOOT, level=0.90)
    dc["verdict"] = an.three_way(dc["lo"], dc["hi"], -0.05, 0.05)
    J["H10_classifier"] = dc
    log("H10 done")

    # attribution field, read against each world's source names
    att = defaultdict(lambda: Counter())
    for r in s2:
        if r["arm"] == "stripped":
            continue
        srcs = [p.source for p in wmap[r["world"]].propositions]
        for t in r["texts"]:
            a = att[(r["producer"].split("-")[0], r["access"], r["arm"], r["structure"])]
            ns = named_sources(t, srcs)
            a["messages"] += 1
            if ns is not None:
                a["present"] += 1
                a["names"] += len(ns["named"])
                a["other_text"] += ns["other_text"]
                a["empty"] += ns["empty"]
    J["attribution"] = {"|".join(k): dict(v) for k, v in att.items()}

    # H7 by prompt family, and the worst stratum
    J["H7_family"] = {f"{acc}|{arm}|{a_}|{b_}|{fam}": analyze.single_leak(s2, fo, a_, b_, acc, arm, family=fam)
                      for acc in ("full", "partial") for arm in ("neutral", "conceal") for fam in ("A", "B")
                      for a_, b_ in (("IND", "DEP"), ("IND", "MIX"), ("DEP", "MIX"))}
    J["H7_worst"] = max(J["H7_family"].items(), key=lambda kv: abs(kv[1]["auc"] - 0.5))[0]

    # 7. interactions: message length tertile with P2 and P3
    r, y, w, g = rows1(s1, ["SD-same", "SI-same"])
    P = oof(analyze.text_X([x["text"] for x in r]), y, w, fo)[:, 1]
    ln = np.array([len(body(x["text"]).split()) for x in r])
    cuts = np.quantile(ln, [1 / 3, 2 / 3])
    tert = np.digitize(ln, cuts)
    J["length_P2"] = {int(t): an.auc_with_ci(y[tert == t], P[tert == t], [w[i] for i in np.flatnonzero(tert == t)],
                                             n=analyze.NBOOT) for t in range(3)}
    J["length_P2_cuts"] = cuts.tolist()
    rows = sets_of(run.PRIMARY, "full", "neutral", ("IND", "DEP"))
    y3, w3, X03, pw3 = set_models(rows, ["IND", "DEP"])
    P3r, P30 = pw3(y3)[:, 1], oof(X03, y3, w3, fo)[:, 1]
    ln3 = np.array([np.mean([len(body(t).split()) for t in x["texts"]]) for x in rows])
    c3 = np.quantile(ln3, [1 / 3, 2 / 3])
    t3 = np.digitize(ln3, c3)
    J["length_P3"] = {int(t): an.paired_delta_auc(y3[t3 == t], P3r[t3 == t], P30[t3 == t],
                                                  [w3[i] for i in np.flatnonzero(t3 == t)], n=analyze.NBOOT)
                      for t in range(3)}
    J["length_P3_cuts"] = c3.tolist()
    log("interactions done")

    # 8. observer diversity and hub-against-diamond discriminability, by world
    by_w = defaultdict(list)
    for i, x in enumerate(r):
        by_w[x["world"]].append(i)
    div, disc = [], []
    for wid, ii in sorted(by_w.items()):
        yy, pp = y[ii], P[ii]
        if len(set(yy)) < 2:
            continue
        si = [res[b]["SI-same"] for b in res if b.split("|")[1] == wid and "SI-same" in res[b]]
        cos = []
        for nodes in si:
            v = embed.many([body(nodes[o].text) for o in ("o1", "o2", "o3")])
            v = [np.array(a) / np.linalg.norm(a) for a in v]
            cos += [float(v[a] @ v[b]) for a, b in combinations(range(3), 2)]
        div.append(1 - np.mean(cos))
        disc.append(an.auc(yy, pp))
    rho = spearmanr(div, disc)
    J["diversity"] = {"worlds": len(div), "spearman": float(rho.correlation), "p": float(rho.pvalue),
                      "mean_diversity": float(np.mean(div))}

    # 9. copying: depth discriminability by how many of R5's rewrites changed the text
    r, y, w, g = rows1(s1, ["R1", "R5"])
    P = oof(analyze.text_X([x["text"] for x in r]), y, w, fo)[:, 1]
    changed = {}
    for b in res:
        if "R5" in res[b]:
            n = res[b]["R5"]
            ch = ["o1", "r1", "r2", "r3", "r4", "r5"]
            changed[(b.split("|")[1], int(b.split("|")[2]))] = sum(n[a].text.strip() != n[c].text.strip() for a, c in zip(ch, ch[1:]))
    strata = {}
    for k in sorted(set(changed.values())):
        keep = [i for i, x in enumerate(r) if changed.get((x["world"], x["rep"])) == k]
        if len({int(y[i]) for i in keep}) == 2 and len(keep) >= 20:
            strata[k] = {"pairs": len(keep) // 2, **an.auc_with_ci(y[keep], P[keep], [w[i] for i in keep], n=analyze.NBOOT)}
    J["copying_R1_R5"] = {"distribution": dict(Counter(changed.values())), "by_changed": strata}

    # 10. structure predictor: 13 histories from one message (Part V-A)
    conds = [c for c in HISTORY_TABLE if c != "SD-div"]
    hist = sorted(set(HISTORY_TABLE[c] for c in conds), key=str)
    names = ["synthesis", "inputs", "roots", "rewrites_before", "rewrites_after"]
    J["predictor"] = {"histories": [list(map(str, h)) for h in hist]}
    for prod in run.PRODUCERS:
        r = [x for x in s1 if x["producer"] == prod and x["genre"] == "incident" and x["cond"] in conds]
        y = np.array([hist.index(HISTORY_TABLE[x["cond"]]) for x in r])
        w = [x["world"] for x in r]
        XF = np.asarray(analyze.text_X([x["text"] for x in r]), float)
        learners = {"features": lambda: oof(XF, y, w, fo)}
        if prod == run.PRIMARY:
            XB = np.asarray(embed.many([body(x["text"]) for x in r]), float)
            learners["embedding"] = lambda: oof(XB, y, w, fo)
            learners["boosting"] = lambda: gb_oof(XF, y, w, fo)
        out = {"majority_baseline": float(Counter(y).most_common(1)[0][1] / len(y)), "n": len(y)}
        for lname, fn in learners.items():
            P = fn()
            cm = np.zeros((len(hist), len(hist)), int)
            for a_, b_ in zip(y, P.argmax(1)):
                cm[a_, b_] += 1
            attr = {}
            for j, nm in enumerate(names):
                vals = sorted({h[j] for h in hist}, key=str)
                ya = np.array([vals.index(hist[k][j]) for k in y])
                Pa = np.stack([P[:, [i for i, h in enumerate(hist) if h[j] == v]].sum(1) for v in vals], 1)
                attr[nm] = an.auc_with_ci(ya, Pa[:, 1] if len(vals) == 2 else Pa, w, n=analyze.NBOOT)
            by_type = {}
            for et in sorted({wmap[x].event_type for x in w}):
                ii = [i for i, x in enumerate(w) if wmap[x].event_type == et]
                by_type[et] = float(np.mean(P[ii].argmax(1) == y[ii]))
            out[lname] = {"macro_auc": an.auc_with_ci(y, P, w, n=analyze.NBOOT), **metrics(y, P),
                          "recall_by_history": [float(cm[i, i] / cm[i].sum()) if cm[i].sum() else 0.0 for i in range(len(hist))],
                          "confusion": cm.tolist(), "attributes": attr, "accuracy_by_event_type": by_type}
        J["predictor"][prod] = out
    # five-configuration set predictor: structure from the set model, odd position from a pair model
    rows = sets_of(run.PRIMARY, "full", "neutral")
    y3, w3, X03, pw3 = set_models(rows, ["IND", "DEP", "MIX"])
    Ps = pw3(y3)
    fold_of = np.array([fo[r["world"]] for r in rows])
    same = {"IND": (0, 0, 0), "DEP": (1, 1, 1), "MIX": (1, 0, 0)}
    yp = np.array([v for r in rows for v in same[r["structure"]]])
    pwld = [r["world"] for r in rows for _ in range(3)]
    Pp = np.zeros(len(yp))
    pfold = np.repeat(fold_of, 3)
    for f in sorted(set(fold_of)):
        rar = RarityTable([t for r, fv in zip(rows, fold_of) if fv != f for t in r["texts"]])
        X = np.array([[d[k] for k in sorted(d)] for r in rows
                      for d in (pair_features(a_, b_, rar, embed) for a_, b_ in combinations(r["texts"], 2))])
        pf = an.oof_predict(X, yp, pwld, fo)[0][:, 1]
        Pp[pfold == f] = pf[pfold == f]
    Pp = Pp.reshape(len(rows), 3)  # pairs (1,2), (1,3), (2,3) in generation slots
    # odd message k is the one outside the most likely same-root pair: pair (2,3) -> odd 1, (1,3) -> 2, (1,2) -> 3
    q = Pp[:, [2, 1, 0]]
    q = q / q.sum(1, keepdims=True)
    cfg = np.column_stack([Ps[:, 0], Ps[:, 1], Ps[:, 2:3] * q])  # IND, DEP, MIX odd at slot 1, 2, 3
    truth = np.array([0 if r["structure"] == "IND" else 1 if r["structure"] == "DEP" else 4 for r in rows])
    J["set_predictor"] = {"configurations": ["IND", "DEP", "MIX odd 1", "MIX odd 2", "MIX odd 3"],
                          "accuracy": float(np.mean(cfg.argmax(1) == truth)),
                          "mix_odd_correct": float(np.mean(cfg[truth == 4, 2:].argmax(1) == 2)),
                          "same_root_auc": an.auc_with_ci(yp, np.column_stack([cfg[:, 1] + cfg[:, 4], cfg[:, 1] + cfg[:, 3],
                                                                               cfg[:, 1] + cfg[:, 2]]).ravel(), pwld, n=analyze.NBOOT)}
    log("predictor done")

    with open(os.path.join(OUT, "secondary.json"), "w") as fh:
        json.dump(J, fh, indent=1, default=float)

    # ---------- report ----------
    def pn(x):
        return f"{x['auc']:.3f} (null {x['null_mean']:.3f}, SD {x['null_sd']:.3f}, p {x['p_one_sided']:.3f})"

    tm = J["timing"]
    L += ["# Secondary text-only analyses, full run", "",
          f"Generated by `analyze_secondary.py` at {time.strftime('%Y-%m-%d %H:%M')}. Same rows, folds, and learners as "
          f"`text_only.md`. Permutation nulls use {NPERM} permutations within each world and replicate and rerun the whole "
          "out-of-fold procedure, so a one-sided p cannot fall below "
          f"{1 / (NPERM + 1):.3f}. No result here uses the matcher.", "",
          "## Generation context", "",
          f"Among calls with byte-identical requests in the same block (the shared direct-report observation, the "
          f"dead-end control's three observations, and the hub's other observers, {tm['per_block']:.1f} per block, "
          f"{tm['calls']} in all), can a model tell the earlier half from the later half? Embedding learner: "
          f"{pn(tm['embedding'])}. Feature learner: {pn(tm['features'])}.", "",
          "Pseudo-control: in each block, the earliest against the latest of the identical requests other than the direct "
          f"report's and its control's own. Embedding learner: {pn(tm['pseudo_control_embedding'])}. Feature learner: "
          f"{pn(tm['pseudo_control_features'])}.", "",
          "Audit of the 180 direct-report and control pairs: "
          f"identical request hash in {sum(a['same_request'] for a in tm['audit'])}; "
          f"accepted on the first attempt in {sum(a['attempt_d0'] == 0 and a['attempt_nc0'] == 0 for a in tm['audit'])}; "
          f"stop reasons {dict(Counter((a['stop_d0'], a['stop_nc0']) for a in tm['audit']))}; "
          f"control generated later in {sum(a['gap_s'] > 0 for a in tm['audit'])}, median gap "
          f"{np.median([a['gap_s'] for a in tm['audit']]):.0f} s; direct report first among the block's identical requests "
          f"in {sum(a['rank_d0'] == 0 for a in tm['audit'])}; mean words {np.mean([a['words_d0'] for a in tm['audit']]):.1f} "
          f"against {np.mean([a['words_nc0'] for a in tm['audit']]):.1f}.", "",
          "## Permutation nulls, Study 1, primary producer", "",
          "| Contrast | Features | Embedding |", "|---|---|---|"]
    for k, v in J["study1_perm"].items():
        L.append(f"| {k}: {' against '.join(name(c) for c in v['classes'])} | {pn(v['features'])} | {pn(v['embedding'])} |")
    L += ["", "## Secondary metrics and the second learner", "", "| Contrast | Accuracy | Balanced accuracy | Macro-F1 | Brier | Log loss | Boosting AUC [95%] |",
          "|---|---|---|---|---|---|---|"]
    for k, m in J["metrics"].items():
        L.append(f"| {k} | {m['accuracy']:.3f} | {m['balanced_accuracy']:.3f} | {m['macro_f1']:.3f} | {m['brier']:.3f} | "
                 f"{m['log_loss']:.3f} | {fmt(J['boosting'][k])} |")
    h = J["H6_R1R3"]
    L += ["", "## Transfer of chain of 1 relay against chain of 3 relays (H6)", "", "| Setting | Features AUC [95%] |", "|---|---|"]
    for p, x in h["by_producer"].items():
        L.append(f"| producer {p} | {fmt(x)} |")
    L.append(f"| news genre, primary producer | {fmt(h['news'])} |")
    for k in ("transfer_family", "transfer_producer", "transfer_genre"):
        L.append(f"| {k.replace('_', ' ')}: same | {fmt(h[k]['same'])} |")
        L.append(f"| {k.replace('_', ' ')}: transferred | {fmt(h[k]['transfer'])} |")
    L += ["", "## Sets: three structures (H8)", "",
          "Full access, neutral attribution. Macro one-versus-one AUC over three unconnected sources, out-star, and Y.", "",
          "| Producer | Pooled baseline | Pairwise model | Aggregate of single-message predictions |", "|---|---|---|---|"]
    for p, x in J["sets"].items():
        L.append(f"| {p} | {fmt(x['three_class_pooled'])} | {fmt(x['three_class_pairwise'])} | "
                 f"{fmt(x['three_class_aggregate_of_singles'])} |")
    p3 = J["P3_perm"]
    L += ["", f"Structural association (IND against DEP, primary producer), each model tested separately against label "
          f"exchange: pooled {pn(p3['pooled'])}, pairwise {pn(p3['pairwise'])}. These are not tests of the gain, which is "
          "in `inference.md`.", "",
          f"Five-configuration set predictor (structure from the pairwise set model, odd position from a pair model): "
          f"configuration accuracy {J['set_predictor']['accuracy']:.3f}; among Y sets, the odd message identified in "
          f"{J['set_predictor']['mix_odd_correct']:.0%}; same-root AUC from the configuration probabilities "
          f"{fmt(J['set_predictor']['same_root_auc'])}.", "",
          "## Pairwise same-root detection (H8 pairs, H9)", "",
          f"Each pair of messages in a set labeled by whether the two share a root, from the three pairwise features. Full "
          f"access {fmt(J['pairs']['full'])}. Partial access {fmt(J['pairs']['partial'])}, where shared packages contribute "
          "by construction.", "",
          "## Attribution (H10)", "",
          "Paired change in IND-against-DEP AUC on the same sets. Stripping is judged by the three-way rule at plus or minus "
          "0.05 with 90% intervals.", "", "| Model | Access | Stripped minus neutral [90%] | Verdict | Concealed minus stripped [95%] |",
          "|---|---|---|---|---|"]
    for k, v in J["H10_readers"].items():
        reader, access = k.split("|")
        a, b = v["stripped_minus_neutral"], v["conceal_minus_stripped"]
        L.append(f"| {reader} | {access} | {a['delta']:.3f} [{a['lo']:.3f}, {a['hi']:.3f}] | {a['verdict']} | "
                 f"{b['delta']:.3f} [{b['lo']:.3f}, {b['hi']:.3f}] |")
    c = J["H10_classifier"]
    L += [f"| pairwise classifier | full | {c['delta']:.3f} [{c['lo']:.3f}, {c['hi']:.3f}] | {c['verdict']} | |", "",
          "Attribution field by producer, access, arm, and structure, read against each world's source names (messages, "
          "share with the line, mean names listed, share listing anything that is not a world source name):", "",
          "| Producer | Access | Arm | Structure | Messages | Line present | Mean names | Other text |", "|---|---|---|---|---|---|---|---|"]
    for k, v in sorted(J["attribution"].items()):
        p, acc, arm, st = k.split("|")
        pres = v.get("present", 0)
        L.append(f"| {p} | {acc} | {arm} | {name(st)} | {v['messages']} | {pres / v['messages']:.0%} | "
                 f"{(v.get('names', 0) / pres if pres else 0):.1f} | {(v.get('other_text', 0) / pres if pres else 0):.0%} |")
    L += ["", "## Single-message leakage by prompt family (H7)", "",
          "One randomly chosen message per set, 90% intervals, tolerance 0.43 to 0.57. Stripped sets are omitted, because "
          "their text features equal the neutral sets' apart from a Sources indicator that is constant within the arm.", "",
          "| Access, arm, pair, family | AUC [90%] | Verdict |", "|---|---|---|"]
    for k, x in J["H7_family"].items():
        acc, arm, a_, b_, fam = k.split("|")
        L.append(f"| {acc}, {arm}, {name(a_)} against {name(b_)}, family {fam} | {fmt(x)} | {x['verdict']} |")
    L += ["", f"Stratum furthest from chance: {J['H7_worst'].replace('|', ', ')}. AUC below 0.5 is a reversed "
          "ranking under the fixed label orientation, not evidence of no information.", "",
          "## Message length", "",
          f"Hub against diamond by length tertile (cuts at {J['length_P2_cuts'][0]:.0f} and {J['length_P2_cuts'][1]:.0f} words): "
          + ", ".join(f"tertile {t + 1} {fmt(v)}" for t, v in J["length_P2"].items()) + ".",
          f"P3 gain by mean set length tertile (cuts at {J['length_P3_cuts'][0]:.0f} and {J['length_P3_cuts'][1]:.0f} words): "
          + ", ".join(f"tertile {t + 1} {v['delta']:.3f} [{v['lo']:.3f}, {v['hi']:.3f}]" for t, v in J["length_P3"].items()) + ".", "",
          "## Observer diversity", "",
          f"Across {J['diversity']['worlds']} worlds, the Spearman correlation between the hub's observer diversity (one "
          f"minus mean pairwise embedding cosine, mean {J['diversity']['mean_diversity']:.3f}) and the world's hub-against-"
          f"diamond AUC is {J['diversity']['spearman']:.3f} (p {J['diversity']['p']:.3f}). Each world's AUC rests on three "
          "replicates, so it is noisy.", "",
          "## Copying and depth", "",
          "Rewrites in each chain of 5 relays that changed the text: " + ", ".join(
              f"{k} changed in {v} chains" for k, v in sorted(J["copying_R1_R5"]["distribution"].items())) + ". "
          "Chain of 1 relay against chain of 5 relays, by that count: " + (", ".join(
              f"{k} changed {fmt(v)} ({v['pairs']} pairs)" for k, v in J["copying_R1_R5"]["by_changed"].items()) or "too few")
          + ". The count is realized, not assigned, so this is descriptive.", "",
          "## Structure predictor, single message (Part V-A)", "",
          "Thirteen histories, incident genre. Accuracy is compared with the majority-class rate, because D0 and NC0, R1 "
          "and NCR1, and SI-same and SI-div share histories. Brier is the multiclass Brier score.", "",
          "| Producer | Learner | Macro AUC [95%] | Accuracy | Majority baseline | Balanced accuracy | Brier | Log loss |",
          "|---|---|---|---|---|---|---|---|"]
    for prod in run.PRODUCERS:
        pr = J["predictor"][prod]
        for lname in ("features", "embedding", "boosting"):
            if lname in pr:
                v = pr[lname]
                L.append(f"| {prod} | {lname} | {fmt(v['macro_auc'])} | {v['accuracy']:.3f} | {pr['majority_baseline']:.3f} | "
                         f"{v['balanced_accuracy']:.3f} | {v['brier']:.3f} | {v['log_loss']:.3f} |")
    pf = J["predictor"][run.PRIMARY]["features"]
    L += ["", "Attribute AUCs from the history probabilities, primary producer, feature learner: "
          + ", ".join(f"{k} {fmt(v)}" for k, v in pf["attributes"].items()) + ".", "",
          "Recall by history, primary producer, feature learner: " + ", ".join(
              f"{', '.join(J['predictor']['histories'][i])}: {r_:.2f}" for i, r_ in enumerate(pf["recall_by_history"])) + ".", "",
          "Accuracy by event type, primary producer, feature learner (about four worlds each): " + ", ".join(
              f"{k} {v:.2f}" for k, v in pf["accuracy_by_event_type"].items()) + ".", "",
          "Confusion matrix, primary producer, feature learner (rows true history, columns predicted; histories are "
          "(synthesis, inputs, roots, rewrites before, rewrites after)):", "",
          "| | " + " | ".join(str(i) for i in range(len(hist))) + " |", "|---|" + "---|" * len(hist)]
    for i, row in enumerate(pf["confusion"]):
        L.append(f"| {i}: {', '.join(J['predictor']['histories'][i])} | " + " | ".join(str(v) for v in row) + " |")
    L += ["", f"Run time {time.time() - t0:.0f} s.", ""]
    with open(os.path.join(OUT, "secondary.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("wrote", os.path.join(OUT, "secondary.md"))


if __name__ == "__main__":
    main()

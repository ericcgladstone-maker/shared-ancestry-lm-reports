"""Text-only analyses of the full run (design Parts V and VIII).

    python analyze.py

Reads runs/full/calls.jsonl and runs/full/reader_calls.jsonl, makes no
model calls, and writes runs/full/analysis/text_only.md and .json. Every
model here sees message text only: the formal and attributional feature
families (the specification without propositional features), and, as a
second learner, the message's embedding. The matcher is not used.

Structures are named by shape, with condition codes as secondary labels.
"""
import json
import os
import sys
import time
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run  # noqa: E402
from residue import analysis as an  # noqa: E402
from residue import readers as rd  # noqa: E402
from residue.embed import Embedder  # noqa: E402
from residue.features import RarityTable, body, f_set_relational, pooled_set_features, sentences, text_features  # noqa: E402
from residue.fixtures import FIXTURES  # noqa: E402
from residue.store import CallStore  # noqa: E402

FULL = os.path.join(HERE, "runs", "full")
OUT = os.path.join(FULL, "analysis")
NBOOT = 2000
SHAPE = {
    "D0": "direct report", "NC0": "direct report with dead-end branches",
    "R1": "chain of 1 relay", "NCR1": "chain of 1 relay with dead-end branches",
    "R3": "chain of 3 relays", "R5": "chain of 5 relays",
    "F1": "hub with 1 spoke", "F2": "hub with 2 split-access spokes", "F3": "hub with 3 split-access spokes",
    "SI-same": "hub", "SD-same": "diamond", "SD-div": "diamond (identical to SD-same)", "SI-div": "hub with overlapping access",
    "SI-same+1": "hub then 1 relay", "SD-same+1": "diamond then 1 relay",
    "SI-same+3": "hub then 3 relays", "SD-same+3": "diamond then 3 relays",
    "IND": "three unconnected sources", "DEP": "out-star", "MIX": "Y",
}


def name(c):
    return f"{SHAPE[c]} ({c})"


def load():
    worlds = run.load_worlds("full")
    store = CallStore(os.path.join(FULL, "calls.jsonl"))
    models = {k: run.Frozen(m) for k, m in run.producers(False, None).items()}
    results, failures, errors = run.run_blocks(run.plan(worlds, [0, 1, 2]), store, models, 16)
    assert not errors, errors
    fam = run.families(worlds, [0, 1, 2])
    s1, s2 = [], []
    for bid, res in results.items():
        study, wid, rep, genre, prod = bid.split("|")
        rep = int(rep)
        f = fam[(wid, rep)]
        for cond, nodes in res.items():
            terms = [nodes[t].text for t in FIXTURES[cond]["terminals"]]
            if study == "S1":
                s1.append(dict(world=wid, rep=rep, genre=genre, producer=prod, family=f, cond=cond, text=terms[0]))
            else:
                st, access, instr = cond.split("-")
                # the facts each message could carry: the package of the observation it descends from
                pk = [list(nodes[nodes[t].parents[0]].package) for t in FIXTURES[cond]["terminals"]]
                s2.append(dict(world=wid, rep=rep, producer=prod, family=f, structure=st, access=access, arm=instr,
                               texts=terms, packages=pk))
                if instr == "neutral" and prod == run.PRIMARY:
                    s2.append(dict(world=wid, rep=rep, producer=prod, family=f, structure=st, access=access,
                                   arm="stripped", texts=[run.strip_sources(t)[0] for t in terms], packages=pk))
    # blocks finish in arbitrary order, and row order changes how GroupKFold forms inner folds and which message
    # H7 draws, so rows are put in a fixed order before any model sees them
    s1.sort(key=lambda r: (r["world"], r["rep"], r["genre"], r["producer"], r["cond"]))
    s2.sort(key=lambda r: (r["world"], r["rep"], r["producer"], r["access"], r["arm"], r["structure"]))
    return worlds, s1, s2, failures


def folds():
    return json.load(open(os.path.join(HERE, "worlds", "assignment.json")))["folds"]


def fit(X, y, w, fo, level=0.95):
    probs, Cs = an.oof_predict(np.asarray(X, float), np.asarray(y), w, fo)
    res = an.auc_with_ci(y, probs, w, n=NBOOT, level=level)
    res["penalties"] = Cs
    res["n"] = len(y)
    return res, probs


def text_X(texts):
    feats = [text_features(t) for t in texts]
    keys = sorted(feats[0])
    return [[d[k] for k in keys] for d in feats]


def contrast(s1, classes, embed, fo, producer=run.PRIMARY, genre="incident", level=0.95, family=None):
    rows = [r for r in s1 if r["producer"] == producer and r["genre"] == genre and r["cond"] in classes
            and (family is None or r["family"] == family)]
    y = np.array([classes.index(r["cond"]) for r in rows])
    w = [r["world"] for r in rows]
    out = {}
    out["features"], _ = fit(text_X([r["text"] for r in rows]), y, w, fo, level)
    if embed is not None:
        out["embedding"], _ = fit(embed.many([body(r["text"]) for r in rows]), y, w, fo, level)
    return out


def transfer(s1, classes, fo, split):
    """Train on one value of a factor and test on another without retraining,
    world-grouped: the model for a test fold is trained on the other folds'
    worlds only. split is (key, train value, test value)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    key, a, b = split
    rows = [r for r in s1 if r["cond"] in classes]
    base = {"producer": run.PRIMARY, "genre": "incident"}
    tr_rows = [r for r in rows if r[key] == a and all(r[k] == v for k, v in base.items() if k != key)]
    te_rows = [r for r in rows if r[key] == b and all(r[k] == v for k, v in base.items() if k != key)]
    out = {}
    for label, test in (("same", tr_rows), ("transfer", te_rows)):
        ys, ps, ws = [], [], []
        for f in sorted(set(fo.values())):
            tr = [r for r in tr_rows if fo[r["world"]] != f]
            te = [r for r in test if fo[r["world"]] == f]
            if not te:
                continue
            m = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000))
            m.fit(text_X([r["text"] for r in tr]), [classes.index(r["cond"]) for r in tr])
            ps += list(m.predict_proba(text_X([r["text"] for r in te]))[:, 1])
            ys += [classes.index(r["cond"]) for r in te]
            ws += [r["world"] for r in te]
        out[label] = an.auc_with_ci(np.array(ys), np.array(ps), ws, n=NBOOT)
        out[label].update(rows=len(ys), worlds=len(set(ws)))
    out["shared_worlds"] = len({r["world"] for r in tr_rows} & {r["world"] for r in te_rows})
    return out


def set_contrast(s2, embed, fo, producer=run.PRIMARY, access="full", arm="neutral"):
    """P3: IND against DEP. A_0 pools each message's features; A_r adds the
    pairwise relational features, whose rare-n-gram table is learned on each
    outer fold's training worlds only."""
    rows = [r for r in s2 if r["producer"] == producer and r["access"] == access and r["arm"] == arm
            and r["structure"] in ("IND", "DEP")]
    y = np.array([1 if r["structure"] == "IND" else 0 for r in rows])
    w = [r["world"] for r in rows]
    fold_of = np.array([fo[x] for x in w])
    pooled = [pooled_set_features(r["texts"]) for r in rows]
    pk = sorted(pooled[0])
    X0 = np.array([[d[k] for k in pk] for d in pooled])
    p0, _ = an.oof_predict(X0, y, w, fo)
    embed.many([body(t) for r in rows for t in r["texts"]] + [s for r in rows for t in r["texts"] for s in sentences(t)])
    pr = np.zeros_like(p0)
    for f in sorted(set(fold_of)):
        rar = RarityTable([t for r, fv in zip(rows, fold_of) if fv != f for t in r["texts"]])
        rel = [f_set_relational(r["texts"], rar, embed) for r in rows]
        rk = sorted(rel[0])
        Xr = np.hstack([X0, np.array([[d[k] for k in rk] for d in rel])])
        pf, _ = an.oof_predict(Xr, y, w, fo)
        pr[fold_of == f] = pf[fold_of == f]
    return {"pooled": an.auc_with_ci(y, p0, w, n=NBOOT), "pairwise": an.auc_with_ci(y, pr, w, n=NBOOT),
            "delta": an.paired_delta_auc(y, pr, p0, w, n=NBOOT), "n": len(y)}


def single_leak(s2, fo, a, b, access, arm, producer=run.PRIMARY, family=None):
    """H7: one randomly chosen message per set."""
    import random
    rows = [r for r in s2 if r["producer"] == producer and r["access"] == access and r["arm"] == arm
            and r["structure"] in (a, b) and (family is None or r["family"] == family)]
    rng = random.Random(f"h7|{run.RUN_SEED}")
    texts = [r["texts"][rng.randrange(3)] for r in rows]
    y = np.array([0 if r["structure"] == a else 1 for r in rows])
    w = [r["world"] for r in rows]
    res, _ = fit(text_X(texts), y, w, fo, level=0.90)
    res["verdict"] = an.three_way(res["lo"], res["hi"], 0.43, 0.57)
    return res


def reader_results():
    rows = [json.loads(l) for l in open(os.path.join(FULL, "reader_calls.jsonl"), encoding="utf-8")]
    rows = [r for r in rows if r.get("final")]
    out = {}
    by = defaultdict(list)
    for r in rows:
        parts = r["item"].split("|")
        key = (r["reader"], "|".join(parts[:2]) if r["task"] != rd.SET_TASK else "|".join(parts[:3]))
        by[key].append(r)
    for (reader, task), rs in sorted(by.items()):
        w = [r["item"].split("|")[-2] for r in rs]
        if rs[0]["task"] == rd.SET_TASK:
            cp = [rd.config_probs(r["probs"]) for r in rs]
            truth = [r["truth"][:3] for r in rs]
            sel = [i for i, t in enumerate(truth) if t in ("IND", "DEP")]
            y = np.array([1 if truth[i] == "IND" else 0 for i in sel])
            s = np.array([cp[i]["IND"] / max(cp[i]["IND"] + cp[i]["DEP"], 1e-9) for i in sel])
            res = an.auc_with_ci(y, s, [w[i] for i in sel], n=NBOOT)
            classes = ["IND", "DEP", "MIX"]
            y3 = np.array([classes.index(t) for t in truth])
            P3 = np.array([[c[k] for k in classes] for c in cp])
            res3 = an.auc_with_ci(y3, P3, w, n=NBOOT)
            out[f"{reader}|{task}"] = {"IND_vs_DEP": res, "three_class": res3, "n": len(rs)}
        else:
            conds = [c for c, _ in rd.TASKS[rs[0]["task"]]]
            y = np.array([conds.index(r["truth"]) for r in rs])
            P = np.array([r["probs"] for r in rs])
            res = an.auc_with_ci(y, P[:, 1] if len(conds) == 2 else P, w, n=NBOOT)
            res["n"] = len(rs)
            res["uniform"] = sum(1 for r in rs if not r["valid"])
            out[f"{reader}|{task}"] = res
    return out


def fmt(r):
    return f"{r['auc']:.3f} [{r['lo']:.3f}, {r['hi']:.3f}]"


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    worlds, s1, s2, failures = load()
    fo = folds()
    embed = Embedder(run.EMBED_CACHE)
    J, L = {}, []
    print(f"loaded {len(s1)} Study 1 messages and {len(s2)} Study 2 sets", flush=True)

    # P1: dead-end branches (90% intervals, three-way rule)
    J["P1"] = {}
    for a, b in (("D0", "NC0"), ("R1", "NCR1")):
        r = contrast(s1, [a, b], embed, fo, level=0.90)
        for k in r:
            r[k]["verdict"] = an.three_way(r[k]["lo"], r[k]["hi"], 0.43, 0.57)
        J["P1"][f"{a}|{b}"] = r
    print("P1 done", flush=True)
    # P2: hub against diamond
    J["P2"] = contrast(s1, ["SD-same", "SI-same"], embed, fo)
    print("P2 done", flush=True)
    # P3: relational gain in sets
    J["P3"] = set_contrast(s2, embed, fo)
    print("P3 done", flush=True)
    J["holm"] = an.holm({"P2": J["P2"]["features"]["p_gt_chance"], "P3": J["P3"]["delta"]["p_gt_zero"]})

    # secondary Study 1 contrasts, primary producer, incident genre
    sec = {"depth": ["R1", "R3", "R5"], "partition": ["F1", "F2", "F3"], "access": ["SD-same", "SI-div"],
           "after 1 relay": ["SD-same+1", "SI-same+1"], "after 3 relays": ["SD-same+3", "SI-same+3"],
           "composition": ["R5", "SD-same+3"]}
    J["secondary"] = {k: contrast(s1, v, embed, fo) for k, v in sec.items()}
    print("secondary done", flush=True)
    # H6: hub against diamond under the other producers and genre, and transfers
    J["H6"] = {"by_producer": {p: contrast(s1, ["SD-same", "SI-same"], None, fo, producer=p)["features"]
                               for p in run.PRODUCERS},
               "news": contrast(s1, ["SD-same", "SI-same"], None, fo, genre="news")["features"],
               "transfer_family": transfer(s1, ["SD-same", "SI-same"], fo, ("family", "A", "B")),
               "transfer_producer": transfer(s1, ["SD-same", "SI-same"], fo, ("producer", run.PRIMARY, "claude-haiku-5-5")),
               "transfer_genre": transfer(s1, ["SD-same", "SI-same"], fo, ("genre", "incident", "news"))}
    print("H6 done", flush=True)
    # H7: single-message leakage in Study 2
    J["H7"] = {f"{acc}|{arm}|{a}|{b}": single_leak(s2, fo, a, b, acc, arm)
               for acc in ("full", "partial") for arm in ("neutral", "conceal", "stripped")
               for a, b in (("IND", "DEP"), ("IND", "MIX"), ("DEP", "MIX"))}
    # P3 under the other producers and the partial arm
    J["P3_other"] = {p: set_contrast(s2, embed, fo, producer=p) for p in run.PRODUCERS[1:]}
    J["P3_partial"] = set_contrast(s2, embed, fo, access="partial")
    print("H7 and P3 variants done", flush=True)
    J["readers"] = reader_results()
    J["failures"] = failures

    with open(os.path.join(OUT, "text_only.json"), "w") as fh:
        json.dump(J, fh, indent=1, default=float)

    # report
    L += ["# Text-only results, full run", "",
          f"Generated by `analyze.py` at {time.strftime('%Y-%m-%d %H:%M')} from `runs/full/`. Sixty worlds, three "
          "replicates, outer five-fold cross-validation grouped by world (folds fixed in `worlds/assignment.json`), "
          "penalty chosen by inner four-fold world-grouped cross-validation, intervals from 2,000 world-cluster "
          "bootstrap draws on fixed out-of-fold predictions. Unless noted, the producer is the primary producer, "
          f"{run.PRIMARY}, and the genre is the incident report. Features are the formal and attributional families "
          "only, and the second learner uses the message's embedding. No result here uses the matcher. AUC is the "
          "probability that the model ranks a random message of one class above a random message of the other, so "
          "0.5 is chance.", "",
          "## P1: dead-end branches", "",
          "Structures that differ only in branches that never reach the observed message. AUC with two-sided 90% "
          "intervals, judged against the stipulated tolerance of 0.43 to 0.57.", "",
          "| Contrast | Learner | AUC [90% interval] | Verdict |", "|---|---|---|---|"]
    for k, r in J["P1"].items():
        a, b = k.split("|")
        for lrn, x in r.items():
            L.append(f"| {name(a)} against {name(b)} | {lrn} | {fmt(x)} | {x['verdict']} |")
    p2, p3 = J["P2"], J["P3"]
    L += ["", "## P2: hub against diamond", "",
          "One terminal message. Hub: three independent observers, each relayed once, combined. Diamond: one "
          "observation relayed three ways and combined. All observers see the full record.", "",
          "| Learner | AUC [95% interval] | One-sided p |", "|---|---|---|"]
    for lrn, x in p2.items():
        L.append(f"| {lrn} | {fmt(x)} | {x['p_gt_chance']:.4f} |")
    L += ["", "## P3: relations among three messages", "",
          "Sets of three messages, full access, neutral attribution. Three unconnected sources (IND) against an "
          "out-star (DEP). The pooled baseline pools each message's features. The pairwise model adds rare "
          "word-sequence overlap, sentence-order similarity, and embedding similarity between messages.", "",
          f"Pooled baseline AUC {fmt(p3['pooled'])}. Pairwise model AUC {fmt(p3['pairwise'])}. Gain "
          f"{p3['delta']['delta']:.3f} [{p3['delta']['lo']:.3f}, {p3['delta']['hi']:.3f}], one-sided p "
          + (f"{p3['delta']['p_gt_zero']:.4f}" if p3['delta']['p_gt_zero'] > 0 else "< 0.0005 (no draw of 2,000 at or beyond)")
          + f". Sets: {p3['n']}.", "",
          "Intervals and p-values in this report come from the world bootstrap on fixed out-of-fold predictions, the "
          "conditional estimand of design Part VIII: held-out performance of the fitted fold models on these worlds. "
          "They leave out retraining variability. Inference on P1, P2, and P3, and the Holm family, is in "
          "`inference.md`, from refitted label-exchangeability permutations (P1, P2) and a refitted world bootstrap "
          "of the paired gain (P3).", "",
          "## Secondary Study 1 contrasts", "", "| Contrast | Features AUC [95%] | Embedding AUC [95%] |", "|---|---|---|"]
    for k, r in J["secondary"].items():
        cl = sec[k]
        L.append(f"| {k}: {' against '.join(name(c) for c in cl)} | {fmt(r['features'])} | {fmt(r['embedding'])} |")
    h6 = J["H6"]
    L += ["", "## Transfer of hub against diamond (H6)", "",
          "| Setting | Features AUC [95%] |", "|---|---|"]
    for p, x in h6["by_producer"].items():
        L.append(f"| producer {p} | {fmt(x)} |")
    L.append(f"| news genre, primary producer | {fmt(h6['news'])} |")
    for k in ("transfer_family", "transfer_producer", "transfer_genre"):
        L.append(f"| {k.replace('_', ' ')}: trained and tested on the first | {fmt(h6[k]['same'])} |")
        L.append(f"| {k.replace('_', ' ')}: trained on the first, tested on the second | {fmt(h6[k]['transfer'])} |")
    L += ["", "Transfer rows use a fixed penalty of 1 (no inner selection). Family A to B, primary producer to Haiku, "
          "incident to news. The same-setting and transferred rows are different messages (for family transfer, "
          "different replicates of the same worlds), so these are unpaired descriptive estimates of domain transfer, "
          "not paired estimates of a loss: " + "; ".join(
              f"{k.replace('transfer_', '')} same {h6[k]['same']['rows']} rows, transferred {h6[k]['transfer']['rows']} rows, "
              f"{h6[k]['shared_worlds']} worlds in both" for k in ("transfer_family", "transfer_producer", "transfer_genre"))
          + ".", "",
          "## Single-message leakage in sets (H7)", "",
          "One randomly chosen message per set, 90% intervals, tolerance 0.43 to 0.57.", "",
          "| Access, arm, pair | AUC [90%] | Verdict |", "|---|---|---|"]
    for k, x in J["H7"].items():
        acc, arm, a, b = k.split("|")
        L.append(f"| {acc}, {arm}, {name(a)} against {name(b)} | {fmt(x)} | {x['verdict']} |")
    L += ["", "## P3 under other producers and partial access", ""]
    for p, x in J["P3_other"].items():
        L.append(f"- {p}: pooled {fmt(x['pooled'])}, pairwise {fmt(x['pairwise'])}, gain {x['delta']['delta']:.3f} "
                 f"[{x['delta']['lo']:.3f}, {x['delta']['hi']:.3f}].")
    x = J["P3_partial"]
    L.append(f"- partial access, primary producer: pooled {fmt(x['pooled'])}, pairwise {fmt(x['pairwise'])}, gain "
             f"{x['delta']['delta']:.3f} [{x['delta']['lo']:.3f}, {x['delta']['hi']:.3f}]. Here shared packages "
             "contribute by construction.")
    L += ["", "## Prompted readers", "",
          "First replicate, 60 worlds, examples from the fold's training worlds. Descriptive.", "",
          "| Reader | Task | Items | AUC [95%] |", "|---|---|---|---|"]
    for k, x in J["readers"].items():
        reader, task = k.split("|", 1)
        if "IND_vs_DEP" in x:
            L.append(f"| {reader} | {task}, IND against DEP | {x['n']} | {fmt(x['IND_vs_DEP'])} |")
            L.append(f"| {reader} | {task}, three structures | {x['n']} | {fmt(x['three_class'])} |")
        else:
            L.append(f"| {reader} | {task} | {x['n']} | {fmt(x)} |")
    L += ["", f"Failed trials: {json.dumps(failures)}. Run time {time.time() - t0:.0f} s.", ""]
    with open(os.path.join(OUT, "text_only.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("wrote", os.path.join(OUT, "text_only.md"))


if __name__ == "__main__":
    main()

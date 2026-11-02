"""Analysis of the deeper-rewriting run, as fixed in runs/depth/PLAN.md.

    python analyze_depth.py

Reads runs/depth/sets.jsonl and makes no model calls. Writes
runs/depth/analysis.md and analysis.json. Depths 1, 2, 3, and 5, primary
producer, full access, neutral arm. Depth 1 is the full run's texts and must
reproduce its values.
"""
import json
import os
import sys
import time
from itertools import combinations

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyze  # noqa: E402
import run  # noqa: E402
from residue import analysis as an  # noqa: E402
from residue.embed import Embedder  # noqa: E402
from residue.features import WorldRarity, body, f_set_relational, pair_features, pooled_set_features, sentences  # noqa: E402

DIR = os.environ.get("DEPTH_DIR", os.path.join(HERE, "runs", "depth"))  # override only to test on the dry run
DEPTHS = tuple(int(x) for x in os.environ.get("DEPTHS", "1,2,3,5").split(","))
NBOOT = analyze.NBOOT
# full-run values that depth 1 must reproduce (manuscript_numbers.json)
EXPECT = {"pooled": 0.6993, "relational": 0.9077, "score": 0.863}


def relational_by_fold(rows, X0, fo, embed):
    """Pooled features plus relational features, with each outer fold's rarity
    table fit on its training worlds and each row's own world removed."""
    fold_of = np.array([fo[r["world"]] for r in rows])
    embed.many([body(t) for r in rows for t in r["texts"]] + [s for r in rows for t in r["texts"] for s in sentences(t)])
    out = {}
    for f in sorted(set(fold_of)):
        rar = WorldRarity.from_rows([r for r, fv in zip(rows, fold_of) if fv != f])
        rel = [f_set_relational(r["texts"], rar.for_world(r["world"]), embed) for r in rows]
        rk = sorted(rel[0])
        out[f] = (rar, np.hstack([X0, np.array([[d[k] for k in rk] for d in rel])]))
    return fold_of, out


def oof_by_fold(fold_of, Xr_by, y, w, fo):
    P = None
    for f, (_, Xr) in Xr_by.items():
        pf = an.oof_predict(Xr, y, w, fo)[0]
        if P is None:
            P = pf.copy()
        P[fold_of == f] = pf[fold_of == f]
    return P


def pooled_X(rows):
    pooled = [pooled_set_features(r["texts"]) for r in rows]
    pk = sorted(pooled[0])
    return np.array([[d[k] for k in pk] for d in pooled])


def binary(rows, fo, embed):
    rows = [r for r in rows if r["structure"] in ("IND", "DEP")]
    y = np.array([1 if r["structure"] == "DEP" else 0 for r in rows])  # out-star positive, as for the unfitted score
    w = [r["world"] for r in rows]
    X0 = pooled_X(rows)
    p0 = an.oof_predict(X0, y, w, fo)[0][:, 1]
    fold_of, Xr_by = relational_by_fold(rows, X0, fo, embed)
    pr = oof_by_fold(fold_of, Xr_by, y, w, fo)[:, 1]
    stats = {}
    for f, (rar, _) in Xr_by.items():
        for i in np.flatnonzero(fold_of == f):
            r = rows[i]
            pf = [pair_features(a, b, rar.for_world(r["world"]), embed) for a, b in combinations(r["texts"], 2)]
            for k in pf[0]:
                vals = sorted(p[k] for p in pf)
                for agg, v in (("min", vals[0]), ("median", vals[1]), ("max", vals[2])):
                    stats.setdefault(f"{k}_{agg}", np.zeros(len(rows)))[i] = v
    score = stats["rare_ngram_jaccard_max"]
    return {"n": len(rows),
            "pooled": an.auc_with_ci(y, p0, w, n=NBOOT),
            "relational": an.auc_with_ci(y, pr, w, n=NBOOT),
            "gain": an.paired_delta_auc(y, pr, p0, w, n=NBOOT),
            "score": an.auc_with_ci(y, score, w, n=NBOOT),
            "relational_minus_score": an.paired_delta_auc(y, pr, score, w, n=NBOOT),
            "unfitted": {k: an.auc_with_ci(y, v, w, n=NBOOT) for k, v in sorted(stats.items())}}


def three(rows, fo, embed):
    y = np.array([["IND", "DEP", "MIX"].index(r["structure"]) for r in rows])
    w = [r["world"] for r in rows]
    X0 = pooled_X(rows)
    P0 = an.oof_predict(X0, y, w, fo)[0]
    fold_of, Xr_by = relational_by_fold(rows, X0, fo, embed)
    Pr = oof_by_fold(fold_of, Xr_by, y, w, fo)
    return {"pooled": an.auc_with_ci(y, P0, w, n=NBOOT), "relational": an.auc_with_ci(y, Pr, w, n=NBOOT)}


def single_unshared(rows, fo, embed):
    rows = [r for r in rows if r["structure"] in ("IND", "DEP")]
    texts = [r["texts"][j] for r in rows for j in (1, 2)]
    y = np.array([["IND", "DEP"].index(r["structure"]) for r in rows for _ in (1, 2)])
    w = [r["world"] for r in rows for _ in (1, 2)]
    shared = len({t for r in rows if r["structure"] == "IND" for t in r["texts"][1:]} &
                 {t for r in rows if r["structure"] == "DEP" for t in r["texts"][1:]})
    out = {"n_reports": len(texts), "texts_shared_between_structures": shared}
    for name, X in (("features", np.asarray(analyze.text_X(texts), float)),
                    ("embedding", np.asarray(embed.many([body(t) for t in texts]), float))):
        P, _ = an.oof_predict(X, y, w, fo)
        out[name] = an.auc_with_ci(y, P, w, n=NBOOT, level=0.90)
        out[name]["verdict"] = an.three_way(out[name]["lo"], out[name]["hi"], 0.43, 0.57)
    return out


def main():
    t0 = time.time()
    allrows = [json.loads(l) for l in open(os.path.join(DIR, "sets.jsonl"), encoding="utf-8")]
    fo = analyze.folds()
    embed = Embedder(run.EMBED_CACHE)
    J = {"embedding_digest": embed.digest, "depths": {}}
    for d in DEPTHS:
        rows = [r for r in allrows if r["depth"] == d]
        rows.sort(key=lambda r: (r["world"], r["rep"], r["structure"]))  # the order analyze.load gives
        assert len(rows) == 540, (d, len(rows))
        J["depths"][d] = {"binary": binary(rows, fo, embed), "three": three(rows, fo, embed),
                          "single_unshared": single_unshared(rows, fo, embed)}
        if d == 1:
            b = J["depths"][1]["binary"]
            got = {"pooled": b["pooled"]["auc"], "relational": b["relational"]["auc"], "score": b["score"]["auc"]}
            for k, v in EXPECT.items():
                assert abs(got[k] - v) < 0.0006, f"depth 1 does not reproduce the full run: {k} {got[k]:.4f} vs {v}"
            J["depth1_check"] = got
        print(f"[{time.time() - t0:.0f}s] depth {d}", flush=True)
    with open(os.path.join(DIR, "analysis.json"), "w") as fh:
        json.dump(J, fh, indent=1, default=float)

    def ci(x, k="auc"):
        return f"{x[k]:.3f} [{x['lo']:.3f}, {x['hi']:.3f}]"
    L = ["# Deeper rewriting of the matched sets: analysis", "",
         f"Generated by `analyze_depth.py` at {time.strftime('%Y-%m-%d %H:%M')}. Plan: `PLAN.md`. Primary producer, full "
         "access, neutral arm, 180 sets per structure at each depth. Depth is the number of rewrites between each "
         "observation and each final report; depth 1 is the full run. 95% world-cluster intervals on fixed out-of-fold "
         "predictions unless noted. Out-star is the positive class.", "",
         "## Independent against out-star", "",
         "| Depth | Pooled | Relational | Gain | Unfitted max rare overlap | Relational minus score |",
         "|---|---|---|---|---|---|"]
    for d in DEPTHS:
        b = J["depths"][d]["binary"]
        L.append(f"| {d} | {ci(b['pooled'])} | {ci(b['relational'])} | {ci(b['gain'], 'delta')} | {ci(b['score'])} | "
                 f"{ci(b['relational_minus_score'], 'delta')} |")
    L += ["", "## Three structures, macro one-versus-one AUC", "", "| Depth | Pooled | Relational |", "|---|---|---|"]
    for d in DEPTHS:
        t = J["depths"][d]["three"]
        L.append(f"| {d} | {ci(t['pooled'])} | {ci(t['relational'])} |")
    L += ["", "## Single reports, unshared texts (90% intervals, band 0.43 to 0.57)", "",
          "| Depth | Reports | Shared texts | Features | Embedding |", "|---|---|---|---|---|"]
    for d in DEPTHS:
        s = J["depths"][d]["single_unshared"]
        L.append(f"| {d} | {s['n_reports']} | {s['texts_shared_between_structures']} | {ci(s['features'])} "
                 f"({s['features']['verdict']}) | {ci(s['embedding'])} ({s['embedding']['verdict']}) |")
    keys = list(J["depths"][1]["binary"]["unfitted"])
    L += ["", "## All nine unfitted statistics", "", "| Statistic | " + " | ".join(f"Depth {d}" for d in DEPTHS) + " |",
          "|---" * (len(DEPTHS) + 1) + "|"]
    for k in keys:
        L.append(f"| {k} | " + " | ".join(ci(J["depths"][d]["binary"]["unfitted"][k]) for d in DEPTHS) + " |")
    L += ["", f"Depth 1 check against the full run: {json.dumps({k: round(v, 4) for k, v in J['depth1_check'].items()})}.",
          f"Run time {time.time() - t0:.0f} s."]
    with open(os.path.join(DIR, "analysis.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("wrote analysis.md")


if __name__ == "__main__":
    main()

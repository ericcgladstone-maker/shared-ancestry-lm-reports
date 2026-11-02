"""World-anchored analyses from the proposition judge. UNVALIDATED.

    python analyze_anchored.py

Uses runs/full/judge/judgments.jsonl (residue/judge_matcher.py). Human
coding has not validated the judge, so every result here is labeled
unvalidated and none supports a claim until validation (design Part VI).
Writes runs/full/analysis/anchored.md and anchored.json.

Deviations. For each message, the events by which it departs from the
world record, counted only over facts its observation ancestor received:
an undisputed fact absent, changed, or doubted, and each dispute resolved
as first, second, or neither (both is faithful). The members of a dispute
enter only through its resolution, so one omission is never counted twice.

Shared-deviation statistic (design H8, as corrected by GPT Review of
Full-Run Analyses, section IV). For each pair, the events the two messages
share over the facts open to both, minus the type-matched expectation if
each message's events fell at random on those facts. Version 1 subtracted
a fold-level constant, which standardization cancels. A_s adds the excess's
minimum, median, and maximum over the set's three pairs to the pooled
baseline A_0. The design's support condition is that A_s - A_0 has a 95%
lower bound above 0 and (A_s - A_0) / (A_r - A_0) is at least 0.5; that
ratio compares AUC gains and is not a mediation fraction.
"""
import json
import os
import sys
import time
from collections import Counter, defaultdict
from itertools import combinations
from statistics import median

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyze  # noqa: E402
import run  # noqa: E402
from analyze import fmt, name  # noqa: E402
from residue import analysis as an  # noqa: E402
from residue.embed import Embedder  # noqa: E402
from residue.features import WorldRarity, body, f_set_relational, pooled_set_features, sentences  # noqa: E402
from residue.keys import canonical, sha256  # noqa: E402
from residue import judge_matcher as jm  # noqa: E402


def load_judgments():
    out = {}
    for line in open(os.path.join(analyze.FULL, "judge", "judgments.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        if r.get("final") and r["valid"]:
            out[(r["world"], r["text_hash"])] = r["result"]
    return out


def events(result, world, accessible=None):
    """Deviation units of one message: {unit: event}. A unit is an undisputed
    fact, or a dispute whose two members could both reach the message; a
    dispute with only one accessible member is treated as that member's fact.
    Only facts the message's observation ancestor received count
    (GPT Review of Full-Run Analyses, section IV). The event is the fact's
    state if not stated, or the dispute's resolution if not both."""
    acc = set(accessible) if accessible is not None else set(result["facts"])
    pairs = world.conflict_pairs()
    disputed = {p for pr in pairs for p in pr}
    units = {}
    for pid, st in result["facts"].items():
        if pid in acc and pid not in disputed:
            units[pid] = None if st == "stated" else st
    for i, (a, b) in enumerate(pairs):
        if a in acc and b in acc:
            r = result["disputes"][i] if i in result["disputes"] else result["disputes"].get(str(i))
            units[("d", i)] = None if r == "both" else r
        else:
            for m in (a, b):
                if m in acc:
                    st = result["facts"][m]
                    units[m] = None if st == "stated" else st
    return units


OMISSION = {"absent", "neither"}
AFFIRMATIVE = {"changed", "doubted", "first", "second"}
VARIANTS = {"all": None, "omission only": OMISSION, "affirmative only": AFFIRMATIVE,
            "all except neither": {"absent", "changed", "doubted", "first", "second"}}


def shared_excess(ua, ub, keep=None):
    """Shared events of a pair over the units open to both, and the excess
    over the expectation if each message's events fell on those units at
    random, matched by event type: sum over types of k_a * k_b / N."""
    U = set(ua) & set(ub)
    if not U:
        return 0.0, 0.0
    ea = {u: ua[u] for u in U if ua[u] is not None and (keep is None or ua[u] in keep)}
    eb = {u: ub[u] for u in U if ub[u] is not None and (keep is None or ub[u] in keep)}
    shared = sum(1 for u in ea if eb.get(u) == ea[u])
    ka, kb = Counter(ea.values()), Counter(eb.values())
    expected = sum(ka[t] * kb[t] for t in ka) / len(U)
    return float(shared), float(shared - expected)


def consistency(result, world):
    """Cross-field contradictions between fact states and dispute resolutions."""
    bad = 0
    for i, (a, b) in enumerate(world.conflict_pairs()):
        r = result["disputes"].get(i, result["disputes"].get(str(i)))
        fa, fb = result["facts"][a], result["facts"][b]
        if (r == "first" and fa == "absent") or (r == "second" and fb == "absent") or \
           (r == "both" and "absent" in (fa, fb)) or (r == "neither" and "stated" in (fa, fb)):
            bad += 1
    return bad


def main():
    t0 = time.time()
    worlds, s1, s2, _ = analyze.load()
    wmap = {w.world_id: w for w in worlds}
    fo = analyze.folds()
    embed = Embedder(run.EMBED_CACHE)
    jd = load_judgments()

    def ev_of(wid, text, accessible=None):
        r = jd.get((wid, sha256(body(text))))
        return None if r is None else events(r, wmap[wid], accessible)

    J, L = {}, []

    # descriptive deviation rates by structure
    rates = defaultdict(list)
    for r in s1:
        if r["producer"] == run.PRIMARY and r["genre"] == "incident":
            e = ev_of(r["world"], r["text"])
            if e is not None:
                res = jd[(r["world"], sha256(body(r["text"])))]
                rates[r["cond"]].append((sum(v == "absent" for v in res["facts"].values()),
                                         sum(v == "changed" for v in res["facts"].values()),
                                         sum(v == "doubted" for v in res["facts"].values()),
                                         sum(v in ("first", "second") for v in res["disputes"].values()),
                                         sum(v == "both" for v in res["disputes"].values())))
    J["rates"] = {c: {"n": len(v), "absent": float(np.mean([x[0] for x in v])), "changed": float(np.mean([x[1] for x in v])),
                      "doubted": float(np.mean([x[2] for x in v])), "disputes_resolved_one_way": float(np.mean([x[3] for x in v])),
                      "disputes_both": float(np.mean([x[4] for x in v]))} for c, v in rates.items()}

    # full specification for Study 1: text-only features plus propositional counts
    def prop_feats(wid, text):
        res = jd.get((wid, sha256(body(text))))
        f = res["facts"]
        d = res["disputes"]
        return [sum(v == s for v in f.values()) for s in ("absent", "changed", "doubted")] + \
               [sum(v == s for v in d.values()) for s in ("first", "second", "both", "neither")]
    J["full_spec"] = {}
    for k, cl in {"P2": ["SD-same", "SI-same"], "depth": ["R1", "R3", "R5"]}.items():
        rows = [r for r in s1 if r["producer"] == run.PRIMARY and r["genre"] == "incident" and r["cond"] in cl
                and (r["world"], sha256(body(r["text"]))) in jd]
        if len({r["cond"] for r in rows}) < len(cl):
            continue
        y = np.array([cl.index(r["cond"]) for r in rows])
        w = [r["world"] for r in rows]
        XT = np.array(analyze.text_X([r["text"] for r in rows]), float)
        XP = np.array([prop_feats(r["world"], r["text"]) for r in rows], float)
        pt = an.oof_predict(XT, y, w, fo)[0]
        pf = an.oof_predict(np.hstack([XT, XP]), y, w, fo)[0]
        pp = an.oof_predict(XP, y, w, fo)[0]
        sel = lambda P: P[:, 1] if P.shape[1] == 2 else P  # noqa: E731
        J["full_spec"][k] = {"n": len(y), "text_only": an.auc_with_ci(y, sel(pt), w, n=analyze.NBOOT),
                             "full": an.auc_with_ci(y, sel(pf), w, n=analyze.NBOOT),
                             "propositional_only": an.auc_with_ci(y, sel(pp), w, n=analyze.NBOOT)}

    # judge consistency between fact states and dispute resolutions
    flags = [consistency(res, wmap[wid]) for (wid, _), res in jd.items()]
    J["consistency"] = {"messages": len(flags), "with_contradiction": int(sum(1 for f in flags if f)),
                        "disputes_contradicted": int(sum(flags)), "disputes_judged": 2 * len(flags)}

    # H8 shared-deviation account, by access
    J["H8"] = {}
    for access in ("full", "partial"):
        rows = [r for r in s2 if r["producer"] == run.PRIMARY and r["access"] == access and r["arm"] == "neutral"
                and r["structure"] in ("IND", "DEP")]
        evs = [[ev_of(r["world"], t, pk) for t, pk in zip(r["texts"], r["packages"])] for r in rows]
        keep = [i for i, e in enumerate(evs) if all(x is not None for x in e)]
        rows, evs = [rows[i] for i in keep], [evs[i] for i in keep]
        if not rows:
            continue
        y = np.array([1 if r["structure"] == "IND" else 0 for r in rows])
        w = [r["world"] for r in rows]
        fold_of = np.array([fo[x] for x in w])
        pooled = [pooled_set_features(r["texts"]) for r in rows]
        pk_ = sorted(pooled[0])
        X0 = np.array([[d[k] for k in pk_] for d in pooled])
        p0 = an.oof_predict(X0, y, w, fo)[0][:, 1]
        embed.many([body(t) for r in rows for t in r["texts"]] + [s for r in rows for t in r["texts"] for s in sentences(t)])
        pr = np.zeros(len(y))
        for f in sorted(set(fold_of)):
            rar = WorldRarity.from_rows([r for r, fv in zip(rows, fold_of) if fv != f])
            rel = [f_set_relational(r["texts"], rar.for_world(r["world"]), embed) for r in rows]
            rk = sorted(rel[0])
            Xr = np.hstack([X0, np.array([[d[k] for k in rk] for d in rel])])
            pr[fold_of == f] = an.oof_predict(Xr, y, w, fo)[0][:, 1][fold_of == f]
        dr = an.paired_delta_auc(y, pr, p0, w, n=analyze.NBOOT)
        out = {"sets": len(y), "A0": an.auc_with_ci(y, p0, w, n=analyze.NBOOT), "Ar": an.auc_with_ci(y, pr, w, n=analyze.NBOOT),
               "Ar_minus_A0": dr, "variants": {}}
        for vname, keepset in VARIANTS.items():
            pairs = [[shared_excess(a, b, keepset) for a, b in combinations(e, 2)] for e in evs]
            raw = [[p[0] for p in ps_] for ps_ in pairs]
            exc = [[p[1] for p in ps_] for ps_ in pairs]
            S = np.array([[min(x), median(x), max(x)] for x in exc])
            ps = an.oof_predict(np.hstack([X0, S]), y, w, fo)[0][:, 1]
            alone = an.oof_predict(S, y, w, fo)[0][:, 1]
            ds = an.paired_delta_auc(y, ps, p0, w, n=analyze.NBOOT)

            def ratio(idx, ps=ps):
                if len(np.unique(y[idx])) < 2:
                    return np.nan
                a0, as_, ar = (an.auc(y[idx], q[idx]) for q in (p0, ps, pr))
                return (as_ - a0) / (ar - a0) if ar != a0 else np.nan
            boot = an.world_bootstrap(ratio, w, n=analyze.NBOOT)
            boot = boot[~np.isnan(boot)]
            rt = ratio(np.arange(len(y)))
            out["variants"][vname] = {
                "As": an.auc_with_ci(y, ps, w, n=analyze.NBOOT), "alone": an.auc_with_ci(y, alone, w, n=analyze.NBOOT),
                "As_minus_A0": ds, "gain_ratio": float(rt),
                "gain_ratio_ci": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))],
                "support_condition_met": bool(ds["lo"] > 0 and dr["lo"] > 0 and rt >= 0.5),
                "mean_shared": {st: float(np.mean([np.mean(x) for x, r in zip(raw, rows) if r["structure"] == st]))
                                for st in ("IND", "DEP")},
                "mean_excess": {st: float(np.mean([np.mean(x) for x, r in zip(exc, rows) if r["structure"] == st]))
                                for st in ("IND", "DEP")}}
        J["H8"][access] = out
    J["judged_messages"] = len(jd)

    with open(os.path.join(analyze.OUT, "anchored.json"), "w") as fh:
        json.dump(J, fh, indent=1, default=float)

    L += ["# World-anchored results, full run (UNVALIDATED)", "",
          f"Generated by `analyze_anchored.py` at {time.strftime('%Y-%m-%d %H:%M')} from {J['judged_messages']} messages "
          f"judged by gpt-6.1-terra ({jm.VERSION}, `residue/judge_matcher.py`), primary producer. Human coding has not "
          "validated the judge. None of these results supports a claim until it does, and the design withholds them "
          "if validation fails.", "",
          "## Deviations from the record by structure", "",
          "Mean per message: facts absent, changed, and doubted (of 20, including dispute members), and disputes (of 2) "
          "given one way or both ways.", "",
          "| Structure | Messages | Absent | Changed | Doubted | Disputes one way | Disputes both ways |", "|---|---|---|---|---|---|---|"]
    order = ["D0", "R1", "R3", "R5", "SI-same", "SD-same"]
    # only the structures judged as such; a few other conditions' messages are byte-identical copies of judged ones
    for c in [x for x in order if x in J["rates"] and J["rates"][x]["n"] >= 100]:
        v = J["rates"][c]
        L.append(f"| {name(c)} | {v['n']} | {v['absent']:.2f} | {v['changed']:.2f} | {v['doubted']:.2f} | "
                 f"{v['disputes_resolved_one_way']:.2f} | {v['disputes_both']:.2f} |")
    L += ["", "## Text plus seven judged counts, Study 1", "",
          "Not the design's full propositional family: the counts are facts absent, changed, and doubted, and disputes "
          "resolved first, second, both, and neither. Unsupported additions and proposition order are not measured.", "",
          "| Contrast | Text-only | Text plus judged counts | Judged counts only |",
          "|---|---|---|---|"]
    for k, v in J["full_spec"].items():
        L.append(f"| {k} | {fmt(v['text_only'])} | {fmt(v['full'])} | {fmt(v['propositional_only'])} |")
    c = J["consistency"]
    L += ["", f"Judge consistency: {c['with_contradiction']} of {c['messages']} messages have a dispute resolution that "
          f"contradicts the judge's own fact states ({c['disputes_contradicted']} of {c['disputes_judged']} disputes). The "
          "judge's output is not constrained to be consistent.", "",
          "## Shared-deviation account of the set result (H8)", "",
          "Three unconnected sources against out-star. Each pair's events are counted over the facts both messages could "
          "carry (the packages of their observation ancestors), and the statistic is the excess of shared events over "
          "their type-matched expectation if each message's events fell at random on those facts. A_s adds the excess's "
          "minimum, median, and maximum over the set's three pairs to the pooled baseline. The gain ratio is "
          "(A_s − A_0) / (A_r − A_0), a ratio of AUC gains under these classifiers, not a share of a causal effect. "
          "Variants keep only some event types, to separate shared omission (absent facts and disputes given neither "
          "way) from shared affirmative departures (changed or doubted facts and one-sided dispute resolutions).", ""]
    for access, v in J["H8"].items():
        L += [f"**{access.capitalize()} access**, {v['sets']} sets. A_0 {fmt(v['A0'])}, A_r {fmt(v['Ar'])}, A_r − A_0 "
              f"{v['Ar_minus_A0']['delta']:.3f} [{v['Ar_minus_A0']['lo']:.3f}, {v['Ar_minus_A0']['hi']:.3f}]."
              + (" Partial-access observers receive different packages under IND and one package under out-star, so "
                 "this arm still combines shared access with shared ancestry." if access == "partial" else ""), "",
              "| Events | Shared per pair, IND / out-star | Excess per pair, IND / out-star | A_s [95%] | Excess alone [95%] | "
              "A_s − A_0 [95%] | Gain ratio [95%] | Support condition |", "|---|---|---|---|---|---|---|---|"]
        for vname, x in v["variants"].items():
            d = x["As_minus_A0"]
            L.append(f"| {vname} | {x['mean_shared']['IND']:.2f} / {x['mean_shared']['DEP']:.2f} | "
                     f"{x['mean_excess']['IND']:.2f} / {x['mean_excess']['DEP']:.2f} | {fmt(x['As'])} | {fmt(x['alone'])} | "
                     f"{d['delta']:.3f} [{d['lo']:.3f}, {d['hi']:.3f}] | {x['gain_ratio']:.2f} [{x['gain_ratio_ci'][0]:.2f}, "
                     f"{x['gain_ratio_ci'][1]:.2f}] | {'met' if x['support_condition_met'] else 'not met'} |")
        L.append("")
    L += ["## Not built", "",
          "H11's world-free method is described in the design only as using an independent reference corpus, which "
          "leaves its construction open. It is not built here. H10's anchored invariance to stripping holds by "
          "construction, because the judge reads the body without the Sources line.", "",
          f"Run time {time.time() - t0:.0f} s.", ""]
    with open(os.path.join(analyze.OUT, "anchored.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("wrote", os.path.join(analyze.OUT, "anchored.md"))


if __name__ == "__main__":
    main()

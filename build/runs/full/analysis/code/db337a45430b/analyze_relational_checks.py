"""Two checks on the relational set models of the full run (agreed with GPT, 2026-10-31).

    python analyze_relational_checks.py

Makes no model calls. Writes runs/full/analysis/relational_checks.md and .json.

1. Presentation-order invariance of the five-configuration set predictor.
   Generation puts a Y set's odd message in slot 3. The predictor's features
   are symmetric in the messages and carry no slot index, so reordering the
   three messages should move each prediction with its text. Every set is
   presented in each of the six orders, and once in a random order per set,
   with features recomputed on the reordered texts and the models refitted.
   Readings fixed before the run: if accuracy, odd-message identification,
   and the per-set predictions in generation terms match the identity order
   to numerical tolerance, the reported 0.591 and 81% stand and nothing
   changes. Any other outcome is a defect to fix before those numbers are
   used. The run also splits the gap between three-structure and
   five-configuration accuracy into its sources.

2. Ablation of the three relational feature families (rare word-sequence
   overlap, sentence-order similarity, embedding similarity) in the P3 set
   model and in the pair model behind odd-message identification: the full
   model, each family removed, and each family alone, with the same rows,
   folds, and learners as analyze_secondary.py. Intervals are the paired
   world bootstrap on fixed out-of-fold predictions, the conditional
   estimand of text_only.md. Sentence-order similarity matches sentences by
   embedding, so removing the embedding family does not remove all use of
   embeddings.

   The first run of this script found that the rarity table, fitted on a
   fold's training texts, counts each training row's own texts and the
   identical messages its sibling sets reuse, so rare overlap is near zero
   in training rows and zero in all of them in the three-structure models.
   The ablation and the set predictor are therefore reported under that fit
   and under a fit that removes each training row's own world from the
   counts (OwnWorldExcluded). Neither fit uses test-world texts.
"""
import json
import os
import random
import sys
import time
from itertools import combinations, permutations
from statistics import median

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyze  # noqa: E402
import run  # noqa: E402
from residue import analysis as an  # noqa: E402
from residue.embed import Embedder  # noqa: E402
from residue.features import RarityTable, body, ngrams, pair_features, pooled_set_features, sentences  # noqa: E402

OUT = analyze.OUT
FAMILIES = {"rare word-sequence overlap": "rare_ngram_jaccard", "sentence-order similarity": "sentence_order_similarity",
            "embedding similarity": "embedding_cosine"}
SHARED = {"IND": (False, False, False), "DEP": (True, True, True), "MIX": (True, False, False)}  # slot pairs (1,2), (1,3), (2,3)


def oof(X, y, w, fo):
    return an.oof_predict(np.asarray(X, float), np.asarray(y), w, fo)[0]


class OwnWorldExcluded:
    """A fold's rarity table with one world's own texts removed from the
    counts. Sets in a block reuse identical messages across structures, so a
    training row's shared n-grams are counted in its own and sibling rows and
    almost never count as rare, while a test row's texts are absent from the
    table. Removing the row's world makes training rows see the counts a test
    row sees."""

    def __init__(self, base, own, max_df=2):
        self.base, self.own, self.max_df = base, own, max_df

    def rare(self, text):
        out = set()
        for n in (3, 4, 5):
            out |= {g for g in ngrams(text, n) if self.base.get(g, 0) - self.own.get(g, 0) <= self.max_df}
        return out


class Pairs:
    """pair_features on the real texts, cached by fold, row, and ordered pair.
    The rarity table is rebuilt from each fold's training texts, as in
    analyze_secondary.py (fit "fold"), or with each row's own world removed
    from the counts (fit "own world excluded")."""

    def __init__(self, rows, fo, embed, fit="fold"):
        self.rows, self.embed, self.fit = rows, embed, fit
        self.fold_of = np.array([fo[r["world"]] for r in rows])
        self.rar = {f: RarityTable([t for r, fv in zip(rows, self.fold_of) if fv != f for t in r["texts"]])
                    for f in sorted(set(self.fold_of))}
        self.own = {}
        if fit != "fold":
            for x in sorted({r["world"] for r in rows}):
                self.own[x] = RarityTable([t for r in rows if r["world"] == x for t in r["texts"]]).df
        self.cache = {}

    def table(self, f, i):
        x = self.rows[i]["world"]
        if self.fit == "fold" or self.fold_of[i] == f:  # a test row's world is never in its table
            return self.rar[f]
        return OwnWorldExcluded(self.rar[f].df, self.own[x])

    def get(self, f, a, b, i=None):
        k = (f, a, b) if self.fit == "fold" else (f, self.rows[i]["world"], a, b)
        if k not in self.cache:
            self.cache[k] = pair_features(a, b, self.table(f, i) if i is not None else self.rar[f], self.embed)
        return self.cache[k]


def relational(pairs, keep):
    """f_set_relational's min, median, and max, over the kept families."""
    out = {}
    for k in sorted(pairs[0]):
        if k not in keep:
            continue
        vals = sorted(p[k] for p in pairs)
        out[f"{k}_min"], out[f"{k}_median"], out[f"{k}_max"] = vals[0], median(vals), vals[-1]
    return out


def set_probs(PF, texts_of, y, w, fo, keep, X0):
    """Out-of-fold probabilities of the pooled-plus-relational set model, one
    relational design per test fold (its rarity table), as in set_models."""
    P = None
    for f in sorted(PF.rar):
        rel = [relational([PF.get(f, a, b, i) for a, b in combinations(texts_of(i), 2)], keep) for i in range(len(y))]
        rk = sorted(rel[0])
        X = np.hstack([X0, np.array([[d[k] for k in rk] for d in rel])])
        pf = oof(X, y, w, fo)
        P = pf if P is None else P
        P[PF.fold_of == f] = pf[PF.fold_of == f]
    return P


def pair_probs(PF, texts_of, n, yp, pw, fo, keep):
    """Out-of-fold same-root probabilities for each set's three presented pairs."""
    Pp = np.zeros(len(yp))
    pfold = np.repeat(PF.fold_of, 3)
    for f in sorted(PF.rar):
        X = np.array([[d[k] for k in sorted(d) if k in keep] for i in range(n)
                      for d in (PF.get(f, a, b, i) for a, b in combinations(texts_of(i), 2))])
        pf = oof(X, yp, pw, fo)[:, 1]
        Pp[pfold == f] = pf[pfold == f]
    return Pp.reshape(n, 3)


def pooled_X(rows):
    pooled = [pooled_set_features(r["texts"]) for r in rows]
    pk = sorted(pooled[0])
    return np.array([[d[k] for k in pk] for d in pooled])


def main():
    t0 = time.time()
    log = lambda m: print(f"[{time.time() - t0:.0f}s] {m}", flush=True)  # noqa: E731
    worlds, s1, s2, failures = analyze.load()
    fo = analyze.folds()
    embed = Embedder(run.EMBED_CACHE)
    allkeys = set(FAMILIES.values())
    J = {"families": FAMILIES}

    def sets_of(producer, structures):
        return [r for r in s2 if r["producer"] == producer and r["access"] == "full" and r["arm"] == "neutral"
                and r["structure"] in structures]

    # ---------- 1. presentation-order invariance ----------
    rows = sets_of(run.PRIMARY, ("IND", "DEP", "MIX"))
    embed.many([body(t) for r in rows for t in r["texts"]] + [s for r in rows for t in r["texts"] for s in sentences(t)])
    n = len(rows)
    y3 = np.array([["IND", "DEP", "MIX"].index(r["structure"]) for r in rows])
    w3 = [r["world"] for r in rows]
    pw = [x for x in w3 for _ in range(3)]
    X0 = pooled_X(rows)  # mean and max over messages, unchanged by order
    PF = Pairs(rows, fo, embed)
    rng = random.Random(f"order|{run.RUN_SEED}")
    orders = {"".join(str(s + 1) for s in p): [p] * n for p in permutations(range(3))}
    orders["random per set"] = [tuple(rng.sample(range(3), 3)) for _ in range(n)]
    res, ident = {}, None
    for oname, perm in orders.items():
        # perm[i][j] is the generation slot shown at presented position j
        texts_of = lambda i, perm=perm: [rows[i]["texts"][s] for s in perm[i]]  # noqa: E731
        Ps = set_probs(PF, texts_of, y3, w3, fo, allkeys, X0)
        # a presented pair shares a root under DEP, and under Y when neither member is generation slot 3
        yp = np.array([(rows[i]["structure"] == "DEP") or (rows[i]["structure"] == "MIX" and 2 not in (perm[i][a], perm[i][b]))
                       for i in range(n) for a, b in combinations(range(3), 2)], int)
        Pp = pair_probs(PF, texts_of, n, yp, pw, fo, allkeys)
        q = Pp[:, [2, 1, 0]]  # presented pair (2,3) -> odd 1, (1,3) -> odd 2, (1,2) -> odd 3
        q = q / q.sum(1, keepdims=True)
        cfg = np.column_stack([Ps[:, 0], Ps[:, 1], Ps[:, 2:3] * q])
        # back to generation terms: probability that the odd message is generation slot s
        gen = np.zeros_like(cfg)
        gen[:, :2] = cfg[:, :2]
        for i in range(n):
            for j, s in enumerate(perm[i]):
                gen[i, 2 + s] = cfg[i, 2 + j]
        truth = np.array([0 if r["structure"] == "IND" else 1 if r["structure"] == "DEP" else 4 for r in rows])
        mix = truth == 4
        r_ = {"accuracy": float(np.mean(gen.argmax(1) == truth)),
              "three_structure_accuracy": float(np.mean(Ps.argmax(1) == y3)),
              "mix_odd_correct": float(np.mean(gen[mix, 2:].argmax(1) == 2)),
              "odd_slot_presented": dict(zip(*[x.tolist() for x in np.unique(
                  [perm[i].index(2) + 1 for i in np.flatnonzero(mix)], return_counts=True)]))}
        if ident is None:
            ident = (gen, Ps)
            pred_cfg = gen.argmax(1)
            p3 = Ps.argmax(1)
            dec = {"truth Y": {}, "truth three unconnected or out-star": {}}
            for i in range(n):
                if mix[i]:
                    k = ("correct" if pred_cfg[i] == 4 else
                         "three-structure Y, odd message wrong" if p3[i] == 2 and pred_cfg[i] in (2, 3) else
                         "three-structure Y, demoted by the split" if p3[i] == 2 else "three-structure wrong")
                    dec["truth Y"][k] = dec["truth Y"].get(k, 0) + 1
                else:
                    k = ("both correct" if p3[i] == y3[i] and pred_cfg[i] == truth[i] else
                         "five-configuration correct only (Y split below it)" if pred_cfg[i] == truth[i] else
                         "three-structure correct only" if p3[i] == y3[i] else "both wrong")
                    dec["truth three unconnected or out-star"][k] = dec["truth three unconnected or out-star"].get(k, 0) + 1
            J["gap_decomposition"] = dec
        else:
            r_["max_abs_prob_diff_vs_identity"] = float(np.max(np.abs(gen - ident[0])))
            r_["max_abs_structure_prob_diff_vs_identity"] = float(np.max(np.abs(Ps - ident[1])))
            r_["sets_with_different_configuration"] = int(np.sum(gen.argmax(1) != ident[0].argmax(1)))
        res[oname] = r_
        log(f"order {oname}: accuracy {r_['accuracy']:.3f}, odd {r_['mix_odd_correct']:.3f}")
    J["invariance"] = {"n_sets": n, "n_y_sets": int(np.sum(y3 == 2)), "orders": res}

    # ---------- 2. relational family ablation, under both rarity fits ----------
    variants = {"all three": allkeys}
    variants.update({f"without {k}": allkeys - {v} for k, v in FAMILIES.items()})
    variants.update({f"{k} alone": {v} for k, v in FAMILIES.items()})
    FITS = ("fold", "own world excluded")
    J["P3_ablation"], J["pair_ablation"], J["set_predictor"] = {f: {} for f in FITS}, {f: {} for f in FITS}, {}
    for prod in run.PRODUCERS:
        rows = sets_of(prod, ("IND", "DEP"))
        embed.many([body(t) for r in rows for t in r["texts"]] + [s for r in rows for t in r["texts"] for s in sentences(t)])
        y = np.array([["IND", "DEP"].index(r["structure"]) for r in rows])
        w = [r["world"] for r in rows]
        X0 = pooled_X(rows)
        texts_of = lambda i, rows=rows: rows[i]["texts"]  # noqa: E731
        p0 = oof(X0, y, w, fo)[:, 1]
        for fit in FITS:
            PF = Pairs(rows, fo, embed, fit)
            P = {v: set_probs(PF, texts_of, y, w, fo, keep, X0)[:, 1] for v, keep in variants.items()}
            out = {"n_sets": len(rows), "pooled": an.auc_with_ci(y, p0, w, n=analyze.NBOOT)}
            for v in variants:
                out[v] = {"auc": an.auc_with_ci(y, P[v], w, n=analyze.NBOOT),
                          "gain_over_pooled": an.paired_delta_auc(y, P[v], p0, w, n=analyze.NBOOT)}
                if v != "all three":
                    out[v]["change_from_all_three"] = an.paired_delta_auc(y, P[v], P["all three"], w, n=analyze.NBOOT)
            J["P3_ablation"][fit][prod] = out
            log(f"P3 ablation {prod}, {fit}")

    # odd-message identification, same-root pairs, and the five-configuration predictor, primary producer
    rows = sets_of(run.PRIMARY, ("IND", "DEP", "MIX"))
    n = len(rows)
    texts_of = lambda i: rows[i]["texts"]  # noqa: E731
    yp = np.array([v for r in rows for v in SHARED[r["structure"]]], int)
    pw = [r["world"] for r in rows for _ in range(3)]
    mix = np.array([r["structure"] == "MIX" for r in rows])
    y3 = np.array([["IND", "DEP", "MIX"].index(r["structure"]) for r in rows])
    w3 = [r["world"] for r in rows]
    X0 = pooled_X(rows)
    truth = np.array([0 if r["structure"] == "IND" else 1 if r["structure"] == "DEP" else 4 for r in rows])
    for fit in FITS:
        PF = Pairs(rows, fo, embed, fit)
        for v, keep in variants.items():
            Pp = pair_probs(PF, texts_of, n, yp, pw, fo, keep)
            J["pair_ablation"][fit][v] = {"same_root_auc": an.auc_with_ci(yp, Pp.ravel(), pw, n=analyze.NBOOT),
                                          "mix_odd_correct": float(np.mean(Pp[mix][:, [2, 1, 0]].argmax(1) == 2))}
            if v == "all three":
                Ps = set_probs(PF, texts_of, y3, w3, fo, keep, X0)
                q = Pp[:, [2, 1, 0]] / Pp.sum(1, keepdims=True)
                cfg = np.column_stack([Ps[:, 0], Ps[:, 1], Ps[:, 2:3] * q])
                J["set_predictor"][fit] = {"three_structure_accuracy": float(np.mean(Ps.argmax(1) == y3)),
                                           "three_structure_macro_auc": an.auc_with_ci(y3, Ps, w3, n=analyze.NBOOT),
                                           "configuration_accuracy": float(np.mean(cfg.argmax(1) == truth)),
                                           "y_sets_fully_correct": int(np.sum(cfg[mix].argmax(1) == 4)),
                                           "mix_odd_correct": float(np.mean(q[mix].argmax(1) == 2))}
        log(f"pair ablation, {fit}")

    with open(os.path.join(OUT, "relational_checks.json"), "w") as fh:
        json.dump(J, fh, indent=1, default=float)

    # ---------- report ----------
    def ci(x):
        return f"{x['auc']:.3f} [{x['lo']:.3f}, {x['hi']:.3f}]"

    def dci(x):
        return f"{x['delta']:+.3f} [{x['lo']:+.3f}, {x['hi']:+.3f}]"

    inv = J["invariance"]
    L = ["# Relational checks, full run", "",
         f"Generated by `analyze_relational_checks.py` at {time.strftime('%Y-%m-%d %H:%M')}. No model calls. Full access, "
         "neutral attribution. Same rows, folds, learners, and per-fold rarity tables as `analyze_secondary.py`.", "",
         "## Presentation order of the five-configuration predictor", "",
         f"{inv['n_sets']} sets of the primary producer, {inv['n_y_sets']} of them Y sets. Order 123 is generation order, "
         "the arrangement behind `secondary.md`. In each other order the three messages are presented in that sequence of "
         "generation slots, features are recomputed on the reordered texts, and every model is refitted. Probabilities are "
         "then mapped back to generation slots and compared with order 123.", "",
         "| Presented order | Configuration accuracy | Three-structure accuracy | Y sets, odd message identified | "
         "Largest probability difference from 123 | Sets whose predicted configuration differs from 123 |",
         "|---|---|---|---|---|---|"]
    for o, r_ in inv["orders"].items():
        L.append(f"| {o} | {r_['accuracy']:.3f} | {r_['three_structure_accuracy']:.3f} | {r_['mix_odd_correct']:.1%} | "
                 f"{r_.get('max_abs_prob_diff_vs_identity', 0):.2e} | {r_.get('sets_with_different_configuration', 0)} |")
    L += ["", "Presented position of the odd message, random order per set: "
          + ", ".join(f"position {k}: {v}" for k, v in inv["orders"]["random per set"]["odd_slot_presented"].items()) + ".",
          "", "Sources of the gap between three-structure and five-configuration accuracy, generation order:", ""]
    for g, d in J["gap_decomposition"].items():
        L.append(f"- {g}: " + ", ".join(f"{k} {v}" for k, v in sorted(d.items())) + ".")
    L += ["", "## Rarity fit", "",
          "Rare word-sequence overlap counts the 3- to 5-word sequences two messages share that appear in at most two "
          "documents of the fold's training texts. Sets in a block reuse identical messages across structures (the store "
          "keeps one call per key), so 900 distinct texts fill the 1,080 message slots of the IND and DEP sets and the "
          "1,620 of the three-structure sets. A training row's shared sequences are then counted in its own and its sibling "
          "rows and seldom stay rare, while a test row's texts are absent from the table. Under the fit used so far "
          "(fold), the feature is near zero in training rows and large in test rows, and in the three-structure rows it is "
          "zero in every training row, so the pair and set models there cannot use it. No test-world information enters "
          "either fit. The second fit (own world excluded) removes each training row's world from the counts, so training "
          "and test rows see the same kind of table. Every result below is reported under both fits.", "",
          "| Rarity fit | Three-structure accuracy | Three-structure macro AUC | Configuration accuracy | "
          "Y sets fully correct | Y sets, odd message identified |", "|---|---|---|---|---|---|"]
    for fit, x in J["set_predictor"].items():
        L.append(f"| {fit} | {x['three_structure_accuracy']:.3f} | {ci(x['three_structure_macro_auc'])} | "
                 f"{x['configuration_accuracy']:.3f} | {x['y_sets_fully_correct']} of {inv['n_y_sets']} | "
                 f"{x['mix_odd_correct']:.1%} |")
    L += ["", "## Relational feature families", "",
          "P3 set model, three unconnected sources (IND) against out-star (DEP). The pooled baseline has no cross-message "
          "features. Each variant adds the min, median, and max over a set's three pairs of the families named. Intervals "
          "are paired world bootstraps on fixed out-of-fold predictions (2,000 draws). Sentence-order similarity matches "
          "sentences by embedding, so the variants without embedding similarity still use embeddings inside that family.", ""]
    for fit in J["P3_ablation"]:
        for prod, out in J["P3_ablation"][fit].items():
            L += [f"### {prod}, rarity fit: {fit}", "", f"{out['n_sets']} sets. Pooled baseline {ci(out['pooled'])}.", "",
                  "| Relational features | AUC | Gain over pooled | Change from all three |", "|---|---|---|---|"]
            for v in variants:
                x = out[v]
                L.append(f"| {v} | {ci(x['auc'])} | {dci(x['gain_over_pooled'])} | "
                         f"{dci(x['change_from_all_three']) if 'change_from_all_three' in x else ''} |")
            L.append("")
    L += ["## Pair model behind odd-message identification", "",
          "Primary producer, all three structures, pairs in generation order. Same-root AUC over all pairs, and the share "
          "of Y sets whose odd message is the one outside the most likely same-root pair.", "",
          "| Rarity fit | Pair features | Same-root AUC | Y sets, odd message identified |", "|---|---|---|---|"]
    for fit in J["pair_ablation"]:
        for v, x in J["pair_ablation"][fit].items():
            L.append(f"| {fit} | {v} | {ci(x['same_root_auc'])} | {x['mix_odd_correct']:.1%} |")
    L += ["", f"Run time {time.time() - t0:.0f} s."]
    with open(os.path.join(OUT, "relational_checks.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("wrote", os.path.join(OUT, "relational_checks.md"))


if __name__ == "__main__":
    main()

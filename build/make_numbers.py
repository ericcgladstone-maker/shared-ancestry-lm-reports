"""Canonical numbers sheet for the manuscript.

    python make_numbers.py

Reads only the canonical analysis outputs and writes manuscript_numbers.md
and manuscript_numbers.json in build/. Every value the manuscript cites
should come from a row of this sheet, by its key. Each row records the
source file and the JSON path it was read from, and the sheet records the
SHA-256 of every source file, so a value can be traced and a stale sheet
detected. Nothing is computed here beyond reading, except counts that are
stated as such.
"""
import hashlib
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join("runs", "full", "analysis")
SOURCES = {
    "text_only": os.path.join(A, "text_only.json"),
    "secondary": os.path.join(A, "secondary.json"),
    "inference": os.path.join(A, "inference.json"),
    "relational": os.path.join(A, "relational_checks.json"),
    "transfer": os.path.join(A, "cross_producer_transfer.json"),
    "replication": os.path.join("runs", "replication", "analysis.json"),
    "invariance": os.path.join(A, "invariance_corrected.json"),
    "review": os.path.join(A, "review_checks.json"),
    "depth": os.path.join("runs", "depth", "analysis.json"),
}
PRODUCERS = ("gemini-3.5-flash-lite", "claude-haiku-5-5", "gpt-6-luna")
READERS = ("claude-sonnet-5-5", "gpt-6.1-terra")
ROWS = []


def load():
    J, H = {}, {}
    for k, p in SOURCES.items():
        full = os.path.join(HERE, p)
        if os.path.exists(full):
            J[k] = json.load(open(full))
            H[k] = hashlib.sha256(open(full, "rb").read()).hexdigest()
    return J, H


def get(J, src, path):
    o = J[src]
    for p in path:
        o = o[p]
    return o


def row(key, J, src, path, desc, note=""):
    """One sheet row from a stats dict (auc/delta with lo and hi) or a scalar."""
    v = get(J, src, path)
    if isinstance(v, dict):
        est = v.get("auc", v.get("delta", v.get("gain")))
        r = {"key": key, "value": est, "lo": v.get("lo"), "hi": v.get("hi"), "n": v.get("n"),
             "p": v.get("p_upper", v.get("p_centered", v.get("p_gt_zero", v.get("p_gt_chance")))),
             "verdict": v.get("verdict"), "level": v.get("level")}
    else:
        r = {"key": key, "value": v}
    r.update({"description": desc, "source": SOURCES[src], "path": "/".join(map(str, path)), "note": note})
    ROWS.append(r)


def main():
    J, H = load()
    cond = "Conditional interval: world bootstrap on fixed out-of-fold predictions, 95% unless noted."

    # design counts, stated
    ROWS.append({"key": "design.worlds", "value": 60, "description": "Synthetic worlds in the full run", "source": "build/README.md",
                 "path": "", "note": "Design constant, not an estimate."})
    ROWS.append({"key": "design.replicates", "value": 3, "description": "Replicates per world in the full run", "source": "build/README.md",
                 "path": "", "note": "Design constant. Sets per structure and producer: 60 worlds x 3 replicates = 180."})

    # P3, primary
    row("P3.pooled", J, "text_only", ["P3", "pooled"], "IND vs DEP, primary producer, full access, neutral: pooled baseline AUC", cond)
    row("P3.relational", J, "text_only", ["P3", "pairwise"], "IND vs DEP, primary producer: relational model AUC", cond)
    row("P3.gain", J, "text_only", ["P3", "delta"], "IND vs DEP, primary producer: relational minus pooled AUC", cond)
    row("P3.n_sets", J, "text_only", ["P3", "n"], "IND vs DEP sets, primary producer")
    row("P3.refit.gain", J, "inference", ["P3_refit", "gain"], "P3 gain, refitted inference (point estimate)")
    row("P3.refit.lo", J, "inference", ["P3_refit", "lo"], "P3 gain, refitted world bootstrap 95% lower bound",
        "Refitted bootstrap holds the fold-level rarity construction fixed.")
    row("P3.refit.hi", J, "inference", ["P3_refit", "hi"], "P3 gain, refitted world bootstrap 95% upper bound")
    row("P3.refit.p", J, "inference", ["P3_refit", "p_centered"], "P3 gain, centered one-sided refitted bootstrap p")
    row("P3.refit.n_boot", J, "inference", ["P3_refit", "n_boot"], "P3 refitted bootstrap resamples completed")
    row("holm.P2", J, "inference", ["holm", "P2"], "P2 rejected at 0.05 after Holm")
    row("holm.P3", J, "inference", ["holm", "P3"], "P3 rejected at 0.05 after Holm")
    for p in PRODUCERS[1:]:
        for part, nm in (("pooled", "pooled"), ("pairwise", "relational"), ("delta", "gain")):
            row(f"P3.{p}.{nm}", J, "text_only", ["P3_other", p, part], f"IND vs DEP, {p}: {nm}", cond + " No refitted inference.")
    for part, nm in (("pooled", "pooled"), ("pairwise", "relational"), ("delta", "gain")):
        row(f"P3.partial.{nm}", J, "text_only", ["P3_partial", part], f"IND vs DEP, partial access, primary producer: {nm}",
            "Shared packages separate the structures by construction.")

    # three structures, per producer
    for p in PRODUCERS:
        for part, nm in (("three_class_aggregate_of_singles", "aggregate_of_singles"), ("three_class_pooled", "pooled"),
                         ("three_class_pairwise", "relational")):
            row(f"sets3.{p}.{nm}", J, "secondary", ["sets", p, part], f"Three structures, {p}: {nm} macro one-vs-one AUC", cond)
        row(f"sets3.{p}.relational_accuracy", J, "secondary", ["sets", p, "pairwise_metrics", "accuracy"],
            f"Three structures, {p}: relational model accuracy")

    # isolated-message leakage within sets (H7)
    for k in J["text_only"]["H7"]:
        row(f"H7.{k.replace('|', '.')}", J, "text_only", ["H7", k], f"One message per set, {k}: AUC with 90% interval and verdict",
            "Equivalence tolerance 0.43 to 0.57.")
    row("H7.worst_family_stratum", J, "secondary", ["H7_worst"], "Isolated-message stratum furthest from chance, by prompt family")
    for k in J["secondary"]["H7_family"]:
        row(f"H7family.{k.replace('|', '.')}", J, "secondary", ["H7_family", k], f"One message per set by prompt family, {k}: AUC, 90% interval",
            "Equivalence tolerance 0.43 to 0.57.")

    # specific relationships
    row("pairs.full", J, "secondary", ["pairs", "full"], "Same-root pair AUC, full access, primary producer", cond)
    row("pairs.partial", J, "secondary", ["pairs", "partial"], "Same-root pair AUC, partial access", "Shared packages contribute by construction.")
    row("config5.accuracy", J, "secondary", ["set_predictor", "accuracy"], "Five-configuration accuracy, all sets, primary producer")
    row("config5.odd_given_Y", J, "secondary", ["set_predictor", "mix_odd_correct"], "Odd message identified, conditional on the set being a Y")
    row("config5.same_root_auc", J, "secondary", ["set_predictor", "same_root_auc"], "Same-root AUC from configuration probabilities", cond)
    row("config5.Y_fully_correct", J, "relational", ["set_predictor", "own world excluded", "y_sets_fully_correct"],
        "Y sets assigned their exact configuration (of 180)", "Corrected rarity fit.")
    row("config5.three_structure_accuracy", J, "relational", ["set_predictor", "own world excluded", "three_structure_accuracy"],
        "Three-structure accuracy of the set model inside the five-configuration predictor", "Corrected rarity fit.")
    if "invariance" in J:
        inv = ["invariance", "orders", "random per set"]
        row("invariance.max_prob_diff", J, "invariance", inv + ["max_abs_prob_diff_vs_identity"],
            "Largest probability difference from generation order, random presentation order per set", "Corrected rarity fit.")
        row("invariance.sets_changed", J, "invariance", inv + ["sets_with_different_configuration"],
            "Sets whose predicted configuration changes under random presentation order", "Corrected rarity fit.")
        dY = J["invariance"]["gap_decomposition"]["truth Y"]
        for name, lab in (("correct", "correct"), ("odd_wrong", "three-structure Y, odd message wrong"),
                          ("demoted", "three-structure Y, demoted by the split"), ("structure_wrong", "three-structure wrong")):
            ROWS.append({"key": f"config5.decomp.Y.{name}", "value": int(dY.get(lab, 0)),
                         "description": f"Y sets (of 180): {lab}", "source": SOURCES["invariance"],
                         "path": f"gap_decomposition/truth Y/{lab}", "note": "Corrected rarity fit. A missing category is 0."})
        dO = J["invariance"]["gap_decomposition"]["truth three unconnected or out-star"]
        for name, lab in (("both_correct", "both correct"), ("five_only", "five-configuration correct only (Y split below it)"),
                          ("three_only", "three-structure correct only"), ("both_wrong", "both wrong")):
            ROWS.append({"key": f"config5.decomp.other.{name}", "value": int(dO.get(lab, 0)),
                         "description": f"IND or DEP sets (of 360): {lab}", "source": SOURCES["invariance"],
                         "path": f"gap_decomposition/truth three unconnected or out-star/{lab}", "note": "Corrected rarity fit. A missing category is 0."})

    # ablation, corrected fit
    for p in PRODUCERS:
        base = ["P3_ablation", "own world excluded", p]
        for v in get(J, "relational", base):
            if v in ("n_sets", "pooled"):
                continue
            row(f"ablation.{p}.{v}.auc", J, "relational", base + [v, "auc"], f"P3 ablation, {p}, {v}: AUC", cond)
            row(f"ablation.{p}.{v}.gain", J, "relational", base + [v, "gain_over_pooled"], f"P3 ablation, {p}, {v}: gain over pooled", cond)
            if v != "all three":
                row(f"ablation.{p}.{v}.change", J, "relational", base + [v, "change_from_all_three"],
                    f"P3 ablation, {p}, {v}: change from all three families", cond)
    for v in get(J, "relational", ["pair_ablation", "own world excluded"]):
        row(f"pair_ablation.{v}.auc", J, "relational", ["pair_ablation", "own world excluded", v, "same_root_auc"],
            f"Pair model, {v}: same-root AUC", cond)
        row(f"pair_ablation.{v}.odd_given_Y", J, "relational", ["pair_ablation", "own world excluded", v, "mix_odd_correct"],
            f"Pair model, {v}: odd message identified given Y")

    # single-message results (Study 1)
    for k in ("D0|NC0", "R1|NCR1"):
        for lrn in ("features", "embedding"):
            row(f"P1.{k.replace('|', '_')}.{lrn}", J, "text_only", ["P1", k, lrn], f"Dead-end control {k}, {lrn}: AUC with 90% interval",
                "Equivalence tolerance 0.43 to 0.57.")
            row(f"P1.{k.replace('|', '_')}.{lrn}.perm", J, "inference", ["perm", f"{k}|{lrn}"], f"Dead-end control {k}, {lrn}: refitted permutation",
                "Permutations from the 2026-10-31 11:14 run, reused because P1 does not use rarity.")
    for lrn in ("features", "embedding"):
        row(f"P2.{lrn}", J, "text_only", ["P2", lrn], f"Hub vs diamond, {lrn}: AUC", cond)
        row(f"P2.{lrn}.perm", J, "inference", ["perm", f"SD-same|SI-same|{lrn}"], f"Hub vs diamond, {lrn}: refitted permutation",
            "Permutations from the 2026-10-31 11:14 run, reused because P2 does not use rarity.")
    for k in J["replication"]["results"]:
        row(f"replication.{k.replace('|', '_')}", J, "replication", ["results", k], f"Replication, {k}")
    row("replication.control_later", J, "replication", ["timing", "control_later"], "Replication: pairs in which the control ran after the direct report (of 180)")
    for k in J["text_only"]["secondary"]:
        for lrn in ("features", "embedding"):
            row(f"study1.{k.replace(' ', '_')}.{lrn}", J, "text_only", ["secondary", k, lrn], f"Study 1 {k}, {lrn}: AUC", cond)
    for k in ("by_producer",):
        for p in PRODUCERS:
            row(f"P2.by_producer.{p}", J, "text_only", ["H6", k, p], f"Hub vs diamond, features, {p}", cond)
    row("P2.news", J, "text_only", ["H6", "news"], "Hub vs diamond, features, news genre", cond)
    for t in ("transfer_family", "transfer_producer", "transfer_genre"):
        for part in ("same", "transfer"):
            row(f"P2.{t}.{part}", J, "text_only", ["H6", t, part], f"Hub vs diamond, {t}: {part}", "Unpaired descriptive comparison, fixed penalty.")
    for t in ("transfer_family", "transfer_producer", "transfer_genre"):
        for part in ("same", "transfer"):
            row(f"R1R3.{t}.{part}", J, "secondary", ["H6_R1R3", t, part], f"R1 vs R3, {t}: {part}", "Unpaired descriptive comparison.")

    # prompted readers
    for rd in READERS:
        for arm in ("neutral", "conceal", "stripped"):
            for acc in ("full", "partial"):
                for task in ("IND_vs_DEP", "three_class"):
                    row(f"readers.{rd}.{acc}.{arm}.{task}", J, "text_only", ["readers", f"{rd}|structure|{acc}|{arm}", task],
                        f"Reader {rd}, {acc} access, {arm}: {task}", "Descriptive. Few-shot examples from training worlds.")

    # post hoc review checks
    if "review" in J:
        for p_ in PRODUCERS:
            for lrn in ("features", "embedding"):
                row(f"unshared.{p_}.{lrn}", J, "review", ["single_unshared", p_, lrn],
                    f"Single reports 2 and 3 only (never shared between IND and DEP), {p_}, {lrn}: AUC, 90% interval",
                    "Post hoc, added in response to the 2026-11-02 review. Equivalence band 0.43 to 0.57.")
            for k in J["review"]["unsupervised"][p_]:
                row(f"unsup.{p_}.{k}", J, "review", ["unsupervised", p_, k],
                    f"Untrained score {k}, IND vs DEP, {p_}: AUC", "Post hoc. No training. Rarity tables per fold, own world removed.")

    # deeper rewriting (runs/depth/PLAN.md), primary producer
    if "depth" in J:
        note = "Planned in runs/depth/PLAN.md before the run. Depth 1 is the full run's texts."
        for d in J["depth"]["depths"]:
            for part in ("pooled", "relational", "gain", "score", "relational_minus_score"):
                row(f"depth.{d}.{part}", J, "depth", ["depths", d, "binary", part],
                    f"Depth {d}, IND vs DEP, primary producer: {part}", note)
            for part in ("pooled", "relational"):
                row(f"depth.{d}.three.{part}", J, "depth", ["depths", d, "three", part],
                    f"Depth {d}, three structures, macro AUC: {part}", note)
            for lrn in ("features", "embedding"):
                row(f"depth.{d}.unshared.{lrn}", J, "depth", ["depths", d, "single_unshared", lrn],
                    f"Depth {d}, single reports 2 and 3, {lrn}: AUC, 90% interval", note + " Equivalence band 0.43 to 0.57.")
            for k in J["depth"]["depths"][d]["binary"]["unfitted"]:
                row(f"depth.{d}.unfitted.{k}", J, "depth", ["depths", d, "binary", "unfitted", k],
                    f"Depth {d}, unfitted score {k}, IND vs DEP: AUC", note)

    # cross-producer transfer
    if "transfer" in J:
        for task, out in J["transfer"]["tasks"].items():
            for pair, o in out.items():
                a, b = pair.split("|")
                tk = "IND_vs_DEP" if task == "IND against DEP" else "three_structures"
                for part in ("pooled", "relational", "relational_minus_pooled", "relational_minus_within"):
                    if part in o:
                        row(f"transfer.{tk}.{a}__to__{b}.{part}", J, "transfer", ["tasks", task, pair, part],
                            f"Transfer, {task}, trained on {a}, tested on {b}: {part}", cond)

    out = {"generated": time.strftime("%Y-%m-%d %H:%M"), "source_sha256": H, "rows": ROWS}
    with open(os.path.join(HERE, "manuscript_numbers.json"), "w") as fh:
        json.dump(out, fh, indent=1, default=float)

    def f(x):
        if x is None:
            return ""
        if isinstance(x, bool):
            return str(x)
        if isinstance(x, float):
            return f"{x:.4f}"
        return str(x)
    L = ["# Canonical numbers sheet", "",
         f"Generated by `make_numbers.py` at {out['generated']}. Cite every manuscript value by its key. Values are read from the "
         "canonical outputs listed below, never typed by hand, and each row names its source file and JSON path. Rerun this "
         "script after any analysis rerun. A source hash that differs from the one below means this sheet is stale.", "",
         "| Source | SHA-256 (first 12) |", "|---|---|"]
    L += [f"| `{SOURCES[k]}` | {h[:12]} |" for k, h in H.items()]
    missing = [k for k in SOURCES if k not in H]
    if missing:
        L += ["", "Missing sources (rows not generated): " + ", ".join(f"`{SOURCES[k]}`" for k in missing) + "."]
    L += ["", "| Key | Value | Interval | n | p | Verdict | Description | Source path | Note |", "|---|---|---|---|---|---|---|---|---|"]
    for r in ROWS:
        iv = f"[{f(r.get('lo'))}, {f(r.get('hi'))}]" + (f" ({r['level']:.0%})" if r.get("level") else "") if r.get("lo") is not None else ""
        L.append(f"| `{r['key']}` | {f(r['value'])} | {iv} | {f(r.get('n'))} | {f(r.get('p'))} | {f(r.get('verdict'))} | "
                 f"{r['description']} | `{r['source']}` {r['path']} | {r['note']} |")
    with open(os.path.join(HERE, "manuscript_numbers.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"wrote manuscript_numbers.md ({len(ROWS)} rows)")


if __name__ == "__main__":
    main()

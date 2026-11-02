"""Score the proposition judge against human coding (validation/PLAN.md).

    python score_validation.py validation/coding/*.json

Reads the coders' exported JSON logs (the latest record per coder and item
counts), validation/sample.json, and validation/judge/judgments.jsonl.
Writes validation/report.md and report.json. Coder IDs: A for the 240,
B for the 60, ADJ for adjudicated codes.
"""
import json
import os
import sys
from collections import Counter, defaultdict
from itertools import combinations

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from residue import analysis as an  # noqa: E402
from residue import judge_matcher as jm  # noqa: E402
from residue.keys import sha256  # noqa: E402

V = os.path.join(HERE, "validation")
REPORT_DIR = os.environ.get("VALIDATION_REPORT_DIR", V)  # set only to test the scorer away from the real report
MIN_CLASS = 30


def latest(paths):
    out = {}
    for p in paths:
        for r in json.load(open(p)):
            k = (r["coder"].strip().upper(), r["item_id"])
            if k not in out or r["time"] > out[k]["time"]:
                out[k] = r
    return out


def balanced_accuracy(h, j, classes):
    rec = [np.mean([a == b for a, b in zip(h, j) if a == c]) for c in classes if any(a == c for a in h)]
    return float(np.mean(rec)) if rec else float("nan")


def kappa(a, b, classes):
    n = len(a)
    if not n:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in classes)
    return float((po - pe) / (1 - pe)) if pe < 1 else float("nan")


def main():
    S = json.load(open(os.path.join(V, "sample.json")))["items"]
    item = {it["item_id"]: it for it in S}
    J = {}
    for line in open(os.path.join(V, "judge", "judgments.jsonl")):
        r = json.loads(line)
        if r.get("final"):
            J[(r["world"], r["text_hash"])] = r["result"]
    codes = latest(sys.argv[1:])

    def human(iid):
        return codes.get(("ADJ", iid)) or codes.get(("A", iid))

    def judge(iid):
        it = item[iid]
        return J.get((it["world"], sha256(it["body"])))

    # unit records: (item, kind, id, human, judge)
    units = []
    for iid, it in item.items():
        h, j = human(iid), judge(iid)
        if h is None or j is None:
            continue
        pkg = set(it["accessible"])
        for pid, v in h["facts"].items():
            units.append({"item": iid, "kind": "fact", "id": pid, "human": v, "judge": j["facts"][pid],
                          "accessible": pid in pkg, "producer": it["producer"], "fn": it["fn"],
                          "study": it["study"], "world": it["world"]})
        for n, v in h["disputes"].items():
            units.append({"item": iid, "kind": "dispute", "id": n, "human": v, "judge": j["disputes"].get(str(int(n) - 1), j["disputes"].get(int(n) - 1)),
                          "accessible": None, "producer": it["producer"], "fn": it["fn"], "study": it["study"],
                          "world": it["world"]})
    R = {"coded_items": len({u["item"] for u in units}), "judgments": {}}
    for kind, classes in (("fact", jm.STATES), ("dispute", jm.RESOLUTIONS)):
        U = [u for u in units if u["kind"] == kind]
        if not U:
            continue
        h, j, w = [u["human"] for u in U], [u["judge"] for u in U], [u["world"] for u in U]
        idx = np.arange(len(U))
        boot = an.world_bootstrap(lambda i: balanced_accuracy([h[k] for k in i], [j[k] for k in i], classes), w, n=2000)
        counts = Counter(h)
        out = {"n": len(U), "class_counts": dict(counts),
               "confusion": {a: {b: sum(1 for x, y in zip(h, j) if x == a and y == b) for b in classes} for a in classes},
               "balanced_accuracy": balanced_accuracy(h, j, classes),
               "ci": [float(np.nanquantile(boot, 0.025)), float(np.nanquantile(boot, 0.975))],
               "recall": {c: (float(np.mean([y == c for x, y in zip(h, j) if x == c])) if counts[c] else None) for c in classes},
               "not_validated_classes": [c for c in classes if counts[c] < MIN_CLASS]}
        out["criterion_met"] = bool(out["balanced_accuracy"] >= 0.80 and not out["not_validated_classes"])
        by = {}
        for key in ("producer", "fn", "study", "accessible"):
            g = defaultdict(list)
            for u in U:
                g[str(u[key])].append(u)
            by[key] = {k: {"n": len(v), "balanced_accuracy": balanced_accuracy([u["human"] for u in v], [u["judge"] for u in v], classes)}
                       for k, v in sorted(g.items())}
        out["by"] = by
        # coder agreement before adjudication
        a_, b_ = [], []
        for (c, iid), rb in codes.items():
            ra = codes.get(("A", iid))
            if c != "B" or ra is None:
                continue
            for k in (rb["facts"] if kind == "fact" else rb["disputes"]):
                a_.append((ra["facts"] if kind == "fact" else ra["disputes"])[k])
                b_.append((rb["facts"] if kind == "fact" else rb["disputes"])[k])
        out["kappa_A_B"] = kappa(a_, b_, classes)
        out["double_coded_units"] = len(a_)
        R["judgments"][kind] = out

    # linked diagnostics on facts
    F = {(u["item"], u["id"]): u for u in units if u["kind"] == "fact"}
    trans = Counter()
    both_stated, both_false_absent, miss_p, miss_c = 0, 0, [], []
    for iid, it in item.items():
        for pid_item in it["parent_items"]:
            for (i2, pid), u in F.items():
                if i2 != iid or (pid_item, pid) not in F:
                    continue
                p = F[(pid_item, pid)]
                hp, hc = p["human"] != "absent", u["human"] != "absent"
                jp, jc = p["judge"] != "absent", u["judge"] != "absent"
                trans[("present" if hp else "absent", "present" if hc else "absent", "judge " +
                       ("agrees" if (hp, hc) == (jp, jc) else "differs"))] += 1
                if p["human"] == "stated" and u["human"] == "stated":
                    both_stated += 1
                    miss_p.append(p["judge"] == "absent")
                    miss_c.append(u["judge"] == "absent")
                    both_false_absent += p["judge"] == "absent" and u["judge"] == "absent"
    R["transitions"] = {" / ".join(k): v for k, v in sorted(trans.items())}
    R["joint_false_absence_parent_child"] = {
        "facts_stated_in_both": both_stated, "judge_absent_in_both": int(both_false_absent),
        "expected_if_independent": float(np.mean(miss_p) * np.mean(miss_c) * both_stated) if both_stated else None}
    sib = defaultdict(list)
    for iid, it in item.items():
        if it["linked"] and it["linked"]["kind"] == "out-star" and it["linked"]["position"] > 0:
            sib[it["linked"]["unit"]].append(iid)
    pairs_stated, pairs_false, ma, mb = 0, 0, [], []
    for unit, ids in sib.items():
        for a, b in combinations(ids, 2):
            for (i2, pid), u in F.items():
                if i2 != a or (b, pid) not in F:
                    continue
                v = F[(b, pid)]
                if u["human"] == "stated" and v["human"] == "stated":
                    pairs_stated += 1
                    ma.append(u["judge"] == "absent")
                    mb.append(v["judge"] == "absent")
                    pairs_false += u["judge"] == "absent" and v["judge"] == "absent"
    pairs = sum(len(list(combinations(ids, 2))) for ids in sib.values())
    R["joint_false_absence_siblings"] = {
        "sibling_pairs": pairs, "facts_stated_in_both": pairs_stated, "judge_absent_in_both": int(pairs_false),
        "expected_if_independent": float(np.mean(ma) * np.mean(mb) * pairs_stated) if pairs_stated else None,
        "false_shared_omissions_per_pair": (pairs_false / pairs) if pairs else None}
    with open(os.path.join(REPORT_DIR, "report.json"), "w") as fh:
        json.dump(R, fh, indent=1)

    L = ["# Validation of the proposition judge", "",
         f"Scored by `score_validation.py` from {len(sys.argv) - 1} coder export(s). {R['coded_items']} items with human and "
         "judge codes. Criteria and procedure in `PLAN.md`. This report covers the natural sample only. The challenge set is "
         "scored separately.", ""]
    for kind, v in R["judgments"].items():
        cls = jm.STATES if kind == "fact" else jm.RESOLUTIONS
        L += [f"## {'Fact states' if kind == 'fact' else 'Dispute resolutions'}", "",
              f"{v['n']} judgments. Balanced accuracy {v['balanced_accuracy']:.3f} [{v['ci'][0]:.3f}, {v['ci'][1]:.3f}], "
              f"criterion 0.80: {'met' if v['criterion_met'] else 'not met'}. Classes with fewer than {MIN_CLASS} natural "
              f"instances: {', '.join(v['not_validated_classes']) or 'none'}. Kappa between coders A and B before "
              f"adjudication {v['kappa_A_B']:.3f} over {v['double_coded_units']} judgments.", "",
              "| Human \\ judge | " + " | ".join(cls) + " | Human count | Recall |", "|---" * (len(cls) + 3) + "|"]
        for a in cls:
            rc = v["recall"][a]
            L.append(f"| {a} | " + " | ".join(str(v["confusion"][a][b]) for b in cls) +
                     f" | {v['class_counts'].get(a, 0)} | {'' if rc is None else f'{rc:.3f}'} |")
        L.append("")
        for key, g in v["by"].items():
            L.append(f"By {key}: " + ", ".join(f"{k} {x['balanced_accuracy']:.3f} (n {x['n']})" for k, x in g.items()) + ".")
        L.append("")
    L += ["## Linked diagnostics", "", "Parent and child fact transitions (human parent, human child, judge):", ""]
    L += [f"- {k}: {v}" for k, v in R["transitions"].items()]
    pc, sb = R["joint_false_absence_parent_child"], R["joint_false_absence_siblings"]
    L += ["", f"Joint false absence, parent and child: of {pc['facts_stated_in_both']} facts the humans code as stated in both, "
          f"the judge codes {pc['judge_absent_in_both']} absent in both (independent errors would give "
          f"{pc['expected_if_independent']}).",
          f"Joint false absence, out-star siblings: of {sb['facts_stated_in_both']} facts stated in both members of "
          f"{sb['sibling_pairs']} sibling pairs, the judge codes {sb['judge_absent_in_both']} absent in both (independent: "
          f"{sb['expected_if_independent']}), or {sb['false_shared_omissions_per_pair']} false shared omissions per pair, "
          "to set against the full run's out-star excess.", ""]
    with open(os.path.join(REPORT_DIR, "report.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("wrote", os.path.join(REPORT_DIR, "report.md"))


if __name__ == "__main__":
    main()

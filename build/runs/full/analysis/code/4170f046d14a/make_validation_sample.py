"""Natural validation sample for the proposition judge (design Part VI).

    python make_validation_sample.py [--judge]

Draws 240 messages from the re-verification run (runs/verification_v2/),
which no full-run analysis uses, under the plan in validation/PLAN.md:
stratified by producer, study, and node function, spread over condition
groups and worlds, with linked units placed inside the strata (an out-star
set, its observation and three rewrites, and a three-relay chain, its
observation and three rewrites) so that parent-to-child transitions and
errors shared by siblings can be checked. 60 of the 240, chosen by the same
strata with linked units kept whole, are coded by the second coder.

Writes validation/sample.json (every item's metadata, kept from the
coders), validation/items_coder_A.json (240 items) and items_coder_B.json
(60 items), which show each message body and the record and nothing else.
The item order is shuffled per coder by the form. --judge then runs the
proposition judge (judge-v1, as used on the full run) on the 240 bodies and
writes validation/judge/judgments.jsonl, which coders never see.
The draw uses only the design labels, never the judge's output.
"""
import argparse
import json
import os
import random
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run  # noqa: E402
from residue import adapters  # noqa: E402
from residue import judge_matcher as jm  # noqa: E402
from residue.features import body  # noqa: E402
from residue.keys import canonical, sha256  # noqa: E402
from residue.store import CallStore  # noqa: E402

VER = os.path.join(HERE, "runs", "verification_v2")
OUT = os.path.join(HERE, "validation")
SEED = "validation|20261031"
# per producer: (study, node function) -> messages; 80 per producer, 240 in all
QUOTA = {("S1", "observe"): 16, ("S1", "rewrite"): 24, ("S1", "synthesize"): 16, ("S2", "observe"): 8, ("S2", "rewrite"): 16}
LINKED_PER_PRODUCER = {"out-star": 2, "chain": 2}
SECOND_CODER = 60
GROUP = {"D0": "direct report and controls", "NC0": "direct report and controls", "NCR1": "direct report and controls",
         "R1": "chains", "R3": "chains", "R5": "chains", "F1": "split-access hubs", "F2": "split-access hubs",
         "F3": "split-access hubs"}


def group_of(study, cond):
    if study == "S2":
        st, access, arm = cond.split("-")
        return f"{ {'IND': 'three unconnected sources', 'DEP': 'out-star', 'MIX': 'Y'}[st]}, {access} access"
    return GROUP.get(cond, "hub and diamond family")


def population():
    worlds = run.load_worlds("verification")
    wmap = {w.world_id: w for w in worlds}
    store = CallStore(os.path.join(VER, "calls.jsonl"))
    models = {k: run.Frozen(m) for k, m in run.producers(False, None).items()}
    results, failures, errors = run.run_blocks(run.plan(worlds, [0]), store, models, 8)
    assert not errors, errors
    msgs, units = {}, []
    for bid in sorted(results):
        study, wid, rep, genre, prod = bid.split("|")
        for cond in sorted(results[bid]):
            nodes = results[bid][cond]
            for n in nodes.values():
                m = msgs.setdefault(n.key, {"key": n.key, "world": wid, "study": study, "genre": genre, "producer": prod,
                                            "fn": n.fn, "conditions": [], "groups": [], "body": body(n.text),
                                            "parents": [nodes[p].key for p in n.parents]})
                if cond not in m["conditions"]:
                    m["conditions"].append(cond)
                g = group_of(study, cond)
                if g not in m["groups"]:
                    m["groups"].append(g)
                if n.fn == "observe":
                    m["package"] = list(n.package)
                    m["full_access"] = len(n.package) == len(wmap[wid].ids())
            if study == "S2" and cond == "DEP-full-neutral" and genre == "incident":
                obs = nodes["o1"].key
                units.append(("out-star", prod, wid, [obs] + [nodes[t].key for t in ("m1", "m2", "m3")]))
            if study == "S1" and cond == "R3" and genre == "incident":
                units.append(("chain", prod, wid, [nodes[x].key for x in ("o1", "r1", "r2", "r3")]))
    def accessible(key):
        m = msgs[key]
        if m["fn"] == "observe":
            return set(m["package"])
        return set().union(*(accessible(k) for k in m["parents"]))
    for m in msgs.values():
        m["accessible"] = sorted(accessible(m["key"]))
    return wmap, msgs, units


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    wmap, msgs, units = population()
    rng = random.Random(SEED)
    chosen, unit_of = [], {}
    taken_quota = defaultdict(int)
    # linked units first, on distinct worlds within each producer
    for prod in run.PRODUCERS:
        for kind, k in LINKED_PER_PRODUCER.items():
            cand = [u for u in units if u[0] == kind and u[1] == prod]
            rng.shuffle(cand)
            used = set()
            for u in cand:
                if len([1 for x in unit_of.values() if x["kind"] == kind and x["producer"] == prod]) >= k * 4:
                    break
                if u[2] in used or any(key in unit_of for key in u[3]):
                    continue
                used.add(u[2])
                uid = f"{kind}-{prod.split('-')[0]}-{u[2]}"
                for i, key in enumerate(u[3]):
                    unit_of[key] = {"unit": uid, "kind": kind, "position": i, "producer": prod}
                    chosen.append(key)
                    m = msgs[key]
                    taken_quota[(prod, m["study"], m["fn"])] += 1
    # the rest by stratum, round-robin over condition groups and worlds, no duplicate bodies
    bodies = {(msgs[k]["world"], msgs[k]["body"]) for k in chosen}
    for prod in run.PRODUCERS:
        for (study, fn), q in QUOTA.items():
            need = q - taken_quota[(prod, study, fn)]
            pool = [m for m in msgs.values() if m["producer"] == prod and m["study"] == study and m["fn"] == fn
                    and m["key"] not in unit_of]
            rng.shuffle(pool)
            bygroup = defaultdict(list)
            for m in pool:
                bygroup[m["groups"][0]].append(m)
            order = sorted(bygroup)
            worlds_used = defaultdict(int)
            while need > 0 and any(bygroup.values()):
                for g in order:
                    if need <= 0 or not bygroup[g]:
                        continue
                    bygroup[g].sort(key=lambda m: worlds_used[m["world"]])
                    m = bygroup[g].pop(0)
                    if (m["world"], m["body"]) in bodies:
                        continue
                    bodies.add((m["world"], m["body"]))
                    worlds_used[m["world"]] += 1
                    chosen.append(m["key"])
                    need -= 1
    assert len(chosen) == 240, len(chosen)

    items = []
    for key in chosen:
        m = msgs[key]
        iid = sha256(canonical({"seed": SEED, "key": key}))[:10]
        items.append({**{k: v for k, v in m.items() if k != "body"}, "item_id": iid, "linked": unit_of.get(key),
                      "parent_items": [], "body": m["body"]})
    by_key = {it["key"]: it for it in items}
    for it in items:
        it["parent_items"] = [by_key[p]["item_id"] for p in it["parents"] if p in by_key]

    # second coder: 60, one out-star unit and one chain unit kept whole, the rest by producer and function
    rng2 = random.Random(SEED + "|B")
    second = []
    for kind in ("out-star", "chain"):
        uids = sorted({it["linked"]["unit"] for it in items if it["linked"] and it["linked"]["kind"] == kind})
        u = rng2.choice(uids)
        second += [it["item_id"] for it in items if it["linked"] and it["linked"]["unit"] == u]
    rest = [it for it in items if it["item_id"] not in second]
    cells = defaultdict(list)
    for it in rest:
        cells[(it["producer"], it["study"], it["fn"])].append(it)
    for c in cells.values():
        rng2.shuffle(c)
    while len(second) < SECOND_CODER:
        for c in sorted(cells):
            if len(second) < SECOND_CODER and cells[c]:
                second.append(cells[c].pop()["item_id"])
    for it in items:
        it["second_coder"] = it["item_id"] in second

    def coder_item(it):
        w = wmap[it["world"]]
        by = w.by_id()
        return {"item_id": it["item_id"], "message": it["body"],
                "facts": [{"pid": p.pid, "text": p.text} for p in w.propositions],
                "disputes": [{"n": i + 1, "first": {"pid": x, "text": by[x].text}, "second": {"pid": y, "text": by[y].text}}
                             for i, (x, y) in enumerate(w.conflict_pairs())]}
    with open(os.path.join(OUT, "sample.json"), "w") as fh:
        json.dump({"seed": SEED, "source": "runs/verification_v2/calls.jsonl", "quota": {f"{k[0]}|{k[1]}": v for k, v in QUOTA.items()},
                   "items": items}, fh, indent=1, ensure_ascii=False)
    for name, ids, seed in (("A", [it["item_id"] for it in items], 11), ("B", second, 23)):
        with open(os.path.join(OUT, f"items_coder_{name}.json"), "w") as fh:
            json.dump({"seed": seed, "items": [coder_item(by) for by in items if by["item_id"] in ids]}, fh, indent=1,
                      ensure_ascii=False)
    print(f"sample: {len(items)} items, {sum(1 for i in items if i['linked'])} in linked units, second coder {len(second)}")

    if a.judge:
        ledger = adapters.Ledger(os.path.join(HERE, "smoke", "ledger.json"))
        judge = adapters.make("gpt-6.1-terra", ledger, role="reader", max_output_tokens=600)
        judge.cache_split = jm.CACHE_SPLIT
        os.makedirs(os.path.join(OUT, "judge"), exist_ok=True)
        log = jm.JudgeLog(os.path.join(OUT, "judge", "judgments.jsonl"))
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=16) as ex:
            out = list(ex.map(lambda it: log.judge(judge, wmap[it["world"]], it["body"]), items))
        print(f"judged {len(out)}, invalid after retry {sum(1 for r in out if not r['valid'])}; spend {ledger.spent}")


if __name__ == "__main__":
    main()

"""Walkthrough of one world's messages through the hub and the diamond.

    python make_walkthrough.py [--world W012] [--replicate 0]

Reads the full run's stored calls only and makes no producer calls. Every
text shown is the stored output, verbatim. Without --world the world is
drawn by a fixed seed from the 60 full-run worlds, so the example is not
chosen for how it looks. The script shows texts only. It does not mark
facts kept or dropped, because on this example the proposition matcher
called facts omitted that the messages state (2026-10-31), and human coding
has not validated it. Any reading of the texts is added by hand below the
generated part and labeled as such. Writes walkthroughs/hub_vs_diamond_<world>.md.
"""
import argparse
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run  # noqa: E402
from residue import graphs as gr  # noqa: E402
from residue.dispatcher import BlockSpec, run_block  # noqa: E402
from residue.features import parse_sources  # noqa: E402
from residue.prompts import instruction_of  # noqa: E402
from residue.store import CallStore  # noqa: E402

LABEL = {"o1": "Observer 1", "o2": "Observer 2", "o3": "Observer 3",
         "w1": "Relay 1", "w2": "Relay 2", "w3": "Relay 3", "syn": "Hub"}
MARK = "<!-- Everything below this line is written by hand and kept when the file is regenerated. -->"
SHAPES = {"SI-same": ("Hub", "three observers each see the whole event record and write independently, each report "
                             "passes through one relay, and a hub writer combines the three relayed reports"),
          "SD-same": ("Diamond", "one observer sees the whole event record, three relays each rewrite that one "
                                 "report, and a hub writer combines the three rewrites")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world")
    ap.add_argument("--replicate", type=int, default=0)
    a = ap.parse_args()
    worlds = run.load_worlds("full")
    w = next(x for x in worlds if x.world_id == a.world) if a.world else \
        random.Random(f"walkthrough|{run.RUN_SEED}").choice(worlds)
    fam = run.families(worlds, [a.replicate])[(w.world_id, a.replicate)]
    store = CallStore(os.path.join(HERE, "runs", "full", "calls.jsonl"))
    model = run.Frozen(run.producers(False, None)[(run.PRIMARY, "incident")])
    spec = BlockSpec(w, a.replicate, "incident", run.PRIMARY, fam, run.RUN_SEED)
    res = run_block(spec, {k: gr.STUDY1[k] for k in SHAPES}, store, model, model.version, run.req_params(model))
    by_id = w.by_id()
    pairs = w.conflict_pairs()

    L = [f"# Walkthrough: the hub and the diamond in world {w.world_id}", "",
         f"World {w.world_id} ({w.event_type}), replicate {a.replicate}, prompt family {fam}, primary producer "
         f"{run.PRIMARY}. " + ("The world was named on the command line." if a.world else
                              "The world was drawn at random by a fixed seed from the 60 full-run worlds.")
         + " Every message below is the stored output of the full run, verbatim (`runs/full/calls.jsonl`). The two "
         "structures share Observer 1 and Relay 1, which are one stored call each, so their texts are identical by "
         "construction.", "",
         "## The event record", "",
         "Every observer in both structures received all of these facts with their sources.", ""]
    for p in w.propositions:
        tag = " (core event)" if p.core else ""
        L.append(f"- {p.pid}{tag}: {p.text} *Source: {p.source}.*")
    L += ["", "Disputes, where two sources give incompatible accounts:", ""]
    for i, (x, y) in enumerate(pairs):
        L.append(f"- Dispute {i + 1}: {x} \"{by_id[x].text}\" against {y} \"{by_id[y].text}\"")
    L.append("")

    for cond, (shape, desc) in SHAPES.items():
        nodes = res[cond]
        L += [f"## {shape}", "", f"In the {shape.lower()}, {desc}.", ""]
        order = [n for n in ("o1", "o2", "o3", "w1", "w2", "w3", "syn") if n in nodes]
        for n in order:
            r = nodes[n]
            src = " from the event record" if r.fn == "observe" else \
                " from " + " and ".join(LABEL[p].lower() for p in r.parents) + "'s text"
            shared = " Shared with the hub (same stored call)." if cond == "SD-same" and n in ("o1", "w1") else ""
            L += [f"### {LABEL[n] if n != 'syn' else shape + ' writer'}{src}", "",
                  f"Instruction: \"{instruction_of(r.prompt).strip()}\"{shared}", "", "> " + r.text.strip().replace("\n", "\n> "), ""]
    L += ["## The two terminal messages compared", "",
          "| | Hub | Diamond |", "|---|---|---|"]
    terms = {c: res[c]["syn"].text for c in SHAPES}
    L.append("| Words | " + " | ".join(str(len(terms[c].split())) for c in SHAPES) + " |")
    L.append("| Sources line | " + " | ".join(
        (terms[c].rstrip().splitlines()[-1][len("Sources:"):].strip() if parse_sources(terms[c]) is not None else "absent")
        for c in SHAPES) + " |")
    L.append("")
    out = os.path.join(HERE, "walkthroughs", f"hub_vs_diamond_{w.world_id}.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    kept = ""
    if os.path.exists(out):
        old = open(out, encoding="utf-8").read()
        if MARK in old:
            kept = old[old.index(MARK):]  # the hand-written reading survives regeneration
    with open(out, "w") as fh:
        fh.write("\n".join(L) + "\n" + (kept or MARK + "\n"))
    print("wrote", out)


if __name__ == "__main__":
    main()

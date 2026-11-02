"""Build step 2: smoke test. A few real calls per model to check request
formatting, response parsing, store-once logic, spending caps, and tokens per
call. Costs well under a dollar. Run from build/ with the venv's python."""
import json
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from residue import adapters  # noqa: E402
from residue.features import parse_sources  # noqa: E402
from residue.keys import make_key  # noqa: E402
from residue.prompts import render_observe, render_with_inputs, target_words  # noqa: E402
from residue.store import CallStore, validate_output  # noqa: E402
from residue.worlds import Proposition, World  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smoke")
os.makedirs(OUT, exist_ok=True)

# The original study's W001, used only to exercise the plumbing.
W = World("SMOKE1", "generator shutdown", 0, [
    Proposition("p1", "Generator 2 at Site B shut down unexpectedly at 09:40.", True, "shift supervisor"),
    Proposition("p2", "The cooling loop ran above normal temperature for approximately 20 minutes before the shutdown.", False, "sensor record"),
    Proposition("p3", "The shutdown was caused by a cooling system malfunction.", False, "maintenance log", 0),
    Proposition("p4", "The shutdown was caused by a temperature sensor fault.", False, "safety officer", 0),
    Proposition("p5", "Routine sensor diagnostics were overdue.", False, "maintenance log"),
    Proposition("p6", "The east processing line was affected.", False, "dispatch note"),
    Proposition("p7", "The backup unit came online after 8 minutes.", False, "dispatch note"),
    Proposition("p8", "The west processing line remained operational.", False, "shift supervisor"),
])
PKG = tuple(p.pid for p in W.propositions)

PRODUCERS = ["gemini-3.5-flash-lite", "claude-haiku-5-5", "gpt-6-luna"]
READERS = ["claude-sonnet-5-5", "gpt-6.1-terra"]
GENRE = "incident"


def main():
    ledger = adapters.Ledger(os.path.join(OUT, "ledger.json"))
    store = CallStore(os.path.join(OUT, "calls.jsonl"))
    report = []
    tw = target_words(GENRE)
    for model in PRODUCERS:
        try:
            ad = adapters.make(model, ledger, role="producer")
            texts = {}
            steps = [("observe", "A:observe:0", None), ("rewrite", "A:rewrite:0", ["observe"]),
                     ("synthesize", "A:synthesize:0", ["observe", "rewrite"])]
            for name, tid, parents in steps:
                prompt = (render_observe(tid, W, PKG, GENRE) if parents is None
                          else render_with_inputs(tid, [texts[p] for p in parents], GENRE))
                k = make_key(study="SMOKE", world=W.world_id, replicate=0, genre=GENRE, producer=model, family="A",
                             role=name, template_id=tid, package_id=None, parent_keys=[p for p in (parents or [])])
                t0 = time.time()
                text = store.get_or_call(k, prompt, ad.version, ad.params(), ad, tw, {"node": name})
                texts[name] = text
                report.append({"model": model, "step": name, "words": len(text.split()),
                               "valid": validate_output(text, tw) is None, "sources": parse_sources(text),
                               "usage": ad.last_usage, "seconds": round(time.time() - t0, 1)})
        except Exception as e:  # report and continue with the next model
            report.append({"model": model, "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-600:]})
    sample = texts.get("synthesize") if "texts" in dir() else None
    for model in READERS:
        try:
            ad = adapters.make(model, ledger, role="reader", max_output_tokens=300)
            msg = next((r for r in report if r.get("step") == "rewrite" and "error" not in r), None)
            prompt = ('Here is a report. Reply with JSON only: {"synthesis": p} where p is your probability '
                      'from 0 to 1 that the report was written from several source documents.\n-----\n'
                      + (store.records and list(store.records.values())[1]["output"] or "Test report."))
            t0 = time.time()
            text = ad(prompt, 1)
            report.append({"model": model, "step": "reader", "reply": text[:200], "usage": ad.last_usage,
                           "seconds": round(time.time() - t0, 1)})
        except Exception as e:
            report.append({"model": model, "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-600:]})
    report.append({"ledger": ledger.spent})
    with open(os.path.join(OUT, "smoke_report.json"), "w") as fh:
        json.dump(report, fh, indent=1)
    for r in report:
        print(json.dumps({k: v for k, v in r.items() if k != "trace"})[:400])


if __name__ == "__main__":
    main()

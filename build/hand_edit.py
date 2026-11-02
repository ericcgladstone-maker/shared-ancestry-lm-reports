"""Apply hand edits to bank worlds, log them in worlds/hand_edits.jsonl with
the before and after text, and have the checker re-read each edited world.
Usage: hand_edit.py edits.json, where the file maps a world ID to
{pid: [text, source]} and optionally "_dispute0"/"_dispute1": {kind, about}
and "_sources": [the full replacement source list]."""
import dataclasses
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from residue import adapters  # noqa: E402
from residue.worldgen import CHECK_PROMPT, _load_json, check_problems, load_bank, record_for_check, save_bank  # noqa: E402
from residue.worlds import validate  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(HERE, "worlds")


def main(path, editor="Claude"):
    edits = json.load(open(path))
    ledger = adapters.Ledger(os.path.join(HERE, "smoke", "ledger.json"))
    checker = adapters.make("gpt-6.1-terra", ledger, role="checker", max_output_tokens=16000)
    out = []
    for w, m in load_bank(os.path.join(W, "bank.jsonl"), with_meta=True):
        e = edits.get(w.world_id)
        if e:
            before = {p.pid: [p.text, p.source] for p in w.propositions}
            w = dataclasses.replace(w, propositions=[dataclasses.replace(p, text=e[p.pid][0], source=e[p.pid][1])
                                                     if p.pid in e else p for p in w.propositions])
            validate(w)
            for k in ("_dispute0", "_dispute1"):
                if k in e:
                    m["disputes"][int(k[-1])] = e[k]
            if "_sources" in e:
                before["_sources"] = m["sources"]
                m["sources"] = e["_sources"]
            assert all(p.source in m["sources"] for p in w.propositions), w.world_id
            rec, _ = record_for_check(w, m)
            problems = check_problems(_load_json(checker(CHECK_PROMPT.format(record=rec), 0)))
            m.update(check_problems=problems, flagged=bool(problems),
                     hand_edited=sorted(set(m.get("hand_edited", [])) | {k for k in e if not k.startswith("_")}))
            with open(os.path.join(W, "hand_edits.jsonl"), "a") as fh:
                fh.write(json.dumps({"world_id": w.world_id, "editor": editor, "time": time.time(),
                                     "edits": {k: {"before": before.get(k), "after": v} for k, v in e.items()},
                                     "recheck": problems}) + "\n")
            print(w.world_id, problems)
        out.append((w, m))
    save_bank(out, os.path.join(W, "bank.jsonl"))
    print("flagged:", [w.world_id for w, m in out if m.get("flagged")], "| spend:", ledger.spent)


if __name__ == "__main__":
    main(sys.argv[1])

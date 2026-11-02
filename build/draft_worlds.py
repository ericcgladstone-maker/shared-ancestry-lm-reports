"""Draft the 70-world bank with Claude Sonnet 5.5, assign the 10 verification
worlds and the evaluation folds, and write a review document. Run once."""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from residue import adapters  # noqa: E402
from residue.analysis import assign_folds  # noqa: E402
from residue.worldgen import draft_bank, save_bank  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "worlds")
os.makedirs(OUT, exist_ok=True)


def main():
    ledger = adapters.Ledger(os.path.join(OUT, "..", "smoke", "ledger.json"))
    ad = adapters.make("claude-sonnet-5-5", ledger, role="drafter", max_output_tokens=8000)
    checker = adapters.make("gpt-6.1-terra", ledger, role="checker", max_output_tokens=16000)
    bank = draft_bank(lambda prompt: ad(prompt, 0), os.path.join(OUT, "draft_log.jsonl"),
                      check=lambda prompt: checker(prompt, 0), workers=14)
    save_bank(bank, os.path.join(OUT, "bank.jsonl"))
    rng = random.Random(20261030)
    by_type = {}
    for w, _ in bank:
        by_type.setdefault(w.event_type, []).append(w.world_id)
    types = sorted(by_type)
    rng.shuffle(types)
    verification = sorted(rng.choice(by_type[t]) for t in types[:10])  # ten worlds from ten different event types
    full = [w.world_id for w, _ in bank if w.world_id not in verification]
    folds = assign_folds(full, {w.world_id: w.event_type for w, _ in bank}, k=5, seed=20261030)
    with open(os.path.join(OUT, "assignment.json"), "w") as fh:
        json.dump({"verification": verification, "folds": folds}, fh, indent=1)
    flagged = [w.world_id for w, m in bank if m.get("flagged")]
    print("worlds:", len(bank), "| flagged:", flagged, "| verification:", verification, "| spend:", ledger.spent)


if __name__ == "__main__":
    main()

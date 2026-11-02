"""Repair flagged worlds in place. A flagged world kept its best draft, which
still had checker defects. The drafter receives that draft and the defects,
with each labeled sentence quoted, and returns the record with only those
sentences changed. The checker then reads the repaired world. Up to two
repair rounds per world. Every round is logged in worlds/repair_log.jsonl,
and the repaired raw draft replaces the kept one in the bank."""
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from residue import adapters  # noqa: E402
from residue.worldgen import (CHECK_PROMPT, _load_json, check_problems, load_bank, parse_draft,  # noqa: E402
                              record_for_check, save_bank)

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(HERE, "worlds")

REPAIR_PROMPT = """Below is a fictional event record in JSON, written for a study of how reports change as they are passed between writers, followed by defects a checker found in it. Each record has two disputes whose claims must concern the same thing, be incompatible, come from sources placed to know them, and be balanced, with no other sentence favoring either claim. Every sentence's source must be able to observe or document what it says.

Record:
{raw}

Defects:
{defects}

Return the complete record as JSON in exactly the same format, fixing every defect with the smallest change: reassign a sentence to a source on the list that could know it, reword the sentence, or remove the detail that favors a claim. Do not change any sentence that has no defect, do not add or remove sentences, and keep the source list unless a defect cannot be fixed otherwise. Return only the JSON."""


def quote_defects(problems, labels, by):
    """Replace checker labels such as F3 or D1a with the quoted sentence."""
    def sub(m):
        pid = labels.get(m.group(0))
        return f'"{by[pid].text}" ({by[pid].source})' if pid else m.group(0)
    return "\n".join("- " + re.sub(r"\b(C|F\d{1,2}|D[12][ab])\b", sub, p) for p in problems)


def repair(wid, kept, drafter, checker, log):
    raw, problems = kept["raw"], kept["problems"]
    for rnd in range(2):
        w, m = parse_draft(raw, wid, kept["event_type"], int(wid[1:]))
        _, labels = record_for_check(w, m)
        prompt = REPAIR_PROMPT.format(raw=raw, defects=quote_defects(problems, labels, w.by_id()))
        new_raw = drafter(prompt, 0)
        try:
            w2, m2 = parse_draft(new_raw, wid, kept["event_type"], int(wid[1:]))
            record, _ = record_for_check(w2, m2)
            verdict = checker(CHECK_PROMPT.format(record=record), 0)
            new_problems = check_problems(_load_json(verdict))
            err = None
        except Exception as e:
            new_problems, verdict, err = None, "", f"{type(e).__name__}: {e}"
        changed = None
        if err is None:
            old_texts = {(p.text, p.source) for p in w.propositions}
            changed = [p.pid for p in w2.propositions if (p.text, p.source) not in old_texts]
        log({"world_id": wid, "round": rnd, "prompt": prompt, "raw": new_raw, "verdict": verdict,
             "problems": new_problems, "error": err, "changed": changed})
        if err is None:
            raw, problems = new_raw, new_problems
            if not problems:
                return raw, [], True
    return raw, problems, False


def main():
    ledger = adapters.Ledger(os.path.join(HERE, "smoke", "ledger.json"))
    drafter = adapters.make("claude-sonnet-5-5", ledger, role="drafter", max_output_tokens=8000)
    checker = adapters.make("gpt-6.1-terra", ledger, role="checker", max_output_tokens=16000)
    bank = load_bank(os.path.join(W, "bank.jsonl"), with_meta=True)
    # The kept draft is the accepted log entry whose text matches the bank. The
    # log also holds entries from an overlapping run (README, world bank
    # findings), so the last accepted entry is not necessarily the bank's.
    pre = {w.world_id: w for w in load_bank(os.path.join(W, "bank_before_repair.jsonl"))}
    kept = {}
    for line in open(os.path.join(W, "draft_log.jsonl")):
        r = json.loads(line)
        if r["accepted"] and r["raw"]:
            try:
                w0, _ = parse_draft(r["raw"], r["world_id"], r["event_type"], int(r["world_id"][1:]))
            except ValueError:
                continue
            if [p.text for p in w0.propositions] == [p.text for p in pre[r["world_id"]].propositions]:
                kept[r["world_id"]] = r
    import threading
    lock = threading.Lock()
    log_path = os.path.join(W, "repair_log.jsonl")

    def log(rec):
        with lock:
            with open(log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")

    flagged = sys.argv[1:] or [w.world_id for w, m in bank if m.get("flagged")]
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = dict(zip(flagged, pool.map(lambda wid: repair(wid, kept[wid], drafter, checker, log), flagged)))
    out = []
    for w, m in bank:
        if w.world_id in results:
            raw, problems, ok = results[w.world_id]
            w, m2 = parse_draft(raw, w.world_id, w.event_type, w.index)
            m2.update(check_problems=problems, flagged=not ok, repaired=True)
            m = m2
        out.append((w, m))
    save_bank(out, os.path.join(W, "bank.jsonl"))
    still = [w.world_id for w, m in out if m.get("flagged")]
    print("repaired:", len(results), "| still flagged:", still, "| spend:", ledger.spent)


if __name__ == "__main__":
    main()

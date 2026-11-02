"""Run the proposition judge on the full run's primary-producer messages.

    python judge_run.py

Order, so that a spending stop leaves the most needed sets complete: Study 2
full access neutral (the inherited-deviation account of H8), Study 1 hub and
diamond, Study 2 partial access neutral, then the chains of 1, 3, and 5
relays. Each distinct message body is judged once. Resumable. Writes
runs/full/judge/judgments.jsonl.
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyze  # noqa: E402
import run  # noqa: E402
from residue import adapters  # noqa: E402
from residue import judge_matcher as jm  # noqa: E402
from residue.features import body  # noqa: E402


def main():
    worlds, s1, s2, _ = analyze.load()
    wmap = {w.world_id: w for w in worlds}
    stages = [
        [(r["world"], t) for r in s2 if r["producer"] == run.PRIMARY and r["access"] == "full" and r["arm"] == "neutral"
         for t in r["texts"]],
        [(r["world"], r["text"]) for r in s1 if r["producer"] == run.PRIMARY and r["genre"] == "incident"
         and r["cond"] in ("SI-same", "SD-same")],
        [(r["world"], t) for r in s2 if r["producer"] == run.PRIMARY and r["access"] == "partial" and r["arm"] == "neutral"
         for t in r["texts"]],
        [(r["world"], r["text"]) for r in s1 if r["producer"] == run.PRIMARY and r["genre"] == "incident"
         and r["cond"] in ("R1", "R3", "R5")],
    ]
    ledger = adapters.Ledger(os.path.join(HERE, "smoke", "ledger.json"))
    judge = adapters.make("gpt-6.1-terra", ledger, role="reader", max_output_tokens=600)
    judge.cache_split = jm.CACHE_SPLIT
    log = jm.JudgeLog(os.path.join(analyze.FULL, "judge", "judgments.jsonl"))
    seen = set()
    for i, jobs in enumerate(stages):
        todo = []
        for wid, t in jobs:
            b = body(t)
            if (wid, b) not in seen:
                seen.add((wid, b))
                todo.append((wid, b))
        with ThreadPoolExecutor(max_workers=16) as ex:
            out = list(ex.map(lambda j: log.judge(judge, wmap[j[0]], j[1]), todo))
        print(f"stage {i + 1}: {len(todo)} messages, invalid after retry {sum(1 for r in out if not r['valid'])}; "
              f"spend {ledger.spent}", flush=True)


if __name__ == "__main__":
    main()

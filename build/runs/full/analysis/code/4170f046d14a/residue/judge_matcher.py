"""Proposition judge (replaces the embedding matcher for anchored measures).

The embedding matcher of residue/matcher.py could not separate paraphrase
from unrelated text with nomic-embed-text (unrelated propositions reach a
cosine of 0.81, and paraphrases of stated facts fell below the 0.86
threshold; build README, 2026-10-31). This judge gives a language model the
world record and one message body and asks, for every proposition, whether
the message states it, states it with a changed detail, states it with
added doubt, or does not state it, and how each dispute is handled.

The judge never sees a condition, structure, or other message. The Sources
line is removed before judging, so attribution cannot affect the states.
Like the matcher it replaces, it is an instrument that human coding
validates (design Part VI). Its outputs are anchored measures and never
enter a text-only model.
"""
import json
import os
import re
import threading
import time
from typing import Dict, Optional

from .keys import canonical, sha256
from .worlds import World

STATES = ("stated", "changed", "doubted", "absent")
RESOLUTIONS = ("first", "second", "both", "neither")
VERSION = "judge-v1"
CACHE_SPLIT = "\nMessage to judge"

PROMPT = """You will compare a short report with the record of the event it describes. The record lists numbered facts. Some facts come in disputed pairs, where two sources give incompatible accounts.

For each fact, decide how the report treats it:
- "stated": the report states the fact, in any wording. Paraphrase, summary, and a different but equivalent form of a number or time count as stated.
- "changed": the report states the fact but with a different value, person, place, time, cause, or other detail that contradicts the record.
- "doubted": the report states the fact but presents it as uncertain, disputed, or unconfirmed when the record does not.
- "absent": the report does not state the fact.

For each disputed pair, decide how the report handles it:
- "first": it gives only the first account.
- "second": it gives only the second account.
- "both": it gives both accounts, or says the accounts differ and gives both values.
- "neither": it gives neither account.

Judge only what the report says. Do not reward or penalize style, length, or wording.

Record:
{facts}

Disputed pairs:
{disputes}
"""
ITEM = """
Message to judge:
-----
{text}
-----

Reply with JSON only, in this form: {{"facts": {{"p00": "stated", ...}}, "disputes": {{"1": "neither", ...}}}}, with every fact id and every dispute number."""


def render(world: World, text: str) -> str:
    facts = "\n".join(f"{p.pid}: {p.text}" for p in world.propositions)
    by = world.by_id()
    disputes = "\n".join(f"{i + 1}. first: {a} ({by[a].text}) / second: {b} ({by[b].text})"
                         for i, (a, b) in enumerate(world.conflict_pairs()))
    return PROMPT.format(facts=facts, disputes=disputes) + ITEM.format(text=text.strip())


def parse(reply: str, world: World) -> Optional[Dict]:
    m = re.search(r"\{.*\}", reply or "", re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
        facts = {p.pid: str(d["facts"][p.pid]).lower() for p in world.propositions}
        disp = {i: str(d["disputes"][str(i + 1)]).lower() for i in range(len(world.conflict_pairs()))}
    except (ValueError, KeyError, TypeError):
        return None
    if any(v not in STATES for v in facts.values()) or any(v not in RESOLUTIONS for v in disp.values()):
        return None
    return {"facts": facts, "disputes": disp}


class JudgeLog:
    """Append-only, resumable by (version, world, text)."""

    def __init__(self, path: str):
        self.path = path
        self.done: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        if os.path.exists(path):
            for line in open(path, encoding="utf-8"):
                r = json.loads(line)
                if r.get("final"):
                    self.done[r["item_key"]] = r

    def judge(self, model, world: World, body_text: str) -> Dict:
        ik = sha256(canonical({"v": VERSION, "world": world.world_id, "text": sha256(body_text)}))
        if ik in self.done:
            return self.done[ik]
        prompt = render(world, body_text)
        rec = None
        for attempt in range(2):
            t0 = time.time()
            reply = model(prompt, attempt + 1)
            out = parse(reply, world)
            final = out is not None or attempt == 1
            rec = {"item_key": ik, "version": VERSION, "world": world.world_id, "text_hash": sha256(body_text),
                   "attempt": attempt, "reply": reply, "result": out, "valid": out is not None, "final": final,
                   "model": getattr(model, "version", "?"), "usage": dict(getattr(model, "last_usage", {}) or {}),
                   "seconds": round(time.time() - t0, 2), "time": time.time()}
            with self._lock:
                with open(self.path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if final:
                break
        with self._lock:
            self.done[ik] = rec
        return rec

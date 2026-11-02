"""Prompted readers (design Part VIII, build spec section 11).

A reader receives neutral descriptions of the label classes, labeled
examples from training worlds (the same for every test item in a fold, in
an order shuffled by the fold seed), and the item. It returns a probability
for each label as JSON. An invalid reply is retried once; if it is invalid
again the item is scored as a uniform distribution and counted.

Class descriptions never use condition names. The labels the reader sees
are letters. Messages are shown whole, including the Sources line.
"""
import json
import os
import random
import re
import threading
import time
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .keys import canonical, sha256

# Study 1 single-message tasks. Each class is (condition, description).
TASKS: Dict[str, List[Tuple[str, str]]] = {
    "independence": [
        ("SI-same", "The message combines three reports. Each report was rewritten from its own observation of the "
                    "event, and the three observations were written separately."),
        ("SD-same", "The message combines three reports. All three were rewritten from one single observation of "
                    "the event."),
    ],
    "depth": [
        ("R1", "The message was written from the event record and then rewritten once."),
        ("R3", "The message was written from the event record and then rewritten three times in succession."),
        ("R5", "The message was written from the event record and then rewritten five times in succession."),
    ],
    "partition": [
        ("F1", "The message combines the report of one observer, who saw the whole event record."),
        ("F2", "The message combines the reports of two observers, each of whom saw a different part of the "
               "event record."),
        ("F3", "The message combines the reports of three observers, each of whom saw a different part of the "
               "event record."),
    ],
    "inert": [
        ("D0", "The two classes were produced by procedures that are described only by the examples."),
        ("NC0", "The two classes were produced by procedures that are described only by the examples."),
    ],
}
PER_CLASS = {2: 8, 3: 6}  # 16 examples for binary tasks, 18 for three-class tasks
LETTERS = "ABC"

HEAD = ("You will classify a message by how it was produced. Every message is a report about a fictional event. "
        "The possible classes are:\n{classes}\n\nHere are labeled examples.\n\n{examples}\n\n"
        "Now classify this message.\n-----\n{item}\n-----\n"
        "Reply with JSON only, giving your probability for each class, for example {fmt}. "
        "The probabilities must sum to 1.")


def render(task: str, examples: Sequence[Tuple[str, str]], item: str) -> str:
    """examples are (text, condition) pairs, already in their presented order."""
    classes = TASKS[task]
    letter = {c: LETTERS[i] for i, (c, _) in enumerate(classes)}
    if task == "inert":
        cls = "\n".join(f"{LETTERS[i]}: a message of class {LETTERS[i]}." for i in range(len(classes)))
        cls += "\n" + classes[0][1]
    else:
        cls = "\n".join(f"{LETTERS[i]}: {d}" for i, (_, d) in enumerate(classes))
    ex = "\n\n".join(f"Example {j + 1} (class {letter[c]}):\n-----\n{t.strip()}\n-----" for j, (t, c) in enumerate(examples))
    fmt = "{" + ", ".join(f'"{LETTERS[i]}": 0.{5 if len(classes) == 2 else 3}' for i in range(len(classes))) + "}"
    return HEAD.format(classes=cls, examples=ex, item=item.strip(), fmt=fmt)


def draw_examples(task: str, pool: Dict[str, List[Tuple[str, str]]], fold_seed: str) -> List[Tuple[str, str]]:
    """pool maps condition to (world_id, text) from training worlds only."""
    classes = [c for c, _ in TASKS[task]]
    k = PER_CLASS[len(classes)]
    rng = random.Random(f"examples|{task}|{fold_seed}")
    out = []
    for c in classes:
        cands = sorted(pool[c])
        assert len(cands) >= k, f"{task}: {len(cands)} training examples for {c}, need {k}"
        out += [(t, c) for _, t in rng.sample(cands, k)]
    rng.shuffle(out)
    return out


def parse(reply: str, n: int) -> Optional[List[float]]:
    m = re.search(r"\{[^{}]*\}", reply or "")
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
        p = [float(d[LETTERS[i]]) for i in range(n)]
    except (ValueError, KeyError, TypeError):
        return None
    if any(x < 0 for x in p) or not 0.95 <= sum(p) <= 1.05:
        return None
    s = sum(p)
    return [x / s for x in p]


class ReaderLog:
    """Append-only log of reader calls, resumable by item key."""

    def __init__(self, path: str, extra: Optional[Dict] = None):
        self.path = path
        self.extra = dict(extra or {})
        self.done: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        if os.path.exists(path):
            for line in open(path, encoding="utf-8"):
                r = json.loads(line)
                if r.get("final"):
                    self.done[r["item_key"]] = r

    def read(self, reader: Callable[[str, int], str], reader_name: str, task: str, item_id: str, prompt: str,
             truth: str) -> Dict:
        ik = sha256(canonical({"reader": reader_name, "task": task, "item": item_id, "prompt": sha256(prompt)}))
        if ik in self.done:
            return self.done[ik]
        n = len(TASKS[task])
        rec = None
        for attempt in range(2):
            t0 = time.time()
            reply = reader(prompt, attempt + 1)
            probs = parse(reply, n)
            final = probs is not None or attempt == 1
            rec = {"item_key": ik, "reader": reader_name, "task": task, "item": item_id, "attempt": attempt,
                   "truth": truth, "prompt": prompt, "reply": reply, "probs": probs or [1 / n] * n,
                   "valid": probs is not None, "final": final, "usage": dict(getattr(reader, "last_usage", {}) or {}),
                   "seconds": round(time.time() - t0, 2), "time": time.time(), **self.extra}
            with self._lock:
                with open(self.path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if final:
                break
        with self._lock:
            self.done[ik] = rec
        return rec

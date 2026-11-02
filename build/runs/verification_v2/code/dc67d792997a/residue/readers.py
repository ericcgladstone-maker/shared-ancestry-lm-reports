"""Prompted readers (design Part VIII, build spec section 11).

A reader receives neutral descriptions of the label classes, labeled
examples from training worlds (the same for every test item in a fold, in
an order shuffled by the fold seed), and the item. It returns a probability
for each label as JSON. An invalid reply is retried once; if it is invalid
again the item is scored as a uniform distribution and counted.

Class descriptions never use condition names. The labels the reader sees
are letters. Messages are shown whole, including the Sources line.

Study 1 tasks read one message. The Study 2 task reads a set of three
messages in random presented order and returns a probability for each of
five configurations (design Part V-A): IND, DEP, and MIX with the odd
message in each presented position, so the structure probabilities and the
pairwise same-root probabilities are sums over one distribution.

Everything before "Now classify this" is the same for every item in a task
and fold, so providers can cache it (CACHE_SPLIT).
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
    "inert_rewrite": [
        ("R1", "The two classes were produced by procedures that are described only by the examples."),
        ("NCR1", "The two classes were produced by procedures that are described only by the examples."),
    ],
    "independence_div": [
        ("SI-div", "The message combines three reports. Each report was rewritten from its own observation of the "
                   "event, and the three observers saw different, partly overlapping parts of the event record."),
        ("SD-div", "The message combines three reports. All three were rewritten from one single observation of "
                   "the event."),
    ],
    "independence_post1": [
        ("SI-same+1", "Three reports, each rewritten from its own separately written observation of the event, were "
                      "combined into one message, which was then rewritten once."),
        ("SD-same+1", "Three reports, all rewritten from one single observation of the event, were combined into one "
                      "message, which was then rewritten once."),
    ],
    "independence_post3": [
        ("SI-same+3", "Three reports, each rewritten from its own separately written observation of the event, were "
                      "combined into one message, which was then rewritten three times in succession."),
        ("SD-same+3", "Three reports, all rewritten from one single observation of the event, were combined into one "
                      "message, which was then rewritten three times in succession."),
    ],
    "composition": [
        ("SD-same+3", "Three reports, all rewritten from one single observation of the event, were combined into one "
                      "message, which was then rewritten three times in succession."),
        ("R5", "The message was written from the event record and then rewritten five times in succession."),
    ],
    "depth13": [
        ("R1", "The message was written from the event record and then rewritten once."),
        ("R3", "The message was written from the event record and then rewritten three times in succession."),
    ],
}
INERT = {"inert", "inert_rewrite"}
# Tasks read on each genre's terminals. Together the primary-genre tasks read every Study 1 condition.
GENRE_TASKS = {"incident": ["independence", "depth", "partition", "inert", "inert_rewrite", "independence_div",
                            "independence_post1", "independence_post3", "composition"],
               "news": ["independence", "depth13"]}

# Study 2: one structure label per set, read as five configurations.
SET_TASK = "structure"
SET_CLASSES: List[Tuple[str, str]] = [
    ("IND", "The three messages were produced independently. Each was rewritten from its own observation of the "
            "event."),
    ("DEP", "All three messages were rewritten from one single observation of the event."),
    ("MIX1", "Messages 2 and 3 were rewritten from one shared observation of the event, and Message 1 was rewritten "
             "from a separate observation."),
    ("MIX2", "Messages 1 and 3 were rewritten from one shared observation of the event, and Message 2 was rewritten "
             "from a separate observation."),
    ("MIX3", "Messages 1 and 2 were rewritten from one shared observation of the event, and Message 3 was rewritten "
             "from a separate observation."),
]
SET_PER_STRUCTURE = 6  # 18 example sets, six per structure

PER_CLASS = {2: 8, 3: 6}  # 16 examples for binary tasks, 18 for three-class tasks
LETTERS = "ABCDE"
CACHE_SPLIT = "\nNow classify this"


def classes_of(task: str) -> List[Tuple[str, str]]:
    return SET_CLASSES if task == SET_TASK else TASKS[task]

HEAD = ("You will classify a message by how it was produced. Every message is a report about a fictional event. "
        "The possible classes are:\n{classes}\n\nHere are labeled examples.\n\n{examples}\n\n"
        "Now classify this message.\n-----\n{item}\n-----\n"
        "Reply with JSON only, giving your probability for each class, for example {fmt}. "
        "The probabilities must sum to 1.")


def render(task: str, examples: Sequence[Tuple[str, str]], item: str) -> str:
    """examples are (text, condition) pairs, already in their presented order."""
    classes = TASKS[task]
    letter = {c: LETTERS[i] for i, (c, _) in enumerate(classes)}
    if task in INERT:
        cls = "\n".join(f"{LETTERS[i]}: a message of class {LETTERS[i]}." for i in range(len(classes)))
        cls += "\n" + classes[0][1]
    else:
        cls = "\n".join(f"{LETTERS[i]}: {d}" for i, (_, d) in enumerate(classes))
    ex = "\n\n".join(f"Example {j + 1} (class {letter[c]}):\n-----\n{t.strip()}\n-----" for j, (t, c) in enumerate(examples))
    fmt = "{" + ", ".join(f'"{LETTERS[i]}": 0.{5 if len(classes) == 2 else 3}' for i in range(len(classes))) + "}"
    return HEAD.format(classes=cls, examples=ex, item=item.strip(), fmt=fmt)


SET_HEAD = ("You will classify a set of three messages by how they were produced. Every message is a report about "
            "a fictional event, and the three messages in a set are about the same event. The possible classes "
            "are:\n{classes}\n\nHere are labeled example sets.\n\n{examples}\n\n"
            "Now classify this set.\n{item}\n"
            "Reply with JSON only, giving your probability for each class, for example {fmt}. "
            "The probabilities must sum to 1.")


def _set_block(texts: Sequence[str]) -> str:
    return "\n".join(f"Message {i + 1}:\n-----\n{t.strip()}\n-----" for i, t in enumerate(texts))


def render_set(examples: Sequence[Tuple[Sequence[str], str]], item: Sequence[str]) -> str:
    """examples are (three texts in presented order, configuration) pairs, already in their presented order."""
    letter = {c: LETTERS[i] for i, (c, _) in enumerate(SET_CLASSES)}
    cls = "\n".join(f"{LETTERS[i]}: {d}" for i, (_, d) in enumerate(SET_CLASSES))
    ex = "\n\n".join(f"Example set {j + 1} (class {letter[c]}):\n{_set_block(ts)}" for j, (ts, c) in enumerate(examples))
    fmt = "{" + ", ".join(f'"{LETTERS[i]}": 0.2' for i in range(len(SET_CLASSES))) + "}"
    return SET_HEAD.format(classes=cls, examples=ex, item=_set_block(item), fmt=fmt)


def present(texts: Sequence[str], structure: str, seed: str) -> Tuple[List[str], str]:
    """Permute a set's messages (in generation slots 1 to 3) into presented
    order and return them with the configuration. MIX's odd message is the
    one in generation slot 3."""
    order = [0, 1, 2]
    random.Random(f"present|{seed}").shuffle(order)
    shown = [texts[i] for i in order]
    config = structure if structure != "MIX" else f"MIX{order.index(2) + 1}"
    return shown, config


def config_probs(probs: Sequence[float]) -> Dict[str, object]:
    """Structure probabilities and pairwise same-root probabilities, by
    presented position, as sums over the five configurations. A pair shares
    a root under DEP and under the MIX configuration whose odd message is
    the third one."""
    p = dict(zip([c for c, _ in SET_CLASSES], probs))
    pair = {(1, 2): p["DEP"] + p["MIX3"], (1, 3): p["DEP"] + p["MIX2"], (2, 3): p["DEP"] + p["MIX1"]}
    return {"IND": p["IND"], "DEP": p["DEP"], "MIX": p["MIX1"] + p["MIX2"] + p["MIX3"],
            "same_root": {f"{a}{b}": v for (a, b), v in pair.items()}}


def draw_set_examples(pool: Dict[str, List[Tuple[str, Sequence[str], str]]], fold_seed: str
                      ) -> List[Tuple[Sequence[str], str]]:
    """pool maps structure (IND, DEP, MIX) to (world_id, presented texts,
    configuration) from training worlds only."""
    rng = random.Random(f"examples|{SET_TASK}|{fold_seed}")
    out = []
    for c in ("IND", "DEP", "MIX"):
        cands = sorted(pool[c], key=lambda x: (x[0], x[2]))
        assert len(cands) >= SET_PER_STRUCTURE, f"{len(cands)} training sets for {c}, need {SET_PER_STRUCTURE}"
        out += [(ts, cfg) for _, ts, cfg in rng.sample(cands, SET_PER_STRUCTURE)]
    rng.shuffle(out)
    return out


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
        n = len(classes_of(task))
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

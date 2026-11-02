"""Proposition matcher (build spec section 8).

Aligns message sentences to world propositions and labels each proposition
preserved, qualified, altered, or omitted, and each conflict pair by the
member asserted. The embedding function is injected, so tests can use a toy
embedding and the real run uses the registered model.

This module is anchored: it reads the world record. Nothing here may feed a
text-only model (features.assert_text_only enforces that boundary).
"""
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .features import body, sentences
from .worlds import World

PRESERVED, QUALIFIED, ALTERED, OMITTED = "preserved", "qualified", "altered", "omitted"
NUM = re.compile(r"\b\d+(?:[:.]\d+)?\b")
NEGATION = re.compile(r"\b(not|no|never|none|nobody|nothing|neither|nor|without|ruled out|denied)\b", re.IGNORECASE)
QUALIFIERS = re.compile(r"\b(may|might|could|possibly|likely|reportedly|apparently|unconfirmed|not confirmed|"
                        r"according to|suggest(s|ed)?|appear(s|ed)?|said|stated|reported)\b", re.IGNORECASE)


def _cos(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def _values(text: str, aliases: Dict[str, List[str]]) -> Tuple[set, set]:
    nums = set(NUM.findall(text))
    low = text.lower()
    ents = {canon for canon, forms in aliases.items() if any(f.lower() in low for f in [canon] + forms)}
    return nums, ents


@dataclass
class Match:
    states: Dict[str, str] = field(default_factory=dict)  # proposition id -> label
    conflicts: Dict[int, str] = field(default_factory=dict)  # pair index -> member id, "both", or "neither"
    unsupported: int = 0  # sentences matching no proposition
    sentence_map: Dict[int, Optional[str]] = field(default_factory=dict)


NUMBER_WORDS = {w: str(i) for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
    "seventeen eighteen nineteen twenty".split())}
NUMBER_WORDS.update({"thirty": "30", "forty": "40", "fifty": "50", "sixty": "60", "seventy": "70",
                     "eighty": "80", "ninety": "90", "hundred": "100"})


def _spelled(seq: List[str]) -> List[str]:
    """Number words joined by hyphens: twenty-six is 26, and a spelled clock
    time such as zero-one-thirty-eight is 01:38."""
    v = [int(NUMBER_WORDS[w]) for w in seq]
    if len(v) == 2 and v[0] >= 20 and v[0] % 10 == 0 and v[1] < 10:
        return [str(v[0] + v[1])]
    if len(v) == 3 and v[0] <= 2 and v[1] <= 9 and v[2] < 60:
        return [f"{v[0]}{v[1]}:{v[2]:02d}"]
    if len(v) == 4 and v[0] <= 2 and v[1] <= 9 and v[2] >= 20 and v[2] % 10 == 0 and v[3] < 10:
        return [f"{v[0]}{v[1]}:{v[2] + v[3]:02d}"]
    if len(v) == 4 and all(x <= 9 for x in v) and v[0] <= 2 and v[2] <= 5:
        return [f"{v[0]}{v[1]}:{v[2]}{v[3]}"]
    return [str(x) for x in v]


def _numbers(text: str) -> set:
    """Digits, with thousands separators removed, plus number words, so that
    14 and fourteen, 1,140 and 1140, and 01:38 and zero-one-thirty-eight match."""
    low = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text.lower())
    out = set(NUM.findall(low))
    for tok in re.findall(r"[a-z]+(?:-[a-z]+)*", low):
        parts = tok.split("-")
        if all(w in NUMBER_WORDS for w in parts):
            out.update(_spelled(parts))
    return out


def match(text: str, world: World, embed: Callable[[str], Sequence[float]],
          aliases: Optional[Dict[str, List[str]]] = None, threshold: float = 0.86) -> Match:
    """Each proposition is present if some sentence of the message is at
    least threshold-similar to it, so one sentence can carry several
    propositions. The two members of a conflict pair usually resemble the
    same sentence, so the pair is resolved by values where they differ, and
    otherwise by the more similar member. A sentence similar to no
    proposition is an unsupported addition.

    The default threshold suits nomic-embed-text, where propositions from an
    unrelated world reach about 0.81 and restatements about 0.87 and above
    (verification-run spot check, 2026-10-30)."""
    aliases = aliases or {}
    props = world.propositions
    sents = sentences(body(text))
    pvec = {p.pid: embed(p.text) for p in props}
    svec = [embed(s) for s in sents]
    out = Match()
    best: Dict[str, Tuple[float, int]] = {}
    for p in props:
        sims = [(_cos(v, pvec[p.pid]), i) for i, v in enumerate(svec)]
        if sims:
            best[p.pid] = max(sims)
    for i, v in enumerate(svec):
        top = max(((_cos(v, pvec[p.pid]), p.pid) for p in props), default=(0.0, None))
        out.sentence_map[i] = top[1] if top[0] >= threshold else None
        if top[0] < threshold:
            out.unsupported += 1
    present = {pid for pid, (sim, _) in best.items() if sim >= threshold}
    by_id = world.by_id()
    for idx, (a, b) in enumerate(world.conflict_pairs()):
        if a in present and b in present:
            na, nb = _numbers(by_id[a].text), _numbers(by_id[b].text)
            sa, sb = _numbers(sents[best[a][1]]), _numbers(sents[best[b][1]])
            a_val, b_val = bool(na - nb) and (na - nb) <= sa, bool(nb - na) and (nb - na) <= sb
            if a_val and b_val:
                pass  # the message states both values, as in "seven or eleven"
            elif a_val != b_val:
                present.discard(b if a_val else a)
            elif best[a][1] == best[b][1]:
                present.discard(b if best[a][0] >= best[b][0] else a)
    for p in props:
        if p.pid not in present:
            out.states[p.pid] = OMITTED
            continue
        s = sents[best[p.pid][1]]
        nums, ents = _values(s, aliases)
        nums = _numbers(s)
        pnums, pents = _numbers(p.text), _values(p.text, aliases)[1]
        values_kept = bool(pnums) and pnums <= nums
        # a negation elsewhere in a long sentence does not alter a proposition whose values are all present
        neg_flip = not values_kept and bool(NEGATION.search(s)) != bool(NEGATION.search(p.text))
        value_changed = (pnums and nums and not (pnums & nums)) or (pents and ents and not (pents & ents))
        if neg_flip or value_changed:
            out.states[p.pid] = ALTERED
        elif QUALIFIERS.search(s) and not QUALIFIERS.search(p.text):
            out.states[p.pid] = QUALIFIED
        else:
            out.states[p.pid] = PRESERVED
    for idx, pair in enumerate(world.conflict_pairs()):
        asserted = [pid for pid in pair if out.states.get(pid) in (PRESERVED, QUALIFIED)]
        out.conflicts[idx] = asserted[0] if len(asserted) == 1 else ("both" if len(asserted) == 2 else "neither")
    return out


def deviations(m: Match, package: Sequence[str]) -> set:
    """Deviations from the world record that a message carries. Omission of a
    proposition outside the message's package does not count (spec 8)."""
    pkg = set(package)
    dev = set()
    for pid, st in m.states.items():
        if st == OMITTED and pid in pkg:
            dev.add(("omit", pid))
        elif st == ALTERED:
            dev.add(("alter", pid))
    for idx, res in m.conflicts.items():
        dev.add(("conflict", idx, res))
    return dev


def shared_deviations(a: set, b: set) -> int:
    """Each proposition counts at most once per pair."""
    return len(a & b)


class IndependentNull:
    """Mean shared-deviation count for independent full-access IND pairs in
    the training fold, by event type, smoothed toward the overall mean."""

    def __init__(self, weight: float = 5.0):
        self.weight = weight
        self.by_type: Dict[str, List[int]] = {}

    def add(self, event_type: str, count: int) -> None:
        self.by_type.setdefault(event_type, []).append(count)

    def expected(self, event_type: str) -> float:
        allv = [c for v in self.by_type.values() for c in v]
        overall = sum(allv) / len(allv) if allv else 0.0
        v = self.by_type.get(event_type, [])
        return (sum(v) + self.weight * overall) / (len(v) + self.weight)

    def excess(self, event_type: str, count: int) -> float:
        return count - self.expected(event_type)

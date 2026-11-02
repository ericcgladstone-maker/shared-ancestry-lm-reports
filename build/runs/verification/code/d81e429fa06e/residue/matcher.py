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
NEGATION = re.compile(r"\b(not|no|never|none|without|ruled out|denied)\b", re.IGNORECASE)
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


def match(text: str, world: World, embed: Callable[[str], Sequence[float]],
          aliases: Optional[Dict[str, List[str]]] = None, threshold: float = 0.75) -> Match:
    aliases = aliases or {}
    props = world.propositions
    pvec = {p.pid: embed(p.text) for p in props}
    pval = {p.pid: _values(p.text, aliases) for p in props}
    out = Match()
    best_sentence: Dict[str, Tuple[float, str]] = {}
    for i, s in enumerate(sentences(body(text))):
        sv = embed(s)
        scored = sorted(((_cos(sv, pvec[p.pid]), p.pid) for p in props), reverse=True)
        sim, pid = scored[0]
        if sim < threshold:
            out.sentence_map[i] = None
            out.unsupported += 1
            continue
        out.sentence_map[i] = pid
        if pid not in best_sentence or sim > best_sentence[pid][0]:
            best_sentence[pid] = (sim, s)
    for p in props:
        if p.pid not in best_sentence:
            out.states[p.pid] = OMITTED
            continue
        s = best_sentence[p.pid][1]
        nums, ents = _values(s, aliases)
        pnums, pents = pval[p.pid]
        neg_flip = bool(NEGATION.search(s)) != bool(NEGATION.search(p.text))
        value_changed = (pnums and nums and nums != pnums) or (pents and ents and not (pents & ents))
        if neg_flip or value_changed:
            out.states[p.pid] = ALTERED
        elif QUALIFIERS.search(s) and not QUALIFIERS.search(p.text):
            out.states[p.pid] = QUALIFIED
        else:
            out.states[p.pid] = PRESERVED
    for idx, pair in enumerate(world.conflict_pairs()):
        present = [pid for pid in pair if out.states.get(pid) in (PRESERVED, QUALIFIED)]
        out.conflicts[idx] = present[0] if len(present) == 1 else ("both" if len(present) == 2 else "neither")
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

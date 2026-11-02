"""Lineage audit (design principle 8, build spec section 3).

Compares every realized graph with its hand-written fixture and checks that
each prompt contains exactly its parents' texts and no other node's text.
"""
from typing import Dict, List

from . import allocators as al
from .dispatcher import RealizedNode
from .fixtures import FIXTURES
from .worlds import World


def audit_condition(condition: str, realized: Dict[str, RealizedNode], world: World,
                    block_texts: Dict[str, str]) -> List[str]:
    problems: List[str] = []
    fx = FIXTURES.get(condition)
    if fx is None:
        return [f"{condition}: no fixture"]
    want = fx["nodes"]
    got = {n: (r.fn, tuple(r.parents)) for n, r in realized.items()}
    if set(got) != set(want):
        problems.append(f"{condition}: nodes {sorted(got)} differ from fixture {sorted(want)}")
    for n in set(got) & set(want):
        if got[n] != want[n]:
            problems.append(f"{condition}.{n}: realized {got[n]} differs from fixture {want[n]}")
    full = al.full_record(world)
    for n, r in realized.items():
        if r.fn == "observe":
            is_full = tuple(r.package) == full
            should = n in fx.get("full", ())
            if is_full != should:
                problems.append(f"{condition}.{n}: full-record observer expected={should} got={is_full}")
    # prompt contents: parents' texts present, no other node's text present
    for n, r in realized.items():
        for p in r.parents:
            if realized[p].text not in r.prompt:
                problems.append(f"{condition}.{n}: prompt lacks parent {p}'s text")
        allowed = {realized[p].text for p in r.parents}
        for key, text in block_texts.items():
            if text in allowed or key == r.key:
                continue
            if text and text in r.prompt:
                problems.append(f"{condition}.{n}: prompt contains a non-parent text ({key[:10]})")
    return problems


def audit_block(block: Dict[str, Dict[str, RealizedNode]], world: World) -> List[str]:
    texts: Dict[str, str] = {}
    for realized in block.values():
        for r in realized.values():
            if r.key in texts and texts[r.key] != r.text:
                return [f"key {r.key[:12]} has two different texts"]
            texts[r.key] = r.text
    problems: List[str] = []
    for condition, realized in block.items():
        problems.extend(audit_condition(condition, realized, world, texts))
    return problems

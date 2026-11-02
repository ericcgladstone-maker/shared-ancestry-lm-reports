"""Graph builders used by the dispatcher (design Parts IV and V).

These builders are deliberately separate from fixtures.py, which states the
same graphs by hand. The lineage audit compares the two, so a wiring error
here cannot pass by agreeing with itself.
"""
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from . import allocators as al
from .worlds import World

OBSERVE, REWRITE, SYNTHESIZE = "observe", "rewrite", "synthesize"


@dataclass(frozen=True)
class Node:
    name: str
    fn: str
    parents: Tuple[str, ...]
    role: str  # enters the call key
    template_slot: str  # which block template the node uses
    package: Optional[al.Package] = None  # observers only
    condition_tag: bool = False  # key includes the condition name
    instruction: str = "neutral"  # Study 2 rewrites: neutral or conceal


@dataclass(frozen=True)
class Graph:
    condition: str
    study: str
    nodes: Tuple[Node, ...]
    terminals: Tuple[str, ...]  # one for Study 1, three for Study 2

    def node(self, name: str) -> Node:
        return {n.name: n for n in self.nodes}[name]


def _obs(name: str, role: str, pkg: al.Package, tag: bool = False) -> Node:
    return Node(name, OBSERVE, (), role, "src", pkg, tag)


def _rw(name: str, parent: str, role: str, slot: str, tag: bool = False, instruction: str = "neutral") -> Node:
    return Node(name, REWRITE, (parent,), role, slot, None, tag, instruction)


def _syn(name: str, parents: Tuple[str, ...], role: str = "syn") -> Node:
    return Node(name, SYNTHESIZE, parents, role, "syn")


# ---------- Study 1 ----------

def d0(w: World, r: int, seed: int) -> Graph:
    full = al.full_record(w)
    return Graph("D0", "S1", (_obs("o1", "obs:s1", full),), ("o1",))


def nc0(w: World, r: int, seed: int) -> Graph:
    full = al.full_record(w)
    nodes = (_obs("o1", "obs:s1", full, tag=True),
             _obs("x2", "sib:s2", full, tag=True),
             _obs("x3", "sib:s3", full, tag=True))
    return Graph("NC0", "S1", nodes, ("o1",))


def chain(k: int) -> Callable[[World, int, int], Graph]:
    def build(w: World, r: int, seed: int) -> Graph:
        nodes = [_obs("o1", "obs:s1", al.full_record(w))]
        prev = "o1"
        for d in range(1, k + 1):
            nodes.append(_rw(f"r{d}", prev, f"rw:d{d}", f"rw:d{d}"))
            prev = f"r{d}"
        return Graph(f"R{k}", "S1", tuple(nodes), (prev,))
    return build


def ncr1(w: World, r: int, seed: int) -> Graph:
    nodes = (_obs("o1", "obs:s1", al.full_record(w)),
             _rw("r1", "o1", "rw:d1", "rw:d1", tag=True),
             _rw("x2", "o1", "sib-rw:s2", "rw:s2", tag=True),
             _rw("x3", "o1", "sib-rw:s3", "rw:s3", tag=True))
    return Graph("NCR1", "S1", nodes, ("r1",))


def fan(k: int) -> Callable[[World, int, int], Graph]:
    def build(w: World, r: int, seed: int) -> Graph:
        pkgs = al.partition_packages(w, k, r, seed)
        obs = [_obs(f"f{j + 1}", f"obs:s{j + 1}", pkgs[j]) for j in range(k)]
        syn = _syn("syn", tuple(o.name for o in obs))
        return Graph(f"F{k}", "S1", tuple(obs + [syn]), ("syn",))
    return build


def _independent_core(w: World, r: int, seed: int, arm: str) -> List[Node]:
    if arm == "same":
        pkgs = [al.full_record(w)] * 3
    else:
        pkgs, _ = al.diverse_packages(w, r, seed)
    return [_obs("o1", "obs:s1", pkgs[0]), _obs("o2", "obs:s2", pkgs[1]), _obs("o3", "obs:s3", pkgs[2]),
            _rw("w1", "o1", "rw:d1", "rw:d1"), _rw("w2", "o2", "rw:s2", "rw:s2"), _rw("w3", "o3", "rw:s3", "rw:s3"),
            _syn("syn", ("w1", "w2", "w3"))]


def _dependent_core(w: World, r: int, seed: int, arm: str) -> List[Node]:
    pkg = al.full_record(w) if arm == "same" else al.diverse_packages(w, r, seed)[1]
    return [_obs("o1", "obs:s1", pkg),
            _rw("w1", "o1", "rw:d1", "rw:d1"), _rw("w2", "o1", "rw:s2", "rw:s2"), _rw("w3", "o1", "rw:s3", "rw:s3"),
            _syn("syn", ("w1", "w2", "w3"))]


def independence(kind: str, arm: str, post: int = 0) -> Callable[[World, int, int], Graph]:
    """kind is SI or SD, arm is same or div, post is 0, 1, or 3 downstream rewrites.

    Downstream rewrites follow the slot map in Part IV: the +3 branch uses the
    templates of R5's positions 3 to 5, and the +1 branch uses position 3.
    The two branches carry different roles, so they are separate calls.
    """
    def build(w: World, r: int, seed: int) -> Graph:
        core = _independent_core(w, r, seed, arm) if kind == "SI" else _dependent_core(w, r, seed, arm)
        nodes = list(core)
        prev = "syn"
        for i in range(1, post + 1):
            pos = 2 + i
            nodes.append(_rw(f"p{i}", prev, f"post{post}:d{pos}", f"rw:d{pos}"))
            prev = f"p{i}"
        name = f"{kind}-{arm}" + (f"+{post}" if post else "")
        return Graph(name, "S1", tuple(nodes), (prev,))
    return build


STUDY1: Dict[str, Callable[[World, int, int], Graph]] = {
    "D0": d0, "NC0": nc0, "R1": chain(1), "R3": chain(3), "R5": chain(5), "NCR1": ncr1,
    "F1": fan(1), "F2": fan(2), "F3": fan(3),
    "SI-same": independence("SI", "same"), "SD-same": independence("SD", "same"),
    "SI-div": independence("SI", "div"), "SD-div": independence("SD", "div"),
    "SI-same+1": independence("SI", "same", 1), "SD-same+1": independence("SD", "same", 1),
    "SI-same+3": independence("SI", "same", 3), "SD-same+3": independence("SD", "same", 3),
}
SECOND_GENRE = ("R1", "R3", "SI-same", "SD-same")


# ---------- Study 2 ----------

def study2(structure: str, access: str, instruction: str, set_index: int = 0) -> Callable[[World, int, int], Graph]:
    """structure is IND, DEP, or MIX. access is full or partial. instruction is
    neutral or conceal. Generation slots follow Part IV: MIX's shared pair is
    in slots 1 and 2 and its odd message in slot 3."""
    def build(w: World, r: int, seed: int) -> Graph:
        pkgs = [al.full_record(w)] * 3 if access == "full" else al.study2_draw(w, r, set_index, seed)
        if structure == "IND":
            obs = [_obs(f"o{j}", f"s2obs:g{j}", pkgs[j - 1]) for j in (1, 2, 3)]
            parents = ("o1", "o2", "o3")
        elif structure == "DEP":
            obs = [_obs("o1", "s2obs:g1", pkgs[0])]
            parents = ("o1", "o1", "o1")
        else:
            obs = [_obs("o1", "s2obs:g1", pkgs[0]), _obs("o3", "s2obs:g3", pkgs[2])]
            parents = ("o1", "o1", "o3")
        rws = [_rw(f"m{j}", parents[j - 1], f"s2rw:g{j}:{instruction}", f"s2rw:g{j}", instruction=instruction)
               for j in (1, 2, 3)]
        name = f"{structure}-{access}-{instruction}"
        return Graph(name, "S2", tuple(obs + rws), ("m1", "m2", "m3"))
    return build


STUDY2: Dict[str, Callable[[World, int, int], Graph]] = {
    f"{s}-{a}-{i}": study2(s, a, i)
    for s in ("IND", "DEP", "MIX") for a in ("full", "partial") for i in ("neutral", "conceal")
}

"""History attributes computed from a graph (design Part V-A), and the
derivations that keep predictor outputs consistent."""
from typing import Dict, List, Sequence, Tuple

ATTRIBUTES = ("synthesis", "inputs", "roots", "rewrites_before", "rewrites_after")
History = Tuple[str, int, int, int, int]


def ancestors(nodes: Dict[str, Tuple[str, Tuple[str, ...]]], terminal: str) -> List[str]:
    seen: List[str] = []
    stack = [terminal]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.append(n)
        stack.extend(nodes[n][1])
    return seen


def history_of(nodes: Dict[str, Tuple[str, Tuple[str, ...]]], terminal: str) -> History:
    """Compute the five attributes from the terminal's ancestry alone, so that
    unused siblings never count."""
    anc = ancestors(nodes, terminal)
    fns = {n: nodes[n][0] for n in anc}
    roots = sorted(n for n in anc if fns[n] == "observe")
    syns = [n for n in anc if fns[n] == "synthesize"]
    assert len(syns) <= 1, "the design has at most one synthesis on a path"
    if syns:
        syn = syns[0]
        inputs = len(nodes[syn][1])
        before = 0
        p = nodes[syn][1][0]
        while fns[p] == "rewrite":
            before += 1
            p = nodes[p][1][0]
        after = 0
        n = terminal
        while n != syn:
            after += 1
            n = nodes[n][1][0]
        return ("yes", inputs, len(roots), before, after)
    after = 0
    n = terminal
    while fns[n] == "rewrite":
        after += 1
        n = nodes[n][1][0]
    return ("no", 0, len(roots), 0, after)


def distinct_histories(table: Dict[str, History]) -> List[History]:
    return sorted(set(table.values()), key=str)


def attribute_marginals(history_probs: Dict[History, float]) -> Dict[str, Dict[object, float]]:
    """Attribute probabilities are sums of history probabilities, so the two
    outputs cannot contradict each other."""
    out: Dict[str, Dict[object, float]] = {a: {} for a in ATTRIBUTES}
    for h, p in history_probs.items():
        for a, v in zip(ATTRIBUTES, h):
            out[a][v] = out[a].get(v, 0.0) + p
    return out


# Study 2 set configurations: IND, DEP, and MIX with the odd message at each
# presented position. A pair shares a root under DEP, and under the MIX
# configuration whose odd message is neither member of the pair.
SET_CONFIGS = ("IND", "DEP", "MIX-odd1", "MIX-odd2", "MIX-odd3")
PAIRS = ((1, 2), (1, 3), (2, 3))


def pair_shares_root(config: str, pair: Sequence[int]) -> bool:
    if config == "IND":
        return False
    if config == "DEP":
        return True
    odd = int(config[-1])
    return odd not in pair


def set_marginals(config_probs: Dict[str, float]) -> Tuple[Dict[str, float], Dict[Tuple[int, int], float]]:
    structure = {"IND": 0.0, "DEP": 0.0, "MIX": 0.0}
    for c, p in config_probs.items():
        structure["MIX" if c.startswith("MIX") else c] += p
    pairs = {pr: sum(p for c, p in config_probs.items() if pair_shares_root(c, pr)) for pr in PAIRS}
    return structure, pairs

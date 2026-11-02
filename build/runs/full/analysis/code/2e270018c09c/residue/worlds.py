"""World schema (build spec section 4) and a synthetic generator for tests."""
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Proposition:
    pid: str
    text: str
    core: bool
    source: str
    conflict_pair: Optional[int] = None  # 0 or 1 for members of a conflict pair


@dataclass
class World:
    world_id: str
    event_type: str
    index: int  # position in the world bank, used by the co-location rotation
    propositions: List[Proposition] = field(default_factory=list)

    @property
    def core(self) -> Proposition:
        cores = [p for p in self.propositions if p.core]
        assert len(cores) == 1, f"{self.world_id}: expected one core proposition"
        return cores[0]

    def conflict_pairs(self) -> List[Tuple[str, str]]:
        pairs: Dict[int, List[str]] = {}
        for p in self.propositions:
            if p.conflict_pair is not None:
                pairs.setdefault(p.conflict_pair, []).append(p.pid)
        out = [tuple(sorted(pairs[i])) for i in sorted(pairs)]
        assert len(out) == 2 and all(len(x) == 2 for x in out), f"{self.world_id}: expected two conflict pairs"
        return out  # type: ignore[return-value]

    def ids(self) -> List[str]:
        return [p.pid for p in self.propositions]

    def by_id(self) -> Dict[str, Proposition]:
        return {p.pid: p for p in self.propositions}


def validate(world: World) -> None:
    ids = world.ids()
    assert len(ids) == len(set(ids)), f"{world.world_id}: duplicate proposition ids"
    assert 16 <= len(ids) <= 24, f"{world.world_id}: about 20 propositions expected"
    world.core
    pairs = world.conflict_pairs()
    core_id = world.core.pid
    assert all(core_id not in pr for pr in pairs), f"{world.world_id}: core cannot be in a conflict pair"


def synthetic_world(index: int, n: int = 20, seed: int = 0) -> World:
    """A schema-valid world with placeholder text, for offline tests only."""
    rng = random.Random(seed * 1000 + index)
    sources = ["maintenance log", "shift supervisor", "sensor record", "safety officer", "dispatch note"]
    props = [Proposition(f"p{i:02d}", f"Placeholder fact {i} in world {index}.", i == 0, rng.choice(sources))
             for i in range(n)]
    # members 1-2 form pair 0, members 3-4 form pair 1
    for i, pair in ((1, 0), (2, 0), (3, 1), (4, 1)):
        p = props[i]
        props[i] = Proposition(p.pid, p.text, False, p.source, pair)
    w = World(f"W{index:03d}", f"type{index % 14:02d}", index, props)
    validate(w)
    return w

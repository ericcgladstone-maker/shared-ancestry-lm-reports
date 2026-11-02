"""Package allocators (build spec section 4).

Every allocator is a pure function of the world and a seed, and asserts its own
rules before returning, so a wrong package can never reach a model call.
"""
import random
from typing import Dict, List, Tuple

from .keys import canonical, sha256
from .worlds import World

Package = Tuple[str, ...]  # sorted proposition ids


def package_id(pkg: Package) -> str:
    return sha256(canonical(list(pkg)))[:16]


def full_record(world: World) -> Package:
    return tuple(sorted(world.ids()))


def colocated_pair_index(world: World, replicate: int) -> int:
    """Which conflict pair is co-located in F2 and F3 (design Part IV).

    Alternates by replicate, and the starting pair alternates between odd- and
    even-indexed worlds. Over 60 worlds and 3 replicates each pair is
    co-located in exactly 90 of 180 trials.
    """
    return (world.index + replicate) % 2


def partition_packages(world: World, k: int, replicate: int, seed: int) -> List[Package]:
    """F1 to F3: core to every observer, conflict pairs placed first, the rest
    dealt so that counts differ by at most one."""
    assert k in (1, 2, 3)
    core = world.core.pid
    if k == 1:
        return [full_record(world)]
    pairs = world.conflict_pairs()
    co = pairs[colocated_pair_index(world, replicate)]
    split = pairs[1 - colocated_pair_index(world, replicate)]
    rng = random.Random(f"{seed}|{world.world_id}|{replicate}|F{k}")
    bins: List[List[str]] = [[] for _ in range(k)]
    co_obs = rng.randrange(k)
    bins[co_obs].extend(co)
    a, b = rng.sample(range(k), 2)
    bins[a].append(split[0])
    bins[b].append(split[1])
    placed = {core, *co, *split}
    rest = [p for p in world.ids() if p not in placed]
    rng.shuffle(rest)
    for pid in rest:
        smallest = min(range(k), key=lambda i: (len(bins[i]), i))
        bins[smallest].append(pid)
    pkgs = [tuple(sorted([core] + b)) for b in bins]
    _assert_partition(world, pkgs, co, split)
    return pkgs


def _assert_partition(world: World, pkgs: List[Package], co: Tuple[str, str], split: Tuple[str, str]) -> None:
    core = world.core.pid
    assert all(core in p for p in pkgs), "core missing from a package"
    non_core = [set(p) - {core} for p in pkgs]
    union = set().union(*non_core)
    assert union == set(world.ids()) - {core}, "assigned union differs from the world record"
    assert sum(len(s) for s in non_core) == len(union), "non-core propositions overlap"
    sizes = [len(s) for s in non_core]
    assert max(sizes) - min(sizes) <= 1, f"package sizes differ by more than one: {sizes}"
    assert sum(set(co) <= s for s in non_core) == 1, "co-located pair not with a single observer"
    holders = [i for i, s in enumerate(non_core) if split[0] in s] + [i for i, s in enumerate(non_core) if split[1] in s]
    assert len(holders) == 2 and holders[0] != holders[1], "split pair not across two observers"


def diverse_packages(world: World, replicate: int, seed: int, overlap: int = 2) -> Tuple[List[Package], Package]:
    """SI-div packages with a fixed pairwise overlap, and SD-div's union."""
    core = world.core.pid
    rng = random.Random(f"{seed}|{world.world_id}|{replicate}|div")
    rest = [p for p in world.ids() if p != core]
    rng.shuffle(rest)
    shared = {pair: [rest.pop() for _ in range(overlap)] for pair in ((0, 1), (0, 2), (1, 2))}
    own: List[List[str]] = [[], [], []]
    for i, pid in enumerate(rest):
        own[i % 3].append(pid)
    pkgs = []
    for j in range(3):
        members = set(own[j])
        for pair, pids in shared.items():
            if j in pair:
                members.update(pids)
        pkgs.append(tuple(sorted({core} | members)))
    union = tuple(sorted(set().union(*map(set, pkgs))))
    assert union == full_record(world), "SI-div union differs from the world record"
    for a, b in ((0, 1), (0, 2), (1, 2)):
        assert len((set(pkgs[a]) & set(pkgs[b])) - {core}) == overlap, "overlap size wrong"
    return pkgs, union


def study2_pool(world: World, seed: int, size: int = 6) -> List[Package]:
    """Six equal-size packages per world, each the core plus a random half of the rest."""
    core = world.core.pid
    rest = sorted(p for p in world.ids() if p != core)
    rng = random.Random(f"{seed}|{world.world_id}|pool")
    half = len(rest) // 2
    pool = [tuple(sorted([core] + rng.sample(rest, half))) for _ in range(size)]
    assert len({len(p) for p in pool}) == 1, "pool packages differ in size"
    return pool


def study2_draw(world: World, replicate: int, set_index: int, seed: int) -> List[Package]:
    """Three packages drawn without replacement for generation slots 1 to 3."""
    pool = study2_pool(world, seed)
    rng = random.Random(f"{seed}|{world.world_id}|{replicate}|{set_index}|draw")
    picks = rng.sample(range(len(pool)), 3)
    return [pool[i] for i in picks]


def coverage_report(pkgs: List[Package]) -> Dict[str, int]:
    return {"packages": len(pkgs), "union": len(set().union(*map(set, pkgs)))}

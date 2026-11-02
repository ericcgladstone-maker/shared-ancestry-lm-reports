"""Dispatcher: realizes condition graphs for one block through the store.

A block is one world, replicate, genre, producer, and prompt family. Every
call goes through CallStore, so a shared key is called once and its stored
output is reused.
"""
import random
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from . import allocators as al
from .graphs import OBSERVE, REWRITE, SYNTHESIZE, Graph
from .keys import make_key
from .prompts import block_templates, render_observe, render_with_inputs, target_words
from .store import CallStore, StoreError
from .worlds import World


@dataclass
class BlockSpec:
    world: World
    replicate: int
    genre: str
    producer: str
    family: str
    seed: int


@dataclass
class RealizedNode:
    name: str
    fn: str
    parents: tuple
    key: str
    prompt: str
    text: str
    package: Optional[tuple]
    template_id: str


def realize(
    graph: Graph,
    spec: BlockSpec,
    store: CallStore,
    model: Callable[[str, int], str],
    model_version: str,
    params: Dict[str, object],
    order_rng: random.Random,
) -> Dict[str, RealizedNode]:
    templates = block_templates(spec.family, f"{spec.seed}|{spec.world.world_id}|{spec.replicate}|{spec.genre}|{spec.producer}")
    nodes = {n.name: n for n in graph.nodes}
    done: Dict[str, RealizedNode] = {}
    pending = list(nodes)
    while pending:
        ready = [n for n in pending if all(p in done for p in nodes[n].parents)]
        assert ready, f"{graph.condition}: cycle or missing parent"
        name = order_rng.choice(ready)  # random order among calls not constrained by parents
        pending.remove(name)
        node = nodes[name]
        tid = templates[node.template_slot][node.instruction]
        parent_keys = [done[p].key for p in node.parents]
        key = make_key(
            study=graph.study, world=spec.world.world_id, replicate=spec.replicate, genre=spec.genre,
            producer=spec.producer, family=spec.family, role=node.role, template_id=tid,
            package_id=al.package_id(node.package) if node.package else None,
            parent_keys=parent_keys, condition_tag=graph.condition if node.condition_tag else None,
        )
        if node.fn == OBSERVE:
            prompt = render_observe(tid, spec.world, node.package, spec.genre)
        elif node.fn in (REWRITE, SYNTHESIZE):
            prompt = render_with_inputs(tid, [done[p].text for p in node.parents], spec.genre)
        else:
            raise ValueError(node.fn)
        text = store.get_or_call(key, prompt, model_version, params, model, target_words(spec.genre),
                                 {"condition_first_seen": graph.condition, "node": name, "fn": node.fn})
        done[name] = RealizedNode(name, node.fn, node.parents, key, prompt, text, node.package, tid)
    return done


def run_block(
    spec: BlockSpec,
    builders: Dict[str, Callable[[World, int, int], Graph]],
    store: CallStore,
    model: Callable[[str, int], str],
    model_version: str,
    params: Dict[str, object],
    failures: Optional[Dict[str, str]] = None,
) -> Dict[str, Dict[str, RealizedNode]]:
    """If failures is given, a condition whose node fails every attempt is
    recorded there (principle 9: the trial is marked failed) and the block
    continues. Otherwise the failure propagates."""
    rng = random.Random(f"order|{spec.seed}|{spec.world.world_id}|{spec.replicate}|{spec.genre}|{spec.producer}")
    names = list(builders)
    rng.shuffle(names)  # conditions interleaved in random order (design principle 10)
    out: Dict[str, Dict[str, RealizedNode]] = {}
    for name in names:
        graph = builders[name](spec.world, spec.replicate, spec.seed)
        try:
            out[graph.condition] = realize(graph, spec, store, model, model_version, params, rng)
        except StoreError as e:
            if failures is None:
                raise
            failures[graph.condition] = str(e)
    return out

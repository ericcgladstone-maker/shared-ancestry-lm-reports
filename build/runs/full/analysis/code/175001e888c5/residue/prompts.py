"""Prompt pools and rendering (build spec section 5).

Templates come from prompts/pools_v1.json. The genre, format, and sources
lines are added by the renderer, so they are identical across node
functions within a genre (design principle 12).
"""
import json
import os
import random
import re
from functools import lru_cache
from typing import Dict, List, Sequence

from .worlds import World

FAMILIES = ("A", "B")
PER_FAMILY = 6
DELIM = "\n-----\n"
POOLS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts", "pools_v1.json")


@lru_cache(maxsize=None)
def pools() -> dict:
    with open(POOLS_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def target_words(genre: str) -> int:
    return pools()["genres"][genre]["target_words"]


def template_id(family: str, fn: str, idx: int) -> str:
    return f"{family}:{fn}:{idx}"


def _task_sentence(tid: str, genre: str) -> str:
    family, fn, idx = tid.split(":")
    base_fn = "rewrite" if fn == "conceal" else fn
    text = pools()["families"][family][base_fn][int(idx)]
    return text.format(genre_noun=pools()["genres"][genre]["noun"])


def instruction_parts(tid: str, genre: str) -> List[str]:
    """Task sentence, genre line, format line, and the final attribution line."""
    p = pools()
    fn = tid.split(":")[1]
    g = p["genres"][genre]
    parts = [_task_sentence(tid, genre), g["style"], p["format_line"].format(words=g["target_words"])]
    if fn == "observe":
        parts.append(p["sources_line"]["observe"])
    elif fn == "conceal":
        parts.append(p["conceal_line"])
    else:
        parts.append(p["sources_line"]["carry"])
    return parts


def instruction(tid: str, genre: str) -> str:
    """Everything the model is told, apart from its inputs."""
    return " ".join(instruction_parts(tid, genre))


def instruction_of(prompt: str) -> str:
    """Recover the instruction from a rendered prompt."""
    return prompt.split("\n\nFacts:\n")[0].split(DELIM)[0]


BLOCK_SLOTS = ("src", "rw:d1", "rw:d2", "rw:d3", "rw:d4", "rw:d5", "rw:s2", "rw:s3", "syn",
               "s2rw:g1", "s2rw:g2", "s2rw:g3")


def block_templates(family: str, seed: str) -> Dict[str, Dict[str, str]]:
    """One template per slot for the whole block (design principle 5).
    Study 2 rewrite slots get a neutral and a concealment variant with the
    same index, so the two arms differ only in the concealment line."""
    rng = random.Random(seed)
    out: Dict[str, Dict[str, str]] = {}
    for slot in BLOCK_SLOTS:
        idx = rng.randrange(PER_FAMILY)
        if slot == "src":
            out[slot] = {"neutral": template_id(family, "observe", idx)}
        elif slot == "syn":
            out[slot] = {"neutral": template_id(family, "synthesize", idx)}
        else:
            out[slot] = {"neutral": template_id(family, "rewrite", idx),
                         "conceal": template_id(family, "conceal", idx)}
    return out


def render_observe(tid: str, world: World, package: Sequence[str], genre: str) -> str:
    by_id = world.by_id()
    facts = "\n".join(f"- {by_id[p].text} (source: {by_id[p].source})" for p in package)
    return f"{instruction(tid, genre)}\n\nFacts:\n{facts}"


def render_with_inputs(tid: str, inputs: List[str], genre: str) -> str:
    return f"{instruction(tid, genre)}{DELIM}{DELIM.join(inputs)}{DELIM}"


BANNED_IN_TEMPLATES = re.compile(
    r"(independen|dependen|chain|relay|synthes|motif|structure|network|"
    r"\bother (node|agent|writer|report|source|account)s?\b|downstream|next step|pass(ed)? (on|along)|"
    r"\b(one|two|three|several|multiple|each|both|all) (of the )?(reports|messages|inputs|accounts|texts|items|sources)\b|"
    r"\bcompare\b|\breconcile\b|\bagree\b|\bconflict|"
    # wording that changes paraphrase intensity, certainty, or invites additions
    # (GPT review of prompt pools v1, R4 to R13)
    r"own word|afresh|\bagain\b|establish|act on|recommend)",
    re.IGNORECASE,
)


def lint(text: str) -> List[str]:
    """Problems that disqualify a template: naming a structure, mentioning
    other nodes, stating or implying an input count, asking for comparison or
    reconciliation, or mentioning downstream use."""
    return [m.group(0) for m in BANNED_IN_TEMPLATES.finditer(text)]


def all_instructions() -> Dict[str, str]:
    """Every distinct instruction, for lint and review."""
    out = {}
    for genre in pools()["genres"]:
        for family in FAMILIES:
            for fn in ("observe", "rewrite", "synthesize", "conceal"):
                for idx in range(PER_FAMILY):
                    tid = template_id(family, fn, idx)
                    out[f"{genre}|{tid}"] = instruction(tid, genre)
    return out

"""Feature registry (build spec section 7).

Every feature is a named deterministic function with a declared scope:
  text      one message
  set       several messages, order-invariant
  anchored  uses the world record or the matcher

Text-only models may consume only text and set features. The registry
enforces this, so world information cannot leak into the predictor.
"""
import re
from dataclasses import dataclass
from itertools import combinations
from statistics import median
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple

TEXT, SET, ANCHORED = "text", "set", "anchored"
TEXT_ONLY_SCOPES = (TEXT, SET)

_WORD = re.compile(r"[A-Za-z0-9']+")
_SENT = re.compile(r"[^.!?]+[.!?]")

HEDGES = ("may", "might", "could", "possibly", "likely", "appears", "apparently", "suggests", "reportedly")
UNCERTAINTY = ("unclear", "unconfirmed", "not confirmed", "uncertain", "unknown", "under investigation")
EVIDENTIAL = ("according to", "indicated", "showed", "recorded", "logged", "observed", "confirmed")
SOURCE_MARKERS = ("said", "stated", "reported", "told", "noted", "per ")


@dataclass(frozen=True)
class Feature:
    name: str
    scope: str
    family: str  # formal, attributional, propositional, relational
    fn: Callable


REGISTRY: Dict[str, Feature] = {}


def register(name: str, scope: str, family: str):
    def deco(fn):
        assert name not in REGISTRY, name
        REGISTRY[name] = Feature(name, scope, family, fn)
        return fn
    return deco


def body(text: str) -> str:
    """The message without its trailing Sources line, so attribution-line
    presence does not leak into formal features."""
    lines = text.rstrip().splitlines()
    if lines and lines[-1].strip().lower().startswith("sources:"):
        lines = lines[:-1]
    return "\n".join(lines)


def words(text: str) -> List[str]:
    return _WORD.findall(body(text).lower())


def sentences(text: str) -> List[str]:
    return [s.strip() for s in _SENT.findall(body(text))] or [body(text)]


def _count(text: str, terms: Iterable[str]) -> float:
    low = " " + " ".join(words(text)) + " "
    return float(sum(low.count(" " + t + " ") if " " not in t.strip() else low.count(t) for t in terms))


# ---------- formal (text) ----------

@register("tokens", TEXT, "formal")
def f_tokens(text: str) -> float:
    return float(len(words(text)))


@register("sentences", TEXT, "formal")
def f_sentences(text: str) -> float:
    return float(len(sentences(text)))


@register("type_token_ratio", TEXT, "formal")
def f_ttr(text: str) -> float:
    w = words(text)
    return len(set(w)) / len(w) if w else 0.0


@register("mean_sentence_length", TEXT, "formal")
def f_msl(text: str) -> float:
    s = sentences(text)
    return len(words(text)) / len(s) if s else 0.0


@register("mean_word_length", TEXT, "formal")
def f_mwl(text: str) -> float:
    w = words(text)
    return sum(map(len, w)) / len(w) if w else 0.0


@register("punctuation_density", TEXT, "formal")
def f_punct(text: str) -> float:
    b = body(text)
    return sum(ch in ",;:()-\"'" for ch in b) / max(1, len(words(text)))


@register("numeric_tokens", TEXT, "formal")
def f_numeric(text: str) -> float:
    return float(sum(any(c.isdigit() for c in t) for t in words(text)))


# ---------- attributional (text) ----------

@register("hedges", TEXT, "attributional")
def f_hedges(text: str) -> float:
    return _count(text, HEDGES)


@register("uncertainty", TEXT, "attributional")
def f_uncertainty(text: str) -> float:
    return _count(text, UNCERTAINTY)


@register("evidential", TEXT, "attributional")
def f_evidential(text: str) -> float:
    return _count(text, EVIDENTIAL)


@register("source_markers", TEXT, "attributional")
def f_source(text: str) -> float:
    return _count(text, SOURCE_MARKERS)


@register("has_sources_line", TEXT, "attributional")
def f_has_sources(text: str) -> float:
    lines = text.rstrip().splitlines()
    return float(bool(lines) and lines[-1].strip().lower().startswith("sources:"))


def parse_sources(text: str):
    """The attribution field: None if absent, [] if present but empty,
    otherwise the listed names. Never a reason for retry (principle 9)."""
    lines = text.rstrip().splitlines()
    if not lines or not lines[-1].strip().lower().startswith("sources:"):
        return None
    rest = lines[-1].strip()[len("sources:"):].strip()
    return [x.strip() for x in rest.split(",") if x.strip()] if rest else []


# ---------- relational (set) ----------

def ngrams(text: str, n: int) -> Set[Tuple[str, ...]]:
    w = words(text)
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


class RarityTable:
    """Document frequency of word 3- to 5-grams, learned on training-fold
    messages only. A rare n-gram appears in at most `max_df` documents."""

    def __init__(self, train_texts: Sequence[str], max_df: int = 2):
        self.max_df = max_df
        self.df: Dict[Tuple[str, ...], int] = {}
        for t in train_texts:
            for n in (3, 4, 5):
                for g in ngrams(t, n):
                    self.df[g] = self.df.get(g, 0) + 1

    def rare(self, text: str) -> Set[Tuple[str, ...]]:
        out = set()
        for n in (3, 4, 5):
            out |= {g for g in ngrams(text, n) if self.df.get(g, 0) <= self.max_df}
        return out


class _ExcludedRarity:
    def __init__(self, df: Dict[Tuple[str, ...], int], own: Dict[Tuple[str, ...], int], max_df: int):
        self.df, self.own, self.max_df = df, own, max_df

    def rare(self, text: str) -> Set[Tuple[str, ...]]:
        out = set()
        for n in (3, 4, 5):
            out |= {g for g in ngrams(text, n) if self.df.get(g, 0) - self.own.get(g, 0) <= self.max_df}
        return out


class WorldRarity:
    """A fold's rarity reference that never counts the scored message's own
    world. Sets in a block reuse identical messages across structures, so a
    table of the training texts scored on those same texts counts a row's
    shared n-grams in its own and its sibling rows, and they almost never
    stay rare, while a held-out row's world is absent from the table. Scoring
    every row against the table with its whole world removed, all replicates
    and reused copies included, gives training and held-out rows the same
    kind of reference (LOG.md, 2026-10-31 evening). A world absent from the
    reference, such as a held-out world, gets the full table."""

    def __init__(self, texts_by_world: Dict[str, Sequence[str]], max_df: int = 2):
        self.max_df = max_df
        self.by_world = {x: RarityTable(ts, max_df).df for x, ts in texts_by_world.items()}
        self.df: Dict[Tuple[str, ...], int] = {}
        for d in self.by_world.values():
            for g, c in d.items():
                self.df[g] = self.df.get(g, 0) + c

    @classmethod
    def from_rows(cls, rows: Sequence[Dict], max_df: int = 2) -> "WorldRarity":
        by: Dict[str, List[str]] = {}
        for r in rows:
            by.setdefault(r["world"], []).extend(r["texts"])
        return cls(by, max_df)

    def for_world(self, world: Optional[str]) -> _ExcludedRarity:
        return _ExcludedRarity(self.df, self.by_world.get(world, {}) if world is not None else {}, self.max_df)


def jaccard(a: Set, b: Set) -> float:
    return len(a & b) / len(a | b) if (a or b) else 0.0


def pair_features(a: str, b: str, rarity: RarityTable, embed: Callable[[str], Sequence[float]]) -> Dict[str, float]:
    ea, eb = embed(body(a)), embed(body(b))
    dot = sum(x * y for x, y in zip(ea, eb))
    na = sum(x * x for x in ea) ** 0.5
    nb = sum(x * x for x in eb) ** 0.5
    sa, sb = sentences(a), sentences(b)
    # sentence-order similarity: fraction of sentence pairs whose best matches in
    # the other message keep their relative order, averaged over both
    # directions so that the pair feature, and the set features built on it,
    # do not depend on which message is listed first (GPT Review of Full-Run
    # Analyses, 2026-10-31; version 1 used the a-to-b direction only)
    order = 0.5 * (_order_similarity(sa, sb, embed) + _order_similarity(sb, sa, embed))
    return {
        "rare_ngram_jaccard": jaccard(rarity.rare(a), rarity.rare(b)),
        "embedding_cosine": dot / (na * nb) if na and nb else 0.0,
        "sentence_order_similarity": order,
    }


def _order_similarity(sa: List[str], sb: List[str], embed) -> float:
    if len(sa) < 2 or len(sb) < 2:
        return 0.0
    vb = [embed(s) for s in sb]

    def best(s):
        v = embed(s)
        sims = [sum(x * y for x, y in zip(v, w)) for w in vb]
        return max(range(len(sims)), key=sims.__getitem__)

    idx = [best(s) for s in sa]
    agree = sum(1 for i, j in combinations(range(len(idx)), 2) if idx[i] <= idx[j])
    return agree / (len(idx) * (len(idx) - 1) / 2)


@register("set_relational", SET, "relational")
def f_set_relational(texts: Sequence[str], rarity: RarityTable, embed) -> Dict[str, float]:
    """Min, median, and max of each pairwise feature over a set's three
    pairs, so the result does not depend on presentation order."""
    pairs = [pair_features(a, b, rarity, embed) for a, b in combinations(texts, 2)]
    out = {}
    for k in pairs[0]:
        vals = sorted(p[k] for p in pairs)
        # prefixed with the registered parent, so the text-only guard can verify scope
        out[f"set_relational__{k}_min"] = vals[0]
        out[f"set_relational__{k}_median"] = median(vals)
        out[f"set_relational__{k}_max"] = vals[-1]
    return out


# ---------- registry access ----------

def text_features(text: str, families: Iterable[str] = ("formal", "attributional")) -> Dict[str, float]:
    fams = set(families)
    out = {}
    for f in REGISTRY.values():
        if f.scope == TEXT and f.family in fams:
            out[f.name] = f.fn(text)
    return out


def assert_text_only(feature_names: Iterable[str]) -> None:
    """Fail if any requested feature is anchored or unknown."""
    for n in feature_names:
        base = n.split("__")[0]
        f = REGISTRY.get(base)
        if f is None or f.scope not in TEXT_ONLY_SCOPES:
            raise PermissionError(f"feature {n!r} is not text-only and cannot enter a text-only model")


def pooled_set_features(texts: Sequence[str]) -> Dict[str, float]:
    """The pooled baseline (A_0): per-message features pooled by mean and
    maximum, with no cross-message comparison."""
    per = [text_features(t) for t in texts]
    out = {}
    for k in per[0]:
        vals = [p[k] for p in per]
        out[f"{k}__mean"] = sum(vals) / len(vals)
        out[f"{k}__max"] = max(vals)
    return out

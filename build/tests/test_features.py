import itertools
import random

import pytest

from residue.features import (REGISTRY, RarityTable, WorldRarity, ngrams, assert_text_only, f_set_relational, parse_sources, pooled_set_features,
                              register, text_features, ANCHORED)


def toy_embed(text):
    """Deterministic bag-of-letters embedding for tests."""
    v = [0.0] * 26
    for ch in text.lower():
        if "a" <= ch <= "z":
            v[ord(ch) - 97] += 1
    return v


A = "The generator stopped at 09:40. Engineers said the cooling loop ran hot. Backup power came on.\nSources: log"
B = "Engineers said the cooling loop ran hot. The generator stopped at 09:40. Backup power came on.\nSources: log"
C = "A pump failed in the west hall. Crews isolated the line. No injuries were reported."


def test_sources_line_excluded_from_formal_features():
    with_line = text_features(A)
    without = text_features(A.rsplit("\n", 1)[0])
    for k in ("tokens", "sentences", "type_token_ratio"):
        assert with_line[k] == without[k]
    assert with_line["has_sources_line"] == 1 and without["has_sources_line"] == 0


def test_set_features_are_order_invariant():
    rarity = RarityTable([C, "unrelated filler text about weather patterns today"])
    ref = f_set_relational([A, B, C], rarity, toy_embed)
    for perm in itertools.permutations([A, B, C]):
        assert f_set_relational(list(perm), rarity, toy_embed) == pytest.approx(ref)


def test_pooled_baseline_has_no_cross_message_terms():
    feats = pooled_set_features([A, B, C])
    assert all(k.endswith("__mean") or k.endswith("__max") for k in feats)
    assert_text_only(feats)


def test_anchored_feature_is_blocked_from_text_models():
    @register("toy_anchored", ANCHORED, "propositional")
    def _anch(text, world):
        return 0.0
    try:
        with pytest.raises(PermissionError):
            assert_text_only(["tokens", "toy_anchored"])
        with pytest.raises(PermissionError):
            assert_text_only(["world_id"])
    finally:
        REGISTRY.pop("toy_anchored")


def test_rarity_learned_only_from_given_texts():
    rarity = RarityTable([A] * 5)  # every trigram of A is common in training
    assert not rarity.rare(A)
    assert rarity.rare(C)



def test_world_rarity_matches_a_table_rebuilt_without_the_world():
    """Messages reused across a world's structures and replicates: each row's
    rare set must equal the one from a table rebuilt from the other worlds."""
    rng = random.Random(3)
    vocab = [f"w{i}" for i in range(40)]
    rows = []
    for x in ("a", "b", "c", "d"):
        shared = " ".join(rng.choice(vocab) for _ in range(30))
        own = [" ".join(rng.choice(vocab) for _ in range(30)) for _ in range(2)]
        # three sets reuse the same message, as sets in a block do
        rows += [{"world": x, "texts": [shared, shared + " " + own[0], own[1]]} for _ in range(3)]
    wr = WorldRarity.from_rows(rows)
    for r in rows:
        ref = RarityTable([t for q in rows if q["world"] != r["world"] for t in q["texts"]])
        for t in r["texts"]:
            assert wr.for_world(r["world"]).rare(t) == ref.rare(t)
    full = RarityTable([t for q in rows for t in q["texts"]])
    assert wr.for_world("held out").rare(A) == full.rare(A)  # a world outside the reference gets the full table
    # the defect this replaces: a table that includes the scored row's world finds none of its reused n-grams rare
    shared = rows[0]["texts"][0]
    elsewhere = set().union(*[ngrams(t, n) for q in rows if q["world"] != "a" for t in q["texts"] for n in (3, 4, 5)])
    unique = {g for n in (3, 4, 5) for g in ngrams(shared, n)} - elsewhere
    assert unique and not (full.rare(shared) & unique)
    assert unique <= wr.for_world("a").rare(shared)

def test_parse_sources():
    assert parse_sources("Body text.") is None
    assert parse_sources("Body text.\nSources:") == []
    assert parse_sources("Body text.\nSources: maintenance log, shift supervisor") == ["maintenance log", "shift supervisor"]

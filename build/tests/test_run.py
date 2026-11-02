from collections import Counter

import pytest

import run
from residue import readers as rd
from residue.models import MockModel
from residue.store import CallStore, StoreError
from residue.worlds import synthetic_world


def test_strip_deletes_only_the_sources_line():
    text = "First line.\nSecond line with Sources: inside.\nSources: log, officer\n"
    s, line = run.strip_sources(text)
    assert s == "First line.\nSecond line with Sources: inside." and line == "Sources: log, officer"
    assert text.rstrip().startswith(s)
    assert run.strip_sources("No attribution here.") == ("No attribution here.", None)


def test_families_balanced_within_each_replicate():
    worlds = [synthetic_world(i) for i in range(60)]
    fam = run.families(worlds, [0, 1, 2])
    for r in (0, 1, 2):
        assert Counter(v for (w, rr), v in fam.items() if rr == r) == {"A": 30, "B": 30}


def test_plan_covers_every_producer_and_arm():
    worlds = [synthetic_world(i) for i in range(2)]
    blocks = run.plan(worlds, [0])
    ids = [b[0] for b in blocks]
    assert len(ids) == len(set(ids)) == 2 * 7
    s2_other = [b for b in blocks if b[0].startswith("S2") and not b[0].endswith(run.PRIMARY)]
    assert all(set(b[2]) == {"IND-full-neutral", "DEP-full-neutral", "MIX-full-neutral"} for b in s2_other)
    news = [b for b in blocks if "|news|" in b[0]]
    assert all(b[1].producer == run.PRIMARY and set(b[2]) == {"R1", "R3", "SI-same", "SD-same"} for b in news)


def test_reader_prompts_never_name_conditions():
    for task, classes in rd.TASKS.items():
        ex = [("Example text.\nSources: a", c) for c, _ in classes]
        prompt = rd.render(task, ex, "Item text.\nSources: b")
        for c, _ in classes:
            assert c not in prompt.replace("class", "")


def test_reader_parse():
    assert rd.parse('{"A": 0.7, "B": 0.3}', 2) == pytest.approx([0.7, 0.3])
    assert rd.parse('Sure: {"A": 0.2, "B": 0.3, "C": 0.5}', 3) == pytest.approx([0.2, 0.3, 0.5])
    assert rd.parse('{"A": 0.9, "B": 0.9}', 2) is None
    assert rd.parse("no json", 2) is None


def test_failed_key_is_not_called_again(tmp_path):
    store = CallStore(str(tmp_path / "c.jsonl"), max_attempts=2)
    m = MockModel(fail_first={"x": 99})
    for _ in range(2):
        with pytest.raises(StoreError):
            store.get_or_call("ab12cd34ef", "x prompt", "mock", {}, m, 220, {})
    assert m.calls == 2
    again = CallStore(str(tmp_path / "c.jsonl"), max_attempts=2)
    with pytest.raises(StoreError):
        again.get_or_call("ab12cd34ef", "x prompt", "mock", {}, m, 220, {})
    assert m.calls == 2


def test_set_prompt_never_names_structures_and_probs_are_consistent():
    ex = [(["a", "b", "c"], c) for c, _ in rd.SET_CLASSES]
    prompt = rd.render_set(ex, ["x", "y", "z"])
    for c in ("IND", "DEP", "MIX"):
        assert c not in prompt
    assert prompt.count(rd.CACHE_SPLIT) == 1
    cp = rd.config_probs([0.1, 0.2, 0.3, 0.25, 0.15])
    assert cp["IND"] + cp["DEP"] + cp["MIX"] == pytest.approx(1)
    assert cp["same_root"]["12"] == pytest.approx(0.2 + 0.15)


def test_present_tracks_the_odd_message():
    for seed in range(20):
        shown, cfg = rd.present(["s1", "s2", "odd"], "MIX", str(seed))
        assert cfg == f"MIX{shown.index('odd') + 1}"
        assert rd.present(["s1", "s2", "s3"], "IND", str(seed))[1] == "IND"


def test_length_counts_the_body_only():
    from residue.store import validate_output
    body = " ".join(["word"] * 440)
    assert validate_output(body, 220) is None
    assert validate_output(body + " extra", 220) is not None
    assert validate_output(body + "\nSources: " + ", ".join(["Desk Log"] * 30), 220) is None
    assert validate_output(" ".join(["word"] * 109), 220) is not None


def test_independent_strip_agrees():
    for t in ["A.\nB.\nSources: log\n\n", "A.\nSources: x", "No line.", "Sources: only"]:
        exp = run.strip_expected(t)
        s, line = run.strip_sources(t)
        assert (exp is None and line is None) or exp == s


def test_reader_groups_keep_test_worlds_out_of_examples():
    import residue.readers as r2
    with pytest.raises(AssertionError):
        run.reader_groups({}, [], [("f", ["W1"], ["W1", "W2"])])


def test_set_relational_features_are_order_invariant():
    import itertools
    import random as _r
    from residue.features import RarityTable, f_set_relational, pair_features

    def embed(t):
        rng = _r.Random(t)
        return [rng.random() for _ in range(8)]
    texts = ["The pump stopped. Staff called the depot. The engine restarted.",
             "Staff called the depot. The pump stopped at two. It restarted later. Nobody lost supply.",
             "The engine restarted after an hour. The pump had stopped. A log recorded it."]
    rar = RarityTable(texts)
    a, b = texts[0], texts[1]
    assert pair_features(a, b, rar, embed) == pytest.approx(pair_features(b, a, rar, embed))
    ref = f_set_relational(texts, rar, embed)
    for perm in itertools.permutations(texts):
        got = f_set_relational(list(perm), rar, embed)
        assert got.keys() == ref.keys()
        for k in ref:
            assert got[k] == pytest.approx(ref[k])

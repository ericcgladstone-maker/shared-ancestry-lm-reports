"""Offline tests for build step 1. No network calls are possible here: the
only model is MockModel."""
import dataclasses
import random

import pytest

from residue import allocators as al
from residue import graphs as gr
from residue.audit import audit_block
from residue.dispatcher import BlockSpec, realize, run_block
from residue.fixtures import FIXTURES, HISTORY_TABLE
from residue.histories import (SET_CONFIGS, attribute_marginals, distinct_histories, history_of,
                               set_marginals)
from residue.models import MockModel
from residue.prompts import all_instructions, instruction_of, instruction_parts, lint
from residue.store import CallStore, StoreError
from residue.worlds import synthetic_world

ALL = {**gr.STUDY1, **gr.STUDY2}


def make_block(tmp_path, builders=ALL, index=3, replicate=1, model=None):
    w = synthetic_world(index)
    spec = BlockSpec(w, replicate, "incident", "mock", "A", seed=7)
    store = CallStore(str(tmp_path / "calls.jsonl"))
    m = model or MockModel()
    block = run_block(spec, builders, store, m, m.version, m.params())
    return w, spec, store, m, block


# ---------- fixtures, histories ----------

def test_every_builder_has_a_fixture():
    assert set(ALL) == set(FIXTURES)


def test_histories_from_fixtures_match_design_table():
    for cond, hist in HISTORY_TABLE.items():
        fx = FIXTURES[cond]
        assert history_of(fx["nodes"], fx["terminals"][0]) == hist, cond


def test_thirteen_distinct_histories():
    assert len(distinct_histories(HISTORY_TABLE)) == 13


def test_attribute_marginals_sum_to_one():
    hs = distinct_histories(HISTORY_TABLE)
    probs = {h: 1 / len(hs) for h in hs}
    for attr, dist in attribute_marginals(probs).items():
        assert abs(sum(dist.values()) - 1) < 1e-9, attr


def test_set_marginals_consistent():
    probs = {c: 1 / len(SET_CONFIGS) for c in SET_CONFIGS}
    structure, pairs = set_marginals(probs)
    assert abs(sum(structure.values()) - 1) < 1e-9
    # each pair shares a root under DEP and under one MIX configuration
    assert all(abs(p - 2 / 5) < 1e-9 for p in pairs.values())


# ---------- allocators ----------

def test_partition_rules_and_rotation_balance():
    counts = {0: 0, 1: 0}
    for i in range(60):
        w = synthetic_world(i)
        for r in range(3):
            for k in (2, 3):
                al.partition_packages(w, k, r, seed=1)  # asserts its own rules
            counts[al.colocated_pair_index(w, r)] += 1
    assert counts == {0: 90, 1: 90}


def test_diverse_and_pool():
    w = synthetic_world(5)
    pkgs, union = al.diverse_packages(w, 0, seed=1)
    assert union == al.full_record(w)
    draw = al.study2_draw(w, 0, 0, seed=1)
    assert len({p for p in draw}) == 3


# ---------- dispatcher, sharing, audit ----------

def test_full_block_passes_audit(tmp_path):
    w, spec, store, m, block = make_block(tmp_path)
    assert audit_block(block, w) == []


def key(block, cond, node):
    return block[cond][node].key


def test_intended_sharing(tmp_path):
    w, spec, store, m, b = make_block(tmp_path)
    # SI-same and SD-same share the slot 1 observation and its first rewrite
    assert key(b, "SI-same", "o1") == key(b, "SD-same", "o1")
    assert key(b, "SI-same", "w1") == key(b, "SD-same", "w1")
    assert key(b, "SI-same", "w2") != key(b, "SD-same", "w2")
    # the +3 compound branch descends from the same synthesis call as SD-same
    assert key(b, "SD-same+3", "syn") == key(b, "SD-same", "syn")
    assert key(b, "SD-same+3", "p1") != key(b, "SD-same+1", "p1")
    # chains share prefixes
    assert key(b, "R5", "r1") == key(b, "R1", "r1")
    # Study 2 sharing by generation slot
    assert key(b, "IND-full-neutral", "m1") == key(b, "DEP-full-neutral", "m1") == key(b, "MIX-full-neutral", "m1")
    assert key(b, "DEP-full-neutral", "m2") == key(b, "MIX-full-neutral", "m2")
    assert key(b, "MIX-full-neutral", "m3") == key(b, "IND-full-neutral", "m3")
    assert key(b, "IND-full-neutral", "m2") != key(b, "MIX-full-neutral", "m2")
    # concealment shares observations, not rewrites
    assert key(b, "IND-full-conceal", "o1") == key(b, "IND-full-neutral", "o1")
    assert key(b, "IND-full-conceal", "m1") != key(b, "IND-full-neutral", "m1")


def test_negative_controls_are_distinct_calls(tmp_path):
    w, spec, store, m, b = make_block(tmp_path)
    assert key(b, "NC0", "o1") != key(b, "D0", "o1")
    assert b["NC0"]["o1"].prompt == b["D0"]["o1"].prompt  # same input, separate draw
    assert key(b, "NCR1", "r1") != key(b, "R1", "r1")
    sib_keys = {key(b, "NC0", "x2"), key(b, "NC0", "x3"), key(b, "NCR1", "x2"), key(b, "NCR1", "x3")}
    others = {r.key for c, nodes in b.items() if c not in ("NC0", "NCR1") for r in nodes.values()}
    assert len(sib_keys) == 4 and not (sib_keys & others)


def test_compound_and_r5_get_full_record(tmp_path):
    w, spec, store, m, b = make_block(tmp_path)
    full = al.full_record(w)
    assert b["R5"]["o1"].package == full
    assert b["SD-same+3"]["o1"].package == full
    assert all(b["SI-same+3"][o].package == full for o in ("o1", "o2", "o3"))


# ---------- store-once ----------

def test_rerun_makes_no_calls(tmp_path):
    w, spec, store, m, b1 = make_block(tmp_path)
    store2 = CallStore(str(tmp_path / "calls.jsonl"))
    m2 = MockModel()
    b2 = run_block(spec, ALL, store2, m2, m2.version, m2.params())
    assert m2.calls == 0
    assert all(b1[c][n].text == b2[c][n].text for c in b1 for n in b1[c])


def test_changed_request_is_refused(tmp_path):
    w, spec, store, m, b = make_block(tmp_path, builders={"D0": gr.d0})
    store2 = CallStore(str(tmp_path / "calls.jsonl"))
    with pytest.raises(StoreError):
        run_block(spec, {"D0": gr.d0}, store2, m, "mock-2", m.params())  # model version changed


def test_retry_then_success_and_failure_logged(tmp_path):
    m = MockModel(fail_first={"Facts:": 2})
    w, spec, store, _, b = make_block(tmp_path, builders={"D0": gr.d0}, model=m)
    assert m.calls == 3
    lines = (tmp_path / "calls.jsonl").read_text().strip().splitlines()
    assert len(lines) == 3


# ---------- the audit catches miswiring ----------

def _miswire(builder, node_name, **changes):
    def build(w, r, s):
        g = builder(w, r, s)
        nodes = tuple(dataclasses.replace(n, **changes) if n.name == node_name else n for n in g.nodes)
        return dataclasses.replace(g, nodes=nodes)
    return build


def test_audit_rejects_compound_restarting_from_world(tmp_path):
    w = synthetic_world(2)
    bad = _miswire(gr.STUDY1["SD-same+3"], "p1", fn="observe", parents=(), package=al.full_record(w),
                   template_slot="src")
    _, _, _, _, b = make_block(tmp_path, builders={"SD-same+3": bad}, index=2)
    assert audit_block(b, w)


def test_audit_rejects_wrong_parent(tmp_path):
    bad = _miswire(gr.STUDY1["SD-same"], "w2", parents=("w1",))
    w, _, _, _, b = make_block(tmp_path, builders={"SD-same": bad})
    assert audit_block(b, w)


def test_audit_rejects_wrong_package(tmp_path):
    w0 = synthetic_world(3)
    partial = al.partition_packages(w0, 2, 1, seed=7)[0]
    bad = _miswire(gr.STUDY1["R5"], "o1", package=partial)
    w, _, _, _, b = make_block(tmp_path, builders={"R5": bad})
    assert audit_block(b, w)


# ---------- prompts ----------

def test_every_instruction_passes_lint():
    bad = {k: lint(v) for k, v in all_instructions().items() if lint(v)}
    assert bad == {}


def test_instruction_counts_and_pairing():
    ins = all_instructions()
    assert len(ins) == 2 * 2 * 4 * 6  # genres x families x functions x variants
    # the concealment variant differs from its neutral rewrite only in the final attribution line
    for genre in ("incident", "news"):
        for fam in ("A", "B"):
            for i in range(6):
                n = instruction_parts(f"{fam}:rewrite:{i}", genre)
                c = instruction_parts(f"{fam}:conceal:{i}", genre)
                assert n[:-1] == c[:-1] and n[-1] != c[-1]


def test_one_sources_instruction_for_every_neutral_function():
    for genre in ("incident", "news"):
        finals = {instruction_parts(f"A:{fn}:0", genre)[-1] for fn in ("observe", "rewrite", "synthesize")}
        assert len(finals) == 1


def test_instruction_bytes_depend_only_on_template(tmp_path):
    """Renderer check 1 and 2 (GPT prompt review, section III): every call
    with the same template gets byte-identical instructions, whatever its
    structure, depth, roots, or fan-in, including one- and three-input
    synthesis."""
    w, spec, store, m, b = make_block(tmp_path)
    seen = {}
    for cond, nodes in b.items():
        for r in nodes.values():
            seen.setdefault(r.template_id, set()).add(instruction_of(r.prompt))
    assert all(len(v) == 1 for v in seen.values()), {k: len(v) for k, v in seen.items() if len(v) > 1}
    assert b["F1"]["syn"].template_id == b["F3"]["syn"].template_id
    assert instruction_of(b["F1"]["syn"].prompt) == instruction_of(b["F3"]["syn"].prompt)


def test_format_line_identical_across_functions():
    ins = all_instructions()
    for genre in ("incident", "news"):
        # task sentences differ, but the style and format lines are the same text
        from residue.prompts import pools
        fmt = pools()["format_line"].format(words=pools()["genres"][genre]["target_words"])
        style = pools()["genres"][genre]["style"]
        assert all(fmt in v and style in v for k, v in ins.items() if k.startswith(genre))


def test_lint_catches_structure_words():
    for bad in ("Combine the three reports from independent sources.", "Compare the accounts.",
                "Reconcile any conflicts.", "This will be passed on to the next step."):
        assert lint(bad), bad

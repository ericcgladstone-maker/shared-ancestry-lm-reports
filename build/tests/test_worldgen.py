import json

import pytest

from residue.worldgen import (EVENT_TYPES, N_FACTS, WORLDS_PER_TYPE, check_problems, draft_bank, load_bank,
                              parse_draft, record_for_check, save_bank)

SOURCES = ["log", "sensor", "officer", "witness"]
ITEMS = [{"label": l, "source_can_know": True, "favors": None} for l in ["C"] + [f"F{i}" for i in range(1, 16)] + ["D1a", "D1b", "D2a", "D2b"]]
PASS = json.dumps({"items": ITEMS, "disputes": [{"dispute": 1, "same_referent": True, "incompatible": True, "one_side_obvious": False},
                                {"dispute": 2, "same_referent": True, "incompatible": True, "one_side_obvious": False}],
                   "inconsistencies": [], "real_referents": []})


def good_world_json(seed=0):
    return json.dumps({
        "event": "x", "sources": SOURCES, "names": [f"Place{seed}"],
        "core": {"text": f"At 09:{40 + seed % 10} unit {seed} shut down.", "source": "officer"},
        "facts": [{"text": f"Fact {i} for world {seed}: reading {i * 3} units.", "source": SOURCES[i % 4]} for i in range(N_FACTS)],
        "disputes": [
            {"kind": "cause", "about": "cause", "claims": [{"text": "The cause was A alone.", "source": "log"},
                                                           {"text": "The cause was B alone.", "source": "sensor"}]},
            {"kind": "count", "about": "count", "claims": [{"text": "Three pumps failed.", "source": "officer"},
                                                           {"text": "Four pumps failed.", "source": "witness"}]}]})


def test_parse_builds_explicit_pairs_and_shuffles():
    w, meta = parse_draft(good_world_json(1), "W000", "generator shutdown", 0)
    assert len(w.propositions) == 20
    by = w.by_id()
    pairs = [{by[a].text, by[b].text} for a, b in w.conflict_pairs()]
    assert pairs == [{"The cause was A alone.", "The cause was B alone."}, {"Three pumps failed.", "Four pumps failed."}]
    assert meta["disputes"][0]["kind"] == "cause" and meta["sources"] == SOURCES
    # the order depends on the world ID, so the core is not always first
    cores = {parse_draft(good_world_json(1), f"W{i:03d}", "generator shutdown", i)[0].core.pid for i in range(10)}
    assert len(cores) > 1
    parse_draft("```json\n" + good_world_json(2) + "\n```", "W001", "generator shutdown", 1)


@pytest.mark.parametrize("mutate", [
    lambda d: d.__setitem__("sources", SOURCES + ["a", "b", "c"]),            # seven sources
    lambda d: d["facts"][0].__setitem__("source", "radio"),                   # source not in the list
    lambda d: d["disputes"][0]["claims"][1].__setitem__("source", "log"),     # one source for a dispute
    lambda d: d["disputes"][1].__setitem__("kind", "cause"),                  # same kind twice
    lambda d: d["facts"].pop(),                                               # 14 facts
    lambda d: d.__setitem__("sources", ["log", "Log", "officer", "witness"]),  # case-only difference
])
def test_parse_rejects_bad_drafts(mutate):
    d = json.loads(good_world_json(3))
    mutate(d)
    with pytest.raises(ValueError):
        parse_draft(json.dumps(d), "W002", "generator shutdown", 2)


def test_record_for_check_labels_every_proposition():
    w, meta = parse_draft(good_world_json(4), "W003", "generator shutdown", 3)
    text, labels = record_for_check(w, meta)
    assert len(labels) == 20 and set(labels.values()) == set(w.ids())
    assert "Dispute 2, about count:" in text


def test_check_problems():
    assert check_problems(json.loads(PASS)) == []
    v = json.loads(PASS)
    v["disputes"][0]["same_referent"] = False
    v["items"][3]["favors"] = "D2a"
    v["items"][19]["source_can_know"] = False
    assert len(check_problems(v)) == 3
    v["items"] = v["items"][:10]
    assert any("10 of 20" in p for p in check_problems(v))


def test_draft_bank_with_mock_retry_and_flag(tmp_path):
    calls = {"n": 0, "checks": 0, "passes": 0}
    bad = json.loads(PASS)
    bad["items"][1]["source_can_know"] = False

    def draft(prompt):
        calls["n"] += 1
        return "not json" if calls["n"] == 1 else good_world_json(calls["n"])

    def check(prompt):
        # the first checked draft fails, and the 70th world fails every attempt, so it is flagged
        calls["checks"] += 1
        if calls["checks"] == 1 or calls["passes"] == 69:
            return json.dumps(bad)
        calls["passes"] += 1
        return PASS

    log_path = str(tmp_path / "draft_log.jsonl")
    bank = draft_bank(draft, log_path, check=check)
    assert len(bank) == len(EVENT_TYPES) * WORLDS_PER_TYPE == 70
    log = [json.loads(l) for l in open(log_path)]
    assert [r["accepted"] for r in log[:3]] == [False, False, True]
    assert "rejected for these reasons" in log[2]["prompt"]
    assert bank[-1][1]["flagged"] is True and len(bank[-1][1]["check_problems"]) == 1
    assert not any(m["flagged"] for _, m in bank[:-1])
    save_bank(bank, str(tmp_path / "bank.jsonl"))
    assert [w.world_id for w in load_bank(str(tmp_path / "bank.jsonl"))] == [w.world_id for w, _ in bank]
    # a rerun resumes from the log without drafting again
    n = calls["n"]
    again = draft_bank(draft, log_path, check=check)
    assert calls["n"] == n and [w.world_id for w, _ in again] == [w.world_id for w, _ in bank]
    assert again[-1][1]["flagged"] is True

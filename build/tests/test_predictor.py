import json
import random

from residue.fixtures import HISTORY_TABLE
from residue.histories import SET_CONFIGS
from residue.predictor import HISTORIES, StructurePredictor, to_json


def embed(text):
    v = [0.0] * 26
    for ch in text.lower():
        if "a" <= ch <= "z":
            v[ord(ch) - 97] += 1
    return v


def fake_message(cond, rng):
    """Length and hedging vary with the history, so the predictor has a
    learnable signal. Only for testing the interface."""
    h = HISTORY_TABLE[cond]
    n = 120 + 15 * h[4] + 10 * h[1] + rng.randint(0, 5)
    hedge = " possibly" * h[2]
    return ("word " * n) + hedge + ".\nSources: log"


def test_single_output_contract_and_consistency():
    rng = random.Random(0)
    conds = [c for c in HISTORY_TABLE for _ in range(8)]
    texts = [fake_message(c, rng) for c in conds]
    pred = StructurePredictor(embed, target_words=200).fit_single(texts, conds)
    out = pred.predict_single(texts[0])
    assert out["task"] == "single"
    total = sum(h["p"] for h in out["histories"])
    assert abs(total - 1) < 1e-9 and len(out["histories"]) == len(HISTORIES) == 13
    for attr, dist in out["attributes"].items():
        assert abs(sum(dist.values()) - 1) < 1e-9, attr
    json.loads(to_json(out))


def test_set_output_contract_and_consistency():
    rng = random.Random(1)
    sets, configs, pool = [], [], []
    for i in range(60):
        cfg = SET_CONFIGS[i % 5]
        base = [f"alpha{i} beta gamma delta {k}" for k in range(3)]
        if cfg == "DEP":
            base = [base[0] + f" extra{j}" for j in range(3)]
        elif cfg.startswith("MIX"):
            odd = int(cfg[-1]) - 1
            shared = base[0]
            base = [shared + f" v{j}" if j != odd else base[odd] for j in range(3)]
        texts = [b + ". " + "filler words here. " * 8 + "\nSources: log" for b in base]
        sets.append(texts)
        configs.append(cfg)
        pool.extend(texts)
    pred = StructurePredictor(embed, target_words=40).fit_set(sets, configs, [f"w{i // 5}" for i in range(60)])
    out = pred.predict_set(sets[-1])
    assert abs(sum(out["configurations"].values()) - 1) < 1e-9
    assert abs(sum(out["structure"].values()) - 1) < 1e-9
    assert set(out["pairs_same_root"]) == {"1-2", "1-3", "2-3"}
    assert all(0 <= v <= 1 for v in out["pairs_same_root"].values())

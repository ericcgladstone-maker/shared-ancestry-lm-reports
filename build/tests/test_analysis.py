import numpy as np

from residue.analysis import (assign_folds, auc_with_ci, holm, oof_predict, paired_delta_auc, three_way)


def synthetic(n_worlds=60, per=6, signal=1.0, seed=0):
    rng = np.random.default_rng(seed)
    worlds, y, X = [], [], []
    for w in range(n_worlds):
        offset = rng.normal(0, 1)  # world effect shared by all rows of a world
        for i in range(per):
            label = i % 2
            worlds.append(f"W{w:03d}")
            y.append(label)
            X.append([offset + signal * label + rng.normal(0, 1), rng.normal(0, 1)])
    return np.array(X), np.array(y), worlds


def folds_for(worlds):
    types = {w: f"t{int(w[1:]) % 14}" for w in set(worlds)}
    return assign_folds(sorted(set(worlds)), types, seed=1)


def test_folds_are_by_world_and_balanced():
    worlds = [f"W{i:03d}" for i in range(60)]
    f = assign_folds(worlds, {w: f"t{i % 14}" for i, w in enumerate(worlds)}, seed=1)
    sizes = np.bincount(list(f.values()))
    assert sizes.tolist() == [12] * 5


def test_signal_detected_and_null_not():
    X, y, worlds = synthetic(signal=1.0)
    probs, chosen = oof_predict(X, y, worlds, folds_for(worlds))
    res = auc_with_ci(y, probs, worlds, n=400)
    assert res["lo"] > 0.5 and res["p_gt_chance"] < 0.01
    X0, y0, w0 = synthetic(signal=0.0, seed=3)
    p0, _ = oof_predict(X0, y0, w0, folds_for(w0))
    r0 = auc_with_ci(y0, p0, w0, n=400)
    assert r0["lo"] < 0.5 < r0["hi"]


def test_paired_delta_detects_added_information():
    X, y, worlds = synthetic(signal=1.0)
    full, _ = oof_predict(X, y, worlds, folds_for(worlds))
    base, _ = oof_predict(X[:, 1:], y, worlds, folds_for(worlds))  # baseline lacks the signal column
    d = paired_delta_auc(y, full, base, worlds, n=400)
    assert d["delta"] > 0 and d["lo"] > 0


def test_three_way_rule():
    assert three_way(0.46, 0.54, 0.43, 0.57) == "equivalent"
    assert three_way(0.60, 0.70, 0.43, 0.57) == "leak beyond tolerance"
    assert three_way(0.50, 0.62, 0.43, 0.57) == "inconclusive"
    # an interval centered at chance that excludes 0.57 is not a leak
    assert three_way(0.47, 0.53, 0.43, 0.57) == "equivalent"


def test_holm():
    assert holm({"P2": 0.01, "P3": 0.03}) == {"P2": True, "P3": True}
    assert holm({"P2": 0.04, "P3": 0.02}) == {"P2": True, "P3": True}  # 0.02 <= 0.025, then 0.04 <= 0.05
    assert holm({"P2": 0.04, "P3": 0.03}) == {"P2": False, "P3": False}  # 0.03 > 0.025 stops the procedure
    assert holm({"P2": 0.03, "P3": 0.2}) == {"P2": False, "P3": False}

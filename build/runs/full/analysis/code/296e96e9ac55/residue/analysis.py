"""Evaluation core (design Part VIII).

World-grouped outer folds, nested selection of the penalty, out-of-fold
predictions, world-cluster bootstrap intervals, centered bootstrap p-values,
and the three-way rule. The estimand is the out-of-fold performance of the
fixed procedure on this world split, conditional on the registered templates.
"""
import random
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

PENALTIES = (0.01, 0.1, 1.0, 10.0)  # inverse regularization strength C, as listed in Part VIII


def assign_folds(world_ids: Sequence[str], event_types: Dict[str, str], k: int = 5, seed: int = 0) -> Dict[str, int]:
    """Seeded fold assignment balanced on event type. Fixed before any run."""
    rng = random.Random(seed)
    by_type: Dict[str, List[str]] = {}
    for w in sorted(set(world_ids)):
        by_type.setdefault(event_types[w], []).append(w)
    order: List[str] = []
    for t in sorted(by_type):
        ws = by_type[t][:]
        rng.shuffle(ws)
        order.extend(ws)
    return {w: i % k for i, w in enumerate(order)}


def _model(C: float):
    return make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=5000))


def _score(y, p) -> float:
    if p.ndim == 2 and p.shape[1] == 2:
        p = p[:, 1]
    if p.ndim == 1:
        return roc_auc_score(y, p)
    return roc_auc_score(y, p, multi_class="ovo", average="macro")


def oof_predict(X: np.ndarray, y: np.ndarray, worlds: Sequence[str], folds: Dict[str, int],
                inner_k: int = 4) -> Tuple[np.ndarray, List[float]]:
    """Out-of-fold class probabilities. The penalty is chosen by world-grouped
    inner cross-validation inside each training set, so test worlds never
    influence selection."""
    worlds = np.asarray(worlds)
    fold_of = np.array([folds[w] for w in worlds])
    classes = np.unique(y)
    probs = np.zeros((len(y), len(classes)))
    chosen = []
    for f in sorted(set(fold_of)):
        tr, te = fold_of != f, fold_of == f
        best_C, best = PENALTIES[0], -np.inf
        gkf = GroupKFold(n_splits=inner_k)
        for C in PENALTIES:
            scores = []
            for itr, iva in gkf.split(X[tr], y[tr], worlds[tr]):
                m = _model(C).fit(X[tr][itr], y[tr][itr])
                if len(np.unique(y[tr][iva])) < len(classes):
                    continue
                scores.append(_score(y[tr][iva], m.predict_proba(X[tr][iva])))
            if scores and np.mean(scores) > best:
                best, best_C = float(np.mean(scores)), C
        m = _model(best_C).fit(X[tr], y[tr])
        probs[te] = m.predict_proba(X[te])
        chosen.append(best_C)
    return probs, chosen


def auc(y: np.ndarray, probs: np.ndarray) -> float:
    return float(_score(y, probs))


def world_bootstrap(stat, worlds: Sequence[str], n: int = 2000, seed: int = 0) -> np.ndarray:
    """Resample whole worlds with replacement. `stat(index_array)` returns the
    statistic on the rows selected. Rows sharing a world stay together, so
    shared keys and shared synthesis outputs are never split."""
    worlds = np.asarray(worlds)
    uniq = np.unique(worlds)
    rows = {w: np.flatnonzero(worlds == w) for w in uniq}
    rng = np.random.default_rng(seed)
    out = np.empty(n)
    for b in range(n):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([rows[w] for w in pick])
        out[b] = stat(idx)
    return out


def interval(boot: np.ndarray, level: float) -> Tuple[float, float]:
    a = (1 - level) / 2
    return float(np.quantile(boot, a)), float(np.quantile(boot, 1 - a))


def centered_p(observed: float, boot: np.ndarray) -> float:
    """One-sided p-value for observed > 0 from the centered bootstrap: the
    proportion of replicates in which (T* - T) is at least T."""
    return float(np.mean((boot - observed) >= observed))


def auc_with_ci(y, probs, worlds, n=2000, seed=0, level=0.95) -> Dict[str, float]:
    y, probs = np.asarray(y), np.asarray(probs)

    def stat(idx):
        if len(np.unique(y[idx])) < 2:
            return 0.5
        return _score(y[idx], probs[idx])

    obs = stat(np.arange(len(y)))
    boot = world_bootstrap(stat, worlds, n, seed)
    lo, hi = interval(boot, level)
    return {"auc": obs, "lo": lo, "hi": hi, "p_gt_chance": centered_p(obs - 0.5, boot - 0.5)}


def paired_delta_auc(y, probs_a, probs_b, worlds, n=2000, seed=0, level=0.95) -> Dict[str, float]:
    """AUC(a) - AUC(b) on the same rows (P3), with a paired world bootstrap."""
    y = np.asarray(y)

    def stat(idx):
        if len(np.unique(y[idx])) < 2:
            return 0.0
        return _score(y[idx], probs_a[idx]) - _score(y[idx], probs_b[idx])

    obs = stat(np.arange(len(y)))
    boot = world_bootstrap(stat, worlds, n, seed)
    lo, hi = interval(boot, level)
    return {"delta": obs, "lo": lo, "hi": hi, "p_gt_zero": centered_p(obs, boot)}


def three_way(lo: float, hi: float, low_bound: float, high_bound: float) -> str:
    """Design Part V. Equivalent if the whole interval is inside the band,
    leak if it is wholly outside, otherwise inconclusive."""
    if low_bound <= lo and hi <= high_bound:
        return "equivalent"
    if lo > high_bound or hi < low_bound:
        return "leak beyond tolerance"
    return "inconclusive"


def holm(pvalues: Dict[str, float], alpha: float = 0.05) -> Dict[str, bool]:
    """Holm's step-down procedure over the primary family (P2, P3)."""
    order = sorted(pvalues, key=pvalues.get)
    out, m = {}, len(order)
    still = True
    for i, k in enumerate(order):
        ok = still and pvalues[k] <= alpha / (m - i)
        out[k] = ok
        still = still and ok
    return out

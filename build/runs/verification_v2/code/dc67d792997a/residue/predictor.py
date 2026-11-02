"""Structure predictor (design Part V-A).

Single message: a multinomial history head over the 13 histories. Attribute
probabilities are sums of history probabilities, so the two outputs cannot
contradict each other.

Set of three messages: a head over five configurations (IND, DEP, and MIX
with the odd message at each presented position). Structure and pair
probabilities are sums over the configurations.

Input is text only. No world identifier, condition label, key, or metadata
enters the predictor, and only text-scope and set-scope features are used.
"""
import json
from typing import Callable, Dict, List, Optional, Sequence

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .features import RarityTable, assert_text_only, f_set_relational, pooled_set_features, text_features
from .fixtures import HISTORY_TABLE
from .histories import ATTRIBUTES, SET_CONFIGS, attribute_marginals, set_marginals
from .store import validate_output

HISTORIES = sorted(set(HISTORY_TABLE.values()), key=str)
HIST_INDEX = {h: i for i, h in enumerate(HISTORIES)}


def history_label(condition: str) -> int:
    return HIST_INDEX[HISTORY_TABLE[condition]]


def _vec(d: Dict[str, float], names: List[str]) -> List[float]:
    return [float(d[n]) for n in names]


class StructurePredictor:
    def __init__(self, embed: Callable[[str], Sequence[float]], C: float = 1.0, target_words: int = 220):
        self.embed = embed
        self.C = C
        self.target_words = target_words
        self.single_names: List[str] = []
        self.set_names: List[str] = []
        self.single = None
        self.setm = None
        self.rarity: Optional[RarityTable] = None

    # ---------- single message ----------

    def fit_single(self, texts: Sequence[str], conditions: Sequence[str]) -> "StructurePredictor":
        feats = [text_features(t) for t in texts]
        self.single_names = sorted(feats[0])
        assert_text_only(self.single_names)
        X = np.array([_vec(f, self.single_names) for f in feats])
        y = np.array([history_label(c) for c in conditions])
        self.single = make_pipeline(StandardScaler(), LogisticRegression(C=self.C, max_iter=5000)).fit(X, y)
        return self

    def predict_single(self, text: str) -> Dict:
        flag = validate_output(text, self.target_words)
        x = np.array([_vec(text_features(text), self.single_names)])
        p = self.single.predict_proba(x)[0]
        probs = {HISTORIES[c]: 0.0 for c in range(len(HISTORIES))}
        for cls, pr in zip(self.single.classes_, p):
            probs[HISTORIES[cls]] = float(pr)
        marg = attribute_marginals(probs)
        return {
            "task": "single",
            "histories": [{"history": dict(zip(ATTRIBUTES, h)), "p": pr} for h, pr in probs.items()],
            "attributes": {a: {str(k): v for k, v in d.items()} for a, d in marg.items()},
            "input_flag": flag,
        }

    # ---------- set of messages ----------

    def _set_features(self, texts: Sequence[str]) -> Dict[str, float]:
        f = dict(pooled_set_features(texts))
        f.update(f_set_relational(texts, self.rarity, self.embed))
        return f

    def fit_set(self, sets: Sequence[Sequence[str]], configs: Sequence[str],
                rarity_texts: Sequence[str]) -> "StructurePredictor":
        self.rarity = RarityTable(rarity_texts)
        feats = [self._set_features(s) for s in sets]
        self.set_names = sorted(feats[0])
        assert_text_only(self.set_names)
        X = np.array([_vec(f, self.set_names) for f in feats])
        y = np.array([SET_CONFIGS.index(c) for c in configs])
        self.setm = make_pipeline(StandardScaler(), LogisticRegression(C=self.C, max_iter=5000)).fit(X, y)
        return self

    def predict_set(self, texts: Sequence[str]) -> Dict:
        assert len(texts) == 3, "a set has three messages"
        flags = [validate_output(t, self.target_words) for t in texts]
        x = np.array([_vec(self._set_features(texts), self.set_names)])
        p = self.setm.predict_proba(x)[0]
        cfg = {c: 0.0 for c in SET_CONFIGS}
        for cls, pr in zip(self.setm.classes_, p):
            cfg[SET_CONFIGS[cls]] = float(pr)
        structure, pairs = set_marginals(cfg)
        return {
            "task": "set",
            "configurations": cfg,
            "structure": structure,
            "pairs_same_root": {f"{a}-{b}": v for (a, b), v in pairs.items()},
            "input_flags": flags,
        }


def to_json(result: Dict) -> str:
    return json.dumps(result, sort_keys=True)

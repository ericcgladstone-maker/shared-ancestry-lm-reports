"""Local sentence embeddings (build spec section 1): nomic-embed-text served
by Ollama on this machine. Every text gets the same task prefix, so
similarities are symmetric. Vectors are cached on disk by text hash, so
reruns embed nothing twice and the cache is part of the released record.

Start the server with `ollama serve` (on this Mac, the binary is inside
/Applications/Ollama.app/Contents/Resources) and `ollama pull nomic-embed-text`.
"""
import json
import os
import threading
from typing import Dict, List, Sequence

import httpx

from .keys import sha256

MODEL = "nomic-embed-text"
PREFIX = "clustering: "
URL = "http://localhost:11434"


class Embedder:
    def __init__(self, cache_path: str, url: str = URL):
        self.cache_path = cache_path
        self.url = url
        self.http = httpx.Client(timeout=120)
        self._lock = threading.Lock()
        self.cache: Dict[str, List[float]] = {}
        if os.path.exists(cache_path):
            with open(cache_path) as fh:
                for line in fh:
                    rec = json.loads(line)
                    self.cache[rec["h"]] = rec["v"]
        self.digest = self._digest()

    def _digest(self) -> str:
        """The model's content digest, recorded with every run."""
        r = self.http.get(f"{self.url}/api/tags")
        r.raise_for_status()
        for m in r.json().get("models", []):
            if m["name"].split(":")[0] == MODEL:
                return m["digest"]
        raise RuntimeError(f"{MODEL} is not pulled")

    def many(self, texts: Sequence[str]) -> List[List[float]]:
        need = [t for t in dict.fromkeys(texts) if sha256(PREFIX + t) not in self.cache]
        for i in range(0, len(need), 64):
            batch = need[i:i + 64]
            r = self.http.post(f"{self.url}/api/embed", json={"model": MODEL, "input": [PREFIX + t for t in batch]})
            r.raise_for_status()
            vecs = r.json()["embeddings"]
            with self._lock:
                with open(self.cache_path, "a") as fh:
                    for t, v in zip(batch, vecs):
                        h = sha256(PREFIX + t)
                        self.cache[h] = v
                        fh.write(json.dumps({"h": h, "v": v}) + "\n")
        return [self.cache[sha256(PREFIX + t)] for t in texts]

    def __call__(self, text: str) -> List[float]:
        return self.many([text])[0]

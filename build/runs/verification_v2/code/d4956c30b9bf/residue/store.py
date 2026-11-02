"""Store-once call manifest (build spec section 2).

Each key is called once. A stored record is valid for a key only if its
request hash matches the request the key would produce now. The manifest is
append-only JSON Lines, so an interrupted run resumes without regenerating.
"""
import json
import os
import re
import threading
import time
from typing import Any, Callable, Dict, Optional

from .features import body
from .keys import request_hash, seed_for, sha256

# Talk about the task itself. Ordinary synthesis words such as "reports" or
# "sources" are deliberately absent, so validation cannot regenerate one
# structure more often than another (build spec section 6).
FORBIDDEN = re.compile(
    r"(\bas an ai\b|\blanguage model\b|\bthe (instructions|prompt)\b|\bi (cannot|can't|am unable to)\b)",
    re.IGNORECASE,
)


class StoreError(RuntimeError):
    pass


# Length window in multiples of the genre's target, inclusive. The design's 0.5 to 1.5 rule failed 155 of
# 280 Haiku observations in the first verification pass, so the accepted Haiku reports would have been its
# short, atypical ones. Widened to 2.0 for every producer and genre (GPT Review of Verification Run, 2026-10-30).
LENGTH_WINDOW = (0.5, 2.0)


def validate_output(text: str, target_words: int) -> Optional[str]:
    """Return None if valid, otherwise the reason. Length counts the
    whitespace-delimited words of the body, which excludes only a final
    Sources line, so the line's presence or length never decides a retry.
    The attribution line is never checked here, in any arm."""
    if not text or not text.strip():
        return "empty"
    n = len(body(text).split())
    lo, hi = LENGTH_WINDOW[0] * target_words, LENGTH_WINDOW[1] * target_words
    if n < lo or n > hi:
        return f"length {n} outside {lo:.0f}-{hi:.0f}"
    if FORBIDDEN.search(text):
        return "meta-commentary"
    return None


class CallStore:
    """Blocks may run in parallel threads. Keys belong to one block, so two
    threads never call the same key, but appends and the record table are
    shared and are guarded by a lock. A key that has failed every attempt is
    not called again, so conditions sharing it do not each retry it."""

    def __init__(self, path: str, max_attempts: int = 4, extra: Optional[Dict[str, Any]] = None):
        self.path = path
        self.max_attempts = max_attempts
        self.extra = dict(extra or {})  # stamped on every record, for example the code hash
        self.records: Dict[str, Dict[str, Any]] = {}
        self.failures: Dict[str, int] = {}
        self.calls_made = 0
        self._lock = threading.Lock()
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    rec = json.loads(line)
                    if rec.get("valid"):
                        if rec["key"] in self.records:
                            raise StoreError(f"two valid records for key {rec['key'][:12]}")
                        self.records[rec["key"]] = rec
                    else:
                        self.failures[rec["key"]] = self.failures.get(rec["key"], 0) + 1

    def _append(self, rec: Dict[str, Any]) -> None:
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def get_or_call(
        self,
        key: str,
        prompt: str,
        model_version: str,
        params: Dict[str, Any],
        call: Callable[[str, int], str],
        target_words: int,
        meta: Dict[str, Any],
    ) -> str:
        rh = request_hash(model_version, prompt, params)
        if key in self.records:
            rec = self.records[key]
            if rec["request_hash"] != rh:
                raise StoreError(f"key {key[:12]} stored with a different request; refusing to reuse")
            return rec["output"]
        if self.failures.get(key, 0) >= self.max_attempts:
            raise StoreError(f"key {key[:12]} already failed validation {self.max_attempts} times")
        last_reason = None
        for attempt in range(self.failures.get(key, 0), self.max_attempts):
            seed = seed_for(key, attempt)
            t0 = time.time()
            out = call(prompt, seed)
            self.calls_made += 1
            reason = validate_output(out, target_words)
            rec = {
                "key": key, "attempt": attempt, "seed": seed, "model": model_version, "params": params,
                "request_hash": rh, "prompt": prompt, "prompt_hash": sha256(prompt),
                "output": out, "output_hash": sha256(out), "valid": reason is None,
                "invalid_reason": reason, "time": time.time(), "seconds": round(time.time() - t0, 2),
                "usage": dict(getattr(call, "last_usage", None) or {}), **self.extra, **meta,
            }
            self._append(rec)
            if reason is None:
                with self._lock:
                    self.records[key] = rec
                return out
            with self._lock:
                self.failures[key] = self.failures.get(key, 0) + 1
            last_reason = reason
        raise StoreError(f"key {key[:12]} failed validation {self.max_attempts} times: {last_reason}")

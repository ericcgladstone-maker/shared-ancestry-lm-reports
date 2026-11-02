"""Model adapters. Only the mock exists in the offline build; real adapters
are added at the smoke-test step behind the same interface."""
import hashlib
from typing import Callable, Dict, Optional


class MockModel:
    """Returns canned text derived from the prompt and seed. Never touches a
    network. fail_first lets tests force validation failures."""

    def __init__(self, version: str = "mock-1", words: int = 220, fail_first: Optional[Dict[str, int]] = None):
        self.version = version
        self.words = words
        self.fail_first = dict(fail_first or {})
        self.calls = 0

    def params(self) -> Dict[str, object]:
        return {"sampling": "provider-default", "reasoning": "none"}

    def __call__(self, prompt: str, seed: int) -> str:
        self.calls += 1
        tag = hashlib.sha256(f"{prompt}|{seed}".encode()).hexdigest()[:12]
        for marker, n in list(self.fail_first.items()):
            if marker in prompt and n > 0:
                self.fail_first[marker] = n - 1
                return ""
        body = " ".join(f"w{tag}{i % 7}" for i in range(self.words - 3))
        return f"MOCK {tag} {body}\nSources: mock"


ModelFn = Callable[[str, int], str]

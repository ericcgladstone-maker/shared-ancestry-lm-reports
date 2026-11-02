"""Provider adapters (build spec section 1).

Keys are read at call time from the environment (ANTHROPIC_API_KEY,
OPENAI_API_KEY, GEMINI_API_KEY) or, failing that, from the macOS Keychain,
and are held only in memory.
Every adapter records token usage and enforces a hard spending cap per
provider, refusing a call once its projected spend would pass the cap.
Prices are per million tokens, from list prices to be confirmed against
provider pages, and are used only for the cap and for cost reports.
"""
import fcntl
import json
import os
import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from .keys import sha256

KEYCHAIN = {"anthropic": "residue-anthropic", "openai": "residue-openai", "google": "residue-gemini"}
ENV_KEYS = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY", "google": "GEMINI_API_KEY"}

# (input, output) dollars per million tokens, standard rates. Confirm on provider pages.
PRICES = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
    "gpt-6-luna": (0.10, 0.50),
    "gpt-6.1-terra": (1.00, 5.00),
    "gemini-3.5-flash-lite": (0.10, 0.40),
}

# Prompt caching, as multiples of the input price. Anthropic: reads 0.1 and five-minute writes 1.25 (Claude
# API reference, 2026-10-30). OpenAI: third-party rate cards list gpt-6.1-terra cached input at 0.05 of input
# and cache writes at 1.25, not confirmed on OpenAI's page, so the ledger charges reads at 0.1.
CACHE_READ = {"anthropic": 0.1, "openai": 0.1, "google": 1.0}
CACHE_WRITE = {"anthropic": 1.25, "openai": 1.25, "google": 1.0}

# ledger spend plus credit remaining in the provider console; OpenAI after a $5 top-up on 2026-10-30
CAPS = {"anthropic": 46.67, "openai": 22.94, "google": 24.99}


class BudgetExceeded(RuntimeError):
    pass


def key(provider: str) -> str:
    env = os.environ.get(ENV_KEYS[provider])
    if env:
        return env.strip()
    out = subprocess.run(["security", "find-generic-password", "-s", KEYCHAIN[provider], "-a", "eric", "-w"],
                         capture_output=True, text=True)
    if out.returncode != 0 or not out.stdout.strip():
        raise RuntimeError(f"no Keychain entry for {provider}")
    return out.stdout.strip()


@dataclass
class Ledger:
    """Spend per provider, persisted so caps hold across processes. Every
    check and every addition re-reads the file under an exclusive lock, so
    several processes or threads add to one total instead of overwriting
    each other's."""
    path: str
    spent: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self._lock = threading.Lock()
        self._read()

    def _read(self) -> None:
        if os.path.exists(self.path):
            with open(self.path) as fh:
                self.spent = json.load(fh)

    def check(self, provider: str, projected: float) -> None:
        with self._lock:
            self._read()
            if self.spent.get(provider, 0.0) + projected > CAPS[provider]:
                raise BudgetExceeded(f"{provider}: spent {self.spent.get(provider, 0):.4f}, next call would pass cap {CAPS[provider]}")

    def add(self, provider: str, cost: float) -> None:
        with self._lock:
            with open(self.path, "a+") as fh:
                fcntl.flock(fh, fcntl.LOCK_EX)
                fh.seek(0)
                text = fh.read()
                self.spent = json.loads(text) if text.strip() else {}
                self.spent[provider] = self.spent.get(provider, 0.0) + cost
                fh.seek(0)
                fh.truncate()
                json.dump(self.spent, fh, indent=1)
                fh.flush()
                fcntl.flock(fh, fcntl.LOCK_UN)


class Adapter:
    provider = ""

    def __init__(self, model: str, ledger: Ledger, max_output_tokens: int = 700, role: str = "producer"):
        self.model = model
        self.ledger = ledger
        self.max_output_tokens = max_output_tokens
        self.role = role
        self.cache_split: Optional[str] = None  # readers: the prompt before this marker is cached
        self._local = threading.local()

    @property
    def last_usage(self) -> Dict[str, int]:
        """Usage of the last call made by the current thread."""
        return getattr(self._local, "usage", {})

    @property
    def version(self) -> str:
        return f"{self.provider}:{self.model}"

    def params(self) -> Dict[str, object]:
        raise NotImplementedError

    def request_params(self) -> Dict[str, object]:
        """Everything that shapes the request apart from the prompt, for the request hash."""
        extra = {"cache_split": self.cache_split} if self.cache_split else {}
        return {**self.params(), "max_output_tokens": self.max_output_tokens, **extra}

    def _split(self, prompt: str):
        i = prompt.find(self.cache_split) if self.cache_split else -1
        return (prompt[:i], prompt[i:]) if i > 0 else (None, prompt)

    def _cost(self, inp: int, out: int, cache_read: int = 0, cache_write: int = 0) -> float:
        """inp is uncached input; cached tokens are priced separately."""
        pi, po = PRICES[self.model]
        return (inp + cache_read * CACHE_READ[self.provider] + cache_write * CACHE_WRITE[self.provider]) / 1e6 * pi \
            + out / 1e6 * po

    def __call__(self, prompt: str, seed: int) -> str:
        # projected worst case for this call: prompt tokens (about 4 chars each) plus the output cap
        self.ledger.check(self.provider, self._cost(len(prompt) // 3, self.max_output_tokens))
        for attempt in range(4):
            try:
                text, inp, out = self._call(prompt, seed)
                break
            except Exception as e:  # network errors, rate limits, server errors: same request again
                if attempt == 3 or "invalid_request" in str(e).lower() or "400" in str(e)[:40]:
                    raise
                time.sleep(5 * 2 ** attempt)
        extra = getattr(self._local, "extra", {})
        self._local.usage = {"input_tokens": inp, "output_tokens": out, **extra}
        self.ledger.add(self.provider, self._cost(inp, out, extra.get("cache_read", 0), extra.get("cache_write", 0)))
        return text

    def _call(self, prompt: str, seed: int):
        raise NotImplementedError


class AnthropicAdapter(Adapter):
    provider = "anthropic"

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        import anthropic
        self.client = anthropic.Anthropic(api_key=key("anthropic"))

    def params(self):
        if self.role == "producer":
            return {"thinking": {"type": "disabled"}, "effort": "high", "sampling": "provider-default"}
        if self.role == "drafter":
            return {"thinking": {"type": "adaptive"}, "effort": "medium", "sampling": "provider-default"}
        return {"thinking": {"type": "adaptive"}, "effort": "low", "sampling": "provider-default"}

    def _call(self, prompt, seed):
        p = self.params()
        prefix, rest = self._split(prompt)
        content = prompt if prefix is None else [
            {"type": "text", "text": prefix, "cache_control": {"type": "ephemeral"}}, {"type": "text", "text": rest}]
        r = self.client.messages.create(
            model=self.model, max_tokens=self.max_output_tokens,
            thinking=p["thinking"], output_config={"effort": p["effort"]},
            messages=[{"role": "user", "content": content}],
        )
        # a refusal returns no text, which fails validation and is logged and retried like any invalid output
        text = "" if r.stop_reason == "refusal" else "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        u = r.usage
        self._local.extra = {"stop_reason": r.stop_reason, "cache_read": getattr(u, "cache_read_input_tokens", 0) or 0,
                             "cache_write": getattr(u, "cache_creation_input_tokens", 0) or 0}
        return text, u.input_tokens, u.output_tokens


class OpenAIAdapter(Adapter):
    provider = "openai"

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        import openai
        self.client = openai.OpenAI(api_key=key("openai"))

    def params(self):
        # the world checker reasons; producers and readers do not
        effort = "high" if self.role == "checker" else "none"
        return {"reasoning_effort": effort, "sampling": "provider-default", "seed_sent": True}

    def _call(self, prompt, seed):
        prefix, rest = self._split(prompt)
        # gpt-6.1-terra wrote but never read a cache for prompts that differ after a shared prefix until the
        # prefix carried an explicit breakpoint (tested 2026-10-30); the text sent is unchanged
        content = prompt if prefix is None else [
            {"type": "text", "text": prefix, "prompt_cache_breakpoint": {"mode": "explicit"}},
            {"type": "text", "text": rest}]
        r = self.client.chat.completions.create(
            model=self.model, messages=[{"role": "user", "content": content}],
            max_completion_tokens=self.max_output_tokens, reasoning_effort=self.params()["reasoning_effort"], seed=seed,
        )
        u = r.usage
        d = getattr(u, "prompt_tokens_details", None)
        cached = getattr(d, "cached_tokens", 0) or 0
        written = getattr(d, "cache_write_tokens", 0) or 0
        self._local.extra = {"stop_reason": r.choices[0].finish_reason, "cache_read": cached, "cache_write": written}
        # prompt_tokens includes cached and written tokens; return the rest so _cost prices each once
        return r.choices[0].message.content or "", u.prompt_tokens - cached - written, u.completion_tokens


class GeminiAdapter(Adapter):
    """Calls the REST API directly. Gemini 3.5 models are controlled by
    thinkingLevel, which the SDK available for Python 3.9 cannot send, and
    they ignore thinkingBudget (a budget of 1 still produced about 670
    reasoning tokens in the smoke test)."""
    provider = "google"
    URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        import httpx
        self.http = httpx.Client(timeout=120, headers={"x-goog-api-key": key("google")})

    def params(self):
        return {"thinkingLevel": "MINIMAL", "sampling": "provider-default", "seed_sent": True}

    def _call(self, prompt, seed):
        body = {"contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": self.max_output_tokens, "seed": seed,
                                     "thinkingConfig": {"thinkingLevel": "MINIMAL"}}}
        r = self.http.post(self.URL.format(model=self.model), json=body)
        r.raise_for_status()
        d = r.json()
        cand = d["candidates"][0]
        text = "".join(part.get("text", "") for part in cand.get("content", {}).get("parts", []))
        u = d.get("usageMetadata", {})
        out = (u.get("candidatesTokenCount") or 0) + (u.get("thoughtsTokenCount") or 0)
        self._local.extra = {"stop_reason": cand.get("finishReason")}
        return text, u.get("promptTokenCount") or 0, out


def provider_of(model: str) -> str:
    return "anthropic" if model.startswith("claude") else "openai" if model.startswith("gpt") else "google"


def make(model: str, ledger: Ledger, role: str = "producer", max_output_tokens: int = 700) -> Adapter:
    if model.startswith("claude"):
        return AnthropicAdapter(model, ledger, max_output_tokens, role)
    if model.startswith("gpt"):
        return OpenAIAdapter(model, ledger, max_output_tokens, role)
    if model.startswith("gemini"):
        return GeminiAdapter(model, ledger, max_output_tokens, role)
    raise ValueError(model)

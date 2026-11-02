"""Canonical call keys, seeds, and request hashes (build spec section 2).

A call key names one logical model call. It includes the keys of the call's
parents, so two calls share a key, and therefore a stored output, exactly when
everything that determines their request is the same.
"""
import hashlib
import json
from typing import Any, Dict, List, Optional


def canonical(obj: Any) -> str:
    """Serialize with sorted keys and no whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_key(
    *,
    study: str,
    world: str,
    replicate: int,
    genre: str,
    producer: str,
    family: str,
    role: str,
    template_id: str,
    package_id: Optional[str],
    parent_keys: List[str],
    condition_tag: Optional[str] = None,
) -> str:
    """Return the hex digest identifying one logical call.

    condition_tag is set only where the design requires a call to be distinct
    per condition: the NC0 and NCR1 terminals and their unused siblings.
    Parent order is kept, because a synthesis sees its inputs in order.
    """
    fields: Dict[str, Any] = {
        "study": study,
        "world": world,
        "replicate": replicate,
        "genre": genre,
        "producer": producer,
        "family": family,
        "role": role,
        "template_id": template_id,
        "package_id": package_id,
        "parent_keys": list(parent_keys),
        "condition_tag": condition_tag,
    }
    return sha256(canonical(fields))


def seed_for(key: str, attempt: int = 0) -> int:
    """Seed sent to providers that accept one. Retries change the seed."""
    digest = key if attempt == 0 else sha256(canonical({"key": key, "attempt": attempt}))
    return int(digest[:8], 16) % (2**31 - 1)


def request_hash(model_version: str, prompt: str, params: Dict[str, Any]) -> str:
    """Hash of everything sent to the provider. A stored output is valid for a
    key only if this hash matches the request the key would produce now."""
    return sha256(canonical({"model": model_version, "prompt": prompt, "params": params}))

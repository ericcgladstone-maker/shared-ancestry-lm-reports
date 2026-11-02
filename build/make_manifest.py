"""Record the state of the full run: hashes, counts, environment, and an analysis code snapshot.

    python make_manifest.py

Writes runs/full/MANIFEST.json. Copies the analysis code (the scripts run after
the producer snapshot in runs/full/code/, and the residue package as it stood
when the analyses ran) to runs/full/analysis/code/<hash>/, and a gzip copy of
the embedding cache to runs/full/embeddings/, because the cache otherwise
lives only outside Drive. Reads every file, changes none. Rerun it to check
that nothing has changed since: the hashes must match.
"""
import gzip
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
FULL = os.path.join(HERE, "runs", "full")
CACHE = os.path.expanduser("~/.cache/residue/embeddings.jsonl")
ANALYSIS_CODE = ["analyze.py", "analyze_secondary.py", "analyze_anchored.py", "inference.py", "permutation_null.py",
                 "judge_run.py", "make_walkthrough.py", "make_manifest.py", "run.py", "requirements.txt",
                 "replicate.py", "analyze_replication.py", "analyze_salience.py", "analyze_relational_checks.py", "analyze_transfer.py", "make_numbers.py", "analyze_review_checks.py", "run_depth.py", "analyze_depth.py", "analyze_generation_order.py", "analyze_comparators.py", "analyze_copying.py", "make_validation_sample.py",
                 "score_validation.py"]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def lines(path):
    with open(path, "rb") as fh:
        return sum(1 for _ in fh)


def tree(root, rel_to):
    out = {}
    for d, _, fs in os.walk(root):
        if "__pycache__" in d:
            continue
        for f in sorted(fs):
            if f == ".DS_Store" or f.endswith(".pyc") or os.path.join(d, f) == os.path.join(FULL, "MANIFEST.json"):
                continue
            p = os.path.join(d, f)
            out[os.path.relpath(p, rel_to)] = {"sha256": sha(p), "bytes": os.path.getsize(p),
                                               "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(p)))}
            if f.endswith(".jsonl"):
                out[os.path.relpath(p, rel_to)]["lines"] = lines(p)
    return out


def main():
    M = {"written": time.strftime("%Y-%m-%d %H:%M:%S"), "python": sys.version.split()[0], "platform": platform.platform()}
    M["pip_freeze"] = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True).stdout.split()
    try:
        tags = json.load(urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5))
        M["ollama_models"] = {m["name"]: m["digest"] for m in tags["models"]}
    except OSError as e:
        M["ollama_models"] = f"unavailable: {e}"

    # analysis code snapshot, named by the hash of its file hashes
    files = ANALYSIS_CODE + sorted(os.path.join("residue", f) for f in os.listdir(os.path.join(HERE, "residue"))
                                   if f.endswith(".py"))
    fh = {f: sha(os.path.join(HERE, f)) for f in files}
    code_hash = hashlib.sha256(json.dumps(fh, sort_keys=True).encode()).hexdigest()
    dest = os.path.join(FULL, "analysis", "code", code_hash[:12])
    if not os.path.exists(dest):
        for f in files:
            os.makedirs(os.path.dirname(os.path.join(dest, f)), exist_ok=True)
            shutil.copy2(os.path.join(HERE, f), os.path.join(dest, f))
        with open(os.path.join(dest, "MANIFEST.json"), "w") as out:
            json.dump({"code_hash": code_hash, "files": fh}, out, indent=1)
    M["analysis_code"] = {"hash": code_hash, "snapshot": os.path.relpath(dest, HERE), "files": fh}
    with open(os.path.join(FULL, "config.jsonl")) as cf:
        M["producer_code"] = sorted({json.loads(x)["code_hash"] for x in cf})

    # embedding cache copy
    edir = os.path.join(FULL, "embeddings")
    os.makedirs(edir, exist_ok=True)
    gz = os.path.join(edir, "embeddings.jsonl.gz")
    src_hash = sha(CACHE)
    meta = os.path.join(edir, "source.json")
    if not (os.path.exists(meta) and json.load(open(meta))["sha256"] == src_hash):
        with open(CACHE, "rb") as a, gzip.open(gz, "wb", compresslevel=6) as b:
            shutil.copyfileobj(a, b, 1 << 20)
        with open(meta, "w") as out:
            json.dump({"source": CACHE, "sha256": src_hash, "lines": lines(CACHE), "copied": M["written"],
                       "note": "gunzip and compare sha256 to restore ~/.cache/residue/embeddings.jsonl"}, out, indent=1)
    M["embedding_cache"] = json.load(open(meta))

    M["records"] = tree(os.path.join(HERE, "runs"), HERE)
    M["records"].update(tree(os.path.join(HERE, "worlds"), HERE))
    M["records"].update(tree(os.path.join(HERE, "prompts"), HERE))
    M["records"].update(tree(os.path.join(HERE, "walkthroughs"), HERE))
    M["records"].update(tree(os.path.join(HERE, "smoke"), HERE))
    M["records"].update(tree(os.path.join(HERE, "validation"), HERE))
    M["records"].update(tree(os.path.join(HERE, "rating"), HERE))
    with open(os.path.join(FULL, "MANIFEST.json"), "w") as out:
        json.dump(M, out, indent=1)
    print(f"{len(M['records'])} files hashed; analysis code {code_hash[:12]}; embeddings {src_hash[:12]}")


if __name__ == "__main__":
    main()

"""Verification and full runs (build spec section 13, steps 3 and 4).

    python run.py verification [--dry-run] [--workers N]
    python run.py full [--dry-run] [--workers N]

A run generates every producer call for its worlds through the store-once
manifest, then (verification only) runs the engineering checks of design
Part IX step 2 and writes runs/verification/report.md: the lineage audit,
key sharing, template and package rules, validation failures, the
attribution field and stripping, observer diversity, the single-input
synthesis preflight (principle 1), a matcher spot check, reader format
checks, and each provider's full-run cost projected from measured tokens.

--dry-run uses the mock model and mock readers, spends nothing, and writes
to runs/<phase>-dry/. Every run first copies the code, prompt pools, and
world bank into runs/<phase>/code/<hash>/ and stamps that hash on every
record, so each output can be traced to the exact code that produced it.
Runs resume: a key with a valid stored output is never called again.
"""
import argparse
import json
import os
import random
import shutil
import sys
import tempfile
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from residue import adapters  # noqa: E402
from residue import graphs as gr  # noqa: E402
from residue import readers as rd  # noqa: E402
from residue.audit import audit_block  # noqa: E402
from residue.dispatcher import BlockSpec, run_block  # noqa: E402
from residue.features import body, jaccard, ngrams, parse_sources  # noqa: E402
from residue.fixtures import FIXTURES  # noqa: E402
from residue.keys import canonical, make_key, sha256  # noqa: E402
from residue.matcher import match  # noqa: E402
from residue.models import MockModel  # noqa: E402
from residue.prompts import PER_FAMILY, render_with_inputs, target_words, template_id  # noqa: E402
from residue.store import CallStore, StoreError  # noqa: E402
from residue.worldgen import load_bank  # noqa: E402

RUN_SEED = 20261030
PRIMARY = "gemini-3.5-flash-lite"
PRODUCERS = (PRIMARY, "claude-haiku-5-5", "gpt-6-luna")
READERS = ("claude-sonnet-5-5", "gpt-6.1-terra")
JUDGE = "claude-sonnet-5-5"
CACHE_READ_PRICE = {"anthropic": 0.1, "openai": 0.5}  # fraction of input price; assumed, confirm on provider pages
# Output tokens per word, measured on untruncated verification outputs (2026-10-30). The cap is set per
# producer so that it binds equally: Claude's tokenizer uses about two tokens per word, and a single
# 4/3 ratio truncated 425 of 510 Haiku outputs in the first verification pass.
# Gemini (1.32) and Luna (1.36) measured within rounding of 4/3 and never reached the cap, so they keep it.
TOKENS_PER_WORD = {"gemini-3.5-flash-lite": 4 / 3, "claude-haiku-5-5": 2.0, "gpt-6-luna": 4 / 3}
EMBED_CACHE = os.path.expanduser("~/.cache/residue/embeddings.jsonl")  # recomputable, too large for Drive
SNAPSHOT = ["run.py", "requirements.txt", "residue", "prompts", "worlds/bank.jsonl", "worlds/assignment.json"]


# ---------- record keeping ----------

def snapshot(run_dir):
    files = []
    for item in SNAPSHOT:
        p = os.path.join(HERE, item)
        if os.path.isdir(p):
            files += sorted(os.path.join(item, f) for f in os.listdir(p) if f.endswith((".py", ".json")))
        else:
            files.append(item)
    hashes = [(f, sha256(open(os.path.join(HERE, f), encoding="utf-8").read())) for f in files]
    h = sha256(canonical(hashes))
    dest = os.path.join(run_dir, "code", h[:12])
    if not os.path.exists(dest):
        for f, _ in hashes:
            os.makedirs(os.path.dirname(os.path.join(dest, f)), exist_ok=True)
            shutil.copy2(os.path.join(HERE, f), os.path.join(dest, f))
        with open(os.path.join(dest, "MANIFEST.json"), "w") as fh:
            json.dump({"code_hash": h, "files": dict(hashes), "time": time.time()}, fh, indent=1)
    return h


# ---------- the plan ----------

def load_worlds(phase):
    bank = {w.world_id: w for w in load_bank(os.path.join(HERE, "worlds", "bank.jsonl"))}
    a = json.load(open(os.path.join(HERE, "worlds", "assignment.json")))
    ids = a["verification"] if phase == "verification" else sorted(a["folds"])
    return [bank[i] for i in sorted(ids)]


def replicates(phase):
    return [0] if phase == "verification" else [0, 1, 2]


def families(worlds, reps):
    """Prompt family by trial (principle 4), balanced within each replicate.
    One family per world and replicate, shared by producers and genres, so
    producer and genre transfer compare matched trials."""
    out = {}
    for r in reps:
        order = sorted(w.world_id for w in worlds)
        random.Random(f"family|{RUN_SEED}|{r}").shuffle(order)
        for i, wid in enumerate(order):
            out[(wid, r)] = "A" if i < len(order) // 2 else "B"
    return out


def plan(worlds, reps):
    """Every block of the run: (block id, spec, builders)."""
    fam = families(worlds, reps)
    s2_others = {k: v for k, v in gr.STUDY2.items() if k.endswith("-full-neutral")}
    out = []
    for w in worlds:
        for r in reps:
            f = fam[(w.world_id, r)]
            for p in PRODUCERS:
                out.append((f"S1|{w.world_id}|{r}|incident|{p}", BlockSpec(w, r, "incident", p, f, RUN_SEED), gr.STUDY1))
                out.append((f"S2|{w.world_id}|{r}|incident|{p}", BlockSpec(w, r, "incident", p, f, RUN_SEED),
                            gr.STUDY2 if p == PRIMARY else s2_others))
            out.append((f"S1|{w.world_id}|{r}|news|{PRIMARY}", BlockSpec(w, r, "news", PRIMARY, f, RUN_SEED),
                        {k: gr.STUDY1[k] for k in gr.SECOND_GENRE}))
    return out


def max_tokens(genre, producer):
    """Build spec section 1: 1.8 times the genre's target length, in the producer's tokens."""
    return round(1.8 * target_words(genre) * TOKENS_PER_WORD[producer])


class MockReader:
    version = "mock-reader"
    last_usage = {"input_tokens": 0, "output_tokens": 0}

    def __call__(self, prompt, seed):
        n = 3 if "\nC: " in prompt else 2
        return json.dumps({rd.LETTERS[i]: 1 / n for i in range(n)})


class MockJudge:
    version = "mock-judge"
    last_usage = {}

    def __call__(self, prompt, seed):
        return '{"refers_to_inputs": false, "compares_inputs": false, "quote": ""}'


def producers(dry, ledger):
    if dry:
        return {(p, g): MockModel(version=f"mock:{p}") for p in PRODUCERS for g in ("incident", "news")}
    return {(p, g): adapters.make(p, ledger, role="producer", max_output_tokens=max_tokens(g, p))
            for p in PRODUCERS for g in ("incident", "news")}


def req_params(m):
    return m.request_params() if hasattr(m, "request_params") else m.params()


def run_blocks(blocks, store, models, workers):
    results, failures, errors = {}, {}, {}
    stop = threading.Event()

    def one(bid, spec, builders):
        if stop.is_set():
            return bid, None, {}
        m = models[(spec.producer, spec.genre)]
        f = {}
        try:
            return bid, run_block(spec, builders, store, m, m.version, req_params(m), failures=f), f
        except adapters.BudgetExceeded:
            stop.set()
            raise

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(one, *b) for b in blocks]
        for i, fut in enumerate(as_completed(futs)):
            try:
                bid, res, f = fut.result()
                if res is not None:
                    results[bid] = res
                if f:
                    failures[bid] = f
            except Exception as e:
                errors[str(i)] = f"{type(e).__name__}: {e}"
            if (i + 1) % 20 == 0 or i + 1 == len(futs):
                print(f"  blocks {i + 1}/{len(futs)}, calls made {store.calls_made}", flush=True)
    return results, failures, errors


# ---------- checks ----------

def terminal(res, cond):
    return res[cond][FIXTURES[cond]["terminals"][0]]


def strip_sources(text):
    """Stripping (principle 9): delete the final Sources line and nothing
    else. Returns (stripped text, deleted line or None)."""
    t = text.rstrip()
    lines = t.splitlines()
    if not lines or not lines[-1].strip().lower().startswith("sources:"):
        return text, None
    cut = t.rfind("\n")
    return (t[:cut].rstrip() if cut >= 0 else ""), lines[-1]


def source_validity(names, world_sources):
    low = [s.lower() for s in world_sources]
    ok = [n for n in names if any(n.lower() in s or s in n.lower() for s in low)]
    return len(ok), len(names)


def check_templates(res):
    problems = []
    obs = {r.template_id for c in res.values() for r in c.values() if r.fn == "observe"}
    syn = {r.template_id for c in res.values() for r in c.values() if r.fn == "synthesize"}
    if len(obs) > 1:
        problems.append(f"observers use {len(obs)} templates")
    if len(syn) > 1:
        problems.append(f"syntheses use {len(syn)} templates")
    return problems


def manifest_stats(path):
    recs = [json.loads(l) for l in open(path, encoding="utf-8")]
    by = defaultdict(lambda: {"attempts": 0, "invalid": 0, "reasons": Counter()})
    for r in recs:
        k = (r["model"], r.get("fn", "?"), r.get("condition_first_seen", "?"))
        by[k]["attempts"] += 1
        if not r["valid"]:
            by[k]["invalid"] += 1
            by[k]["reasons"][(r["invalid_reason"] or "")[:20]] += 1
    return recs, by


def call_cost(model, usage):
    pi, po = adapters.PRICES.get(model.split(":", 1)[-1], (0, 0))
    return usage.get("input_tokens", 0) / 1e6 * pi + usage.get("output_tokens", 0) / 1e6 * po


# Version 1 of this prompt judged the whole output. It counted the required Sources line, whose in-event
# record names ("Incident Report", "Desk Log") it read as input documents, and phrases copied from the
# input. Its judgments are kept in preflight_judgments.jsonl. Version 2 shows the inputs and judges the body.
JUDGE_PROMPT = """A writer received the input text or texts below and wrote the report that follows them. Answer two questions about the written report only.

1. Does the report refer to its inputs as documents in a way the inputs themselves do not? Examples: "the reports differ", "another account says", "the provided documents", "no second report confirms". Do not count attributions to people, logs, records, or instruments inside the event (such as "the controller log recorded"), statements that sources inside the event disagree, or wording copied from an input.
2. Does the report compare or weigh its input texts against each other, as texts? Do not count reporting that sources inside the event disagree.

Reply with JSON only: {{"refers_to_inputs": true or false, "compares_inputs": true or false, "quote": "the shortest phrase showing a yes, or empty"}}

{inputs}

Written report:
-----
{text}
-----"""


def preflight(results, worlds, fam, store, model, judge, out_dir):
    """Principle 1: 50 synthesis outputs each for one, two, and three inputs
    on the primary producer. F1 is dropped if more than 5% of single-input
    outputs refer to other or missing sources or compare sources."""
    rows = []
    jp = os.path.join(out_dir, "preflight_judgments_v2.jsonl")
    jl = open(jp, "a", encoding="utf-8")
    done = set()
    if os.path.exists(jp):
        done = {json.loads(l)["key"] for l in open(jp, encoding="utf-8")}
    tw = target_words("incident")
    for w in worlds:
        res = results.get(f"S1|{w.world_id}|0|incident|{PRIMARY}")
        if not res or "SI-same" not in res:
            continue
        si = res["SI-same"]
        pool = [si[n] for n in ("o1", "o2", "o3", "w1", "w2", "w3")]
        f = fam[(w.world_id, 0)]
        rng = random.Random(f"preflight|{RUN_SEED}|{w.world_id}")
        for k in (1, 2, 3):
            for j in range(5):
                inputs = rng.sample(pool, k)
                tid = template_id(f, "synthesize", (5 * k + j) % PER_FAMILY)
                key = make_key(study="PREFLIGHT", world=w.world_id, replicate=0, genre="incident", producer=PRIMARY,
                               family=f, role=f"pre:k{k}:j{j}", template_id=tid, package_id=None,
                               parent_keys=[x.key for x in inputs])
                prompt = render_with_inputs(tid, [x.text for x in inputs], "incident")
                try:
                    text = store.get_or_call(key, prompt, model.version, req_params(model), model, tw,
                                             {"condition_first_seen": "PREFLIGHT", "node": f"k{k}", "fn": "synthesize"})
                except StoreError as e:
                    rows.append({"world": w.world_id, "k": k, "key": key, "failed": str(e)})
                    continue
                if key in done:
                    continue
                shown = "\n\n".join(f"Input {i + 1}:\n-----\n{x.text.strip()}\n-----" for i, x in enumerate(inputs))
                reply = judge(JUDGE_PROMPT.format(inputs=shown, text=strip_sources(text)[0]), 1)
                try:
                    v = json.loads(reply[reply.index("{"):reply.rindex("}") + 1])
                except ValueError:
                    v = {"refers_to_inputs": None, "compares_inputs": None, "quote": reply[:200]}
                rec = {"key": key, "world": w.world_id, "k": k, "template": tid, "text": text, **v,
                       "usage": dict(getattr(judge, "last_usage", {}) or {})}
                jl.write(json.dumps(rec, ensure_ascii=False) + "\n")
                jl.flush()
    jl.close()
    if os.path.exists(jp):
        rows += [json.loads(l) for l in open(jp, encoding="utf-8")]
    return rows


def reader_items(results, worlds):
    """Terminal texts of the primary producer's incident blocks, by world and condition."""
    out = {}
    for w in worlds:
        res = results.get(f"S1|{w.world_id}|0|incident|{PRIMARY}")
        if res:
            out[w.world_id] = {c: terminal(res, c).text for c in res}
    return out


def run_readers(items, readers, log, workers):
    """Leave-one-world-out among the verification worlds: a world's items are
    read with examples drawn from the other nine."""
    jobs = []
    for task, classes in rd.TASKS.items():
        conds = [c for c, _ in classes]
        for wid in sorted(items):
            if not all(c in items[wid] for c in conds):
                continue
            pool = {c: [(o, items[o][c]) for o in items if o != wid and c in items[o]] for c in conds}
            ex = rd.draw_examples(task, pool, f"{RUN_SEED}|verification|{wid}")
            for c in conds:
                prompt = rd.render(task, ex, items[wid][c])
                for name, reader in readers.items():
                    jobs.append((reader, name, task, f"{wid}|{c}", prompt, c))
    out = []
    with ThreadPoolExecutor(max_workers=workers) as exr:
        for fut in as_completed([exr.submit(log.read, *j) for j in jobs]):
            out.append(fut.result())
    return out


def count_plan(phase):
    """Exact producer call counts for a phase, by realizing its plan with the
    mock model in a scratch store. Shared keys are counted once."""
    worlds, reps = load_worlds(phase), replicates(phase)
    counts = Counter()
    with tempfile.TemporaryDirectory() as tmp:
        store = CallStore(os.path.join(tmp, "calls.jsonl"))
        seen = set()
        for bid, spec, builders in plan(worlds, reps):
            m = MockModel(version=f"mock:{spec.producer}")
            run_block(spec, builders, store, m, m.version, m.params())
            for k, rec in store.records.items():
                if k not in seen:
                    seen.add(k)
                    counts[(spec.producer, spec.genre, rec["fn"])] += 1
    return counts


# ---------- verification report ----------

def verification_report(phase_dir, worlds, results, failures, errors, store, ledger, dry, embed, workers):
    fam = families(worlds, [0])
    L = []
    J = {}
    wmap = {w.world_id: w for w in worlds}

    # lineage audit, key sharing, templates
    audit_problems = {}
    for bid, res in results.items():
        p = audit_block(res, wmap[bid.split("|")[1]]) + check_templates(res)
        if p:
            audit_problems[bid] = p
    J["audit_problems"] = audit_problems
    n_cond = sum(len(r) for r in results.values())
    L += ["## Lineage audit and key sharing", "",
          f"{len(results)} blocks and {n_cond} realized conditions were audited against the hand-written fixtures: "
          "node functions and parents, full-record observers, every prompt containing exactly its parents' texts and no "
          "other node's text, one stored text per shared key, and one observer and one synthesis template per block.",
          f"Problems: {sum(len(v) for v in audit_problems.values())} "
          + ("" if not audit_problems else "| " + " | ".join(f"{b}: {p}" for b, ps in audit_problems.items() for p in ps[:3])),
          "Requests are stateless by construction: each adapter sends one user message and no history "
          "(`residue/adapters.py`).", ""]

    # co-location rotation
    colo = Counter()
    for w in worlds:
        res = results.get(f"S1|{w.world_id}|0|incident|{PRIMARY}")
        if not res:
            continue
        pairs = w.conflict_pairs()
        for cond in ("F2", "F3"):
            pk = [set(res[cond][n].package) for n in res[cond] if res[cond][n].fn == "observe"]
            for i, pr in enumerate(pairs):
                if sum(set(pr) <= s for s in pk) == 1:
                    colo[(cond, i)] += 1
    J["colocation"] = {f"{c}|pair{i}": v for (c, i), v in colo.items()}
    L += ["## Packages and co-location", "",
          "Allocators assert their own rules before any call. Co-located conflict pair in F2 and F3, counted over the "
          "primary producer's blocks: " + ", ".join(f"{c} pair {i + 1}: {v}" for (c, i), v in sorted(colo.items())) + ".", ""]

    # validation failures
    recs, by = manifest_stats(store.path)
    failed_trials = {b: f for b, f in failures.items()}
    L += ["## Validation and retries", "",
          f"Producer attempts in the manifest: {len(recs)}, of which {sum(1 for r in recs if not r['valid'])} failed validation. "
          f"Trials marked failed after every attempt: {sum(len(f) for f in failed_trials.values())}. Block errors: {len(errors)}.", "",
          "| Model | Function | Attempts | Invalid | Reasons |", "|---|---|---|---|---|"]
    byfn = defaultdict(lambda: [0, 0, Counter()])
    for (m, fn, c), v in by.items():
        byfn[(m, fn)][0] += v["attempts"]
        byfn[(m, fn)][1] += v["invalid"]
        byfn[(m, fn)][2].update(v["reasons"])
    for (m, fn), (a, inv, rs) in sorted(byfn.items()):
        L.append(f"| {m} | {fn} | {a} | {inv} | {', '.join(f'{k} ({n})' for k, n in rs.most_common(3))} |")
    worst = sorted(((v["invalid"] / v["attempts"], k) for k, v in by.items() if v["attempts"] >= 5), reverse=True)[:5]
    L += ["", "Highest invalid rates by condition: " + ", ".join(f"{k[0].split(':')[-1]} {k[2]} {k[1]} {r:.0%}" for r, k in worst) + ".", ""]
    if failed_trials:
        L += ["Failed trials: " + "; ".join(f"{b} {c}" for b, f in failed_trials.items() for c in f), ""]
    if errors:
        L += ["Block errors: " + "; ".join(errors.values()), ""]
    # copying on rewrite: an output identical to its input, or nearly so
    copy = defaultdict(lambda: [0, 0, 0])
    for r in recs:
        if not r["valid"] or r.get("fn") != "rewrite":
            continue
        inp = r["prompt"].split("\n-----\n")[1].strip()
        out = r["output"].strip()
        a, b = set(inp.split()), out.split()
        exact = out == inp
        near = not exact and bool(b) and sum(x in a for x in b) / len(b) > 0.97 and abs(len(b) - len(inp.split())) < 5
        c = copy[r["model"].split(":")[-1]]
        c[0] += 1
        c[1] += exact
        c[2] += near
    L += ["## Copying on rewrite", "",
          "Rewrites whose output is identical to the input, and near copies (over 97% of output words in the input and "
          "a length within five words). Validation does not reject either.", "",
          "| Producer | Rewrites | Identical | Near copy |", "|---|---|---|---|"]
    for m, (n, e, nr) in sorted(copy.items()):
        L.append(f"| {m} | {n} | {e} ({e / n:.0%}) | {nr} ({nr / n:.0%}) |")
    L.append("")
    J["copying"] = {m: {"rewrites": n, "identical": e, "near": nr} for m, (n, e, nr) in copy.items()}
    J["failed_trials"] = failed_trials
    J["errors"] = errors

    # attribution field
    att = defaultdict(lambda: [0, 0, 0, 0])  # outputs, present, names listed, names valid
    for bid, res in results.items():
        w = wmap[bid.split("|")[1]]
        srcs = [p.source for p in w.propositions]
        prod = bid.split("|")[4]
        for cond, nodes in res.items():
            arm = "conceal" if cond.endswith("conceal") else "neutral"
            for n, r in nodes.items():
                ps = parse_sources(r.text)
                a = att[(prod.split("-")[0], r.fn, arm)]
                a[0] += 1
                if ps is not None:
                    a[1] += 1
                    ok, tot = source_validity(ps, srcs)
                    a[2] += tot
                    a[3] += ok
    L += ["## Attribution field", "",
          "Presence of the final Sources line, and the share of listed names that match an in-world source, by producer, "
          "function, and arm (calls counted once per condition that uses them).", "",
          "| Producer | Function | Arm | Outputs | Line present | Names valid |", "|---|---|---|---|---|---|"]
    for (p, fn, arm), (n, pres, tot, ok) in sorted(att.items()):
        L.append(f"| {p} | {fn} | {arm} | {n} | {pres / n:.0%} | {(ok / tot if tot else float('nan')):.0%} |")
    L.append("")

    # stripping
    strip_rows = []
    for bid, res in results.items():
        if not bid.startswith("S2") or not bid.endswith(PRIMARY):
            continue
        for cond, nodes in res.items():
            if not cond.endswith("neutral"):
                continue
            for t in FIXTURES[cond]["terminals"]:
                text = nodes[t].text
                s, line = strip_sources(text)
                exact = line is None or (text.rstrip().startswith(s) and text.rstrip()[len(s):].strip() == line.strip())
                strip_rows.append((bid, cond, t, line is not None, exact, text, s))
    n_line = sum(r[3] for r in strip_rows)
    n_exact = sum(r[4] for r in strip_rows)
    w_match = []
    for bid, cond, t, has, exact, text, s in strip_rows[:12] if not dry else []:
        w = wmap[bid.split("|")[1]]
        a, b = match(text, w, embed), match(s, w, embed)
        w_match.append(a.states == b.states and a.conflicts == b.conflicts)
    L += ["## Stripping", "",
          f"Stripped messages derived from the primary producer's neutral Study 2 messages: {len(strip_rows)}. "
          f"Sources line present: {n_line}. Deletion exact (only the line removed): {n_exact} of {len(strip_rows)}. "
          f"Matcher output unchanged by stripping: {sum(w_match)} of {len(w_match)} checked pairs.", ""]
    J["stripping"] = {"messages": len(strip_rows), "line_present": n_line, "exact": n_exact,
                      "matcher_unchanged": [sum(w_match), len(w_match)]}

    # observer diversity
    div = []
    if not dry:
        for w in worlds:
            res = results.get(f"S1|{w.world_id}|0|incident|{PRIMARY}")
            if not res or "SI-same" not in res:
                continue
            obs = [res["SI-same"][n].text for n in ("o1", "o2", "o3")]
            vecs = embed.many([body(t) for t in obs])
            cos = [sum(x * y for x, y in zip(vecs[a], vecs[b])) /
                   ((sum(x * x for x in vecs[a]) ** .5) * (sum(x * x for x in vecs[b]) ** .5))
                   for a, b in combinations(range(3), 2)]
            jac = [jaccard(ngrams(body(obs[a]), 4), ngrams(body(obs[b]), 4)) for a, b in combinations(range(3), 2)]
            res_c = [match(t, w, embed).conflicts for t in obs]
            disagree = sum(len({rc[i] for rc in res_c}) > 1 for i in (0, 1))
            div.append({"world": w.world_id, "cosine": cos, "jaccard4": jac, "conflict_resolutions": res_c,
                        "pairs_resolved_differently": disagree})
    J["observer_diversity"] = div
    if div:
        mc = sum(sum(d["cosine"]) / 3 for d in div) / len(div)
        mj = sum(sum(d["jaccard4"]) / 3 for d in div) / len(div)
        dis = sum(d["pairs_resolved_differently"] for d in div)
        L += ["## Observer diversity (principle 13)", "",
              f"Independent observers given the same full record (SI-same, primary producer): mean pairwise embedding "
              f"cosine {mc:.3f}, mean pairwise word 4-gram Jaccard {mj:.3f}. Conflict pairs that the three observers "
              f"resolved differently, by the matcher: {dis} of {2 * len(div)}.", ""]

    # matcher spot check
    spot = []
    if not dry:
        rng = random.Random(f"spot|{RUN_SEED}")
        cands = [(bid, c) for bid, res in results.items() if bid.startswith("S1") for c in res]
        for bid, c in rng.sample(sorted(cands), min(12, len(cands))):
            w = wmap[bid.split("|")[1]]
            t = terminal(results[bid], c).text
            m = match(t, w, embed)
            spot.append({"block": bid, "condition": c, "text": t, "states": m.states, "conflicts": m.conflicts,
                         "unsupported": m.unsupported, "sentence_map": m.sentence_map})
        with open(os.path.join(phase_dir, "matcher_spot_check.json"), "w") as fh:
            json.dump(spot, fh, indent=1, ensure_ascii=False)
        L += ["## Matcher spot check", "",
              f"{len(spot)} messages with the matcher's states are in `matcher_spot_check.json` for inspection "
              "(an engineering check for implementation bugs, not validation). State counts: "
              + ", ".join(f"{k} {v}" for k, v in Counter(s for x in spot for s in x["states"].values()).most_common())
              + f". Unsupported sentences: {sum(x['unsupported'] for x in spot)}.", ""]

    # preflight
    ledger_obj = ledger
    judge = MockJudge() if dry else adapters.make(JUDGE, ledger_obj, role="reader", max_output_tokens=1500)
    model = producers(dry, ledger_obj)[(PRIMARY, "incident")]
    pf = preflight(results, worlds, fam, store, model, judge, phase_dir)
    J["preflight"] = [{k: v for k, v in r.items() if k != "text"} for r in pf]
    L += ["## Single-input synthesis preflight (principle 1)", "",
          "| Inputs | Outputs | Refers to inputs | Compares inputs |", "|---|---|---|---|"]
    single_bad = None
    for k in (1, 2, 3):
        rows = [r for r in pf if r.get("k") == k and "failed" not in r]
        ref = sum(1 for r in rows if r.get("refers_to_inputs"))
        cmp_ = sum(1 for r in rows if r.get("compares_inputs"))
        bad = sum(1 for r in rows if r.get("refers_to_inputs") or r.get("compares_inputs"))
        if k == 1:
            single_bad = (bad, len(rows))
        L.append(f"| {k} | {len(rows)} | {ref} | {cmp_} |")
    if single_bad and single_bad[1]:
        verdict = "F1 is dropped" if single_bad[0] / single_bad[1] > 0.05 else "F1 is kept"
        L += ["", f"Single-input outputs flagged: {single_bad[0]} of {single_bad[1]}. Rule: more than 5% drops F1. {verdict}. "
              f"The judge is {JUDGE}; it sees the inputs and the report body without its Sources line, and flagged outputs are in `preflight_judgments_v2.jsonl`. Version 1 of the judge, which judged the whole output and flagged the required Sources line, is kept in `preflight_judgments.jsonl`.", ""]

    # readers
    rlog = rd.ReaderLog(os.path.join(phase_dir, "reader_calls.jsonl"))
    readers = ({n: MockReader() for n in READERS} if dry else
               {"claude-sonnet-5-5": adapters.make("claude-sonnet-5-5", ledger_obj, role="reader", max_output_tokens=2000),
                "gpt-6.1-terra": adapters.make("gpt-6.1-terra", ledger_obj, role="reader", max_output_tokens=300)})
    rr = run_readers(reader_items(results, worlds), readers, rlog, workers)
    L += ["## Readers", "",
          "Each verification world's messages were read with examples drawn from the other nine worlds (16 for binary "
          "tasks, 18 for three-class tasks). This checks formats, parsing, and tokens. Ten worlds give no accuracy estimate.", "",
          "| Reader | Task | Items | Valid first time | Uniform after retry | Mean input tokens | Accuracy (descriptive) |",
          "|---|---|---|---|---|---|---|"]
    grp = defaultdict(list)
    for r in rr:
        grp[(r["reader"], r["task"])].append(r)
    for (name, task), rows in sorted(grp.items()):
        conds = [c for c, _ in rd.TASKS[task]]
        acc = sum(1 for r in rows if conds[max(range(len(conds)), key=lambda i: r["probs"][i])] == r["truth"]) / len(rows)
        first = sum(1 for r in rows if r["valid"] and r["attempt"] == 0)
        uni = sum(1 for r in rows if not r["valid"])
        tin = sum(r["usage"].get("input_tokens", 0) for r in rows) / len(rows)
        L.append(f"| {name} | {task} | {len(rows)} | {first} | {uni} | {tin:.0f} | {acc:.2f} |")
    L.append("")

    # cost projection
    measured = defaultdict(lambda: [0.0, set()])
    for r in recs:
        if r.get("condition_first_seen") == "PREFLIGHT":
            continue
        m = r["model"].split(":", 1)[-1]
        g = "news" if r.get("params", {}).get("max_output_tokens") == max_tokens("news", m) else "incident"
        measured[(m, g, r["fn"])][0] += call_cost(r["model"], r.get("usage", {}))
        measured[(m, g, r["fn"])][1].add(r["key"])
    per_call = {k: c / len(keys) for k, (c, keys) in measured.items() if keys}
    full_counts = count_plan("full")
    proj = Counter()
    for (p, g, fn), n in full_counts.items():
        c = per_call.get((p, g, fn))
        if c is None:
            c = per_call.get((p, "incident", fn), 0.0)
        proj[adapters.provider_of(p)] += n * c
    reader_cost, reader_cached = {}, {}
    proj_cached = Counter({k: v for k, v in proj.items()})  # producers at standard prices
    for name in READERS:
        rows = [r for r in rr if r["reader"] == name]
        if rows:
            pi, po = adapters.PRICES[name]
            tin = sum(r["usage"].get("input_tokens", 0) for r in rows) / len(rows)
            tout = sum(r["usage"].get("output_tokens", 0) for r in rows) / len(rows)
            share = sum(len(r["prompt"].split("Now classify this message")[0]) / len(r["prompt"]) for r in rows) / len(rows)
            single = tin / 1e6 * pi + tout / 1e6 * po
            # full run: every first-replicate Study 1 message (1,020 primary genre, 240 second genre) and 1,080
            # Study 2 sets; a set prompt carries three messages per example and item, so about 2.8 times the input
            reader_cost[name] = 1260 * single + 1080 * (tin * 2.8 / 1e6 * pi + tout / 1e6 * po)
            proj[adapters.provider_of(name)] += reader_cost[name]
            f = CACHE_READ_PRICE[adapters.provider_of(name)]
            eff = (share * f + (1 - share)) / 1e6 * pi
            reader_cached[name] = 0.5 * (1260 * (tin * eff + tout / 1e6 * po) + 1080 * (tin * 2.8 * eff + tout / 1e6 * po))
            proj_cached[adapters.provider_of(name)] += reader_cached[name]
    spent = ledger.spent if ledger else {}
    L += ["## Full-run cost projection", "",
          "Producer calls are exact counts from realizing the full plan with the mock model (shared keys counted once), "
          "times the measured mean cost per logical call, including retries, by model, genre, and function. Reader calls "
          "follow design Part VII (both readers, first replicate). Set-reader prompts are not run in verification and are "
          "estimated at 2.8 times the single-message input. Standard (non-batch) prices; batch processing halves them.", "",
          "The last projection runs producers synchronously at standard prices, and readers through the batch API "
          "(half price) with the fixed examples cached, at assumed cache-read prices of "
          + ", ".join(f"{k} {v:g} of the input price" for k, v in CACHE_READ_PRICE.items()) + " (to be confirmed).", "",
          "| Provider | All standard | All batch | Producers standard, readers batched and cached | Spent so far | Cap | Remaining |",
          "|---|---|---|---|---|---|---|"]
    for prov in ("google", "anthropic", "openai"):
        s = spent.get(prov, 0.0)
        L.append(f"| {prov} | ${proj[prov]:.2f} | ${proj[prov] / 2:.2f} | ${proj_cached[prov]:.2f} | ${s:.2f} | "
                 f"${adapters.CAPS[prov]:.2f} | ${adapters.CAPS[prov] - s:.2f} |")
    L += ["", "Producer calls in the full run: " + ", ".join(
        f"{p.split('-')[0]} {g} {fn} {n}" for (p, g, fn), n in sorted(full_counts.items())) + ".", ""]
    J["projection"] = {"by_provider_standard": dict(proj), "reader": reader_cost, "reader_batched_cached": reader_cached,
                       "by_provider_producers_standard_readers_cached": dict(proj_cached),
                       "per_call": {"|".join(k): v for k, v in per_call.items()},
                       "full_counts": {"|".join(k): v for k, v in full_counts.items()}}
    return L, J


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["verification", "full"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args()
    phase_dir = os.path.join(HERE, "runs", a.phase + ("-dry" if a.dry_run else ""))
    os.makedirs(phase_dir, exist_ok=True)
    code_hash = snapshot(phase_dir)
    ledger = None if a.dry_run else adapters.Ledger(os.path.join(HERE, "smoke", "ledger.json"))
    embed = None
    if not a.dry_run or a.phase == "verification":
        os.makedirs(os.path.dirname(EMBED_CACHE), exist_ok=True)
        try:
            from residue.embed import Embedder
            embed = Embedder(EMBED_CACHE)
        except Exception as e:
            if not a.dry_run:
                raise
            print("embedding server unavailable in dry run:", e)
    worlds, reps = load_worlds(a.phase), replicates(a.phase)
    config = {"phase": a.phase, "dry_run": a.dry_run, "code_hash": code_hash, "run_seed": RUN_SEED,
              "producers": list(PRODUCERS), "readers": list(READERS), "judge": JUDGE,
              "max_output_tokens": {f"{p}|{g}": max_tokens(g, p) for p in PRODUCERS for g in ("incident", "news")},
              "worlds": [w.world_id for w in worlds], "replicates": reps,
              "embedding": {"model": "nomic-embed-text", "digest": getattr(embed, "digest", None)},
              "started": time.time()}
    with open(os.path.join(phase_dir, "config.jsonl"), "a") as fh:
        fh.write(json.dumps(config) + "\n")
    store = CallStore(os.path.join(phase_dir, "calls.jsonl"), extra={"code_hash": code_hash})
    blocks = plan(worlds, reps)
    print(f"{a.phase}: {len(worlds)} worlds, {len(blocks)} blocks, code {code_hash[:12]}", flush=True)
    results, failures, errors = run_blocks(blocks, store, producers(a.dry_run, ledger), a.workers)
    print(f"generation done: {store.calls_made} calls made, {len(failures)} blocks with failed trials, "
          f"{len(errors)} block errors", flush=True)
    if a.phase == "verification":
        L, J = verification_report(phase_dir, worlds, results, failures, errors, store, ledger, a.dry_run, embed, a.workers)
        head = [f"# Verification Run Report{' (dry run, mock models)' if a.dry_run else ''}", "",
                f"Generated by `run.py` at {time.strftime('%Y-%m-%d %H:%M')}, code hash {code_hash[:12]} "
                f"(snapshot in `code/{code_hash[:12]}/`). Worlds: {', '.join(w.world_id for w in worlds)}. One replicate. "
                f"Producers: {', '.join(PRODUCERS)}. Readers: {', '.join(READERS)}.", ""]
        with open(os.path.join(phase_dir, "report.md"), "w") as fh:
            fh.write("\n".join(head + L) + "\n")
        with open(os.path.join(phase_dir, "report.json"), "w") as fh:
            json.dump(J, fh, indent=1, default=str)
        print("wrote", os.path.join(phase_dir, "report.md"))
    if ledger:
        print("spend:", ledger.spent)


if __name__ == "__main__":
    main()

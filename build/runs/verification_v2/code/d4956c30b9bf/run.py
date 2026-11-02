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
import math
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
from residue.prompts import PER_FAMILY, render_observe, render_with_inputs, target_words, template_id  # noqa: E402
from residue.store import CallStore, StoreError  # noqa: E402
from residue.worldgen import load_bank  # noqa: E402

RUN_SEED = 20261030
PRIMARY = "gemini-3.5-flash-lite"
PRODUCERS = (PRIMARY, "claude-haiku-5-5", "gpt-6-luna")
READERS = ("claude-sonnet-5-5", "gpt-6.1-terra")
JUDGE = "claude-sonnet-5-5"
# Output tokens per word, the 99th percentile of output tokens over words on the first verification pass
# (2026-10-30; medians Gemini 1.32, Luna 1.36, Haiku 2.08). Version 1 of this table used 4/3 for every
# producer and truncated 425 of 510 Haiku outputs.
TOKENS_PER_WORD = {"gemini-3.5-flash-lite": 1.45, "claude-haiku-5-5": 2.3, "gpt-6-luna": 1.45}
SOURCES_MARGIN = 64  # tokens for the Sources line and a natural ending
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
    """A generation safety limit, not a length target: 2.2 times the genre's target, in the producer's
    tokens, plus room for the Sources line. Above the 2.0 validation ceiling, so the cap never decides
    validity (GPT Review of Verification Run, section 4; build spec section 1 said 1.8)."""
    return math.ceil(2.2 * target_words(genre) * TOKENS_PER_WORD[producer]) + SOURCES_MARGIN


class MockReader:
    version = "mock-reader"
    last_usage = {"input_tokens": 0, "output_tokens": 0}

    def __call__(self, prompt, seed):
        n = 5 if "\nE: " in prompt else 3 if "\nC: " in prompt else 2
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


def plan_coverage(blocks, results, failures):
    """Planned versus realized conditions, by producer: every planned
    condition either realized or recorded as failed."""
    out = defaultdict(Counter)
    for bid, spec, builders in blocks:
        got, bad = set(results.get(bid, {})), set(failures.get(bid, {}))
        for c in builders:
            out[spec.producer]["planned"] += 1
            out[spec.producer]["realized" if c in got else "failed" if c in bad else "missing"] += 1
    return out


def request_check(results, worlds, store, models):
    """Rebuilds every stored request from the hand-written fixture's parents,
    the stored parent outputs, and the versioned renderer, and compares its
    prompt hash and request hash with the record actually sent. An extra
    instruction or a stray text in a sent prompt changes the hash."""
    wmap = {w.world_id: w for w in worlds}
    from residue.keys import request_hash
    bad, n, seen = [], 0, set()
    for bid, res in results.items():
        _, wid, _, genre, prod = bid.split("|")
        w, m = wmap[wid], models[(prod, genre)]
        for cond, nodes in res.items():
            for name, r in nodes.items():
                if r.key in seen:
                    continue
                seen.add(r.key)
                fn, parents = FIXTURES[cond]["nodes"][name]
                if fn == "observe":
                    exp = render_observe(r.template_id, w, r.package, genre)
                else:
                    exp = render_with_inputs(r.template_id, [store.records[nodes[q].key]["output"] for q in parents], genre)
                rec = store.records[r.key]
                n += 1
                if sha256(exp) != rec["prompt_hash"] or request_hash(m.version, exp, req_params(m)) != rec["request_hash"]:
                    bad.append(f"{bid} {cond}.{name}")
    return n, bad


def package_check(results, worlds):
    """Package rules checked on the realized records, for every producer,
    from the design's statement of each rule rather than the allocators."""
    wmap = {w.world_id: w for w in worlds}
    bad, n = [], 0
    for bid, res in results.items():
        w = wmap[bid.split("|")[1]]
        core, ids = w.core.pid, set(w.ids())
        pairs = w.conflict_pairs()
        pk = {c: {nm: set(r.package) for nm, r in nodes.items() if r.fn == "observe"} for c, nodes in res.items()}

        def fail(msg):
            bad.append(f"{bid} {msg}")
        for c, obs in pk.items():
            n += 1
            if any(core not in p for p in obs.values()):
                fail(f"{c}: core missing")
            if any(not p <= ids for p in obs.values()):
                fail(f"{c}: proposition outside the world")
        for c in ("F2", "F3"):
            if c not in pk:
                continue
            nc = [p - {core} for p in pk[c].values()]
            if set().union(*nc) != ids - {core} or sum(map(len, nc)) != len(ids) - 1:
                fail(f"{c}: not a partition of the record")
            if max(map(len, nc)) - min(map(len, nc)) > 1:
                fail(f"{c}: sizes differ by more than one")
            co = [sum(set(pr) <= q for q in nc) for pr in pairs]
            if sorted(co) != [0, 1]:
                fail(f"{c}: co-location {co}")
        if "F1" in pk and pk["F1"]["f1"] != ids:
            fail("F1: observer lacks the full record")
        if "SI-div" in pk:
            d = list(pk["SI-div"].values())
            if set().union(*d) != ids or any(len((a & b) - {core}) != 2 for a, b in combinations(d, 2)):
                fail("SI-div: union or overlap wrong")
        for c, obs in pk.items():
            if "-full-" in c and any(p != ids for p in obs.values()):
                fail(f"{c}: full-access observer lacks the full record")
        for instr in ("neutral", "conceal"):
            ind, dep, mix = (pk.get(f"{s}-partial-{instr}") for s in ("IND", "DEP", "MIX"))
            if not ind:
                continue
            size = 1 + (len(ids) - 1) // 2
            if any(len(p) != size for p in ind.values()):
                fail(f"IND-partial-{instr}: package size")
            if len({frozenset(p) for p in ind.values()}) != 3:
                fail(f"IND-partial-{instr}: packages not distinct")
            if dep and dep["o1"] != ind["o1"]:
                fail(f"DEP-partial-{instr}: slot 1 package differs from IND's")
            if mix and (mix["o1"] != ind["o1"] or mix["o3"] != ind["o3"]):
                fail(f"MIX-partial-{instr}: slot packages differ from IND's")
    return n, bad


def strip_expected(text):
    """Independent statement of the stripping rule: drop trailing blank
    lines, then the last line if it starts with "Sources:", then trailing
    whitespace. Returns None if there is no Sources line."""
    lines = text.split("\n")
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines or not lines[-1].lstrip().lower().startswith("sources:"):
        return None
    return "\n".join(lines[:-1]).rstrip()


def chain_edits(results):
    """For each realized R5 chain, the number of its five rewrites whose output differs from its input."""
    out = defaultdict(Counter)
    for bid, res in results.items():
        if "R5" not in res:
            continue
        nodes = res["R5"]
        chain = ["o1", "r1", "r2", "r3", "r4", "r5"]
        if not all(c in nodes for c in chain):
            continue
        changed = sum(nodes[a].text.strip() != nodes[b].text.strip() for a, b in zip(chain, chain[1:]))
        out[bid.split("|")[4]][changed] += 1
    return out


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


def f1_preflight(results, worlds, fam, store, model, judge, out_dir):
    """Principle 1 on F1's own input type (GPT Review of Verification Run,
    section 3): one synthesis of one full-record observation. Per world, F1's
    realized synthesis plus four more on the block's full-record observations
    (F1's observer and SI-same's three), with synthesis templates of the same
    family other than the block's, judged by judge version 2."""
    rows = []
    jp = os.path.join(out_dir, "preflight_f1_judgments.jsonl")
    done = {json.loads(l)["key"]: json.loads(l) for l in open(jp, encoding="utf-8")} if os.path.exists(jp) else {}
    jl = open(jp, "a", encoding="utf-8")
    tw = target_words("incident")
    for w in worlds:
        res = results.get(f"S1|{w.world_id}|0|incident|{PRIMARY}")
        if not res or "F1" not in res or "SI-same" not in res:
            continue
        f = fam[(w.world_id, 0)]
        own = res["F1"]["syn"]
        cases = [(own.key, res["F1"]["f1"], own.text)]
        others = [i for i in range(PER_FAMILY) if template_id(f, "synthesize", i) != own.template_id]
        for j, obs in enumerate([res["F1"]["f1"], res["SI-same"]["o1"], res["SI-same"]["o2"], res["SI-same"]["o3"]]):
            tid = template_id(f, "synthesize", others[j % len(others)])
            key = make_key(study="PREFLIGHT-F1", world=w.world_id, replicate=0, genre="incident", producer=PRIMARY,
                           family=f, role=f"pre:f1:j{j}", template_id=tid, package_id=None, parent_keys=[obs.key])
            try:
                text = store.get_or_call(key, render_with_inputs(tid, [obs.text], "incident"), model.version,
                                         req_params(model), model, tw,
                                         {"condition_first_seen": "PREFLIGHT-F1", "node": f"j{j}", "fn": "synthesize"})
            except StoreError as e:
                rows.append({"world": w.world_id, "key": key, "failed": str(e)})
                continue
            cases.append((key, obs, text))
        for key, obs, text in cases:
            if key in done:
                rows.append(done[key])
                continue
            shown = f"Input 1:\n-----\n{obs.text.strip()}\n-----"
            reply = judge(JUDGE_PROMPT.format(inputs=shown, text=strip_sources(text)[0]), 1)
            try:
                v = json.loads(reply[reply.index("{"):reply.rindex("}") + 1])
            except ValueError:
                v = {"refers_to_inputs": None, "compares_inputs": None, "quote": reply[:200]}
            rec = {"key": key, "world": w.world_id, "k": 1, "realized_F1": key == own.key, "text": text, **v,
                   "usage": dict(getattr(judge, "last_usage", {}) or {})}
            jl.write(json.dumps(rec, ensure_ascii=False) + "\n")
            jl.flush()
            rows.append(rec)
    jl.close()
    return rows


# ---------- readers ----------

def reader_groups(results, worlds, splits, s2_strata=None, s1_tasks=None):
    """Reader jobs grouped so that every job in a group has the same prompt
    before rd.CACHE_SPLIT: one task (or Study 2 access and arm), genre, and
    split. splits are (split id, test world ids, training world ids). Examples
    come only from training worlds, and from the first replicate of the
    primary producer, the messages the readers read."""
    groups = {}
    s1 = {}
    for w in worlds:
        for genre in rd.GENRE_TASKS:
            res = results.get(f"S1|{w.world_id}|0|{genre}|{PRIMARY}")
            if res:
                s1[(w.world_id, genre)] = {c: terminal(res, c).text for c in res}
    sets = {}  # (world, access, arm) -> {structure: (presented texts, configuration)}
    for w in worlds:
        res = results.get(f"S2|{w.world_id}|0|incident|{PRIMARY}")
        if not res:
            continue
        for access in ("full", "partial"):
            for arm in ("neutral", "conceal", "stripped"):
                d = {}
                for st in ("IND", "DEP", "MIX"):
                    cond = f"{st}-{access}-{'conceal' if arm == 'conceal' else 'neutral'}"
                    if cond not in res:
                        continue
                    texts = [res[cond][t].text for t in FIXTURES[cond]["terminals"]]
                    if arm == "stripped":
                        texts = [strip_sources(t)[0] for t in texts]
                    d[st] = rd.present(texts, st, f"{RUN_SEED}|{w.world_id}|0|{st}|{access}")
                sets[(w.world_id, access, arm)] = d
    for sid, test, train in splits:
        assert not set(test) & set(train), "a test world is among the training worlds"
        for genre, tasks in rd.GENRE_TASKS.items():
            for task in tasks:
                if s1_tasks is not None and task not in s1_tasks:
                    continue
                conds = [c for c, _ in rd.TASKS[task]]
                pool = {c: [(o, s1[(o, genre)][c]) for o in train if c in s1.get((o, genre), {})] for c in conds}
                if any(len(v) < rd.PER_CLASS[len(conds)] for v in pool.values()):
                    continue
                ex = rd.draw_examples(task, pool, f"{RUN_SEED}|{sid}|{genre}")
                jobs = []
                for wid in test:
                    for c in conds:
                        if c in s1.get((wid, genre), {}):
                            jobs.append((f"{task}|{genre}", f"{wid}|{c}", rd.render(task, ex, s1[(wid, genre)][c]), c))
                if jobs:
                    groups[(f"{task}|{genre}", sid)] = jobs
        for access in ("full", "partial"):
            for arm in ("neutral", "conceal", "stripped"):
                if s2_strata is not None and (access, arm) not in s2_strata:
                    continue
                pool = {st: [(o, *sets[(o, access, arm)][st]) for o in train
                             if st in sets.get((o, access, arm), {})] for st in ("IND", "DEP", "MIX")}
                if any(len(v) < rd.SET_PER_STRUCTURE for v in pool.values()):
                    continue
                ex = rd.draw_set_examples(pool, f"{RUN_SEED}|{sid}|{access}|{arm}")
                task = f"{rd.SET_TASK}|{access}|{arm}"
                jobs = [(task, f"{wid}|{st}-{access}-{arm}", rd.render_set(ex, sets[(wid, access, arm)][st][0]),
                         sets[(wid, access, arm)][st][1])
                        for wid in test for st in ("IND", "DEP", "MIX") if st in sets.get((wid, access, arm), {})]
                if jobs:
                    groups[(task, sid)] = jobs
    return groups


def run_reader_groups(groups, readers, log, outer=6, inner=4):
    """Each group's first call runs alone and writes the provider's cache;
    the rest of the group follows at once and reads it. Groups run in
    parallel, each within the five-minute cache lifetime."""
    def one_group(reader, name, jobs):
        task0 = jobs[0][0].split("|")[0]
        out = [log.read(reader, name, task0, f"{jobs[0][0]}|{jobs[0][1]}", jobs[0][2], jobs[0][3])]
        with ThreadPoolExecutor(max_workers=inner) as ex:
            out += list(ex.map(lambda j: log.read(reader, name, j[0].split("|")[0], f"{j[0]}|{j[1]}", j[2], j[3]),
                               jobs[1:]))
        return out
    rows = []
    with ThreadPoolExecutor(max_workers=outer) as ex:
        futs = [ex.submit(one_group, reader, name, jobs) for (_, _), jobs in sorted(groups.items())
                for name, reader in readers.items()]
        for i, fut in enumerate(as_completed(futs)):
            rows += fut.result()
            if (i + 1) % 10 == 0 or i + 1 == len(futs):
                print(f"  reader groups {i + 1}/{len(futs)}", flush=True)
    return rows


def make_readers(dry, ledger):
    if dry:
        return {n: MockReader() for n in READERS}
    out = {"claude-sonnet-5-5": adapters.make("claude-sonnet-5-5", ledger, role="reader", max_output_tokens=2000),
           "gpt-6.1-terra": adapters.make("gpt-6.1-terra", ledger, role="reader", max_output_tokens=300)}
    for m in out.values():
        m.cache_split = rd.CACHE_SPLIT
    return out


def reader_usage(rows):
    """Measured tokens by reader and kind (single message or set): prefix
    tokens, uncached item tokens, and output, from calls that read or wrote
    the cache."""
    agg = defaultdict(lambda: defaultdict(list))
    for r in rows:
        u = r.get("usage") or {}
        kind = "set" if r["task"] == rd.SET_TASK else "single"
        a = agg[(r["reader"], kind)]
        a["prefix"].append(u.get("cache_read", 0) + u.get("cache_write", 0))
        a["read"].append(u.get("cache_read", 0))
        a["write"].append(u.get("cache_write", 0))
        a["uncached"].append(u.get("input_tokens", 0))
        a["out"].append(u.get("output_tokens", 0))
    return {k: {f: sum(v) / len(v) for f, v in d.items()} | {"n": len(d["out"]),
                "hit": sum(1 for x in d["read"] if x > 0) / len(d["read"])} for k, d in agg.items()}


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

def verification_report(phase_dir, worlds, results, failures, errors, store, ledger, dry, embed, workers, blocks, models):
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
          "The prompt test is substring membership, so the request check below is the stronger one. "
          "Requests are stateless by construction: each adapter sends one user message and no history "
          "(`residue/adapters.py`).", ""]
    cov = plan_coverage(blocks, results, failures)
    nreq, badreq = request_check(results, worlds, store, models)
    npk, badpk = package_check(results, worlds)
    J["coverage"] = {k: dict(v) for k, v in cov.items()}
    J["request_check"] = {"requests": nreq, "mismatched": badreq}
    J["package_check"] = {"conditions": npk, "problems": badpk}
    L += ["## Planned versus realized conditions", "",
          "| Producer | Planned | Realized | Failed | Missing |", "|---|---|---|---|---|"]
    for prod, c in sorted(cov.items()):
        L.append(f"| {prod} | {c['planned']} | {c['realized']} | {c['failed']} | {c['missing']} |")
    L += ["", "## Request reconstruction", "",
          f"Every distinct stored request ({nreq}) was rebuilt from the hand-written fixture's parents, the stored "
          "parent outputs, and the versioned renderer, and its prompt hash and request hash compared with the record "
          f"sent. Mismatches: {len(badreq)}" + (": " + "; ".join(badreq[:10]) if badreq else "") + ".", "",
          "## Package rules on realized records", "",
          f"{npk} realized conditions, all producers, checked against the design's package rules (core in every "
          "package; F2 and F3 a partition of the record with sizes within one and exactly one conflict pair "
          "co-located; F1 and every full-access observer the whole record; SI-div's union the record with pairwise "
          "overlap of two; Study 2 partial packages of equal size, distinct across IND's slots, and shared by slot "
          f"with DEP and MIX). Problems: {len(badpk)}" + (": " + "; ".join(badpk[:10]) if badpk else "") + ".", ""]

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
    ce = chain_edits(results)
    J["chain_edits"] = {m: dict(c) for m, c in ce.items()}
    L += ["Rewrites that changed the text, of the five in each realized R5 chain (the structural label stays R5 "
          "whatever the count):", "", "| Producer | " + " | ".join(str(i) for i in range(6)) + " |",
          "|---|" + "---|" * 6]
    for m, c in sorted(ce.items()):
        L.append(f"| {m.split('-')[0]} | " + " | ".join(str(c.get(i, 0)) for i in range(6)) + " |")
    stops = defaultdict(Counter)
    for r in recs:
        stops[r["model"].split(":")[-1]][str((r.get("usage") or {}).get("stop_reason"))] += 1
    J["stop_reasons"] = {m: dict(c) for m, c in stops.items()}
    L += ["", "Stop reasons of every producer attempt (a cap stop is max_tokens, length, or MAX_TOKENS):", ""]
    L += [f"- {m}: " + ", ".join(f"{k} {v}" for k, v in c.most_common()) for m, c in sorted(stops.items())]
    L.append("")
    J["failed_trials"] = failed_trials
    J["errors"] = errors

    # attribution field
    att = defaultdict(lambda: [0, 0, 0, 0, 0])  # outputs, present, names listed, names matching, names exact
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
                    a[4] += sum(1 for x in ps if x.strip().lower() in {q.lower() for q in srcs})
    L += ["## Attribution field", "",
          "Presence of the final Sources line, the share of listed names that contain or are contained in an in-world "
          "source name, and the share exactly equal to one (case-insensitive), by producer, function, and arm (calls "
          "counted once per condition that uses them). These are rates among outputs that passed validation. Whether "
          "a named source supports the propositions the message keeps is not checked here.", "",
          "| Producer | Function | Arm | Outputs | Line present | Names matching | Names exact |",
          "|---|---|---|---|---|---|---|"]
    for (p, fn, arm), (n, pres, tot, ok, ex) in sorted(att.items()):
        L.append(f"| {p} | {fn} | {arm} | {n} | {pres / n:.0%} | {(ok / tot if tot else float('nan')):.0%} | "
                 f"{(ex / tot if tot else float('nan')):.0%} |")
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
                exp = strip_expected(text)
                exact = (line is None and exp is None) or (exp is not None and s == exp)
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
          f"Sources line present: {n_line}. Stripped text byte-identical to an independently written statement of the "
          f"rule (`strip_expected`): {n_exact} of {len(strip_rows)}. The matcher reads the body without the Sources "
          f"line, so its invariance holds by construction: {sum(w_match)} of {len(w_match)} checked pairs.", ""]
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

    # preflight on F1's input type
    judge = MockJudge() if dry else adapters.make(JUDGE, ledger, role="reader", max_output_tokens=1500)
    model = models[(PRIMARY, "incident")]
    pf = f1_preflight(results, worlds, fam, store, model, judge, phase_dir)
    J["preflight_f1"] = [{k: v for k, v in r.items() if k != "text"} for r in pf]
    ok = [r for r in pf if "failed" not in r]
    badf = [r for r in ok if r.get("refers_to_inputs") or r.get("compares_inputs")]
    L += ["## Single-input synthesis preflight on F1's input (principle 1)", "",
          f"Syntheses of one full-record observation by the primary producer: {len(ok)} "
          f"({sum(1 for r in ok if r.get('realized_F1'))} are F1's realized syntheses), failed calls "
          f"{len(pf) - len(ok)}. Flagged by judge version 2: {len(badf)}. Rule: more than 5% drops F1. "
          f"{'F1 is dropped' if ok and len(badf) / len(ok) > 0.05 else 'F1 is kept'}. Judgments are in "
          "`preflight_f1_judgments.jsonl`" + (": " + "; ".join(str(r.get("quote")) for r in badf[:5]) if badf else "")
          + ".", ""]

    # readers: every Study 1 task on three held-out worlds, and the Study 2 set task on two strata
    rlog = rd.ReaderLog(os.path.join(phase_dir, "reader_calls.jsonl"))
    readers = make_readers(dry, ledger)
    ids = [w.world_id for w in worlds]
    test = ids[:3] if not dry else ids
    splits = [(f"lowo-{wid}", [wid], [o for o in ids if o != wid]) for wid in test]
    groups = reader_groups(results, worlds, splits, s2_strata={("full", "neutral"), ("partial", "stripped")})
    rr = run_reader_groups(groups, readers, rlog)
    L += ["## Readers", "",
          f"Held-out worlds {', '.join(test)}, each read with examples drawn from the other nine (16 for binary tasks, "
          "18 for three-class tasks, 18 example sets for Study 2). Study 1: every task on both genres. Study 2: the "
          "five-configuration set task, full access neutral and partial access stripped. Prompts before "
          "\"Now classify this\" are cached. This checks formats, parsing, caching, and tokens. "
          f"{len(test)} held-out worlds give no accuracy estimate.", "",
          "| Reader | Task | Items | Valid first time | Uniform after retry | Mean uncached input | Mean cached prefix | "
          "Accuracy (descriptive) |", "|---|---|---|---|---|---|---|---|"]
    grp = defaultdict(list)
    for r in rr:
        grp[(r["reader"], r["item"].split("|")[0] + ("|" + r["item"].split("|")[1] if r["task"] != rd.SET_TASK else ""))].append(r)
    for (name, task), rows in sorted(grp.items()):
        conds = [c for c, _ in rd.classes_of(rows[0]["task"])]
        acc = sum(1 for r in rows if conds[max(range(len(conds)), key=lambda i: r["probs"][i])] == r["truth"]) / len(rows)
        first = sum(1 for r in rows if r["valid"] and r["attempt"] == 0)
        uni = sum(1 for r in rows if not r["valid"])
        tin = sum(r["usage"].get("input_tokens", 0) for r in rows) / len(rows)
        tc = sum(r["usage"].get("cache_read", 0) + r["usage"].get("cache_write", 0) for r in rows) / len(rows)
        L.append(f"| {name} | {task} | {len(rows)} | {first} | {uni} | {tin:.0f} | {tc:.0f} | {acc:.2f} |")
    sets_ok = [r for r in rr if r["task"] == rd.SET_TASK and r["valid"]]
    if sets_ok:
        cp = rd.config_probs(sets_ok[0]["probs"])
        L += ["", f"Set replies decompose into structure and same-root probabilities, for example {json.dumps(cp)}."]
    ru = reader_usage(rr)
    J["reader_usage"] = {f"{a}|{b}": v for (a, b), v in ru.items()}
    L += ["", "Cache behavior by reader and kind: " + "; ".join(
        f"{a} {b}: {v['n']:.0f} calls, {v['hit']:.0%} read the cache, mean prefix {v['prefix']:.0f} tokens"
        for (a, b), v in sorted(ru.items())) + ".", ""]

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
    proj_producers = dict(proj)
    # readers in the full run, per reader: items and cache groups (one group per task or stratum and fold)
    nf = 5
    full_reader = {
        "single": (60 * sum(len(rd.TASKS[t]) for ts in rd.GENRE_TASKS.values() for t in ts),
                   nf * sum(len(ts) for ts in rd.GENRE_TASKS.values())),
        "set": (60 * 3 * 2 * 3, nf * 2 * 3),
    }
    scen = {"no cache": Counter(), "cached": Counter()}
    reader_detail = {}
    for name in READERS:
        prov = adapters.provider_of(name)
        pi, po = adapters.PRICES[name]
        for kind, (n_items, n_groups) in full_reader.items():
            u = ru.get((name, kind))
            if not u:
                continue
            total_in = u["uncached"] + u["prefix"]
            hits = [r for r in rr if r["reader"] == name and (r["task"] == rd.SET_TASK) == (kind == "set")
                    and r["usage"].get("cache_read", 0) > 0]
            P = (sum(r["usage"]["cache_read"] for r in hits) / len(hits)) if hits else 0.0
            item_in = total_in - P
            c_none = n_items * (total_in * pi + u["out"] * po) / 1e6
            c_cache = (n_groups * P * adapters.CACHE_WRITE[prov] + (n_items - n_groups) * P * adapters.CACHE_READ[prov]
                       + n_items * item_in + 0) / 1e6 * pi + n_items * u["out"] * po / 1e6
            scen["no cache"][prov] += c_none
            scen["cached"][prov] += c_cache
            reader_detail[f"{name}|{kind}"] = {"items": n_items, "groups": n_groups, "input": total_in,
                                               "cached_prefix": P, "output": u["out"], "no_cache": c_none,
                                               "cached": c_cache}
    spent = ledger.spent if ledger else {}
    L += ["## Full-run cost projection", "",
          "Producers: exact call counts from realizing the full plan with the mock model (shared keys counted once), "
          "times the measured mean cost per logical call in this run, including retries, by model, genre, and "
          "function, at standard synchronous prices. Readers: synchronous calls, both readers on the first replicate, "
          "items and cache groups counted from the reader stage's plan, tokens as measured here. The cached "
          "scenario writes each group's prefix once and reads it for the rest of the group, at the ledger's cache "
          "prices (" + ", ".join(f"{k} read {adapters.CACHE_READ[k]:g}, write {adapters.CACHE_WRITE[k]:g}"
                                  for k in ("anthropic", "openai")) + " of input). The no-cache scenario is the "
          "bound if caching fails.", "",
          "| Provider | Producers | Readers, no cache | Readers, cached | Total, cached | Total, no cache | Spent so far | "
          "Ledger cap | Remaining under cap |", "|---|---|---|---|---|---|---|---|---|"]
    for prov in ("google", "anthropic", "openai"):
        sp = spent.get(prov, 0.0)
        pr = proj_producers.get(prov, 0.0)
        L.append(f"| {prov} | ${pr:.2f} | ${scen['no cache'][prov]:.2f} | ${scen['cached'][prov]:.2f} | "
                 f"${pr + scen['cached'][prov]:.2f} | ${pr + scen['no cache'][prov]:.2f} | ${sp:.2f} | "
                 f"${adapters.CAPS[prov]:.2f} | ${adapters.CAPS[prov] - sp:.2f} |")
    L += ["", "Reader detail: " + "; ".join(
        f"{k}: {v['items']} items in {v['groups']} groups, {v['input']:.0f} input tokens of which {v['cached_prefix']:.0f} "
        f"cached, {v['output']:.0f} output" for k, v in reader_detail.items()) + ".", "",
        "Producer calls in the full run: " + ", ".join(
        f"{p.split('-')[0]} {g} {fn} {n}" for (p, g, fn), n in sorted(full_counts.items())) + ".", ""]
    J["projection"] = {"producers": proj_producers, "readers": {k: dict(v) for k, v in scen.items()},
                       "reader_detail": reader_detail, "per_call": {"|".join(k): v for k, v in per_call.items()},
                       "full_counts": {"|".join(k): v for k, v in full_counts.items()}}
    return L, J


class Frozen:
    """A producer that may only read the store: same version and request
    parameters as the live adapter, so request hashes match, but any call
    raises. The reader stage rebuilds the producer results through it."""

    def __init__(self, m):
        self.version, self._p = m.version, req_params(m)

    def request_params(self):
        return self._p

    def __call__(self, prompt, seed):
        raise RuntimeError("the reader stage found a producer key with no stored output")


def full_splits(worlds):
    folds = json.load(open(os.path.join(HERE, "worlds", "assignment.json")))["folds"]
    ids = [w.world_id for w in worlds]
    return [(f"fold{f}", [i for i in ids if folds[i] == f], [i for i in ids if folds[i] != f])
            for f in sorted(set(folds.values()))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["verification", "full", "readers"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--tag", default="", help="suffix for the run directory, e.g. v2 writes runs/verification_v2")
    a = ap.parse_args()
    stage = "full" if a.phase == "readers" else a.phase
    phase_dir = os.path.join(HERE, "runs", stage + (f"_{a.tag}" if a.tag else "") + ("-dry" if a.dry_run else ""))
    os.makedirs(phase_dir, exist_ok=True)
    code_hash = snapshot(phase_dir)
    ledger = None if a.dry_run else adapters.Ledger(os.path.join(HERE, "smoke", "ledger.json"))
    embed = None
    if a.phase == "verification":
        os.makedirs(os.path.dirname(EMBED_CACHE), exist_ok=True)
        try:
            from residue.embed import Embedder
            embed = Embedder(EMBED_CACHE)
        except Exception as e:
            if not a.dry_run:
                raise
            print("embedding server unavailable in dry run:", e)
    worlds, reps = load_worlds(stage), replicates(stage)
    models = producers(a.dry_run, ledger)
    config = {"phase": a.phase, "dry_run": a.dry_run, "code_hash": code_hash, "run_seed": RUN_SEED,
              "producers": list(PRODUCERS), "readers": list(READERS), "judge": JUDGE,
              "max_output_tokens": {f"{p}|{g}": max_tokens(g, p) for p in PRODUCERS for g in ("incident", "news")},
              "length_window": list(__import__("residue.store", fromlist=["x"]).LENGTH_WINDOW),
              "worlds": [w.world_id for w in worlds], "replicates": reps,
              "embedding": {"model": "nomic-embed-text", "digest": getattr(embed, "digest", None)},
              "started": time.time()}
    with open(os.path.join(phase_dir, "config.jsonl"), "a") as fh:
        fh.write(json.dumps(config) + "\n")
    store = CallStore(os.path.join(phase_dir, "calls.jsonl"), extra={"code_hash": code_hash})
    blocks = plan(worlds, reps)
    if a.phase == "readers":
        # first replicate only, primary producer, rebuilt from the store without calls
        rblocks = [b for b in blocks if b[1].replicate == 0 and b[1].producer == PRIMARY]
        frozen = {k: Frozen(m) for k, m in models.items()}
        results, failures, errors = run_blocks(rblocks, store, frozen, a.workers)
        print(f"rebuilt {len(results)} blocks; failed trials in {len(failures)} blocks; errors {len(errors)}", flush=True)
        groups = reader_groups(results, worlds, full_splits(worlds))
        print(f"reader groups {len(groups)}, items per reader {sum(len(v) for v in groups.values())}", flush=True)
        rr = run_reader_groups(groups, make_readers(a.dry_run, ledger),
                               rd.ReaderLog(os.path.join(phase_dir, "reader_calls.jsonl"), extra={"code_hash": code_hash}))
        print(f"reader calls final {len(rr)}; uniform after retry {sum(1 for r in rr if not r['valid'])}")
        print("usage:", json.dumps({f"{x}|{y}": v for (x, y), v in reader_usage(rr).items()}))
        if ledger:
            print("spend:", ledger.spent)
        return
    print(f"{a.phase}: {len(worlds)} worlds, {len(blocks)} blocks, code {code_hash[:12]}", flush=True)
    results, failures, errors = run_blocks(blocks, store, models, a.workers)
    print(f"generation done: {store.calls_made} calls made, {len(failures)} blocks with failed trials, "
          f"{len(errors)} block errors", flush=True)
    with open(os.path.join(phase_dir, "generation_summary.json"), "w") as fh:
        json.dump({"calls_made": store.calls_made, "failures": failures, "errors": errors,
                   "coverage": {k: dict(v) for k, v in plan_coverage(blocks, results, failures).items()},
                   "time": time.time()}, fh, indent=1)
    if a.phase == "verification":
        L, J = verification_report(phase_dir, worlds, results, failures, errors, store, ledger, a.dry_run, embed,
                                   a.workers, blocks, models)
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

"""World drafting (design Part VII, build spec section 4).

A drafting model writes each world as JSON from a fixed schema and event
type. The draft is parsed and checked mechanically, then read by a checking
model from a different family, which looks for the semantic defects the
mechanical checks cannot see: disputes whose claims concern different
referents or can both be true, facts that settle a dispute, sources that
could not know their facts, and inconsistencies. A rejected draft is redrafted
with the checker's reasons. Every prompt, response, and verdict is logged.

Version 2 (2026-10-30), after the GPT review of world bank v1. The v1 schema
marked conflicts with a 0/1 field that the drafter read as member order in
nine worlds, pairing causes with counts. Disputes are now explicit objects,
each holding its two claims, so pair membership cannot be mislabeled. The
source list is closed and counted, and fact order is shuffled by world ID so
the core and the disputes do not sit at fixed positions.
"""
import json
import os
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, List, Optional, Tuple

from .worlds import Proposition, World, validate

EVENT_TYPES = (
    "generator shutdown", "water main break", "warehouse fire", "chemical spill", "network outage",
    "bridge closure", "food contamination", "hospital power loss", "train derailment", "dam spillway release",
    "airport baggage system failure", "gas leak", "elevator failure", "server room flood",
)  # 14 types, five worlds each
WORLDS_PER_TYPE = 5
N_FACTS = 15  # plus the core and four dispute claims: 20 propositions
DISPUTE_KINDS = ("cause", "count", "time", "duration", "measurement", "location", "identity", "sequence", "decision basis")

DRAFT_PROMPT = """Write one fictional event record as JSON for a controlled study of how information changes as reports are passed between writers.

Event type: {event_type}.

Already drafted events of this type. This one must differ from them in setting, circumstances, the people or objects affected, and the kinds of disagreement:
{siblings}

Invented place and organization names already used in other records, which you must not reuse: {used_names}
{feedback}
Return only one JSON object with these fields:
- "event": one sentence describing the central event.
- "sources": the closed list of four to six distinct in-world sources for this record, chosen before writing the facts. Mix human observers, institutional records, and instruments.
- "core": an object with "text", one sentence stating the central event and when it happened, and "source".
- "facts": exactly 15 further facts, each an object with "text" (one factual sentence) and "source".
- "disputes": exactly two objects. Each has "kind" (one of: {kinds}), "about" (a short phrase naming the single thing in dispute, such as "number of workers inside when the alarm sounded"), and "claims", a list of exactly two objects with "text" and "source".
- "names": every invented place and organization name used in this record.

Requirements:
1. Every "source" value must exactly match one name in "sources". Each source must be able to observe or document the fact attributed to it, and this applies to the dispute claims too: each claim's source must be placed to know the disputed thing. A sensor or log records readings and events, not causal diagnoses. A roster cannot record an arrival time. A ticket manifest cannot establish injuries or how long a line was closed.
2. The two claims of a dispute come from different sources and concern the same referent, with the same measurement definition, population, place, and time or reporting window. They must be incompatible, so that a careful writer could not report both as true, and neither may be obviously the correct one. Do not set people present at an alarm against people counted later at an assembly point, or a whole system's contents against one part of it. If the dispute is about a cause or a decision basis, state each claim as the sole cause or basis, excluding the other.
3. The two disputes must be of different kinds. Prefer kinds and number contrasts that the records above did not use.
4. No fact, including the core, may confirm one claim of either dispute or make the other impossible. Background facts may be relevant, but they must not settle either dispute. A repair, excavation, inspection, or reading at one place, or of one part, settles a dispute about where or what failed.
5. At least four sentences contain numbers: times, counts, durations, or measurements. Mix highly salient facts, useful operational details, and peripheral but relevant ones. No sentence repeats or paraphrases another. Vary how sentences begin, and do not open most of them with a time.
6. Keep chronology, quantities, places, and sources consistent everywhere outside the two disputes, and use plausible times, measurements, roles, and actions.
7. Use invented names for every person, institution, and place, and describe no real incident. Ordinary reporting about accidents, outages, failures, illness, or releases is fine. Include no instructions for causing harm.
8. Return only the JSON, with no commentary or markdown fences."""

CHECK_PROMPT = """You are checking a fictional event record written for a study of how reports change as they are passed between writers. Writers will receive these facts with their sources. Each record has a core fact (C), background facts (F1 to F15), and two disputes. Each dispute has two claims from different sources that are meant to be incompatible accounts of the same thing, with neither obviously correct and with no other sentence settling it.

Record:
{record}

Go through every labeled sentence, including C and the dispute claims. For each one, decide whether its source could actually observe or document what the sentence says. A log or instrument records readings and events, not diagnoses. A person can report what they saw, heard, measured, or did, or what their role requires them to know. A bystander, volunteer, or class instructor cannot be the source of a technical finding such as where a pipe failed or what an inspection found. For C and each F sentence, also decide whether it would lead a careful reader of the whole record to prefer one claim of a dispute, for example because it reports an action, finding, repair, or reading that fits one claim and not the other. Then assess each dispute.

Report clear defects, not stylistic preferences or remote possibilities. Answer with only a JSON object of this form, with one entry in "items" for every labeled sentence:
{{"items": [{{"label": "C", "source_can_know": true, "favors": null, "note": ""}}, {{"label": "F1", "source_can_know": true, "favors": null, "note": ""}}],
 "disputes": [{{"dispute": 1, "same_referent": true, "incompatible": true, "one_side_obvious": false, "note": ""}}, {{"dispute": 2, "same_referent": true, "incompatible": true, "one_side_obvious": false, "note": ""}}],
 "inconsistencies": [{{"labels": ["F2", "F9"], "note": "the contradiction outside the disputes"}}],
 "real_referents": [{{"name": "", "note": "a real organization, person, place, or incident"}}]}}
"favors" is null or the label of the claim the sentence favors (D1a, D1b, D2a, or D2b), and is always null for the dispute claims themselves. same_referent is false when the two claims concern different populations, times, measurement definitions, or objects. incompatible is false when both claims could be true together. Use empty lists where there is nothing to report."""


def draft_prompt(event_type: str, siblings: List[str], used_names: List[str], feedback: str = "") -> str:
    fb = f"\nA previous draft of this record was rejected for these reasons, which this draft must avoid:\n{feedback}\n" if feedback else ""
    return DRAFT_PROMPT.format(event_type=event_type, siblings="\n".join(siblings) if siblings else "none yet",
                               used_names=", ".join(sorted(set(used_names))) if used_names else "none yet",
                               feedback=fb, kinds=", ".join(DISPUTE_KINDS))


def _load_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):]
    try:
        return json.loads(text[text.find("{"): text.rfind("}") + 1])
    except json.JSONDecodeError as e:
        raise ValueError(f"not JSON: {e}")


def parse_draft(raw: str, world_id: str, event_type: str, index: int) -> Tuple[World, dict]:
    """Parse a drafted response into a World plus its metadata, running the
    mechanical checks. Raises ValueError with the reason when the draft is not
    acceptable. Fact order is shuffled with a seed derived from the world ID."""
    d = _load_json(raw)
    try:
        sources = [str(s).strip() for s in d["sources"]]
        core = d["core"]
        facts = d["facts"]
        disputes = d["disputes"]
    except (KeyError, TypeError) as e:
        raise ValueError(f"missing field: {e}")
    if not 4 <= len(set(sources)) <= 6 or len(set(sources)) != len(sources):
        raise ValueError(f"source list must hold four to six distinct names, got {len(sources)}")
    if len({s.lower() for s in sources}) != len(sources):
        raise ValueError("two sources differ only in case")
    if not isinstance(facts, list) or len(facts) != N_FACTS:
        raise ValueError(f"expected {N_FACTS} facts, got {len(facts) if isinstance(facts, list) else 'none'}")
    if not isinstance(disputes, list) or len(disputes) != 2 or any(len(x.get("claims", [])) != 2 for x in disputes):
        raise ValueError("expected two disputes with two claims each")
    kinds = [str(x.get("kind", "")).strip().lower() for x in disputes]
    if any(k not in DISPUTE_KINDS for k in kinds) or kinds[0] == kinds[1]:
        raise ValueError(f"dispute kinds must be two different listed kinds, got {kinds}")
    entries = [(core, True, None)] + [(f, False, None) for f in facts] + \
              [(c, False, i) for i, x in enumerate(disputes) for c in x["claims"]]
    for e, _, _ in entries:
        if str(e.get("source", "")).strip() not in sources:
            raise ValueError(f"source not in the list: {e.get('source')!r}")
    for i, x in enumerate(disputes):
        a, b = x["claims"]
        if a["source"].strip() == b["source"].strip():
            raise ValueError(f"dispute {i + 1} has one source")
    texts = [str(e["text"]).strip() for e, _, _ in entries]
    if len({t.lower() for t in texts}) != len(texts):
        raise ValueError("duplicate sentence")
    if sum(any(ch.isdigit() for ch in t) for t in texts) < 4:
        raise ValueError("fewer than four sentences with numbers")
    order = list(range(len(entries)))
    random.Random(world_id).shuffle(order)
    props = [Proposition(f"p{j:02d}", texts[k], entries[k][1], str(entries[k][0]["source"]).strip(), entries[k][2])
             for j, k in enumerate(order)]
    world = World(world_id, event_type, index, props)
    try:
        validate(world)
    except AssertionError as e:
        raise ValueError(str(e))
    meta = {"event": str(d.get("event", "")).strip(), "sources": sources, "names": [str(n) for n in d.get("names", [])],
            "disputes": [{"kind": kinds[i], "about": str(x.get("about", "")).strip()} for i, x in enumerate(disputes)]}
    return world, meta


def parse_world(raw: str, world_id: str, event_type: str, index: int) -> World:
    return parse_draft(raw, world_id, event_type, index)[0]


def record_for_check(world: World, meta: dict) -> Tuple[str, Dict[str, str]]:
    """The record as the checker sees it, with labels C (core), F1.. (facts),
    and D1a, D1b, D2a, D2b (dispute claims). Returns the text and label->pid."""
    labels: Dict[str, str] = {}
    by = world.by_id()
    lines = [f"C. {world.core.text} (source: {world.core.source})"]
    labels["C"] = world.core.pid
    n = 0
    for p in world.propositions:
        if not p.core and p.conflict_pair is None:
            n += 1
            labels[f"F{n}"] = p.pid
            lines.append(f"F{n}. {p.text} (source: {p.source})")
    for i, pair in enumerate(world.conflict_pairs()):
        lines.append(f"Dispute {i + 1}, about {meta['disputes'][i]['about']}:")
        for tag, pid in zip("ab", pair):
            labels[f"D{i + 1}{tag}"] = pid
            lines.append(f"D{i + 1}{tag}. {by[pid].text} (source: {by[pid].source})")
    return "\n".join(lines), labels


def check_problems(verdict: dict, n_items: int = 20) -> List[str]:
    """The checker's verdict as a list of defects. An empty list passes."""
    out = []
    items = verdict.get("items", [])
    if len(items) != n_items:
        out.append(f"checker assessed {len(items)} of {n_items} sentences")
    for x in items:
        if not x.get("source_can_know", True):
            out.append(f"{x.get('label')}: the source could not know this. {x.get('note', '')}")
        if x.get("favors"):
            out.append(f"{x.get('label')} favors {x.get('favors')}. {x.get('note', '')}")
    for x in verdict.get("disputes", []):
        if not x.get("same_referent", False):
            out.append(f"dispute {x.get('dispute')}: the claims concern different referents. {x.get('note', '')}")
        if not x.get("incompatible", False):
            out.append(f"dispute {x.get('dispute')}: both claims could be true. {x.get('note', '')}")
        if x.get("one_side_obvious", False):
            out.append(f"dispute {x.get('dispute')}: one claim is obviously correct. {x.get('note', '')}")
    if len(verdict.get("disputes", [])) != 2:
        out.append("checker did not assess both disputes")
    for x in verdict.get("inconsistencies", []):
        out.append(f"{', '.join(x.get('labels', []))} are inconsistent. {x.get('note', '')}")
    for x in verdict.get("real_referents", []):
        out.append(f"real referent {x.get('name')}. {x.get('note', '')}")
    return [s.strip() for s in out]


def _accepted_from_log(log_path: str) -> Dict[str, dict]:
    """Accepted drafts already in the log, so an interrupted run resumes
    without paying for them again."""
    out: Dict[str, dict] = {}
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                if r.get("accepted"):
                    out[r["world_id"]] = r
    return out


def _sibling_line(world: World, meta: dict) -> str:
    ds = "; ".join(f"{x['kind']}: {x['about']}" for x in meta["disputes"])
    return f"- {world.core.text} Disputes: {ds}."


def draft_bank(draft: Callable[[str], str], log_path: str, check: Optional[Callable[[str], str]] = None,
               max_attempts: int = 4, workers: int = 1) -> List[Tuple[World, dict]]:
    """Draft 70 worlds, five per event type, logging every attempt. A draft
    must pass the mechanical checks and, when a checker is given, the semantic
    check. When no attempt passes, the attempt with the fewest checker
    problems is kept and flagged for manual review. A refusal or an API error
    counts as a failed attempt. Event types can be drafted in parallel. The
    five worlds of a type are drafted in order, each seeing its siblings, and
    the invented names of every world finished so far are shared across types."""
    done = _accepted_from_log(log_path)
    used_names: List[str] = []
    lock = threading.Lock()

    def log(rec: dict) -> None:
        with lock:
            with open(log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")

    def one_world(wid: str, et: str, index: int, siblings: List[str]) -> Tuple[World, dict]:
        prev = done.get(wid)
        if prev is not None and prev["event_type"] == et:
            world, meta = parse_draft(prev["raw"], wid, et, index)
            meta.update(check_problems=prev.get("problems", []), flagged=prev.get("flagged", False))
            return world, meta
        best: Optional[Tuple[int, World, dict, List[str], str, str]] = None
        feedback = ""
        for attempt in range(max_attempts):
            with lock:
                names = list(used_names)
            prompt = draft_prompt(et, siblings, names, feedback)
            reason, problems, raw, verdict_raw = None, [], "", ""
            try:
                raw = draft(prompt)
            except Exception as e:  # refusal or API error
                reason = f"call failed: {type(e).__name__}: {e}"
            if reason is None:
                try:
                    w, m = parse_draft(raw, wid, et, index)
                except ValueError as e:
                    reason = str(e)
            if reason is None and check is not None:
                record, _ = record_for_check(w, m)
                try:
                    verdict_raw = check(CHECK_PROMPT.format(record=record))
                    problems = check_problems(_load_json(verdict_raw))
                except Exception as e:
                    problems = [f"check failed: {type(e).__name__}: {e}"]
                if best is None or len(problems) < best[0]:
                    best = (len(problems), w, m, problems, raw, verdict_raw)
                if problems:
                    reason = "check: " + " | ".join(problems)
            flagged = bool(attempt == max_attempts - 1 and reason and best is not None)
            accepted = reason is None or flagged
            if flagged:
                _, w, m, problems, raw, verdict_raw = best
            log({"world_id": wid, "event_type": et, "attempt": attempt, "prompt": prompt, "raw": raw,
                 "verdict": verdict_raw, "problems": problems, "accepted": accepted, "flagged": flagged,
                 "reason": reason, "time": time.time()})
            if accepted:
                m.update(check_problems=problems, flagged=flagged)
                return w, m
            feedback = reason or ""
        raise RuntimeError(f"{wid}: no parseable draft after {max_attempts} attempts")

    def one_type(t: int, et: str) -> List[Tuple[World, dict]]:
        out: List[Tuple[World, dict]] = []
        siblings: List[str] = []
        for k in range(WORLDS_PER_TYPE):
            index = t * WORLDS_PER_TYPE + k
            world, meta = one_world(f"W{index:03d}", et, index, siblings)
            out.append((world, meta))
            siblings.append(_sibling_line(world, meta))
            with lock:
                used_names.extend(meta["names"])
        return out

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(one_type, t, et) for t, et in enumerate(EVENT_TYPES)]
        results = [f.result() for f in futures]
    return [x for r in results for x in r]


def save_bank(bank: List[Tuple[World, dict]], path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for w, meta in bank:
            fh.write(json.dumps({"world_id": w.world_id, "event_type": w.event_type, "index": w.index,
                                 "propositions": [p.__dict__ for p in w.propositions], "meta": meta}) + "\n")


def load_bank(path: str, with_meta: bool = False):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            w = World(d["world_id"], d["event_type"], d["index"], [Proposition(**p) for p in d["propositions"]])
            validate(w)
            out.append((w, d.get("meta", {})) if with_meta else w)
    return out

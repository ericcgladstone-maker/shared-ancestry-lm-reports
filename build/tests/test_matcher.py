from residue.matcher import (ALTERED, OMITTED, PRESERVED, QUALIFIED, IndependentNull, deviations, match,
                             shared_deviations)
from residue.worlds import Proposition, World


def make_world():
    props = [
        Proposition("p0", "Generator 2 shut down at 09:40.", True, "shift supervisor"),
        Proposition("p1", "The cooling loop ran hot for 20 minutes.", False, "sensor record", 0),
        Proposition("p2", "A sensor fault caused the alarm.", False, "maintenance log", 0),
        Proposition("p3", "The backup unit started after 8 minutes.", False, "dispatch note", 1),
        Proposition("p4", "The backup unit failed to start.", False, "safety officer", 1),
        Proposition("p5", "The west line kept running.", False, "shift supervisor"),
    ]
    return World("WT", "generator", 0, props)


def embed(text):
    """Word-overlap embedding: tests need only that a sentence is closest to
    the proposition it restates."""
    vocab = ["generator", "shut", "cooling", "loop", "hot", "sensor", "fault", "alarm", "backup", "unit",
             "started", "start", "failed", "west", "line", "running", "minutes"]
    low = text.lower()
    return [float(w in low) for w in vocab]


def test_states_and_conflicts():
    w = make_world()
    text = ("Generator 2 shut down at 09:40. The cooling loop may have run hot for 20 minutes. "
            "The backup unit started after 9 minutes.\nSources: shift supervisor")
    m = match(text, w, embed, threshold=0.6)
    assert m.states["p0"] == PRESERVED
    assert m.states["p1"] == QUALIFIED
    assert m.states["p3"] == ALTERED  # 8 minutes became 9
    assert m.states["p5"] == OMITTED
    assert m.conflicts[0] == "p1"  # only the loop member asserted


def test_omission_outside_package_is_not_a_deviation():
    w = make_world()
    m = match("Generator 2 shut down at 09:40.", w, embed, threshold=0.6)
    dev_full = deviations(m, [p.pid for p in w.propositions])
    dev_small = deviations(m, ["p0"])
    assert ("omit", "p5") in dev_full and ("omit", "p5") not in dev_small


def test_shared_deviation_and_null():
    a = {("omit", "p5"), ("alter", "p3")}
    b = {("omit", "p5"), ("alter", "p1")}
    assert shared_deviations(a, b) == 1
    null = IndependentNull(weight=5)
    for c in (1, 1, 2):
        null.add("generator", c)
    null.add("fire", 4)
    assert 1.0 < null.expected("generator") < 2.5
    assert null.excess("generator", 3) > 0

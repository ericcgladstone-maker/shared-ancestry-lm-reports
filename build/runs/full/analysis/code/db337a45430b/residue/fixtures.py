"""Hand-written reference graphs (build spec section 3).

Written out literally, without loops or shared helpers, so that they are an
independent statement of the design. Each entry maps node name to
(function, parents). "terminals" lists the observed node or nodes. "full"
lists the observers that must receive the full world record.
"""

O, R, S = "observe", "rewrite", "synthesize"

FIXTURES = {
    "D0": {"nodes": {"o1": (O, ())}, "terminals": ("o1",), "full": ("o1",)},
    "NC0": {"nodes": {"o1": (O, ()), "x2": (O, ()), "x3": (O, ())}, "terminals": ("o1",), "full": ("o1", "x2", "x3")},
    "R1": {"nodes": {"o1": (O, ()), "r1": (R, ("o1",))}, "terminals": ("r1",), "full": ("o1",)},
    "R3": {"nodes": {"o1": (O, ()), "r1": (R, ("o1",)), "r2": (R, ("r1",)), "r3": (R, ("r2",))},
           "terminals": ("r3",), "full": ("o1",)},
    "R5": {"nodes": {"o1": (O, ()), "r1": (R, ("o1",)), "r2": (R, ("r1",)), "r3": (R, ("r2",)),
                     "r4": (R, ("r3",)), "r5": (R, ("r4",))},
           "terminals": ("r5",), "full": ("o1",)},
    "NCR1": {"nodes": {"o1": (O, ()), "r1": (R, ("o1",)), "x2": (R, ("o1",)), "x3": (R, ("o1",))},
             "terminals": ("r1",), "full": ("o1",)},
    "F1": {"nodes": {"f1": (O, ()), "syn": (S, ("f1",))}, "terminals": ("syn",), "full": ("f1",)},
    "F2": {"nodes": {"f1": (O, ()), "f2": (O, ()), "syn": (S, ("f1", "f2"))}, "terminals": ("syn",), "full": ()},
    "F3": {"nodes": {"f1": (O, ()), "f2": (O, ()), "f3": (O, ()), "syn": (S, ("f1", "f2", "f3"))},
           "terminals": ("syn",), "full": ()},
    "SI-same": {"nodes": {"o1": (O, ()), "o2": (O, ()), "o3": (O, ()),
                          "w1": (R, ("o1",)), "w2": (R, ("o2",)), "w3": (R, ("o3",)),
                          "syn": (S, ("w1", "w2", "w3"))},
                "terminals": ("syn",), "full": ("o1", "o2", "o3")},
    "SD-same": {"nodes": {"o1": (O, ()), "w1": (R, ("o1",)), "w2": (R, ("o1",)), "w3": (R, ("o1",)),
                          "syn": (S, ("w1", "w2", "w3"))},
                "terminals": ("syn",), "full": ("o1",)},
    "SI-div": {"nodes": {"o1": (O, ()), "o2": (O, ()), "o3": (O, ()),
                         "w1": (R, ("o1",)), "w2": (R, ("o2",)), "w3": (R, ("o3",)),
                         "syn": (S, ("w1", "w2", "w3"))},
               "terminals": ("syn",), "full": ()},
    "SD-div": {"nodes": {"o1": (O, ()), "w1": (R, ("o1",)), "w2": (R, ("o1",)), "w3": (R, ("o1",)),
                         "syn": (S, ("w1", "w2", "w3"))},
               "terminals": ("syn",), "full": ("o1",)},
    "SI-same+1": {"nodes": {"o1": (O, ()), "o2": (O, ()), "o3": (O, ()),
                            "w1": (R, ("o1",)), "w2": (R, ("o2",)), "w3": (R, ("o3",)),
                            "syn": (S, ("w1", "w2", "w3")), "p1": (R, ("syn",))},
                  "terminals": ("p1",), "full": ("o1", "o2", "o3")},
    "SD-same+1": {"nodes": {"o1": (O, ()), "w1": (R, ("o1",)), "w2": (R, ("o1",)), "w3": (R, ("o1",)),
                            "syn": (S, ("w1", "w2", "w3")), "p1": (R, ("syn",))},
                  "terminals": ("p1",), "full": ("o1",)},
    # The compound fixtures: the synthesis output, not the world record, is the
    # parent of the first downstream rewrite.
    "SI-same+3": {"nodes": {"o1": (O, ()), "o2": (O, ()), "o3": (O, ()),
                            "w1": (R, ("o1",)), "w2": (R, ("o2",)), "w3": (R, ("o3",)),
                            "syn": (S, ("w1", "w2", "w3")),
                            "p1": (R, ("syn",)), "p2": (R, ("p1",)), "p3": (R, ("p2",))},
                  "terminals": ("p3",), "full": ("o1", "o2", "o3")},
    "SD-same+3": {"nodes": {"o1": (O, ()), "w1": (R, ("o1",)), "w2": (R, ("o1",)), "w3": (R, ("o1",)),
                            "syn": (S, ("w1", "w2", "w3")),
                            "p1": (R, ("syn",)), "p2": (R, ("p1",)), "p3": (R, ("p2",))},
                  "terminals": ("p3",), "full": ("o1",)},
}

_S2_IND = {"nodes": {"o1": (O, ()), "o2": (O, ()), "o3": (O, ()),
                     "m1": (R, ("o1",)), "m2": (R, ("o2",)), "m3": (R, ("o3",))},
           "terminals": ("m1", "m2", "m3")}
_S2_DEP = {"nodes": {"o1": (O, ()), "m1": (R, ("o1",)), "m2": (R, ("o1",)), "m3": (R, ("o1",))},
           "terminals": ("m1", "m2", "m3")}
_S2_MIX = {"nodes": {"o1": (O, ()), "o3": (O, ()), "m1": (R, ("o1",)), "m2": (R, ("o1",)), "m3": (R, ("o3",))},
           "terminals": ("m1", "m2", "m3")}

for _instr in ("neutral", "conceal"):
    FIXTURES[f"IND-full-{_instr}"] = dict(_S2_IND, full=("o1", "o2", "o3"))
    FIXTURES[f"DEP-full-{_instr}"] = dict(_S2_DEP, full=("o1",))
    FIXTURES[f"MIX-full-{_instr}"] = dict(_S2_MIX, full=("o1", "o3"))
    FIXTURES[f"IND-partial-{_instr}"] = dict(_S2_IND, full=())
    FIXTURES[f"DEP-partial-{_instr}"] = dict(_S2_DEP, full=())
    FIXTURES[f"MIX-partial-{_instr}"] = dict(_S2_MIX, full=())

# Histories (design Part V-A), written from the design table, not computed.
# (synthesis, inputs, roots, rewrites before, rewrites after)
HISTORY_TABLE = {
    "D0": ("no", 0, 1, 0, 0), "NC0": ("no", 0, 1, 0, 0),
    "R1": ("no", 0, 1, 0, 1), "NCR1": ("no", 0, 1, 0, 1),
    "R3": ("no", 0, 1, 0, 3), "R5": ("no", 0, 1, 0, 5),
    "F1": ("yes", 1, 1, 0, 0), "F2": ("yes", 2, 2, 0, 0), "F3": ("yes", 3, 3, 0, 0),
    "SD-same": ("yes", 3, 1, 1, 0), "SD-div": ("yes", 3, 1, 1, 0),
    "SI-same": ("yes", 3, 3, 1, 0), "SI-div": ("yes", 3, 3, 1, 0),
    "SD-same+1": ("yes", 3, 1, 1, 1), "SD-same+3": ("yes", 3, 1, 1, 3),
    "SI-same+1": ("yes", 3, 3, 1, 1), "SI-same+3": ("yes", 3, 3, 1, 3),
}

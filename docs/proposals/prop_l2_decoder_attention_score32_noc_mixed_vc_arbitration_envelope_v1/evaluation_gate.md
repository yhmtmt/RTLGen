# Evaluation Gate

Require every row to deliver exactly 60,928 VC0 and 10,020 VC1 flits. Evaluate
all five relative-release offsets under both endpoint policies. Preserve four
sequential VC1 group lifecycles and the exact 256-bit, four-VC, depth-four
router contract.

Reject a result that omits source queue occupancy, silently treats an
unbounded queue as current RTL, or selects a raw latency minimum that fails the
one-register source boundary.

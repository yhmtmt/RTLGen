# Quality Gate

- Exact 419-bit round-trip for multiple canonical groups in both modes.
- Arbitrary deterministic source, transport, and sink stalls.
- Exactly 256 aligned or 167 stats-once flits per 128-beat group.
- Stable ready/valid payloads and no protocol errors for valid traffic.
- Invalid order, context, terminal marker, and padding are rejected.
- Generated hierarchy passes Icarus elaboration and Yosys process/check.
- Both PPA candidates use the same source, sink, counters, and stall schedule.

Status: passed locally with 13 focused aligned/stats/matched RTL and generated-
hierarchy tests; physical evaluation remains pending.

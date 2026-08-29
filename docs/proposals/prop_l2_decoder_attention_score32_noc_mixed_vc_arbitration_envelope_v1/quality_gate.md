# Quality Gate

- Preserve exact score32 stats-once precision and all 70,948 flits.
- Keep VC0 and VC1 identities distinct through endpoint and router arbitration.
- Report per-phase and per-VC delivery counts for every offset and policy.
- Treat missing SRAM-residency and reducer release timing as a swept variable.
- Treat any endpoint injection stall or per-VC source depth above one as
  diagnostic rather than directly replayable.
- Do not infer a Llama7B precision change from a transport-only replay.

# Quality Gate

- Require exact equality for all 11,576 packed 102-bit commands.
- Require every generated address to be 256-byte aligned and within slots
  0..562; require exact class/source slot formulas.
- Require the runtime generated-mode guard to match the canonical packed-stream
  SHA-256 and reject same-length mutations before RTL replay.
- Require command stability while `valid && !ready`.
- Require generated hierarchy to select `GENERATED_SOURCE=1` and include the
  generator, paired scheduler, and observation harness RTL explicitly.
- Require composed endpoint/mesh replay to complete every packet and flit
  without protocol errors.

Status: exhaustive command comparison, composed replay, and generated-hierarchy
synthesis passed locally; physical evaluation pending.

# Quality Gate

- Require exact equality for all 11,576 packed 102-bit commands.
- Require command stability while `valid && !ready`.
- Require generated hierarchy to select `GENERATED_SOURCE=1` and include the
  generator, paired scheduler, and observation harness RTL explicitly.
- Require composed endpoint/mesh replay to complete every packet and flit
  without protocol errors.

Status: exhaustive command comparison, composed replay, and generated-hierarchy
synthesis passed locally; physical evaluation pending.

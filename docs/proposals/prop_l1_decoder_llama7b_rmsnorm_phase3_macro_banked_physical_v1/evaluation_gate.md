# Evaluation Gate

- Status: pending human approval and implementation merge.
- Do not dispatch from the local development branch.
- Before queueing, pin `source_commit` to the exact clean `origin/master` commit.
- Require the macro-backed Phase-3 equivalence probe to pass all seven rows.
- Require exactly 64 `fakeram45_64x32` instances and zero inferred row/gamma
  memories after elaboration.
- Preserve all non-OK rows as physical boundary evidence.
- Treat vectorless power as screening evidence only and FakeRAM as a proxy, not
  foundry SRAM signoff.

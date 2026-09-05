# Evaluation Gate

- Status: implementation merged; pending human approval.
- Do not dispatch from the local development branch.
- Source is pinned to clean merged commit `09a9854c357a419a70bc04417509b451de235c2a`.
- Require conservative and three-credit-pipelined Phase-3 equivalence probes to
  pass all seven rows.
- Require the three-credit candidate to pass the additional twelve-cycle burst
  backpressure row without exhausting a response credit.
- Require exactly 64 `fakeram45_64x32` instances and zero inferred row/gamma
  memories after elaboration for both candidates.
- Preserve all non-OK rows as physical boundary evidence.
- Treat vectorless power as screening evidence only and FakeRAM as a proxy, not
  foundry SRAM signoff.

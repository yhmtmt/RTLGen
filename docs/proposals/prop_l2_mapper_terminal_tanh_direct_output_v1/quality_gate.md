# Quality Gate

- local mapper regression covers:
  - non-fused terminal `Tanh` lowering
  - direct-output terminal `Tanh` lowering
- campaign paths validate before remote spend
- accepted reduced `nm1_tanhproxy` physical source is used in baseline and intended paired campaign
- baseline review result:
  - PR `#82` merged
  - status: `passed`
- proposal-level note:
  - quality gate is satisfied for proceeding to the paired comparison
  - proposal promotion is still blocked on the paired direct-output evidence

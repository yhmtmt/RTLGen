# Quality Gate

- no separate model-quality gate is required at the circuit-only stage
- required local checks before remote spend:
  - signed-domain smoke simulation passes
  - monotonicity on representative points is preserved
  - saturation endpoints remain bounded in the expected int8 range
- any broader output-quality gate belongs to the later integrated or Layer 2 use of this block

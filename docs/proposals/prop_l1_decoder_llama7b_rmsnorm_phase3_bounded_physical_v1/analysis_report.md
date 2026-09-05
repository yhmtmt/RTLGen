# Analysis Report

## Candidate
- `proposal_id`: `prop_l1_decoder_llama7b_rmsnorm_phase3_bounded_physical_v1`
- `candidate_id`: `l1_decoder_llama7b_rmsnorm_phase3_bounded_physical_v1_r1`

## Evaluations Consumed
- `l1_decoder_llama7b_rmsnorm_phase3_bounded_physical_v1_r1`
- `l1_decoder_llama7b_rmsnorm_phase3_bounded_physical_v1_r1_run_ac8b6daeb1245602`
- execution source: `aa752025f0742fe4496ef0940eea3a2ea96a488b`
- merged review evidence: `b64f283cf857c3a5e6c5e3dbc8cc082d4c538f2e`

## Baseline Comparison
- Both conservative clock points used the same LANES=16 Phase-3 RTL with full
  4096-element row and gamma state inferred as registers.
- 16 ns: synthesis failed after 1218.93 s with 12,074,860 KB peak memory.
- 20 ns: synthesis failed after 1107.78 s with 11,975,828 KB peak memory.
- Neither row reached routed timing, area, or power measurement.

## Result
- `boundary_no_feasible_points`
- The exact Phase-3 behavior remains useful, but the current register-storage
  embodiment is not a physically credible RMSNorm Pareto point.

## Failures and Caveats
- storage arrays are inferred registers, not SRAM evidence
- both rows failed at synthesis with return code 2
- the result is a synthesis-resource boundary, not proof that an SRAM-banked
  implementation is infeasible
- vectorless or activity-backed power cannot be claimed because no row reached
  physical implementation

## Recommendation
- iterate by preserving the Phase-3 ready/valid and arithmetic equivalence
  contract while replacing row/gamma register arrays with an explicitly banked
  SRAM interface; only then rerun bounded PPA and activity power

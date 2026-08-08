# Quality gate

- The campaign contract fixes service period 10 ns, temporal period 12 ns, divider lanes 1/2/4/8, SRAM temporal state, and macro-banked service value memory.
- The driver rejects any other point set or backend and publishes no new output directory when a probe fails.
- Every per-lane output remains compatible with `audit_attention_decode_score_multivalue_service_exact_partial_physical_recost.py` and omits row histories and generated manifests.
- Focused driver and control-plane task-generation tests pass.
- `python3 scripts/validate_runs.py --skip_eval_queue` passes.
- Dispatch is prohibited until this proposal is merged and the task is generated from the merged `origin/master` SHA.

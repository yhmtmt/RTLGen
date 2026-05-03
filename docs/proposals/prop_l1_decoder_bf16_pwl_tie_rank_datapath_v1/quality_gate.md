# Quality Gate

## Checks

- RTL generation succeeds for `examples/config_score_tie_rank.json`.
- Behavioral simulation covers score priority, logit tie-break, stable exact ties,
  and signed negative logit ordering.
- Layer 1 task generation accepts `score_tie_rank` as a single-operation wrapper.

## Local Commands

- `bash tests/test_score_tie_rank.sh`
- `python3 -m py_compile control_plane/control_plane/services/l1_task_generator.py`
- `PYTHONPATH=/workspaces/RTLGen:/workspaces/RTLGen/control_plane /workspaces/RTLGen/control_plane/.venv/bin/python3 -m pytest -q control_plane/control_plane/tests/test_l1_task_generator.py`

## Result

- status: pass
- note: local RTL generation, Verilog simulation, Python syntax check, and Layer 1 generator tests passed on 2026-05-03.

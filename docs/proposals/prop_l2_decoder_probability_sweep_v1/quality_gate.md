# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_probability_sweep_v1`
- `title`: `LLM decoder probability-template sweep`

## Why This Gate Is Required
The proposal adds a new dataset-backed decoder-quality sweep path. The gate
checks that the sweep runs locally and that generated evaluator jobs include the
new evidence command and expected output.

## Reference
- proposal: `docs/proposals/prop_l2_decoder_probability_sweep_v1/proposal.json`
- sweep tool: `npu/eval/sweep_llm_decoder_candidate_quality.py`
- dataset: `runs/datasets/llm_decoder_eval_tiny_v1/manifest.json`

## Checks
- sweep syntax:
  - threshold: `python3 -m py_compile` passes
- local sweep:
  - threshold: exact and approximate template quality summaries are emitted
- task generator:
  - threshold: `decoder_probability_sweep` adds the sweep command and output
- run index validation:
  - threshold: `scripts/validate_runs.py --skip_eval_queue` passes

## Local Commands
- `python3 -m py_compile npu/eval/sweep_llm_decoder_candidate_quality.py`
- `python3 npu/eval/sweep_llm_decoder_candidate_quality.py --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest.json --template candidate_onnx_softmax_exact --template candidate_onnx_softmax_approx --out-dir /tmp/decoder_candidate_sweep --out /tmp/decoder_candidate_sweep.json`
- `PYTHONPATH=control_plane python3 -m pytest control_plane/control_plane/tests/test_l2_task_generator.py -q`
- `python3 scripts/validate_runs.py --skip_eval_queue`

## Result
- status: local-pass
- note: local sweep, task-generator, and run-index checks passed; remote
  evaluator execution remains pending.

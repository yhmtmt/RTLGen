# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_probability_sweep_v1`
- `title`: `LLM decoder probability-template sweep`

## Problem
The exact decoder probability path restored `llm_decoder_eval_tiny_v1` quality
to `1.0` exact/top-k, while the earlier approximate path recorded `0.8`.
Approximation work should not resume from graph-pressure evidence alone. The
next step is a dataset-backed sweep that compares exact and bounded approximate
probability templates without replacing the active exact candidate.

## Hypothesis
A sidecar sweep over decoder backend templates can identify whether the current
bounded approximation envelope preserves quality, and can provide the artifact
shape needed for later approximation-specific proposals.

## Evaluation Scope
- direct comparison set:
  - `candidate_onnx_softmax_exact`
  - `candidate_onnx_softmax_approx`
  - `llm_decoder_eval_tiny_v1`
- evaluation mode:
  - `broad_ranking`
- expected result:
  - record candidate-template quality ranking, not promote hardware
- excluded first-stage comparisons:
  - RTL approximation implementation
  - mapper scheduling changes
  - tokenizer/model/prompt-set changes

## Knowledge Inputs
- `runs/datasets/llm_decoder_eval_tiny_v1/manifest.json`
- `runs/models/llm_decoder_tiny_v1/model_contract.json`
- `npu/eval/sweep_llm_decoder_candidate_quality.py`
- `docs/architecture/llm_decoder_accuracy_stage_v1.md`

## Candidate Direction
If the approximate template fails quality, continue with exact probability as
the active candidate and defer approximate datapath work. If it preserves
quality, use the sweep output to define a narrower approximation proposal.

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-04-29T00:00:00Z
- note: dataset-backed probability-template sweep approved after practical
  graph proxy evidence did not justify softmax datapath work.

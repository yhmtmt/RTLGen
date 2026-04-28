# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_exact_probability_path_v1`
- `title`: `LLM decoder exact probability-path candidate`

## Problem
- the evaluator-confirmed decoder gate currently records a valid but imperfect
  active candidate: 4/5 next-token exact matches and 4/5 top-k containment
- the miss happens before the repo has a stable quality-preserving candidate
  reference for later approximation sweeps

## Hypothesis
- switching only the active candidate probability path from q4 PWL softmax plus
  quantized reciprocal normalization to exact softmax plus exact normalization
  should recover the token-quality miss while preserving the existing model,
  tokenizer, selected tensor trace, and missing-model failure contracts

## Evaluation Scope
- direct comparison set:
  - prior evaluator-confirmed q4 PWL candidate evidence from
    `l2_decoder_contract_eval_confirm_v1`
  - regenerated exact probability-path candidate artifacts for
    `llm_decoder_eval_tiny_v1`
- evaluation modes:
  - first remote item should be `paired_comparison`
  - expected result is `better_than_historical` against the 0.8 exact/top-k
    rates from the prior candidate
- dependency order:
  - depends on `l2_decoder_contract_eval_confirm_v1` being merged and
    materialized
- excluded first-stage comparisons:
  - no claim that the exact path is a final hardware approximation
  - no model, tokenizer, or prompt-set change
- follow-on broad sweep:
  - reintroduce approximation knobs one at a time after this exact path is
    established as the active quality reference

## Knowledge Inputs
- `docs/architecture/llm_decoder_accuracy_stage_v1.md`
- `runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_compare__l2_decoder_contract_eval_confirm_v1.json`
- `runs/models/llm_decoder_tiny_v1/model_contract.json`

## Candidate Direction
- update the active candidate backend to use:
  - `softmax_mode: exact`
  - `normalization_mode: exact`
  - same ONNX model, tokenizer, top-k setting, and selected tensor trace list

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-04-28T07:29:55Z
- note: bounded quality-reference candidate for the ordinary decoder workflow

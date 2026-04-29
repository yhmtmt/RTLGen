# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_probability_sensitivity_v1`
- `title`: `LLM decoder probability sensitivity map`

## Problem
The current exact-vs-approx sweep showed that the active q4 PWL plus reciprocal
candidate drops decoder quality to `0.8`, but that single point is not enough to
understand the approximation space. Probability-path approximation behavior is
deeply dependent on model weights, prompt distribution, and logit margins.

## Hypothesis
A rough grid over several probability-path approximation families can identify
where quality cliffs begin without overfitting the next decision to one narrow
benchmark setup.

## Evaluation Scope
- rough grid:
  - exact path with coarse logit and probability quantization probes
  - PWL softmax with float, q8, q6, and q4 input/weight probes
  - reciprocal normalization probes
  - final probability quantization stress probes
- evaluation mode:
  - `broad_ranking`
- excluded:
  - RTL changes
  - mapper changes
  - promotion of approximate softmax hardware

## Caveat
Passing this benchmark is not general acceptance evidence. The result is a
local map for the pinned `llm_decoder_eval_tiny_v1` model, tokenizer, and prompt
set. A later broad dataset/model expansion is required before any hardware
approximation is promoted.

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-04-29T00:00:00Z
- note: proceed as a broad outline map, not a narrow parameter optimization.

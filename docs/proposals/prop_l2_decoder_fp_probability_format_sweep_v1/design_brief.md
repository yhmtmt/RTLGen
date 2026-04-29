# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_fp_probability_format_sweep_v1`
- `title`: `LLM decoder floating-point probability format sweep`

## Problem
The previous rough integer/fixed-point sensitivity map showed that final
unsigned q8 probability storage collapses large-vocab decoder probabilities to
zero. That is a fixed-point dynamic-range failure, not a general statement about
q8 logits or about arithmetic prompts.

## Hypothesis
A separate fp-like format sweep can distinguish dynamic-range preservation from
integer fixed-point precision loss. It should compare fp16, bf16, and fp8-style
formats at the major probability-path boundaries before any narrower hardware
format decision is made.

## Evaluation Scope
- rough grid:
  - exact baseline
  - fp-like logit probes
  - fp-like softmax input and weight probes
  - fp-like reciprocal-normalization probes
  - fp-like final probability probes
  - PWL softmax paths with fp-like intermediates
- evaluation mode:
  - `broad_ranking`
- excluded:
  - RTL changes
  - mapper changes
  - final format selection

## Caveat
Passing this benchmark is not general acceptance evidence. Approximation
sensitivity depends on weight, prompt, input, and logit-margin distributions.
This job only maps the pinned `llm_decoder_eval_tiny_v1` setup.

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-04-29T00:00:00Z
- note: proceed as a broad fp-format outline map after the integer/fixed-point
  probability sensitivity map.

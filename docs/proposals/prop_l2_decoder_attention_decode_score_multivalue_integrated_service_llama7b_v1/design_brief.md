# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1`
- `title`: `Llama7B multivalue integrated service probe`

## Problem
The merged exact shared-score multivalue cluster equivalence result proves the
arithmetic contract in isolation, but it does not expose shared-result blocking,
router arbitration, bank conflicts, or occupancy behavior once the integrated
on-chip value service is active.

## Hypothesis
A bounded integrated-service matrix through `cluster_count=32` can preserve the
exact Python/baseline/integrated hash contract while surfacing the first
service-level penalties that matter before later NoC or value-memory
composition work.

## Evaluation Scope
- direct comparison set:
  - merged exact shared-score multivalue cluster equivalence evidence
  - fixed-resource scaling `c1/c2/c4/c8/c16/c32` at `p128/b4/q4/rl2/round_robin`
  - scaled-resource `p256` points at `c8/b8`, `c16/b16`, and `c32/b32` with
    round-robin and locality variants
  - one queue-depth stress case and one read-latency stress case at `c32`
- evaluation mode:
  - `frontier_detail` probe/evidence only
- excluded first-stage claims:
  - no physical PPA
  - no SRAM macro timing closure
  - no HBM closure
  - no total-token energy claim
- output discipline:
  - compact repo-portable JSON/Markdown only, with deduplicated shared artifact identities and a pretty-printed JSON gate of `<=100000` bytes / `<=2500` lines
  - no full stdout traces
  - no intermediate tensors
  - identify the largest nominal round-robin case only as a representative
    `selected_scale_point`, never as an architectural or performance best

## Knowledge Inputs
- `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_cluster_equivalence__l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1.json`
- `npu/eval/probe_attention_decode_score_multivalue_integrated_service.py`
- `control_plane/control_plane/services/l2_task_generator.py`

## Candidate Direction
Record the integrated shared-score service evidence as the next merged service
closure input for later NoC/value-memory composition, while keeping physical
and HBM claims explicitly out of scope.

## Direction Gate
- status: ready_after_proposal_merge
- note: The dependency item is already merged/materialized. Dispatch only after
  the proposal implementation itself is merged onto `origin/master`.

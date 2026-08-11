# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_score32_noc_phase2_schedule_v1`
- `candidate_id`: `l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1`

## Evaluations Consumed
- Pending remote execution from the exact finalized source commit.

## Baseline Comparison
- Source traffic quantities: checked-in score32 exact-reduction recost artifact.
- Physical anchors: checked-in measured L1 attention endpoint costs.
- Replaced abstraction: the prior one-flow NoC scalar.

## Result
- Pending. No architectural promotion or rerank is permitted before the result
  artifact is merged and its full-workload assertions pass.
- The unrun v1 item is superseded because it interpreted compute-wrapper cycles
  directly as NoC cycles and therefore represented a saturation stress trace,
  not a physically timed producer-coupled schedule.

## Failures and Caveats
- HBM/DRAM timing and controller behavior remain abstract.
- SRAM floorplanning and shared-home placement remain unmeasured.
- Root-finalizer compute and source descriptor/control storage remain uncosted.

## Recommendation
- Run the immutable full-workload item remotely, then decide whether the routed
  evidence is sufficient for score32 reranking or requires an SRAM-placement
  adapter first.

# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1`
- `title`: `Llama7B multivalue integrated service probe`

## Why This Gate Is Required
The exact shared-score multivalue equivalence result is necessary but not
sufficient for later composition work. This gate proves that the integrated
shared-result/value-service path still preserves exact hashes and protocol/count
gates while exposing the service contention profile across the bounded matrix.

## Checks
- metric: exact gates
  - threshold: every case keeps Python/baseline/integrated hash, protocol, and count gates green
- metric: service evidence
  - threshold: every case reports completion cycle, service penalty cycle, shared-result arbitration/blocking, router/service contention, and occupancy maxima
- metric: exclusions
  - threshold: the evidence explicitly lists physical PPA, SRAM macro timing, HBM, and total-token energy as excluded claims
- metric: compactness
  - threshold: outputs remain repo-portable JSON/Markdown without full stdout or intermediate tensors
- metric: selection semantics
  - threshold: the largest nominal round-robin coverage point is reported only
    as `selected_scale_point`, with no architectural-best or performance-best claim

## Local Command
- command: `python3 npu/eval/probe_attention_decode_score_multivalue_integrated_service.py --proposal-id prop_l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1 --proposal-path docs/proposals/prop_l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1/proposal.json --depends-on-item-id l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1 --out /tmp/decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1.json --out-md /tmp/decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1.md`

## Result
- status: ready_after_proposal_merge
- note: the dependency item is already merged/materialized; only the proposal implementation merge remains before dispatch.

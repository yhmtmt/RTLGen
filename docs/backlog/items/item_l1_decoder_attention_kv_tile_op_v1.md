# Decoder attention/KV tile RTLGen op

- item_id: `item_l1_decoder_attention_kv_tile_op_v1`
- layer: `layer1`
- kind: `circuit`
- status: `promoted_to_proposal_dependency`
- priority: `high`
- owner: `developer_agent`
- created_utc: `2026-05-12T02:30:00Z`
- updated_utc: `2026-05-12T02:30:00Z`
- proposal_id: `prop_l1_decoder_attention_kv_tile_stream_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_attention_kv_tile_stream_v1/proposal.json`
- triggered_by_proposal: `prop_l2_decoder_attention_kv_memory_v1`
- triggering_evidence: `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_memory_large_context_v2.json`

## Problem
- The current long-context decoder model says attention/KV service dominates, but RTLGen has no standalone attention/KV tile operation to measure.
- Dispatching a Layer 1 measurement before adding that operation would only test missing-source failure handling, not architecture cost.

## Candidate Idea
- Add a bounded `attention_kv_tile` RTLGen operation that models the QK/KV read-side tile datapath used by single-token decode.
- Keep the first operation intentionally narrow: dot-product lanes, KV width/precision parameters, a simple streaming valid/ready interface, and observable cycle/data counters for perf-sim equivalence.

## Why It Might Matter
- Converts the current analytical QK/KV bottleneck into measured timing, area, and power.
- Provides a reusable primitive for later producer+attention+ranker composition.

## Required Work
- l1 change? `yes`: new RTLGen operation, configs, wrapper/sweep, and local tests.
- l2 change? `no` for the source-enabling step.
- mapper change? `no` for the source-enabling step.
- quality gate required? `yes`: generated Verilog smoke, C++/unit tests, and perf-sim/RTL equivalence on cycle/data counters.

## Evaluation Sketch
- Local: build `rtlgen`, generate at least one `attention_kv_tile` Verilog wrapper, run unit tests.
- Remote: after merge, dispatch `l1_decoder_attention_kv_tile_smoke_v1`.

## Inputs / Sources
- `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_memory__l2_decoder_attention_kv_memory_large_context_v2.json`
- `npu/eval/estimate_llm_decoder_attention_kv_memory.py`
- `src/rtlgen/rtl_operations.cpp`
- `src/rtlgen/config.cpp`
- `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_memory_large_context_v2.json`

## Open Questions
- Whether the first tile should include value-mix accumulation or only QK/KV read service.
- Whether SRAM/NoC bandwidth should be represented as explicit ready throttling or as separate perf counters in the first RTL block.

## Promotion Rule
- Promote to remote measurement after the new op, configs, and local equivalence tests are merged to `master`.

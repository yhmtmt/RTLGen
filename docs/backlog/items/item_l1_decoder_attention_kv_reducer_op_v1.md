# Decoder attention/KV reducer RTLGen op

- item_id: `item_l1_decoder_attention_kv_reducer_op_v1`
- layer: `layer1`
- kind: `circuit`
- status: `implemented_pending_review`
- priority: `high`
- owner: `developer_agent`
- created_utc: `2026-05-28T00:00:00Z`
- updated_utc: `2026-05-28T00:00:00Z`
- proposal_id: `prop_l1_decoder_attention_kv_reducer_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_attention_kv_reducer_v1/proposal.json`
- triggered_by_proposal: `prop_l2_decoder_attention_kv_clustered_schedule_overhead_v1`

## Problem
- The clustered Llama7B attention schedule now has explicit command and cross-tile reduction overhead knobs, but the reducer cost is still analytical.
- The next measured anchor needs a standalone reducer block before the L2 schedule model treats the command/reducer overhead as calibrated.

## Candidate Idea
- Add a bounded `attention_kv_reducer` RTLGen operation that accepts value fragments and two statistic fields through a ready/valid interface.
- Keep the first block exact and deterministic: fixed-width lane sums, fixed-width statistic sums, and observable counters for perf-sim/RTL equivalence.

## Required Work
- l1 change? `yes`: new RTLGen operation, example configs, wrapper/sweep, and local tests.
- l2 change? `no` for this source-enabling step.
- mapper change? `no`.
- quality gate required? `yes`: generated Verilog smoke, wrapper smoke, dry-run sweep, and deterministic RTL equivalence.

## Evaluation Sketch
- Local: build `rtlgen`, generate the reducer, run the Verilog testbench, and dry-run the smoke/frontier sweep paths.
- Remote: after merge, dispatch `l1_decoder_attention_kv_reducer_smoke_v1`, then `l1_decoder_attention_kv_reducer_frontier_v1` if smoke passes.

## Promotion Rule
- Promote after remote L1 PPA records accepted metrics for the reducer geometry needed by the clustered attention schedule model.

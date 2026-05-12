# Implementation Summary

- proposal_id: `prop_l1_decoder_attention_kv_tile_stream_v1`
- title: `Decoder attention/KV tile stream measured RTL anchor`

## Prepared Jobs

- `l1_decoder_attention_kv_tile_smoke_v1`
- `l1_decoder_attention_kv_tile_frontier_v1`

## Source Work Required Before Dispatch

- Add an `attention_kv_tile` operation to RTLGen config parsing and Verilog generation.
- Add local tests that compare a simple perf model against generated RTL-visible cycle and byte counters.
- Add the config files listed in `proposal.json`.
- Add the sweep files listed in `proposal.json`.

## Dispatch Status

The evaluation jobs are intentionally prepared but not dispatchable yet. They
must remain blocked until the implementing source commit is merged and can be
attached to the control-plane `source_requirement.required_sha`.

# Implementation Summary

- proposal_id: `prop_l1_decoder_attention_kv_reducer_v1`
- title: `Decoder attention/KV cross-tile reducer measured RTL anchor`

## Prepared Jobs

- `l1_decoder_attention_kv_reducer_smoke_v1`
- `l1_decoder_attention_kv_reducer_frontier_v1`

## Source Work Required Before Dispatch

- Add an `attention_kv_reducer` operation to RTLGen config parsing and Verilog generation.
- Add local tests that compare a deterministic reduction rule against generated RTL-visible values and counters.
- Add the config files listed in `proposal.json`.
- Add the sweep files listed in `proposal.json`.

## Dispatch Status

The evaluation jobs are intentionally prepared but not dispatchable yet. They
must remain blocked until the implementing source commit is merged and can be
attached to the control-plane `source_requirement.required_sha`.

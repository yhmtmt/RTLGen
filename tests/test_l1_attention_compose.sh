#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 "$ROOT/scripts/generate_design.py" \
  "$ROOT/examples/config_attention_kv_tile_reducer_folded.json" \
  nangate45 \
  --force_gen True

iverilog -g2012 \
  -s attention_kv_tile_reducer_hd8_kv4_tl4_b16_p4_ppc2_l4_v8_s12_a16_wrapper \
  -t null \
  /orfs/flow/designs/src/attention_kv_tile_reducer_hd8_kv4_tl4_b16_p4_ppc2_l4_v8_s12_a16_wrapper/*.v

python3 "$ROOT/scripts/run_sweep.py" \
  --configs "$ROOT/examples/config_attention_kv_tile_reducer_folded.json" \
  --platform nangate45 \
  --sweep "$ROOT/runs/campaigns/activations/attention_kv_tile_reducer_folded/sweeps/nangate45_macro_frontier.json" \
  --out_root "$TMP/runs" \
  --dry_run

python3 "$ROOT/scripts/generate_design.py" \
  "$ROOT/examples/config_l1_memory_noc_primitive.json" \
  nangate45 \
  --force_gen True

iverilog -g2012 \
  -s l1_noc_fifo_w64_d8_wrapper \
  -t null \
  /orfs/flow/designs/src/l1_noc_fifo_w64_d8_wrapper/*.v

python3 "$ROOT/scripts/generate_design.py" \
  "$ROOT/runs/designs/noc/l1_noc_router_p4_w128_wrapper/config_l1_noc_router_p4_w128.json" \
  nangate45 \
  --force_gen True

iverilog -g2012 \
  -s l1_noc_router_p4_w128_wrapper \
  -t null \
  /orfs/flow/designs/src/l1_noc_router_p4_w128_wrapper/*.v

python3 "$ROOT/scripts/run_sweep.py" \
  --configs "$ROOT/runs/designs/noc/l1_noc_router_p4_w128_wrapper/config_l1_noc_router_p4_w128.json" \
  --platform nangate45 \
  --sweep "$ROOT/runs/campaigns/noc/l1_memory_noc_primitives/sweeps/nangate45_macro_frontier.json" \
  --out_root "$TMP/runs" \
  --dry_run

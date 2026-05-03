#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

cp "$ROOT/examples/config_score_tie_rank.json" "$TMP/config.json"

pushd "$TMP" >/dev/null
"$ROOT/build/rtlgen" config.json

grep -q "module score_tie_rank_r4_s16_l16" score_tie_rank_r4_s16_l16.v
grep -q "score_i == best_score" score_tie_rank_r4_s16_l16.v

iverilog -g2012 -s score_tie_rank_tb -o sim score_tie_rank_r4_s16_l16.v "$ROOT/tests/score_tie_rank_tb.v"
vvp sim
popd >/dev/null

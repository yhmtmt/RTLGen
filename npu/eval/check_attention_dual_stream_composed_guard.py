#!/usr/bin/env python3
"""Check generated composed dual-stream attention RTL before PPA."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", required=True)
    args = parser.parse_args()

    design_dir = Path(args.design_dir)
    manifest_path = design_dir / "verilog" / "attention_dual_stream_composed_manifest.json"
    top_path = design_dir / "verilog" / "top.v"
    if not manifest_path.exists():
        raise SystemExit(f"missing manifest: {manifest_path}")
    if not top_path.exists():
        raise SystemExit(f"missing generated RTL: {top_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    top_text = top_path.read_text(encoding="utf-8")
    top_name = str(manifest["top_name"])
    total_macs = int(manifest["total_macs"])
    streams = int(manifest["streams"])
    equivalence_hash = bool(manifest.get("equivalence_hash", False))
    softmax_impl = str(manifest.get("softmax_impl", "exact_div"))
    softmax_pipeline_stages = int(manifest.get("softmax_pipeline_stages", 0))
    softmax_internal_pipeline_stages = int(manifest.get("softmax_internal_pipeline_stages", 0))
    softmax_latency_stages = int(manifest.get("softmax_latency_stages", 1))
    value_alignment_delay_stages = int(manifest.get("value_alignment_delay_stages", 0))
    if streams != 2:
        raise SystemExit(f"expected 2 streams, found {streams}")
    if f"module {top_name} " not in top_text:
        raise SystemExit(f"missing top module {top_name}")

    mac_instances = len(re.findall(r"\bu_mac_\d{4}\s*\(", top_text))
    if mac_instances != total_macs:
        raise SystemExit(f"MAC instance count mismatch: expected {total_macs}, found {mac_instances}")
    value_instances = len(re.findall(r"\bu_value_stream_\d+\s*\(", top_text))
    if value_instances != 2:
        raise SystemExit(f"value stream count mismatch: expected 2, found {value_instances}")
    if len(re.findall(r"\bu_softmax\s*\(", top_text)) != 1:
        raise SystemExit("expected exactly one shared softmax instance")
    if "stream_buf_0" not in top_text or "stream_buf_1" not in top_text:
        raise SystemExit("missing dual stream buffer registers")
    if softmax_impl not in {"exact_div", "pow2sum", "recip_lut"}:
        raise SystemExit(f"unsupported softmax_impl={softmax_impl}")
    if softmax_latency_stages != 1 + softmax_internal_pipeline_stages:
        raise SystemExit("softmax latency must equal output register latency plus internal pipeline stages")
    if softmax_pipeline_stages:
        if softmax_pipeline_stages != 1:
            raise SystemExit(f"unsupported softmax_pipeline_stages={softmax_pipeline_stages}")
        if value_alignment_delay_stages != softmax_pipeline_stages + softmax_latency_stages:
            raise SystemExit(
                "value alignment delay must match the softmax input stage plus softmax module latency"
            )
        required_tokens = [
            "softmax_scores_pipe_0",
            ".scores(softmax_scores_pipe_0)",
        ]
        last_stage = value_alignment_delay_stages - 1
        required_tokens.extend(
            [
                f"stream_buf_0_pipe_{last_stage}",
                f"stream_buf_1_pipe_{last_stage}",
                f".stream_data(stream_buf_0_pipe_{last_stage})",
                f".stream_data(stream_buf_1_pipe_{last_stage})",
                f".score_mix(score_mix_0_pipe_{last_stage})",
                f".score_mix(score_mix_1_pipe_{last_stage})",
            ]
        )
        for token in required_tokens:
            if token not in top_text:
                raise SystemExit(f"missing softmax pipeline alignment token: {token}")
    else:
        if value_alignment_delay_stages != 0:
            raise SystemExit("value alignment delay must be 0 when softmax pipeline is disabled")
        if "softmax_scores_pipe_0" in top_text:
            raise SystemExit("softmax pipeline register present when disabled")
    if softmax_internal_pipeline_stages:
        for token in ("exp_weight_q", "sum_weight_q"):
            if token not in top_text:
                raise SystemExit(f"missing split softmax pipeline token: {token}")
    if softmax_impl == "pow2sum":
        for token in ("denom_shift", "lane_scaled"):
            if token not in top_text:
                raise SystemExit(f"missing replacement softmax token: {token}")
        if "/ sum_weight" in top_text or "/ sum_weight_q" in top_text:
            raise SystemExit("pow2sum replacement must not contain a sum_weight divider")
    if softmax_impl == "recip_lut":
        for token in ("function [RECIPROCAL_WIDTH-1:0] reciprocal_lut", "reciprocal_q", "lane_scaled"):
            if token not in top_text:
                raise SystemExit(f"missing reciprocal-LUT softmax token: {token}")
        if "denom_shift" in top_text:
            raise SystemExit("reciprocal-LUT replacement must not contain pow2 denominator shift logic")
        if "/ sum_weight" in top_text or "/ sum_weight_q" in top_text:
            raise SystemExit("reciprocal-LUT replacement must not contain a sum_weight divider")
    if equivalence_hash:
        if "result_hash <=" not in top_text:
            raise SystemExit("result_hash is not updated")
        fold_match = re.search(r"\bwire\s+\[31:0\]\s+compute_fold\s*=\s*(.*?);", top_text, flags=re.DOTALL)
        if fold_match is None:
            raise SystemExit("missing compute_fold assignment")
        fold_expr = fold_match.group(1)
        missing_macs = [f"mac_r_{idx:04d}" for idx in range(total_macs) if f"mac_r_{idx:04d}" not in fold_expr]
        if missing_macs:
            raise SystemExit(f"MAC outputs are not visible in compute fold: {missing_macs[:8]}")
        for token in ("softmax_weight_hash", "value_hash_0", "value_hash_1", "value_accum_0", "value_accum_1"):
            if token not in top_text:
                raise SystemExit(f"missing result visibility token: {token}")
    else:
        forbidden_tokens = ("result_hash", "softmax_weight_hash", "value_hash_0", "value_hash_1", "compute_fold")
        for token in forbidden_tokens:
            if token in top_text:
                raise SystemExit(f"equivalence-only hash token present in PPA mode: {token}")
        for token in ("softmax_weights_out", "value_accum_0_out", "value_accum_1_out", "score_mix_0_out", "score_mix_1_out"):
            if token not in top_text:
                raise SystemExit(f"missing PPA datapath output token: {token}")
        missing_macs = [f"mac_r_{idx:04d}" for idx in range(total_macs) if f"mac_r_{idx:04d}" not in top_text]
        if missing_macs:
            raise SystemExit(f"MAC outputs are not visible in PPA datapath: {missing_macs[:8]}")

    print(
        json.dumps(
            {
                "ok": True,
                "design_dir": str(design_dir),
                "top_name": top_name,
                "streams": streams,
                "total_macs": total_macs,
                "value_streams": value_instances,
                "equivalence_hash": equivalence_hash,
                "softmax_impl": softmax_impl,
                "softmax_pipeline_stages": softmax_pipeline_stages,
                "softmax_internal_pipeline_stages": softmax_internal_pipeline_stages,
                "softmax_latency_stages": softmax_latency_stages,
                "value_alignment_delay_stages": value_alignment_delay_stages,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

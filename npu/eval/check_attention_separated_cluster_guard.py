#!/usr/bin/env python3
"""Guard semantic separated-attention RTL before physical evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", required=True)
    args = parser.parse_args(argv)
    design_dir = Path(args.design_dir)
    config_path = design_dir / "config.json"
    generated_config_path = design_dir / "verilog" / "config.json"
    manifest_path = design_dir / "verilog" / "attention_separated_cluster_manifest.json"
    top_path = design_dir / "verilog" / "top.v"
    for path in (config_path, generated_config_path, manifest_path, top_path):
        if not path.exists():
            raise SystemExit(f"missing separated-attention artifact: {path}")

    config = _load(config_path)
    if config != _load(generated_config_path):
        raise SystemExit("generated config does not match source config")
    manifest = _load(manifest_path)
    cluster = config.get("attention_separated_cluster")
    if not isinstance(cluster, dict):
        raise SystemExit("config must contain attention_separated_cluster object")
    producer_count = int(cluster.get("producer_count", 0))
    consumer_count = int(cluster.get("consumer_count", 0))
    if manifest.get("semantic_profile") != "q8_k8_v8_a32_s32_w16_exp_lut_div_b20":
        raise SystemExit("unexpected separated-attention semantic profile")
    if int(manifest.get("producer_count", 0)) != producer_count:
        raise SystemExit("manifest producer_count does not match config")
    if int(manifest.get("consumer_count", 0)) != consumer_count:
        raise SystemExit("manifest consumer_count does not match config")
    if manifest.get("producer_to_consumer_ratio") != f"{producer_count}:{consumer_count}":
        raise SystemExit("manifest producer-to-consumer ratio does not match config")
    if int(manifest.get("producer_payload_width", 0)) != 784:
        raise SystemExit("producer payload must contain command id, full score row, and full V matrix")
    if int(manifest.get("consumer_result_width", 0)) != 720:
        raise SystemExit("consumer result must contain command id and exact score, weight, and V outputs")

    text = top_path.read_text(encoding="utf-8", errors="replace")
    top_name = str(config.get("top_name") or "")
    if not re.search(rf"^\s*module\s+{re.escape(top_name)}\b", text, re.MULTILINE):
        raise SystemExit(f"generated RTL does not define top module {top_name}")
    required = (
        "payload_score_row",
        "payload_value_matrix",
        "result_score_row",
        "result_weights",
        "result_value",
        "dispatch_fire",
        "result_fire",
        "consumer_enable",
        "score_accum <<< 20",
        "delta_score + 32'd524288",
        "32'd2048",
        "17'd65535",
        "weight_numer / sum_exp",
        "$signed(value_lane) * $signed({1'b0, weight_lane[row_idx]})",
    )
    for token in required:
        if token not in text:
            raise SystemExit(f"separated-attention RTL missing semantic token: {token}")
    forbidden = ("result_hash", "equivalence_hash", "PRODUCER_INDEX *")
    for token in forbidden:
        if token in text:
            raise SystemExit(f"separated-attention RTL contains forbidden proxy token: {token}")
    for index in range(producer_count):
        if f"u_producer_{index}" not in text:
            raise SystemExit(f"missing producer instance {index}")
    for index in range(consumer_count):
        if f"u_consumer_{index}" not in text:
            raise SystemExit(f"missing consumer instance {index}")

    print(f"OK: separated-attention guard passed for {design_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

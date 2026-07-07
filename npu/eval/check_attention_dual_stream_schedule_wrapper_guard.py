#!/usr/bin/env python3
"""Check generated dual-stream schedule wrapper RTL before PPA."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--design-dir", required=True)
    args = ap.parse_args(argv)

    design_dir = Path(args.design_dir)
    config_path = design_dir / "config.json"
    generated_config_path = design_dir / "verilog" / "config.json"
    manifest_path = design_dir / "verilog" / "attention_dual_stream_schedule_wrapper_manifest.json"
    top_path = design_dir / "verilog" / "top.v"
    for path in (config_path, generated_config_path, manifest_path, top_path):
        if not path.exists():
            raise SystemExit(f"missing generated schedule-wrapper artifact: {path}")

    cfg = _load_json(config_path)
    gen_cfg = _load_json(generated_config_path)
    if cfg != gen_cfg:
        raise SystemExit("generated config does not match source config")
    wrapper_cfg = cfg.get("attention_dual_stream_schedule_wrapper")
    if not isinstance(wrapper_cfg, dict):
        raise SystemExit("config must contain attention_dual_stream_schedule_wrapper object")

    manifest = _load_json(manifest_path)
    top_name = str(manifest.get("top_name", ""))
    clusters = int(manifest.get("clusters", 0))
    datapath_macs = int(manifest.get("datapath_total_macs_per_cluster", 0))
    total_macs = int(manifest.get("total_macs", 0))
    if not top_name:
        raise SystemExit("manifest top_name must not be empty")
    if clusters < 1 or clusters > 8:
        raise SystemExit(f"unexpected schedule-wrapper cluster count: {clusters}")
    if datapath_macs <= 0 or total_macs != datapath_macs * clusters:
        raise SystemExit("schedule-wrapper total_macs must equal datapath_macs * clusters")

    text = top_path.read_text(encoding="utf-8", errors="replace")
    if not re.search(rf"^\s*module\s+{re.escape(top_name)}\b", text, re.MULTILINE):
        raise SystemExit(f"generated RTL does not define top module {top_name}")
    required_tokens = [
        "u_dispatch",
        "command_valid",
        "command_ready",
        "local_issue_valid",
        "cluster_done_valid",
        "external_cluster_ready",
        "datapath_result_fold",
        "result_fold <=",
        "attention_softmax_weight_score32_w16_exp_lut_div_b20_like",
        "int8_mac_s8s8_acc32",
    ]
    for token in required_tokens:
        if token not in text:
            raise SystemExit(f"schedule-wrapper RTL missing expected token: {token}")
    for idx in range(clusters):
        for token in (
            f"u_cluster_datapath_{idx}",
            f"cluster_{idx}_start",
            f"cluster_{idx}_complete",
            f"cluster_{idx}_weights",
            f"cluster_{idx}_value0",
            f"cluster_{idx}_score0",
        ):
            if token not in text:
                raise SystemExit(f"schedule-wrapper RTL missing cluster token: {token}")

    datapath_manifest = manifest.get("datapath_manifest")
    if not isinstance(datapath_manifest, dict):
        raise SystemExit("manifest must include datapath_manifest object")
    if datapath_manifest.get("semantic_profile") != "score32_exp_lut_div":
        raise SystemExit("schedule-wrapper datapath must preserve score32_exp_lut_div semantic profile")
    if datapath_manifest.get("softmax_impl") != "exp_lut_div":
        raise SystemExit("schedule-wrapper datapath must preserve exp_lut_div softmax implementation")

    print(f"OK: attention dual-stream schedule-wrapper guard passed for {design_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

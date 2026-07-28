#!/usr/bin/env python3
"""Guard the generated exact GQA8 cluster SRAM service artifacts against drift."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_cluster_sram_service_gqa8 import generate
from npu.sim.perf.attention_score32_exact_cluster_sram_service_gqa8 import (
    CONFIG_KEY,
    MANIFEST_NAME,
    build_default_config,
    cluster_sram_service_manifest,
)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_selected_config(*, design_dir: Path, selected: Path | None) -> Path:
    config_path = selected or (design_dir / "config.json")
    config_path = config_path.resolve()
    if not config_path.exists():
        raise SystemExit(f"missing config: {config_path}")
    try:
        relative_path = config_path.relative_to(design_dir)
    except ValueError as exc:
        raise SystemExit(f"selected config must live under design-dir: {config_path}") from exc
    if len(relative_path.parts) != 1:
        raise SystemExit(f"selected config must be a direct child of design-dir, got: {relative_path.as_posix()}")
    return config_path


def _require(mapping: dict[str, object], key: str, expected: object, label: str) -> None:
    if mapping.get(key) != expected:
        raise SystemExit(f"{label} {key} must be {expected}")


def _require_token(text: str, token: str, label: str) -> None:
    if token not in text:
        raise SystemExit(f"{label} missing semantic token: {token}")


def _forbid_token(text: str, token: str, label: str) -> None:
    if token in text:
        raise SystemExit(f"{label} contains forbidden token: {token}")


def _compare_current_generation(*, config: dict[str, object], rtl_dir: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="score32_exact_cluster_sram_service_gqa8_guard_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        generate(config, temp_dir)
        for relative_name in ("top.v", "config.json", MANIFEST_NAME):
            generated_text = (temp_dir / relative_name).read_text(encoding="utf-8")
            current_text = (rtl_dir / relative_name).read_text(encoding="utf-8")
            if generated_text != current_text:
                raise SystemExit(f"generated RTL artifacts do not match current generator output: {relative_name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    design_dir = args.design_dir.resolve()
    config_path = _resolve_selected_config(design_dir=design_dir, selected=args.config)
    rtl_dir = design_dir / "verilog"
    generated_config_path = rtl_dir / "config.json"
    manifest_path = rtl_dir / MANIFEST_NAME
    top_path = rtl_dir / "top.v"
    for path in (config_path, generated_config_path, manifest_path, top_path):
        if not path.is_file():
            raise SystemExit(f"missing exact cluster SRAM service artifact: {path}")

    config = _load_json(config_path)
    generated_config = _load_json(generated_config_path)
    if config != generated_config:
        raise SystemExit("generated config does not match source config")

    body = config.get(CONFIG_KEY)
    top_name = str(config.get("top_name") or "").strip()
    if not top_name or not isinstance(body, dict):
        raise SystemExit(f"config must contain top_name and {CONFIG_KEY}")
    producers = int(body.get("producers", 0))
    if producers not in {53, 54}:
        raise SystemExit("producers must remain exactly 53 or 54")

    probe_defaults = config.get("probe_defaults")
    if not isinstance(probe_defaults, dict):
        raise SystemExit("config must include probe_defaults")
    _require(probe_defaults, "head_bases", [0, 8, 16, 24], "probe_defaults")
    _require(probe_defaults, "waves", 8, "probe_defaults")
    _require(probe_defaults, "seed", 73, "probe_defaults")

    manifest = _load_json(manifest_path)
    expected_manifest = {
        "version": 1,
        "generator": "npu/rtlgen/gen_attention_score32_exact_cluster_sram_service_gqa8.py",
        "top_name": top_name,
        "semantic_profile": "attention_score32_exact_cluster_sram_service_gqa8_v1",
        "producers": producers,
        "value_memory_lanes": producers * 2,
        "architecture_metadata": {
            "topology": "mesh2d",
            "scheduler_policy": "locality_aware",
            "reduction_strategy": "cluster_tree",
            "endpoint_policy": "per_cluster_local",
            "schedule_policy": "prefetch_overlap",
            "bank_arbiter_policy": "locality_first",
            "virtual_channels": 4,
        },
        "service_model": cluster_sram_service_manifest(producers=producers),
        "equivalence_hash": False,
        "rtl_files": ["top.v"],
        "checked_in_probe_defaults": probe_defaults,
    }
    for key, expected in expected_manifest.items():
        _require(manifest, key, expected, "generated manifest")

    synth_note = str(manifest.get("synthesizability_note") or "")
    if "not SRAM-macro closed" not in synth_note:
        raise SystemExit("generated manifest synthesizability_note must disclose the non-macro-closed caveat")

    rtl = top_path.read_text(encoding="utf-8", errors="replace")
    required_tokens = (
        "reg [ROW_BITS-1:0] bank_mem [0:BANKS-1][0:1][0:ROWS_PER_BANK_PER_BUFFER-1];",
        "reg [31:0] bank_conflict_count_q;",
        "assign bank_conflict_count = bank_conflict_count_q;",
        "bank_candidate_count_r[bank] = bank_candidate_count_r[bank] + 1;",
        "if (bank_candidate_count_r[bank] > 1)",
        "bank_conflict_count_q <= bank_conflict_count_q + bank_conflict_delta_r;",
        "request_accept_count_q <= request_accept_count_q + request_accept_delta_r;",
        "response_accept_count_q <= response_accept_count_q + response_accept_delta_r;",
        "response_stall_cycles_q <= response_stall_cycles_q + response_stall_delta_r;",
        "request_stall_cycles_q <= request_stall_cycles_q + request_stall_delta_r;",
        "assign command_ready = !command_active_q && command_metadata_valid && command_resident_match;",
        "assign fill_ready = fill_target_active_q;",
    )
    for token in required_tokens:
        _require_token(rtl, token, "generated RTL")

    forbidden_tokens = (
        "if (fill_target_valid && fill_target_metadata_valid && !fill_target_ready)",
        "if (command_valid && !command_metadata_valid)",
        "if (command_valid && command_active_q)",
        "if ((|value_read_req_valid) && !command_active_q)",
    )
    for token in forbidden_tokens:
        _forbid_token(rtl, token, "generated RTL")

    _compare_current_generation(config=config, rtl_dir=rtl_dir)

    print(
        json.dumps(
            {
                "design": top_name,
                "guard": "attention_score32_exact_cluster_sram_service_gqa8_v1",
                "producers": producers,
                "default_config_top_name": build_default_config(producers=producers)["top_name"],
                "status": "ok",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

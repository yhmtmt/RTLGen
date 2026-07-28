#!/usr/bin/env python3
"""Strict generated RTL guard for the bounded local temporal exact-partial reducer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tempfile

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_local_temporal_reducer import generate
from npu.sim.perf.attention_exact_partial import (
    LOCAL_TEMPORAL_WAVES,
    PARTIAL_LINK_BITS,
    PARTIAL_PAYLOAD_BITS,
    exact_local_temporal_reducer_service_manifest,
)

_CONFIG_KEY = "attention_score32_exact_local_temporal_reducer"
_MANIFEST_NAME = "attention_score32_exact_local_temporal_reducer_manifest.json"


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


def _extract_module(rtl: str, module_name: str) -> str:
    pattern = re.compile(rf"module\s+{re.escape(module_name)}\b.*?endmodule\s*", re.DOTALL)
    match = pattern.search(rtl)
    if match is None:
        raise SystemExit(f"generated RTL does not define module {module_name}")
    return match.group(0)


def _compare_current_generation(*, config: dict[str, object], rtl_dir: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="score32_exact_local_temporal_guard_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        generate(config, temp_dir)
        for relative_name in ("top.v", "config.json", _MANIFEST_NAME):
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
    manifest_path = rtl_dir / _MANIFEST_NAME
    top_path = rtl_dir / "top.v"
    for path in (config_path, generated_config_path, manifest_path, top_path):
        if not path.is_file():
            raise SystemExit(f"missing local temporal reducer artifact: {path}")

    config = _load_json(config_path)
    generated_config = _load_json(generated_config_path)
    if config != generated_config:
        raise SystemExit("generated config does not match source config")

    top_name = str(config.get("top_name") or "").strip()
    body = config.get(_CONFIG_KEY)
    if not top_name or not isinstance(body, dict):
        raise SystemExit(f"config must contain top_name and {_CONFIG_KEY}")

    producers = int(body.get("producers", 0))
    value_slices = int(body.get("value_slices", 0))
    head_id_bits = int(body.get("head_id_bits", 0))
    persistent_waves = int(body.get("persistent_waves", 0))
    if producers not in {53, 54}:
        raise SystemExit("producers must remain exactly 53 or 54")
    if value_slices != 16:
        raise SystemExit("value_slices must remain 16")
    if head_id_bits != 5:
        raise SystemExit("head_id_bits must remain 5")
    if persistent_waves != LOCAL_TEMPORAL_WAVES:
        raise SystemExit(f"persistent_waves must remain {LOCAL_TEMPORAL_WAVES}")

    probe_defaults = config.get("probe_defaults", {})
    if not isinstance(probe_defaults, dict):
        probe_defaults = {}
    service_model = exact_local_temporal_reducer_service_manifest(
        producers=producers,
        waves=persistent_waves,
        heads=int(probe_defaults.get("heads", 1)),
    )
    manifest = _load_json(manifest_path)
    expected_manifest = {
        "top_name": top_name,
        "generator": "npu/rtlgen/gen_attention_score32_exact_local_temporal_reducer.py",
        "semantic_profile": "score32_exact_local_temporal_reducer_v1",
        "producers": producers,
        "value_slices": 16,
        "head_id_bits": 5,
        "persistent_waves": 8,
        "result_interface": "local_exact_partial_producer_streams_to_single_aggregate_after_8_waves",
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "equivalence_hash": False,
        "command_schedule_contract": "in_order_leaf_streams_grouped_by_exact_8_wave_temporal_windows",
        "head_mapping_contract": "explicit_head_id_no_tile_or_wave_inference",
        "comparison_baseline_contract": service_model["comparison_baseline_contract"],
        "comparison_cycle_origin": service_model["comparison_cycle_origin"],
        "diagnostic_only_baseline": service_model["diagnostic_only_baseline"],
        "remaining_abstractions": service_model["remaining_abstractions"],
        "service_model": service_model,
    }
    for key, expected in expected_manifest.items():
        _require(manifest, key, expected, "generated manifest")
    if isinstance(config.get("probe_defaults"), dict):
        _require(manifest, "checked_in_probe_defaults", config["probe_defaults"], "generated manifest")

    submodule_manifests = manifest.get("submodule_manifests")
    if not isinstance(submodule_manifests, dict):
        raise SystemExit("generated manifest must contain submodule_manifests")
    local_manifest = submodule_manifests.get("local_reducer")
    temporal_manifest = submodule_manifests.get("temporal_merge")
    if not isinstance(local_manifest, dict) or not isinstance(temporal_manifest, dict):
        raise SystemExit("generated manifest must contain local_reducer and temporal_merge submodule manifests")
    _require(local_manifest, "generator", "npu/rtlgen/gen_attention_score32_exact_local_reducer.py", "local reducer submodule manifest")
    _require(local_manifest, "producers", producers, "local reducer submodule manifest")
    _require(local_manifest, "partial_payload_bits_per_beat", 328, "local reducer submodule manifest")
    _require(temporal_manifest, "generator", "npu/rtlgen/gen_attention_score32_online_state_merge.py", "temporal merge submodule manifest")
    _require(temporal_manifest, "result_interface", "ready_valid_exact_partial_slice_stream", "temporal merge submodule manifest")

    links = config.get("report_links")
    if not isinstance(links, dict):
        raise SystemExit("config must include report_links for evaluator artifact linkage")
    _require(links, "proposal_id", "prop_l1_decoder_attention_score32_local_temporal_reducer_v1", "report_links")

    rtl = top_path.read_text(encoding="utf-8", errors="replace")
    local_top = f"{top_name}__local_reducer"
    temporal_top = f"{top_name}__temporal_merge"
    top_module = _extract_module(rtl, top_name)
    _extract_module(rtl, local_top)
    _extract_module(rtl, temporal_top)

    if len(re.findall(rf"\bmodule\s+{re.escape(local_top)}\b", rtl)) != 1:
        raise SystemExit("generated RTL must contain exactly one local reducer module definition")
    if len(re.findall(rf"\bmodule\s+{re.escape(temporal_top)}\b", rtl)) != 1:
        raise SystemExit("generated RTL must contain exactly one temporal merge module definition")
    if top_module.count(f"{local_top} u_local_reducer") != 1:
        raise SystemExit("generated RTL must instantiate the local reducer exactly once")
    if top_module.count(f"{temporal_top} u_temporal_merge") != 1:
        raise SystemExit("generated RTL must instantiate the temporal merge exactly once")

    for token in (
        "localparam integer PERSISTENT_WAVES = 8;",
        "assign local_root_ready_w =",
        "phase_q <= PHASE_EMIT;",
        "phase_q <= PHASE_COLLECT;",
        "if (wave_count_q == (PERSISTENT_WAVES - 1)) begin",
        "state_command_id_q[local_root_slice_w] <= local_root_command_id_w;",
        "state_command_id_q[temporal_out_slice_w] <= temporal_out_command_id_w;",
        "completed_command_count_q <= completed_command_count_q + 1'b1;",
        ".right_command_id(state_command_id_q[local_root_slice_w])",
        "output_stall_cycles_q <= output_stall_cycles_q + 1'b1;",
    ):
        _require_token(top_module, token, "generated RTL")

    for forbidden in ("equivalence_hash", "finalizer", "llama_throughput", "ppa_claim"):
        if forbidden in rtl:
            raise SystemExit(f"functional datapath must not contain {forbidden} tokens")

    _compare_current_generation(config=config, rtl_dir=rtl_dir)

    print(
        json.dumps(
            {
                "design": top_name,
                "guard": "attention_score32_exact_local_temporal_reducer_v1",
                "producers": producers,
                "persistent_waves": persistent_waves,
                "status": "ok",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

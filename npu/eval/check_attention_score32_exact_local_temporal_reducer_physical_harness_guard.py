#!/usr/bin/env python3
"""Strict generated RTL guard for the local temporal reducer physical harness."""

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

from npu.rtlgen.gen_attention_score32_exact_local_temporal_reducer_physical_harness import generate

_CONFIG_KEY = "attention_score32_exact_local_temporal_reducer_physical_harness"
_MANIFEST_NAME = "attention_score32_exact_local_temporal_reducer_physical_harness_manifest.json"
_PROPOSAL_ID = "prop_l1_decoder_attention_score32_local_temporal_reducer_v1"


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
    with tempfile.TemporaryDirectory(prefix="score32_exact_local_temporal_physical_guard_") as temp_dir_name:
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
            raise SystemExit(f"missing physical harness artifact: {path}")

    config = _load_json(config_path)
    generated_config = _load_json(generated_config_path)
    if config != generated_config:
        raise SystemExit("generated config does not match source config")

    top_name = str(config.get("top_name") or "").strip()
    body = config.get(_CONFIG_KEY)
    if not top_name or not isinstance(body, dict):
        raise SystemExit(f"config must contain top_name and {_CONFIG_KEY}")

    producers = int(body.get("producers", 0))
    mode = str(body.get("mode", "")).strip()
    waves = int(body.get("waves", 0))
    if producers not in {53, 54}:
        raise SystemExit("producers must remain exactly 53 or 54")
    if mode not in {"reducer", "source_only"}:
        raise SystemExit("mode must remain reducer or source_only")
    if waves != 8:
        raise SystemExit("waves must remain 8")

    manifest = _load_json(manifest_path)
    expected_manifest = {
        "generator": "npu/rtlgen/gen_attention_score32_exact_local_temporal_reducer_physical_harness.py",
        "top_name": top_name,
        "semantic_profile": "score32_exact_local_temporal_reducer_physical_harness_v1",
        "producers": producers,
        "mode": mode,
        "waves": 8,
        "value_slices": 16,
        "head_id_bits": 5,
        "result_interface": "narrow_io_observable_structural_local_temporal_harness",
        "equivalence_hash": False,
        "top_pin_bits": 776,
        "source_traffic_contract": "shared_state_atomic_batch_stable_ready_valid",
        "source_state_contract": "single_shared_held_lfsr_and_beat_counter",
        "source_batch_contract": "all_leaf_valids_atomic_advance_on_all_leaf_handshakes",
        "per_leaf_payload_state": False,
        "observable_contract": "done_plus_final_command_head_max_sum_slice_last_value_and_counters",
        "linked_proposal_id": _PROPOSAL_ID,
        "linked_proposal_path": "docs/proposals/prop_l1_decoder_attention_score32_local_temporal_reducer_v1/proposal.json",
    }
    for key, expected in expected_manifest.items():
        _require(manifest, key, expected, "generated manifest")
    _require(
        manifest,
        "caveats",
        ["structural_only", "nonlinear_ppa_delta_vs_functional_reducer_measurement"],
        "generated manifest",
    )

    links = config.get("report_links")
    if not isinstance(links, dict):
        raise SystemExit("config must include report_links for evaluator artifact linkage")
    _require(links, "proposal_id", _PROPOSAL_ID, "report_links")

    submodule_manifests = manifest.get("submodule_manifests")
    if not isinstance(submodule_manifests, dict):
        raise SystemExit("generated manifest must contain submodule_manifests")
    merged_reducer_manifest = submodule_manifests.get("merged_reducer")
    if mode == "reducer":
        if not isinstance(merged_reducer_manifest, dict):
            raise SystemExit("reducer mode must include merged reducer manifest")
        _require(
            merged_reducer_manifest,
            "generator",
            "npu/rtlgen/gen_attention_score32_exact_local_temporal_reducer.py",
            "merged reducer submodule manifest",
        )
    elif merged_reducer_manifest is not None:
        raise SystemExit("source_only mode must not include merged reducer manifest")

    rtl = top_path.read_text(encoding="utf-8", errors="replace")
    top_module = _extract_module(rtl, top_name)
    _require_token(top_module, "localparam integer WAVES = 8;", "generated RTL")
    _require_token(top_module, "reg [31:0] shared_lfsr_q;", "generated RTL")
    _require_token(top_module, "reg [8:0] shared_beat_count_q;", "generated RTL")
    _require_token(top_module, "wire atomic_batch_valid_w = batch_pending_w && batch_ready_w;", "generated RTL")
    _require_token(top_module, "if (running_q && atomic_batch_fire_w) begin", "generated RTL")
    _require_token(top_module, "{24'd0, leaf_value_w[320 +: 8]}", "generated RTL")
    _require_token(
        top_module,
        "source_fold_q <= source_fold_q ^ source_fold_next_w;",
        "generated RTL",
    )
    _require_token(top_module, "leaf_fire_count_q <= leaf_fire_count_q + leaf_fire_count_inc_w;", "generated RTL")
    _require_token(top_module, "output wire [327:0] final_value,", "generated RTL")

    if mode == "reducer":
        reducer_top = f"{top_name}__reducer"
        _extract_module(rtl, reducer_top)
        if top_module.count(f"{reducer_top} u_reducer") != 1:
            raise SystemExit("generated RTL must instantiate the merged reducer exactly once in reducer mode")
        _require_token(top_module, "reducer_result_fire_w", "generated RTL")
        _require_token(top_module, "reducer_out_command_id_w == 16'h7901", "generated RTL")
    else:
        if "__reducer" in top_module:
            raise SystemExit("source_only RTL must not instantiate the merged reducer")
        _require_token(top_module, "if (SOURCE_ONLY_MODE == 1'b1) begin", "generated RTL")
        _require_token(top_module, "if (shared_beat_count_q == 9'd255) begin", "generated RTL")

    for forbidden in (
        "equivalence_hash",
        "openroad",
        "hash_out",
        "leaf_lfsr_q",
        "leaf_beat_count_q",
        "leaf_value_q",
        "shared_lfsr_q [0:PRODUCERS-1]",
    ):
        if forbidden in rtl:
            raise SystemExit(f"physical harness RTL must not contain {forbidden} tokens")

    _compare_current_generation(config=config, rtl_dir=rtl_dir)

    print(
        json.dumps(
            {
                "design": top_name,
                "guard": "attention_score32_exact_local_temporal_reducer_physical_harness_v1",
                "producers": producers,
                "mode": mode,
                "waves": waves,
                "status": "ok",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

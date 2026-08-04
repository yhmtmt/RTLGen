import json
from pathlib import Path

from npu.synth.build_composite_macro_manifest import build_manifest


def _write_manifest(path: Path, *, module: str, platform: str = "nangate45") -> str:
    payload = {
        "version": "0.1",
        "design_id": f"{module}_macro",
        "module": module,
        "platform": platform,
        "flow_variant": "base",
        "blackboxes": [module],
        "additional_lefs": [f"runs/designs/npu_macros/{module}/abstract/{module}.lef"],
        "additional_libs": [f"runs/designs/npu_macros/{module}/abstract/{module}_typ.lib"],
        "additional_gds": [],
        "blackbox_verilog": [f"runs/designs/npu_macros/{module}/abstract/{module}_blackbox.v"],
        "source": {"mode": "unit_test"},
        "manifest_params": {"module_kind": module},
        "make_target": "generate_abstract",
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return str(path)


def test_build_manifest_combines_component_assets_and_metadata(tmp_path: Path) -> None:
    pair_manifest = _write_manifest(tmp_path / "pair_manifest.json", module="pair_node")
    temporal_manifest = _write_manifest(tmp_path / "temporal_manifest.json", module="temporal_merge")

    manifest = build_manifest(
        design_id="gqa8_bundle_r7",
        module="gqa8_top",
        platform="nangate45",
        component_manifest_paths=[pair_manifest, temporal_manifest],
        flow_variant="base",
        source_config="runs/designs/npu_blocks/gqa8_top/config.json",
        source_generator="npu/rtlgen/gen_attention_score32_exact_local_temporal_reducer_gqa8_physical_harness.py",
        manifest_params={
            "pair_node_instance_count": "52",
            "temporal_merge_instance_count": "1",
        },
    )

    assert manifest["design_id"] == "gqa8_bundle_r7"
    assert manifest["module"] == "gqa8_top"
    assert manifest["platform"] == "nangate45"
    assert manifest["blackboxes"] == ["pair_node", "temporal_merge"]
    assert manifest["additional_lefs"] == [
        "runs/designs/npu_macros/pair_node/abstract/pair_node.lef",
        "runs/designs/npu_macros/temporal_merge/abstract/temporal_merge.lef",
    ]
    assert manifest["additional_libs"] == [
        "runs/designs/npu_macros/pair_node/abstract/pair_node_typ.lib",
        "runs/designs/npu_macros/temporal_merge/abstract/temporal_merge_typ.lib",
    ]
    assert manifest["blackbox_verilog"] == [
        "runs/designs/npu_macros/pair_node/abstract/pair_node_blackbox.v",
        "runs/designs/npu_macros/temporal_merge/abstract/temporal_merge_blackbox.v",
    ]
    assert manifest["source"]["mode"] == "composite_macro_bundle"
    assert manifest["source"]["component_manifests"] == [pair_manifest, temporal_manifest]
    assert manifest["manifest_params"]["pair_node_instance_count"] == "52"
    assert manifest["manifest_params"]["temporal_merge_instance_count"] == "1"

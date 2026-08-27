"""Coverage for the block-level OpenROAD sweep runner."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


def _load_run_block_sweep_module():
    script_path = Path(__file__).resolve().parents[3] / "npu" / "synth" / "run_block_sweep.py"
    spec = importlib.util.spec_from_file_location("rtlgen_run_block_sweep", script_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_skip_existing_reconstructs_metrics_csv(tmp_path: Path) -> None:
    run_block_sweep = _load_run_block_sweep_module()
    design_name = "npu_dense_gemm_tile_fp16_4x4_k1_p1"
    design_dir = tmp_path / "runs" / "designs" / "npu_blocks" / design_name
    verilog_dir = design_dir / "verilog"
    verilog_dir.mkdir(parents=True)
    (verilog_dir / f"{design_name}.v").write_text(f"module {design_name}; endmodule\n", encoding="utf-8")

    out_root = tmp_path / "runs" / "campaigns" / "npu" / "dense_gemm_tile_v1"
    sweep_params = {
        "CLOCK_PERIOD": 2.5,
        "CORE_UTILIZATION": 50,
        "TAG": "npu_dense_gemm_tile_v1_cached",
    }
    run_id = run_block_sweep.make_run_id(sweep_params)
    result_path = out_root / design_name / "work" / run_id / "result.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(
        json.dumps(
            {
                "status": "ok",
                "critical_path_ns": 2.1,
                "die_area": 1000.0,
                "total_power_mw": 12.5,
            }
        ),
        encoding="utf-8",
    )

    result = run_block_sweep.run_single(
        design_dir=design_dir,
        design_name=design_name,
        platform="nangate45",
        top=design_name,
        verilog_dir=verilog_dir,
        sdc_template=None,
        sweep_params=sweep_params,
        out_root=out_root,
        skip_existing=True,
        dry_run=False,
        force_copy=False,
        make_target=None,
        macro_manifest=None,
    )

    metrics_path = out_root / design_name / "metrics.csv"
    assert metrics_path.exists()
    rows = list(csv.DictReader(metrics_path.open(encoding="utf-8", newline="")))
    assert len(rows) == 1
    assert rows[0]["design"] == design_name
    assert rows[0]["platform"] == "nangate45"
    assert rows[0]["param_hash"] == run_id
    assert rows[0]["tag"] == "npu_dense_gemm_tile_v1_cached"
    assert rows[0]["work_result_json"] == str(result_path)
    assert result["config_hash"]


def test_isolated_flow_variant_includes_parameter_hash(tmp_path: Path) -> None:
    run_block_sweep = _load_run_block_sweep_module()
    design_name = "noc_segmented_mesh_router_node5"
    design_dir = tmp_path / design_name
    verilog_dir = design_dir / "verilog"
    verilog_dir.mkdir(parents=True)
    (verilog_dir / "router.sv").write_text(
        "module noc_segmented_mesh_router_node5; endmodule\n",
        encoding="utf-8",
    )
    sweep_params = {
        "CLOCK_PERIOD": 1.8,
        "CORE_UTILIZATION": 50,
        "FLOW_VARIANT": "router_node5_bare_v1",
    }
    run_id = run_block_sweep.make_run_id(sweep_params)

    row = run_block_sweep.run_single(
        design_dir=design_dir,
        design_name=design_name,
        platform="nangate45",
        top=design_name,
        verilog_dir=verilog_dir,
        sdc_template=None,
        sweep_params=sweep_params,
        out_root=tmp_path / "out",
        skip_existing=False,
        dry_run=True,
        force_copy=False,
        make_target=None,
        macro_manifest=None,
        isolate_flow_variant=True,
    )

    assert row is not None
    assert row["param_hash"] == run_id
    assert row["effective_flow_variant"] == f"router_node5_bare_v1__{run_id}"


def test_isolated_flow_variant_rejects_unproven_cached_route() -> None:
    run_block_sweep = _load_run_block_sweep_module()

    assert not run_block_sweep.flow_variant_cache_matches(
        {},
        expected="router_node5_bare_v1__abc12345",
        isolation_required=True,
    )
    assert not run_block_sweep.flow_variant_cache_matches(
        {"effective_flow_variant": "router_node5_bare_v1"},
        expected="router_node5_bare_v1__abc12345",
        isolation_required=True,
    )
    assert run_block_sweep.flow_variant_cache_matches(
        {"effective_flow_variant": "router_node5_bare_v1__abc12345"},
        expected="router_node5_bare_v1__abc12345",
        isolation_required=True,
    )

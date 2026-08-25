from __future__ import annotations

import csv
import json
from pathlib import Path
import shutil
import subprocess
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.db import create_all
from control_plane.models.work_items import WorkItem
from control_plane.services.l1_task_generator import (
    Layer1SweepGenerateRequest,
    generate_l1_sweep_task,
)
from npu.eval import physical_hierarchy_metrics as hierarchy
from npu.eval.check_attention_shared_stream_context_service_ppa_guard import check
from npu.rtlgen.gen_attention_shared_stream_context_service_ppa_activity_harness import (
    generate,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DESIGN = REPO_ROOT / "runs/designs/npu_blocks/attention_shared_stream_context_service_ppa_l1"
CONFIG = DESIGN / "config.json"
SWEEP = REPO_ROOT / (
    "runs/campaigns/npu/attention_shared_stream_context_service_ppa_l1/"
    "sweeps/nangate45_canary.json"
)
SYNTH_DIAG_SWEEP = REPO_ROOT / (
    "runs/campaigns/npu/attention_shared_stream_context_service_ppa_l1/"
    "sweeps/nangate45_synth_mode_diag_r3.json"
)
PROPOSAL = "docs/proposals/prop_l1_attention_shared_stream_context_service_ppa_v1"
SYNTH_DIAG_ITEM = "l1_attention_shared_stream_context_service_synth_mode_diag_v1_r3"


def test_generator_and_guard_prove_complete_vc0_service(tmp_path: Path) -> None:
    out_dir = tmp_path / DESIGN.name
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    generate(config, out_dir / "verilog")
    (out_dir / "config.json").write_text(
        CONFIG.read_text(encoding="utf-8"), encoding="utf-8"
    )

    check(out_dir)
    manifest = json.loads(
        (
            out_dir
            / "verilog"
            / "attention_shared_stream_context_service_ppa_activity_harness_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["top_pin_inventory"] == {
        "input_bits": 35,
        "output_bits": 128,
        "total_bits": 163,
        "inputs": ["clk:1", "rst_n:1", "enable:1", "control:32"],
        "outputs": ["observable:128"],
    }
    assert manifest["composition"]["dut_hierarchy_area_prefix"] == "composition/service/"
    assert manifest["service_contract"]["remote_contexts"] == 112
    assert manifest["service_contract"]["total_packets"] == 7616
    assert manifest["service_contract"]["total_flits"] == 60928
    assert manifest["remaining_abstractions"][1].startswith("VC1 exact reduction")


def test_canary_uses_two_explicit_clock_points() -> None:
    sweep = json.loads(SWEEP.read_text(encoding="utf-8"))
    flow = sweep["flow_params"]
    assert flow["CLOCK_PERIOD"] == [5.0, 8.0]
    assert flow["CORE_UTILIZATION"] == [45]
    assert flow["PLACE_DENSITY"] == [0.52]
    assert flow["SYNTH_HIERARCHICAL"] == [1]
    assert flow["SYNTH_HIER_SEPARATOR"] == ["/"]
    assert "SYNTH_KEEP_MODULES" not in flow
    assert "CHECK_SYNTH_KEEP_MODULES" not in flow


def test_synth_diagnostic_compares_unique_flat_and_hierarchical_variants() -> None:
    sweep = json.loads(SYNTH_DIAG_SWEEP.read_text(encoding="utf-8"))
    modes = sweep["mode_compare"]["modes"]
    assert [mode["name"] for mode in modes] == ["flat_synth", "hierarchical_synth"]
    assert [mode["use_macro"] for mode in modes] == [False, False]
    assert [mode["param_overrides"]["FLOW_VARIANT"] for mode in modes] == [
        "synth_diag_r3_flat",
        "synth_diag_r3_hierarchical",
    ]
    assert [mode["param_overrides"]["SYNTH_HIERARCHICAL"] for mode in modes] == [0, 1]


def test_segmented_mesh_router_has_no_yosys_driver_conflicts(tmp_path: Path) -> None:
    yosys = shutil.which("yosys")
    if yosys is None:
        pytest.skip("yosys is not installed")
    script = "; ".join(
        [
            "read_verilog -sv npu/sim/rtl/noc_ready_valid_fifo.sv "
            "npu/sim/rtl/noc_segmented_mesh_router.sv",
            "hierarchy -top noc_segmented_mesh_router",
            "proc",
            "check",
        ]
    )
    result = subprocess.run(
        [yosys, "-p", script],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout
    assert "Drivers conflicting" not in result.stdout


def test_generic_l1_task_manifest_contains_complete_service_commands() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    with Session(engine) as session:
        with (
            patch(
                "control_plane.services.l1_task_generator._resolve_source_commit",
                return_value="1234567890abcdef",
            ),
            patch(
                "control_plane.services.l1_task_generator.build_generation_source_identity",
                return_value={
                    "version": 1,
                    "declared_source_commit": "1234567890abcdef",
                    "repo_head_sha": "1234567890abcdef",
                    "relation": "exact",
                    "proof": "test",
                    "clean": True,
                },
            ),
        ):
            result = generate_l1_sweep_task(
                session,
                Layer1SweepGenerateRequest(
                    repo_root=str(REPO_ROOT),
                    sweep_path=str(SWEEP),
                    config_paths=[str(CONFIG)],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    item_id="l1_attention_shared_stream_context_service_ppa_test",
                    source_commit="HEAD",
                    proposal_id="prop_l1_attention_shared_stream_context_service_ppa_v1",
                    proposal_path=PROPOSAL,
                    update_proposal_files=False,
                ),
            )
        item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
        assert [command["name"] for command in item.command_manifest] == [
            "generate_attention_shared_stream_context_service_ppa_activity_harness_rtl",
            "check_attention_shared_stream_context_service_ppa_activity_harness_guard",
            "run_block_sweep",
            "attach_attention_shared_stream_context_service_ppa_activity_harness_hierarchical_area",
            "extract_attention_shared_stream_context_service_ppa_activity_harness_timing_paths",
            "build_runs_index",
            "validate",
        ]
        assert "--post-sweep" in item.command_manifest[3]["run"]
        assert any(path.endswith("/hierarchy_reports/index.json") for path in item.expected_outputs)


def test_synth_only_l1_task_omits_physical_postchecks() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    with Session(engine) as session:
        with (
            patch(
                "control_plane.services.l1_task_generator._resolve_source_commit",
                return_value="1234567890abcdef",
            ),
            patch(
                "control_plane.services.l1_task_generator.build_generation_source_identity",
                return_value={
                    "version": 1,
                    "declared_source_commit": "1234567890abcdef",
                    "repo_head_sha": "1234567890abcdef",
                    "relation": "exact",
                    "proof": "test",
                    "clean": True,
                },
            ),
        ):
            result = generate_l1_sweep_task(
                session,
                Layer1SweepGenerateRequest(
                    repo_root=str(REPO_ROOT),
                    sweep_path=str(SYNTH_DIAG_SWEEP),
                    config_paths=[str(CONFIG)],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    item_id=SYNTH_DIAG_ITEM,
                    source_commit="HEAD",
                    proposal_id="prop_l1_attention_shared_stream_context_service_ppa_v1",
                    proposal_path=PROPOSAL,
                    update_proposal_files=False,
                ),
            )
        item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
        assert [command["name"] for command in item.command_manifest] == [
            "generate_attention_shared_stream_context_service_ppa_activity_harness_rtl",
            "check_attention_shared_stream_context_service_ppa_activity_harness_guard",
            "run_block_sweep",
            "build_runs_index",
            "validate",
        ]
        assert "--make_target 1_2_yosys" in item.command_manifest[2]["run"]
        assert item.expected_outputs == [
            "runs/designs/npu_blocks/attention_shared_stream_context_service_ppa_l1/metrics.csv"
        ]
        assert item.task_request.request_payload["developer_loop"]["evaluation"]["mode"] == (
            "synth_prefilter"
        )


def _write_metrics(path: Path, status: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["design", "tag", "status", "params_json", "result_path"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "design": path.parent.name,
                "tag": "canary_0",
                "status": status,
                "params_json": json.dumps({"FLOW_VARIANT": "canary_0"}),
                "result_path": "reports/6_finish.rpt",
            }
        )


def test_hierarchy_metrics_preserve_failed_boundary_row(tmp_path: Path) -> None:
    design_dir = tmp_path / "failed_design"
    _write_metrics(design_dir / "metrics.csv", "failed")

    hierarchy.attach_hierarchy_reports(
        design_dir,
        prefix="composition/service/",
        precheck=lambda _: None,
        repo_root=tmp_path,
    )

    with (design_dir / "metrics.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert rows[0]["status"] == "failed"
    assert rows[0]["hierarchical_instance_area_um2"] == ""
    index = json.loads((design_dir / "hierarchy_reports/index.json").read_text())
    assert index["status"] == "no_successful_physical_rows"


def test_hierarchy_metrics_attach_successful_service_area(tmp_path: Path) -> None:
    design_dir = tmp_path / "successful_design"
    _write_metrics(design_dir / "metrics.csv", "ok")
    odb = tmp_path / "6_final.odb"
    odb.write_text("test", encoding="utf-8")
    payload = {
        "prefix": "composition/service/",
        "matched_instance_count": 42,
        "matched_instance_area_um2": 123.5,
    }

    with (
        patch.object(hierarchy, "find_final_odb", return_value=odb),
        patch.object(hierarchy, "measure_hierarchy", return_value=payload),
    ):
        hierarchy.attach_hierarchy_reports(
            design_dir,
            prefix="composition/service/",
            precheck=lambda _: None,
            repo_root=tmp_path,
        )

    with (design_dir / "metrics.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert reader.fieldnames[-2:] == ["params_json", "result_path"]
    assert rows[0]["hierarchical_instance_area_um2"] == "123.5"
    assert rows[0]["hierarchical_instance_count"] == "42"

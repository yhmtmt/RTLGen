from __future__ import annotations

import csv
import json
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.db import create_all
from control_plane.models.work_items import WorkItem
from control_plane.services.l1_task_generator import (
    Layer1SweepGenerateRequest,
    generate_l1_sweep_task,
)
from npu.eval import check_attention_score32_exact_shared_root_transport_ppa_activity_guard as guard
from npu.eval.check_attention_score32_exact_shared_root_transport_ppa_activity_guard import (
    attach_hierarchy_reports,
    check,
)
from npu.rtlgen.gen_attention_score32_exact_shared_root_transport_ppa_activity_harness import generate


REPO_ROOT = Path(__file__).resolve().parents[3]
DESIGN = REPO_ROOT / "runs/designs/npu_blocks/attention_score32_exact_shared_root_transport_ppa_activity_l1"
CONFIG = DESIGN / "config.json"
SWEEP = REPO_ROOT / (
    "runs/campaigns/npu/attention_score32_exact_shared_root_transport_ppa_activity_l1/"
    "sweeps/nangate45_canary.json"
)
SYNTH_DIAG_SWEEP = REPO_ROOT / (
    "runs/campaigns/npu/attention_score32_exact_shared_root_transport_ppa_activity_l1/"
    "sweeps/nangate45_synth_mode_diag_r3.json"
)
PROPOSAL = "docs/proposals/prop_l1_attention_score32_exact_shared_root_transport_ppa_activity_v1"
SYNTH_DIAG_ITEM = "l1_attention_score32_exact_shared_root_transport_synth_mode_diag_v1_r3"


def test_generator_and_guard_prove_compact_exact_transport_contract(tmp_path: Path) -> None:
    out_dir = tmp_path / DESIGN.name
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    generate(config, out_dir / "verilog")
    (out_dir / "config.json").write_text(CONFIG.read_text(encoding="utf-8"), encoding="utf-8")

    check(out_dir)
    manifest = json.loads(
        (out_dir / "verilog" / "attention_score32_exact_shared_root_transport_ppa_activity_harness_manifest.json")
        .read_text(encoding="utf-8")
    )
    macro_manifest = json.loads((out_dir / "verilog" / "macro_manifest.json").read_text(encoding="utf-8"))
    assert manifest["top_pin_inventory"] == {
        "input_bits": 35,
        "output_bits": 128,
        "total_bits": 163,
        "inputs": ["clk:1", "rst_n:1", "enable:1", "control:32"],
        "outputs": ["observable:128"],
    }
    assert manifest["composition"]["instance_name"] == "composition"
    assert manifest["composition"]["parameters"] == {"PHYSICAL_BANKS": 15, "USE_FAKERAM": 1}
    assert manifest["root_storage"]["macro_count"] == 120
    assert macro_manifest["manifest_params"]["root_storage_macro_count"] == 120
    source_roles = {entry["role"]: entry["path"] for entry in manifest["source_files"]}
    assert source_roles["simulation_memory_model"] == "npu/sim/rtl/fakeram45_64x32_model.sv"
    assert source_roles["physical_memory_blackbox"] == "npu/rtl/fakeram45_64x32_blackbox.v"
    assert any("112 shared-SRAM" in item for item in manifest["remaining_abstractions"])


def test_canary_uses_two_clocks_in_a_conservative_fixed_envelope() -> None:
    sweep = json.loads(SWEEP.read_text(encoding="utf-8"))
    flow = sweep["flow_params"]
    assert flow["CLOCK_PERIOD"] == [10.0, 12.0]
    assert flow["DIE_AREA"] == ["0 0 4000 4000"]
    assert flow["CORE_AREA"] == ["100 100 3900 3900"]
    assert flow["PLACE_DENSITY"] == [0.30]
    assert flow["SYNTH_HIERARCHICAL"] == [1]
    assert flow["SYNTH_HIER_SEPARATOR"] == ["/"]
    assert "SYNTH_KEEP_MODULES" not in flow
    assert "CHECK_SYNTH_KEEP_MODULES" not in flow


def test_synth_diagnostic_keeps_blackboxes_but_excludes_macro_liberty() -> None:
    sweep = json.loads(SYNTH_DIAG_SWEEP.read_text(encoding="utf-8"))
    assert sweep["flow_params"]["ADDITIONAL_LIBS"] == [""]
    modes = sweep["mode_compare"]["modes"]
    assert [mode["name"] for mode in modes] == ["flat_synth", "hierarchical_synth"]
    assert [mode["use_macro"] for mode in modes] == [True, True]
    assert [mode["param_overrides"]["FLOW_VARIANT"] for mode in modes] == [
        "synth_diag_r3_flat",
        "synth_diag_r3_hierarchical",
    ]
    assert [mode["param_overrides"]["SYNTH_HIERARCHICAL"] for mode in modes] == [0, 1]


def test_generic_l1_task_manifest_contains_physical_plumbing() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    with Session(engine) as session:
        with patch(
            "control_plane.services.l1_task_generator.build_generation_source_identity",
            return_value={
                "version": 1,
                "declared_source_commit": "e99c75ca",
                "repo_head_sha": "e99c75ca",
                "relation": "exact",
                "proof": "test",
                "clean": True,
            },
        ):
            result = generate_l1_sweep_task(
                session,
                Layer1SweepGenerateRequest(
                    repo_root=str(REPO_ROOT),
                    sweep_path=str(SWEEP),
                    config_paths=[str(CONFIG)],
                    platform="nangate45",
                    out_root="runs/designs/npu_blocks",
                    item_id="l1_attention_score32_exact_shared_root_transport_ppa_activity_test",
                    source_commit="HEAD",
                    proposal_id="prop_l1_attention_score32_exact_shared_root_transport_ppa_activity_v1",
                    proposal_path=PROPOSAL,
                    update_proposal_files=False,
                ),
            )
        work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
        assert [entry["name"] for entry in work_item.command_manifest] == [
            "generate_attention_score32_exact_shared_root_transport_ppa_activity_harness_rtl",
            "check_attention_score32_exact_shared_root_transport_ppa_activity_harness_guard",
            "run_block_sweep",
            "attach_attention_score32_exact_shared_root_transport_ppa_activity_harness_hierarchical_area",
            "extract_attention_score32_exact_shared_root_transport_ppa_activity_harness_timing_paths",
            "build_runs_index",
            "validate",
        ]
        assert "--macro_manifest" in work_item.command_manifest[2]["run"]
        assert "--post-sweep" in work_item.command_manifest[3]["run"]
        assert any(path.endswith("/timing_debug_report.md") for path in work_item.expected_outputs)
        assert "hierarchy_reports/index.json" in " ".join(work_item.expected_outputs)
        assert work_item.task_request.request_payload["developer_loop"]["proposal_id"] == (
            "prop_l1_attention_score32_exact_shared_root_transport_ppa_activity_v1"
        )


def test_synth_only_l1_task_uses_checked_in_request_and_omits_physical_postchecks() -> None:
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
                    proposal_id="prop_l1_attention_score32_exact_shared_root_transport_ppa_activity_v1",
                    proposal_path=PROPOSAL,
                    update_proposal_files=False,
                ),
            )
        item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
        assert [command["name"] for command in item.command_manifest] == [
            "generate_attention_score32_exact_shared_root_transport_ppa_activity_harness_rtl",
            "check_attention_score32_exact_shared_root_transport_ppa_activity_harness_guard",
            "run_block_sweep",
            "build_runs_index",
            "validate",
        ]
        assert "--make_target 1_2_yosys" in item.command_manifest[2]["run"]
        assert "--macro_manifest" in item.command_manifest[2]["run"]
        assert item.expected_outputs == [
            "runs/designs/npu_blocks/attention_score32_exact_shared_root_transport_ppa_activity_l1/metrics.csv"
        ]
        assert item.task_request.request_payload["developer_loop"]["evaluation"]["mode"] == (
            "synth_prefilter"
        )


def _write_metrics(path: Path, *, status: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "design",
                "tag",
                "status",
                "work_result_json",
                "params_json",
                "result_path",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "design": path.parent.name,
                "tag": "canary_0",
                "status": status,
                "work_result_json": "result.json",
                "params_json": json.dumps({"FLOW_VARIANT": "canary_0"}),
                "result_path": "reports/6_finish.rpt",
            }
        )


def test_post_sweep_preserves_all_infeasible_points_without_failing(tmp_path: Path) -> None:
    design_dir = tmp_path / "failed_design"
    _write_metrics(design_dir / "metrics.csv", status="failed")

    with patch.object(guard, "check"):
        attach_hierarchy_reports(design_dir)

    with (design_dir / "metrics.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert reader.fieldnames[-2:] == ["params_json", "result_path"]
    assert rows[0]["status"] == "failed"
    assert rows[0]["hierarchical_instance_area_um2"] == ""
    report_index = json.loads((design_dir / "hierarchy_reports/index.json").read_text(encoding="utf-8"))
    assert report_index["status"] == "no_successful_physical_rows"
    assert report_index["rows"] == []


def test_post_sweep_places_hierarchy_fields_before_canonical_csv_tail(tmp_path: Path) -> None:
    design_dir = tmp_path / "successful_design"
    _write_metrics(design_dir / "metrics.csv", status="ok")
    odb = tmp_path / "6_final.odb"
    odb.write_text("test", encoding="utf-8")
    hierarchy_payload = {
        "prefix": guard.HIERARCHY_PREFIX,
        "matched_instance_count": 42,
        "matched_instance_area_um2": 123.5,
    }

    with (
        patch.object(guard, "REPO_ROOT", tmp_path),
        patch.object(guard, "check"),
        patch.object(guard, "_find_odb", return_value=odb),
        patch.object(guard, "_measure_hierarchy", return_value=hierarchy_payload),
    ):
        attach_hierarchy_reports(design_dir)

    with (design_dir / "metrics.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert reader.fieldnames[-2:] == ["params_json", "result_path"]
    assert reader.fieldnames.index("hierarchical_instance_area_um2") < reader.fieldnames.index("params_json")
    assert rows[0]["hierarchical_instance_area_um2"] == "123.5"
    assert rows[0]["hierarchical_instance_count"] == "42"
    report_index = json.loads((design_dir / "hierarchy_reports/index.json").read_text(encoding="utf-8"))
    assert report_index["status"] == "ok"

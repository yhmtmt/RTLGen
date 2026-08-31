from __future__ import annotations

import json
import csv
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
from npu.eval import (
    check_attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_guard as guard,
)
from npu.rtlgen.gen_attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness import (
    generate,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DESIGN = REPO_ROOT / (
    "runs/designs/npu_blocks/"
    "attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_l1"
)
CONFIG = DESIGN / "config.json"
SYNTH_SWEEP = REPO_ROOT / (
    "runs/campaigns/npu/"
    "attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_l1/"
    "sweeps/nangate45_synth_mode_diag_v1.json"
)
PHYSICAL_SWEEP = SYNTH_SWEEP.with_name("nangate45_canary.json")
PROPOSAL = "docs/proposals/prop_l1_attention_score32_exact_dual_producer_shared_mesh_ppa_activity_v1"


def test_generator_and_guard_bind_complete_shared_mesh(tmp_path: Path) -> None:
    out_dir = tmp_path / DESIGN.name
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    generate(config, out_dir / "verilog")
    (out_dir / "config.json").write_text(
        CONFIG.read_text(encoding="utf-8"), encoding="utf-8"
    )

    guard.check(out_dir)
    manifest = json.loads(
        (
            out_dir
            / "verilog"
            / "attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["top_pin_bits"] == 163
    assert manifest["vc0_service"]["total_flits"] == 60928
    assert manifest["vc1_exact_reduction"]["total_flits"] == 10020
    assert manifest["shared_transport"]["mesh_count"] == 1
    assert manifest["shared_transport"]["injection_arbiter_count"] == 16
    assert manifest["blackbox_instance_counts"] == {"fakeram45_64x32": 120}


def test_hierarchy_tcl_quotes_json_arrays(tmp_path: Path) -> None:
    script = guard._hierarchy_tcl(tmp_path / "final.odb", tmp_path / "report.json")
    assert '\\[\\"composition/vc0_activity/service/\\"' in script
    assert '\\"prefix_reports\\": \\[' in script
    assert 'puts $report "  \\]"' in script


def test_post_sweep_attaches_disjoint_prefix_sum(tmp_path: Path) -> None:
    out_dir = tmp_path / DESIGN.name
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    generate(config, out_dir / "verilog")
    (out_dir / "config.json").write_text(
        CONFIG.read_text(encoding="utf-8"), encoding="utf-8"
    )
    with (out_dir / "metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["design", "tag", "status", "params_json", "result_path"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "design": out_dir.name,
                "tag": "canary_0",
                "status": "ok",
                "params_json": "{}",
                "result_path": "reports/6_finish.rpt",
            }
        )
    odb = tmp_path / "6_final.odb"
    odb.write_text("test", encoding="utf-8")
    prefix_reports = [
        {
            "prefix": prefix,
            "matched_instance_count": index + 1,
            "matched_instance_area_um2": float((index + 1) * 10),
        }
        for index, prefix in enumerate(guard.HIERARCHY_PREFIXES)
    ]
    payload = {
        "prefixes": list(guard.HIERARCHY_PREFIXES),
        "matched_instance_count": 6,
        "matched_instance_area_um2": 60.0,
        "prefix_reports": prefix_reports,
    }
    with (
        patch.object(guard, "check"),
        patch.object(guard, "REPO_ROOT", tmp_path),
        patch.object(guard, "_find_odb", return_value=odb),
        patch.object(guard, "_measure_hierarchy", return_value=payload),
    ):
        guard.attach_hierarchy_reports(out_dir)

    with (out_dir / "metrics.csv").open(newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    assert row["hierarchical_instance_area_um2"] == "60.0"
    assert row["hierarchical_instance_count"] == "6"
    index = json.loads((out_dir / "hierarchy_reports/index.json").read_text())
    assert index["aggregation"] == "sum matched areas from disjoint prefixes"
    assert index["rows"][0]["prefix_reports"] == prefix_reports


def _generate_task(session: Session, sweep: Path, item_id: str, make_target: str | None) -> WorkItem:
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
                sweep_path=str(sweep),
                config_paths=[str(CONFIG)],
                platform="nangate45",
                out_root="runs/designs/npu_blocks",
                item_id=item_id,
                source_commit="HEAD",
                proposal_id=(
                    "prop_l1_attention_score32_exact_dual_producer_shared_mesh_ppa_activity_v1"
                ),
                proposal_path=PROPOSAL,
                make_target=make_target,
                update_proposal_files=False,
            ),
        )
    return session.query(WorkItem).filter_by(item_id=result.item_id).one()


def test_synth_prefilter_omits_physical_postchecks() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    with Session(engine) as session:
        item = _generate_task(
            session,
            SYNTH_SWEEP,
            "l1_attention_score32_exact_dual_producer_shared_mesh_synth_test",
            "1_2_yosys",
        )
        assert [command["name"] for command in item.command_manifest] == [
            "generate_attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness_rtl",
            "check_attention_score32_exact_dual_producer_shared_mesh4x4_ppa_activity_harness_guard",
            "run_block_sweep",
            "build_runs_index",
            "validate",
        ]
        assert "--make_target 1_2_yosys" in item.command_manifest[2]["run"]
        assert item.expected_outputs == [f"{DESIGN.relative_to(REPO_ROOT)}/metrics.csv"]


def test_physical_task_retains_hierarchy_and_timing_outputs() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    with Session(engine) as session:
        item = _generate_task(
            session,
            PHYSICAL_SWEEP,
            "l1_attention_score32_exact_dual_producer_shared_mesh_physical_test",
            None,
        )
        names = [command["name"] for command in item.command_manifest]
        assert names[3].startswith("attach_attention_score32_exact_dual_producer")
        assert names[4].startswith("extract_attention_score32_exact_dual_producer")
        assert names[-2:] == ["build_runs_index", "validate"]
        assert any(path.endswith("/hierarchy_reports/index.json") for path in item.expected_outputs)
        assert any(path.endswith("/timing_debug_report.md") for path in item.expected_outputs)

"""Layer 2 task generation coverage."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.db import create_all
from control_plane.models.enums import WorkItemState
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.services.l2_task_generator import Layer2CampaignGenerateRequest, Layer2TaskGenerationError, generate_l2_campaign_task


def _write_campaign(repo_root: Path) -> str:
    campaign_path = repo_root / "runs" / "campaigns" / "npu" / "demo_campaign" / "campaign.json"
    campaign_path.parent.mkdir(parents=True, exist_ok=True)
    campaign_path.write_text(
        json.dumps(
            {
                "version": 0.1,
                "campaign_id": "demo_campaign",
                "description": "Demo Layer2 campaign for control-plane generation coverage.",
                "platform": "nangate45",
                "model_manifest": "runs/models/demo_set/manifest.json",
                "architecture_points": [
                    {
                        "arch_id": "fp16_nm1_demo",
                        "rtlgen_config": "runs/designs/npu_blocks/demo_nm1/config.json",
                        "synth_design_dir": "runs/designs/npu_blocks/demo_nm1",
                        "sweep_file": "runs/designs/npu_blocks/demo_nm1/sweep.json",
                        "macro_manifest": "runs/designs/npu_macros/demo_nm1/macro_manifest.json",
                        "layer1_modules": {
                            "manifest": "runs/candidates/nangate45/module_candidates.json",
                            "variant_ids": ["demo_variant"],
                        },
                    },
                    {
                        "arch_id": "fp16_nm2_demo",
                        "rtlgen_config": "runs/designs/npu_blocks/demo_nm2/config.json",
                        "synth_design_dir": "runs/designs/npu_blocks/demo_nm2",
                        "sweep_file": "runs/designs/npu_blocks/demo_nm2/sweep.json",
                        "macro_manifest": "runs/designs/npu_macros/demo_nm2/macro_manifest.json",
                        "layer1_modules": {
                            "manifest": "runs/candidates/nangate45/module_candidates.json",
                            "variant_ids": ["demo_variant"],
                        },
                    },
                ],
                "outputs": {
                    "campaign_dir": "runs/campaigns/npu/demo_campaign",
                    "results_csv": "runs/campaigns/npu/demo_campaign/results.csv",
                    "report_md": "runs/campaigns/npu/demo_campaign/report.md",
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return str(campaign_path.relative_to(repo_root))


def _init_git_repo(repo_root: Path) -> str:
    origin_root = repo_root.parent / "origin.git"
    subprocess.run(["git", "init", "--bare", str(origin_root)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "init"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "config", "user.email", "tester@example.com"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "config", "user.name", "Tester"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "add", "."], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "commit", "-m", "test repo"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "remote", "add", "origin", str(origin_root)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "push", "-u", "origin", "HEAD:master"], check=True, capture_output=True, text=True)
    result = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def test_generate_l2_campaign_task_creates_ready_work_item() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        campaign_path = _write_campaign(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l2_campaign_task(
                session,
                Layer2CampaignGenerateRequest(
                    repo_root=str(repo_root),
                    campaign_path=campaign_path,
                    requested_by="@tester",
                    source_commit=source_commit,
                    objective_profiles_json="runs/campaigns/npu/base/objective_profiles.json",
                    proposal_id="prop_l2_demo_v1",
                    proposal_path="docs/developer_loop/prop_l2_demo_v1",
                    evaluation_mode="paired_comparison",
                    abstraction_layer="full_architecture",
                    expected_direction="better_than_historical",
                    expected_reason="Candidate should improve the measured baseline.",
                    comparison_role="candidate",
                    paired_baseline_item_id="l2_demo_baseline",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            proposal_dir = repo_root / "docs" / "developer_loop" / "prop_l2_demo_v1"
            evaluation_requests = json.loads((proposal_dir / "evaluation_requests.json").read_text(encoding="utf-8"))
            assert result.status == "applied"
            assert work_item.task_type == "l2_campaign"
            assert work_item.state == WorkItemState.DISPATCH_PENDING
            assert work_item.source_mode == "src_verilog"
            assert evaluation_requests["proposal_id"] == "prop_l2_demo_v1"
            assert evaluation_requests["source_commit"] == source_commit
            assert evaluation_requests["requested_items"] == [
                {
                    "item_id": result.item_id,
                    "task_type": "l2_campaign",
                    "objective": "Demo Layer2 campaign for control-plane generation coverage.",
                    "evaluation_mode": "paired_comparison",
                    "abstraction_layer": "full_architecture",
                    "comparison_role": "candidate",
                    "paired_baseline_item_id": "l2_demo_baseline",
                    "depends_on_item_ids": [],
                    "requires_merged_inputs": False,
                    "requires_materialized_refs": False,
                    "expected_result": {
                        "direction": "better_than_historical",
                        "reason": "Candidate should improve the measured baseline.",
                    },
                    "status": "pending",
                }
            ]
            for name in (
                "proposal.json",
                "evaluation_requests.json",
                "promotion_decision.json",
                "promotion_result.json",
                "README.md",
                "analysis_report.md",
            ):
                assert (proposal_dir / name).exists()
            assert [command["name"] for command in work_item.command_manifest] == [
                "fetch_models",
                "validate_campaign",
                "run_campaign",
                "report_campaign",
                "objective_sweep",
                "validate_runs",
            ]
            assert work_item.command_manifest[0]["run"] == "python3 npu/eval/fetch_models.py --manifest runs/models/demo_set/manifest.json"
            assert work_item.command_manifest[5]["run"] == "python3 scripts/validate_runs.py --skip_eval_queue"
            assert work_item.expected_outputs == [
                f"runs/campaigns/npu/demo_campaign/campaign__{result.item_id}.json",
                f"runs/campaigns/npu/demo_campaign__{result.item_id}/results.csv",
                f"runs/campaigns/npu/demo_campaign__{result.item_id}/report.md",
                f"runs/campaigns/npu/demo_campaign__{result.item_id}/summary.csv",
                f"runs/campaigns/npu/demo_campaign__{result.item_id}/pareto.csv",
                f"runs/campaigns/npu/demo_campaign__{result.item_id}/best_point.json",
                f"runs/campaigns/npu/demo_campaign__{result.item_id}/objective_sweep.csv",
                f"runs/campaigns/npu/demo_campaign__{result.item_id}/objective_sweep.md",
                "runs/designs/npu_blocks/demo_nm1/metrics.csv",
                "runs/designs/npu_blocks/demo_nm2/metrics.csv",
            ]
            payload = work_item.task_request.request_payload
            assert payload["layer"] == "layer2"
            assert payload["task"]["inputs"]["candidate_manifests"] == [
                "runs/candidates/nangate45/module_candidates.json"
            ]
            assert payload["task"]["inputs"]["generated_campaign"] == {
                "base_campaign_path": "runs/campaigns/npu/demo_campaign/campaign.json",
                "path": f"runs/campaigns/npu/demo_campaign/campaign__{result.item_id}.json",
                "outputs": {
                    "campaign_dir": f"runs/campaigns/npu/demo_campaign__{result.item_id}",
                    "results_csv": f"runs/campaigns/npu/demo_campaign__{result.item_id}/results.csv",
                    "report_md": f"runs/campaigns/npu/demo_campaign__{result.item_id}/report.md",
                },
                "clean_outputs": True,
            }
            assert payload["developer_loop"] == {
                "proposal_id": "prop_l2_demo_v1",
                "proposal_path": "docs/developer_loop/prop_l2_demo_v1",
                "evaluation": {
                    "mode": "paired_comparison",
                    "expected_direction": "better_than_historical",
                    "expected_reason": "Candidate should improve the measured baseline.",
                },
                "abstraction": {
                    "layer": "full_architecture",
                },
                "comparison": {
                    "role": "candidate",
                    "paired_baseline_item_id": "l2_demo_baseline",
                },
            }
            assert payload["task"]["commands"][0]["name"] == "fetch_models"
            assert "--run_physical" in payload["task"]["commands"][2]["run"]


def test_generate_l2_campaign_task_adds_decoder_probability_path_evidence() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        campaign_path = _write_campaign(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l2_campaign_task(
                session,
                Layer2CampaignGenerateRequest(
                    repo_root=str(repo_root),
                    campaign_path=campaign_path,
                    requested_by="@tester",
                    source_commit=source_commit,
                    item_id="l2_decoder_exact_probability_path_v1",
                    proposal_id="prop_l2_decoder_exact_probability_path_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_exact_probability_path_v1/proposal.json",
                    evaluation_mode="paired_comparison",
                    abstraction_layer="decoder_probability_path",
                    expected_direction="better_than_historical",
                    comparison_role="candidate",
                    paired_baseline_item_id="l2_decoder_contract_eval_confirm_v1",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[:3] == [
                "validate_decoder_contract",
                "compare_decoder_quality",
                "check_decoder_missing_model_error",
            ]
            assert command_names == [
                "validate_decoder_contract",
                "compare_decoder_quality",
                "check_decoder_missing_model_error",
                "fetch_models",
                "validate_campaign",
                "run_campaign",
                "report_campaign",
                "validate_runs",
            ]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs == {
                "dataset_manifest": "runs/datasets/llm_decoder_eval_tiny_v1/manifest.json",
                "reference_manifest": "runs/datasets/llm_decoder_eval_tiny_v1/reference_manifest.json",
                "candidate_manifest": "runs/datasets/llm_decoder_eval_tiny_v1/candidate_manifest.json",
                "baseline_quality_out": "runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_compare__l2_decoder_contract_eval_confirm_v1.json",
                "validation_out": "runs/datasets/llm_decoder_eval_tiny_v1/decoder_contract_validation__l2_decoder_exact_probability_path_v1.json",
                "quality_out": "runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_compare__l2_decoder_exact_probability_path_v1.json",
                "missing_model_check_out": "runs/datasets/llm_decoder_eval_tiny_v1/missing_model_check__l2_decoder_exact_probability_path_v1.json",
            }
            assert decoder_inputs["validation_out"] in work_item.expected_outputs
            assert decoder_inputs["quality_out"] in work_item.expected_outputs
            assert decoder_inputs["missing_model_check_out"] in work_item.expected_outputs
            assert "NoSuchFile" in work_item.command_manifest[2]["run"]
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_probability_path",
            }


def test_generate_l2_campaign_task_adds_decoder_probability_sweep_evidence() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        campaign_path = _write_campaign(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l2_campaign_task(
                session,
                Layer2CampaignGenerateRequest(
                    repo_root=str(repo_root),
                    campaign_path=campaign_path,
                    requested_by="@tester",
                    source_commit=source_commit,
                    item_id="l2_decoder_probability_sweep_v1",
                    proposal_id="prop_l2_decoder_probability_sweep_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_probability_sweep_v1/proposal.json",
                    evaluation_mode="broad_ranking",
                    abstraction_layer="decoder_probability_sweep",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[:4] == [
                "validate_decoder_contract",
                "compare_decoder_quality",
                "check_decoder_missing_model_error",
                "sweep_decoder_candidate_quality",
            ]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["candidate_sweep_out"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/"
                "decoder_quality_sweep__l2_decoder_probability_sweep_v1.json"
            )
            assert decoder_inputs["candidate_sweep_dir"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/"
                "candidate_sweeps/l2_decoder_probability_sweep_v1"
            )
            assert decoder_inputs["candidate_sweep_templates"] == [
                "candidate_onnx_softmax_exact",
                "candidate_onnx_softmax_approx",
            ]
            assert decoder_inputs["candidate_sweep_out"] in work_item.expected_outputs
            assert "--template candidate_onnx_softmax_exact" in work_item.command_manifest[3]["run"]
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_probability_sweep",
            }


def test_generate_l2_campaign_task_adds_decoder_probability_sensitivity_evidence() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        campaign_path = _write_campaign(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l2_campaign_task(
                session,
                Layer2CampaignGenerateRequest(
                    repo_root=str(repo_root),
                    campaign_path=campaign_path,
                    requested_by="@tester",
                    source_commit=source_commit,
                    item_id="l2_decoder_probability_sensitivity_v1",
                    proposal_id="prop_l2_decoder_probability_sensitivity_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_probability_sensitivity_v1/proposal.json",
                    evaluation_mode="broad_ranking",
                    abstraction_layer="decoder_probability_sensitivity",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[:4] == [
                "validate_decoder_contract",
                "compare_decoder_quality",
                "check_decoder_missing_model_error",
                "sweep_decoder_candidate_quality",
            ]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["candidate_sweep_out"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/"
                "decoder_quality_sweep__l2_decoder_probability_sensitivity_v1.json"
            )
            assert decoder_inputs["candidate_sweep_dir"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/"
                "candidate_sweeps/l2_decoder_probability_sensitivity_v1"
            )
            assert decoder_inputs["candidate_sweep_grid"] == "decoder_probability_broad_v1"
            assert "distribution-dependent sensitivity map" in decoder_inputs["candidate_sweep_scope"]
            assert "--rough-grid decoder_probability_broad_v1" in work_item.command_manifest[3]["run"]
            assert decoder_inputs["candidate_sweep_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_probability_sensitivity",
            }


def test_generate_l2_campaign_task_adds_decoder_probability_fp_sensitivity_evidence() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        campaign_path = _write_campaign(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l2_campaign_task(
                session,
                Layer2CampaignGenerateRequest(
                    repo_root=str(repo_root),
                    campaign_path=campaign_path,
                    requested_by="@tester",
                    source_commit=source_commit,
                    item_id="l2_decoder_fp_probability_format_sweep_v1",
                    proposal_id="prop_l2_decoder_fp_probability_format_sweep_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_fp_probability_format_sweep_v1/proposal.json",
                    evaluation_mode="broad_ranking",
                    abstraction_layer="decoder_probability_fp_sensitivity",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[:4] == [
                "validate_decoder_contract",
                "compare_decoder_quality",
                "check_decoder_missing_model_error",
                "sweep_decoder_candidate_quality",
            ]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["candidate_sweep_out"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/"
                "decoder_quality_sweep__l2_decoder_fp_probability_format_sweep_v1.json"
            )
            assert decoder_inputs["candidate_sweep_dir"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/"
                "candidate_sweeps/l2_decoder_fp_probability_format_sweep_v1"
            )
            assert decoder_inputs["candidate_sweep_grid"] == "decoder_probability_fp_formats_v1"
            assert "fp-like format sensitivity map" in decoder_inputs["candidate_sweep_scope"]
            assert "--rough-grid decoder_probability_fp_formats_v1" in work_item.command_manifest[3]["run"]
            assert decoder_inputs["candidate_sweep_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_probability_fp_sensitivity",
            }


def test_generate_l2_campaign_task_recovers_metadata_from_evaluation_requests() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        campaign_path = _write_campaign(repo_root)
        source_commit = _init_git_repo(repo_root)
        proposal_dir = repo_root / "docs" / "developer_loop" / "prop_l2_demo_v1"
        proposal_dir.mkdir(parents=True, exist_ok=True)
        (proposal_dir / "evaluation_requests.json").write_text(
            json.dumps(
                {
                    "proposal_id": "prop_l2_demo_v1",
                    "requested_items": [
                        {
                            "item_id": "l2_demo_candidate_r1",
                            "task_type": "l2_campaign",
                            "evaluation_mode": "paired_comparison",
                            "abstraction_layer": "full_architecture",
                            "paired_baseline_item_id": "l2_demo_baseline_r1",
                            "depends_on_item_ids": ["l2_demo_baseline_r1"],
                            "requires_merged_inputs": True,
                            "requires_materialized_refs": True,
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l2_campaign_task(
                session,
                Layer2CampaignGenerateRequest(
                    repo_root=str(repo_root),
                    campaign_path=campaign_path,
                    item_id="l2_demo_candidate_r1",
                    requested_by="@tester",
                    proposal_id="prop_l2_demo_v1",
                    proposal_path="docs/developer_loop/prop_l2_demo_v1",
                ),
            )

            payload = session.query(WorkItem).filter_by(item_id=result.item_id).one().task_request.request_payload
            assert payload["handoff"]["pr_title"] == "eval: run layer2 campaign demo_campaign on nangate45"
            assert payload["developer_loop"]["evaluation"]["mode"] == "paired_comparison"
            assert payload["developer_loop"]["abstraction"]["layer"] == "full_architecture"
            assert payload["developer_loop"]["comparison"] == {
                "role": "candidate",
                "paired_baseline_item_id": "l2_demo_baseline_r1",
            }
            assert payload["developer_loop"]["dependencies"] == {
                "item_ids": ["l2_demo_baseline_r1"],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_blocks_when_dependency_not_merged() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        campaign_path = _write_campaign(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            baseline_task = TaskRequest(
                request_key="queue:l2_demo_baseline",
                source="test",
                requested_by="@tester",
                title="baseline",
                description="baseline",
                layer="layer2",
                flow="openroad",
                priority=1,
                request_payload={},
            )
            session.add(baseline_task)
            session.flush()
            session.add(
                WorkItem(
                    work_item_key="queue:l2_demo_baseline",
                    task_request_id=baseline_task.id,
                    item_id="l2_demo_baseline",
                    layer="layer2",
                    flow="openroad",
                    platform="nangate45",
                    task_type="l2_campaign",
                    state=WorkItemState.AWAITING_REVIEW,
                    priority=1,
                    source_mode="src_verilog",
                    input_manifest={},
                    command_manifest=[],
                    expected_outputs=[],
                    acceptance_rules=[],
                )
            )
            session.commit()

            result = generate_l2_campaign_task(
                session,
                Layer2CampaignGenerateRequest(
                    repo_root=str(repo_root),
                    campaign_path=campaign_path,
                    item_id="l2_demo_candidate",
                    requested_by="@tester",
                    proposal_id="prop_l2_demo_v1",
                    proposal_path="docs/developer_loop/prop_l2_demo_v1",
                    evaluation_mode="paired_comparison",
                    comparison_role="candidate",
                    paired_baseline_item_id="l2_demo_baseline",
                    depends_on_item_ids=["l2_demo_baseline"],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert work_item.state == WorkItemState.BLOCKED
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": ["l2_demo_baseline"],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_upserts_existing_item() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        campaign_path = _write_campaign(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            first = generate_l2_campaign_task(
                session,
                Layer2CampaignGenerateRequest(
                    repo_root=str(repo_root),
                    campaign_path=campaign_path,
                    item_id="l2_demo_campaign",
                    title="Layer2 demo",
                    requested_by="@tester",
                ),
            )
            second = generate_l2_campaign_task(
                session,
                Layer2CampaignGenerateRequest(
                    repo_root=str(repo_root),
                    campaign_path=campaign_path,
                    item_id="l2_demo_campaign",
                    title="Layer2 demo updated",
                    requested_by="@tester2",
                    run_physical=False,
                ),
            )

            assert first.status == "applied"
            assert second.status == "applied"
            work_item = session.query(WorkItem).filter_by(item_id="l2_demo_campaign").one()
            assert work_item.task_request.title == "Layer2 demo updated"
            assert work_item.task_request.requested_by == "@tester2"
            assert work_item.command_manifest[0]["name"] == "fetch_models"
            assert "--run_physical" not in work_item.command_manifest[2]["run"]
            assert (
                f"runs/campaigns/npu/demo_campaign/campaign__l2_demo_campaign.json"
                in work_item.expected_outputs
            )
            assert "runs/campaigns/npu/demo_campaign__l2_demo_campaign/objective_sweep.csv" not in work_item.expected_outputs
            assert "runs/campaigns/npu/demo_campaign__l2_demo_campaign/objective_sweep.md" not in work_item.expected_outputs


def test_generate_l2_campaign_task_requeues_failed_item_on_upsert() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        campaign_path = _write_campaign(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            generate_l2_campaign_task(
                session,
                Layer2CampaignGenerateRequest(
                    repo_root=str(repo_root),
                    campaign_path=campaign_path,
                    item_id="l2_demo_campaign",
                    requested_by="@tester",
                ),
            )
            work_item = session.query(WorkItem).filter_by(item_id="l2_demo_campaign").one()
            work_item.state = WorkItemState.FAILED
            work_item.queue_snapshot_path = "runs/eval_queue/openroad/failed/l2_demo_campaign.json"
            session.commit()

            generate_l2_campaign_task(
                session,
                Layer2CampaignGenerateRequest(
                    repo_root=str(repo_root),
                    campaign_path=campaign_path,
                    item_id="l2_demo_campaign",
                    requested_by="@tester2",
                ),
            )

            session.refresh(work_item)
            assert work_item.state == WorkItemState.DISPATCH_PENDING
            assert work_item.queue_snapshot_path is None


def test_generate_l2_campaign_task_defaults_source_commit_from_repo_head() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        campaign_path = _write_campaign(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with patch("control_plane.services.l2_task_generator.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["git", "-C", str(repo_root), "rev-parse", "HEAD"],
                returncode=0,
                stdout="feedface12345678\n",
                stderr="",
            )
            with Session(engine) as session:
                result = generate_l2_campaign_task(
                    session,
                    Layer2CampaignGenerateRequest(
                        repo_root=str(repo_root),
                        campaign_path=campaign_path,
                        requested_by="@tester",
                    ),
                )

                work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
                assert work_item.source_commit == "feedface12345678"
                assert work_item.task_request.source_commit == "feedface12345678"
                mock_run.assert_called_once()


def test_generate_l2_campaign_task_rejects_invalid_explicit_source_commit() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        campaign_path = _write_campaign(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            try:
                generate_l2_campaign_task(
                    session,
                    Layer2CampaignGenerateRequest(
                        repo_root=str(repo_root),
                        campaign_path=campaign_path,
                        requested_by="@tester",
                        source_commit="badbadbad",
                    ),
                )
            except Layer2TaskGenerationError as exc:
                assert "provided source_commit does not resolve to a commit" in str(exc)
            else:
                raise AssertionError("expected invalid source_commit failure")


def test_generate_l2_campaign_task_rejects_source_commit_not_pushed_to_origin() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        campaign_path = _write_campaign(repo_root)
        _init_git_repo(repo_root)
        extra = repo_root / "LOCAL_ONLY.txt"
        extra.write_text("local only\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo_root), "add", "LOCAL_ONLY.txt"], check=True, capture_output=True, text=True)
        subprocess.run(["git", "-C", str(repo_root), "commit", "-m", "local only"], check=True, capture_output=True, text=True)
        local_only_commit = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            try:
                generate_l2_campaign_task(
                    session,
                    Layer2CampaignGenerateRequest(
                        repo_root=str(repo_root),
                        campaign_path=campaign_path,
                        requested_by="@tester",
                        source_commit=local_only_commit,
                    ),
                )
            except Layer2TaskGenerationError as exc:
                assert "not reachable from origin" in str(exc)
            else:
                raise AssertionError("expected Layer2TaskGenerationError")

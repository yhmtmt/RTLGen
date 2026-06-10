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
            assert payload["source_requirement"]["required_sha"] == source_commit
            assert payload["source_requirement"]["required_ref"] == "origin/master"
            assert payload["source_requirement"]["requires_daemon_restart"] is True
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


def test_generate_l2_campaign_task_adds_decoder_distribution_robustness_evidence() -> None:
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
                    item_id="l2_decoder_distribution_robustness_v1",
                    proposal_id="prop_l2_decoder_distribution_robustness_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_distribution_robustness_v1/proposal.json",
                    evaluation_mode="broad_ranking",
                    abstraction_layer="decoder_distribution_robustness",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[:5] == [
                "generate_decoder_distribution_reference",
                "generate_decoder_distribution_candidate",
                "validate_decoder_distribution_contract",
                "compare_decoder_distribution_quality",
                "sweep_decoder_distribution_quality",
            ]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["dataset_manifest"] == "runs/datasets/llm_decoder_eval_tiny_v1/manifest_distribution_v1.json"
            assert decoder_inputs["candidate_sweep_grid"] == "decoder_distribution_robustness_v1"
            assert "entropy/margin regimes" in decoder_inputs["candidate_sweep_scope"]
            assert "--rough-grid decoder_distribution_robustness_v1" in work_item.command_manifest[4]["run"]
            assert decoder_inputs["candidate_sweep_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_distribution_robustness",
            }


def test_generate_l2_campaign_task_adds_decoder_survivor_prompt_stress_evidence() -> None:
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
                    item_id="l2_decoder_survivor_prompt_stress_v1",
                    proposal_id="prop_l2_decoder_survivor_prompt_stress_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_survivor_prompt_stress_v1/proposal.json",
                    evaluation_mode="focused_stress",
                    abstraction_layer="decoder_survivor_prompt_stress",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[:5] == [
                "generate_decoder_prompt_stress_reference",
                "generate_decoder_prompt_stress_candidate",
                "validate_decoder_prompt_stress_contract",
                "compare_decoder_prompt_stress_quality",
                "sweep_decoder_prompt_stress_quality",
            ]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["dataset_manifest"] == "runs/datasets/llm_decoder_eval_tiny_v1/manifest_prompt_stress_v1.json"
            assert decoder_inputs["candidate_sweep_grid"] == "decoder_survivor_prompt_stress_v1"
            assert "survived or bordered failure" in decoder_inputs["candidate_sweep_scope"]
            assert "--rough-grid decoder_survivor_prompt_stress_v1" in work_item.command_manifest[4]["run"]
            assert decoder_inputs["candidate_sweep_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_survivor_prompt_stress",
            }


def test_generate_l2_campaign_task_adds_decoder_survivor_cost_proxy_evidence() -> None:
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
                    item_id="l2_decoder_survivor_cost_proxy_v1",
                    proposal_id="prop_l2_decoder_survivor_cost_proxy_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_survivor_cost_proxy_v1/proposal.json",
                    evaluation_mode="cost_proxy",
                    abstraction_layer="decoder_survivor_cost_proxy",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[0] == "estimate_decoder_survivor_cost_proxy"
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert (
                decoder_inputs["source_sweep"]
                == "runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_survivor_prompt_stress_v1.json"
            )
            assert "relative planning proxy" in decoder_inputs["cost_proxy_scope"]
            assert "estimate_llm_decoder_survivor_cost.py" in work_item.command_manifest[0]["run"]
            assert decoder_inputs["cost_proxy_out"] in work_item.expected_outputs
            assert decoder_inputs["cost_proxy_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_survivor_cost_proxy",
            }


def test_generate_l2_campaign_task_adds_decoder_pwl_frontier_detail_evidence() -> None:
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
                    item_id="l2_decoder_pwl_frontier_detail_v1",
                    proposal_id="prop_l2_decoder_pwl_frontier_detail_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_pwl_frontier_detail_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_pwl_frontier_detail",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[0] == "estimate_decoder_pwl_frontier_detail"
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert (
                decoder_inputs["source_sweep"]
                == "runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_survivor_prompt_stress_v1.json"
            )
            assert (
                decoder_inputs["source_cost_proxy"]
                == "runs/datasets/llm_decoder_eval_tiny_v1/decoder_survivor_cost_proxy__l2_decoder_survivor_cost_proxy_v1.json"
            )
            assert "table footprint" in decoder_inputs["frontier_detail_scope"]
            assert "estimate_llm_decoder_pwl_frontier.py" in work_item.command_manifest[0]["run"]
            assert decoder_inputs["frontier_detail_out"] in work_item.expected_outputs
            assert decoder_inputs["frontier_detail_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_pwl_frontier_detail",
            }


def test_generate_l2_campaign_task_adds_decoder_q8_normalization_frontier_evidence() -> None:
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
                    item_id="l2_decoder_q8_normalization_frontier_v1",
                    proposal_id="prop_l2_decoder_q8_normalization_frontier_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_q8_normalization_frontier_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_q8_normalization_frontier",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[:6] == [
                "generate_decoder_q8_norm_reference",
                "generate_decoder_q8_norm_candidate",
                "validate_decoder_q8_norm_contract",
                "compare_decoder_q8_norm_quality",
                "sweep_decoder_q8_norm_frontier",
                "estimate_decoder_q8_norm_frontier",
            ]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["candidate_sweep_grid"] == "decoder_q8_normalization_frontier_v1"
            assert "quantized reciprocal" in decoder_inputs["candidate_sweep_scope"]
            assert "--rough-grid decoder_q8_normalization_frontier_v1" in work_item.command_manifest[4]["run"]
            assert "estimate_llm_decoder_q8_norm_frontier.py" in work_item.command_manifest[5]["run"]
            assert "--q8-recip-ppa control_plane/shadow_exports/l1_promotions/l1_decoder_q8_recip_norm_datapath_v1_r3.json" in work_item.command_manifest[5]["run"]
            assert (
                "--q8-exact-ppa control_plane/shadow_exports/l1_promotions/"
                "l1_prop_l1_softmax_rowwise_int8_r8_acc24_block_v1_nangate45_r1.json"
                in work_item.command_manifest[5]["run"]
            )
            assert (
                "--bf16-recip-ppa control_plane/shadow_exports/l1_promotions/"
                "l1_decoder_bf16_recip_norm_datapath_v1_r2.json"
                in work_item.command_manifest[5]["run"]
            )
            assert (
                decoder_inputs["q8_reciprocal_datapath_ppa"]
                == "control_plane/shadow_exports/l1_promotions/l1_decoder_q8_recip_norm_datapath_v1_r3.json"
            )
            assert (
                decoder_inputs["q8_exact_datapath_ppa"]
                == "control_plane/shadow_exports/l1_promotions/"
                "l1_prop_l1_softmax_rowwise_int8_r8_acc24_block_v1_nangate45_r1.json"
            )
            assert (
                decoder_inputs["bf16_reciprocal_datapath_ppa"]
                == "control_plane/shadow_exports/l1_promotions/l1_decoder_bf16_recip_norm_datapath_v1_r2.json"
            )
            assert decoder_inputs["frontier_out"] in work_item.expected_outputs
            assert decoder_inputs["frontier_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_q8_normalization_frontier",
            }


def test_generate_l2_campaign_task_adds_decoder_q8_normalization_distribution_evidence() -> None:
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
                    item_id="l2_decoder_q8_norm_distribution_robustness_v1",
                    proposal_id="prop_l2_decoder_q8_norm_distribution_robustness_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_q8_norm_distribution_robustness_v1/proposal.json",
                    evaluation_mode="broad_ranking",
                    abstraction_layer="decoder_q8_normalization_distribution",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[:6] == [
                "generate_decoder_q8_norm_distribution_reference",
                "generate_decoder_q8_norm_distribution_candidate",
                "validate_decoder_q8_norm_distribution_contract",
                "compare_decoder_q8_norm_distribution_quality",
                "sweep_decoder_q8_norm_distribution_frontier",
                "estimate_decoder_q8_norm_distribution_frontier",
            ]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["dataset_manifest"] == "runs/datasets/llm_decoder_eval_tiny_v1/manifest_distribution_v1.json"
            assert decoder_inputs["sample_file"] == "runs/datasets/llm_decoder_eval_tiny_v1/samples_distribution_v1.jsonl"
            assert decoder_inputs["candidate_sweep_grid"] == "decoder_q8_normalization_frontier_v1"
            assert "broader distribution robustness" in decoder_inputs["candidate_sweep_scope"]
            assert "--rough-grid decoder_q8_normalization_frontier_v1" in work_item.command_manifest[4]["run"]
            assert "estimate_llm_decoder_q8_norm_frontier.py" in work_item.command_manifest[5]["run"]
            assert (
                "--bf16-recip-ppa control_plane/shadow_exports/l1_promotions/"
                "l1_decoder_bf16_recip_norm_datapath_v1_r2.json"
                in work_item.command_manifest[5]["run"]
            )
            assert decoder_inputs["frontier_out"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/"
                "decoder_q8_norm_frontier__l2_decoder_q8_norm_distribution_robustness_v1.json"
            )
            assert decoder_inputs["frontier_out"] in work_item.expected_outputs
            assert decoder_inputs["frontier_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_q8_normalization_distribution",
            }


def test_generate_l2_campaign_task_adds_decoder_q8_normalization_distribution_broad_v2_evidence() -> None:
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
                    item_id="l2_decoder_q8_norm_distribution_broad_v2",
                    proposal_id="prop_l2_decoder_q8_norm_distribution_broad_v2",
                    proposal_path="docs/proposals/prop_l2_decoder_q8_norm_distribution_broad_v2/proposal.json",
                    evaluation_mode="broad_ranking",
                    abstraction_layer="decoder_q8_normalization_distribution_broad_v2",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[:6] == [
                "generate_decoder_q8_norm_distribution_v2_reference",
                "generate_decoder_q8_norm_distribution_v2_candidate",
                "validate_decoder_q8_norm_distribution_v2_contract",
                "compare_decoder_q8_norm_distribution_v2_quality",
                "sweep_decoder_q8_norm_distribution_v2_frontier",
                "estimate_decoder_q8_norm_distribution_v2_frontier",
            ]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["dataset_manifest"] == "runs/datasets/llm_decoder_eval_tiny_v1/manifest_distribution_v2.json"
            assert decoder_inputs["sample_file"] == "runs/datasets/llm_decoder_eval_tiny_v1/samples_distribution_v2.jsonl"
            assert decoder_inputs["reference_manifest"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/reference_distribution_v2_manifest.json"
            )
            assert decoder_inputs["candidate_manifest"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/candidate_distribution_v2_manifest.json"
            )
            assert decoder_inputs["candidate_sweep_grid"] == "decoder_q8_normalization_frontier_v1"
            assert "expanded v2 broad distribution" in decoder_inputs["candidate_sweep_scope"]
            assert "--dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest_distribution_v2.json" in (
                work_item.command_manifest[4]["run"]
            )
            assert decoder_inputs["frontier_out"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/"
                "decoder_q8_norm_frontier__l2_decoder_q8_norm_distribution_broad_v2.json"
            )
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_q8_normalization_distribution_broad_v2",
            }


def test_generate_l2_campaign_task_adds_decoder_quantization_outline_evidence() -> None:
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
                    item_id="l2_decoder_quantization_outline_v1",
                    proposal_id="prop_l2_decoder_quantization_outline_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_quantization_outline_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_quantization_outline",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert work_item.command_manifest[0]["name"] == "estimate_decoder_quantization_outline"
            assert "estimate_llm_decoder_quantization_outline.py" in work_item.command_manifest[0]["run"]
            assert "--fp-sweep runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_fp_probability_format_sweep_v1.json" in work_item.command_manifest[0]["run"]
            assert "--distribution-sweep runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_distribution_robustness_v1.json" in work_item.command_manifest[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["quantization_outline_out"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/decoder_quantization_outline__l2_decoder_quantization_outline_v1.json"
            )
            assert "avoid cross-category ranking" in decoder_inputs["quantization_outline_scope"]
            assert decoder_inputs["quantization_outline_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_quantization_outline",
            }


def test_generate_l2_campaign_task_adds_decoder_pwl_failure_diagnosis_evidence() -> None:
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
                    item_id="l2_decoder_pwl_failure_diagnosis_v1",
                    proposal_id="prop_l2_decoder_pwl_failure_diagnosis_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_pwl_failure_diagnosis_v1/proposal.json",
                    evaluation_mode="broad_ranking",
                    abstraction_layer="decoder_pwl_failure_diagnosis",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert work_item.command_manifest[0]["name"] == "diagnose_decoder_pwl_failures"
            assert "diagnose_llm_decoder_pwl_failures.py" in work_item.command_manifest[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["source_sweep"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/"
                "decoder_quality_sweep__l2_decoder_q8_norm_distribution_broad_v2.json"
            )
            assert decoder_inputs["sample_file"] == "runs/datasets/llm_decoder_eval_tiny_v1/samples_distribution_v2.jsonl"
            assert decoder_inputs["focus_samples"] == [
                "dist2_arith_three_plus_five",
                "dist2_sequence_months",
            ]
            assert decoder_inputs["diagnosis_out"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/"
                "decoder_pwl_failure_diagnosis__l2_decoder_pwl_failure_diagnosis_v1.json"
            )
            assert decoder_inputs["diagnosis_out"] in work_item.expected_outputs
            assert decoder_inputs["diagnosis_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_pwl_failure_diagnosis",
            }


def test_generate_l2_campaign_task_adds_decoder_bf16_pwl_recoverability_evidence() -> None:
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
                    item_id="l2_decoder_bf16_pwl_recoverability_v1",
                    proposal_id="prop_l2_decoder_bf16_pwl_recoverability_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_bf16_pwl_recoverability_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_bf16_pwl_recoverability",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert work_item.command_manifest[0]["name"] == "estimate_decoder_bf16_pwl_recoverability"
            assert "estimate_llm_decoder_bf16_recoverability.py" in work_item.command_manifest[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["source_sweep"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/"
                "decoder_quality_sweep__l2_decoder_q8_norm_distribution_broad_v2.json"
            )
            assert decoder_inputs["target_template"] == "grid_approx_pwl_bf16_path"
            assert "score-gap screen" in decoder_inputs["recoverability_scope"]
            assert decoder_inputs["recoverability_out"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/"
                "decoder_bf16_pwl_recoverability__l2_decoder_bf16_pwl_recoverability_v1.json"
            )
            assert decoder_inputs["recoverability_out"] in work_item.expected_outputs
            assert decoder_inputs["recoverability_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_bf16_pwl_recoverability",
            }


def test_generate_l2_campaign_task_adds_decoder_bf16_pwl_recovery_evidence() -> None:
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
                    item_id="l2_decoder_bf16_pwl_recovery_v1",
                    proposal_id="prop_l2_decoder_bf16_pwl_recovery_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_bf16_pwl_recovery_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_bf16_pwl_recovery",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[:6] == [
                "generate_decoder_bf16_pwl_recovery_reference",
                "generate_decoder_bf16_pwl_recovery_candidate",
                "validate_decoder_bf16_pwl_recovery_contract",
                "compare_decoder_bf16_pwl_recovery_quality",
                "sweep_decoder_bf16_pwl_recovery",
                "summarize_decoder_bf16_pwl_recovery",
            ]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["dataset_manifest"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/manifest_distribution_v2.json"
            )
            assert decoder_inputs["sample_file"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/samples_distribution_v2.jsonl"
            )
            assert decoder_inputs["candidate_sweep_grid"] == "decoder_bf16_pwl_recovery_v1"
            assert "logit tie-breaking" in decoder_inputs["recovery_scope"]
            assert "--rough-grid decoder_bf16_pwl_recovery_v1" in work_item.command_manifest[4]["run"]
            assert "summarize_llm_decoder_bf16_pwl_recovery.py" in work_item.command_manifest[5]["run"]
            assert decoder_inputs["recovery_out"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/"
                "decoder_bf16_pwl_recovery__l2_decoder_bf16_pwl_recovery_v1.json"
            )
            assert decoder_inputs["recovery_out"] in work_item.expected_outputs
            assert decoder_inputs["recovery_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_bf16_pwl_recovery",
            }


def test_generate_l2_campaign_task_adds_decoder_bf16_pwl_scale_probe_evidence() -> None:
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
                    item_id="l2_decoder_bf16_pwl_scale_probe_v1",
                    proposal_id="prop_l2_decoder_bf16_pwl_scale_probe_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_bf16_pwl_scale_probe_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_bf16_pwl_scale_probe",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[:6] == [
                "generate_decoder_bf16_pwl_scale_probe_reference",
                "generate_decoder_bf16_pwl_scale_probe_candidate",
                "validate_decoder_bf16_pwl_scale_probe_contract",
                "compare_decoder_bf16_pwl_scale_probe_quality",
                "sweep_decoder_bf16_pwl_scale_probe",
                "summarize_decoder_bf16_pwl_scale_probe",
            ]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["dataset_manifest"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/manifest_scale_proxy_v1.json"
            )
            assert decoder_inputs["sample_file"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/samples_scale_proxy_v1.jsonl"
            )
            assert decoder_inputs["candidate_sweep_grid"] == "decoder_bf16_pwl_scale_probe_v1"
            assert "scale-sensitivity screen" in decoder_inputs["scale_probe_scope"]
            assert "--rough-grid decoder_bf16_pwl_scale_probe_v1" in work_item.command_manifest[4]["run"]
            assert "summarize_llm_decoder_bf16_pwl_recovery.py" in work_item.command_manifest[5]["run"]
            assert decoder_inputs["scale_probe_out"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/"
                "decoder_bf16_pwl_scale_probe__l2_decoder_bf16_pwl_scale_probe_v1.json"
            )
            assert decoder_inputs["scale_probe_out"] in work_item.expected_outputs
            assert decoder_inputs["scale_probe_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_bf16_pwl_scale_probe",
            }


def test_generate_l2_campaign_task_adds_decoder_trained_tiny_quality_evidence() -> None:
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
                    item_id="l2_decoder_trained_tiny_quality_v1",
                    proposal_id="prop_l2_decoder_trained_tiny_quality_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_trained_tiny_quality_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_trained_tiny_quality",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[:6] == [
                "generate_decoder_trained_tiny_reference",
                "generate_decoder_trained_tiny_candidate",
                "validate_decoder_trained_tiny_contract",
                "compare_decoder_trained_tiny_quality",
                "sweep_decoder_trained_tiny_quality",
                "summarize_decoder_trained_tiny_quality",
            ]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["dataset_manifest"] == "runs/datasets/llm_decoder_eval_trained_tiny_v1/manifest.json"
            assert decoder_inputs["sample_file"] == "runs/datasets/llm_decoder_eval_trained_tiny_v1/samples.jsonl"
            assert decoder_inputs["candidate_sweep_grid"] == "decoder_bf16_pwl_scale_probe_v1"
            assert "first trained-weight GPT-2-family decoder smoke" in decoder_inputs["trained_quality_scope"]
            assert "--rough-grid decoder_bf16_pwl_scale_probe_v1" in work_item.command_manifest[4]["run"]
            assert "summarize_llm_decoder_bf16_pwl_recovery.py" in work_item.command_manifest[5]["run"]
            assert decoder_inputs["trained_quality_out"] == (
                "runs/datasets/llm_decoder_eval_trained_tiny_v1/"
                "decoder_trained_tiny_quality__l2_decoder_trained_tiny_quality_v1.json"
            )
            assert decoder_inputs["trained_quality_out"] in work_item.expected_outputs
            assert decoder_inputs["trained_quality_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_trained_tiny_quality",
            }


def test_generate_l2_campaign_task_adds_decoder_distilgpt2_quality_evidence() -> None:
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
                    item_id="l2_decoder_distilgpt2_quality_v1",
                    proposal_id="prop_l2_decoder_distilgpt2_quality_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_distilgpt2_quality_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_distilgpt2_quality",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[:7] == [
                "materialize_decoder_distilgpt2_contract",
                "generate_decoder_distilgpt2_reference",
                "generate_decoder_distilgpt2_candidate",
                "validate_decoder_distilgpt2_contract",
                "compare_decoder_distilgpt2_quality",
                "sweep_decoder_distilgpt2_quality",
                "summarize_decoder_distilgpt2_quality",
            ]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["dataset_manifest"] == "runs/datasets/llm_decoder_eval_distilgpt2_trained_v1/manifest.json"
            assert decoder_inputs["sample_file"] == "runs/datasets/llm_decoder_eval_distilgpt2_trained_v1/samples.jsonl"
            assert decoder_inputs["candidate_sweep_grid"] == "decoder_bf16_pwl_scale_probe_v1"
            assert decoder_inputs["materialized_model_contract"] == (
                "runs/models/llm_decoder_distilgpt2_trained_v1/model_contract.json"
            )
            assert "evaluator-local generated" in decoder_inputs["materialized_model_scope"]
            assert "bash npu/eval/run_hf_decoder_materializer.sh" in work_item.command_manifest[0]["run"]
            assert "--model-id distilgpt2" in work_item.command_manifest[0]["run"]
            assert "--rough-grid decoder_bf16_pwl_scale_probe_v1" in work_item.command_manifest[5]["run"]
            assert "summarize_llm_decoder_bf16_pwl_recovery.py" in work_item.command_manifest[6]["run"]
            assert decoder_inputs["trained_quality_out"] == (
                "runs/datasets/llm_decoder_eval_distilgpt2_trained_v1/"
                "decoder_distilgpt2_quality__l2_decoder_distilgpt2_quality_v1.json"
            )
            assert decoder_inputs["trained_quality_out"] in work_item.expected_outputs
            assert decoder_inputs["trained_quality_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_distilgpt2_quality",
            }


def test_generate_l2_campaign_task_adds_decoder_distilgpt2_prompt_stress_evidence() -> None:
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
                    item_id="l2_decoder_distilgpt2_prompt_stress_v1",
                    proposal_id="prop_l2_decoder_distilgpt2_prompt_stress_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_distilgpt2_prompt_stress_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_distilgpt2_prompt_stress",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[:7] == [
                "materialize_decoder_distilgpt2_prompt_stress_contract",
                "generate_decoder_distilgpt2_prompt_stress_reference",
                "generate_decoder_distilgpt2_prompt_stress_candidate",
                "validate_decoder_distilgpt2_prompt_stress_contract",
                "compare_decoder_distilgpt2_prompt_stress_quality",
                "sweep_decoder_distilgpt2_prompt_stress_quality",
                "summarize_decoder_distilgpt2_prompt_stress_quality",
            ]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["dataset_manifest"] == (
                "runs/datasets/llm_decoder_eval_distilgpt2_prompt_stress_v1/manifest.json"
            )
            assert decoder_inputs["sample_file"] == (
                "runs/datasets/llm_decoder_eval_distilgpt2_prompt_stress_v1/samples.jsonl"
            )
            assert decoder_inputs["candidate_sweep_grid"] == "decoder_bf16_pwl_scale_probe_v1"
            assert decoder_inputs["trained_quality_out"] == (
                "runs/datasets/llm_decoder_eval_distilgpt2_prompt_stress_v1/"
                "decoder_distilgpt2_prompt_stress__l2_decoder_distilgpt2_prompt_stress_v1.json"
            )
            assert "prompt/input-distribution stress" in decoder_inputs["trained_quality_scope"]
            assert "--dataset-id llm_decoder_eval_distilgpt2_prompt_stress_v1" in work_item.command_manifest[0]["run"]
            assert "bash npu/eval/run_hf_decoder_materializer.sh" in work_item.command_manifest[0]["run"]
            assert "--rough-grid decoder_bf16_pwl_scale_probe_v1" in work_item.command_manifest[5]["run"]
            assert decoder_inputs["trained_quality_out"] in work_item.expected_outputs
            assert decoder_inputs["trained_quality_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_distilgpt2_prompt_stress",
            }


def test_generate_l2_campaign_task_adds_decoder_gpt2_quality_evidence() -> None:
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
                    item_id="l2_decoder_gpt2_quality_v1",
                    proposal_id="prop_l2_decoder_gpt2_quality_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_gpt2_quality_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_gpt2_quality",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[:7] == [
                "materialize_decoder_gpt2_contract",
                "generate_decoder_gpt2_reference",
                "generate_decoder_gpt2_candidate",
                "validate_decoder_gpt2_contract",
                "compare_decoder_gpt2_quality",
                "sweep_decoder_gpt2_quality",
                "summarize_decoder_gpt2_quality",
            ]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["dataset_manifest"] == "runs/datasets/llm_decoder_eval_gpt2_trained_v1/manifest.json"
            assert decoder_inputs["sample_file"] == "runs/datasets/llm_decoder_eval_gpt2_trained_v1/samples.jsonl"
            assert decoder_inputs["candidate_sweep_grid"] == "decoder_bf16_pwl_scale_probe_v1"
            assert decoder_inputs["materialized_model_contract"] == (
                "runs/models/llm_decoder_gpt2_trained_v1/model_contract.json"
            )
            assert decoder_inputs["materialized_tokenizer_manifest"] == (
                "runs/tokenizers/llm_decoder_gpt2_trained_v1/manifest.json"
            )
            assert "--model-id gpt2" in work_item.command_manifest[0]["run"]
            assert "--contract-id llm_decoder_gpt2_trained_v1" in work_item.command_manifest[0]["run"]
            assert "--model-dir runs/models/llm_decoder_gpt2_trained_v1" in work_item.command_manifest[0]["run"]
            assert "--rough-grid decoder_bf16_pwl_scale_probe_v1" in work_item.command_manifest[5]["run"]
            assert decoder_inputs["trained_quality_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_trained_v1/"
                "decoder_gpt2_quality__l2_decoder_gpt2_quality_v1.json"
            )
            assert "12-layer GPT-2 checkpoint" in decoder_inputs["trained_quality_scope"]
            assert decoder_inputs["trained_quality_out"] in work_item.expected_outputs
            assert decoder_inputs["trained_quality_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_gpt2_quality",
            }


def test_generate_l2_campaign_task_adds_decoder_gpt2_prompt_stress_evidence() -> None:
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
                    item_id="l2_decoder_gpt2_prompt_stress_v1",
                    proposal_id="prop_l2_decoder_gpt2_prompt_stress_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_gpt2_prompt_stress_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_gpt2_prompt_stress",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[:7] == [
                "materialize_decoder_gpt2_prompt_stress_contract",
                "generate_decoder_gpt2_prompt_stress_reference",
                "generate_decoder_gpt2_prompt_stress_candidate",
                "validate_decoder_gpt2_prompt_stress_contract",
                "compare_decoder_gpt2_prompt_stress_quality",
                "sweep_decoder_gpt2_prompt_stress_quality",
                "summarize_decoder_gpt2_prompt_stress_quality",
            ]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["dataset_manifest"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/manifest.json"
            )
            assert decoder_inputs["sample_file"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/samples.jsonl"
            )
            assert decoder_inputs["candidate_sweep_grid"] == "decoder_bf16_pwl_scale_probe_v1"
            assert decoder_inputs["materialized_model_contract"] == (
                "runs/models/llm_decoder_gpt2_trained_v1/model_contract.json"
            )
            assert decoder_inputs["trained_quality_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_gpt2_prompt_stress__l2_decoder_gpt2_prompt_stress_v1.json"
            )
            assert "prompt/input-distribution stress" in decoder_inputs["trained_quality_scope"]
            assert "--dataset-id llm_decoder_eval_gpt2_prompt_stress_v1" in work_item.command_manifest[0]["run"]
            assert "--model-id gpt2" in work_item.command_manifest[0]["run"]
            assert "--rough-grid decoder_bf16_pwl_scale_probe_v1" in work_item.command_manifest[5]["run"]
            assert decoder_inputs["trained_quality_out"] in work_item.expected_outputs
            assert decoder_inputs["trained_quality_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_gpt2_prompt_stress",
            }


def test_generate_l2_campaign_task_adds_decoder_gpt2_tie_rank_frontier_evidence() -> None:
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
                    item_id="l2_decoder_gpt2_tie_rank_frontier_v1",
                    proposal_id="prop_l2_decoder_gpt2_tie_rank_frontier_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_gpt2_tie_rank_frontier_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_gpt2_tie_rank_frontier",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[0] == "estimate_decoder_gpt2_tie_rank_frontier"
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["source_recovery"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_gpt2_prompt_stress__l2_decoder_gpt2_prompt_stress_v1.json"
            )
            assert (
                decoder_inputs["bf16_score_tie_rank_datapath_ppa"]
                == "control_plane/shadow_exports/l1_promotions/l1_decoder_bf16_pwl_tie_rank_datapath_v1_r2.json"
            )
            assert decoder_inputs["frontier_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_gpt2_tie_rank_frontier__l2_decoder_gpt2_tie_rank_frontier_v1.json"
            )
            assert "hardware-plausibility gate" in decoder_inputs["frontier_scope"]
            assert "estimate_llm_decoder_tie_rank_frontier.py" in work_item.command_manifest[0]["run"]
            assert decoder_inputs["frontier_out"] in work_item.expected_outputs
            assert decoder_inputs["frontier_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_gpt2_tie_rank_frontier",
            }


def test_generate_l2_campaign_task_adds_decoder_gpt2_logit_rank_bypass_evidence() -> None:
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
                    item_id="l2_decoder_gpt2_logit_rank_bypass_v1",
                    proposal_id="prop_l2_decoder_gpt2_logit_rank_bypass_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_gpt2_logit_rank_bypass_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_gpt2_logit_rank_bypass",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[:7] == [
                "materialize_decoder_gpt2_logit_rank_bypass_contract",
                "generate_decoder_gpt2_logit_rank_bypass_reference",
                "generate_decoder_gpt2_logit_rank_bypass_candidate",
                "validate_decoder_gpt2_logit_rank_bypass_contract",
                "compare_decoder_gpt2_logit_rank_bypass_quality",
                "sweep_decoder_gpt2_logit_rank_bypass_quality",
                "summarize_decoder_gpt2_logit_rank_bypass",
            ]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["candidate_sweep_grid"] == "decoder_logit_rank_bypass_v1"
            assert decoder_inputs["rank_datapath_ppa"] == (
                "control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_datapath_v1_r2.json"
            )
            assert decoder_inputs["logit_rank_bypass_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_gpt2_logit_rank_bypass__l2_decoder_gpt2_logit_rank_bypass_v1.json"
            )
            assert "sampling modes remain out of scope" in decoder_inputs["logit_rank_bypass_scope"]
            assert "measured logit-only" in decoder_inputs["logit_rank_bypass_scope"]
            assert "--rough-grid decoder_logit_rank_bypass_v1" in work_item.command_manifest[5]["run"]
            assert "summarize_llm_decoder_logit_rank_bypass.py" in work_item.command_manifest[6]["run"]
            assert decoder_inputs["logit_rank_bypass_out"] in work_item.expected_outputs
            assert decoder_inputs["logit_rank_bypass_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_gpt2_logit_rank_bypass",
            }


def test_generate_l2_campaign_task_adds_decoder_logit_rank_streaming_hierarchy_evidence() -> None:
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
                    item_id="l2_decoder_logit_rank_streaming_hierarchy_v1",
                    proposal_id="prop_l2_decoder_logit_rank_streaming_hierarchy_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_logit_rank_streaming_hierarchy_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_logit_rank_streaming_hierarchy",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[0] == "estimate_decoder_logit_rank_streaming_hierarchy"
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["source_prompt_stress"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_gpt2_prompt_stress__l2_decoder_gpt2_prompt_stress_v1.json"
            )
            assert decoder_inputs["source_logit_rank_bypass"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_gpt2_logit_rank_bypass__l2_decoder_gpt2_logit_rank_bypass_v1.json"
            )
            assert decoder_inputs["rank_datapath_ppa"] == (
                "control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_datapath_v1_r2.json"
            )
            assert decoder_inputs["rank_scale_ppa"] == (
                "control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_scale_v1.json"
            )
            assert decoder_inputs["candidate_merge_ppa"] == (
                "control_plane/shadow_exports/l1_promotions/l1_decoder_candidate_stream_merge_fifo_v1.json"
            )
            assert decoder_inputs["boundary_ppa"] == (
                "control_plane/shadow_exports/l1_promotions/"
                "l1_decoder_logit_rank_r128_k1_pin_perimeter_bound_v1.json"
            )
            assert decoder_inputs["streaming_hierarchy_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_logit_rank_streaming_hierarchy__l2_decoder_logit_rank_streaming_hierarchy_v1.json"
            )
            assert "avoids full-vocabulary probability materialization" in decoder_inputs["streaming_hierarchy_scope"]
            assert "estimate_llm_decoder_logit_rank_streaming_hierarchy.py" in work_item.command_manifest[0]["run"]
            assert "--scale-ppa control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_scale_v1.json" in work_item.command_manifest[0]["run"]
            assert "--candidate-merge-ppa control_plane/shadow_exports/l1_promotions/l1_decoder_candidate_stream_merge_fifo_v1.json" in work_item.command_manifest[0]["run"]
            assert "--boundary-ppa control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_r128_k1_pin_perimeter_bound_v1.json" in work_item.command_manifest[0]["run"]
            assert "--out runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_logit_rank_streaming_hierarchy__l2_decoder_logit_rank_streaming_hierarchy_v1.json" in work_item.command_manifest[0]["run"]
            assert "--out-md runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_logit_rank_streaming_hierarchy__l2_decoder_logit_rank_streaming_hierarchy_v1.md" in work_item.command_manifest[0]["run"]
            assert decoder_inputs["streaming_hierarchy_out"] in work_item.expected_outputs
            assert decoder_inputs["streaming_hierarchy_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_logit_rank_streaming_hierarchy",
            }


def test_generate_l2_campaign_task_adds_decoder_logit_rank_streaming_overlap_evidence() -> None:
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
                    item_id="l2_decoder_logit_rank_streaming_overlap_v1",
                    proposal_id="prop_l2_decoder_logit_rank_streaming_overlap_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_logit_rank_streaming_overlap_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_logit_rank_streaming_overlap",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[0] == "estimate_decoder_logit_rank_streaming_overlap"
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["rank_datapath_ppa"] == (
                "control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_datapath_v1_r2.json"
            )
            assert decoder_inputs["rank_scale_ppa"] == (
                "control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_scale_v1.json"
            )
            assert decoder_inputs["candidate_merge_ppa"] == (
                "control_plane/shadow_exports/l1_promotions/l1_decoder_candidate_stream_merge_fifo_v1.json"
            )
            assert decoder_inputs["boundary_ppa"] == (
                "control_plane/shadow_exports/l1_promotions/"
                "l1_decoder_logit_rank_r128_k1_pin_perimeter_bound_v1.json"
            )
            assert decoder_inputs["memory_model"] == {
                "memory_bandwidth_bytes_per_cycle": 64,
                "sram_metrics_json": "runs/designs/sram/minimal_v0_2_draft/sram_metrics.json",
                "vocab_size_list": [50257, 100000, 200000],
                "producer_lanes_list": [8, 16, 32, 64, 128],
                "sram_read_energy_pj_per_byte": 0.05,
                "sram_write_energy_pj_per_byte": 0.07,
                "noc_hops": 2,
                "noc_energy_pj_per_byte_hop": 0.02,
                "source": "sram_metrics_json_plus_planning_noc",
                "sram_source": "cacti_estimated_nangate45_minimal_v0_2_draft",
                "noc_source": "planning_default_not_literature_backed",
            }
            assert decoder_inputs["streaming_overlap_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_logit_rank_streaming_overlap__l2_decoder_logit_rank_streaming_overlap_v1.json"
            )
            assert "measured candidate-stream merge/FIFO PPA" in decoder_inputs["streaming_overlap_scope"]
            assert "perf-sim/RTL equivalence observables" in decoder_inputs["streaming_overlap_scope"]
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_logit_rank_streaming_hierarchy.py" in run
            assert "--candidate-merge-ppa control_plane/shadow_exports/l1_promotions/l1_decoder_candidate_stream_merge_fifo_v1.json" in run
            assert "--boundary-ppa control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_r128_k1_pin_perimeter_bound_v1.json" in run
            assert "--vocab-size-list 50257,100000,200000" in run
            assert "--producer-lanes-list 8,16,32,64,128" in run
            assert "--top-k-list 1,4" in run
            assert "--producer-ii-cycles-list 1,2" in run
            assert "--candidate-fifo-depth-groups-list 16,256,4096" in run
            assert "--sram-metrics-json runs/designs/sram/minimal_v0_2_draft/sram_metrics.json" in run
            assert "--noc-hops 2" in run
            assert "--memory-bandwidth-bytes-per-cycle 64" in run
            assert decoder_inputs["streaming_overlap_out"] in work_item.expected_outputs
            assert decoder_inputs["streaming_overlap_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_logit_rank_streaming_overlap",
            }


def test_generate_l2_campaign_task_adds_decoder_logit_rank_streaming_producer_integrated_evidence() -> None:
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
                    item_id="l2_decoder_logit_rank_streaming_producer_integrated_v1",
                    proposal_id="prop_l2_decoder_logit_rank_streaming_producer_integrated_v1",
                    proposal_path=(
                        "docs/proposals/prop_l2_decoder_logit_rank_streaming_producer_integrated_v1/"
                        "proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_logit_rank_streaming_producer_integrated",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[0] == "estimate_decoder_logit_rank_streaming_producer_integrated"
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["producer_integrated_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_logit_rank_streaming_producer_integrated__"
                "l2_decoder_logit_rank_streaming_producer_integrated_v1.json"
            )
            assert decoder_inputs["memory_model"]["producer_interface_focus_lanes"] == [64, 128]
            assert "exposed-pin macro-boundary PPA diagnostic-only" in decoder_inputs["producer_integrated_scope"]
            assert "perf-sim/RTL equivalence observables" in decoder_inputs["producer_integrated_scope"]
            run = work_item.command_manifest[0]["run"]
            assert "--producer-interface-focus-lanes 64,128" in run
            assert "--producer-lanes-list 8,16,32,64,128" in run
            assert "--boundary-ppa control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_r128_k1_pin_perimeter_bound_v1.json" in run
            assert decoder_inputs["producer_integrated_out"] in work_item.expected_outputs
            assert decoder_inputs["producer_integrated_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_logit_rank_streaming_producer_integrated",
            }


def test_generate_l2_campaign_task_adds_decoder_output_projection_service_evidence() -> None:
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
                    item_id="l2_decoder_output_projection_service_v1",
                    proposal_id="prop_l2_decoder_output_projection_service_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_output_projection_service_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_output_projection_service",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert work_item.command_manifest[0]["name"] == "estimate_decoder_output_projection_service"
            assert "--mode producer_service" in work_item.command_manifest[0]["run"]
            assert decoder_inputs["producer_service_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_output_projection_service__l2_decoder_output_projection_service_v1.json"
            )
            assert "Stage-serialized output-projection producer service model" in decoder_inputs["producer_service_scope"]
            assert decoder_inputs["producer_service_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_output_projection_service",
            }


def test_generate_l2_campaign_task_adds_decoder_producer_ranker_coupled_noc_evidence() -> None:
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
                    item_id="l2_decoder_producer_ranker_coupled_noc_v1",
                    proposal_id="prop_l2_decoder_producer_ranker_coupled_noc_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_producer_ranker_coupled_noc_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_producer_ranker_coupled_noc",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert work_item.command_manifest[0]["name"] == "estimate_decoder_producer_ranker_coupled_noc"
            run = work_item.command_manifest[0]["run"]
            assert "--mode coupled_noc" in run
            assert "--memory-share-list 1.0,0.5,0.25" in run
            assert "--producer-control-boundary" in run
            assert "l2_decoder_output_projection_producer_event_scoreboard_v1.json" in run
            assert "--producer-physical-boundary" in run
            assert "l2_decoder_output_projection_producer_pnr_nm16_v1.json" in run
            assert decoder_inputs["producer_ranker_coupled_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_producer_ranker_coupled_noc__l2_decoder_producer_ranker_coupled_noc_v1.json"
            )
            assert "shared NoC/memory bandwidth shares" in decoder_inputs["producer_ranker_coupled_scope"]
            assert "producer-control synthesis evidence" in decoder_inputs["producer_ranker_coupled_scope"]
            assert "nm16 producer-wrapper physical" in decoder_inputs["producer_ranker_coupled_scope"]
            assert decoder_inputs["producer_control_boundary"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_output_projection_producer_softmax_event_ablation__"
                "l2_decoder_output_projection_producer_event_scoreboard_v1.json"
            )
            assert decoder_inputs["producer_physical_boundary"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_output_projection_producer_pnr_feasibility__"
                "l2_decoder_output_projection_producer_pnr_nm16_v1.json"
            )
            assert decoder_inputs["producer_ranker_coupled_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_producer_ranker_coupled_noc",
            }


def test_generate_l2_campaign_task_adds_decoder_producer_ranker_service_compatibility() -> None:
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
                    item_id="l2_decoder_producer_ranker_service_compatibility_v1",
                    proposal_id="prop_l2_decoder_producer_ranker_service_compatibility_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_producer_ranker_service_compatibility_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_producer_ranker_service_compatibility",
                    expected_direction="iterate",
                    comparison_role="producer_ranker_service",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert work_item.command_manifest[0]["name"] == (
                "estimate_decoder_producer_ranker_service_compatibility"
            )
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_producer_ranker_service_compatibility.py" in run
            assert "--producer-service" in run
            assert "--serial-ranker" in run
            assert "--rank-tree" in run
            assert decoder_inputs["producer_ranker_service_compatibility_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_producer_ranker_service_compatibility__"
                "l2_decoder_producer_ranker_service_compatibility_v1.json"
            )
            assert decoder_inputs["serial_ranker_architecture"].endswith(
                "l2_decoder_serial_ranker_architecture_v1.json"
            )
            assert "single-r64 and banked-r64" in decoder_inputs[
                "producer_ranker_service_compatibility_scope"
            ]
            assert decoder_inputs["producer_ranker_service_compatibility_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_producer_ranker_service_compatibility",
            }


def test_generate_l2_campaign_task_adds_decoder_serial_ranker_producer_replay() -> None:
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
                    item_id="l2_decoder_serial_ranker_producer_replay_v1",
                    proposal_id="prop_l2_decoder_serial_ranker_producer_replay_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_serial_ranker_producer_replay_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_serial_ranker_producer_replay",
                    expected_direction="iterate",
                    comparison_role="producer_ranker_service",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:2]] == [
                "build_generator",
                "probe_decoder_serial_ranker_producer_replay"
            ]
            run = work_item.command_manifest[1]["run"]
            assert "probe_llm_decoder_serial_ranker_producer_replay.py" in run
            assert "--merge-config" in run
            assert "--lanes-per-cycle 1,2,4" in run
            assert "--producer-ii-cycles 16,33,65,384" in run
            assert decoder_inputs["serial_ranker_producer_replay_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_serial_ranker_producer_replay__"
                "l2_decoder_serial_ranker_producer_replay_v1.json"
            )
            assert decoder_inputs["producer_ranker_service_compatibility"].endswith(
                "l2_decoder_producer_ranker_service_compatibility_v1.json"
            )
            assert "full-token top-1 equivalence" in decoder_inputs[
                "serial_ranker_producer_replay_scope"
            ]
            assert decoder_inputs["serial_ranker_producer_replay_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_serial_ranker_producer_replay",
            }


def test_generate_l2_campaign_task_adds_decoder_serial_lpc1_producer_coupled_wrapper() -> None:
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
                    item_id="l2_decoder_serial_lpc1_producer_coupled_wrapper_v1",
                    proposal_id="prop_l2_decoder_serial_lpc1_producer_coupled_wrapper_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_serial_lpc1_producer_coupled_wrapper_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_serial_lpc1_producer_coupled_wrapper",
                    expected_direction="iterate",
                    comparison_role="producer_ranker_service",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:2]] == [
                "build_generator",
                "promote_decoder_serial_lpc1_producer_wrapper",
            ]
            run = work_item.command_manifest[1]["run"]
            assert "promote_llm_decoder_serial_lpc1_producer_wrapper.py" in run
            assert "--lanes-per-cycle 1" in run
            assert "--producer-ii-cycles 384" in run
            assert decoder_inputs["serial_lpc1_producer_coupled_wrapper_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_serial_lpc1_producer_coupled_wrapper__"
                "l2_decoder_serial_lpc1_producer_coupled_wrapper_v1.json"
            )
            assert decoder_inputs["serial_ranker_producer_replay"].endswith(
                "l2_decoder_serial_ranker_producer_replay_v1.json"
            )
            assert "selected producer II=384" in decoder_inputs[
                "serial_lpc1_producer_coupled_wrapper_scope"
            ]
            assert decoder_inputs["serial_lpc1_producer_coupled_wrapper_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_serial_lpc1_producer_coupled_wrapper",
            }


def test_generate_l2_campaign_task_adds_decoder_output_projection_cadence_sensitivity() -> None:
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
                    item_id="l2_decoder_output_projection_cadence_sensitivity_v1",
                    proposal_id="prop_l2_decoder_output_projection_cadence_sensitivity_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_output_projection_cadence_sensitivity_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_output_projection_cadence_sensitivity",
                    expected_direction="iterate",
                    comparison_role="producer_ranker_service",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert work_item.command_manifest[0]["name"] == (
                "estimate_decoder_output_projection_cadence_sensitivity"
            )
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_output_projection_cadence_sensitivity.py" in run
            assert "--weight-cache-hit-rate-list 0.0,0.5,0.9,1.0" in run
            assert decoder_inputs["output_projection_cadence_sensitivity_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_output_projection_cadence_sensitivity__"
                "l2_decoder_output_projection_cadence_sensitivity_v1.json"
            )
            assert decoder_inputs["serial_lpc1_producer_coupled_wrapper"].endswith(
                "l2_decoder_serial_lpc1_producer_coupled_wrapper_v1.json"
            )
            assert "resident or cache-backed output weights" in decoder_inputs[
                "output_projection_cadence_sensitivity_scope"
            ]
            assert decoder_inputs["output_projection_cadence_sensitivity_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_output_projection_cadence_sensitivity",
            }


def test_generate_l2_campaign_task_adds_decoder_resident_weight_ranker_fallback() -> None:
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
                    item_id="l2_decoder_resident_weight_ranker_fallback_v1",
                    proposal_id="prop_l2_decoder_resident_weight_ranker_fallback_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_resident_weight_ranker_fallback_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_resident_weight_ranker_fallback",
                    expected_direction="iterate",
                    comparison_role="producer_ranker_service",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert work_item.command_manifest[0]["name"] == (
                "estimate_decoder_resident_weight_ranker_fallback"
            )
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_resident_weight_ranker_fallback.py" in run
            assert "--small-buffer-tiles 32" in run
            assert decoder_inputs["resident_weight_ranker_fallback_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_resident_weight_ranker_fallback__"
                "l2_decoder_resident_weight_ranker_fallback_v1.json"
            )
            assert decoder_inputs["output_projection_cadence_sensitivity"].endswith(
                "l2_decoder_output_projection_cadence_sensitivity_v1.json"
            )
            assert decoder_inputs["rank_tree_architecture"].endswith(
                "l2_decoder_rank_tree_architecture_v1.json"
            )
            assert "resident-weight producer cadences" in decoder_inputs[
                "resident_weight_ranker_fallback_scope"
            ]
            assert decoder_inputs["resident_weight_ranker_fallback_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_resident_weight_ranker_fallback",
            }


def test_generate_l2_campaign_task_adds_decoder_resident_ranktree_fallback_promotion() -> None:
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
                    item_id="l2_decoder_resident_ranktree_fallback_promotion_v1",
                    proposal_id="prop_l2_decoder_resident_ranktree_fallback_promotion_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_resident_ranktree_fallback_promotion_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_resident_ranktree_fallback_promotion",
                    expected_direction="promote",
                    comparison_role="producer_ranker_service",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert work_item.command_manifest[0]["name"] == (
                "promote_decoder_resident_ranktree_fallback"
            )
            run = work_item.command_manifest[0]["run"]
            assert "promote_llm_decoder_resident_ranktree_fallback.py" in run
            assert decoder_inputs["resident_ranktree_fallback_promotion_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_resident_ranktree_fallback_promotion__"
                "l2_decoder_resident_ranktree_fallback_promotion_v1.json"
            )
            assert decoder_inputs["resident_weight_ranker_fallback"].endswith(
                "l2_decoder_resident_weight_ranker_fallback_v1.json"
            )
            assert decoder_inputs["rank_tree_architecture"].endswith(
                "l2_decoder_rank_tree_architecture_v1.json"
            )
            assert "radix-4 r64 rank-tree" in decoder_inputs[
                "resident_ranktree_fallback_promotion_scope"
            ]
            assert decoder_inputs["resident_ranktree_fallback_promotion_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_resident_ranktree_fallback_promotion",
            }


def test_generate_l2_campaign_task_adds_decoder_output_projection_ranker_policy() -> None:
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
                    item_id="l2_decoder_output_projection_ranker_policy_v1",
                    proposal_id="prop_l2_decoder_output_projection_ranker_policy_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_output_projection_ranker_policy_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_output_projection_ranker_policy",
                    expected_direction="promote",
                    comparison_role="producer_ranker_service",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert work_item.command_manifest[0]["name"] == (
                "promote_decoder_output_projection_ranker_policy"
            )
            run = work_item.command_manifest[0]["run"]
            assert "promote_llm_decoder_output_projection_ranker_policy.py" in run
            assert decoder_inputs["output_projection_ranker_policy_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_output_projection_ranker_policy__"
                "l2_decoder_output_projection_ranker_policy_v1.json"
            )
            assert decoder_inputs["serial_lpc1_producer_coupled_wrapper"].endswith(
                "l2_decoder_serial_lpc1_producer_coupled_wrapper_v1.json"
            )
            assert decoder_inputs["resident_ranktree_fallback_promotion"].endswith(
                "l2_decoder_resident_ranktree_fallback_promotion_v1.json"
            )
            assert "ranker selection policy" in decoder_inputs[
                "output_projection_ranker_policy_scope"
            ]
            assert decoder_inputs["output_projection_ranker_policy_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_output_projection_ranker_policy",
            }


def test_generate_l2_campaign_task_adds_decoder_output_projection_ranker_wrapper_contract() -> None:
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
                    item_id="l2_decoder_output_projection_ranker_wrapper_contract_v1",
                    proposal_id="prop_l2_decoder_output_projection_ranker_wrapper_contract_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_output_projection_ranker_wrapper_contract_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_output_projection_ranker_wrapper_contract",
                    expected_direction="iterate",
                    comparison_role="producer_ranker_service",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:2]] == [
                "build_generator",
                "probe_decoder_output_projection_ranker_wrapper_contract",
            ]
            run = work_item.command_manifest[1]["run"]
            assert "probe_llm_decoder_output_projection_ranker_wrapper_contract.py" in run
            assert decoder_inputs["output_projection_ranker_wrapper_contract_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_output_projection_ranker_wrapper_contract__"
                "l2_decoder_output_projection_ranker_wrapper_contract_v1.json"
            )
            assert decoder_inputs["output_projection_ranker_policy"].endswith(
                "l2_decoder_output_projection_ranker_policy_v1.json"
            )
            assert decoder_inputs["serial_lpc1_producer_coupled_wrapper"].endswith(
                "l2_decoder_serial_lpc1_producer_coupled_wrapper_v1.json"
            )
            assert "banked-r64 composition" in decoder_inputs[
                "output_projection_ranker_wrapper_contract_scope"
            ]
            assert decoder_inputs["output_projection_ranker_wrapper_contract_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_output_projection_ranker_wrapper_contract",
            }


def test_generate_l2_campaign_task_adds_decoder_output_projection_ranker_wrapper_physical() -> None:
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
                    item_id="l2_decoder_output_projection_ranker_wrapper_physical_v1",
                    proposal_id="prop_l2_decoder_output_projection_ranker_wrapper_physical_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_output_projection_ranker_wrapper_physical_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_output_projection_ranker_wrapper_physical",
                    expected_direction="iterate",
                    comparison_role="producer_ranker_service",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:3]] == [
                "build_generator",
                "probe_decoder_output_projection_ranker_wrapper_physical",
                "build_runs_index",
            ]
            run = work_item.command_manifest[1]["run"]
            assert "probe_llm_decoder_output_projection_ranker_wrapper_physical.py" in run
            assert "--producer-lanes 64,128" in run
            assert decoder_inputs["output_projection_ranker_wrapper_physical_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_output_projection_ranker_wrapper_physical__"
                "l2_decoder_output_projection_ranker_wrapper_physical_v1.json"
            )
            assert decoder_inputs["output_projection_ranker_wrapper_contract"].endswith(
                "l2_decoder_output_projection_ranker_wrapper_contract_v1.json"
            )
            assert "wrapper mux/control" in decoder_inputs[
                "output_projection_ranker_wrapper_physical_scope"
            ]
            assert "runs/index.csv" in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_output_projection_ranker_wrapper_physical",
            }


def test_generate_l2_campaign_task_adds_decoder_output_projection_producer_ranker_integration() -> None:
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
                    item_id="l2_decoder_output_projection_producer_ranker_integration_v1",
                    proposal_id="prop_l2_decoder_output_projection_producer_ranker_integration_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_output_projection_producer_ranker_integration_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_output_projection_producer_ranker_integration",
                    expected_direction="iterate",
                    comparison_role="producer_ranker_service",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "estimate_decoder_output_projection_producer_ranker_integration",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_output_projection_integrated_breakdown.py" in run
            assert "--lane-map fp16_nm1=64,fp16_nm2=128" in run
            assert decoder_inputs["output_projection_producer_ranker_integration_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_output_projection_producer_ranker_integration__"
                "l2_decoder_output_projection_producer_ranker_integration_v1.json"
            )
            assert decoder_inputs["output_projection_ranker_wrapper_physical"].endswith(
                "l2_decoder_output_projection_ranker_wrapper_physical_v1.json"
            )
            assert "Additively account" in decoder_inputs[
                "output_projection_producer_ranker_integration_scope"
            ]
            assert decoder_inputs["output_projection_producer_ranker_integration_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_output_projection_producer_ranker_integration",
            }


def test_generate_l2_campaign_task_adds_decoder_producer_ranker_policy_calibration() -> None:
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
                    item_id="l2_decoder_producer_ranker_policy_calibration_v1",
                    proposal_id="prop_l2_decoder_producer_ranker_policy_calibration_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_producer_ranker_policy_calibration_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_producer_ranker_policy_calibration",
                    expected_direction="iterate",
                    comparison_role="frontier_synthesis",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "calibrate_decoder_producer_ranker_policy_service",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "calibrate_llm_decoder_producer_ranker_policy_service.py" in run
            assert "--coupled-report" in run
            assert "l2_decoder_frontier_synthesis_integrated_v1.json" in run
            assert decoder_inputs["producer_ranker_policy_calibration_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_producer_ranker_policy_calibration__"
                "l2_decoder_producer_ranker_policy_calibration_v1.json"
            )
            assert "stale ranker hierarchy latency" in decoder_inputs[
                "producer_ranker_policy_calibration_scope"
            ]
            assert decoder_inputs["producer_ranker_policy_calibration_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_producer_ranker_policy_calibration",
            }


def test_generate_l2_campaign_task_adds_decoder_stage_breakdown_evidence() -> None:
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
                    item_id="l2_decoder_stage_breakdown_v1",
                    proposal_id="prop_l2_decoder_stage_breakdown_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_stage_breakdown_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_stage_breakdown",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert work_item.command_manifest[0]["name"] == "estimate_decoder_stage_breakdown"
            run = work_item.command_manifest[0]["run"]
            assert "--sequence-length-list 128,512,2048,8192" in run
            assert "--memory-bandwidth-bytes-per-cycle-list 64,256" in run
            assert decoder_inputs["stage_breakdown_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_stage_breakdown__l2_decoder_stage_breakdown_v1.json"
            )
            assert "attention, MLP, output projection, and ranker" in decoder_inputs["stage_breakdown_scope"]
            assert decoder_inputs["stage_breakdown_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_stage_breakdown",
            }


def test_generate_l2_campaign_task_adds_decoder_attention_kv_memory_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_memory_v1",
                    proposal_id="prop_l2_decoder_attention_kv_memory_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_attention_kv_memory_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_attention_kv_memory",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert work_item.command_manifest[0]["name"] == "estimate_decoder_attention_kv_memory"
            run = work_item.command_manifest[0]["run"]
            assert "--sequence-length-list 128,512,2048,8192,32768,131072" in run
            assert "--kv-memory-tier-list local_sram,shared_sram,hbm,remote_hbm" in run
            assert "--macs-per-cycle-list 8192,32768,131072,524288" in run
            assert "--kv-sharing-list mha,gqa4,gqa8,mqa" in run
            assert "--noc-hops-list 1,2,4,8" in run
            assert "--noc-bandwidth-bytes-per-cycle 4096" in run
            assert "--measured-tile-metrics " in run
            assert "attention_kv_tile_hd128_kv16_l64_b512_wrapper/metrics.csv" in run
            assert decoder_inputs["attention_kv_memory_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_memory__l2_decoder_attention_kv_memory_v1.json"
            )
            assert "KV-cache memory tier" in decoder_inputs["attention_kv_memory_scope"]
            assert (
                "runs/designs/activations/attention_kv_tile_hd64_kv4_l16_b128_wrapper/metrics.csv"
                in decoder_inputs["measured_tile_metrics"]
            )
            assert decoder_inputs["attention_kv_memory_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_kv_memory",
            }


def test_generate_l2_campaign_task_adds_decoder_frontier_synthesis_evidence() -> None:
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
                    item_id="l2_decoder_frontier_synthesis_v1",
                    proposal_id="prop_l2_decoder_frontier_synthesis_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_frontier_synthesis_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_frontier_synthesis",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[:4] == [
                "estimate_decoder_stage_breakdown",
                "estimate_decoder_attention_kv_memory",
                "estimate_decoder_producer_ranker_coupled_noc",
                "synthesize_decoder_frontier",
            ]
            synth_run = work_item.command_manifest[3]["run"]
            assert "synthesize_llm_decoder_frontier.py" in synth_run
            assert "--stage-breakdown" in synth_run
            assert "--attention-kv-memory" in synth_run
            assert "--producer-ranker-coupled" in synth_run
            assert decoder_inputs["decoder_frontier_synthesis_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_frontier_synthesis__l2_decoder_frontier_synthesis_v1.json"
            )
            assert "measured attention/KV tile-calibrated" in decoder_inputs["decoder_frontier_synthesis_scope"]
            assert decoder_inputs["decoder_frontier_synthesis_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_frontier_synthesis",
            }


def test_generate_l2_campaign_task_adds_decoder_frontier_synthesis_integrated_evidence() -> None:
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
                    item_id="l2_decoder_frontier_synthesis_integrated_v1",
                    proposal_id="prop_l2_decoder_frontier_synthesis_integrated_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_frontier_synthesis_integrated_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_frontier_synthesis_integrated",
                    expected_direction="iterate",
                    comparison_role="frontier_synthesis",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[:5] == [
                "estimate_decoder_stage_breakdown",
                "estimate_decoder_attention_kv_memory",
                "estimate_decoder_producer_ranker_coupled_noc",
                "estimate_decoder_output_projection_producer_ranker_integration",
                "synthesize_decoder_frontier",
            ]
            synth_run = work_item.command_manifest[4]["run"]
            assert "--producer-ranker-integration" in synth_run
            assert decoder_inputs["decoder_frontier_synthesis_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_frontier_synthesis__l2_decoder_frontier_synthesis_integrated_v1.json"
            )
            assert "measured additive" in decoder_inputs["decoder_frontier_synthesis_scope"]
            assert decoder_inputs["output_projection_producer_ranker_integration_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_frontier_synthesis_integrated",
            }


def test_generate_l2_campaign_task_adds_decoder_frontier_synthesis_policy_calibrated() -> None:
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
                    item_id="l2_decoder_frontier_synthesis_policy_calibrated_v1",
                    proposal_id="prop_l2_decoder_frontier_synthesis_policy_calibrated_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_frontier_synthesis_policy_calibrated_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_frontier_synthesis_policy_calibrated",
                    expected_direction="iterate",
                    comparison_role="frontier_synthesis",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "synthesize_decoder_frontier_policy_calibrated",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "--producer-ranker-policy-calibration" in run
            assert "l2_decoder_stage_breakdown_large_array_v2.json" in run
            assert "l2_decoder_attention_kv_memory_131k_v1.json" in run
            assert "l2_decoder_producer_ranker_policy_calibration_v1.json" in run
            assert decoder_inputs["decoder_frontier_synthesis_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_frontier_synthesis__l2_decoder_frontier_synthesis_policy_calibrated_v1.json"
            )
            assert "measured policy-wrapper" in decoder_inputs["decoder_frontier_synthesis_scope"]
            assert decoder_inputs["decoder_frontier_synthesis_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_frontier_synthesis_policy_calibrated",
            }


def test_generate_l2_campaign_task_adds_decoder_output_projection_producer_memory_hierarchy() -> None:
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
                    item_id="l2_decoder_output_projection_producer_memory_hierarchy_v1",
                    proposal_id="prop_l2_decoder_output_projection_producer_memory_hierarchy_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_output_projection_producer_memory_hierarchy_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_output_projection_producer_memory_hierarchy",
                    expected_direction="iterate",
                    comparison_role="producer_memory_hierarchy",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "estimate_decoder_output_projection_producer_memory_hierarchy",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_output_projection_producer_memory_hierarchy.py" in run
            assert "--cache-capacity-mb-list 0,8,32,128,256" in run
            assert "l2_decoder_frontier_synthesis_policy_calibrated_v1.json" in run
            assert decoder_inputs["producer_memory_hierarchy_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_output_projection_producer_memory_hierarchy__"
                "l2_decoder_output_projection_producer_memory_hierarchy_v1.json"
            )
            assert "weight-memory hierarchy" in decoder_inputs["producer_memory_hierarchy_scope"]
            assert decoder_inputs["producer_memory_hierarchy_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_output_projection_producer_memory_hierarchy",
            }


def test_generate_l2_campaign_task_adds_decoder_attention_kv_capacity_noc() -> None:
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
                    item_id="l2_decoder_attention_kv_capacity_noc_baseline_v1",
                    proposal_id="prop_l2_decoder_attention_kv_capacity_noc_baseline_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_kv_capacity_noc_baseline_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_attention_kv_capacity_noc",
                    expected_direction="iterate",
                    comparison_role="frontier_synthesis",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "estimate_decoder_attention_kv_capacity_noc",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_attention_kv_capacity_noc.py" in run
            assert "--die-area-mm2-list 25,50,100,200,400" in run
            assert "--noc-hops-list 1,2,4,8" in run
            assert decoder_inputs["attention_kv_memory_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_capacity_noc__"
                "l2_decoder_attention_kv_capacity_noc_baseline_v1.json"
            )
            assert "Capacity-constrained" in decoder_inputs["attention_kv_capacity_noc_scope"]
            assert decoder_inputs["attention_kv_memory_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_kv_capacity_noc",
            }


def test_generate_l2_campaign_task_adds_decoder_attention_kv_noc_scheduler() -> None:
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
                    item_id="l2_decoder_attention_kv_noc_scheduler_selected_v1",
                    proposal_id="prop_l2_decoder_attention_kv_noc_scheduler_selected_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_kv_noc_scheduler_selected_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_attention_kv_noc_scheduler",
                    expected_direction="iterate",
                    comparison_role="frontier_synthesis",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "estimate_decoder_attention_kv_noc_scheduler",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_attention_kv_noc_scheduler.py" in run
            assert "--selected-points gpt2_small:131072:100" in run
            assert "--tile-tokens-list 128,256,512,1024,2048" in run
            assert decoder_inputs["attention_kv_memory_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_noc_scheduler__"
                "l2_decoder_attention_kv_noc_scheduler_selected_v1.json"
            )
            assert "Selected-point" in decoder_inputs["attention_kv_noc_scheduler_scope"]
            assert decoder_inputs["attention_kv_memory_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_kv_noc_scheduler",
            }


def test_generate_l2_campaign_task_adds_decoder_attention_kv_spill_scheduler() -> None:
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
                    item_id="l2_decoder_attention_kv_spill_scheduler_llama7b_v1",
                    proposal_id="prop_l2_decoder_attention_kv_spill_scheduler_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_kv_spill_scheduler_llama7b_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_attention_kv_spill_scheduler",
                    expected_direction="iterate",
                    comparison_role="frontier_synthesis",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "estimate_decoder_attention_kv_spill_scheduler",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_attention_kv_spill_scheduler.py" in run
            assert "--label llama7b_proxy" in run
            assert "--prefetch-distance-tiles-list 1,2,4,8,16" in run
            assert decoder_inputs["attention_kv_memory_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_spill_scheduler__"
                "l2_decoder_attention_kv_spill_scheduler_llama7b_v1.json"
            )
            assert "Tile-level spill scheduler" in decoder_inputs["attention_kv_spill_scheduler_scope"]
            assert decoder_inputs["attention_kv_memory_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_kv_spill_scheduler",
            }


def test_generate_l2_campaign_task_adds_decoder_attention_kv_hbm_controller() -> None:
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
                    item_id="l2_decoder_attention_kv_hbm_controller_llama7b_v1",
                    proposal_id="prop_l2_decoder_attention_kv_hbm_controller_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_kv_hbm_controller_llama7b_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_attention_kv_hbm_controller",
                    expected_direction="iterate",
                    comparison_role="frontier_synthesis",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "estimate_decoder_attention_kv_hbm_controller",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_attention_kv_hbm_controller.py" in run
            assert "--channel-count-list 4,8,16" in run
            assert "--row-hit-rate-list 0.5,0.75,0.9" in run
            assert decoder_inputs["attention_kv_memory_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_hbm_controller__"
                "l2_decoder_attention_kv_hbm_controller_llama7b_v1.json"
            )
            assert "HBM-controller realism" in decoder_inputs["attention_kv_hbm_controller_scope"]
            assert decoder_inputs["attention_kv_memory_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_kv_hbm_controller",
            }


def test_generate_l2_campaign_task_adds_decoder_attention_kv_physical_hbm_frontier() -> None:
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
                    item_id="l2_decoder_attention_kv_physical_hbm_frontier_llama7b_v1",
                    proposal_id="prop_l2_decoder_attention_kv_physical_hbm_frontier_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_kv_physical_hbm_frontier_llama7b_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_attention_kv_physical_hbm_frontier",
                    expected_direction="iterate",
                    comparison_role="frontier_synthesis",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "estimate_decoder_attention_kv_physical_hbm_frontier",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_attention_kv_physical_hbm_frontier.py" in run
            assert "--data-rate-mtps-list 3200,6400,9000" in run
            assert "--kv-bits-list 16,8,4" in run
            assert decoder_inputs["attention_kv_memory_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_physical_hbm_frontier__"
                "l2_decoder_attention_kv_physical_hbm_frontier_llama7b_v1.json"
            )
            assert (
                "Physical-HBM"
                in decoder_inputs["attention_kv_physical_hbm_frontier_scope"]
            )
            assert decoder_inputs["attention_kv_memory_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_kv_physical_hbm_frontier",
            }


def test_generate_l2_campaign_task_adds_decoder_attention_kv_physical_hbm_quality_backed() -> None:
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
                    item_id="l2_decoder_attention_kv_physical_hbm_quality_backed_llama7b_v1",
                    proposal_id="prop_l2_decoder_attention_kv_physical_hbm_quality_backed_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_kv_physical_hbm_quality_backed_llama7b_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_attention_kv_physical_hbm_quality_backed",
                    expected_direction="iterate",
                    comparison_role="frontier_synthesis",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "estimate_decoder_attention_kv_physical_hbm_quality_backed",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_attention_kv_physical_hbm_frontier.py" in run
            assert "--kv-sharing-list gqa8" in run
            assert "--kv-bits-list 16,8" in run
            assert "--kv-bits-list 16,8,4" not in run
            assert decoder_inputs["attention_kv_memory_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_physical_hbm_quality_backed__"
                "l2_decoder_attention_kv_physical_hbm_quality_backed_llama7b_v1.json"
            )
            assert decoder_inputs["attention_kv_model_native_quality"].endswith(
                "decoder_attention_kv_model_native_quality__"
                "l2_decoder_attention_kv_model_native_quality_tinyllama_v1_r2.json"
            )
            assert decoder_inputs["attention_kv_model_native_recovery"].endswith(
                "decoder_attention_kv_model_native_recovery__"
                "l2_decoder_attention_kv_model_native_recovery_tinyllama_v1.json"
            )
            assert (
                "Quality-backed physical-HBM"
                in decoder_inputs["attention_kv_physical_hbm_quality_backed_scope"]
            )
            assert decoder_inputs["attention_kv_memory_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_kv_physical_hbm_quality_backed",
            }


def test_generate_l2_campaign_task_adds_decoder_attention_kv_physical_hbm_memory_noc() -> None:
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
                    item_id="l2_decoder_attention_kv_physical_hbm_memory_noc_llama7b_v1",
                    proposal_id="prop_l2_decoder_attention_kv_physical_hbm_memory_noc_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_kv_physical_hbm_memory_noc_llama7b_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_attention_kv_physical_hbm_memory_noc",
                    expected_direction="iterate",
                    comparison_role="frontier_synthesis",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "estimate_decoder_attention_kv_physical_hbm_memory_noc",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_attention_kv_physical_hbm_frontier.py" in run
            assert "--sequence-length-list 131072" in run
            assert "--kv-sharing-list gqa8" in run
            assert "--kv-bits-list 8,16" in run
            assert "--sram-area-fraction 0.4,0.6,0.75" in run
            assert "--noc-hops 1,4" in run
            assert decoder_inputs["attention_kv_memory_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_physical_hbm_memory_noc__"
                "l2_decoder_attention_kv_physical_hbm_memory_noc_llama7b_v1.json"
            )
            assert decoder_inputs["attention_kv_physical_hbm_quality_backed"].endswith(
                "decoder_attention_kv_physical_hbm_quality_backed__"
                "l2_decoder_attention_kv_physical_hbm_quality_backed_llama7b_v1.json"
            )
            assert (
                "memory/NoC sensitivity"
                in decoder_inputs["attention_kv_physical_hbm_memory_noc_scope"]
            )
            assert decoder_inputs["attention_kv_memory_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_kv_physical_hbm_memory_noc",
            }


def test_generate_l2_campaign_task_adds_decoder_attention_kv_physical_hbm_compute_sensitivity() -> None:
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
                    item_id="l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v1",
                    proposal_id="prop_l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_attention_kv_physical_hbm_compute_sensitivity",
                    expected_direction="iterate",
                    comparison_role="frontier_synthesis",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "estimate_decoder_attention_kv_physical_hbm_compute_sensitivity",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_attention_kv_physical_hbm_frontier.py" in run
            assert "--sequence-length-list 131072" in run
            assert "--kv-sharing-list gqa8" in run
            assert "--kv-bits-list 8" in run
            assert "--die-area-mm2-list 400,800,1200" in run
            assert "--usable-sram-fraction 0.7,0.85" in run
            assert "--bank-count 16,64" in run
            assert "--macs-per-cycle 32768,65536,131072,262144,524288" in run
            assert "--vector-ops-per-cycle 8192,16384,32768,65536" in run
            assert decoder_inputs["attention_kv_memory_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_physical_hbm_compute_sensitivity__"
                "l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v1.json"
            )
            assert decoder_inputs["attention_kv_physical_hbm_memory_noc"].endswith(
                "decoder_attention_kv_physical_hbm_memory_noc__"
                "l2_decoder_attention_kv_physical_hbm_memory_noc_llama7b_v1_r2.json"
            )
            assert (
                "compute-downsizing sensitivity"
                in decoder_inputs["attention_kv_physical_hbm_compute_sensitivity_scope"]
            )
            assert decoder_inputs["attention_kv_memory_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_kv_physical_hbm_compute_sensitivity",
            }


def test_generate_l2_campaign_task_adds_decoder_attention_kv_compute_floor_gap() -> None:
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
                    item_id="l2_decoder_attention_kv_compute_floor_gap_llama7b_v1",
                    proposal_id="prop_l2_decoder_attention_kv_compute_floor_gap_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_kv_compute_floor_gap_llama7b_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_attention_kv_compute_floor_gap",
                    expected_direction="quantify_compute_gap",
                    comparison_role="frontier_synthesis",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "estimate_decoder_attention_kv_compute_floor_gap",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_attention_kv_compute_floor_gap.py" in run
            assert "--target-macs-per-cycle-list 131072,262144,524288" in run
            assert "--logic-area-fraction-list 0.2,0.4,0.6" in run
            assert decoder_inputs["attention_kv_compute_floor_gap_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_compute_floor_gap__"
                "l2_decoder_attention_kv_compute_floor_gap_llama7b_v1.json"
            )
            assert decoder_inputs["attention_kv_physical_hbm_compute_sensitivity"].endswith(
                "decoder_attention_kv_physical_hbm_compute_sensitivity__"
                "l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2.json"
            )
            assert (
                "MAC/cycle/mm2 gap"
                in decoder_inputs["attention_kv_compute_floor_gap_scope"]
            )
            assert decoder_inputs["attention_kv_compute_floor_gap_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_kv_compute_floor_gap",
            }


def test_generate_l2_campaign_task_adds_decoder_attention_kv_compute_ceiling_envelope() -> None:
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
                    item_id="l2_decoder_attention_kv_compute_ceiling_envelope_llama7b_v1",
                    proposal_id="prop_l2_decoder_attention_kv_compute_ceiling_envelope_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_kv_compute_ceiling_envelope_llama7b_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_attention_kv_compute_ceiling_envelope",
                    expected_direction="bound_compute_frontier",
                    comparison_role="frontier_synthesis",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "estimate_decoder_attention_kv_compute_ceiling_envelope",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_attention_kv_compute_ceiling_envelope.py" in run
            assert "--density-envelope-macs-per-cycle-per-mm2-list 150,300" in run
            assert "--vector-ops-per-mac 0.125" in run
            assert "runs/design_registry/internal_measurements.jsonl" in run
            assert "runs/design_registry/external_measurements.jsonl" in run
            assert "--comparison-claims runs/design_registry/comparison_claims.jsonl" in run
            assert decoder_inputs["attention_kv_compute_ceiling_envelope_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_compute_ceiling_envelope__"
                "l2_decoder_attention_kv_compute_ceiling_envelope_llama7b_v1.json"
            )
            assert (
                "registry evidence citations"
                in decoder_inputs["attention_kv_compute_ceiling_envelope_scope"]
            )
            assert decoder_inputs["design_registry_comparison_claims"] == (
                "runs/design_registry/comparison_claims.jsonl"
            )
            assert decoder_inputs["attention_kv_compute_ceiling_envelope_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_kv_compute_ceiling_envelope",
            }


def test_generate_l2_campaign_task_adds_decoder_attention_kv_quality_gate() -> None:
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
                    item_id="l2_decoder_attention_kv_quality_gate_llama7b_v1",
                    proposal_id="prop_l2_decoder_attention_kv_quality_gate_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_kv_quality_gate_llama7b_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_attention_kv_quality_gate",
                    expected_direction="iterate",
                    comparison_role="frontier_synthesis",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "estimate_decoder_attention_kv_quality_gate",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_attention_kv_quality_gate.py" in run
            assert "l2_decoder_attention_kv_physical_hbm_frontier_llama7b_v1.json" in run
            assert "--sequence-length-list 131072" in run
            assert decoder_inputs["attention_kv_memory_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_quality_gate__"
                "l2_decoder_attention_kv_quality_gate_llama7b_v1.json"
            )
            assert "Quality-risk gate" in decoder_inputs["attention_kv_quality_gate_scope"]
            assert decoder_inputs["attention_kv_memory_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_kv_quality_gate",
            }


def test_generate_l2_campaign_task_adds_decoder_attention_kv_clustered_schedule_overhead() -> None:
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
                    item_id="l2_decoder_attention_kv_clustered_schedule_overhead_llama7b_v1",
                    proposal_id="prop_l2_decoder_attention_kv_measured_compute_partition_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_kv_measured_compute_partition_llama7b_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_attention_kv_clustered_schedule_overhead",
                    expected_direction="iterate",
                    comparison_role="frontier_synthesis",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "estimate_decoder_attention_kv_clustered_schedule_overhead",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_attention_kv_clustered_schedule.py" in run
            assert "--command-cycles-per-tile 0,1,4,16" in run
            assert "--reducer-setup-cycles 0,32,128" in run
            assert "--reduction-cycle-multiplier 1,2,4" in run
            assert decoder_inputs["attention_kv_clustered_schedule_overhead_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_clustered_schedule_overhead__"
                "l2_decoder_attention_kv_clustered_schedule_overhead_llama7b_v1.json"
            )
            assert "Sensitivity pass" in decoder_inputs["attention_kv_clustered_schedule_overhead_scope"]
            assert decoder_inputs["attention_kv_clustered_schedule_overhead_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_kv_clustered_schedule_overhead",
            }


def test_generate_l2_campaign_task_adds_decoder_attention_kv_quality_proxy() -> None:
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
                    item_id="l2_decoder_attention_kv_quality_proxy_llama7b_v1",
                    proposal_id="prop_l2_decoder_attention_kv_quality_proxy_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_kv_quality_proxy_llama7b_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_attention_kv_quality_proxy",
                    expected_direction="iterate",
                    comparison_role="frontier_synthesis",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "estimate_decoder_attention_kv_quality_proxy",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_attention_kv_quality_proxy.py" in run
            assert "--candidate-spec-list mha:kv8,mha:kv4,gqa8:kv8,gqa8:kv4,mqa:kv4" in run
            assert decoder_inputs["attention_kv_memory_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_quality_proxy__"
                "l2_decoder_attention_kv_quality_proxy_llama7b_v1.json"
            )
            assert "Controlled attention proxy" in decoder_inputs["attention_kv_quality_proxy_scope"]
            assert decoder_inputs["attention_kv_memory_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_kv_quality_proxy",
            }


def test_generate_l2_campaign_task_adds_decoder_attention_kv_native_gqa_proxy() -> None:
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
                    item_id="l2_decoder_attention_kv_native_gqa_proxy_llama7b_v1",
                    proposal_id="prop_l2_decoder_attention_kv_native_gqa_proxy_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_kv_native_gqa_proxy_llama7b_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_attention_kv_native_gqa_proxy",
                    expected_direction="iterate",
                    comparison_role="frontier_synthesis",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "estimate_decoder_attention_kv_native_gqa_proxy",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_attention_kv_native_gqa_proxy.py" in run
            assert "--candidate-spec-list gqa8:kv8,gqa8:kv4,mqa:kv8,mqa:kv4" in run
            assert decoder_inputs["attention_kv_memory_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_native_gqa_proxy__"
                "l2_decoder_attention_kv_native_gqa_proxy_llama7b_v1.json"
            )
            assert decoder_inputs["attention_kv_quality_proxy"].endswith(
                "decoder_attention_kv_quality_proxy__l2_decoder_attention_kv_quality_proxy_llama7b_v1.json"
            )
            assert "same-sharing KV16 reference" in decoder_inputs["attention_kv_native_gqa_proxy_scope"]
            assert decoder_inputs["attention_kv_memory_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_kv_native_gqa_proxy",
            }


def test_generate_l2_campaign_task_adds_decoder_attention_kv_trace_calibration() -> None:
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
                    item_id="l2_decoder_attention_kv_trace_calibration_v1",
                    proposal_id="prop_l2_decoder_attention_kv_trace_calibration_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_attention_kv_trace_calibration_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_attention_kv_trace_calibration",
                    expected_direction="iterate",
                    comparison_role="frontier_synthesis",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "estimate_decoder_attention_kv_trace_calibration",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_attention_kv_trace_calibration.py" in run
            assert "--quality-compare gpt2_prompt_stress=" in run
            assert "--quality-compare distilgpt2_prompt_stress=" in run
            assert decoder_inputs["attention_kv_memory_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_trace_calibration__l2_decoder_attention_kv_trace_calibration_v1.json"
            )
            assert decoder_inputs["attention_kv_native_gqa_proxy"].endswith(
                "decoder_attention_kv_native_gqa_proxy__l2_decoder_attention_kv_native_gqa_proxy_llama7b_v1.json"
            )
            assert "not a native-GQA quality claim" in decoder_inputs["attention_kv_trace_calibration_scope"]
            assert decoder_inputs["attention_kv_memory_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_kv_trace_calibration",
            }


def test_generate_l2_campaign_task_adds_decoder_attention_kv_model_native_quality() -> None:
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
                    item_id="l2_decoder_attention_kv_model_native_quality_tinyllama_v1",
                    proposal_id="prop_l2_decoder_attention_kv_model_native_quality_tinyllama_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_kv_model_native_quality_tinyllama_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_attention_kv_model_native_quality",
                    expected_direction="iterate",
                    comparison_role="frontier_synthesis",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "evaluate_decoder_attention_kv_model_native_quality",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "run_hf_eval_python.sh" in run
            assert "evaluate_llm_decoder_model_native_kv_quant.py" in run
            assert "--kv-bits-list 8,4" in run
            assert decoder_inputs["attention_kv_memory_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_model_native_quality__"
                "l2_decoder_attention_kv_model_native_quality_tinyllama_v1.json"
            )
            assert decoder_inputs["attention_kv_trace_calibration"].endswith(
                "decoder_attention_kv_trace_calibration__l2_decoder_attention_kv_trace_calibration_v1.json"
            )
            assert "teacher-forced decode" in decoder_inputs["attention_kv_model_native_quality_scope"]
            assert decoder_inputs["attention_kv_memory_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_kv_model_native_quality",
            }


def test_generate_l2_campaign_task_adds_decoder_attention_kv_model_native_recovery() -> None:
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
                    item_id="l2_decoder_attention_kv_model_native_recovery_tinyllama_v1",
                    proposal_id="prop_l2_decoder_attention_kv_model_native_recovery_tinyllama_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_kv_model_native_recovery_tinyllama_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_attention_kv_model_native_recovery",
                    expected_direction="iterate",
                    comparison_role="frontier_synthesis",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "evaluate_decoder_attention_kv_model_native_recovery",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "run_hf_eval_python.sh" in run
            assert "evaluate_llm_decoder_model_native_kv_quant.py" in run
            assert "--kv-bits-list 4" in run
            assert "--kv-granularity-list tensor,kv_head,token_vector" in run
            assert decoder_inputs["attention_kv_memory_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_model_native_recovery__"
                "l2_decoder_attention_kv_model_native_recovery_tinyllama_v1.json"
            )
            assert decoder_inputs["attention_kv_model_native_quality"].endswith(
                "decoder_attention_kv_model_native_quality__"
                "l2_decoder_attention_kv_model_native_quality_tinyllama_v1_r2.json"
            )
            assert "per-token-vector recovery" in decoder_inputs["attention_kv_model_native_recovery_scope"]
            assert decoder_inputs["attention_kv_memory_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_kv_model_native_recovery",
            }


def test_generate_l2_campaign_task_adds_decoder_output_projection_weight_store_feasibility() -> None:
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
                    item_id="l2_decoder_output_projection_weight_store_feasibility_v1",
                    proposal_id="prop_l2_decoder_output_projection_weight_store_feasibility_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_output_projection_weight_store_feasibility_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_output_projection_weight_store_feasibility",
                    expected_direction="iterate",
                    comparison_role="producer_memory_hierarchy",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "estimate_decoder_output_projection_weight_store_feasibility",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_output_projection_weight_store_feasibility.py" in run
            assert "--bank-read-width-bits-list 256,512,1024,2048" in run
            assert "l2_decoder_output_projection_producer_memory_hierarchy_v1.json" in run
            assert decoder_inputs["weight_store_feasibility_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_output_projection_weight_store_feasibility__"
                "l2_decoder_output_projection_weight_store_feasibility_v1.json"
            )
            assert "banking, bandwidth" in decoder_inputs["weight_store_feasibility_scope"]
            assert decoder_inputs["weight_store_feasibility_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_output_projection_weight_store_feasibility",
            }


def test_generate_l2_campaign_task_adds_decoder_output_projection_weight_store_interface() -> None:
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
                    item_id="l2_decoder_output_projection_weight_store_interface_v1",
                    proposal_id="prop_l2_decoder_output_projection_weight_store_interface_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_output_projection_weight_store_interface_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_output_projection_weight_store_interface",
                    expected_direction="iterate",
                    comparison_role="weight_store_contract",
                    paired_baseline_item_id="l2_decoder_output_projection_weight_store_feasibility_v1",
                    depends_on_item_ids=["l2_decoder_output_projection_weight_store_feasibility_v1"],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "probe_decoder_output_projection_weight_store_interface",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "probe_llm_decoder_output_projection_weight_store_interface.py" in run
            assert "--max-representative-banks 64" in run
            assert "--read-latency-cycles-list 1,2,4,8" in run
            assert "l2_decoder_output_projection_weight_store_feasibility_v1.json" in run
            assert decoder_inputs["weight_store_interface_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_output_projection_weight_store_interface__"
                "l2_decoder_output_projection_weight_store_interface_v1.json"
            )
            assert "bounded RTL/perf-sim contract" in decoder_inputs["weight_store_interface_scope"]
            assert decoder_inputs["weight_store_interface_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_output_projection_weight_store_interface",
            }


def test_generate_l2_campaign_task_adds_decoder_output_projection_weight_fetch_wrapper() -> None:
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
                    item_id="l2_decoder_output_projection_weight_fetch_wrapper_v1",
                    proposal_id="prop_l2_decoder_output_projection_weight_fetch_wrapper_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_output_projection_weight_fetch_wrapper_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_output_projection_weight_fetch_wrapper",
                    expected_direction="iterate",
                    comparison_role="weight_fetch_contract",
                    paired_baseline_item_id="l2_decoder_output_projection_weight_store_interface_v1_r2",
                    depends_on_item_ids=["l2_decoder_output_projection_weight_store_interface_v1_r2"],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "probe_decoder_output_projection_weight_fetch_wrapper",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "probe_llm_decoder_output_projection_weight_fetch_wrapper.py" in run
            assert "--outstanding-depth-list 1,4" in run
            assert "l2_decoder_output_projection_weight_store_feasibility_v1.json" in run
            assert decoder_inputs["weight_fetch_wrapper_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_output_projection_weight_fetch_wrapper__"
                "l2_decoder_output_projection_weight_fetch_wrapper_v1.json"
            )
            assert "request cadence" in decoder_inputs["weight_fetch_wrapper_scope"]
            assert decoder_inputs["weight_fetch_wrapper_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_output_projection_weight_fetch_wrapper",
            }


def test_generate_l2_campaign_task_adds_decoder_producer_ranker_memory_integration_plan() -> None:
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
                    item_id="l2_decoder_producer_ranker_memory_integration_plan_v1",
                    proposal_id="prop_l2_decoder_producer_ranker_memory_integration_plan_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_producer_ranker_memory_integration_plan_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_producer_ranker_memory_integration_plan",
                    expected_direction="iterate",
                    comparison_role="integration_plan",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert work_item.command_manifest[0]["name"] == "plan_decoder_producer_ranker_memory_integration"
            run = work_item.command_manifest[0]["run"]
            assert "plan_llm_decoder_producer_ranker_memory_integration.py" in run
            assert "--frontier-synthesis" in run
            assert "--producer-ranker-coupled" in run
            assert "--producer-physical-boundary" in run
            assert "--producer-config" in run
            assert decoder_inputs["integration_plan_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_producer_ranker_memory_integration_plan__"
                "l2_decoder_producer_ranker_memory_integration_plan_v1.json"
            )
            assert "ready-valid stream equivalence" in decoder_inputs["integration_plan_scope"]
            assert decoder_inputs["producer_config"] == (
                "runs/designs/npu_blocks/npu_fp16_cpp_nm16_producer/config_nm16_producer.json"
            )
            assert decoder_inputs["integration_plan_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_producer_ranker_memory_integration_plan",
            }


def test_generate_l2_campaign_task_adds_decoder_producer_ranker_ready_valid_equivalence() -> None:
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
                    item_id="l2_decoder_producer_ranker_ready_valid_equivalence_v1",
                    proposal_id="prop_l2_decoder_producer_ranker_ready_valid_equivalence_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_producer_ranker_ready_valid_equivalence_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_producer_ranker_ready_valid_equivalence",
                    expected_direction="iterate",
                    comparison_role="equivalence_check",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:2]] == [
                "build_generator",
                "probe_decoder_producer_ranker_ready_valid_equivalence",
            ]
            assert work_item.command_manifest[0]["run"] == (
                "export PATH=/oss-cad-suite/bin:$PATH && "
                "cmake -S . -B build && cmake --build build --target rtlgen"
            )
            run = work_item.command_manifest[1]["run"]
            assert "probe_llm_decoder_producer_ranker_ready_valid_equivalence.py" in run
            assert "--run-rtl-sim" in run
            assert "logit_rank_r64_l16_k1" in run
            assert "candidate_stream_merge_fifo_k1_l16_t16_d16" in run
            assert decoder_inputs["ready_valid_equivalence_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_producer_ranker_ready_valid_equivalence__"
                "l2_decoder_producer_ranker_ready_valid_equivalence_v1.json"
            )
            assert "lower-token tie order" in decoder_inputs["ready_valid_equivalence_scope"]
            assert decoder_inputs["ready_valid_equivalence_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_producer_ranker_ready_valid_equivalence",
            }


def test_generate_l2_campaign_task_adds_decoder_producer_ranker_physical_wrapper() -> None:
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
                    item_id="l2_decoder_producer_ranker_physical_wrapper_v1",
                    proposal_id="prop_l2_decoder_producer_ranker_physical_wrapper_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_producer_ranker_physical_wrapper_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_producer_ranker_physical_wrapper",
                    expected_direction="iterate",
                    comparison_role="physical_wrapper",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:2]] == [
                "build_generator",
                "probe_decoder_producer_ranker_physical_wrapper",
            ]
            run = work_item.command_manifest[1]["run"]
            assert "probe_llm_decoder_producer_ranker_physical_wrapper.py" in run
            assert "--make-target 3_3_place_gp" in run
            assert "decoder_r64_k1_producer_ranker_physical_wrapper" in run
            assert decoder_inputs["ready_valid_equivalence"].endswith(
                "l2_decoder_producer_ranker_ready_valid_equivalence_v1_r2.json"
            )
            assert "bounded macro-style PPA" in decoder_inputs[
                "producer_ranker_physical_wrapper_scope"
            ]
            assert (
                "runs/designs/activations/decoder_r64_k1_producer_ranker_physical_wrapper/metrics.csv"
                in work_item.expected_outputs
            )
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_producer_ranker_physical_wrapper",
            }


def test_generate_l2_campaign_task_adds_decoder_pipelined_ranker_architecture() -> None:
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
                    item_id="l2_decoder_pipelined_ranker_architecture_v1",
                    proposal_id="prop_l2_decoder_pipelined_ranker_architecture_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_pipelined_ranker_architecture_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_pipelined_ranker_architecture",
                    expected_direction="iterate",
                    comparison_role="ranker_pipeline_architecture",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:3]] == [
                "build_generator",
                "probe_decoder_pipelined_ranker_architecture",
                "build_runs_index",
            ]
            run = work_item.command_manifest[1]["run"]
            assert "probe_llm_decoder_pipelined_ranker_architecture.py" in run
            assert "--local-lanes 8,16,32" in run
            assert "decoder_pipelined_ranker_architecture" in decoder_inputs[
                "pipelined_ranker_architecture_sweep"
            ]
            assert decoder_inputs["unpipelined_physical_wrapper"].endswith(
                "l2_decoder_producer_ranker_physical_wrapper_v1.json"
            )
            assert "runs/index.csv" in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_pipelined_ranker_architecture",
            }


def test_generate_l2_campaign_task_adds_decoder_rank_tree_architecture() -> None:
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
                    item_id="l2_decoder_rank_tree_architecture_v1",
                    proposal_id="prop_l2_decoder_rank_tree_architecture_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_rank_tree_architecture_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_rank_tree_architecture",
                    expected_direction="iterate",
                    comparison_role="ranker_pipeline_architecture",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:3]] == [
                "build_generator",
                "probe_decoder_rank_tree_architecture",
                "build_runs_index",
            ]
            run = work_item.command_manifest[1]["run"]
            assert "probe_llm_decoder_rank_tree_architecture.py" in run
            assert "--radices 2,4,8" in run
            assert "decoder_rank_tree_architecture" in decoder_inputs[
                "rank_tree_architecture_sweep"
            ]
            assert decoder_inputs["pipelined_ranker_architecture"].endswith(
                "l2_decoder_pipelined_ranker_architecture_v1.json"
            )
            assert "runs/index.csv" in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_rank_tree_architecture",
            }


def test_generate_l2_campaign_task_adds_decoder_serial_ranker_architecture() -> None:
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
                    item_id="l2_decoder_serial_ranker_architecture_v1",
                    proposal_id="prop_l2_decoder_serial_ranker_architecture_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_serial_ranker_architecture_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_serial_ranker_architecture",
                    expected_direction="iterate",
                    comparison_role="ranker_pipeline_architecture",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:3]] == [
                "build_generator",
                "probe_decoder_serial_ranker_architecture",
                "build_runs_index",
            ]
            run = work_item.command_manifest[1]["run"]
            assert "probe_llm_decoder_serial_ranker_architecture.py" in run
            assert "--lanes-per-cycle 1,2,4,8,16" in run
            assert "decoder_serial_ranker_architecture" in decoder_inputs[
                "serial_ranker_architecture_sweep"
            ]
            assert decoder_inputs["rank_tree_architecture"].endswith(
                "l2_decoder_rank_tree_architecture_v1.json"
            )
            assert "runs/index.csv" in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_serial_ranker_architecture",
            }


def test_generate_l2_campaign_task_adds_decoder_producer_synth_boundary_evidence() -> None:
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
                    item_id="l2_decoder_output_projection_producer_synth_boundary_v1",
                    proposal_id="prop_l2_decoder_output_projection_producer_synth_boundary_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_output_projection_producer_synth_boundary_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_output_projection_producer_synth_boundary",
                    expected_direction="iterate",
                    comparison_role="producer_synth_boundary",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert work_item.command_manifest[0]["name"] == (
                "probe_decoder_output_projection_producer_synth_boundary"
            )
            run = work_item.command_manifest[0]["run"]
            assert "probe_decoder_producer_synth_boundary.py" in run
            assert "--make-target 1_2_yosys" in run
            assert "--timeout-seconds 1800" in run
            assert "npu_fp16_cpp_nm2_producer/config_nm2_producer.json" in run
            assert "npu_fp16_cpp_nm3_producer/config_nm3_producer.json" in run
            assert "npu_fp16_cpp_nm4_producer/config_nm4_producer.json" in run
            assert decoder_inputs["producer_synth_boundary_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_output_projection_producer_synth_boundary__"
                "l2_decoder_output_projection_producer_synth_boundary_v1.json"
            )
            assert "synth-only target" in decoder_inputs["producer_synth_boundary_scope"]
            assert decoder_inputs["producer_synth_boundary_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_output_projection_producer_synth_boundary",
            }


def test_generate_l2_campaign_task_adds_decoder_producer_extended_synth_boundary_evidence() -> None:
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
                    item_id="l2_decoder_output_projection_producer_synth_boundary_nm8_nm16_v1",
                    proposal_id="prop_l2_decoder_output_projection_producer_synth_boundary_nm8_nm16_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_output_projection_producer_synth_boundary_nm8_nm16_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_output_projection_producer_synth_boundary",
                    expected_direction="iterate",
                    comparison_role="producer_synth_boundary",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            run = work_item.command_manifest[0]["run"]
            assert "npu_fp16_cpp_nm8_producer/config_nm8_producer.json" in run
            assert "npu_fp16_cpp_nm16_producer/config_nm16_producer.json" in run
            assert "npu_fp16_cpp_nm4_producer/config_nm4_producer.json" not in run
            assert "nm8 and nm16" in decoder_inputs["producer_synth_boundary_scope"]


def test_generate_l2_campaign_task_adds_decoder_producer_pnr_feasibility_evidence() -> None:
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
                    item_id="l2_decoder_output_projection_producer_pnr_nm8_v1",
                    proposal_id="prop_l2_decoder_output_projection_producer_pnr_nm8_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_output_projection_producer_pnr_nm8_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_output_projection_producer_pnr_feasibility",
                    expected_direction="iterate",
                    comparison_role="producer_pnr_feasibility",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            run = work_item.command_manifest[0]["run"]
            assert work_item.command_manifest[0]["name"] == (
                "probe_decoder_output_projection_producer_pnr_feasibility"
            )
            assert "--make-target 3_3_place_gp" in run
            assert "--timeout-seconds 3600" in run
            assert "npu_fp16_cpp_nm8_producer/config_nm8_producer.json" in run
            assert "npu_fp16_cpp_nm16_producer/config_nm16_producer.json" not in run
            assert decoder_inputs["producer_synth_boundary_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_output_projection_producer_pnr_feasibility__"
                "l2_decoder_output_projection_producer_pnr_nm8_v1.json"
            )
            assert decoder_inputs["producer_synth_boundary_make_target"] == "3_3_place_gp"
            assert "full physical implementation" in decoder_inputs["producer_synth_boundary_scope"]
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_output_projection_producer_pnr_feasibility",
            }


def test_generate_l2_campaign_task_adds_decoder_producer_nm16_pnr_feasibility_evidence() -> None:
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
                    item_id="l2_decoder_output_projection_producer_pnr_nm16_v1",
                    proposal_id="prop_l2_decoder_output_projection_producer_pnr_nm16_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_output_projection_producer_pnr_nm16_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_output_projection_producer_pnr_feasibility",
                    expected_direction="iterate",
                    comparison_role="producer_pnr_feasibility",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            run = work_item.command_manifest[0]["run"]
            assert "npu_fp16_cpp_nm16_producer/config_nm16_producer.json" in run
            assert "npu_fp16_cpp_nm8_producer/config_nm8_producer.json" not in run
            assert "post-scoreboard nm16" in decoder_inputs["producer_synth_boundary_scope"]
            assert decoder_inputs["producer_synth_boundary_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_output_projection_producer_pnr_feasibility__"
                "l2_decoder_output_projection_producer_pnr_nm16_v1.json"
            )


def test_generate_l2_campaign_task_adds_decoder_producer_isolated_synth_evidence() -> None:
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
                    item_id="l2_decoder_output_projection_producer_isolated_synth_v1",
                    proposal_id="prop_l2_decoder_output_projection_producer_isolated_synth_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_output_projection_producer_isolated_synth_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_output_projection_producer_isolated_synth",
                    expected_direction="iterate",
                    comparison_role="producer_synth_boundary",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert work_item.command_manifest[0]["name"] == (
                "probe_decoder_output_projection_producer_isolated_synth"
            )
            run = work_item.command_manifest[0]["run"]
            assert "probe_decoder_producer_synth_boundary.py" in run
            assert "--top gemm_compute_array" in run
            assert "--make-target 1_2_yosys" in run
            assert "npu_fp16_cpp_nm1_producer/config_nm1_producer.json" in run
            assert "npu_fp16_cpp_nm2_producer/config_nm2_producer.json" in run
            assert "npu_fp16_cpp_nm3_producer/config_nm3_producer.json" in run
            assert "npu_fp16_cpp_nm4_producer/config_nm4_producer.json" in run
            assert decoder_inputs["producer_synth_boundary_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_output_projection_producer_isolated_synth__"
                "l2_decoder_output_projection_producer_isolated_synth_v1.json"
            )
            assert decoder_inputs["producer_synth_boundary_top"] == "gemm_compute_array"
            assert "nm1 through nm4" in decoder_inputs["producer_synth_boundary_scope"]
            assert "separating compute-array synthesis" in decoder_inputs["producer_synth_boundary_scope"]
            assert decoder_inputs["producer_synth_boundary_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_output_projection_producer_isolated_synth",
            }


def test_generate_l2_campaign_task_adds_decoder_producer_top_ablation_evidence() -> None:
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
                    item_id="l2_decoder_output_projection_producer_top_ablation_v1",
                    proposal_id="prop_l2_decoder_output_projection_producer_top_ablation_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_output_projection_producer_top_ablation_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_output_projection_producer_top_ablation",
                    expected_direction="iterate",
                    comparison_role="producer_synth_boundary",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert work_item.command_manifest[0]["name"] == (
                "probe_decoder_output_projection_producer_top_ablation"
            )
            run = work_item.command_manifest[0]["run"]
            assert "probe_decoder_producer_top_ablation.py" in run
            assert "--base-config runs/designs/npu_blocks/npu_fp16_cpp_nm2_producer/config_nm2_producer.json" in run
            assert "--continue-after-failure" in run
            assert decoder_inputs["producer_top_ablation_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_output_projection_producer_top_ablation__"
                "l2_decoder_output_projection_producer_top_ablation_v1.json"
            )
            assert "bounded synth status" in decoder_inputs["producer_top_ablation_scope"]
            assert decoder_inputs["producer_top_ablation_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_output_projection_producer_top_ablation",
            }


def test_generate_l2_campaign_task_adds_decoder_producer_cq_ablation_evidence() -> None:
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
                    item_id="l2_decoder_output_projection_producer_cq_ablation_v1",
                    proposal_id="prop_l2_decoder_output_projection_producer_cq_ablation_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_output_projection_producer_cq_ablation_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_output_projection_producer_cq_ablation",
                    expected_direction="iterate",
                    comparison_role="producer_synth_boundary",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert work_item.command_manifest[0]["name"] == (
                "probe_decoder_output_projection_producer_cq_ablation"
            )
            run = work_item.command_manifest[0]["run"]
            assert "probe_decoder_producer_cq_ablation.py" in run
            assert "--timeout-seconds 900" in run
            assert decoder_inputs["producer_cq_ablation_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_output_projection_producer_cq_ablation__"
                "l2_decoder_output_projection_producer_cq_ablation_v1.json"
            )
            assert "CQ subpaths" in decoder_inputs["producer_cq_ablation_scope"]
            assert decoder_inputs["producer_cq_ablation_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_output_projection_producer_cq_ablation",
            }


def test_generate_l2_campaign_task_adds_decoder_producer_softmax_event_ablation_evidence() -> None:
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
                    item_id="l2_decoder_output_projection_producer_softmax_event_ablation_v1",
                    proposal_id="prop_l2_decoder_output_projection_producer_softmax_event_ablation_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_output_projection_producer_softmax_event_ablation_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_output_projection_producer_softmax_event_ablation",
                    expected_direction="iterate",
                    comparison_role="producer_synth_boundary",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert work_item.command_manifest[0]["name"] == (
                "probe_decoder_output_projection_producer_softmax_event_ablation"
            )
            run = work_item.command_manifest[0]["run"]
            assert "probe_decoder_producer_softmax_event_ablation.py" in run
            assert "--stall-timeout-seconds 450" in run
            assert decoder_inputs["producer_softmax_event_ablation_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_output_projection_producer_softmax_event_ablation__"
                "l2_decoder_output_projection_producer_softmax_event_ablation_v1.json"
            )
            assert "SOFTMAX/EVENT slice" in decoder_inputs["producer_softmax_event_ablation_scope"]
            assert decoder_inputs["producer_softmax_event_ablation_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_output_projection_producer_softmax_event_ablation",
            }


def test_generate_l2_campaign_task_adds_decoder_pwl_logit_sensitivity_ladder_evidence() -> None:
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
                    item_id="l2_decoder_pwl_logit_ladder_v1",
                    proposal_id="prop_l2_decoder_pwl_logit_ladder_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_pwl_logit_ladder_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_pwl_logit_sensitivity_ladder",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            assert work_item.command_manifest[0]["name"] == "generate_decoder_pwl_logit_focus_reference"
            assert work_item.command_manifest[2]["name"] == "validate_decoder_pwl_logit_focus_contract"
            assert work_item.command_manifest[4]["name"] == "sweep_decoder_pwl_logit_ladder"
            assert "decoder_pwl_logit_sensitivity_ladder_v1" in work_item.command_manifest[4]["run"]
            assert work_item.command_manifest[5]["name"] == "summarize_decoder_pwl_logit_ladder"
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["dataset_manifest"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/manifest_pwl_failure_focus_v1.json"
            )
            assert decoder_inputs["sample_file"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/samples_pwl_failure_focus_v1.jsonl"
            )
            assert decoder_inputs["reference_dir"] == "runs/datasets/llm_decoder_eval_tiny_v1/reference_pwl_failure_focus_v1"
            assert decoder_inputs["candidate_dir"] == "runs/datasets/llm_decoder_eval_tiny_v1/candidate_pwl_failure_focus_v1"
            assert decoder_inputs["candidate_sweep_grid"] == "decoder_pwl_logit_sensitivity_ladder_v1"
            assert decoder_inputs["focus_samples"] == [
                "dist2_arith_three_plus_five",
                "dist2_sequence_months",
            ]
            assert decoder_inputs["ladder_out"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/"
                "decoder_pwl_logit_ladder__l2_decoder_pwl_logit_ladder_v1.json"
            )
            assert decoder_inputs["ladder_out"] in work_item.expected_outputs
            assert decoder_inputs["ladder_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_pwl_logit_sensitivity_ladder",
            }


def test_generate_l2_campaign_task_adds_decoder_pwl_survivor_distribution_evidence() -> None:
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
                    item_id="l2_decoder_pwl_survivor_distribution_v1",
                    proposal_id="prop_l2_decoder_pwl_survivor_distribution_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_pwl_survivor_distribution_v1/proposal.json",
                    evaluation_mode="broad_ranking",
                    abstraction_layer="decoder_pwl_survivor_distribution",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[:6] == [
                "generate_decoder_pwl_survivor_distribution_reference",
                "generate_decoder_pwl_survivor_distribution_candidate",
                "validate_decoder_pwl_survivor_distribution_contract",
                "compare_decoder_pwl_survivor_distribution_quality",
                "sweep_decoder_pwl_survivor_distribution",
                "summarize_decoder_pwl_survivor_distribution",
            ]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["dataset_manifest"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/manifest_distribution_v2.json"
            )
            assert decoder_inputs["sample_file"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/samples_distribution_v2.jsonl"
            )
            assert decoder_inputs["candidate_sweep_grid"] == "decoder_pwl_survivor_distribution_v1"
            assert "q12/unquantized PWL survivors" in decoder_inputs["survivor_distribution_scope"]
            assert "--rough-grid decoder_pwl_survivor_distribution_v1" in work_item.command_manifest[4]["run"]
            assert "summarize_llm_decoder_pwl_survivor_distribution.py" in work_item.command_manifest[5]["run"]
            assert decoder_inputs["survivor_distribution_out"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/"
                "decoder_pwl_survivor_distribution__l2_decoder_pwl_survivor_distribution_v1.json"
            )
            assert decoder_inputs["survivor_distribution_out"] in work_item.expected_outputs
            assert decoder_inputs["survivor_distribution_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_pwl_survivor_distribution",
            }


def test_generate_l2_campaign_task_adds_decoder_pwl_bitwidth_boundary_evidence() -> None:
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
                    item_id="l2_decoder_pwl_bitwidth_boundary_v1",
                    proposal_id="prop_l2_decoder_pwl_bitwidth_boundary_v1",
                    proposal_path="docs/proposals/prop_l2_decoder_pwl_bitwidth_boundary_v1/proposal.json",
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_pwl_bitwidth_boundary",
                    expected_direction="iterate",
                    comparison_role="ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            command_names = [command["name"] for command in work_item.command_manifest]
            assert command_names[:6] == [
                "generate_decoder_pwl_bitwidth_boundary_reference",
                "generate_decoder_pwl_bitwidth_boundary_candidate",
                "validate_decoder_pwl_bitwidth_boundary_contract",
                "compare_decoder_pwl_bitwidth_boundary_quality",
                "sweep_decoder_pwl_bitwidth_boundary",
                "summarize_decoder_pwl_bitwidth_boundary",
            ]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert decoder_inputs["dataset_manifest"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/manifest_distribution_v2.json"
            )
            assert decoder_inputs["sample_file"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/samples_distribution_v2.jsonl"
            )
            assert decoder_inputs["candidate_sweep_grid"] == "decoder_pwl_bitwidth_boundary_v1"
            assert "lowest exact-safe integer PWL" in decoder_inputs["bitwidth_boundary_scope"]
            assert "--rough-grid decoder_pwl_bitwidth_boundary_v1" in work_item.command_manifest[4]["run"]
            assert "summarize_llm_decoder_pwl_bitwidth_boundary.py" in work_item.command_manifest[5]["run"]
            assert decoder_inputs["bitwidth_boundary_out"] == (
                "runs/datasets/llm_decoder_eval_tiny_v1/"
                "decoder_pwl_bitwidth_boundary__l2_decoder_pwl_bitwidth_boundary_v1.json"
            )
            assert decoder_inputs["bitwidth_boundary_out"] in work_item.expected_outputs
            assert decoder_inputs["bitwidth_boundary_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_pwl_bitwidth_boundary",
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


def test_generate_l2_campaign_task_adds_attention_sram_profile_evidence() -> None:
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
                    item_id="l2_decoder_attention_sram_profile_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_sram_profile",
                    evaluation_mode="profile_measurement",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]

            assert "measure_decoder_attention_sram_profile" in command_names
            assert "attention_sram_metrics_json" in decoder_inputs
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith("decoder_attention_sram_profile__l2_decoder_attention_sram_profile_v1.json")
                for output in expected_outputs
            )
            assert "runs/designs/sram/llama7b_attention_tile_buffers_v1/sram_metrics.json" in expected_outputs


def test_generate_l2_campaign_task_adds_attention_local_sram_capacity_evidence() -> None:
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
                    item_id="l2_decoder_attention_local_sram_capacity_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_local_sram_capacity",
                    evaluation_mode="profile_measurement",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "measure_decoder_attention_local_sram_capacity" in command_names
            assert "attention_kv_endpoint_full_onchip_service_schedule" in decoder_inputs
            assert "attention_local_sram_capacity_metrics_json" in decoder_inputs
            assert "measure_llm_decoder_attention_local_sram_capacity.py" in run
            assert "l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_llama7b_v1.json" in run
            assert "--width-bits 1024" in run
            assert "--noc-bandwidth-bytes-per-cycle" not in run
            assert "--data-rate-mtps" not in run
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_local_sram_capacity__"
                    "l2_decoder_attention_local_sram_capacity_llama7b_v1.json"
                )
                for output in expected_outputs
            )
            assert "runs/designs/sram/llama7b_attention_local_capacity_v1/sram_metrics.json" in expected_outputs


def test_generate_l2_campaign_task_adds_attention_measured_sram_rebalance_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_measured_sram_rebalance_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_measured_sram_rebalance",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "estimate_decoder_attention_kv_measured_sram_rebalance" in command_names
            assert "attention_kv_endpoint_full_onchip_service_schedule" in decoder_inputs
            assert "attention_kv_endpoint_router_sram_composition" in decoder_inputs
            assert "attention_local_sram_capacity" in decoder_inputs
            assert "attention_kv_measured_sram_rebalance_out" in decoder_inputs
            assert "estimate_llm_decoder_attention_kv_measured_sram_rebalance.py" in run
            assert "l2_decoder_attention_local_sram_capacity_llama7b_v1.json" in run
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_measured_sram_rebalance__"
                    "l2_decoder_attention_kv_measured_sram_rebalance_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_attention_measured_hbm_service_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_measured_hbm_service_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_measured_hbm_service",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "estimate_decoder_attention_kv_measured_hbm_service" in command_names
            assert "attention_kv_measured_sram_rebalance" in decoder_inputs
            assert "attention_kv_measured_hbm_service_out" in decoder_inputs
            assert "estimate_llm_decoder_attention_kv_measured_hbm_service.py" in run
            assert "l2_decoder_attention_kv_measured_sram_rebalance_llama7b_v1.json" in run
            assert "--channel-count 4,8,16" in run
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_measured_hbm_service__"
                    "l2_decoder_attention_kv_measured_hbm_service_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_attention_noc_profile_evidence() -> None:
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
                    item_id="l2_decoder_attention_noc_profile_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_noc_profile",
                    evaluation_mode="profile_measurement",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]

            assert "measure_decoder_attention_noc_profile" in command_names
            assert "attention_noc_primitive_profile" in decoder_inputs
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith("decoder_attention_noc_profile__l2_decoder_attention_noc_profile_v1.json")
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_all_measured_l1_attention_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_all_measured_l1_clustered_schedule",
                    evaluation_mode="broad_ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]

            assert "estimate_decoder_attention_kv_all_measured_l1_clustered_schedule" in command_names
            assert "attention_kv_all_measured_l1_costs" in decoder_inputs
            assert "attention_softmax_weight_generator_promotion" in decoder_inputs
            assert "attention_sram_profile" in decoder_inputs
            assert "attention_noc_profile" in decoder_inputs
            assert "--measured-l1-costs runs/campaigns/npu/l1_measured_costs/llama7b_attention_local_costs_all_measured_v1.json" in commands[0]["run"]
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_all_measured_l1_clustered_schedule__"
                    "l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_dense_tile_all_measured_l1_attention_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule",
                    evaluation_mode="broad_ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]

            assert "estimate_decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule" in command_names
            assert "attention_kv_dense_tile_measured_compute" in decoder_inputs
            assert "attention_kv_all_measured_l1_costs" in decoder_inputs
            assert "attention_sram_profile" in decoder_inputs
            assert "attention_noc_profile" in decoder_inputs
            assert "--compute-source dense_gemm_tile" in commands[0]["run"]
            assert "--tag-substring npu_dense_gemm_tile_v2_scale_hier" in commands[0]["run"]
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule__"
                    "l2_decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_dense_tile_endpoint_measured_l1_attention_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule",
                    evaluation_mode="broad_ranking",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]

            assert "estimate_decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule" in command_names
            assert "attention_kv_dense_tile_measured_compute" in decoder_inputs
            assert "attention_kv_endpoint_measured_l1_costs" in decoder_inputs
            assert "attention_sram_profile" in decoder_inputs
            assert "attention_noc_profile" in decoder_inputs
            assert "llama7b_attention_local_costs_all_measured_endpoint_v1.json" in commands[0]["run"]
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule__"
                    "l2_decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule_v1.json"
                )
                for output in expected_outputs
            )
            assert work_item.expected_outputs == expected_outputs


def test_generate_l2_campaign_task_adds_dense_tile_reduction_noc_frontier_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_dense_tile_reduction_noc_frontier_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_dense_tile_reduction_noc_frontier",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]

            assert "estimate_decoder_attention_kv_dense_tile_reduction_noc_frontier" in command_names
            assert "attention_kv_dense_tile_all_measured_l1_clustered_schedule" in decoder_inputs
            assert "attention_sram_profile" in decoder_inputs
            assert "attention_noc_profile" in decoder_inputs
            assert "--compute-source dense_gemm_tile" in commands[0]["run"]
            assert "--compute-arch-list dense_gemm_16x8_k1_p1" in commands[0]["run"]
            assert "--noc-bandwidth-bytes-per-cycle 4096,8192,16384,32768,65536" in commands[0]["run"]
            assert "--reduction-strategy centralized_tile,owner_cluster,cluster_tree" in commands[0]["run"]
            assert "hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q10" in commands[0]["run"]
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_dense_tile_reduction_noc_frontier__"
                    "l2_decoder_attention_kv_dense_tile_reduction_noc_frontier_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_dense_tile_topology_scheduler_pairs_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_dense_tile_topology_scheduler_pairs_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_dense_tile_topology_scheduler_pairs",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]

            assert "estimate_decoder_attention_kv_dense_tile_topology_scheduler_pairs" in command_names
            assert "attention_kv_dense_tile_reduction_noc_frontier" in decoder_inputs
            assert "attention_kv_dense_tile_topology_scheduler_pairs_out" in decoder_inputs
            assert "estimate_llm_decoder_attention_kv_topology_scheduler_pairs.py" in commands[0]["run"]
            assert "--topology-list cluster_tree,mesh2d,ring,crossbar" in commands[0]["run"]
            assert "--scheduler-policy-list static_wave,locality_aware" in commands[0]["run"]
            assert "--link-width-bits-list 256,512,1024,2048" in commands[0]["run"]
            assert "l2_decoder_attention_kv_dense_tile_reduction_noc_frontier_llama7b_v1.json" in commands[0]["run"]
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_dense_tile_topology_scheduler_pairs__"
                    "l2_decoder_attention_kv_dense_tile_topology_scheduler_pairs_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_dense_tile_endpoint_topology_scheduler_pairs_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_dense_tile_endpoint_topology_scheduler_pairs_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_dense_tile_endpoint_topology_scheduler_pairs",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]

            assert "estimate_decoder_attention_kv_dense_tile_endpoint_topology_scheduler_pairs" in command_names
            assert "attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule" in decoder_inputs
            assert "attention_kv_dense_tile_endpoint_topology_scheduler_pairs_out" in decoder_inputs
            assert "estimate_llm_decoder_attention_kv_topology_scheduler_pairs.py" in commands[0]["run"]
            assert "decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule__" in commands[0]["run"]
            assert "--topology-list local_only,cluster_tree,mesh2d,ring,crossbar" in commands[0]["run"]
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert work_item.expected_outputs == expected_outputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_dense_tile_endpoint_topology_scheduler_pairs__"
                    "l2_decoder_attention_kv_dense_tile_endpoint_topology_scheduler_pairs_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_dense_tile_topology_derived_schedule_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_dense_tile_topology_derived_schedule_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_dense_tile_topology_derived_schedule",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]

            assert "estimate_decoder_attention_kv_dense_tile_topology_derived_schedule" in command_names
            assert "attention_kv_dense_tile_topology_scheduler_pairs" in decoder_inputs
            assert "attention_kv_dense_tile_topology_derived_schedule_out" in decoder_inputs
            assert "estimate_llm_decoder_attention_kv_topology_derived_schedule.py" in commands[0]["run"]
            assert "l2_decoder_attention_kv_dense_tile_topology_scheduler_pairs_llama7b_v1_r2.json" in commands[0]["run"]
            assert "--topology-row-limit 128" in commands[0]["run"]
            assert "--noc-bandwidth-bytes-per-cycle" not in commands[0]["run"]
            assert "--noc-hops" not in commands[0]["run"]
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_dense_tile_topology_derived_schedule__"
                    "l2_decoder_attention_kv_dense_tile_topology_derived_schedule_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_dense_tile_endpoint_topology_derived_schedule_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_dense_tile_endpoint_topology_derived_schedule_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_dense_tile_endpoint_topology_derived_schedule",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]

            assert "estimate_decoder_attention_kv_dense_tile_endpoint_topology_derived_schedule" in command_names
            assert "attention_kv_dense_tile_endpoint_topology_scheduler_pairs" in decoder_inputs
            assert "attention_kv_endpoint_measured_l1_costs" in decoder_inputs
            assert "estimate_llm_decoder_attention_kv_topology_derived_schedule.py" in commands[0]["run"]
            assert "l2_decoder_attention_kv_dense_tile_endpoint_topology_scheduler_pairs_llama7b_v1.json" in commands[0]["run"]
            assert "llama7b_attention_local_costs_all_measured_endpoint_v1.json" in commands[0]["run"]
            assert "--noc-bandwidth-bytes-per-cycle" not in commands[0]["run"]
            assert "--noc-hops" not in commands[0]["run"]
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert work_item.expected_outputs == expected_outputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_dense_tile_endpoint_topology_derived_schedule__"
                    "l2_decoder_attention_kv_dense_tile_endpoint_topology_derived_schedule_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_sram_noc_constrained_schedule_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_sram_noc_constrained_schedule_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_sram_noc_constrained_schedule",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]

            assert "estimate_decoder_attention_kv_sram_noc_constrained_schedule" in command_names
            assert "attention_kv_dense_tile_topology_derived_schedule" in decoder_inputs
            assert "attention_sram_profile" in decoder_inputs
            assert "attention_kv_sram_noc_constrained_schedule_out" in decoder_inputs
            assert "estimate_llm_decoder_attention_kv_sram_noc_constrained_schedule.py" in commands[0]["run"]
            assert "l2_decoder_attention_kv_dense_tile_topology_derived_schedule_llama7b_v1.json" in commands[0]["run"]
            assert "--sram-bank-port-bytes-per-cycle 32" in commands[0]["run"]
            assert "--endpoint-port-bytes-per-cycle 32,64,128" in commands[0]["run"]
            assert "--noc-bandwidth-bytes-per-cycle" not in commands[0]["run"]
            assert "--noc-hops" not in commands[0]["run"]
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_sram_noc_constrained_schedule__"
                    "l2_decoder_attention_kv_sram_noc_constrained_schedule_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_endpoint_sram_noc_constrained_schedule_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_endpoint_sram_noc_constrained_schedule_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_endpoint_sram_noc_constrained_schedule",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]

            assert "estimate_decoder_attention_kv_endpoint_sram_noc_constrained_schedule" in command_names
            assert "attention_kv_dense_tile_endpoint_topology_derived_schedule" in decoder_inputs
            assert "attention_sram_profile" in decoder_inputs
            assert "attention_kv_endpoint_sram_noc_constrained_schedule_out" in decoder_inputs
            assert "estimate_llm_decoder_attention_kv_sram_noc_constrained_schedule.py" in commands[0]["run"]
            assert "l2_decoder_attention_kv_dense_tile_endpoint_topology_derived_schedule_llama7b_v1_r3.json" in commands[0]["run"]
            assert "l2_decoder_attention_kv_dense_tile_topology_derived_schedule_llama7b_v1.json" not in commands[0]["run"]
            assert "--sram-bank-port-bytes-per-cycle 32" in commands[0]["run"]
            assert "--endpoint-port-bytes-per-cycle 32,64,128" in commands[0]["run"]
            assert "--noc-bandwidth-bytes-per-cycle" not in commands[0]["run"]
            assert "--noc-hops" not in commands[0]["run"]
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert work_item.expected_outputs == expected_outputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_endpoint_sram_noc_constrained_schedule__"
                    "l2_decoder_attention_kv_endpoint_sram_noc_constrained_schedule_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_endpoint_sram_noc_full_search_schedule_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_endpoint_sram_noc_full_search_schedule_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_endpoint_sram_noc_full_search_schedule",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "estimate_decoder_attention_kv_endpoint_sram_noc_full_search_schedule" in command_names
            assert "attention_kv_dense_tile_endpoint_topology_scheduler_pairs" in decoder_inputs
            assert "attention_kv_endpoint_measured_l1_costs" in decoder_inputs
            assert "attention_sram_profile" in decoder_inputs
            assert "attention_kv_endpoint_sram_noc_full_search_schedule_out" in decoder_inputs
            assert "estimate_llm_decoder_attention_kv_sram_noc_constrained_schedule.py" in run
            assert "--topology-pairs-json" in run
            assert "--topology-derived-json" not in run
            assert "l2_decoder_attention_kv_dense_tile_endpoint_topology_scheduler_pairs_llama7b_v1.json" in run
            assert "llama7b_attention_local_costs_all_measured_endpoint_v1.json" in run
            assert "--sram-bank-port-bytes-per-cycle 32" in run
            assert "--endpoint-port-bytes-per-cycle 32,64,128" in run
            assert "--topology-row-limit 128" in run
            assert "--noc-bandwidth-bytes-per-cycle" not in run
            assert "--noc-hops" not in run
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert work_item.expected_outputs == expected_outputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_endpoint_sram_noc_full_search_schedule__"
                    "l2_decoder_attention_kv_endpoint_sram_noc_full_search_schedule_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_onchip_service_schedule_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_onchip_service_schedule_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_onchip_service_schedule",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]

            assert "estimate_decoder_attention_kv_onchip_service_schedule" in command_names
            assert "attention_kv_sram_noc_constrained_schedule" in decoder_inputs
            assert "attention_kv_onchip_service_schedule_out" in decoder_inputs
            assert "estimate_llm_decoder_attention_kv_onchip_service_schedule.py" in commands[0]["run"]
            assert "l2_decoder_attention_kv_sram_noc_constrained_schedule_llama7b_v1_r2.json" in commands[0]["run"]
            assert "--schedule-policy static_wave,staggered_wave,prefetch_overlap" in commands[0]["run"]
            assert "--endpoint-queue-depth-bytes 2048,8192,32768" in commands[0]["run"]
            assert "--router-latency-cycles-per-hop 1,2" in commands[0]["run"]
            assert "--noc-bandwidth-bytes-per-cycle" not in commands[0]["run"]
            assert "--data-rate-mtps" not in commands[0]["run"]
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_onchip_service_schedule__"
                    "l2_decoder_attention_kv_onchip_service_schedule_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_endpoint_full_onchip_service_schedule_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_endpoint_full_onchip_service_schedule",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "estimate_decoder_attention_kv_endpoint_full_onchip_service_schedule" in command_names
            assert "attention_kv_endpoint_sram_noc_full_search_schedule" in decoder_inputs
            assert "attention_kv_endpoint_full_onchip_service_schedule_out" in decoder_inputs
            assert "estimate_llm_decoder_attention_kv_onchip_service_schedule.py" in run
            assert "l2_decoder_attention_kv_endpoint_sram_noc_full_search_schedule_llama7b_v1.json" in run
            assert "l2_decoder_attention_kv_sram_noc_constrained_schedule_llama7b_v1_r2.json" not in run
            assert "--schedule-policy static_wave,staggered_wave,prefetch_overlap" in run
            assert "--endpoint-queue-depth-bytes 2048,8192,32768" in run
            assert "--router-latency-cycles-per-hop 1,2" in run
            assert "--noc-bandwidth-bytes-per-cycle" not in run
            assert "--data-rate-mtps" not in run
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert work_item.expected_outputs == expected_outputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_endpoint_full_onchip_service_schedule__"
                    "l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_endpoint_ready_valid_service_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_endpoint_ready_valid_service_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_endpoint_ready_valid_service",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "probe_decoder_attention_kv_endpoint_ready_valid_service" in command_names
            assert "attention_kv_endpoint_full_onchip_service_schedule" in decoder_inputs
            assert "attention_kv_endpoint_ready_valid_service_out" in decoder_inputs
            assert "probe_llm_decoder_attention_endpoint_ready_valid.py" in run
            assert "l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_llama7b_v1.json" in run
            assert "l2_decoder_attention_kv_endpoint_sram_noc_full_search_schedule_llama7b_v1.json" not in run
            assert "--noc-bandwidth-bytes-per-cycle" not in run
            assert "--data-rate-mtps" not in run
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert work_item.expected_outputs == expected_outputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_endpoint_ready_valid_service__"
                    "l2_decoder_attention_kv_endpoint_ready_valid_service_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_endpoint_router_sram_composition_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_endpoint_router_sram_composition_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_endpoint_router_sram_composition",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "audit_decoder_attention_kv_endpoint_router_sram_composition" in command_names
            assert "attention_kv_endpoint_ready_valid_service" in decoder_inputs
            assert "attention_kv_endpoint_full_onchip_service_schedule" in decoder_inputs
            assert "attention_kv_tile_sram_metrics_summary" in decoder_inputs
            assert "attention_kv_endpoint_router_sram_composition_out" in decoder_inputs
            assert "audit_llm_decoder_attention_endpoint_router_sram_composition.py" in run
            assert "l2_decoder_attention_kv_endpoint_ready_valid_service_llama7b_v1.json" in run
            assert "l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_llama7b_v1.json" in run
            assert "llama7b_attention_tile_buffers_v1/sram_metrics_summary.json" in run
            assert "--noc-bandwidth-bytes-per-cycle" not in run
            assert "--data-rate-mtps" not in run
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert work_item.expected_outputs == expected_outputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_endpoint_router_sram_composition__"
                    "l2_decoder_attention_kv_endpoint_router_sram_composition_llama7b_v1.json"
                )
                for output in expected_outputs
            )

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
            assert decoder_inputs["streaming_hierarchy_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_logit_rank_streaming_hierarchy__l2_decoder_logit_rank_streaming_hierarchy_v1.json"
            )
            assert "avoids full-vocabulary probability materialization" in decoder_inputs["streaming_hierarchy_scope"]
            assert "estimate_llm_decoder_logit_rank_streaming_hierarchy.py" in work_item.command_manifest[0]["run"]
            assert "--scale-ppa control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_scale_v1.json" in work_item.command_manifest[0]["run"]
            assert "--candidate-merge-ppa control_plane/shadow_exports/l1_promotions/l1_decoder_candidate_stream_merge_fifo_v1.json" in work_item.command_manifest[0]["run"]
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
            assert decoder_inputs["memory_model"] == {
                "memory_bandwidth_bytes_per_cycle": 64,
                "sram_read_energy_pj_per_byte": 0.05,
                "sram_write_energy_pj_per_byte": 0.07,
                "noc_hops": 2,
                "noc_energy_pj_per_byte_hop": 0.02,
                "source": "planning_default_not_literature_backed",
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
            assert "--producer-lanes-list 8,16,32" in run
            assert "--top-k-list 1,4" in run
            assert "--producer-ii-cycles-list 1,2,4" in run
            assert "--candidate-fifo-depth-groups-list 16,256,4096" in run
            assert "--noc-hops 2" in run
            assert "--memory-bandwidth-bytes-per-cycle 64" in run
            assert decoder_inputs["streaming_overlap_out"] in work_item.expected_outputs
            assert decoder_inputs["streaming_overlap_report"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_logit_rank_streaming_overlap",
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

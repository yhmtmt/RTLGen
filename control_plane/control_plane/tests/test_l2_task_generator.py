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


def _write_q20_pwl_recip_div_recost_proposal(repo_root: Path) -> None:
    proposal_dir = (
        repo_root
        / "docs"
        / "proposals"
        / "prop_l2_decoder_attention_composed_datapath_q20_pwl_recip_div_reduced_replica_v1"
    )
    proposal_dir.mkdir(parents=True)
    proposal_id = "prop_l2_decoder_attention_composed_datapath_q20_pwl_recip_div_reduced_replica_v1"
    item_id = "l2_decoder_attention_composed_datapath_q20_pwl_recip_div_reduced_replica_llama7b_v1"
    proposal_dir.joinpath("proposal.json").write_text(
        json.dumps(
            {
                "proposal_id": proposal_id,
                "required_evaluations": [
                    {
                        "item_id": item_id,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    proposal_dir.joinpath("evaluation_requests.json").write_text(
        json.dumps(
            {
                "proposal_id": proposal_id,
                "requested_items": [
                    {
                        "item_id": item_id,
                        "evaluation_mode": "frontier_detail",
                        "abstraction_layer": "decoder_attention_composed_datapath_physical_feasibility",
                        "comparison_role": "q20_pwl_recip_div_reduced_replica_recost",
                        "paired_baseline_item_id": (
                            "l2_decoder_attention_composed_datapath_score32_w16_recip_lut_q16_reduced_replica_llama7b_v1"
                        ),
                        "depends_on_item_ids": [
                            "l1_decoder_attention_dual_stream_composed_q20_pwl_recip_div_ppa_v2",
                            "l2_decoder_attention_composed_datapath_score32_w16_recip_lut_q16_reduced_replica_llama7b_v1",
                            "l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1",
                        ],
                        "requires_merged_inputs": True,
                        "requires_materialized_refs": True,
                        "expected_result": {
                            "direction": "record_q20_pwl_recip_div_area_fit_recost",
                            "reason": "q20 boundary recost",
                        },
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )


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


def test_generate_l2_campaign_task_adds_decoder_attention_kv_physical_hbm_quality_backed_7b() -> None:
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
                    item_id="l2_decoder_attention_kv_physical_hbm_quality_backed_7b_llama7b_v1",
                    proposal_id="prop_l2_decoder_attention_kv_physical_hbm_quality_backed_7b_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_kv_physical_hbm_quality_backed_7b_llama7b_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_attention_kv_physical_hbm_quality_backed_7b",
                    expected_direction="iterate",
                    comparison_role="frontier_synthesis",
                    depends_on_item_ids=["l2_decoder_attention_kv_model_native_quality_7b_v1"],
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest[:1]] == [
                "estimate_decoder_attention_kv_physical_hbm_quality_backed_7b",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_attention_kv_physical_hbm_frontier.py" in run
            assert "--kv-sharing-list gqa8" in run
            assert "--kv-bits-list 16,8" in run
            assert "--kv-bits-list 16,8,4" not in run
            assert (
                "--quality-gate-json "
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_model_native_quality_7b__"
                "l2_decoder_attention_kv_model_native_quality_7b_v1.json"
            ) in run
            assert decoder_inputs["attention_kv_memory_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_physical_hbm_quality_backed_7b__"
                "l2_decoder_attention_kv_physical_hbm_quality_backed_7b_llama7b_v1.json"
            )
            assert decoder_inputs["attention_kv_model_native_quality_7b"].endswith(
                "decoder_attention_kv_model_native_quality_7b__"
                "l2_decoder_attention_kv_model_native_quality_7b_v1.json"
            )
            assert (
                "7B-native-quality-backed physical-HBM"
                in decoder_inputs["attention_kv_physical_hbm_quality_backed_7b_scope"]
            )
            assert decoder_inputs["attention_kv_memory_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_kv_physical_hbm_quality_backed_7b",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": ["l2_decoder_attention_kv_model_native_quality_7b_v1"],
                "requires_merged_inputs": False,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_decoder_attention_kv_physical_hbm_quality_backed_7b_retry_dependency() -> None:
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
                    item_id="l2_decoder_attention_kv_physical_hbm_quality_backed_7b_llama7b_v1_r2",
                    proposal_id="prop_l2_decoder_attention_kv_physical_hbm_quality_backed_7b_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_kv_physical_hbm_quality_backed_7b_llama7b_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_attention_kv_physical_hbm_quality_backed_7b",
                    comparison_role="frontier_synthesis",
                    depends_on_item_ids=["l2_decoder_attention_kv_model_native_quality_7b_v1_r2"],
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            run = work_item.command_manifest[0]["run"]
            assert "estimate_llm_decoder_attention_kv_physical_hbm_frontier.py" in run
            assert (
                "--quality-gate-json "
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_model_native_quality_7b__"
                "l2_decoder_attention_kv_model_native_quality_7b_v1_r2.json"
            ) in run
            assert decoder_inputs["attention_kv_model_native_quality_7b"].endswith(
                "decoder_attention_kv_model_native_quality_7b__"
                "l2_decoder_attention_kv_model_native_quality_7b_v1_r2.json"
            )
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": ["l2_decoder_attention_kv_model_native_quality_7b_v1_r2"],
                "requires_merged_inputs": False,
                "requires_materialized_refs": True,
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
            assert decoder_inputs["attention_kv_model_native_quality_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_model_native_quality__"
                "l2_decoder_attention_kv_model_native_quality_tinyllama_v1.json"
            )
            assert decoder_inputs["attention_kv_trace_calibration"].endswith(
                "decoder_attention_kv_trace_calibration__l2_decoder_attention_kv_trace_calibration_v1.json"
            )
            assert "teacher-forced decode" in decoder_inputs["attention_kv_model_native_quality_scope"]
            assert decoder_inputs["attention_kv_model_native_quality_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_kv_model_native_quality",
            }


def test_generate_l2_campaign_task_adds_decoder_attention_kv_model_native_quality_7b() -> None:
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
                    item_id="l2_decoder_attention_kv_model_native_quality_7b_v1",
                    proposal_id="prop_l2_decoder_attention_kv_model_native_quality_7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_kv_model_native_quality_7b_v1/proposal.json"
                    ),
                    evaluation_mode="frontier_detail",
                    abstraction_layer="decoder_attention_kv_model_native_quality_7b",
                    expected_direction="iterate",
                    comparison_role="frontier_synthesis",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            assert [command["name"] for command in work_item.command_manifest] == [
                "evaluate_decoder_attention_kv_model_native_quality_7b",
                "validate_runs",
            ]
            run = work_item.command_manifest[0]["run"]
            assert "RTLGEN_MODEL_NATIVE_7B_MODEL_ID" in run
            assert "mistralai/Mistral-7B-v0.1" in run
            assert "RTLGEN_MODEL_NATIVE_7B_EXPECTED_GQA_GROUP_SIZE" in run
            assert "RTLGEN_MODEL_NATIVE_7B_MAX_PROMPTS" in run
            assert "RTLGEN_MODEL_NATIVE_7B_GENERATION_STEPS" in run
            assert "RTLGEN_MODEL_NATIVE_7B_DTYPE" in run
            assert run.startswith("bash -lc '")
            assert "run_hf_eval_python.sh" in run
            assert "evaluate_llm_decoder_model_native_kv_quant.py" in run
            assert "--model-id \"$MODEL_ID\"" in run
            assert "--expected-gqa-group-size \"$EXPECTED_GQA\"" in run
            assert "--kv-bits-list 8,4" in run
            assert "--kv-granularity-list tensor" in run
            assert "--max-prompts \"$MAX_PROMPTS\"" in run
            assert "--generation-steps \"$GENERATION_STEPS\"" in run
            assert "--dtype \"$DTYPE\"" in run
            assert decoder_inputs["attention_kv_model_native_quality_7b_out"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_model_native_quality_7b__"
                "l2_decoder_attention_kv_model_native_quality_7b_v1.json"
            )
            assert "generated_campaign" not in work_item.input_manifest
            assert decoder_inputs["attention_kv_trace_calibration"].endswith(
                "decoder_attention_kv_trace_calibration__l2_decoder_attention_kv_trace_calibration_v1.json"
            )
            assert "7B-class trained checkpoint" in decoder_inputs["attention_kv_model_native_quality_7b_scope"]
            assert "RTLGEN_MODEL_NATIVE_7B_MODEL_ID" in decoder_inputs["attention_kv_model_native_quality_7b_scope"]
            assert work_item.expected_outputs == [
                (
                    "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                    "decoder_attention_kv_model_native_quality_7b__"
                    "l2_decoder_attention_kv_model_native_quality_7b_v1.json"
                ),
                (
                    "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                    "decoder_attention_kv_model_native_quality_7b__"
                    "l2_decoder_attention_kv_model_native_quality_7b_v1.md"
                ),
            ]
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_kv_model_native_quality_7b",
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


def test_generate_l2_campaign_task_can_refresh_db_without_updating_proposal_files() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        campaign_path = _write_campaign(repo_root)
        source_commit = _init_git_repo(repo_root)
        proposal_dir = repo_root / "docs" / "developer_loop" / "prop_l2_demo_v1"
        proposal_dir.mkdir(parents=True, exist_ok=True)
        evaluation_requests_path = proposal_dir / "evaluation_requests.json"
        evaluation_requests_path.write_text(
            json.dumps(
                {
                    "proposal_id": "prop_l2_demo_v1",
                    "source_commit": "previous",
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
        before = evaluation_requests_path.read_text(encoding="utf-8")
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
                    source_commit=source_commit,
                    proposal_id="prop_l2_demo_v1",
                    proposal_path="docs/developer_loop/prop_l2_demo_v1",
                    update_proposal_files=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            payload = work_item.task_request.request_payload
            assert result.status == "applied"
            assert work_item.source_commit == source_commit
            assert work_item.task_request.source_commit == source_commit
            assert payload["developer_loop"]["evaluation"]["mode"] == "paired_comparison"
            assert payload["developer_loop"]["abstraction"]["layer"] == "full_architecture"
            assert payload["developer_loop"]["dependencies"] == {
                "item_ids": ["l2_demo_baseline_r1"],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }

        assert evaluation_requests_path.read_text(encoding="utf-8") == before


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
            assert (
                "l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_llama7b_v1.json"
                in run
            )
            assert (
                "l2_decoder_attention_kv_endpoint_router_sram_composition_llama7b_v1.json"
                in run
            )
            assert (
                "l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1_r2.json"
                not in run
            )
            assert (
                "l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_r4.json"
                not in run
            )
            assert "l2_decoder_attention_local_sram_capacity_llama7b_v1.json" in run
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_measured_sram_rebalance__"
                    "l2_decoder_attention_kv_measured_sram_rebalance_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_softmax_recip_lut_measured_sram_rebalance_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_measured_sram_rebalance_softmax_recip_lut_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_measured_sram_rebalance",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert (
                "l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1_r2.json"
                in run
            )
            assert (
                "l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_r4.json"
                in run
            )
            assert "l2_decoder_attention_local_sram_capacity_llama7b_v1.json" in run
            assert (
                "l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_llama7b_v1.json"
                not in run
            )
            assert (
                "l2_decoder_attention_kv_endpoint_router_sram_composition_llama7b_v1.json"
                not in run
            )
            assert any(
                output.endswith(
                    "decoder_attention_kv_measured_sram_rebalance__"
                    "l2_decoder_attention_kv_measured_sram_rebalance_softmax_recip_lut_llama7b_v1.json"
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


def test_generate_l2_campaign_task_adds_softmax_recip_lut_measured_hbm_service_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_measured_hbm_service_softmax_recip_lut_llama7b_v1",
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
            assert (
                "l2_decoder_attention_kv_measured_sram_rebalance_softmax_recip_lut_llama7b_v1.json"
                in run
            )
            assert (
                "l2_decoder_attention_kv_measured_sram_rebalance_llama7b_v1.json"
                not in run
            )
            assert "--channel-count 4,8,16" in run
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_measured_hbm_service__"
                    "l2_decoder_attention_kv_measured_hbm_service_softmax_recip_lut_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_attention_hbm_closed_onchip_schedule_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_hbm_closed_onchip_schedule_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_hbm_closed_onchip_schedule",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "estimate_decoder_attention_kv_hbm_closed_onchip_schedule" in command_names
            assert "attention_kv_measured_hbm_service" in decoder_inputs
            assert "attention_kv_hbm_closed_onchip_schedule_out" in decoder_inputs
            assert "estimate_llm_decoder_attention_kv_hbm_closed_onchip_schedule.py" in run
            assert "l2_decoder_attention_kv_measured_hbm_service_llama7b_v1.json" in run
            assert "--router-latency-cycles-per-hop 1,2,4" in run
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_hbm_closed_onchip_schedule__"
                    "l2_decoder_attention_kv_hbm_closed_onchip_schedule_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_softmax_recip_lut_hbm_closed_onchip_schedule_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_hbm_closed_onchip_schedule",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "estimate_decoder_attention_kv_hbm_closed_onchip_schedule" in command_names
            assert "attention_kv_measured_hbm_service" in decoder_inputs
            assert "attention_kv_hbm_closed_onchip_schedule_out" in decoder_inputs
            assert "estimate_llm_decoder_attention_kv_hbm_closed_onchip_schedule.py" in run
            assert (
                "l2_decoder_attention_kv_measured_hbm_service_softmax_recip_lut_llama7b_v1.json"
                in run
            )
            assert (
                "l2_decoder_attention_kv_measured_hbm_service_llama7b_v1.json"
                not in run
            )
            assert "--router-latency-cycles-per-hop 1,2,4" in run
            assert (
                decoder_inputs["attention_kv_measured_hbm_service"]
                == "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_measured_hbm_service__"
                "l2_decoder_attention_kv_measured_hbm_service_softmax_recip_lut_llama7b_v1.json"
            )
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_hbm_closed_onchip_schedule__"
                    "l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_attention_subtile_pipeline_schedule_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_subtile_pipeline_schedule_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_subtile_pipeline_schedule",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "estimate_decoder_attention_kv_subtile_pipeline_schedule" in command_names
            assert "attention_kv_hbm_closed_onchip_schedule" in decoder_inputs
            assert "attention_kv_subtile_pipeline_schedule_out" in decoder_inputs
            assert "estimate_llm_decoder_attention_kv_subtile_pipeline_schedule.py" in run
            assert "l2_decoder_attention_kv_hbm_closed_onchip_schedule_llama7b_v1.json" in run
            assert "--compute-mode shared_mac,split_mac,dual_mac" in run
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_subtile_pipeline_schedule__"
                    "l2_decoder_attention_kv_subtile_pipeline_schedule_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_softmax_recip_lut_subtile_pipeline_schedule_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_subtile_pipeline_schedule",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "estimate_decoder_attention_kv_subtile_pipeline_schedule" in command_names
            assert "attention_kv_hbm_closed_onchip_schedule" in decoder_inputs
            assert "attention_kv_subtile_pipeline_schedule_out" in decoder_inputs
            assert "estimate_llm_decoder_attention_kv_subtile_pipeline_schedule.py" in run
            assert (
                "l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1.json"
                in run
            )
            assert (
                "l2_decoder_attention_kv_hbm_closed_onchip_schedule_llama7b_v1.json"
                not in run
            )
            assert (
                decoder_inputs["attention_kv_hbm_closed_onchip_schedule"]
                == "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_hbm_closed_onchip_schedule__"
                "l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1.json"
            )
            assert "--compute-mode shared_mac,split_mac,dual_mac" in run
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_subtile_pipeline_schedule__"
                    "l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_attention_dual_stream_physical_feasibility_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_dual_stream_physical_feasibility_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_dual_stream_physical_feasibility",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "estimate_decoder_attention_kv_dual_stream_physical_feasibility" in command_names
            assert "attention_kv_subtile_pipeline_schedule" in decoder_inputs
            assert "attention_kv_full_value_tile_metrics" in decoder_inputs
            assert "attention_kv_softmax_weight_metrics" in decoder_inputs
            assert "attention_kv_dual_stream_physical_feasibility_out" in decoder_inputs
            assert "estimate_llm_decoder_attention_kv_dual_stream_physical_feasibility.py" in run
            assert "l2_decoder_attention_kv_subtile_pipeline_schedule_llama7b_v1.json" in run
            assert "attention_kv_full_value_hd64_kv8_tl16_b128_p8_ppc2_w24_a40_wrapper/metrics.csv" in run
            assert "--buffer-area-um2-per-byte 0.0" in run
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_dual_stream_physical_feasibility__"
                    "l2_decoder_attention_kv_dual_stream_physical_feasibility_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_softmax_recip_lut_dual_stream_physical_feasibility_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_dual_stream_physical_feasibility_softmax_recip_lut_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_dual_stream_physical_feasibility",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "estimate_decoder_attention_kv_dual_stream_physical_feasibility" in command_names
            assert "attention_kv_subtile_pipeline_schedule" in decoder_inputs
            assert "attention_kv_full_value_tile_metrics" in decoder_inputs
            assert "attention_kv_softmax_weight_metrics" in decoder_inputs
            assert "attention_kv_dual_stream_physical_feasibility_out" in decoder_inputs
            assert "estimate_llm_decoder_attention_kv_dual_stream_physical_feasibility.py" in run
            assert (
                "decoder_attention_kv_subtile_pipeline_schedule__"
                "l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1.json"
                in run
            )
            assert (
                "decoder_attention_kv_subtile_pipeline_schedule__"
                "l2_decoder_attention_kv_subtile_pipeline_schedule_llama7b_v1.json"
                not in run
            )
            assert (
                decoder_inputs["attention_kv_subtile_pipeline_schedule"]
                == "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_subtile_pipeline_schedule__"
                "l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1.json"
            )
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_dual_stream_physical_feasibility__"
                    "l2_decoder_attention_kv_dual_stream_physical_feasibility_softmax_recip_lut_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_attention_composed_datapath_physical_feasibility_evidence() -> None:
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
                    item_id="l2_decoder_attention_composed_datapath_physical_feasibility_softmax_recip_lut_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_composed_datapath_physical_feasibility",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "estimate_decoder_attention_composed_datapath_physical_feasibility" in command_names
            assert "attention_kv_subtile_pipeline_schedule" in decoder_inputs
            assert "attention_kv_composed_dual_stream_metrics" in decoder_inputs
            assert "attention_composed_datapath_physical_feasibility_out" in decoder_inputs
            assert "attention_composed_datapath_physical_feasibility_report" in decoder_inputs
            assert "estimate_llm_decoder_attention_kv_dual_stream_physical_feasibility.py" in run
            assert (
                "attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/metrics.csv"
                in run
            )
            assert (
                "--model-name llm_decoder_attention_composed_datapath_physical_feasibility_softmax_recip_lut_llama7b_v1"
                in run
            )
            assert "--precision-profile q8_k8_v6_a24_s8_w8_recip_lut_q10_int8_compute" in run
            assert any(
                output.endswith(
                    "decoder_attention_composed_datapath_physical_feasibility__"
                    "l2_decoder_attention_composed_datapath_physical_feasibility_softmax_recip_lut_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_attention_composed_datapath_variant_frontier_evidence() -> None:
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
                    item_id="l2_decoder_attention_composed_datapath_recip_lut_variant_frontier_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_composed_datapath_physical_feasibility",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert "estimate_decoder_attention_composed_datapath_physical_feasibility" in [c["name"] for c in commands]
            assert (
                "--model-name llm_decoder_attention_composed_datapath_recip_lut_variant_frontier_llama7b_v1"
                in run
            )
            composed_dual_stream_metrics = decoder_inputs["attention_kv_composed_dual_stream_metrics"]
            assert set(
                composed_dual_stream_metrics.split(",")
            ) == {
                "runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/metrics.csv",
                "runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/metrics.csv",
                "runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/metrics.csv",
            }
            assert (
                "--composed-dual-stream-metrics runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/metrics.csv "
                in run
            )
            assert (
                "--composed-dual-stream-metrics runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/metrics.csv "
                in run
            )
            assert (
                "--composed-dual-stream-metrics runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q12/metrics.csv "
                in run
            )
            assert any(
                output.endswith(
                    "decoder_attention_composed_datapath_physical_feasibility__"
                    "l2_decoder_attention_composed_datapath_recip_lut_variant_frontier_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )


def test_generate_l2_campaign_task_adds_attention_composed_datapath_q12_pwl_frontier_evidence() -> None:
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
                    item_id="l2_decoder_attention_composed_datapath_q12_pwl_softmax_frontier_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_composed_datapath_physical_feasibility",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert "estimate_decoder_attention_composed_datapath_physical_feasibility" in [c["name"] for c in commands]
            assert (
                "--model-name llm_decoder_attention_composed_datapath_q12_pwl_softmax_frontier_llama7b_v1"
                in run
            )
            assert "--precision-profile q8_k8_v6_a24_s12_w12_pwl_recip_q12_int8_compute" in run
            composed_dual_stream_metrics = decoder_inputs["attention_kv_composed_dual_stream_metrics"]
            assert composed_dual_stream_metrics == (
                "runs/designs/npu_blocks/"
                "attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_q12_pwl_recip_q12/metrics.csv"
            )
            assert (
                "--composed-dual-stream-metrics runs/designs/npu_blocks/"
                "attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_q12_pwl_recip_q12/metrics.csv "
                in run
            )
            assert any(
                output.endswith(
                    "decoder_attention_composed_datapath_physical_feasibility__"
                    "l2_decoder_attention_composed_datapath_q12_pwl_softmax_frontier_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )


def test_generate_l2_campaign_task_adds_attention_composed_datapath_q20_pwl_recip_div_recost_evidence() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        campaign_path = _write_campaign(repo_root)
        _write_q20_pwl_recip_div_recost_proposal(repo_root)
        source_commit = _init_git_repo(repo_root)
        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)

        with Session(engine) as session:
            result = generate_l2_campaign_task(
                session,
                Layer2CampaignGenerateRequest(
                    repo_root=str(repo_root),
                    campaign_path=campaign_path,
                    item_id="l2_decoder_attention_composed_datapath_q20_pwl_recip_div_reduced_replica_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_composed_datapath_physical_feasibility",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            payload = work_item.task_request.request_payload

            assert "estimate_decoder_attention_composed_datapath_physical_feasibility" in [c["name"] for c in commands]
            assert (
                "--model-name llm_decoder_attention_composed_datapath_q20_pwl_recip_div_reduced_replica_llama7b_v1"
                in run
            )
            assert "--recompute-area-fit-replicas" in run
            assert "--precision-profile q8_k8_v8_a24_s20_w20_pwl_recip_div_q20_int8_compute" in run
            assert payload["developer_loop"]["proposal_id"] == (
                "prop_l2_decoder_attention_composed_datapath_q20_pwl_recip_div_reduced_replica_v1"
            )
            assert payload["developer_loop"]["proposal_path"] == (
                "docs/proposals/prop_l2_decoder_attention_composed_datapath_q20_pwl_recip_div_reduced_replica_v1"
            )
            assert payload["developer_loop"]["comparison"]["role"] == "q20_pwl_recip_div_reduced_replica_recost"
            assert payload["developer_loop"]["dependencies"]["item_ids"] == [
                "l1_decoder_attention_dual_stream_composed_q20_pwl_recip_div_ppa_v2",
                "l2_decoder_attention_composed_datapath_score32_w16_recip_lut_q16_reduced_replica_llama7b_v1",
                "l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1",
            ]
            assert payload["developer_loop"]["evaluation"]["expected_direction"] == (
                "record_q20_pwl_recip_div_area_fit_recost"
            )
            assert payload["developer_loop"]["evaluation"]["expected_reason"] == "q20 boundary recost"
            assert decoder_inputs["attention_kv_composed_dual_stream_metrics"] == (
                "runs/designs/npu_blocks/"
                "attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/"
                "metrics.csv"
            )
            assert (
                "--composed-dual-stream-metrics runs/designs/npu_blocks/"
                "attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/"
                "metrics.csv "
                in run
            )
            assert any(
                output.endswith(
                    "decoder_attention_composed_datapath_physical_feasibility__"
                    "l2_decoder_attention_composed_datapath_q20_pwl_recip_div_reduced_replica_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )


def test_generate_l2_campaign_task_adds_attention_composed_datapath_score32_frontier_evidence() -> None:
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
                    item_id="l2_decoder_attention_composed_datapath_score32_w16_exact_div_frontier_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_composed_datapath_physical_feasibility",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert "estimate_decoder_attention_composed_datapath_physical_feasibility" in [c["name"] for c in commands]
            assert (
                "--model-name llm_decoder_attention_composed_datapath_score32_w16_exact_div_frontier_llama7b_v1"
                in run
            )
            assert "--precision-profile q8_k8_v8_a32_s32_w16_exact_div_int8_compute" in run
            composed_dual_stream_metrics = decoder_inputs["attention_kv_composed_dual_stream_metrics"]
            assert composed_dual_stream_metrics == (
                "runs/designs/npu_blocks/"
                "attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/metrics.csv"
            )
            assert (
                "--composed-dual-stream-metrics runs/designs/npu_blocks/"
                "attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/metrics.csv "
                in run
            )
            assert any(
                output.endswith(
                    "decoder_attention_composed_datapath_physical_feasibility__"
                    "l2_decoder_attention_composed_datapath_score32_w16_exact_div_frontier_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )


def test_generate_l2_campaign_task_adds_attention_composed_datapath_score32_reduced_replica_evidence() -> None:
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
                    item_id="l2_decoder_attention_composed_datapath_score32_w16_exact_div_reduced_replica_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_composed_datapath_physical_feasibility",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert "estimate_decoder_attention_composed_datapath_physical_feasibility" in [c["name"] for c in commands]
            assert (
                "--model-name llm_decoder_attention_composed_datapath_score32_w16_exact_div_reduced_replica_llama7b_v1"
                in run
            )
            assert "--recompute-area-fit-replicas" in run
            assert "--precision-profile q8_k8_v8_a32_s32_w16_exact_div_int8_compute" in run
            assert decoder_inputs["attention_kv_composed_dual_stream_metrics"] == (
                "runs/designs/npu_blocks/"
                "attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/metrics.csv"
            )
            assert any(
                output.endswith(
                    "decoder_attention_composed_datapath_physical_feasibility__"
                    "l2_decoder_attention_composed_datapath_score32_w16_exact_div_reduced_replica_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )


def test_generate_l2_campaign_task_adds_attention_composed_datapath_exp_lut_command_overhead() -> None:
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
                    item_id=(
                        "l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_"
                        "command_overhead_llama7b_v1"
                    ),
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_composed_datapath_physical_feasibility",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            gate_run = commands[0]["run"]
            run = commands[1]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert commands[0]["name"] == "check_attention_score32_exp_lut_div_frontier_release"
            assert "estimate_decoder_attention_composed_datapath_physical_feasibility" in [c["name"] for c in commands]
            assert "npu/eval/check_attention_exp_lut_frontier_release.py" in gate_run
            assert "--expected-candidate-id" not in gate_run
            assert decoder_inputs["attention_score32_exp_lut_div_frontier_release_gate"].endswith(
                "decoder_attention_score32_exp_lut_div_frontier_release_gate__"
                "l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_"
                "command_overhead_llama7b_v1.json"
            )
            assert decoder_inputs["attention_score32_exp_lut_div_composed_config"] == (
                "runs/designs/npu_blocks/"
                "attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/"
                "config.json"
            )
            assert (
                "--model-name llm_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_llama7b_v1_command_overhead"
                in run
            )
            assert "--recompute-area-fit-replicas" in run
            assert "--command-cycles-per-tile 0,1,4,16" in run
            assert "--command-cycles-per-wave 0,8,32" in run
            assert "--precision-profile q8_k8_v8_a32_s32_w16_exp_lut_div_b20_int8_compute" in run
            assert decoder_inputs["attention_mixed_int8_score32_exp_lut_div_generation_quality"].endswith(
                "decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality__"
                "l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1.json"
            )
            assert decoder_inputs["attention_kv_composed_dual_stream_metrics"] == (
                "runs/designs/npu_blocks/"
                "attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/"
                "metrics.csv"
            )
            assert any(
                output.endswith(
                    "decoder_attention_score32_exp_lut_div_frontier_release_gate__"
                    "l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_"
                    "command_overhead_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )
            assert any(
                output.endswith(
                    "decoder_attention_composed_datapath_physical_feasibility__"
                    "l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_"
                    "command_overhead_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )


def test_generate_l2_campaign_task_adds_attention_composed_datapath_exp_lut_measured_command_control() -> None:
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
                    item_id=(
                        "l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_"
                        "measured_command_control_llama7b_v1"
                    ),
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_composed_datapath_physical_feasibility",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            gate_run = commands[0]["run"]
            run = commands[1]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert commands[0]["name"] == "check_attention_score32_exp_lut_div_frontier_release"
            assert "estimate_decoder_attention_composed_datapath_physical_feasibility" in [c["name"] for c in commands]
            assert "npu/eval/check_attention_exp_lut_frontier_release.py" in gate_run
            assert decoder_inputs["attention_score32_exp_lut_div_frontier_release_gate"].endswith(
                "decoder_attention_score32_exp_lut_div_frontier_release_gate__"
                "l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_"
                "measured_command_control_llama7b_v1.json"
            )
            assert (
                "--model-name llm_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_llama7b_v1_measured_command_control"
                in run
            )
            assert "--recompute-area-fit-replicas" in run
            assert "--command-cycles-per-tile" not in run
            assert "--command-cycles-per-wave" not in run
            assert "--command-dispatch-control-metrics runs/designs/npu_blocks/attention_command_dispatch_c8_q16/metrics.csv" in run
            assert "--command-dispatch-control-metrics runs/designs/npu_blocks/attention_command_dispatch_c16_q32/metrics.csv" in run
            assert "--command-dispatch-control-metrics runs/designs/npu_blocks/attention_command_dispatch_c32_q64/metrics.csv" in run
            assert decoder_inputs["attention_command_dispatch_control_metrics"] == (
                "runs/designs/npu_blocks/attention_command_dispatch_c8_q16/metrics.csv,"
                "runs/designs/npu_blocks/attention_command_dispatch_c16_q32/metrics.csv,"
                "runs/designs/npu_blocks/attention_command_dispatch_c32_q64/metrics.csv"
            )
            assert decoder_inputs["attention_mixed_int8_score32_exp_lut_div_generation_quality"].endswith(
                "decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality__"
                "l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1.json"
            )
            assert any(
                output.endswith(
                    "decoder_attention_score32_exp_lut_div_frontier_release_gate__"
                    "l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_"
                    "measured_command_control_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )
            assert any(
                output.endswith(
                    "decoder_attention_composed_datapath_physical_feasibility__"
                    "l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_"
                    "measured_command_control_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )


def test_generate_l2_campaign_task_adds_attention_composed_datapath_exp_lut_schedule_wrapper_recost() -> None:
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
                    item_id=(
                        "l2_decoder_attention_composed_datapath_score32_exp_lut_div_"
                        "schedule_wrapper_recost_llama7b_v1"
                    ),
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_composed_datapath_physical_feasibility",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert commands[0]["name"] == "estimate_decoder_attention_composed_datapath_physical_feasibility"
            assert "check_attention_score32_exp_lut_div_frontier_release" not in [c["name"] for c in commands]
            assert (
                "--model-name llm_decoder_attention_composed_datapath_score32_exp_lut_div_"
                "schedule_wrapper_recost_llama7b_v1"
                in run
            )
            assert "--recompute-area-fit-replicas" in run
            assert "--command-dispatch-control-metrics" not in run
            assert (
                "--composed-dual-stream-metrics "
                "runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/metrics.csv"
                in run
            )
            assert (
                "--composed-dual-stream-metrics "
                "runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/metrics.csv"
                in run
            )
            assert decoder_inputs["attention_kv_composed_dual_stream_metrics"] == (
                "runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2/metrics.csv,"
                "runs/designs/npu_blocks/attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c4/metrics.csv"
            )
            assert decoder_inputs["attention_mixed_int8_score32_exp_lut_div_generation_quality"].endswith(
                "decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality__"
                "l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1.json"
            )
            assert any(
                output.endswith(
                    "decoder_attention_composed_datapath_physical_feasibility__"
                    "l2_decoder_attention_composed_datapath_score32_exp_lut_div_"
                    "schedule_wrapper_recost_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )


def test_generate_l2_campaign_task_adds_attention_score32_exp_lut_measured_wrapper_promotion_evidence() -> None:
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
                    item_id="l2_decoder_attention_score32_exp_lut_measured_wrapper_promotion_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_score32_exp_lut_measured_wrapper_promotion",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "audit_decoder_attention_score32_exp_lut_measured_wrapper_promotion",
            ]
            assert "audit_llm_decoder_attention_score32_exp_lut_measured_wrapper_promotion.py" in run
            assert (
                "--measured-composed-datapath-json "
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_composed_datapath_physical_feasibility__"
                "l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_"
                "measured_command_control_llama7b_v1.json"
            ) in run
            assert (
                "--measured-dual-stream-wrapper-json "
                "control_plane/shadow_exports/l1_promotions/"
                "l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_b20_ppa_v1.json"
            ) in run
            assert (
                "--out runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_score32_exp_lut_measured_wrapper_promotion__"
                "l2_decoder_attention_score32_exp_lut_measured_wrapper_promotion_llama7b_v1.json"
            ) in run
            assert (
                "--out-md runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_score32_exp_lut_measured_wrapper_promotion__"
                "l2_decoder_attention_score32_exp_lut_measured_wrapper_promotion_llama7b_v1.md"
            ) in run
            assert decoder_inputs["attention_score32_exp_lut_measured_command_control"] == (
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_composed_datapath_physical_feasibility__"
                "l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_"
                "measured_command_control_llama7b_v1.json"
            )
            assert (
                decoder_inputs["attention_score32_exp_lut_dual_stream_wrapper_ppa"] ==
                "control_plane/shadow_exports/l1_promotions/"
                "l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_b20_ppa_v1.json"
            )
            assert (
                decoder_inputs["attention_score32_exp_lut_measured_wrapper_promotion_out"] ==
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_score32_exp_lut_measured_wrapper_promotion__"
                "l2_decoder_attention_score32_exp_lut_measured_wrapper_promotion_llama7b_v1.json"
            )
            assert (
                decoder_inputs["attention_score32_exp_lut_measured_wrapper_promotion_report"]
                == "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_score32_exp_lut_measured_wrapper_promotion__"
                "l2_decoder_attention_score32_exp_lut_measured_wrapper_promotion_llama7b_v1.md"
            )
            assert decoder_inputs["attention_score32_exp_lut_measured_wrapper_promotion_scope"].startswith(
                "Audit whether the reduced-replica score32 exp-LUT composed datapath schedule"
            )
            assert any(
                output.endswith(
                    "decoder_attention_score32_exp_lut_measured_wrapper_promotion__"
                    "l2_decoder_attention_score32_exp_lut_measured_wrapper_promotion_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )
            assert any(
                output.endswith(
                    "decoder_attention_score32_exp_lut_measured_wrapper_promotion__"
                    "l2_decoder_attention_score32_exp_lut_measured_wrapper_promotion_llama7b_v1.md"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )


def test_generate_l2_campaign_task_adds_attention_score32_exp_lut_service_closure_evidence() -> None:
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
                    item_id="l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_score32_exp_lut_service_closure",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "audit_decoder_attention_score32_exp_lut_service_closure",
            ]
            assert "audit_llm_decoder_attention_score32_exp_lut_service_closure.py" in run
            assert "--measured-command-control-json" in run
            assert "--wrapper-promotion-json" in run
            assert "--endpoint-router-sram-composition-json" in run
            assert "--measured-sram-rebalance-json" in run
            assert (
                "decoder_attention_score32_exp_lut_measured_wrapper_promotion__"
                "l2_decoder_attention_score32_exp_lut_measured_wrapper_promotion_llama7b_v1.json"
            ) in run
            assert (
                "decoder_attention_kv_endpoint_router_sram_composition__"
                "l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_r4.json"
            ) in run
            assert (
                decoder_inputs["attention_score32_exp_lut_service_closure_out"]
                == "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_score32_exp_lut_service_closure__"
                "l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1.json"
            )
            assert decoder_inputs["attention_score32_exp_lut_service_closure_scope"].startswith(
                "Audit the score32 exp-LUT measured-command-control row"
            )
            assert any(
                output.endswith(
                    "decoder_attention_score32_exp_lut_service_closure__"
                    "l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )


def test_generate_l2_campaign_task_adds_attention_score32_exp_lut_hbm_dram_service_closure_evidence() -> None:
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
                    item_id="l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_score32_exp_lut_hbm_dram_service_closure",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "audit_decoder_attention_score32_exp_lut_hbm_dram_service_closure",
            ]
            assert "audit_llm_decoder_attention_score32_exp_lut_hbm_dram_service_closure.py" in run
            assert "--score32-sram-envelope-json" in run
            assert "--score32-measured-command-control-json" in run
            assert "--hbm-command-calibrated-service-json" in run
            assert (
                "decoder_attention_score32_exp_lut_sram_hierarchy_envelope__"
                "l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1.json"
            ) in run
            assert (
                "decoder_attention_composed_datapath_physical_feasibility__"
                "l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_"
                "measured_command_control_llama7b_v1.json"
            ) in run
            assert (
                "decoder_attention_hbm_command_calibrated_service__"
                "l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1.json"
            ) in run
            assert (
                decoder_inputs["attention_score32_exp_lut_hbm_dram_service_closure_out"]
                == "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_score32_exp_lut_hbm_dram_service_closure__"
                "l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1.json"
            )
            assert (
                decoder_inputs["attention_score32_exp_lut_hbm_dram_service_closure_report"]
                == "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_score32_exp_lut_hbm_dram_service_closure__"
                "l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1.md"
            )
            assert (
                decoder_inputs["attention_score32_exp_lut_hbm_dram_service_closure_scope"].startswith(
                    "Close score32 exp-LUT HBM/DRAM service accounting"
                )
            )
            assert any(
                output.endswith(
                    "decoder_attention_score32_exp_lut_hbm_dram_service_closure__"
                    "l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )


def test_generate_l2_campaign_task_adds_attention_score32_integrated_frontier_ranking_evidence() -> None:
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
                    item_id="l2_decoder_attention_score32_integrated_frontier_ranking_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_score32_integrated_frontier_ranking",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "audit_decoder_attention_score32_integrated_frontier_ranking",
            ]
            assert "audit_llm_decoder_attention_score32_integrated_frontier_ranking.py" in run
            assert "--score32-hbm-dram-service-json" in run
            assert "--score32-measured-command-control-json" in run
            assert "--score32-quality-json" in run
            assert "--measured-compute-energy-json" in run
            assert "--mixed-int8-energy-json" in run
            assert "--integrated-energy-json" in run
            assert (
                "decoder_attention_score32_exp_lut_hbm_dram_service_closure__"
                "l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1.json"
            ) in run
            assert (
                "decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality__"
                "l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1.json"
            ) in run
            assert (
                decoder_inputs["attention_score32_integrated_frontier_ranking_out"]
                == "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_score32_integrated_frontier_ranking__"
                "l2_decoder_attention_score32_integrated_frontier_ranking_llama7b_v1.json"
            )
            assert (
                decoder_inputs["attention_score32_integrated_frontier_ranking_scope"].startswith(
                    "Rank the closed score32 exp-LUT Llama7B attention row"
                )
            )
            assert any(
                output.endswith(
                    "decoder_attention_score32_integrated_frontier_ranking__"
                    "l2_decoder_attention_score32_integrated_frontier_ranking_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )


def test_generate_l2_campaign_task_adds_attention_score32_compute_activity_energy_evidence() -> None:
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
                    item_id="l2_decoder_attention_score32_compute_activity_energy_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_score32_compute_activity_energy",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "audit_decoder_attention_score32_compute_activity_energy",
            ]
            assert "audit_llm_decoder_attention_score32_compute_activity_energy.py" in run
            assert "--score32-hbm-dram-service-json" in run
            assert "--score32-measured-command-control-json" in run
            assert "--score32-integrated-frontier-ranking-json" in run
            assert "--idle-power-fraction 0.0,0.05,0.1,0.25,1.0" in run
            assert (
                "decoder_attention_score32_integrated_frontier_ranking__"
                "l2_decoder_attention_score32_integrated_frontier_ranking_llama7b_v1.json"
            ) in run
            assert (
                decoder_inputs["attention_score32_compute_activity_energy_out"]
                == "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_score32_compute_activity_energy__"
                "l2_decoder_attention_score32_compute_activity_energy_llama7b_v1.json"
            )
            assert decoder_inputs["attention_score32_compute_activity_energy_scope"].startswith(
                "Replace the score32 wall-time compute-energy ambiguity"
            )
            assert any(
                output.endswith(
                    "decoder_attention_score32_compute_activity_energy__"
                    "l2_decoder_attention_score32_compute_activity_energy_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )


def test_generate_l2_campaign_task_adds_attention_score32_exp_lut_sram_hierarchy_envelope_evidence() -> None:
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
                    item_id="l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_score32_exp_lut_sram_hierarchy_envelope",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "audit_decoder_attention_score32_exp_lut_sram_hierarchy_envelope",
            ]
            assert "audit_llm_decoder_attention_score32_exp_lut_sram_hierarchy_envelope.py" in run
            assert "--service-closure-json" in run
            assert "--measured-sram-rebalance-json" in run
            assert "--local-sram-capacity-json" in run
            assert "--endpoint-router-sram-composition-json" in run
            assert "--placement-efficiency 1.0,0.85,0.75,0.65,0.55" in run
            assert (
                "decoder_attention_score32_exp_lut_service_closure__"
                "l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1.json"
            ) in run
            assert (
                decoder_inputs["attention_score32_exp_lut_sram_hierarchy_envelope_out"]
                == "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_score32_exp_lut_sram_hierarchy_envelope__"
                "l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1.json"
            )
            assert decoder_inputs["attention_score32_exp_lut_sram_hierarchy_envelope_scope"].startswith(
                "Replace the prior score32 exp-LUT SRAM packing abstraction"
            )
            assert any(
                output.endswith(
                    "decoder_attention_score32_exp_lut_sram_hierarchy_envelope__"
                    "l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )


def test_generate_l2_campaign_task_adds_attention_composed_datapath_score24_reduced_replica_evidence() -> None:
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
                    item_id="l2_decoder_attention_composed_datapath_score24_w16_exact_div_reduced_replica_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_composed_datapath_physical_feasibility",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert "estimate_decoder_attention_composed_datapath_physical_feasibility" in [c["name"] for c in commands]
            assert (
                "--model-name llm_decoder_attention_composed_datapath_score24_w16_exact_div_reduced_replica_llama7b_v1"
                in run
            )
            assert "--recompute-area-fit-replicas" in run
            assert "--precision-profile q8_k8_v8_a24_s24_w16_exact_div_int8_compute" in run
            assert decoder_inputs["attention_kv_composed_dual_stream_metrics"] == (
                "runs/designs/npu_blocks/"
                "attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/metrics.csv"
            )
            assert (
                "--composed-dual-stream-metrics runs/designs/npu_blocks/"
                "attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/metrics.csv "
                in run
            )
            assert any(
                output.endswith(
                    "decoder_attention_composed_datapath_physical_feasibility__"
                    "l2_decoder_attention_composed_datapath_score24_w16_exact_div_reduced_replica_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )


def test_generate_l2_campaign_task_adds_attention_composed_datapath_score32_recip_lut_q16_reduced_replica_evidence() -> None:
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
                    item_id="l2_decoder_attention_composed_datapath_score32_w16_recip_lut_q16_reduced_replica_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_composed_datapath_physical_feasibility",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert "estimate_decoder_attention_composed_datapath_physical_feasibility" in [c["name"] for c in commands]
            assert (
                "--model-name llm_decoder_attention_composed_datapath_score32_w16_recip_lut_q16_reduced_replica_llama7b_v1"
                in run
            )
            assert "--recompute-area-fit-replicas" in run
            assert (
                "--precision-profile q8_k8_v8_a32_s32_w16_recip_lut_q16_int8_compute" in run
            )
            assert decoder_inputs["attention_kv_composed_dual_stream_metrics"] == (
                "runs/designs/npu_blocks/"
                "attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/metrics.csv"
            )
            assert (
                "--composed-dual-stream-metrics runs/designs/npu_blocks/"
                "attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_recip_lut_q16/metrics.csv "
                in run
            )
            assert any(
                output.endswith(
                    "decoder_attention_composed_datapath_physical_feasibility__"
                    "l2_decoder_attention_composed_datapath_score32_w16_recip_lut_q16_reduced_replica_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )


def test_generate_l2_campaign_task_adds_attention_composed_datapath_score32_exp_lut_div_reduced_replica_evidence() -> None:
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
                    item_id="l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_composed_datapath_physical_feasibility",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            gate_run = commands[0]["run"]
            run = commands[1]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert commands[0]["name"] == "check_attention_score32_exp_lut_div_frontier_release"
            assert "estimate_decoder_attention_composed_datapath_physical_feasibility" in [c["name"] for c in commands]
            assert "npu/eval/check_attention_exp_lut_frontier_release.py" in gate_run
            assert "--quality-json runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/" in gate_run
            assert "--metrics-csv runs/designs/npu_blocks/" in gate_run
            assert "--config-json runs/designs/npu_blocks/" in gate_run
            assert decoder_inputs["attention_score32_exp_lut_div_frontier_release_gate"].endswith(
                "decoder_attention_score32_exp_lut_div_frontier_release_gate__"
                "l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_llama7b_v1.json"
            )
            assert decoder_inputs["attention_score32_exp_lut_div_composed_config"] == (
                "runs/designs/npu_blocks/"
                "attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/"
                "config.json"
            )
            assert (
                "--model-name llm_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_llama7b_v1"
                in run
            )
            assert "--recompute-area-fit-replicas" in run
            assert "--precision-profile q8_k8_v8_a32_s32_w16_exp_lut_div_b20_int8_compute" in run
            assert decoder_inputs["attention_kv_composed_dual_stream_metrics"] == (
                "runs/designs/npu_blocks/"
                "attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/"
                "metrics.csv"
            )
            assert decoder_inputs["attention_mixed_int8_score32_exp_lut_div_generation_quality"].endswith(
                "decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality__"
                "l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1.json"
            )
            assert (
                "--quality-gate-json runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality__"
                "l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1.json "
                in run
            )
            assert (
                "--composed-dual-stream-metrics runs/designs/npu_blocks/"
                "attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/"
                "metrics.csv "
                in run
            )
            assert any(
                output.endswith(
                    "decoder_attention_score32_exp_lut_div_frontier_release_gate__"
                    "l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )
            assert any(
                output.endswith(
                    "decoder_attention_composed_datapath_physical_feasibility__"
                    "l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )


def test_generate_l2_campaign_task_adds_attention_composed_datapath_score32_exp_lut_div_parallelism_recost_evidence() -> None:
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
                    item_id="l2_decoder_attention_composed_datapath_score32_exp_lut_div_parallelism_recost_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_composed_datapath_physical_feasibility",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            estimate_commands = [
                command for command in commands
                if command["name"] == "estimate_decoder_attention_composed_datapath_physical_feasibility"
            ]
            run = estimate_commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert len(estimate_commands) == 1
            assert (
                "--model-name llm_decoder_attention_composed_datapath_score32_exp_lut_div_parallelism_recost_llama7b_v1"
                in run
            )
            assert "--recompute-area-fit-replicas" in run
            assert "--precision-profile q8_k8_v8_a32_s32_w16_exp_lut_div_b20_int8_compute" in run
            assert decoder_inputs["attention_mixed_int8_score32_exp_lut_div_generation_quality"].endswith(
                "decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality__"
                "l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1.json"
            )
            assert "attention_score32_exp_lut_div_frontier_release_gate" not in decoder_inputs
            assert decoder_inputs["attention_kv_composed_dual_stream_metrics"].count("metrics.csv") == 4
            for design_name in (
                "attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20",
                "attention_dual_stream_composed_int8_q8k8v8_8x8_p8_ppc1_nohash_score32_w16_exp_lut_div_b20",
                "attention_dual_stream_composed_int8_q8k8v8_8x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20",
                "attention_dual_stream_composed_int8_q8k8v8_4x4_p8_ppc1_nohash_score32_w16_exp_lut_div_b20",
            ):
                expected = f"runs/designs/npu_blocks/{design_name}/metrics.csv"
                assert expected in decoder_inputs["attention_kv_composed_dual_stream_metrics"]
                assert f"--composed-dual-stream-metrics {expected}" in run
            assert any(
                output.endswith(
                    "decoder_attention_composed_datapath_physical_feasibility__"
                    "l2_decoder_attention_composed_datapath_score32_exp_lut_div_parallelism_recost_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )


def test_generate_l2_campaign_task_adds_attention_composed_datapath_score32_split2_reduced_replica_evidence() -> None:
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
                    item_id="l2_decoder_attention_composed_datapath_score32_w16_exact_div_split2_reduced_replica_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_composed_datapath_physical_feasibility",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert "estimate_decoder_attention_composed_datapath_physical_feasibility" in [c["name"] for c in commands]
            assert (
                "--model-name llm_decoder_attention_composed_datapath_score32_w16_exact_div_split2_reduced_replica_llama7b_v1"
                in run
            )
            assert "--recompute-area-fit-replicas" in run
            assert "--precision-profile q8_k8_v8_a32_s32_w16_exact_div_int8_compute" in run
            assert decoder_inputs["attention_kv_composed_dual_stream_metrics"] == (
                "runs/designs/npu_blocks/"
                "attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/metrics.csv"
            )
            assert (
                "--composed-dual-stream-metrics runs/designs/npu_blocks/"
                "attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/metrics.csv "
                in run
            )
            assert any(
                output.endswith(
                    "decoder_attention_composed_datapath_physical_feasibility__"
                    "l2_decoder_attention_composed_datapath_score32_w16_exact_div_split2_reduced_replica_llama7b_v1.json"
                )
                for output in work_item.task_request.request_payload["task"]["expected_outputs"]
            )


def test_generate_l2_campaign_task_adds_attention_integrated_abstraction_closure_evidence() -> None:
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
                    item_id="l2_decoder_attention_integrated_abstraction_closure_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_integrated_abstraction_closure_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_integrated_abstraction_closure_llama7b_v1/proposal.json"
                    ),
                    abstraction_layer="decoder_attention_integrated_abstraction_closure",
                    evaluation_mode="frontier_detail",
                    comparison_role="frontier_closure",
                    depends_on_item_ids=[
                        "l2_decoder_attention_composed_datapath_q12_pwl_softmax_frontier_llama7b_v1",
                        "l2_decoder_attention_kv_physical_hbm_quality_backed_7b_llama7b_v1_r2",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "audit_decoder_attention_integrated_abstraction_closure",
            ]
            assert "audit_llm_decoder_attention_integrated_abstraction_closure.py" in run
            assert (
                "--composed-datapath-json "
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_composed_datapath_physical_feasibility__"
                "l2_decoder_attention_composed_datapath_q12_pwl_softmax_frontier_llama7b_v1.json"
            ) in run
            assert (
                "--hbm-quality-backed-json "
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_physical_hbm_quality_backed_7b__"
                "l2_decoder_attention_kv_physical_hbm_quality_backed_7b_llama7b_v1_r2.json"
            ) in run
            assert decoder_inputs["attention_integrated_abstraction_closure_out"].endswith(
                "decoder_attention_integrated_abstraction_closure__"
                "l2_decoder_attention_integrated_abstraction_closure_llama7b_v1.json"
            )
            assert decoder_inputs["attention_integrated_abstraction_closure_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_integrated_abstraction_closure",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": [
                    "l2_decoder_attention_composed_datapath_q12_pwl_softmax_frontier_llama7b_v1",
                    "l2_decoder_attention_kv_physical_hbm_quality_backed_7b_llama7b_v1_r2",
                ],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_attention_integrated_energy_closure_evidence() -> None:
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
                    item_id="l2_decoder_attention_integrated_energy_closure_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_integrated_energy_closure_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_integrated_energy_closure_llama7b_v1/proposal.json"
                    ),
                    abstraction_layer="decoder_attention_integrated_energy_closure",
                    evaluation_mode="frontier_detail",
                    comparison_role="frontier_closure",
                    depends_on_item_ids=[
                        "l2_decoder_attention_integrated_abstraction_closure_llama7b_v1",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "audit_decoder_attention_integrated_energy_closure",
            ]
            assert "audit_llm_decoder_attention_integrated_energy_closure.py" in run
            assert (
                "--integrated-closure-json "
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_integrated_abstraction_closure__"
                "l2_decoder_attention_integrated_abstraction_closure_llama7b_v1.json"
            ) in run
            assert "--hbm-energy-pj-per-byte 8.0" in run
            assert decoder_inputs["attention_integrated_energy_closure_out"].endswith(
                "decoder_attention_integrated_energy_closure__"
                "l2_decoder_attention_integrated_energy_closure_llama7b_v1.json"
            )
            assert decoder_inputs["attention_integrated_energy_closure_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_integrated_energy_closure",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": [
                    "l2_decoder_attention_integrated_abstraction_closure_llama7b_v1",
                ],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_attention_hbm_energy_sensitivity_evidence() -> None:
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
                    item_id="l2_decoder_attention_hbm_energy_sensitivity_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_hbm_energy_sensitivity_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_hbm_energy_sensitivity_llama7b_v1/proposal.json"
                    ),
                    abstraction_layer="decoder_attention_hbm_energy_sensitivity",
                    evaluation_mode="frontier_detail",
                    comparison_role="frontier_closure",
                    depends_on_item_ids=[
                        "l2_decoder_attention_integrated_energy_closure_llama7b_v1_r2",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "audit_decoder_attention_hbm_energy_sensitivity",
            ]
            assert "audit_llm_decoder_attention_hbm_energy_sensitivity.py" in run
            assert (
                "--integrated-energy-json "
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_integrated_energy_closure__"
                "l2_decoder_attention_integrated_energy_closure_llama7b_v1_r2.json"
            ) in run
            assert "--hbm-energy-pj-per-byte-list 1,2,4,8,16,32" in run
            assert decoder_inputs["attention_hbm_energy_sensitivity_out"].endswith(
                "decoder_attention_hbm_energy_sensitivity__"
                "l2_decoder_attention_hbm_energy_sensitivity_llama7b_v1.json"
            )
            assert decoder_inputs["attention_hbm_energy_sensitivity_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_hbm_energy_sensitivity",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": [
                    "l2_decoder_attention_integrated_energy_closure_llama7b_v1_r2",
                ],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_attention_hbm_dram_service_energy_evidence() -> None:
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
                    item_id="l2_decoder_attention_hbm_dram_service_energy_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_hbm_dram_service_energy_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_hbm_dram_service_energy_llama7b_v1/proposal.json"
                    ),
                    abstraction_layer="decoder_attention_hbm_dram_service_energy",
                    evaluation_mode="frontier_detail",
                    comparison_role="frontier_closure",
                    depends_on_item_ids=[
                        "l2_decoder_attention_hbm_energy_sensitivity_llama7b_v1",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "audit_decoder_attention_hbm_dram_service_energy",
            ]
            assert "audit_llm_decoder_attention_hbm_dram_service_energy.py" in run
            assert (
                "--hbm-energy-sensitivity-json "
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_hbm_energy_sensitivity__"
                "l2_decoder_attention_hbm_energy_sensitivity_llama7b_v1.json"
            ) in run
            assert (
                "--hbm-controller-json "
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_hbm_controller__"
                "l2_decoder_attention_kv_hbm_controller_llama7b_v1_r3.json"
            ) in run
            assert decoder_inputs["attention_hbm_dram_service_energy_out"].endswith(
                "decoder_attention_hbm_dram_service_energy__"
                "l2_decoder_attention_hbm_dram_service_energy_llama7b_v1.json"
            )
            assert decoder_inputs["attention_hbm_dram_service_energy_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_hbm_dram_service_energy",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": [
                    "l2_decoder_attention_hbm_energy_sensitivity_llama7b_v1",
                ],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_attention_hbm_energy_calibration_evidence() -> None:
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
                    item_id="l2_decoder_attention_hbm_energy_calibration_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_hbm_energy_calibration_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_hbm_energy_calibration_llama7b_v1/proposal.json"
                    ),
                    abstraction_layer="decoder_attention_hbm_energy_calibration",
                    evaluation_mode="frontier_detail",
                    comparison_role="frontier_closure",
                    depends_on_item_ids=[
                        "l2_decoder_attention_hbm_dram_service_energy_llama7b_v1",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "audit_decoder_attention_hbm_energy_calibration",
            ]
            assert "audit_llm_decoder_attention_hbm_energy_calibration.py" in run
            assert (
                "--hbm-dram-service-energy-json "
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_hbm_dram_service_energy__"
                "l2_decoder_attention_hbm_dram_service_energy_llama7b_v1.json"
            ) in run
            assert "--external-measurements runs/design_registry/external_measurements.jsonl" in run
            assert "--comparison-claims runs/design_registry/comparison_claims.jsonl" in run
            assert decoder_inputs["attention_hbm_energy_calibration_out"].endswith(
                "decoder_attention_hbm_energy_calibration__"
                "l2_decoder_attention_hbm_energy_calibration_llama7b_v1.json"
            )
            assert decoder_inputs["attention_hbm_energy_calibration_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_hbm_energy_calibration",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": [
                    "l2_decoder_attention_hbm_dram_service_energy_llama7b_v1",
                ],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_attention_hbm_command_calibrated_service_evidence() -> None:
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
                    item_id="l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1/proposal.json"
                    ),
                    abstraction_layer="decoder_attention_hbm_command_calibrated_service",
                    evaluation_mode="frontier_detail",
                    comparison_role="frontier_closure",
                    depends_on_item_ids=[
                        "l2_decoder_attention_hbm_energy_calibration_llama7b_v1",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "audit_decoder_attention_hbm_command_calibrated_service",
            ]
            assert "audit_llm_decoder_attention_hbm_command_calibrated_service.py" in run
            assert (
                "--hbm-dram-service-energy-json "
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_hbm_dram_service_energy__"
                "l2_decoder_attention_hbm_dram_service_energy_llama7b_v1.json"
            ) in run
            assert (
                "--hbm-energy-calibration-json "
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_hbm_energy_calibration__"
                "l2_decoder_attention_hbm_energy_calibration_llama7b_v1.json"
            ) in run
            assert decoder_inputs["attention_hbm_command_calibrated_service_out"].endswith(
                "decoder_attention_hbm_command_calibrated_service__"
                "l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1.json"
            )
            assert decoder_inputs["attention_hbm_command_calibrated_service_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_hbm_command_calibrated_service",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": [
                    "l2_decoder_attention_hbm_energy_calibration_llama7b_v1",
                ],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_attention_measured_compute_energy_closure_evidence() -> None:
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
                    item_id="l2_decoder_attention_measured_compute_energy_closure_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_measured_compute_energy_closure_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_measured_compute_energy_closure_llama7b_v1/proposal.json"
                    ),
                    abstraction_layer="decoder_attention_measured_compute_energy_closure",
                    evaluation_mode="frontier_detail",
                    comparison_role="frontier_closure",
                    depends_on_item_ids=[
                        "l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            run = commands[0]["run"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "audit_decoder_attention_measured_compute_energy_closure",
            ]
            assert "audit_llm_decoder_attention_measured_compute_energy_closure.py" in run
            assert (
                "--hbm-command-calibrated-service-json "
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_hbm_command_calibrated_service__"
                "l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1.json"
            ) in run
            assert (
                "--measured-compute-json "
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_dense_tile_measured_compute__"
                "l2_decoder_attention_kv_dense_tile_measured_compute_llama7b_v1.json"
            ) in run
            assert decoder_inputs["attention_measured_compute_energy_closure_out"].endswith(
                "decoder_attention_measured_compute_energy_closure__"
                "l2_decoder_attention_measured_compute_energy_closure_llama7b_v1.json"
            )
            assert decoder_inputs["attention_measured_compute_energy_closure_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_measured_compute_energy_closure",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": [
                    "l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1",
                ],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_dense_gemm_v3_measured_compute_closure_evidence() -> None:
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
                    item_id="l2_decoder_attention_dense_gemm_v3_measured_compute_closure_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_dense_gemm_v3_measured_compute_closure_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_dense_gemm_v3_measured_compute_closure_llama7b_v1/"
                        "proposal.json"
                    ),
                    abstraction_layer="decoder_attention_dense_gemm_v3_measured_compute_closure",
                    evaluation_mode="frontier_detail",
                    comparison_role="frontier_closure",
                    depends_on_item_ids=[
                        "l1_npu_dense_gemm_tile_scaling_v3",
                        "l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1",
                        "l2_decoder_attention_measured_compute_energy_closure_llama7b_v1",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:2]] == [
                "estimate_decoder_attention_kv_dense_tile_v3_measured_compute",
                "audit_decoder_attention_dense_gemm_v3_measured_compute_closure",
            ]
            assert "--tag-substring npu_dense_gemm_tile_v3_depth_hier" in commands[0]["run"]
            assert "audit_llm_decoder_attention_measured_compute_energy_closure.py" in commands[1]["run"]
            assert (
                "--measured-compute-json "
                "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
                "decoder_attention_kv_dense_tile_v3_measured_compute__"
                "l2_decoder_attention_dense_gemm_v3_measured_compute_closure_llama7b_v1.json"
            ) in commands[1]["run"]
            assert decoder_inputs["attention_kv_dense_tile_v3_measured_compute_out"] in work_item.expected_outputs
            assert (
                decoder_inputs["attention_dense_gemm_v3_measured_compute_closure_out"]
                in work_item.expected_outputs
            )
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_dense_gemm_v3_measured_compute_closure",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": [
                    "l1_npu_dense_gemm_tile_scaling_v3",
                    "l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1",
                    "l2_decoder_attention_measured_compute_energy_closure_llama7b_v1",
                ],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_mixed_int8_energy_closure_evidence() -> None:
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
                    item_id="l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1/"
                        "proposal.json"
                    ),
                    abstraction_layer="decoder_attention_mixed_int8_energy_closure",
                    evaluation_mode="frontier_detail",
                    comparison_role="frontier_closure",
                    depends_on_item_ids=[
                        "l2_decoder_attention_mixed_precision_int8_compute_physical_feasibility_softmax_recip_lut_llama7b_v1",
                        "l2_decoder_attention_dense_gemm_v3_measured_compute_closure_llama7b_v1",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "audit_decoder_attention_mixed_int8_energy_closure",
            ]
            run = commands[0]["run"]
            assert "audit_llm_decoder_attention_mixed_precision_int8_compute_energy_closure.py" in run
            assert "--mixed-precision-int8-compute-physical-feasibility-json" in run
            assert "--baseline-closure-json" in run
            assert "attention_mixed_precision_int8_compute_physical_feasibility" in decoder_inputs
            assert "attention_mixed_int8_energy_closure_out" in decoder_inputs
            assert decoder_inputs["attention_mixed_int8_energy_closure_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_mixed_int8_energy_closure",
            }


def test_generate_l2_campaign_task_adds_mixed_int8_native_quality_evidence() -> None:
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
                    item_id="l2_decoder_attention_mixed_int8_native_quality_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_mixed_int8_native_quality_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_mixed_int8_native_quality_llama7b_v1/"
                        "proposal.json"
                    ),
                    abstraction_layer="decoder_attention_mixed_int8_native_quality",
                    evaluation_mode="frontier_detail",
                    comparison_role="precision_gate",
                    depends_on_item_ids=[
                        "l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1_r2",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "evaluate_decoder_attention_mixed_int8_native_quality",
            ]
            run = commands[0]["run"]
            assert "evaluate_llm_decoder_model_native_mixed_int8_attention.py" in run
            assert "RTLGEN_MODEL_NATIVE_7B_MODEL_ID" in run
            assert "--softmax-mode rtl_recip_lut_q8" in run
            assert "--q-bits 8 --k-bits 8 --v-bits 8" in run
            assert decoder_inputs["attention_mixed_int8_energy_closure"].endswith(
                "decoder_attention_mixed_int8_energy_closure__"
                "l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1_r2.json"
            )
            assert "attention_mixed_int8_native_quality_out" in decoder_inputs
            assert decoder_inputs["attention_mixed_int8_native_quality_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_mixed_int8_native_quality",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": ["l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1_r2"],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_mixed_int8_native_quality_ablation_evidence() -> None:
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
                    item_id="l2_decoder_attention_mixed_int8_native_quality_ablation_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_mixed_int8_native_quality_ablation_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_mixed_int8_native_quality_ablation_llama7b_v1/"
                        "proposal.json"
                    ),
                    abstraction_layer="decoder_attention_mixed_int8_native_quality_ablation",
                    evaluation_mode="frontier_detail",
                    comparison_role="precision_failure_diagnosis",
                    depends_on_item_ids=[
                        "l2_decoder_attention_mixed_int8_native_quality_llama7b_v1",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "evaluate_decoder_attention_mixed_int8_native_quality_ablation",
            ]
            run = commands[0]["run"]
            assert "evaluate_llm_decoder_model_native_mixed_int8_attention.py" in run
            assert "--candidate qkv8_float_softmax:q8,k8,v8,s24,w16,float_quantized" in run
            assert "--candidate qkv8_score8_rtl_recip_q8:q8,k8,v8,s8,w8,rtl_recip_lut_q8" in run
            assert "--primary-candidate-id qkv8_score8_rtl_recip_q8" in run
            assert decoder_inputs["attention_mixed_int8_native_quality"].endswith(
                "decoder_attention_mixed_int8_native_quality__"
                "l2_decoder_attention_mixed_int8_native_quality_llama7b_v1.json"
            )
            assert "attention_mixed_int8_native_quality_ablation_out" in decoder_inputs
            assert decoder_inputs["attention_mixed_int8_native_quality_ablation_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_mixed_int8_native_quality_ablation",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": ["l2_decoder_attention_mixed_int8_native_quality_llama7b_v1"],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_mixed_int8_score_boundary_evidence() -> None:
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
                    item_id="l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1/"
                        "proposal.json"
                    ),
                    abstraction_layer="decoder_attention_mixed_int8_score_boundary",
                    evaluation_mode="frontier_detail",
                    comparison_role="precision_boundary",
                    depends_on_item_ids=[
                        "l2_decoder_attention_mixed_int8_native_quality_ablation_llama7b_v1",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "evaluate_decoder_attention_mixed_int8_score_boundary",
            ]
            run = commands[0]["run"]
            assert "--candidate score10_float:q8,k8,v8,s10,w16,float_quantized" in run
            assert "--candidate score16_rtl_exact:q8,k8,v8,s16,w8,rtl_exact" in run
            assert "--primary-candidate-id score12_rtl_exact" in run
            assert decoder_inputs["attention_mixed_int8_native_quality_ablation"].endswith(
                "decoder_attention_mixed_int8_native_quality_ablation__"
                "l2_decoder_attention_mixed_int8_native_quality_ablation_llama7b_v1.json"
            )
            assert "attention_mixed_int8_score_boundary_out" in decoder_inputs
            assert decoder_inputs["attention_mixed_int8_score_boundary_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_mixed_int8_score_boundary",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": ["l2_decoder_attention_mixed_int8_native_quality_ablation_llama7b_v1"],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_mixed_int8_high_score_boundary_evidence() -> None:
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
                    item_id="l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1/"
                        "proposal.json"
                    ),
                    abstraction_layer="decoder_attention_mixed_int8_high_score_boundary",
                    evaluation_mode="frontier_detail",
                    comparison_role="precision_boundary",
                    depends_on_item_ids=[
                        "l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "evaluate_decoder_attention_mixed_int8_high_score_boundary",
            ]
            run = commands[0]["run"]
            assert "evaluate_llm_decoder_model_native_mixed_int8_attention.py" in run
            assert "--candidate score18_float:q8,k8,v8,s18,w16,float_quantized" in run
            assert "--candidate score24_rtl_exact:q8,k8,v8,s24,w8,rtl_exact" in run
            assert "--candidate qkv8_float_exact:q8,k8,v8,s24,w16,float_exact" in run
            assert "--primary-candidate-id score24_float" in run
            assert decoder_inputs["attention_mixed_int8_score_boundary"].endswith(
                "decoder_attention_mixed_int8_score_boundary__"
                "l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1.json"
            )
            assert "attention_mixed_int8_high_score_boundary_out" in decoder_inputs
            assert (
                decoder_inputs["attention_mixed_int8_high_score_boundary_out"]
                in work_item.expected_outputs
            )
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_mixed_int8_high_score_boundary",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": ["l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1"],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_mixed_int8_broad_native_quality_evidence() -> None:
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
                    item_id="l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1/"
                        "proposal.json"
                    ),
                    abstraction_layer="decoder_attention_mixed_int8_broad_native_quality",
                    evaluation_mode="quality_gate",
                    comparison_role="precision_validation",
                    depends_on_item_ids=[
                        "l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "evaluate_decoder_attention_mixed_int8_broad_native_quality",
            ]
            run = commands[0]["run"]
            assert "evaluate_llm_decoder_model_native_mixed_int8_attention.py" in run
            assert "RTLGEN_MODEL_NATIVE_7B_BROAD_MAX_PROMPTS" in run
            assert "RTLGEN_MODEL_NATIVE_7B_BROAD_GENERATION_STEPS" in run
            assert "--generation-steps \"$GEN_STEPS\"" in run
            assert "--candidate score22_float:q8,k8,v8,s22,w16,float_quantized" in run
            assert "--candidate score24_float:q8,k8,v8,s24,w16,float_quantized" in run
            assert "--candidate score24_rtl_exact:q8,k8,v8,s24,w8,rtl_exact" in run
            assert "--candidate qkv8_float_exact:q8,k8,v8,s24,w16,float_exact" in run
            assert "--primary-candidate-id score24_float" in run
            assert decoder_inputs["attention_mixed_int8_high_score_boundary"].endswith(
                "decoder_attention_mixed_int8_high_score_boundary__"
                "l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1.json"
            )
            assert "attention_mixed_int8_broad_native_quality_out" in decoder_inputs
            assert (
                decoder_inputs["attention_mixed_int8_broad_native_quality_out"]
                in work_item.expected_outputs
            )
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_mixed_int8_broad_native_quality",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": ["l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1"],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_mixed_int8_q12_pwl_native_quality_evidence() -> None:
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
                    item_id="l2_decoder_attention_mixed_int8_q12_pwl_native_quality_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_mixed_int8_q12_pwl_native_quality_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_mixed_int8_q12_pwl_native_quality_llama7b_v1/"
                        "proposal.json"
                    ),
                    abstraction_layer="decoder_attention_mixed_int8_q12_pwl_native_quality",
                    evaluation_mode="quality_gate",
                    comparison_role="precision_validation",
                    depends_on_item_ids=[
                        "l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "evaluate_decoder_attention_mixed_int8_q12_pwl_native_quality",
            ]
            run = commands[0]["run"]
            assert "evaluate_llm_decoder_model_native_mixed_int8_attention.py" in run
            assert "pwl_recip_lut_q12_bucket8" in run
            assert "--candidate qkv8_float_exact:q8,k8,v8,s24,w16,float_exact" in run
            assert "--candidate qkv8_score24_float:q8,k8,v8,s24,w16,float_quantized" in run
            assert "--candidate qkv8_score24_rtl_exact:q8,k8,v8,s24,w8,rtl_exact" in run
            assert (
                "--candidate qkv8_q12_pwl_recip_q12_bucket8:q8,k8,v8,s12,w12,pwl_recip_lut_q12_bucket8"
                in run
            )
            assert "--primary-candidate-id qkv8_q12_pwl_recip_q12_bucket8" in run
            assert decoder_inputs["attention_mixed_int8_quality_backed_frontier"].endswith(
                "decoder_attention_mixed_int8_quality_backed_frontier__"
                "l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1.json"
            )
            assert "attention_mixed_int8_q12_pwl_native_quality_out" in decoder_inputs
            assert (
                decoder_inputs["attention_mixed_int8_q12_pwl_native_quality_out"]
                in work_item.expected_outputs
            )
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_mixed_int8_q12_pwl_native_quality",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": ["l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1"],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_mixed_int8_q24_pwl_native_quality_evidence() -> None:
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
                    item_id="l2_decoder_attention_mixed_int8_q24_pwl_native_quality_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_mixed_int8_q24_pwl_native_quality_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_mixed_int8_q24_pwl_native_quality_llama7b_v1/"
                        "proposal.json"
                    ),
                    abstraction_layer="decoder_attention_mixed_int8_q24_pwl_native_quality",
                    evaluation_mode="quality_gate",
                    comparison_role="precision_validation",
                    depends_on_item_ids=[
                        "l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "evaluate_decoder_attention_mixed_int8_q24_pwl_native_quality",
            ]
            run = commands[0]["run"]
            assert "evaluate_llm_decoder_model_native_mixed_int8_attention.py" in run
            assert "--candidate qkv8_float_exact:q8,k8,v8,s24,w16,float_exact" in run
            assert "--candidate qkv8_score24_float:q8,k8,v8,s24,w16,float_quantized" in run
            assert (
                "--candidate qkv8_q20_pwl_recip_q20_bucket8:q8,k8,v8,s20,w20,pwl_recip_lut_q20_bucket8"
                in run
            )
            assert (
                "--candidate qkv8_q24_pwl_recip_q24_bucket8:q8,k8,v8,s24,w24,pwl_recip_lut_q24_bucket8"
                in run
            )
            assert "--primary-candidate-id qkv8_q24_pwl_recip_q24_bucket8" in run
            assert decoder_inputs["attention_mixed_int8_softmax_replacement_generation_quality"].endswith(
                "decoder_attention_mixed_int8_softmax_replacement_generation_quality__"
                "l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1.json"
            )
            assert "attention_mixed_int8_q24_pwl_native_quality_out" in decoder_inputs
            assert (
                decoder_inputs["attention_mixed_int8_q24_pwl_native_quality_out"]
                in work_item.expected_outputs
            )
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_mixed_int8_q24_pwl_native_quality",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": [
                    "l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1",
                ],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_mixed_int8_q12_pwl_proxy_audit_evidence() -> None:
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
                    item_id="l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1/"
                        "proposal.json"
                    ),
                    abstraction_layer="decoder_attention_mixed_int8_q12_pwl_proxy_audit",
                    evaluation_mode="frontier_detail",
                    comparison_role="quality_backed_proxy",
                    depends_on_item_ids=[
                        "l2_decoder_attention_mixed_int8_q12_pwl_native_quality_llama7b_v1",
                        "l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "audit_decoder_attention_mixed_int8_q12_pwl_proxy",
            ]
            run = commands[0]["run"]
            assert "audit_llm_decoder_attention_mixed_int8_q12_pwl_proxy.py" in run
            assert "--q12-pwl-native-quality-json" in run
            assert "--quality-backed-frontier-json" in run
            assert "--composed-q12-pwl-metrics" in run
            assert "--full-value-v8-metrics" in run
            assert decoder_inputs["attention_mixed_int8_q12_pwl_native_quality"].endswith(
                "decoder_attention_mixed_int8_q12_pwl_native_quality__"
                "l2_decoder_attention_mixed_int8_q12_pwl_native_quality_llama7b_v1.json"
            )
            assert decoder_inputs["attention_mixed_int8_quality_backed_frontier"].endswith(
                "decoder_attention_mixed_int8_quality_backed_frontier__"
                "l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1.json"
            )
            assert decoder_inputs["attention_mixed_int8_q12_pwl_composed_metrics"].endswith(
                "attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_q12_pwl_recip_q12/"
                "metrics.csv"
            )
            assert "attention_mixed_int8_q12_pwl_proxy_audit_out" in decoder_inputs
            assert (
                decoder_inputs["attention_mixed_int8_q12_pwl_proxy_audit_out"]
                in work_item.expected_outputs
            )
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_mixed_int8_q12_pwl_proxy_audit",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": [
                    "l2_decoder_attention_mixed_int8_q12_pwl_native_quality_llama7b_v1",
                    "l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1",
                ],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_mixed_int8_score_precision_recovery_evidence() -> None:
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
                    item_id="l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1/"
                        "proposal.json"
                    ),
                    abstraction_layer="decoder_attention_mixed_int8_score_precision_recovery",
                    evaluation_mode="quality_gate",
                    comparison_role="precision_recovery",
                    depends_on_item_ids=[
                        "l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1",
                        "l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "evaluate_decoder_attention_mixed_int8_score_precision_recovery",
            ]
            run = commands[0]["run"]
            assert "evaluate_llm_decoder_model_native_mixed_int8_attention.py" in run
            assert "RTLGEN_MODEL_NATIVE_7B_BROAD_MAX_PROMPTS" in run
            assert "RTLGEN_MODEL_NATIVE_7B_BROAD_GENERATION_STEPS" in run
            assert "--generation-steps \"$GEN_STEPS\"" in run
            assert "--candidate qkv8_float_exact:q8,k8,v8,s24,w16,float_exact" in run
            assert "--candidate score24_float:q8,k8,v8,s24,w16,float_quantized" in run
            assert "--candidate score28_float:q8,k8,v8,s28,w16,float_quantized" in run
            assert "--candidate score32_float:q8,k8,v8,s32,w16,float_quantized" in run
            assert (
                "--candidate qkv8_q16_pwl_recip_q16_bucket8:q8,k8,v8,s16,w16,pwl_recip_lut_q16_bucket8"
                in run
            )
            assert (
                "--candidate qkv8_q20_pwl_recip_q20_bucket8:q8,k8,v8,s20,w20,pwl_recip_lut_q20_bucket8"
                in run
            )
            assert (
                "--candidate qkv8_q24_pwl_recip_q24_bucket8:q8,k8,v8,s24,w24,pwl_recip_lut_q24_bucket8"
                in run
            )
            assert "--primary-candidate-id score32_float" in run
            assert decoder_inputs["attention_mixed_int8_q12_pwl_proxy_audit"].endswith(
                "decoder_attention_mixed_int8_q12_pwl_proxy_audit__"
                "l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1.json"
            )
            assert decoder_inputs["attention_mixed_int8_quality_backed_frontier"].endswith(
                "decoder_attention_mixed_int8_quality_backed_frontier__"
                "l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1.json"
            )
            assert "attention_mixed_int8_score_precision_recovery_out" in decoder_inputs
            assert (
                decoder_inputs["attention_mixed_int8_score_precision_recovery_out"]
                in work_item.expected_outputs
            )
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_mixed_int8_score_precision_recovery",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": [
                    "l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1",
                    "l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1",
                ],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_mixed_int8_score_margin_audit_evidence() -> None:
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
                    item_id="l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1/"
                        "proposal.json"
                    ),
                    abstraction_layer="decoder_attention_mixed_int8_score_margin_audit",
                    evaluation_mode="quality_gate",
                    comparison_role="score_margin_audit",
                    depends_on_item_ids=[
                        "l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "audit_decoder_attention_mixed_int8_score_margin",
            ]
            run = commands[0]["run"]
            assert "audit_llm_decoder_attention_mixed_int8_score_margin.py" in run
            assert "--score-precision-recovery-json" in run
            assert decoder_inputs["attention_mixed_int8_score_precision_recovery"].endswith(
                "decoder_attention_mixed_int8_score_precision_recovery__"
                "l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1.json"
            )
            assert "attention_mixed_int8_score_margin_audit_out" in decoder_inputs
            assert decoder_inputs["attention_mixed_int8_score_margin_audit_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_mixed_int8_score_margin_audit",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": [
                    "l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1",
                ],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_mixed_int8_generation_quality_evidence() -> None:
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
                    item_id="l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1/"
                        "proposal.json"
                    ),
                    abstraction_layer="decoder_attention_mixed_int8_generation_quality",
                    evaluation_mode="quality_gate",
                    comparison_role="generation_quality",
                    depends_on_item_ids=[
                        "l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1_r2",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "evaluate_decoder_attention_mixed_int8_generation_quality",
            ]
            run = commands[0]["run"]
            assert "evaluate_llm_decoder_model_native_mixed_int8_generation_quality.py" in run
            assert "--candidate score32_float:q8,k8,v8,s32,w16,float_quantized" in run
            assert "RTLGEN_MODEL_NATIVE_7B_GENERATION_MAX_PROMPTS" in run
            assert "RTLGEN_MODEL_NATIVE_7B_GENERATION_STEPS" in run
            assert decoder_inputs["attention_mixed_int8_score_margin_audit"].endswith(
                "decoder_attention_mixed_int8_score_margin_audit__"
                "l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1_r2.json"
            )
            assert "attention_mixed_int8_generation_quality_out" in decoder_inputs
            assert decoder_inputs["attention_mixed_int8_generation_quality_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_mixed_int8_generation_quality",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": [
                    "l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1_r2",
                ],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_score32_w16_recip_lut_q16_generation_quality_evidence() -> None:
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
                    item_id=(
                        "l2_decoder_attention_mixed_int8_score32_w16_recip_lut_q16_"
                        "generation_quality_llama7b_v1"
                    ),
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id=(
                        "prop_l2_decoder_attention_mixed_int8_score32_w16_recip_lut_q16_"
                        "generation_quality_llama7b_v1"
                    ),
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_mixed_int8_score32_w16_recip_lut_q16_"
                        "generation_quality_llama7b_v1/proposal.json"
                    ),
                    abstraction_layer=(
                        "decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality"
                    ),
                    evaluation_mode="quality_gate",
                    comparison_role="score32_w16_recip_lut_q16_generation_quality",
                    depends_on_item_ids=[
                        "l2_decoder_attention_composed_datapath_score32_w16_recip_lut_q16_reduced_replica_llama7b_v1",
                        "l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "evaluate_decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality",
            ]
            run = commands[0]["run"]
            assert "evaluate_llm_decoder_model_native_mixed_int8_generation_quality.py" in run
            assert "--candidate score32_w16_rtl_recip_q16:q8,k8,v8,s32,w16,rtl_recip_lut_q16" in run
            assert "--primary-candidate-id score32_w16_rtl_recip_q16" in run
            assert decoder_inputs["attention_score32_w16_recip_lut_q16_physical_recost"].endswith(
                "decoder_attention_composed_datapath_physical_feasibility__"
                "l2_decoder_attention_composed_datapath_score32_w16_recip_lut_q16_reduced_replica_llama7b_v1.json"
            )
            assert decoder_inputs["attention_mixed_int8_generation_quality_baseline"].endswith(
                "decoder_attention_mixed_int8_generation_quality__"
                "l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3.json"
            )
            assert "attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality_out" in decoder_inputs
            assert (
                decoder_inputs["attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality_out"]
                in work_item.expected_outputs
            )
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": [
                    "l2_decoder_attention_composed_datapath_score32_w16_recip_lut_q16_reduced_replica_llama7b_v1",
                    "l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3",
                ],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_score32_w16_rtl_exact_generation_quality_evidence() -> None:
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
                    item_id="l2_decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id=(
                        "prop_l2_decoder_attention_mixed_int8_score32_w16_rtl_exact_"
                        "generation_quality_llama7b_v1"
                    ),
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_mixed_int8_score32_w16_rtl_exact_"
                        "generation_quality_llama7b_v1/proposal.json"
                    ),
                    abstraction_layer="decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality",
                    evaluation_mode="quality_gate",
                    comparison_role="score32_w16_rtl_exact_generation_quality",
                    depends_on_item_ids=[
                        "l2_decoder_attention_composed_datapath_score32_w16_exact_div_reduced_replica_llama7b_v1_r2",
                        "l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3",
                        "l2_decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality_llama7b_v1",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "evaluate_decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality",
            ]
            run = commands[0]["run"]
            assert "evaluate_llm_decoder_model_native_mixed_int8_generation_quality.py" in run
            assert "--candidate score32_w16_rtl_exact:q8,k8,v8,s32,w16,rtl_exact" in run
            assert "--primary-candidate-id score32_w16_rtl_exact" in run
            assert decoder_inputs["attention_score32_w16_exact_div_physical_recost"].endswith(
                "decoder_attention_composed_datapath_physical_feasibility__"
                "l2_decoder_attention_composed_datapath_score32_w16_exact_div_reduced_replica_llama7b_v1_r2.json"
            )
            assert decoder_inputs["attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality"].endswith(
                "decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality__"
                "l2_decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality_llama7b_v1.json"
            )
            assert "attention_mixed_int8_score32_w16_rtl_exact_generation_quality_out" in decoder_inputs
            assert (
                decoder_inputs["attention_mixed_int8_score32_w16_rtl_exact_generation_quality_out"]
                in work_item.expected_outputs
            )
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality",
            }


def test_generate_l2_campaign_task_adds_score32_exp_lut_div_generation_quality_evidence() -> None:
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
                    item_id="l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id=(
                        "prop_l2_decoder_attention_mixed_int8_score32_exp_lut_div_"
                        "generation_quality_llama7b_v1"
                    ),
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_mixed_int8_score32_exp_lut_div_"
                        "generation_quality_llama7b_v1/proposal.json"
                    ),
                    abstraction_layer="decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality",
                    evaluation_mode="quality_gate",
                    comparison_role="score32_exp_lut_div_generation_quality",
                    depends_on_item_ids=[
                        "l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3",
                        "l2_decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality_llama7b_v1",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "evaluate_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality",
            ]
            run = commands[0]["run"]
            assert "evaluate_llm_decoder_model_native_mixed_int8_generation_quality.py" in run
            assert "--candidate score32_exp_lut_div:q8,k8,v8,s32,w16,exp_lut_div_bucket20" in run
            assert "--primary-candidate-id score32_exp_lut_div" in run
            assert decoder_inputs["attention_mixed_int8_generation_quality_baseline"].endswith(
                "decoder_attention_mixed_int8_generation_quality__"
                "l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3.json"
            )
            assert decoder_inputs["attention_mixed_int8_score32_w16_rtl_exact_generation_quality"].endswith(
                "decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality__"
                "l2_decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality_llama7b_v1.json"
            )
            assert decoder_inputs["attention_score32_exp_lut_div_composed_config"].endswith(
                "attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/"
                "config.json"
            )
            assert "attention_mixed_int8_score32_exp_lut_div_generation_quality_out" in decoder_inputs
            assert (
                decoder_inputs["attention_mixed_int8_score32_exp_lut_div_generation_quality_out"]
                in work_item.expected_outputs
            )
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": [
                    "l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3",
                    "l2_decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality_llama7b_v1",
                ],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_score24_w16_rtl_exact_generation_quality_evidence() -> None:
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
                    item_id="l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id=(
                        "prop_l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_"
                        "generation_quality_llama7b_v1"
                    ),
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_"
                        "generation_quality_llama7b_v1/proposal.json"
                    ),
                    abstraction_layer="decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality",
                    evaluation_mode="quality_gate",
                    comparison_role="score24_w16_rtl_exact_generation_quality",
                    depends_on_item_ids=[
                        "l2_decoder_attention_composed_datapath_score24_w16_exact_div_reduced_replica_llama7b_v1",
                        "l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3",
                        "l2_decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality_llama7b_v1",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "evaluate_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality",
            ]
            run = commands[0]["run"]
            assert "evaluate_llm_decoder_model_native_mixed_int8_generation_quality.py" in run
            assert "--candidate score24_w16_rtl_exact:q8,k8,v8,s24,w16,rtl_exact" in run
            assert "--primary-candidate-id score24_w16_rtl_exact" in run
            assert decoder_inputs["attention_score24_w16_exact_div_physical_recost"].endswith(
                "decoder_attention_composed_datapath_physical_feasibility__"
                "l2_decoder_attention_composed_datapath_score24_w16_exact_div_reduced_replica_llama7b_v1.json"
            )
            assert decoder_inputs["attention_mixed_int8_score32_w16_rtl_exact_generation_quality"].endswith(
                "decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality__"
                "l2_decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality_llama7b_v1.json"
            )
            assert "attention_mixed_int8_score24_w16_rtl_exact_generation_quality_out" in decoder_inputs
            assert (
                decoder_inputs["attention_mixed_int8_score24_w16_rtl_exact_generation_quality_out"]
                in work_item.expected_outputs
            )
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality",
            }


def test_generate_l2_campaign_task_adds_score32_w16_rtl_recip_precision_generation_quality_evidence() -> None:
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
                    item_id=(
                        "l2_decoder_attention_mixed_int8_score32_w16_rtl_recip_precision_"
                        "generation_quality_llama7b_v1"
                    ),
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id=(
                        "prop_l2_decoder_attention_mixed_int8_score32_w16_rtl_recip_precision_"
                        "generation_quality_llama7b_v1"
                    ),
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_mixed_int8_score32_w16_rtl_recip_precision_"
                        "generation_quality_llama7b_v1/proposal.json"
                    ),
                    abstraction_layer=(
                        "decoder_attention_mixed_int8_score32_w16_rtl_recip_precision_generation_quality"
                    ),
                    evaluation_mode="quality_gate",
                    comparison_role="score32_w16_rtl_recip_precision_generation_quality",
                    depends_on_item_ids=[
                        "l2_decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality_llama7b_v1",
                        "l2_decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality_llama7b_v1",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "evaluate_decoder_attention_mixed_int8_score32_w16_rtl_recip_precision_generation_quality",
            ]
            run = commands[0]["run"]
            assert "evaluate_llm_decoder_model_native_mixed_int8_generation_quality.py" in run
            for bits in (16, 18, 20, 22, 24):
                assert (
                    f"--candidate score32_w16_rtl_recip_q{bits}:q8,k8,v8,s32,w16,rtl_recip_lut_q{bits}"
                    in run
                )
            assert "--primary-candidate-id score32_w16_rtl_recip_q24" in run
            assert decoder_inputs["attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality"].endswith(
                "decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality__"
                "l2_decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality_llama7b_v1.json"
            )
            assert decoder_inputs["attention_mixed_int8_score32_w16_rtl_exact_generation_quality"].endswith(
                "decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality__"
                "l2_decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality_llama7b_v1.json"
            )
            assert "attention_mixed_int8_score32_w16_rtl_recip_precision_generation_quality_out" in decoder_inputs
            assert (
                decoder_inputs["attention_mixed_int8_score32_w16_rtl_recip_precision_generation_quality_out"]
                in work_item.expected_outputs
            )
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": [
                    "l2_decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality_llama7b_v1",
                    "l2_decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality_llama7b_v1",
                ],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_softmax_replacement_generation_quality_evidence() -> None:
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
                    item_id="l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1/"
                        "proposal.json"
                    ),
                    abstraction_layer="decoder_attention_mixed_int8_softmax_replacement_generation_quality",
                    evaluation_mode="quality_gate",
                    comparison_role="softmax_replacement_generation_quality",
                    depends_on_item_ids=[
                        "l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3",
                        "l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1",
                        "l2_decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality_llama7b_v1",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "evaluate_decoder_attention_mixed_int8_softmax_replacement_generation_quality",
            ]
            run = commands[0]["run"]
            assert "evaluate_llm_decoder_model_native_mixed_int8_generation_quality.py" in run
            assert "--candidate score32_float:q8,k8,v8,s32,w16,float_quantized" in run
            assert "--candidate qkv8_float_exact:q8,k8,v8,s24,w16,float_exact" in run
            assert "--candidate score32_w16_rtl_exact:q8,k8,v8,s32,w16,rtl_exact" in run
            assert "--candidate qkv8_q20_pwl_recip_q20_bucket8:q8,k8,v8,s20,w20,pwl_recip_lut_q20_bucket8" in run
            assert "--candidate qkv8_q24_pwl_recip_q24_bucket8:q8,k8,v8,s24,w24,pwl_recip_lut_q24_bucket8" in run
            assert "--primary-candidate-id qkv8_q24_pwl_recip_q24_bucket8" in run
            assert decoder_inputs["attention_mixed_int8_generation_quality_baseline"].endswith(
                "decoder_attention_mixed_int8_generation_quality__"
                "l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3.json"
            )
            assert decoder_inputs["attention_mixed_int8_score32_w16_rtl_exact_generation_quality"].endswith(
                "decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality__"
                "l2_decoder_attention_mixed_int8_score32_w16_rtl_exact_generation_quality_llama7b_v1.json"
            )
            assert "attention_mixed_int8_softmax_replacement_generation_quality_out" in decoder_inputs
            assert (
                decoder_inputs["attention_mixed_int8_softmax_replacement_generation_quality_out"]
                in work_item.expected_outputs
            )


def test_generate_l2_campaign_task_adds_mixed_int8_quality_backed_frontier_evidence() -> None:
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
                    item_id="l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1/"
                        "proposal.json"
                    ),
                    abstraction_layer="decoder_attention_mixed_int8_quality_backed_frontier",
                    evaluation_mode="frontier_detail",
                    comparison_role="quality_backed_frontier",
                    depends_on_item_ids=[
                        "l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1_r2",
                        "l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1_r2",
                        "l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "audit_decoder_attention_mixed_int8_quality_backed_frontier",
            ]
            run = commands[0]["run"]
            assert "audit_llm_decoder_attention_mixed_int8_quality_backed_frontier.py" in run
            assert "--mixed-int8-energy-closure-json" in run
            assert "--mixed-int8-broad-native-quality-json" in run
            assert "--mixed-int8-generation-quality-json" in run
            assert decoder_inputs["attention_mixed_int8_energy_closure"].endswith(
                "decoder_attention_mixed_int8_energy_closure__"
                "l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1_r2.json"
            )
            assert decoder_inputs["attention_mixed_int8_broad_native_quality"].endswith(
                "decoder_attention_mixed_int8_broad_native_quality__"
                "l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1_r2.json"
            )
            assert decoder_inputs["attention_mixed_int8_generation_quality"].endswith(
                "decoder_attention_mixed_int8_generation_quality__"
                "l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3.json"
            )
            assert "attention_mixed_int8_quality_backed_frontier_out" in decoder_inputs
            assert (
                decoder_inputs["attention_mixed_int8_quality_backed_frontier_out"]
                in work_item.expected_outputs
            )
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_mixed_int8_quality_backed_frontier",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": [
                    "l2_decoder_attention_mixed_int8_energy_closure_llama7b_v1_r2",
                    "l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1_r2",
                    "l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3",
                ],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_mixed_int8_quality_energy_frontier_evidence() -> None:
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
                    item_id="l2_decoder_attention_mixed_int8_quality_energy_frontier_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_mixed_int8_quality_energy_frontier_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/"
                        "prop_l2_decoder_attention_mixed_int8_quality_energy_frontier_llama7b_v1/"
                        "proposal.json"
                    ),
                    abstraction_layer="decoder_attention_mixed_int8_quality_energy_frontier",
                    evaluation_mode="frontier_detail",
                    comparison_role="quality_energy_frontier",
                    depends_on_item_ids=[
                        "l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1",
                        "l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1_r2",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]

            assert [command["name"] for command in commands[:1]] == [
                "audit_decoder_attention_mixed_int8_quality_energy_frontier",
            ]
            run = commands[0]["run"]
            assert "audit_llm_decoder_attention_mixed_int8_quality_energy_frontier.py" in run
            assert "--quality-backed-frontier-json" in run
            assert "--score-precision-recovery-json" in run
            assert "--fp16-softmax-nm1-metrics" in run
            assert "--fp16-softmax-nm2-metrics" in run
            assert decoder_inputs["attention_mixed_int8_quality_backed_frontier"].endswith(
                "decoder_attention_mixed_int8_quality_backed_frontier__"
                "l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1.json"
            )
            assert decoder_inputs["attention_mixed_int8_score_precision_recovery"].endswith(
                "decoder_attention_mixed_int8_score_precision_recovery__"
                "l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1_r2.json"
            )
            assert decoder_inputs["attention_fp16_softmax_nm1_metrics"].endswith(
                "runs/designs/npu_blocks/npu_fp16_cpp_nm1_softmaxcmp/metrics.csv"
            )
            assert "attention_mixed_int8_quality_energy_frontier_out" in decoder_inputs
            assert (
                decoder_inputs["attention_mixed_int8_quality_energy_frontier_out"]
                in work_item.expected_outputs
            )
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_mixed_int8_quality_energy_frontier",
            }
            assert work_item.task_request.request_payload["developer_loop"]["dependencies"] == {
                "item_ids": [
                    "l2_decoder_attention_mixed_int8_quality_backed_frontier_llama7b_v1",
                    "l2_decoder_attention_mixed_int8_score_precision_recovery_llama7b_v1_r2",
                ],
                "requires_merged_inputs": True,
                "requires_materialized_refs": True,
            }


def test_generate_l2_campaign_task_adds_attention_mixed_precision_quality_evidence() -> None:
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
                    item_id="l2_decoder_attention_mixed_precision_quality_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_mixed_precision_quality",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "estimate_decoder_attention_mixed_precision_quality" in command_names
            assert "attention_kv_dual_stream_physical_feasibility" in decoder_inputs
            assert "attention_mixed_precision_quality_out" in decoder_inputs
            assert "estimate_llm_decoder_attention_mixed_precision_quality.py" in run
            assert "l2_decoder_attention_kv_dual_stream_physical_feasibility_llama7b_v1.json" in run
            assert "--candidate-spec-list q8:k8:v8:a24:s24:w16" in run
            assert "q6:k8:v8:a24:s24:w16" in run
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_mixed_precision_quality__"
                    "l2_decoder_attention_mixed_precision_quality_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_attention_softmax_pow2sum_quality_evidence() -> None:
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
                    item_id="l2_decoder_attention_softmax_pow2sum_quality_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_softmax_pow2sum_quality",
                    evaluation_mode="quality_equivalence_gate",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "estimate_decoder_attention_softmax_pow2sum_quality" in command_names
            assert "attention_kv_dual_stream_physical_feasibility" in decoder_inputs
            assert "attention_mixed_precision_quality_out" in decoder_inputs
            assert "estimate_llm_decoder_attention_mixed_precision_quality.py" in run
            assert "--candidate-spec-list q8:k8:v6:a24:s8:w8" in run
            assert "--softmax-mode-list rtl_exact,rtl_pow2sum" in run
            assert "--seed-count 2" in run
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_mixed_precision_quality__"
                    "l2_decoder_attention_softmax_pow2sum_quality_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_attention_softmax_recip_lut_quality_evidence() -> None:
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
                    item_id="l2_decoder_attention_softmax_recip_lut_quality_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_softmax_recip_lut_quality",
                    evaluation_mode="quality_equivalence_gate",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "estimate_decoder_attention_softmax_recip_lut_quality" in command_names
            assert "attention_kv_dual_stream_physical_feasibility" in decoder_inputs
            assert "attention_mixed_precision_quality_out" in decoder_inputs
            assert "estimate_llm_decoder_attention_mixed_precision_quality.py" in run
            assert "--candidate-spec-list q8:k8:v6:a24:s8:w8" in run
            assert "--softmax-mode-list rtl_exact,rtl_pow2sum,rtl_recip_lut_q8,rtl_recip_lut_q10,rtl_recip_lut_q12" in run
            assert "--seed-count 2" in run
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_mixed_precision_quality__"
                    "l2_decoder_attention_softmax_recip_lut_quality_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_attention_mixed_precision_physical_feasibility_evidence() -> None:
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
                    item_id="l2_decoder_attention_mixed_precision_physical_feasibility_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_mixed_precision_physical_feasibility",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "estimate_decoder_attention_mixed_precision_physical_feasibility" in command_names
            assert "attention_kv_subtile_pipeline_schedule" in decoder_inputs
            assert "attention_mixed_precision_quality" in decoder_inputs
            assert "attention_kv_mixed_precision_full_value_tile_metrics" in decoder_inputs
            assert "attention_mixed_precision_physical_feasibility_out" in decoder_inputs
            assert "estimate_llm_decoder_attention_kv_dual_stream_physical_feasibility.py" in run
            assert "attention_kv_full_value_hd64_kv8_v6_tl16_b128_p8_ppc2_w22_a40_wrapper/metrics.csv" in run
            assert "l2_decoder_attention_mixed_precision_quality_llama7b_v1.json" in run
            assert "--precision-profile q8_k8_v6_a24_s24_w16" in run
            assert "--model-name llm_decoder_attention_mixed_precision_physical_feasibility_llama7b_v1" in run
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_mixed_precision_physical_feasibility__"
                    "l2_decoder_attention_mixed_precision_physical_feasibility_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_attention_mixed_precision_int8_compute_physical_feasibility_evidence() -> None:
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
                    item_id="l2_decoder_attention_mixed_precision_int8_compute_physical_feasibility_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_mixed_precision_int8_compute_physical_feasibility",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "estimate_decoder_attention_mixed_precision_int8_compute_physical_feasibility" in command_names
            assert "attention_kv_subtile_pipeline_schedule" in decoder_inputs
            assert "attention_mixed_precision_quality" in decoder_inputs
            assert "attention_kv_mixed_precision_full_value_tile_metrics" in decoder_inputs
            assert "attention_int8_dense_compute_metrics" in decoder_inputs
            assert "attention_mixed_precision_int8_compute_physical_feasibility_out" in decoder_inputs
            assert "estimate_llm_decoder_attention_kv_dual_stream_physical_feasibility.py" in run
            assert "npu_dense_gemm_tile_int8_16x8_k1_p1/metrics.csv" in run
            assert "--compute-block-macs-per-cycle 128" in run
            assert "--compute-arch-name dense_gemm_int8_16x8_k1_p1" in run
            assert "--precision-profile q8_k8_v6_a24_s24_w16_int8_compute" in run
            assert (
                "--model-name llm_decoder_attention_mixed_precision_int8_compute_physical_feasibility_llama7b_v1"
                in run
            )
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_mixed_precision_int8_compute_physical_feasibility__"
                    "l2_decoder_attention_mixed_precision_int8_compute_physical_feasibility_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_attention_mixed_precision_int8_compute_physical_feasibility_with_softmax_recip_lut_quality_gate() -> None:
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
                    item_id="l2_decoder_attention_mixed_precision_int8_compute_physical_feasibility_softmax_recip_lut_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_mixed_precision_int8_compute_physical_feasibility",
                    evaluation_mode="frontier_detail",
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "estimate_decoder_attention_mixed_precision_int8_compute_physical_feasibility" in command_names
            assert (
                decoder_inputs["attention_kv_subtile_pipeline_schedule"]
                == "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_subtile_pipeline_schedule__"
                "l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1.json"
            )
            assert (
                decoder_inputs["attention_mixed_precision_quality"]
                == "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_precision_quality__"
                "l2_decoder_attention_mixed_precision_quality_llama7b_v1.json"
            )
            assert "attention_kv_mixed_precision_full_value_tile_metrics" in decoder_inputs
            assert "attention_int8_dense_compute_metrics" in decoder_inputs
            assert "attention_mixed_precision_int8_compute_physical_feasibility_out" in decoder_inputs
            assert (
                decoder_inputs["attention_softmax_recip_lut_quality_decision"]
                == "control_plane/shadow_exports/l2_decisions/l2_decoder_attention_softmax_recip_lut_quality_llama7b_v1_r3.json"
            )
            assert "estimate_llm_decoder_attention_kv_dual_stream_physical_feasibility.py" in run
            assert (
                "decoder_attention_kv_subtile_pipeline_schedule__"
                "l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1.json"
                in run
            )
            assert (
                "decoder_attention_mixed_precision_quality__l2_decoder_attention_mixed_precision_quality_llama7b_v1.json"
                in run
            )
            assert (
                "l2_decoder_attention_softmax_recip_lut_quality_llama7b_v1_r3.json"
                not in run
            )
            assert "--precision-profile q8_k8_v6_a24_s8_w8_recip_lut_q10_int8_compute" in run
            assert (
                "--model-name llm_decoder_attention_mixed_precision_int8_compute_physical_feasibility_softmax_recip_lut_llama7b_v1"
                in run
            )
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert any(
                output.endswith(
                    "decoder_attention_mixed_precision_int8_compute_physical_feasibility__"
                    "l2_decoder_attention_mixed_precision_int8_compute_physical_feasibility_softmax_recip_lut_llama7b_v1.json"
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
            assert "--measured-l1-profile hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q10" in run
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


def test_generate_l2_campaign_task_adds_endpoint_sram_noc_full_search_softmax_recip_lut_schedule_evidence() -> None:
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
                    item_id="l2_decoder_attention_kv_endpoint_sram_noc_full_search_softmax_recip_lut_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_endpoint_sram_noc_full_search_softmax_recip_lut_schedule",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            command_names = [command["name"] for command in commands]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            build_run = commands[0]["run"]
            run = commands[1]["run"]

            assert "build_decoder_attention_recip_lut_local_costs" in command_names
            assert "estimate_decoder_attention_kv_endpoint_sram_noc_full_search_schedule" in command_names
            assert "attention_kv_dense_tile_endpoint_topology_scheduler_pairs" in decoder_inputs
            assert "attention_kv_endpoint_measured_l1_costs" in decoder_inputs
            assert "attention_kv_endpoint_base_measured_l1_costs" in decoder_inputs
            assert "attention_sram_profile" in decoder_inputs
            assert "attention_kv_endpoint_sram_noc_full_search_schedule_out" in decoder_inputs
            assert "build_llama7b_attention_recip_lut_local_costs.py" in build_run
            assert "llama7b_attention_local_costs_all_measured_endpoint_v1.json" in build_run
            assert "--bits-list 8,10,12" in build_run
            assert "estimate_llm_decoder_attention_kv_sram_noc_constrained_schedule.py" in run
            assert "--topology-pairs-json" in run
            assert "--topology-derived-json" not in run
            assert "llama7b_attention_local_costs_endpoint_recip_lut_q8_q10_q12__" in run
            assert (
                "--measured-l1-profile "
                "hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q8,"
                "hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q10,"
                "hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q12"
            ) in run
            assert "--sram-bank-port-bytes-per-cycle 32" in run
            assert "--endpoint-port-bytes-per-cycle 32,64,128" in run
            assert "--noc-bandwidth-bytes-per-cycle" not in run
            assert "--noc-hops" not in run
            assert work_item.task_request.request_payload["task"]["inputs"]["decoder_contract"] == decoder_inputs
            assert work_item.expected_outputs == expected_outputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_endpoint_sram_noc_full_search_schedule__"
                    "l2_decoder_attention_kv_endpoint_sram_noc_full_search_softmax_recip_lut_llama7b_v1.json"
                )
                for output in expected_outputs
            )
            assert any(
                output.endswith(
                    "llama7b_attention_local_costs_endpoint_recip_lut_q8_q10_q12__"
                    "l2_decoder_attention_kv_endpoint_sram_noc_full_search_softmax_recip_lut_llama7b_v1.json"
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


def test_generate_l2_campaign_task_adds_softmax_recip_lut_endpoint_full_onchip_source() -> None:
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
                    item_id="l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_endpoint_full_onchip_service_schedule",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "attention_kv_endpoint_sram_noc_full_search_schedule" in decoder_inputs
            assert (
                "l2_decoder_attention_kv_endpoint_sram_noc_full_search_softmax_recip_lut_llama7b_v1_r2.json"
                in run
            )
            assert "l2_decoder_attention_kv_endpoint_sram_noc_full_search_schedule_llama7b_v1.json" not in run
            assert work_item.expected_outputs == expected_outputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_endpoint_full_onchip_service_schedule__"
                    "l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1.json"
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


def test_generate_l2_campaign_task_adds_softmax_recip_lut_endpoint_ready_valid_source() -> None:
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
                    item_id="l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_endpoint_ready_valid_service",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "attention_kv_endpoint_full_onchip_service_schedule" in decoder_inputs
            assert (
                "l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1_r2.json"
                in run
            )
            assert "l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_llama7b_v1.json" not in run
            assert work_item.expected_outputs == expected_outputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_endpoint_ready_valid_service__"
                    "l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_llama7b_v1.json"
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
            assert "attention_kv_endpoint_router_wide_l1_promotion" in decoder_inputs
            assert "attention_kv_endpoint_router_segmented_noc_l1_promotion" in decoder_inputs
            assert "attention_kv_local_sram_capacity" in decoder_inputs
            assert "attention_kv_endpoint_router_sram_composition_out" in decoder_inputs
            assert "audit_llm_decoder_attention_endpoint_router_sram_composition.py" in run
            assert "l2_decoder_attention_kv_endpoint_ready_valid_service_llama7b_v1.json" in run
            assert "l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_llama7b_v1.json" in run
            assert "llama7b_attention_tile_buffers_v1/sram_metrics_summary.json" in run
            assert "--local-sram-capacity-json" in run
            assert "l2_decoder_attention_local_sram_capacity_llama7b_v1.json" in run
            assert "--wide-l1-promotion-json" in run
            assert "l1_decoder_attention_endpoint_router_wide_ppa_v1.json" in run
            assert "--segmented-l1-promotion-json" in run
            assert (
                "l1_decoder_attention_endpoint_router_segmented_noc_ppa_v1.json" in run
            )
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


def test_generate_l2_campaign_task_adds_softmax_recip_lut_endpoint_router_sram_sources() -> None:
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
                    item_id="l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    abstraction_layer="decoder_attention_kv_endpoint_router_sram_composition",
                    evaluation_mode="frontier_detail",
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            expected_outputs = work_item.task_request.request_payload["task"]["expected_outputs"]
            run = commands[0]["run"]

            assert "attention_kv_endpoint_ready_valid_service" in decoder_inputs
            assert "attention_kv_endpoint_full_onchip_service_schedule" in decoder_inputs
            assert (
                "l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_llama7b_v1.json"
                in run
            )
            assert (
                "l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1_r2.json"
                in run
            )
            assert "attention_kv_local_sram_capacity" in decoder_inputs
            assert "--local-sram-capacity-json" in run
            assert "l2_decoder_attention_local_sram_capacity_llama7b_v1.json" in run
            assert "attention_kv_endpoint_router_wide_l1_promotion" in decoder_inputs
            assert "l1_decoder_attention_endpoint_router_wide_ppa_v1.json" in run
            assert "attention_kv_endpoint_router_segmented_noc_l1_promotion" in decoder_inputs
            assert "l1_decoder_attention_endpoint_router_segmented_noc_ppa_v1.json" in run
            assert "l2_decoder_attention_kv_endpoint_ready_valid_service_llama7b_v1.json" not in run
            assert "l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_llama7b_v1.json" not in run
            assert work_item.expected_outputs == expected_outputs
            assert any(
                output.endswith(
                    "decoder_attention_kv_endpoint_router_sram_composition__"
                    "l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1.json"
                )
                for output in expected_outputs
            )


def test_generate_l2_campaign_task_adds_attention_pwl_recip_lut_boundary_evidence() -> None:
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
                    item_id="l2_decoder_attention_pwl_recip_lut_boundary_llama7b_v1",
                    requested_by="@tester",
                    source_commit=source_commit,
                    proposal_id="prop_l2_decoder_attention_pwl_recip_lut_boundary_llama7b_v1",
                    proposal_path=(
                        "docs/proposals/prop_l2_decoder_attention_pwl_recip_lut_boundary_llama7b_v1/proposal.json"
                    ),
                    abstraction_layer="decoder_attention_pwl_recip_lut_boundary",
                    evaluation_mode="frontier_followup",
                    comparison_role="pwl_recip_lut_synthesis_boundary",
                    depends_on_item_ids=[
                        "l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1",
                        "l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1_r2",
                    ],
                    requires_merged_inputs=True,
                    requires_materialized_refs=True,
                    run_physical=False,
                ),
            )

            work_item = session.query(WorkItem).filter_by(item_id=result.item_id).one()
            commands = work_item.task_request.request_payload["task"]["commands"]
            decoder_inputs = work_item.input_manifest["decoder_contract"]
            run = commands[0]["run"]

            assert commands[0]["name"] == "estimate_attention_pwl_recip_lut_boundary"
            assert "estimate_attention_pwl_recip_lut_boundary.py" in run
            assert "qkv8_q20_pwl_recip_q20_bucket8:s=20,w=20,r=20,bucket=8" in run
            assert "qkv8_q24_pwl_recip_q24_bucket8:s=24,w=24,r=24,bucket=8" in run
            assert "attention_pwl_recip_lut_boundary_out" in decoder_inputs
            assert decoder_inputs["attention_pwl_recip_lut_boundary_out"] in work_item.expected_outputs
            assert work_item.task_request.request_payload["developer_loop"]["abstraction"] == {
                "layer": "decoder_attention_pwl_recip_lut_boundary",
            }

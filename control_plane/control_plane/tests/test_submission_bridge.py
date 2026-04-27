"""Submission branch preparation coverage."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.db import create_all
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import ExecutorType, FlowName, LayerName, RunStatus, WorkItemState
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.services.l1_result_consumer import Layer1ConsumeRequest, consume_l1_result
from control_plane.services.l2_result_consumer import Layer2ConsumeRequest, consume_l2_result
from control_plane.services.submission_bridge import SubmissionPrepareRequest, SubmissionPrepareError, prepare_submission_branch


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def _init_repo(repo_root: Path) -> None:
    subprocess.run(["git", "-C", str(repo_root), "init", "-b", "master"], check=True, capture_output=True, text=True)
    _write(repo_root / "README.md", "demo\n")
    _write(repo_root / ".gitignore", "control_plane/shadow_exports/\n")
    _git(repo_root, "add", "README.md", ".gitignore")
    subprocess.run(
        ["git", "-C", str(repo_root), "commit", "-m", "init"],
        check=True,
        capture_output=True,
        text=True,
        env={
            **__import__("os").environ,
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.com",
        },
    )


def _seed_l2_reviewable(session: Session, repo_root: Path) -> tuple[str, str]:
    campaign_dir = repo_root / "control_plane" / "shadow_exports" / "campaigns" / "demo_l2"
    design_metrics_rel = "control_plane/shadow_exports/designs/demo_nm1/metrics.csv"
    schedule_rel = "runs/campaigns/demo_l2/artifacts/mapper/fp16_nm1_demo/demo_model/schedule.yml"
    relu_schedule_rel = "runs/campaigns/demo_l2/artifacts/mapper/fp16_nm1_demo/relu_model/schedule.yml"
    proposal_dir_rel = "docs/proposals/prop_l2_submit_demo"
    proposal_rel = f"{proposal_dir_rel}/proposal.json"
    _write(
        repo_root / proposal_rel,
        json.dumps(
            {
                "proposal_id": "prop_l2_submit_demo",
                "title": "Layer2 submit demo proposal",
                "kind": "architecture",
                "direct_comparison": {
                    "primary_question": "Does the layer2 submission package include proposal context?",
                },
            },
            indent=2,
        )
        + "\n",
    )
    _write(
        repo_root / proposal_dir_rel / "evaluation_requests.json",
        json.dumps(
            {
                "proposal_id": "prop_l2_submit_demo",
                "requested_items": [
                    {
                        "item_id": "l2_submit_demo",
                        "task_type": "l2_campaign",
                        "evaluation_mode": "measurement_only",
                    }
                ],
            },
            indent=2,
        )
        + "\n",
    )
    _write(
        repo_root / design_metrics_rel,
        (
            "design,platform,config_hash,param_hash,tag,status,critical_path_ns,die_area,total_power_mw,params_json,result_path\n"
            'demo_nm1,nangate45,cfg0001,p1,tag1,ok,5.5,2250000,0.18,"{""CLOCK_PERIOD"": 10.0}",'
            "control_plane/shadow_exports/designs/demo_nm1/work/p1/result.json\n"
        ),
    )
    _write(
        campaign_dir / "best_point.json",
        json.dumps(
            {
                "campaign_id": "demo_l2",
                "best": {
                    "arch_id": "fp16_nm1_demo",
                    "macro_mode": "flat_nomacro",
                    "objective_rank": 1,
                    "objective_score": 0.0,
                    "latency_ms_mean": 0.5,
                    "energy_mj_mean": 0.2,
                    "critical_path_ns_mean": 5.5,
                    "die_area_um2_mean": 2250000.0,
                    "total_power_mw_mean": 0.18,
                    "flow_elapsed_s_mean": 1000.0,
                },
            },
            indent=2,
        )
        + "\n",
    )
    _write(
        campaign_dir / "summary.csv",
        (
            "scope,arch_id,macro_mode,model_id,n,sample_count,latency_ms_mean,latency_ms_std,throughput_infer_per_s_mean,throughput_infer_per_s_std,energy_mj_mean,energy_mj_std,critical_path_ns_mean,die_area_um2_mean,total_power_mw_mean,flow_elapsed_s_mean,place_gp_elapsed_s_mean,model_count,rank,latency_norm,energy_norm,area_norm,power_norm,runtime_norm,objective_score,objective_rank\n"
            "aggregate,fp16_nm1_demo,flat_nomacro,,,1,0.5,,1.0,,0.2,,5.5,2250000,0.18,1000,500,1,1,0,0,0,0,0,0,1\n"
        ),
    )
    _write(repo_root / schedule_rel, "schedule: demo\n")
    _write(repo_root / relu_schedule_rel, "schedule: relu\n")
    _write(
        campaign_dir / "results.csv",
        (
            "version,campaign_id,arch_id,macro_mode,model_id,status,artifact_schedule_yml\n"
            f"0.1,demo_l2,fp16_nm1_demo,flat_nomacro,demo_model,ok,{schedule_rel}\n"
            f"0.1,demo_l2,fp16_nm1_demo,flat_nomacro,relu_model,ok,{relu_schedule_rel}\n"
        ),
    )
    _write(campaign_dir / "report.md", "# demo report\n")
    _write(
        campaign_dir / "objective_sweep.csv",
        (
            "profile,w_latency,w_energy,w_area,w_power,w_runtime,best_arch_id,best_macro_mode,objective_score,latency_ms_mean,energy_mj_mean,flow_elapsed_s_mean,best_json,report_md,pareto_csv\n"
            "balanced,1,1,0,0,0,fp16_nm1_demo,flat_nomacro,0.0,0.5,0.2,1000,control_plane/shadow_exports/campaigns/demo_l2/objective_profiles/balanced/best_point.json,control_plane/shadow_exports/campaigns/demo_l2/objective_profiles/balanced/report.md,control_plane/shadow_exports/campaigns/demo_l2/objective_profiles/balanced/pareto.csv\n"
        ),
    )

    payload = {
        "item_id": "l2_submit_demo",
        "title": "Layer2 submit demo",
        "layer": "layer2",
        "flow": "openroad",
        "developer_loop": {
            "proposal_id": "prop_l2_submit_demo",
            "proposal_path": proposal_rel,
            "evaluation": {"mode": "measurement_only"},
            "comparison": {"role": "baseline"},
        },
        "handoff": {
            "branch": "eval/l2_submit_demo/<session_id>",
            "pr_title": "eval: run layer2 submit demo",
            "pr_body_fields": {
                "evaluator_id": "control_plane",
                "session_id": "<session_id>",
                "host": "<host>",
                "queue_item_id": "l2_submit_demo",
            },
            "checklist": ["Commit lightweight campaign outputs only"],
        },
    }
    task_request = TaskRequest(
        request_key="l2_campaign:l2_submit_demo",
        source="test",
        requested_by="@tester",
        title="Layer2 submit demo",
        description="test submission bridge",
        layer=LayerName.LAYER2,
        flow=FlowName.OPENROAD,
        priority=1,
        request_payload=payload,
        source_commit="deadbeef",
    )
    session.add(task_request)
    session.flush()

    work_item = WorkItem(
        work_item_key="l2_campaign:l2_submit_demo",
        task_request_id=task_request.id,
        item_id="l2_submit_demo",
        layer=LayerName.LAYER2,
        flow=FlowName.OPENROAD,
        platform="nangate45",
        task_type="l2_campaign",
        state=WorkItemState.ARTIFACT_SYNC,
        priority=1,
        source_mode="src_verilog",
        input_manifest={},
        command_manifest=[],
        expected_outputs=[
            "control_plane/shadow_exports/campaigns/demo_l2/results.csv",
            "control_plane/shadow_exports/campaigns/demo_l2/summary.csv",
            "control_plane/shadow_exports/campaigns/demo_l2/report.md",
            "control_plane/shadow_exports/campaigns/demo_l2/best_point.json",
            "control_plane/shadow_exports/campaigns/demo_l2/objective_sweep.csv",
            design_metrics_rel,
        ],
        acceptance_rules=[],
        source_commit="deadbeef",
    )
    session.add(work_item)
    session.flush()

    run = Run(
        run_key="l2_submit_demo_run_1",
        work_item_id=work_item.id,
        attempt=1,
        executor_type=ExecutorType.INTERNAL_WORKER,
        status=RunStatus.SUCCEEDED,
        started_at=utcnow(),
        completed_at=utcnow(),
        checkout_commit="deadbeef",
        result_summary="5/5 commands succeeded",
        result_payload={"queue_result": {"status": "ok", "metrics_rows": [f"{design_metrics_rel}:2"], "notes": []}},
    )
    session.add(run)
    session.commit()
    consume_l2_result(session, Layer2ConsumeRequest(repo_root=str(repo_root), item_id=work_item.item_id))
    return work_item.item_id, run.run_key


def _seed_l1_reviewable(session: Session, repo_root: Path) -> tuple[str, str]:
    metrics_rel = "runs/designs/activations/softmax_rowwise_int8_r4_wrapper/metrics.csv"
    _write(
        repo_root / metrics_rel,
        (
            "platform,status,param_hash,tag,critical_path_ns,die_area,total_power_mw,params_json,result_path\n"
            'nangate45,ok,fast0001,tag_fast,12.0,30000,0.18,{"CLOCK_PERIOD": 6.0, "CORE_UTILIZATION": 30},'
            "runs/designs/activations/softmax_rowwise_int8_r4_wrapper/work/fast0001/result.json\n"
        ),
    )
    _write(
        repo_root / "runs/index.csv",
        (
            "circuit_type,design,platform,status,critical_path_ns,die_area,total_power_mw,config_hash,param_hash,tag,result_path,params_json,metrics_path,design_path,sram_area_um2,sram_read_energy_pj,sram_write_energy_pj,sram_max_access_time_ns\n"
            "activations,softmax_rowwise_int8_r4_wrapper,nangate45,ok,12.0,30000,0.18,cfg123,fast0001,tag_fast,runs/designs/activations/softmax_rowwise_int8_r4_wrapper/work/fast0001/result.json,\"{\\\"CLOCK_PERIOD\\\": 6.0}\",runs/designs/activations/softmax_rowwise_int8_r4_wrapper/metrics.csv,runs/designs/activations/softmax_rowwise_int8_r4_wrapper,,,\n"
        ),
    )

    payload = {
        "item_id": "l1_submit_demo",
        "title": "Layer1 submit demo",
        "layer": "layer1",
        "flow": "openroad",
        "handoff": {
            "branch": "eval/l1_submit_demo/<session_id>",
            "pr_title": "eval: run layer1 submit demo",
            "pr_body_fields": {
                "evaluator_id": "control_plane",
                "session_id": "<session_id>",
                "host": "<host>",
                "queue_item_id": "l1_submit_demo",
            },
            "checklist": ["Commit lightweight metrics outputs only"],
        },
    }
    task_request = TaskRequest(
        request_key="l1_sweep:l1_submit_demo",
        source="test",
        requested_by="@tester",
        title="Layer1 submit demo",
        description="test submission bridge with canonical evidence",
        layer=LayerName.LAYER1,
        flow=FlowName.OPENROAD,
        priority=1,
        request_payload=payload,
        source_commit="deadbeef",
    )
    session.add(task_request)
    session.flush()

    work_item = WorkItem(
        work_item_key="l1_sweep:l1_submit_demo",
        task_request_id=task_request.id,
        item_id="l1_submit_demo",
        layer=LayerName.LAYER1,
        flow=FlowName.OPENROAD,
        platform="nangate45",
        task_type="l1_sweep",
        state=WorkItemState.ARTIFACT_SYNC,
        priority=1,
        source_mode="config",
        input_manifest={"configs": ["examples/config_softmax_rowwise_int8.json"]},
        command_manifest=[],
        expected_outputs=[metrics_rel],
        acceptance_rules=[],
        source_commit="deadbeef",
    )
    session.add(work_item)
    session.flush()

    run = Run(
        run_key="l1_submit_demo_run_1",
        work_item_id=work_item.id,
        attempt=1,
        executor_type=ExecutorType.INTERNAL_WORKER,
        status=RunStatus.SUCCEEDED,
        started_at=utcnow(),
        completed_at=utcnow(),
        checkout_commit="deadbeef",
        result_summary="4/4 commands succeeded",
        result_payload={"queue_result": {"status": "ok", "metrics_rows": [f"{metrics_rel}:2"], "notes": []}},
    )
    session.add(run)
    session.commit()
    consume_l1_result(session, Layer1ConsumeRequest(repo_root=str(repo_root), item_id=work_item.item_id))
    return work_item.item_id, run.run_key


def _seed_l1_trial_reviewable(session: Session, repo_root: Path) -> tuple[str, str, str]:
    metrics_rel = "runs/designs/activations/trials/trial_001/softmax_rowwise_int8_r4_wrapper/metrics.csv"
    _write(
        repo_root / metrics_rel,
        (
            "platform,status,param_hash,tag,critical_path_ns,die_area,total_power_mw,params_json,result_path\n"
            'nangate45,ok,trial0001,tag_trial,12.1,30100,0.19,{"CLOCK_PERIOD": 6.0},'
            "runs/designs/activations/trials/trial_001/softmax_rowwise_int8_r4_wrapper/work/trial0001/result.json\n"
        ),
    )
    _write(
        repo_root / "runs/index.csv",
        (
            "circuit_type,design,platform,status,critical_path_ns,die_area,total_power_mw,config_hash,param_hash,tag,result_path,params_json,metrics_path,design_path,sram_area_um2,sram_read_energy_pj,sram_write_energy_pj,sram_max_access_time_ns\n"
            'activations,softmax_rowwise_int8_r4_wrapper,nangate45,ok,12.1,30100,0.19,cfgtrial,trial0001,tag_trial,runs/designs/activations/trials/trial_001/softmax_rowwise_int8_r4_wrapper/work/trial0001/result.json,"{""CLOCK_PERIOD"": 6.0}",runs/designs/activations/trials/trial_001/softmax_rowwise_int8_r4_wrapper/metrics.csv,runs/designs/activations/trials/trial_001/softmax_rowwise_int8_r4_wrapper,,,\n'
        ),
    )

    payload = {
        "item_id": "l1_submit_trial_demo",
        "title": "Layer1 submit trial demo",
        "layer": "layer1",
        "flow": "openroad",
        "handoff": {
            "branch": "eval/l1_submit_trial_demo/<session_id>",
            "pr_title": "eval: run layer1 submit trial demo",
            "pr_body_fields": {
                "evaluator_id": "control_plane",
                "session_id": "<session_id>",
                "host": "<host>",
                "queue_item_id": "l1_submit_trial_demo",
            },
            "checklist": ["Commit lightweight metrics outputs only"],
        },
    }
    task_request = TaskRequest(
        request_key="l1_sweep:l1_submit_trial_demo",
        source="test",
        requested_by="@tester",
        title="Layer1 submit trial demo",
        description="test submission bridge with trial evidence refs",
        layer=LayerName.LAYER1,
        flow=FlowName.OPENROAD,
        priority=1,
        request_payload=payload,
        source_commit="deadbeef",
    )
    session.add(task_request)
    session.flush()

    work_item = WorkItem(
        work_item_key="l1_sweep:l1_submit_trial_demo",
        task_request_id=task_request.id,
        item_id="l1_submit_trial_demo",
        layer=LayerName.LAYER1,
        flow=FlowName.OPENROAD,
        platform="nangate45",
        task_type="l1_sweep",
        state=WorkItemState.ARTIFACT_SYNC,
        priority=1,
        source_mode="config",
        input_manifest={"configs": ["examples/config_softmax_rowwise_int8.json"]},
        command_manifest=[],
        expected_outputs=[],
        acceptance_rules=[],
        source_commit="deadbeef",
    )
    session.add(work_item)
    session.flush()

    run = Run(
        run_key="l1_submit_trial_demo_run_1",
        work_item_id=work_item.id,
        attempt=1,
        executor_type=ExecutorType.INTERNAL_WORKER,
        status=RunStatus.SUCCEEDED,
        started_at=utcnow(),
        completed_at=utcnow(),
        checkout_commit="deadbeef",
        result_summary="4/4 commands succeeded",
        result_payload={"queue_result": {"status": "ok", "metrics_rows": [f"{metrics_rel}:2"], "notes": []}},
    )
    session.add(run)
    session.commit()
    consume_l1_result(session, Layer1ConsumeRequest(repo_root=str(repo_root), item_id=work_item.item_id))
    return work_item.item_id, run.run_key, metrics_rel


def test_prepare_submission_branch_creates_commit_and_manifest() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, run_key = _seed_l2_reviewable(session, repo_root)
            result = prepare_submission_branch(
                session,
                SubmissionPrepareRequest(
                    repo_root=str(repo_root),
                    item_id=item_id,
                    evaluator_id="cpbot",
                    session_id="s20260310t080000z",
                    host="cp-host",
                    worktree_root=str(repo_root / "tmp_submit"),
                ),
            )

            assert result.item_id == item_id
            assert result.run_key == run_key
            assert result.branch_name == "eval/l2_submit_demo/s20260310t080000z"
            assert (Path(result.worktree_path) / "control_plane" / "shadow_exports" / "review" / item_id / "review_package.json").exists()
            assert (Path(result.pr_body_path)).exists()
            manifest = json.loads((repo_root / "control_plane" / "shadow_exports" / "review" / item_id / "submission_manifest.json").read_text())
            assert manifest["branch_name"] == result.branch_name
            assert manifest["materialization_source_commit"] == _git(repo_root, "rev-parse", "HEAD")
            assert manifest["evidence_paths"] == []
            assert "runs/campaigns/demo_l2/artifacts/mapper/fp16_nm1_demo/demo_model/schedule.yml" in manifest["supporting_paths"]
            assert "runs/campaigns/demo_l2/artifacts/mapper/fp16_nm1_demo/relu_model/schedule.yml" in manifest["supporting_paths"]
            assert "docs/proposals/prop_l2_submit_demo/proposal.json" in manifest["supporting_paths"]
            assert "docs/proposals/prop_l2_submit_demo/evaluation_requests.json" in manifest["supporting_paths"]
            assert "gh pr create --draft" in manifest["pr_create_command"]
            assert (
                Path(result.worktree_path)
                / "runs/campaigns/demo_l2/artifacts/mapper/fp16_nm1_demo/demo_model/schedule.yml"
            ).exists()
            assert (
                Path(result.worktree_path)
                / "runs/campaigns/demo_l2/artifacts/mapper/fp16_nm1_demo/relu_model/schedule.yml"
            ).exists()
            assert (
                Path(result.worktree_path)
                / "docs/proposals/prop_l2_submit_demo/proposal.json"
            ).exists()
            assert (
                Path(result.worktree_path)
                / "docs/proposals/prop_l2_submit_demo/evaluation_requests.json"
            ).exists()

            branch_head = _git(repo_root, "rev-parse", result.branch_name)
            assert branch_head == result.commit_sha
            artifact = session.query(Artifact).filter_by(kind="submission_manifest").one()
            assert artifact.path == f"control_plane/shadow_exports/review/{item_id}/submission_manifest.json"


def test_prepare_submission_branch_packages_only_resolved_proposal_file_parent() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, _run_key = _seed_l2_reviewable(session, repo_root)
            _write(
                repo_root / "docs/proposals/prop_unrelated/proposal.json",
                json.dumps({"proposal_id": "prop_unrelated", "title": "Unrelated proposal"}, indent=2) + "\n",
            )

            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            payload = json.loads(json.dumps(work_item.task_request.request_payload))
            payload["developer_loop"]["proposal_path"] = "docs/proposals"
            work_item.task_request.request_payload = payload
            session.commit()

            result = prepare_submission_branch(
                session,
                SubmissionPrepareRequest(
                    repo_root=str(repo_root),
                    item_id=item_id,
                    evaluator_id="cpbot",
                    session_id="s20260310t080010z",
                    host="cp-host",
                    worktree_root=str(repo_root / "tmp_submit"),
                ),
            )

            manifest = json.loads(
                (repo_root / "control_plane" / "shadow_exports" / "review" / item_id / "submission_manifest.json").read_text()
            )
            assert "docs/proposals/prop_l2_submit_demo/proposal.json" in manifest["supporting_paths"]
            assert "docs/proposals/prop_l2_submit_demo/evaluation_requests.json" in manifest["supporting_paths"]
            assert "docs/proposals/prop_unrelated/proposal.json" not in manifest["supporting_paths"]
            assert (Path(result.worktree_path) / "docs/proposals/prop_l2_submit_demo/proposal.json").exists()
            assert not (Path(result.worktree_path) / "docs/proposals/prop_unrelated/proposal.json").exists()


def test_prepare_submission_branch_includes_canonical_runs_evidence_for_real_item() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, run_key = _seed_l1_reviewable(session, repo_root)
            result = prepare_submission_branch(
                session,
                SubmissionPrepareRequest(
                    repo_root=str(repo_root),
                    item_id=item_id,
                    evaluator_id="cpbot",
                    session_id="s20260310t080500z",
                    host="cp-host",
                    worktree_root=str(repo_root / "tmp_submit"),
                ),
            )

            manifest = json.loads((repo_root / "control_plane" / "shadow_exports" / "review" / item_id / "submission_manifest.json").read_text())
            assert manifest["evidence_paths"] == [
                "runs/designs/activations/softmax_rowwise_int8_r4_wrapper/metrics.csv",
            ]
            frozen_map = manifest["frozen_file_map"]
            assert frozen_map["runs/designs/activations/softmax_rowwise_int8_r4_wrapper/metrics.csv"].startswith(
                f"control_plane/shadow_exports/frozen_review/{item_id}/{run_key}/"
            )
            assert (repo_root / frozen_map["runs/designs/activations/softmax_rowwise_int8_r4_wrapper/metrics.csv"]).exists()
            assert (Path(result.worktree_path) / "runs" / "designs" / "activations" / "softmax_rowwise_int8_r4_wrapper" / "metrics.csv").exists()
            assert not (Path(result.worktree_path) / "runs" / "index.csv").exists()


def test_prepare_submission_branch_stages_trial_metrics_from_source_refs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, run_key, metrics_rel = _seed_l1_trial_reviewable(session, repo_root)
            result = prepare_submission_branch(
                session,
                SubmissionPrepareRequest(
                    repo_root=str(repo_root),
                    item_id=item_id,
                    evaluator_id="cpbot",
                    session_id="s20260310t080550z",
                    host="cp-host",
                    worktree_root=str(repo_root / "tmp_submit"),
                ),
            )

            manifest = json.loads((repo_root / "control_plane" / "shadow_exports" / "review" / item_id / "submission_manifest.json").read_text())
            assert manifest["evidence_paths"] == []
            assert manifest["canonical_diff_paths"] == [metrics_rel]
            assert metrics_rel in manifest["supporting_paths"]
            assert (repo_root / manifest["frozen_file_map"][metrics_rel]).exists()
            assert (Path(result.worktree_path) / metrics_rel).exists()


def test_prepare_submission_branch_uses_current_base_branch_instead_of_head() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)
        _write(repo_root / "base.txt", "newer\n")
        _git(repo_root, "add", "base.txt")
        subprocess.run(
            ["git", "-C", str(repo_root), "commit", "-m", "advance master"],
            check=True,
            capture_output=True,
            text=True,
            env={
                **__import__("os").environ,
                "GIT_AUTHOR_NAME": "Test",
                "GIT_AUTHOR_EMAIL": "test@example.com",
                "GIT_COMMITTER_NAME": "Test",
                "GIT_COMMITTER_EMAIL": "test@example.com",
            },
        )
        master_head = _git(repo_root, "rev-parse", "master")
        _git(repo_root, "checkout", "HEAD~1")

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, _run_key = _seed_l1_reviewable(session, repo_root)
            result = prepare_submission_branch(
                session,
                SubmissionPrepareRequest(
                    repo_root=str(repo_root),
                    item_id=item_id,
                    evaluator_id="cpbot",
                    session_id="s20260312t090000z",
                    host="cp-host",
                    worktree_root=str(repo_root / "tmp_submit"),
                ),
            )

            manifest = json.loads((repo_root / "control_plane" / "shadow_exports" / "review" / item_id / "submission_manifest.json").read_text())
            assert manifest["submission_base_commit"] == master_head
            assert _git(repo_root, "rev-parse", f"{result.branch_name}^") == master_head


def test_prepare_submission_branch_rejects_missing_canonical_evidence_diff() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, _run_key = _seed_l1_reviewable(session, repo_root)
            _git(
                repo_root,
                "add",
                "runs/designs/activations/softmax_rowwise_int8_r4_wrapper/metrics.csv",
            )
            subprocess.run(
                ["git", "-C", str(repo_root), "commit", "-m", "seed canonical evidence"],
                check=True,
                capture_output=True,
                text=True,
                env={
                    **__import__("os").environ,
                    "GIT_AUTHOR_NAME": "Test",
                    "GIT_AUTHOR_EMAIL": "test@example.com",
                    "GIT_COMMITTER_NAME": "Test",
                    "GIT_COMMITTER_EMAIL": "test@example.com",
                },
            )

            try:
                prepare_submission_branch(
                    session,
                    SubmissionPrepareRequest(
                        repo_root=str(repo_root),
                        item_id=item_id,
                        evaluator_id="cpbot",
                        session_id="s20260312t083000z",
                        host="cp-host",
                        worktree_root=str(repo_root / "tmp_submit"),
                    ),
                )
            except SubmissionPrepareError as exc:
                assert "no canonical runs evidence diff" in str(exc)
            else:
                raise AssertionError("expected SubmissionPrepareError")


def test_prepare_submission_branch_rejects_existing_branch() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)
        _git(repo_root, "branch", "eval/l2_submit_demo/s20260310t080000z")

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, _run_key = _seed_l2_reviewable(session, repo_root)
            try:
                prepare_submission_branch(
                    session,
                    SubmissionPrepareRequest(
                        repo_root=str(repo_root),
                        item_id=item_id,
                        evaluator_id="cpbot",
                        session_id="s20260310t080000z",
                        host="cp-host",
                        worktree_root=str(repo_root / "tmp_submit"),
                    ),
                )
            except SubmissionPrepareError as exc:
                assert "branch already exists" in str(exc)
            else:
                raise AssertionError("expected SubmissionPrepareError")

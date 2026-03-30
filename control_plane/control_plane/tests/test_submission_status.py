"""Submission eligibility status coverage."""

from __future__ import annotations

import json
import os
from pathlib import Path
from io import StringIO
import subprocess
import tempfile
from contextlib import redirect_stdout

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.cli.submission_status import main as submission_status_main
from control_plane.clock import utcnow
from control_plane.db import create_all
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import ExecutorType, FlowName, LayerName, RunStatus, WorkItemState
from control_plane.models.task_requests import TaskRequest
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem
from control_plane.services.l1_result_consumer import Layer1ConsumeRequest, consume_l1_result
from control_plane.services.l2_result_consumer import Layer2ConsumeRequest, consume_l2_result
from control_plane.services.operator_submission import assess_submission_eligibility


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


def _commit_paths(repo_root: Path, *paths: str) -> None:
    _git(repo_root, 'add', *paths)
    subprocess.run(
        ['git', '-C', str(repo_root), 'commit', '-m', 'record evidence'],
        check=True,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            'GIT_AUTHOR_NAME': 'Test',
            'GIT_AUTHOR_EMAIL': 'test@example.com',
            'GIT_COMMITTER_NAME': 'Test',
            'GIT_COMMITTER_EMAIL': 'test@example.com',
        },
    )


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
            **os.environ,
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.com",
        },
    )


def _seed_l2_reviewable(session: Session, repo_root: Path) -> tuple[str, str]:
    campaign_dir = repo_root / "control_plane" / "shadow_exports" / "campaigns" / "demo_l2"
    design_metrics_rel = "control_plane/shadow_exports/designs/demo_nm1/metrics.csv"
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
    _write(campaign_dir / "results.csv", "version,campaign_id,arch_id,macro_mode,status\n0.1,demo_l2,fp16_nm1_demo,flat_nomacro,ok\n")
    _write(campaign_dir / "report.md", "# demo report\n")
    _write(
        campaign_dir / "objective_sweep.csv",
        (
            "profile,w_latency,w_energy,w_area,w_power,w_runtime,best_arch_id,best_macro_mode,objective_score,latency_ms_mean,energy_mj_mean,flow_elapsed_s_mean,best_json,report_md,pareto_csv\n"
            "balanced,1,1,0,0,0,fp16_nm1_demo,flat_nomacro,0.0,0.5,0.2,1000,control_plane/shadow_exports/campaigns/demo_l2/objective_profiles/balanced/best_point.json,control_plane/shadow_exports/campaigns/demo_l2/objective_profiles/balanced/report.md,control_plane/shadow_exports/campaigns/demo_l2/objective_profiles/balanced/pareto.csv\n"
        ),
    )

    payload = {
        "item_id": "l2_operate_demo",
        "title": "Layer2 operate demo",
        "layer": "layer2",
        "flow": "openroad",
        "handoff": {
            "branch": "eval/l2_operate_demo/<session_id>",
            "pr_title": "eval: run layer2 operate demo",
            "pr_body_fields": {
                "evaluator_id": "control_plane",
                "session_id": "<session_id>",
                "host": "<host>",
                "queue_item_id": "l2_operate_demo",
            },
            "checklist": ["Commit lightweight campaign outputs only"],
        },
    }
    task_request = TaskRequest(
        request_key="l2_campaign:l2_operate_demo",
        source="test",
        requested_by="@tester",
        title="Layer2 operate demo",
        description="test operator submission",
        layer=LayerName.LAYER2,
        flow=FlowName.OPENROAD,
        priority=1,
        request_payload=payload,
        source_commit="deadbeef",
    )
    session.add(task_request)
    session.flush()

    work_item = WorkItem(
        work_item_key="l2_campaign:l2_operate_demo",
        task_request_id=task_request.id,
        item_id="l2_operate_demo",
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
        run_key="l2_operate_demo_run_1",
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
            'nangate45,ok,fast0001,tag_fast,12.0,30000,0.18,{"CLOCK_PERIOD": 6.0},runs/designs/activations/softmax_rowwise_int8_r4_wrapper/work/fast0001/result.json\n'
        ),
    )
    _write(
        repo_root / "runs/index.csv",
        (
            "circuit_type,design,platform,status,critical_path_ns,die_area,total_power_mw,config_hash,param_hash,tag,result_path,params_json,metrics_path,design_path,sram_area_um2,sram_read_energy_pj,sram_write_energy_pj,sram_max_access_time_ns\n"
            'activations,softmax_rowwise_int8_r4_wrapper,nangate45,ok,12.0,30000,0.18,cfg123,fast0001,tag_fast,runs/designs/activations/softmax_rowwise_int8_r4_wrapper/work/fast0001/result.json,{"CLOCK_PERIOD": 6.0},runs/designs/activations/softmax_rowwise_int8_r4_wrapper/metrics.csv,runs/designs/activations/softmax_rowwise_int8_r4_wrapper,,,,\n'
        ),
    )

    payload = {
        "item_id": "l1_status_demo",
        "title": "Layer1 status demo",
        "layer": "layer1",
        "flow": "openroad",
        "handoff": {
            "branch": "eval/l1_status_demo/<session_id>",
            "pr_title": "eval: run layer1 status demo",
            "pr_body_fields": {
                "evaluator_id": "control_plane",
                "session_id": "<session_id>",
                "host": "<host>",
                "queue_item_id": "l1_status_demo",
            },
            "checklist": ["Commit lightweight metrics outputs only"],
        },
    }
    task_request = TaskRequest(
        request_key="l1_sweep:l1_status_demo",
        source="test",
        requested_by="@tester",
        title="Layer1 status demo",
        description="test operator submission eligibility",
        layer=LayerName.LAYER1,
        flow=FlowName.OPENROAD,
        priority=1,
        request_payload=payload,
        source_commit="deadbeef",
    )
    session.add(task_request)
    session.flush()

    work_item = WorkItem(
        work_item_key="l1_sweep:l1_status_demo",
        task_request_id=task_request.id,
        item_id="l1_status_demo",
        layer=LayerName.LAYER1,
        flow=FlowName.OPENROAD,
        platform="nangate45",
        task_type="l1_sweep",
        state=WorkItemState.ARTIFACT_SYNC,
        priority=1,
        source_mode="config",
        input_manifest={"configs": ["examples/config_softmax_rowwise_int8.json"]},
        command_manifest=[],
        expected_outputs=[metrics_rel, "runs/index.csv"],
        acceptance_rules=[],
        source_commit="deadbeef",
    )
    session.add(work_item)
    session.flush()

    run = Run(
        run_key="l1_status_demo_run_1",
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


def test_assess_submission_eligibility_ready_item() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, run_key = _seed_l2_reviewable(session, repo_root)
            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            run = session.query(Run).filter_by(run_key=run_key).one()

            status = assess_submission_eligibility(session, work_item=work_item, run=run)
            assert status.eligible is True
            assert status.reason is None


def test_assess_submission_eligibility_reports_blocked_state() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, run_key = _seed_l2_reviewable(session, repo_root)
            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            work_item.state = WorkItemState.RUNNING
            run = session.query(Run).filter_by(run_key=run_key).one()
            session.commit()

            status = assess_submission_eligibility(session, work_item=work_item, run=run)
            assert status.eligible is False
            assert status.reason == "state=running"


def test_assess_submission_eligibility_reports_no_canonical_runs_evidence_diff() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, run_key = _seed_l2_reviewable(session, repo_root)
            _commit_paths(
                repo_root,
                'control_plane/shadow_exports/campaigns/demo_l2/results.csv',
                'control_plane/shadow_exports/campaigns/demo_l2/summary.csv',
                'control_plane/shadow_exports/campaigns/demo_l2/report.md',
                'control_plane/shadow_exports/campaigns/demo_l2/best_point.json',
                'control_plane/shadow_exports/campaigns/demo_l2/objective_sweep.csv',
                'control_plane/shadow_exports/designs/demo_nm1/metrics.csv',
                'control_plane/shadow_exports/l2_decisions/l2_operate_demo.json',
                'control_plane/shadow_exports/review/l2_operate_demo/evaluated.json',
                'control_plane/shadow_exports/review/l2_operate_demo/review_package.json',
            )
            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            run = session.query(Run).filter_by(run_key=run_key).one()

            status = assess_submission_eligibility(session, work_item=work_item, run=run, repo_root=repo_root)
            assert status.eligible is False
            assert status.reason == 'no canonical runs evidence diff'


def test_assess_submission_eligibility_reports_missing_review_artifact() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, run_key = _seed_l2_reviewable(session, repo_root)
            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            run = session.query(Run).filter_by(run_key=run_key).one()
            artifact = session.query(Artifact).filter_by(run_id=run.id, kind="decision_proposal").one()
            session.delete(artifact)
            session.commit()

            status = assess_submission_eligibility(session, work_item=work_item, run=run)
            assert status.eligible is False
            assert status.reason == "missing decision_proposal artifact"


def test_assess_submission_eligibility_reports_no_canonical_runs_evidence_diff_l1() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, run_key = _seed_l1_reviewable(session, repo_root)
            _commit_paths(
                repo_root,
                'runs/designs/activations/softmax_rowwise_int8_r4_wrapper/metrics.csv',
                'runs/index.csv',
            )
            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            run = session.query(Run).filter_by(run_key=run_key).one()

            status = assess_submission_eligibility(session, work_item=work_item, run=run, repo_root=repo_root)
            assert status.eligible is False
            assert status.reason == 'no canonical runs evidence diff'


def test_submission_status_table_output() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine(f"sqlite+pysqlite:///{Path(td) / 'cp.db'}", future=True)
        create_all(engine)
        with Session(engine) as session:
            _seed_l2_reviewable(session, repo_root)

        buf = StringIO()
        with redirect_stdout(buf):
            rc = submission_status_main(
                [
                    "--database-url",
                    f"sqlite+pysqlite:///{Path(td) / 'cp.db'}",
                    "--format",
                    "table",
                ]
            )
        assert rc == 0
        output = buf.getvalue()
        assert "item_id" in output
        assert "eligible" in output
        assert "l2_operate_demo" in output


def test_submission_status_jsonl_output() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine(f"sqlite+pysqlite:///{Path(td) / 'cp.db'}", future=True)
        create_all(engine)
        with Session(engine) as session:
            _seed_l2_reviewable(session, repo_root)

        buf = StringIO()
        with redirect_stdout(buf):
            rc = submission_status_main(
                [
                    "--database-url",
                    f"sqlite+pysqlite:///{Path(td) / 'cp.db'}",
                    "--jsonl",
                ]
            )
        assert rc == 0
        lines = [line for line in buf.getvalue().splitlines() if line.strip()]
        assert len(lines) == 1
        payload = json.loads(lines[0])
        assert payload["item_id"] == "l2_operate_demo"
        assert payload["eligible"] is True


def test_assess_submission_eligibility_reports_terminal_proposal() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        proposal_dir = repo_root / "docs" / "proposals" / "prop_terminal_demo"
        proposal_dir.mkdir(parents=True, exist_ok=True)
        _write(
            proposal_dir / "proposal.json",
            json.dumps({"proposal_id": "prop_terminal_demo"}, indent=2) + "\n",
        )
        _write(
            proposal_dir / "promotion_result.json",
            json.dumps(
                {
                    "proposal_id": "prop_terminal_demo",
                    "decision": "promote",
                    "pr_number": 114,
                    "merge_commit": "deadbeef",
                    "merged_utc": "2026-03-27T03:10:07Z",
                },
                indent=2,
            ) + "\n",
        )

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, run_key = _seed_l1_reviewable(session, repo_root)
            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            payload = dict(work_item.task_request.request_payload or {})
            payload["developer_loop"] = {
                "proposal_id": "prop_terminal_demo",
                "proposal_path": "docs/proposals/prop_terminal_demo",
            }
            work_item.task_request.request_payload = payload
            session.commit()
            run = session.query(Run).filter_by(run_key=run_key).one()

            status = assess_submission_eligibility(session, work_item=work_item, run=run, repo_root=repo_root)
            assert status.eligible is False
            assert status.reason == "proposal already finalized with decision=promote"

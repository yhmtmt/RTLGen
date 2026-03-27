"""One-shot operator submission coverage."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
import subprocess
import tempfile

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from control_plane.clock import utcnow
from control_plane.db import create_all
from control_plane.models.artifacts import Artifact
from control_plane.models.enums import ExecutorType, FlowName, GitHubLinkState, LayerName, RunStatus, WorkItemState
from control_plane.models.github_links import GitHubLink
from control_plane.models.runs import Run
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem
from control_plane.services.l1_result_consumer import Layer1ConsumeRequest, consume_l1_result
from control_plane.services.l2_result_consumer import Layer2ConsumeRequest, consume_l2_result
from control_plane.services.operator_submission import (
    OperatorSubmissionError,
    OperatorSubmissionRequest,
    operate_submission,
)


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
        "item_id": "l1_operate_demo",
        "title": "Layer1 operate demo",
        "layer": "layer1",
        "flow": "openroad",
        "handoff": {
            "branch": "eval/l1_operate_demo/<session_id>",
            "pr_title": "eval: run layer1 operate demo",
            "pr_body_fields": {
                "evaluator_id": "control_plane",
                "session_id": "<session_id>",
                "host": "<host>",
                "queue_item_id": "l1_operate_demo",
            },
            "checklist": ["Commit lightweight metrics outputs only"],
        },
    }
    task_request = TaskRequest(
        request_key="l1_sweep:l1_operate_demo",
        source="test",
        requested_by="@tester",
        title="Layer1 operate demo",
        description="test operator submission with canonical evidence",
        layer=LayerName.LAYER1,
        flow=FlowName.OPENROAD,
        priority=1,
        request_payload=payload,
        source_commit="deadbeef",
    )
    session.add(task_request)
    session.flush()

    work_item = WorkItem(
        work_item_key="l1_sweep:l1_operate_demo",
        task_request_id=task_request.id,
        item_id="l1_operate_demo",
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
        run_key="l1_operate_demo_run_1",
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


def _make_fake_bin(fake_bin: Path, log_path: Path) -> None:
    fake_bin.mkdir(parents=True, exist_ok=True)
    real_git = shutil.which("git")
    assert real_git is not None
    _write(
        fake_bin / "git",
        "#!/usr/bin/env python3\n"
        "import json, subprocess, sys\n"
        f"log={json.dumps(str(log_path))}\n"
        f"real_git={json.dumps(real_git)}\n"
        "argv=sys.argv[1:]\n"
        "with open(log, 'a', encoding='utf-8') as h:\n"
        "    h.write(json.dumps({'tool':'git','argv':argv})+'\\n')\n"
        "if argv[:4] == ['push', '--force-with-lease', '-u', 'origin'] or argv[:3] == ['push', '-u', 'origin']:\n"
        "    sys.exit(0)\n"
        "completed = subprocess.run([real_git, *argv])\n"
        "sys.exit(completed.returncode)\n",
    )
    _write(
        fake_bin / "gh",
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        f"log={json.dumps(str(log_path))}\n"
        "argv=sys.argv[1:]\n"
        "with open(log, 'a', encoding='utf-8') as h:\n"
        "    h.write(json.dumps({'tool':'gh','argv':argv})+'\\n')\n"
        "if argv[:4] == ['--repo','yhmtmt/RTLGen','pr','create']:\n"
        "    print('https://github.com/yhmtmt/RTLGen/pull/321')\n"
        "    sys.exit(0)\n"
        "if argv[:4] == ['--repo','yhmtmt/RTLGen','pr','view']:\n"
        "    branch=argv[4]\n"
        "    print(json.dumps({'number':321,'url':'https://github.com/yhmtmt/RTLGen/pull/321','headRefName':branch,'baseRefName':'master'}))\n"
        "    sys.exit(0)\n"
        "sys.exit(1)\n",
    )
    os.chmod(fake_bin / "git", 0o755)
    os.chmod(fake_bin / "gh", 0o755)


def test_operate_submission_runs_full_chain_and_reuses_manifest() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, run_key = _seed_l1_reviewable(session, repo_root)
            fake_bin = repo_root / "fake_bin"
            log_path = repo_root / "fake_cmds.log"
            _make_fake_bin(fake_bin, log_path)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}:{old_path}"
            try:
                first = operate_submission(
                    session,
                    OperatorSubmissionRequest(
                        repo_root=str(repo_root),
                        repo="yhmtmt/RTLGen",
                        item_id=item_id,
                        evaluator_id="cpbot",
                        session_id="s20260310t090000z",
                        host="cp-host",
                        worktree_root=str(repo_root / "tmp_submit"),
                    ),
                )
                second = operate_submission(
                    session,
                    OperatorSubmissionRequest(
                        repo_root=str(repo_root),
                        repo="yhmtmt/RTLGen",
                        item_id=item_id,
                        evaluator_id="cpbot",
                        session_id="s20260310t090123z",
                        host="cp-host",
                        worktree_root=str(repo_root / "tmp_submit"),
                    ),
                )
            finally:
                os.environ["PATH"] = old_path

            assert first.item_id == item_id
            assert first.run_key == run_key
            assert first.review_published is True
            assert first.submission_prepared is True
            assert first.submission_prepared_reused is False
            assert first.submission_executed is True
            assert first.pr_number == 321

            assert second.submission_prepared is False
            assert second.submission_prepared_reused is True
            assert second.pr_number == 321
            assert second.branch_name == first.branch_name

            operator_path = repo_root / "control_plane" / "shadow_exports" / "review" / item_id / "operator_submission.json"
            assert operator_path.exists()
            operator_payload = json.loads(operator_path.read_text(encoding="utf-8"))
            assert operator_payload["pr_number"] == 321

            evaluated_path = repo_root / "control_plane" / "shadow_exports" / "review" / item_id / "evaluated.json"
            evaluated_payload = json.loads(evaluated_path.read_text(encoding="utf-8"))
            assert evaluated_payload["result"]["branch"] == first.branch_name
            assert evaluated_payload["result"]["session_id"] == "s20260310t090000z"
            assert evaluated_payload["handoff"]["branch"] == first.branch_name
            assert evaluated_payload["handoff"]["pr_body_fields"]["session_id"] == "s20260310t090000z"

            link = session.query(GitHubLink).filter_by(pr_number=321).one()
            assert link.state == GitHubLinkState.PR_OPEN
            artifact = session.query(Artifact).filter_by(kind="operator_submission").one()
            assert artifact.path == f"control_plane/shadow_exports/review/{item_id}/operator_submission.json"


def test_operate_submission_rebuilds_manifest_when_latest_run_differs() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, _run_key = _seed_l1_reviewable(session, repo_root)
            fake_bin = repo_root / "fake_bin"
            log_path = repo_root / "fake_cmds.log"
            _make_fake_bin(fake_bin, log_path)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}:{old_path}"
            try:
                first = operate_submission(
                    session,
                    OperatorSubmissionRequest(
                        repo_root=str(repo_root),
                        repo="yhmtmt/RTLGen",
                        item_id=item_id,
                        evaluator_id="cpbot",
                        session_id="s20260310t090000z",
                        host="cp-host",
                        worktree_root=str(repo_root / "tmp_submit"),
                    ),
                )
                manifest_path = repo_root / "control_plane" / "shadow_exports" / "review" / item_id / "submission_manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["run_key"] = "stale_run_key"
                manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

                second = operate_submission(
                    session,
                    OperatorSubmissionRequest(
                        repo_root=str(repo_root),
                        repo="yhmtmt/RTLGen",
                        item_id=item_id,
                        evaluator_id="cpbot",
                        session_id="s20260310t090123z",
                        host="cp-host",
                        worktree_root=str(repo_root / "tmp_submit2"),
                    ),
                )
            finally:
                os.environ["PATH"] = old_path

            assert second.submission_prepared is True
            assert second.submission_prepared_reused is False
            assert second.branch_name != first.branch_name


def test_operate_submission_blocks_non_reviewable_state_without_force() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, _run_key = _seed_l2_reviewable(session, repo_root)
            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            work_item.state = WorkItemState.RUNNING
            session.commit()

            try:
                operate_submission(
                    session,
                    OperatorSubmissionRequest(
                        repo_root=str(repo_root),
                        repo="yhmtmt/RTLGen",
                        item_id=item_id,
                    ),
                )
                assert False, "expected OperatorSubmissionError"
            except OperatorSubmissionError as exc:
                assert "state=running" in str(exc)


def test_operate_submission_blocks_missing_review_artifact_without_force() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, run_key = _seed_l2_reviewable(session, repo_root)
            run = session.query(Run).filter_by(run_key=run_key).one()
            artifact = session.query(Artifact).filter_by(run_id=run.id, kind="decision_proposal").one()
            session.delete(artifact)
            session.commit()

            try:
                operate_submission(
                    session,
                    OperatorSubmissionRequest(
                        repo_root=str(repo_root),
                        repo="yhmtmt/RTLGen",
                        item_id=item_id,
                    ),
                )
                assert False, "expected OperatorSubmissionError"
            except OperatorSubmissionError as exc:
                assert "missing decision_proposal artifact" in str(exc)


def test_operate_submission_blocks_invalid_paired_l2_review_payload_without_force() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, run_key = _seed_l2_reviewable(session, repo_root)
            run = session.query(Run).filter_by(run_key=run_key).one()
            artifact = session.query(Artifact).filter_by(run_id=run.id, kind="decision_proposal").one()
            payload = json.loads((repo_root / artifact.path).read_text(encoding="utf-8"))
            payload["evaluation_record"] = {
                **(payload.get("evaluation_record") or {}),
                "evaluation_mode": "paired_comparison",
                "comparison_role": "candidate",
                "abstraction_layer": "",
            }
            payload["proposal_assessment"] = {
                "outcome": "unavailable",
                "baseline_item_id": "",
            }
            (repo_root / artifact.path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

            try:
                operate_submission(
                    session,
                    OperatorSubmissionRequest(
                        repo_root=str(repo_root),
                        repo="yhmtmt/RTLGen",
                        item_id=item_id,
                    ),
                )
                assert False, "expected OperatorSubmissionError"
            except OperatorSubmissionError as exc:
                assert "invalid decision_proposal payload" in str(exc)


def test_operate_submission_blocks_shadow_only_outputs_without_force() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, _run_key = _seed_l2_reviewable(session, repo_root)

            try:
                operate_submission(
                    session,
                    OperatorSubmissionRequest(
                        repo_root=str(repo_root),
                        repo="yhmtmt/RTLGen",
                        item_id=item_id,
                    ),
                )
                assert False, "expected OperatorSubmissionError"
            except OperatorSubmissionError as exc:
                assert "missing canonical runs evidence outputs" in str(exc)


def test_operate_submission_force_bypasses_eligibility_gate() -> None:
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
            artifact = session.query(Artifact).filter_by(run_id=run.id, kind="decision_proposal").one()
            session.delete(artifact)
            session.commit()

            fake_bin = repo_root / "fake_bin"
            log_path = repo_root / "fake_cmds.log"
            _make_fake_bin(fake_bin, log_path)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}:{old_path}"
            try:
                result = operate_submission(
                    session,
                    OperatorSubmissionRequest(
                        repo_root=str(repo_root),
                        repo="yhmtmt/RTLGen",
                        item_id=item_id,
                        evaluator_id="cpbot",
                        session_id="s20260310t090000z",
                        host="cp-host",
                        worktree_root=str(repo_root / "tmp_submit"),
                        force=True,
                    ),
                )
            finally:
                os.environ["PATH"] = old_path

            assert result.pr_number == 321

"""Submission execution coverage."""

from __future__ import annotations

import json
import os
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
from control_plane.services.submission_bridge import prepare_submission_branch, SubmissionPrepareRequest
from control_plane.services.submission_executor import SubmissionExecuteRequest, execute_submission


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
        "item_id": "l2_exec_demo",
        "title": "Layer2 exec demo",
        "layer": "layer2",
        "flow": "openroad",
        "handoff": {
            "branch": "eval/l2_exec_demo/<session_id>",
            "pr_title": "eval: run layer2 exec demo",
            "pr_body_fields": {
                "evaluator_id": "control_plane",
                "session_id": "<session_id>",
                "host": "<host>",
                "queue_item_id": "l2_exec_demo",
            },
            "checklist": ["Commit lightweight campaign outputs only"],
        },
    }
    task_request = TaskRequest(
        request_key="l2_campaign:l2_exec_demo",
        source="test",
        requested_by="@tester",
        title="Layer2 exec demo",
        description="test submission execution",
        layer=LayerName.LAYER2,
        flow=FlowName.OPENROAD,
        priority=1,
        request_payload=payload,
        source_commit="deadbeef",
    )
    session.add(task_request)
    session.flush()

    work_item = WorkItem(
        work_item_key="l2_campaign:l2_exec_demo",
        task_request_id=task_request.id,
        item_id="l2_exec_demo",
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
        run_key="l2_exec_demo_run_1",
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
        "item_id": "l1_exec_demo",
        "title": "Layer1 exec demo",
        "layer": "layer1",
        "flow": "openroad",
        "handoff": {
            "branch": "eval/l1_exec_demo/<session_id>",
            "pr_title": "eval: run layer1 exec demo",
            "pr_body_fields": {
                "evaluator_id": "control_plane",
                "session_id": "<session_id>",
                "host": "<host>",
                "queue_item_id": "l1_exec_demo",
            },
            "checklist": ["Commit lightweight metrics outputs only"],
        },
    }
    task_request = TaskRequest(
        request_key="l1_sweep:l1_exec_demo",
        source="test",
        requested_by="@tester",
        title="Layer1 exec demo",
        description="test submission execution with canonical evidence",
        layer=LayerName.LAYER1,
        flow=FlowName.OPENROAD,
        priority=1,
        request_payload=payload,
        source_commit="deadbeef",
    )
    session.add(task_request)
    session.flush()

    work_item = WorkItem(
        work_item_key="l1_sweep:l1_exec_demo",
        task_request_id=task_request.id,
        item_id="l1_exec_demo",
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
        run_key="l1_exec_demo_run_1",
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
    state_path = fake_bin / "gh_state.json"
    _write(
        fake_bin / "git",
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        f"log={json.dumps(str(log_path))}\n"
        "with open(log, 'a', encoding='utf-8') as h:\n"
        "    h.write(json.dumps({'tool':'git','argv':sys.argv[1:]})+'\\n')\n"
        "if sys.argv[1:3] == ['push', '-u']:\n"
        "    sys.exit(0)\n"
        "sys.exit(1)\n",
    )
    _write(
        fake_bin / "gh",
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        f"log={json.dumps(str(log_path))}\n"
        f"state_path={json.dumps(str(state_path))}\n"
        "with open(log, 'a', encoding='utf-8') as h:\n"
        "    h.write(json.dumps({'tool':'gh','argv':sys.argv[1:]})+'\\n')\n"
        "argv=sys.argv[1:]\n"
        "state = {}\n"
        "if os.path.exists(state_path):\n"
        "    state = json.loads(open(state_path, 'r', encoding='utf-8').read())\n"
        "if argv[:4] == ['--repo','yhmtmt/RTLGen','pr','create']:\n"
        "    state['created'] = True\n"
        "    open(state_path, 'w', encoding='utf-8').write(json.dumps(state))\n"
        "    print('https://github.com/yhmtmt/RTLGen/pull/123')\n"
        "    sys.exit(0)\n"
        "if argv[:4] == ['--repo','yhmtmt/RTLGen','pr','view']:\n"
        "    if not state.get('created'):\n"
        "        sys.exit(1)\n"
        "    print(json.dumps({'number':123,'url':'https://github.com/yhmtmt/RTLGen/pull/123','headRefName':'eval/l2_exec_demo/s20260310t081500z','baseRefName':'master'}))\n"
        "    sys.exit(0)\n"
        "sys.exit(1)\n",
    )
    os.chmod(fake_bin / "git", 0o755)
    os.chmod(fake_bin / "gh", 0o755)


def test_execute_submission_pushes_and_reconciles() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, run_key = _seed_l2_reviewable(session, repo_root)
            prepare_submission_branch(
                session,
                SubmissionPrepareRequest(
                    repo_root=str(repo_root),
                    item_id=item_id,
                    evaluator_id="cpbot",
                    session_id="s20260310t081500z",
                    host="cp-host",
                    worktree_root=str(repo_root / "tmp_submit"),
                ),
            )

            fake_bin = repo_root / "fake_bin"
            log_path = repo_root / "fake_cmds.log"
            _make_fake_bin(fake_bin, log_path)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}:{old_path}"
            try:
                result = execute_submission(
                    session,
                    SubmissionExecuteRequest(
                        repo_root=str(repo_root),
                        repo="yhmtmt/RTLGen",
                        item_id=item_id,
                        evaluator_id="cpbot",
                        session_id="s20260310t081500z",
                        host="cp-host",
                    ),
                )
            finally:
                os.environ["PATH"] = old_path

            assert result.item_id == item_id
            assert result.run_key == run_key
            assert result.pr_number == 123
            assert result.pr_url == "https://github.com/yhmtmt/RTLGen/pull/123"

            link = session.query(GitHubLink).filter_by(pr_number=123).one()
            assert link.state == GitHubLinkState.PR_OPEN
            assert link.branch_name == "eval/l2_exec_demo/s20260310t081500z"

            work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
            assert work_item.state == WorkItemState.AWAITING_REVIEW

            artifact = session.query(Artifact).filter_by(kind="submission_execution").one()
            assert artifact.path == f"control_plane/shadow_exports/review/{item_id}/submission_execution.json"

            log_entries = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
            assert any(entry["tool"] == "git" and entry["argv"][:3] == ["push", "-u", "origin"] for entry in log_entries)
            assert any(entry["tool"] == "gh" and entry["argv"][:4] == ["--repo", "yhmtmt/RTLGen", "pr", "create"] for entry in log_entries)
            assert any(entry["tool"] == "gh" and entry["argv"][:4] == ["--repo", "yhmtmt/RTLGen", "pr", "view"] for entry in log_entries)


def test_execute_submission_reuses_existing_pr_on_rerun() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, run_key = _seed_l2_reviewable(session, repo_root)
            prepare_submission_branch(
                session,
                SubmissionPrepareRequest(
                    repo_root=str(repo_root),
                    item_id=item_id,
                    evaluator_id="cpbot",
                    session_id="s20260310t081500z",
                    host="cp-host",
                    worktree_root=str(repo_root / "tmp_submit"),
                ),
            )

            fake_bin = repo_root / "fake_bin"
            log_path = repo_root / "fake_cmds.log"
            _make_fake_bin(fake_bin, log_path)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}:{old_path}"
            try:
                execute_submission(
                    session,
                    SubmissionExecuteRequest(
                        repo_root=str(repo_root),
                        repo="yhmtmt/RTLGen",
                        item_id=item_id,
                        evaluator_id="cpbot",
                        session_id="s20260310t081500z",
                        host="cp-host",
                    ),
                )
                log_path.write_text("", encoding="utf-8")
                result = execute_submission(
                    session,
                    SubmissionExecuteRequest(
                        repo_root=str(repo_root),
                        repo="yhmtmt/RTLGen",
                        item_id=item_id,
                        evaluator_id="cpbot",
                        session_id="s20260310t081500z",
                        host="cp-host",
                    ),
                )
            finally:
                os.environ["PATH"] = old_path

            assert result.pr_number == 123
            log_entries = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            assert any(entry["tool"] == "git" and entry["argv"][:3] == ["push", "-u", "origin"] for entry in log_entries)
            assert not any(entry["tool"] == "gh" and entry["argv"][:4] == ["--repo", "yhmtmt/RTLGen", "pr", "create"] for entry in log_entries)
            assert any(entry["tool"] == "gh" and entry["argv"][:4] == ["--repo", "yhmtmt/RTLGen", "pr", "view"] for entry in log_entries)


def test_execute_submission_backfills_missing_evidence_paths_on_rerun() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, run_key = _seed_l1_reviewable(session, repo_root)
            prepared = prepare_submission_branch(
                session,
                SubmissionPrepareRequest(
                    repo_root=str(repo_root),
                    item_id=item_id,
                    evaluator_id="cpbot",
                    session_id="s20260310t081700z",
                    host="cp-host",
                    worktree_root=str(repo_root / "tmp_submit"),
                ),
            )
            manifest_path = repo_root / "control_plane" / "shadow_exports" / "review" / item_id / "submission_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.pop("evidence_paths", None)
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            fake_bin = repo_root / "fake_bin"
            log_path = repo_root / "fake_cmds.log"
            _make_fake_bin(fake_bin, log_path)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}:{old_path}"
            try:
                result = execute_submission(
                    session,
                    SubmissionExecuteRequest(
                        repo_root=str(repo_root),
                        repo="yhmtmt/RTLGen",
                        item_id=item_id,
                        evaluator_id="cpbot",
                        session_id="s20260310t081700z",
                        host="cp-host",
                    ),
                )
            finally:
                os.environ["PATH"] = old_path

            assert result.pr_number == 123
            updated_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            assert updated_manifest["evidence_paths"] == [
                "runs/designs/activations/softmax_rowwise_int8_r4_wrapper/metrics.csv",
                "runs/index.csv",
            ]


def test_execute_submission_rejects_branch_without_canonical_evidence_diff() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo_root = Path(td) / "repo"
        repo_root.mkdir()
        _init_repo(repo_root)

        engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        create_all(engine)
        with Session(engine) as session:
            item_id, _run_key = _seed_l1_reviewable(session, repo_root)
            prepare_submission_branch(
                session,
                SubmissionPrepareRequest(
                    repo_root=str(repo_root),
                    item_id=item_id,
                    evaluator_id="cpbot",
                    session_id="s20260312t103000z",
                    host="cp-host",
                    worktree_root=str(repo_root / "tmp_submit"),
                ),
            )
            manifest_path = repo_root / "control_plane" / "shadow_exports" / "review" / item_id / "submission_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            # Simulate a reused bad branch by making base/master contain the same canonical evidence.
            _git(
                repo_root,
                "add",
                "runs/designs/activations/softmax_rowwise_int8_r4_wrapper/metrics.csv",
                "runs/index.csv",
            )
            subprocess.run(
                ["git", "-C", str(repo_root), "commit", "-m", "seed canonical evidence into base"],
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

            fake_bin = repo_root / "fake_bin"
            log_path = repo_root / "fake_cmds.log"
            _make_fake_bin(fake_bin, log_path)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}:{old_path}"
            try:
                try:
                    execute_submission(
                        session,
                        SubmissionExecuteRequest(
                            repo_root=str(repo_root),
                            repo="yhmtmt/RTLGen",
                            item_id=item_id,
                            evaluator_id="cpbot",
                            session_id="s20260312t103000z",
                            host="cp-host",
                        ),
                    )
                except SubmissionExecuteError as exc:
                    assert "no canonical runs evidence diff" in str(exc)
                else:
                    raise AssertionError("expected SubmissionExecuteError")
            finally:
                os.environ["PATH"] = old_path

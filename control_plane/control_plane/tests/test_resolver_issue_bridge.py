"""Tests for resolver issue formatting and bridge helpers."""

from __future__ import annotations

import json
from subprocess import CalledProcessError, CompletedProcess
from unittest.mock import patch

from control_plane.models.resolver_cases import ResolverCase
from control_plane.services.resolver_issue_bridge import (
    ResolverIssueBridgeCommandError,
    build_issue_body,
    fetch_issue,
    list_open_resolver_issues,
    open_issue_for_case,
    parse_resolver_case_block,
    parse_resolver_diagnosis_block,
)


def _case() -> ResolverCase:
    return ResolverCase(
        id="case-1",
        fingerprint="orphaned_running_item:command_progress",
        failure_class="orphaned_running_item",
        owner="eval",
        status="open",
        severity="high",
        latest_item_id="item-1",
        latest_run_key="run-1",
        machine_key="eval-1",
        source_commit="deadbeef",
        evidence_json={
            "item_id": "item-1",
            "run_key": "run-1",
            "machine_key": "eval-1",
            "latest_event_type": "command_progress",
        },
        resolution_json={},
    )


def test_build_issue_body_includes_machine_readable_header() -> None:
    body = build_issue_body(_case())
    assert "<!-- resolver-case" in body
    assert "fingerprint: orphaned_running_item:command_progress" in body
    assert "- latest_event_type: `command_progress`" in body
    assert "<!-- resolver-diagnosis" in body
    assert "recommended_action: <expire_stale_leases|retry_submission|none>" in body


def test_open_issue_for_case_uses_gh_api() -> None:
    with patch("control_plane.services.resolver_issue_bridge.subprocess.run") as run_mock:
        run_mock.return_value = CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps({"number": 175, "html_url": "https://github.com/yhmtmt/RTLGen/issues/175"}),
            stderr="",
        )
        result = open_issue_for_case("yhmtmt/RTLGen", _case())

    assert result.issue_number == 175
    assert result.issue_url.endswith("/175")
    command = run_mock.call_args.args[0]
    assert command[:3] == ["gh", "api", "repos/yhmtmt/RTLGen/issues"]


def test_parse_resolver_case_block_reads_owner_and_case_id() -> None:
    body = """<!-- resolver-case
case_id: case-1
owner: eval
machine_key: eval-1
-->

Symptom:
- orphaned_running_item
"""
    payload = parse_resolver_case_block(body)
    assert payload["case_id"] == "case-1"
    assert payload["owner"] == "eval"
    assert payload["machine_key"] == "eval-1"


def test_parse_resolver_diagnosis_block_reads_recommended_action() -> None:
    body = """Resolver result

<!-- resolver-diagnosis
verdict: worker died during finalize
failure_point: complete_run
recommended_action: expire_stale_leases
-->
"""
    payload = parse_resolver_diagnosis_block(body)
    assert payload["verdict"] == "worker died during finalize"
    assert payload["failure_point"] == "complete_run"
    assert payload["recommended_action"] == "expire_stale_leases"


def test_fetch_issue_reads_state() -> None:
    issue_payload = {
        "number": 184,
        "title": "Resolver: orphaned_running_item [item-1]",
        "body": "<!-- resolver-case\ncase_id: case-1\nowner: eval\n-->",
        "state": "closed",
        "html_url": "https://github.com/yhmtmt/RTLGen/issues/184",
        "updated_at": "2026-04-13T12:11:33Z",
    }
    with patch("control_plane.services.resolver_issue_bridge.subprocess.run") as run_mock:
        run_mock.return_value = CompletedProcess(args=[], returncode=0, stdout=json.dumps(issue_payload), stderr="")
        issue = fetch_issue("yhmtmt/RTLGen", 184)

    assert issue.issue_number == 184
    assert issue.state == "closed"
    assert issue.case_metadata["owner"] == "eval"


def test_list_open_resolver_issues_filters_owner_and_pull_requests() -> None:
    issue_list = [
        {
            "number": 175,
            "title": "Resolver: orphaned_running_item [item-1]",
            "body": "<!-- resolver-case\ncase_id: case-1\nowner: eval\nmachine_key: eval-1\n-->",
            "state": "open",
            "html_url": "https://github.com/yhmtmt/RTLGen/issues/175",
            "updated_at": "2026-04-10T12:00:00Z",
        },
        {
            "number": 176,
            "title": "Resolver: orphaned_running_item [item-2]",
            "body": "<!-- resolver-case\ncase_id: case-2\nowner: dev\n-->",
            "state": "open",
            "html_url": "https://github.com/yhmtmt/RTLGen/issues/176",
            "updated_at": "2026-04-10T12:00:00Z",
        },
        {
            "number": 177,
            "title": "Resolver: orphaned_running_item [pr]",
            "body": "<!-- resolver-case\ncase_id: case-3\nowner: eval\n-->",
            "state": "open",
            "html_url": "https://github.com/yhmtmt/RTLGen/issues/177",
            "updated_at": "2026-04-10T12:00:00Z",
            "pull_request": {"url": "https://api.github.com/repos/yhmtmt/RTLGen/pulls/177"},
        },
    ]
    comments = [{"id": 1, "body": "diag", "user": {"login": "eval-bot"}, "created_at": "2026-04-10T12:05:00Z", "updated_at": "2026-04-10T12:05:00Z"}]

    with patch("control_plane.services.resolver_issue_bridge.subprocess.run") as run_mock:
        run_mock.side_effect = [
            CompletedProcess(args=[], returncode=0, stdout=json.dumps(issue_list), stderr=""),
            CompletedProcess(args=[], returncode=0, stdout=json.dumps(comments), stderr=""),
        ]
        issues = list_open_resolver_issues("yhmtmt/RTLGen", owner="eval", include_comments=True)

    assert len(issues) == 1
    assert issues[0].issue_number == 175
    assert issues[0].case_metadata["owner"] == "eval"
    assert len(issues[0].comments) == 1


def test_fetch_issue_wraps_gh_command_failure() -> None:
    with patch("control_plane.services.resolver_issue_bridge.subprocess.run") as run_mock:
        run_mock.side_effect = CalledProcessError(1, ["gh", "api"], stderr="network down")
        try:
            fetch_issue("yhmtmt/RTLGen", 184)
        except ResolverIssueBridgeCommandError as exc:
            assert "gh api failed" in str(exc)
            assert "network down" in str(exc)
        else:
            raise AssertionError("expected ResolverIssueBridgeCommandError")

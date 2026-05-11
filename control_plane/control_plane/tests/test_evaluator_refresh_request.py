"""Tests for evaluator refresh GitHub issue requests."""

from __future__ import annotations

import json
from subprocess import CompletedProcess
from unittest.mock import patch

from control_plane.services.evaluator_refresh_request import (
    EvaluatorRefreshRequest,
    build_refresh_body,
    request_evaluator_refresh,
)


def test_build_refresh_body_includes_ack_block() -> None:
    body = build_refresh_body(
        EvaluatorRefreshRequest(
            repo="yhmtmt/RTLGen",
            target_commit="abcdef1234567890",
            reason="merged PR #450",
            evaluator="remote-fast",
        )
    )

    assert "target_commit: abcdef1234567890" in body
    assert "evaluator: remote-fast" in body
    assert "evaluator-refresh-ack" in body
    assert "Restart evaluator-side daemons" in body


def test_request_evaluator_refresh_creates_issue_when_none_open() -> None:
    calls = []

    def fake_run(argv, check, capture_output, text):
        calls.append(argv)
        if argv[2].endswith("/issues?state=open&per_page=100"):
            return CompletedProcess(argv, 0, stdout="[]", stderr="")
        return CompletedProcess(
            argv,
            0,
            stdout=json.dumps({"number": 451, "html_url": "https://github.com/yhmtmt/RTLGen/issues/451"}),
            stderr="",
        )

    with patch("control_plane.services.evaluator_refresh_request.subprocess.run", side_effect=fake_run):
        result = request_evaluator_refresh(
            EvaluatorRefreshRequest(repo="yhmtmt/RTLGen", target_commit="abcdef123456")
        )

    assert result.action == "created"
    assert result.issue_number == 451
    assert calls[-1][:5] == ["gh", "api", "repos/yhmtmt/RTLGen/issues", "--method", "POST"]


def test_request_evaluator_refresh_comments_existing_issue() -> None:
    issue = {
        "number": 440,
        "title": "Evaluator refresh: old",
        "body": "<!-- evaluator-refresh\ntarget_commit: old\n-->",
        "html_url": "https://github.com/yhmtmt/RTLGen/issues/440",
    }
    calls = []

    def fake_run(argv, check, capture_output, text):
        calls.append(argv)
        if argv[2].endswith("/issues?state=open&per_page=100"):
            return CompletedProcess(argv, 0, stdout=json.dumps([issue]), stderr="")
        return CompletedProcess(argv, 0, stdout=json.dumps({"body": "comment body"}), stderr="")

    with patch("control_plane.services.evaluator_refresh_request.subprocess.run", side_effect=fake_run):
        result = request_evaluator_refresh(
            EvaluatorRefreshRequest(repo="yhmtmt/RTLGen", target_commit="newcommit")
        )

    assert result.action == "commented"
    assert result.issue_number == 440
    assert calls[-1][2] == "repos/yhmtmt/RTLGen/issues/440/comments"

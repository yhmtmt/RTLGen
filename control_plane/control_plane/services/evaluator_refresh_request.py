"""Request remote evaluator source refresh and daemon restart through GitHub."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import subprocess
from typing import Any


class EvaluatorRefreshRequestError(RuntimeError):
    pass


@dataclass(frozen=True)
class EvaluatorRefreshRequest:
    repo: str
    target_commit: str
    reason: str = "control-plane source changed"
    evaluator: str = "remote evaluator"
    dry_run: bool = False


@dataclass(frozen=True)
class EvaluatorRefreshResult:
    repo: str
    target_commit: str
    issue_number: int | None
    issue_url: str | None
    action: str
    dry_run: bool
    body: str


_REFRESH_BLOCK_RE = re.compile(r"<!--\s*evaluator-refresh\n(.*?)-->", re.DOTALL)


def _gh_api_json(path: str, *, method: str = "GET", fields: dict[str, str] | None = None) -> Any:
    command = ["gh", "api", path]
    if method != "GET":
        command.extend(["--method", method])
    for key, value in (fields or {}).items():
        command.extend(["-f", f"{key}={value}"])
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        stderr = str(exc.stderr or "").strip()
        raise EvaluatorRefreshRequestError(f"gh api failed for {path}: {stderr or exc}") from exc
    except OSError as exc:
        raise EvaluatorRefreshRequestError(f"gh api unavailable for {path}: {exc}") from exc
    return json.loads(result.stdout)


def _gh_api(path: str, *, method: str = "GET", fields: dict[str, str] | None = None) -> dict[str, Any]:
    payload = _gh_api_json(path, method=method, fields=fields)
    if not isinstance(payload, dict):
        raise EvaluatorRefreshRequestError(f"unexpected gh api payload for {path}")
    return payload


def _parse_refresh_block(text: str) -> dict[str, str]:
    match = _REFRESH_BLOCK_RE.search(text or "")
    if match is None:
        return {}
    parsed: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def _find_open_refresh_issue(repo: str) -> dict[str, Any] | None:
    payload = _gh_api_json(f"repos/{repo}/issues?state=open&per_page=100")
    if not isinstance(payload, list):
        raise EvaluatorRefreshRequestError(f"unexpected gh api issues payload for {repo}")
    for row in payload:
        if not isinstance(row, dict):
            continue
        if row.get("pull_request"):
            continue
        title = str(row.get("title") or "")
        body = str(row.get("body") or "")
        if title.startswith("Evaluator refresh:") or _parse_refresh_block(body):
            return row
    return None


def build_refresh_body(request: EvaluatorRefreshRequest) -> str:
    return "\n".join(
        [
            "<!-- evaluator-refresh",
            f"target_commit: {request.target_commit}",
            f"evaluator: {request.evaluator}",
            f"reason: {request.reason}",
            "-->",
            "",
            "Please refresh the evaluator environment to the requested RTLGen commit and restart daemons.",
            "",
            "Requested target:",
            f"- repository: `{request.repo}`",
            f"- target_commit: `{request.target_commit}`",
            f"- evaluator: `{request.evaluator}`",
            f"- reason: {request.reason}",
            "",
            "Expected evaluator procedure:",
            "1. Fetch `origin/master` and update the evaluator worktree to the target commit.",
            "2. Refresh Python dependencies if repository dependency files changed.",
            "3. Restart evaluator-side daemons: worker daemon and eval resolver; restart the API daemon if it runs on the evaluator host.",
            "4. Confirm daemon status and queue readiness.",
            "",
            "Please reply with:",
            "```md",
            "<!-- evaluator-refresh-ack",
            f"target_commit: {request.target_commit}",
            "status: updated|blocked",
            "daemons_restarted: true|false",
            "notes: <short note>",
            "-->",
            "```",
            "",
        ]
    )


def request_evaluator_refresh(request: EvaluatorRefreshRequest) -> EvaluatorRefreshResult:
    body = build_refresh_body(request)
    existing = _find_open_refresh_issue(request.repo)
    if request.dry_run:
        return EvaluatorRefreshResult(
            repo=request.repo,
            target_commit=request.target_commit,
            issue_number=int(existing["number"]) if existing else None,
            issue_url=str(existing.get("html_url") or "") or None if existing else None,
            action="would_comment" if existing else "would_create",
            dry_run=True,
            body=body,
        )

    if existing is not None:
        issue_number = int(existing["number"])
        payload = _gh_api(
            f"repos/{request.repo}/issues/{issue_number}/comments",
            method="POST",
            fields={"body": body},
        )
        return EvaluatorRefreshResult(
            repo=request.repo,
            target_commit=request.target_commit,
            issue_number=issue_number,
            issue_url=str(existing.get("html_url") or "") or None,
            action="commented",
            dry_run=False,
            body=str(payload.get("body") or body),
        )

    payload = _gh_api(
        f"repos/{request.repo}/issues",
        method="POST",
        fields={
            "title": f"Evaluator refresh: {request.target_commit[:12]}",
            "body": body,
        },
    )
    return EvaluatorRefreshResult(
        repo=request.repo,
        target_commit=request.target_commit,
        issue_number=int(payload["number"]),
        issue_url=str(payload.get("html_url") or "") or None,
        action="created",
        dry_run=False,
        body=body,
    )

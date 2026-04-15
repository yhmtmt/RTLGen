"""GitHub issue bridge for resolver cases."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import subprocess
from typing import Any

from control_plane.models.resolver_cases import ResolverCase


class ResolverIssueBridgeError(RuntimeError):
    pass


class ResolverIssueBridgeCommandError(ResolverIssueBridgeError):
    pass


@dataclass(frozen=True)
class ResolverIssueCreateResult:
    issue_number: int
    issue_url: str


@dataclass(frozen=True)
class ResolverIssueComment:
    comment_id: int
    body: str
    author: str | None
    created_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class ResolverRemoteIssue:
    issue_number: int
    title: str
    body: str
    state: str
    issue_url: str | None
    updated_at: str | None
    case_metadata: dict[str, str]
    comments: tuple[ResolverIssueComment, ...] = ()


_RESOLVER_BLOCK_RE = re.compile(r"<!--\s*resolver-case\n(.*?)-->", re.DOTALL)
_RESOLVER_DIAGNOSIS_BLOCK_RE = re.compile(r"<!--\s*resolver-diagnosis\n(.*?)-->", re.DOTALL)


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
        raise ResolverIssueBridgeCommandError(f"gh api failed for {path}: {stderr or exc}") from exc
    except OSError as exc:
        raise ResolverIssueBridgeCommandError(f"gh api unavailable for {path}: {exc}") from exc
    return json.loads(result.stdout)


def _gh_api(path: str, *, method: str = "GET", fields: dict[str, str] | None = None) -> dict[str, Any]:
    payload = _gh_api_json(path, method=method, fields=fields)
    if not isinstance(payload, dict):
        raise ResolverIssueBridgeError(f"unexpected gh api payload for {path}")
    return payload


def _parse_machine_readable_block(text: str, pattern: re.Pattern[str]) -> dict[str, str]:
    match = pattern.search(text or "")
    if match is None:
        return {}
    payload: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        payload[key.strip()] = value.strip()
    return payload


def parse_resolver_case_block(text: str) -> dict[str, str]:
    return _parse_machine_readable_block(text, _RESOLVER_BLOCK_RE)


def parse_resolver_diagnosis_block(text: str) -> dict[str, str]:
    return _parse_machine_readable_block(text, _RESOLVER_DIAGNOSIS_BLOCK_RE)


def build_issue_title(case: ResolverCase) -> str:
    item_id = case.latest_item_id or case.first_item_id or "unknown-item"
    return f"Resolver: {case.failure_class} [{item_id}]"


def build_issue_body(case: ResolverCase) -> str:
    evidence = dict(case.evidence_json or {})
    lines = [
        "<!-- resolver-case",
        f"case_id: {case.id}",
        f"fingerprint: {case.fingerprint}",
        f"owner: {case.owner}",
        f"item_id: {case.latest_item_id or case.first_item_id or ''}",
        f"run_key: {case.latest_run_key or case.first_run_key or ''}",
        f"machine_key: {case.machine_key or ''}",
        f"source_commit: {case.source_commit or ''}",
        "-->",
        "",
        "Symptom:",
        f"- {case.failure_class}",
        "",
        "Current DB evidence:",
    ]
    for key in sorted(evidence):
        lines.append(f"- {key}: `{evidence[key]}`")
    lines.extend(
        [
            "",
            "Requested evaluator diagnosis:",
            "1. inspect worker/service logs around the latest event time",
            "2. inspect the command/log path named in the latest run events",
            "3. reply with the concrete failure point and recommended next action using a resolver-diagnosis block",
            "",
            "Reply format:",
            "```md",
            "<!-- resolver-diagnosis",
            "verdict: <short diagnosis>",
            "failure_point: <code path or command>",
            "recommended_action: <expire_stale_leases|retry_submission|none>",
            "force: <true|false>",
            "-->",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def build_issue_comment(case: ResolverCase, *, reason: str) -> str:
    return "\n".join(
        [
            "Resolver update:",
            f"- case_id: `{case.id}`",
            f"- status: `{case.status}`",
            f"- reason: `{reason}`",
        ]
    )


def open_issue_for_case(repo: str, case: ResolverCase) -> ResolverIssueCreateResult:
    payload = _gh_api(
        f"repos/{repo}/issues",
        method="POST",
        fields={
            "title": build_issue_title(case),
            "body": build_issue_body(case),
        },
    )
    return ResolverIssueCreateResult(issue_number=int(payload["number"]), issue_url=str(payload["html_url"]))


def comment_issue_for_case(repo: str, issue_number: int, *, body: str) -> dict[str, Any]:
    return _gh_api(
        f"repos/{repo}/issues/{issue_number}/comments",
        method="POST",
        fields={"body": body},
    )


def close_issue_for_case(repo: str, issue_number: int) -> dict[str, Any]:
    return _gh_api(
        f"repos/{repo}/issues/{issue_number}",
        method="PATCH",
        fields={"state": "closed"},
    )


def fetch_issue(repo: str, issue_number: int) -> ResolverRemoteIssue:
    payload = _gh_api(f"repos/{repo}/issues/{issue_number}")
    title = str(payload.get("title") or "")
    body = str(payload.get("body") or "")
    return ResolverRemoteIssue(
        issue_number=int(payload.get("number") or issue_number),
        title=title,
        body=body,
        state=str(payload.get("state") or ""),
        issue_url=str(payload.get("html_url") or "") or None,
        updated_at=str(payload.get("updated_at") or "") or None,
        case_metadata=parse_resolver_case_block(body),
        comments=(),
    )


def fetch_issue_comments(repo: str, issue_number: int) -> tuple[ResolverIssueComment, ...]:
    payload = _gh_api_json(f"repos/{repo}/issues/{issue_number}/comments")
    if not isinstance(payload, list):
        raise ResolverIssueBridgeError(f"unexpected gh api comments payload for issue {issue_number}")
    comments: list[ResolverIssueComment] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        comments.append(
            ResolverIssueComment(
                comment_id=int(row.get("id") or 0),
                body=str(row.get("body") or ""),
                author=((row.get("user") or {}).get("login") if isinstance(row.get("user"), dict) else None),
                created_at=str(row.get("created_at") or "") or None,
                updated_at=str(row.get("updated_at") or "") or None,
            )
        )
    return tuple(comments)


def list_open_resolver_issues(
    repo: str,
    *,
    owner: str | None = None,
    include_comments: bool = False,
) -> tuple[ResolverRemoteIssue, ...]:
    payload = _gh_api_json(f"repos/{repo}/issues?state=open&per_page=100")
    if not isinstance(payload, list):
        raise ResolverIssueBridgeError(f"unexpected gh api issues payload for {repo}")
    issues: list[ResolverRemoteIssue] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        if row.get("pull_request"):
            continue
        title = str(row.get("title") or "")
        body = str(row.get("body") or "")
        if not title.startswith("Resolver:") and "resolver-case" not in body:
            continue
        case_metadata = parse_resolver_case_block(body)
        case_owner = case_metadata.get("owner")
        if owner is not None and case_owner not in {owner, "joint"}:
            continue
        issue_number = int(row.get("number") or 0)
        comments = fetch_issue_comments(repo, issue_number) if include_comments else ()
        issues.append(
            ResolverRemoteIssue(
                issue_number=issue_number,
                title=title,
                body=body,
                state=str(row.get("state") or ""),
                issue_url=str(row.get("html_url") or "") or None,
                updated_at=str(row.get("updated_at") or "") or None,
                case_metadata=case_metadata,
                comments=comments,
            )
        )
    return tuple(issues)

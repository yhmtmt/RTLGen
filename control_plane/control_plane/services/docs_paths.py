"""Helpers for resolving canonical and legacy docs paths during migration."""

from __future__ import annotations

from pathlib import Path
import json


def _resolve_path(repo_root: Path, path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return repo_root / path


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def proposal_dir_candidates(repo_root: Path, proposal_path: str | None = None, proposal_id: str | None = None) -> list[Path]:
    candidates: list[Path] = []
    proposal_path_text = str(proposal_path or "").strip()
    proposal_id_text = str(proposal_id or "").strip()

    if proposal_path_text:
        candidates.extend(_proposal_path_candidates(repo_root, proposal_path_text))

    if proposal_id_text:
        candidates.append(repo_root / 'docs' / 'proposals' / proposal_id_text)
        candidates.append(repo_root / 'docs' / 'developer_loop' / proposal_id_text)

    return _dedupe_paths(candidates)


def _proposal_path_candidates(repo_root: Path, proposal_path_text: str) -> list[Path]:
    candidates: list[Path] = []
    resolved = _resolve_path(repo_root, proposal_path_text)
    if resolved.name == 'proposal.json':
        candidates.append(resolved.parent)
    else:
        candidates.append(resolved)

    rel_text = proposal_path_text
    if rel_text.startswith('docs/developer_loop/'):
        mapped = rel_text.replace('docs/developer_loop/', 'docs/proposals/', 1)
        mapped_path = _resolve_path(repo_root, mapped)
        candidates.append(mapped_path.parent if mapped_path.name == 'proposal.json' else mapped_path)
    elif rel_text.startswith('docs/proposals/'):
        mapped = rel_text.replace('docs/proposals/', 'docs/developer_loop/', 1)
        mapped_path = _resolve_path(repo_root, mapped)
        candidates.append(mapped_path.parent if mapped_path.name == 'proposal.json' else mapped_path)
    return _dedupe_paths(candidates)


def resolve_proposal_dir(repo_root: Path, proposal_path: str | None = None, proposal_id: str | None = None) -> Path | None:
    for candidate in proposal_dir_candidates(repo_root, proposal_path=proposal_path, proposal_id=proposal_id):
        proposal_dir = candidate
        if proposal_dir.is_file() and proposal_dir.name == 'proposal.json':
            proposal_dir = proposal_dir.parent
        if proposal_dir.exists():
            return proposal_dir.resolve()
    for candidate in proposal_dir_candidates(repo_root, proposal_path=proposal_path, proposal_id=proposal_id):
        if candidate.name == 'proposal.json':
            return candidate.parent
        return candidate
    return None


def resolve_proposal_file(repo_root: Path, proposal_path: str | None = None, proposal_id: str | None = None) -> Path | None:
    proposal_path_text = str(proposal_path or "").strip()
    if proposal_path_text:
        candidates = _proposal_path_candidates(repo_root, proposal_path_text)
    else:
        candidates = proposal_dir_candidates(repo_root, proposal_id=proposal_id)

    for candidate in candidates:
        proposal_file = candidate if candidate.name == 'proposal.json' else candidate / 'proposal.json'
        if proposal_file.exists():
            return proposal_file.resolve()
    if proposal_path_text:
        return None
    proposal_dir = resolve_proposal_dir(repo_root, proposal_path=proposal_path, proposal_id=proposal_id)
    if proposal_dir is None:
        return None
    return proposal_dir / 'proposal.json'


def proposal_placeholder_reason(proposal_json: Path) -> str | None:
    try:
        payload = json.loads(proposal_json.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None

    title = str(payload.get("title", "")).strip()
    hypothesis = str(payload.get("hypothesis", "")).strip()
    direct_comparison = payload.get("direct_comparison")
    primary_question = ""
    include_values: list[str] = []
    exclude_values: list[str] = []
    if isinstance(direct_comparison, dict):
        primary_question = str(direct_comparison.get("primary_question", "")).strip()
        include_values = [str(value).strip() for value in direct_comparison.get("include", []) if str(value).strip()]
        exclude_values = [str(value).strip() for value in direct_comparison.get("exclude", []) if str(value).strip()]
    expected_benefit = [str(value).strip() for value in payload.get("expected_benefit", []) if str(value).strip()]
    risks = [str(value).strip() for value in payload.get("risks", []) if str(value).strip()]

    placeholders = {
        title == "Example proposal title",
        hypothesis == "Replace this with a bounded engineering hypothesis.",
        primary_question == "What focused comparison directly tests this proposal?",
        any(value.startswith("describe ") for value in include_values),
        any(value.startswith("describe ") for value in exclude_values),
        any(value.startswith("describe ") for value in expected_benefit),
        any(value.startswith("describe ") for value in risks),
    }
    if any(placeholders):
        return "developer_loop proposal is still a template placeholder"
    return None


def canonicalize_proposal_path(repo_root: Path, proposal_path: str | None = None, proposal_id: str | None = None) -> str | None:
    proposal_path_text = str(proposal_path or "").strip()
    wants_file = proposal_path_text.endswith("proposal.json")
    proposal_file = resolve_proposal_file(repo_root, proposal_path=proposal_path, proposal_id=proposal_id)
    if proposal_file is not None:
        target = proposal_file if wants_file else proposal_file.parent
        try:
            return str(target.resolve().relative_to(repo_root.resolve()))
        except ValueError:
            return str(target)
    proposal_dir = resolve_proposal_dir(repo_root, proposal_path=proposal_path, proposal_id=proposal_id)
    if proposal_dir is not None:
        target = proposal_dir / "proposal.json" if wants_file else proposal_dir
        try:
            return str(target.resolve().relative_to(repo_root.resolve()))
        except FileNotFoundError:
            try:
                return str(target.relative_to(repo_root.resolve()))
            except ValueError:
                return str(target)
        except ValueError:
            return str(target)
    if proposal_path_text:
        return proposal_path_text
    return None

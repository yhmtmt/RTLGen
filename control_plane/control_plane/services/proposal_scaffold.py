"""Helpers for ensuring proposal directories contain the full expected scaffold."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from control_plane.clock import utcnow


class ProposalScaffoldError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ProposalScaffoldError(f"expected JSON object at: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _is_placeholder_requested_item(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    item_id = str(value.get("item_id", "")).strip()
    candidate_id = str(value.get("candidate_id", "")).strip()
    objective = str(value.get("objective", "")).strip().lower()
    return (
        item_id == "example_item_id"
        or candidate_id == "cand_example_v1_r1"
        or objective == "balanced"
    )


_DEFAULT_TEMPLATE_FILES = {
    "README.md": "# Proposal Workspace\n\nSeeded automatically by the control plane.\n",
    "design_brief.md": "# Design Brief\n\nFill in the design brief.\n",
    "implementation_summary.md": "# Implementation Summary\n\nFill in the implementation summary.\n",
    "analysis_report.md": "# Analysis Report\n\nPending analysis.\n",
    "evaluation_gate.md": "# Evaluation Gate\n\nPending evaluation.\n",
    "promotion_gate.md": "# Promotion Gate\n\nPending promotion review.\n",
    "quality_gate.md": "# Quality Gate\n\nPending quality review.\n",
}


def _seed_builtin_template_files(*, proposal_dir: Path) -> None:
    for name, content in _DEFAULT_TEMPLATE_FILES.items():
        target = proposal_dir / name
        if not target.exists():
            target.write_text(content, encoding="utf-8")


def _seed_builtin_json_files(*, proposal_dir: Path, proposal_id: str, source_commit: str) -> None:
    builtin_json = {
        "proposal.json": {
            "proposal_id": proposal_id,
            "created_utc": utcnow().isoformat().replace("+00:00", "Z"),
            "created_by": "control_plane",
            "layer": "layer2",
            "kind": "architecture",
            "title": proposal_id,
            "hypothesis": "Replace this with a bounded engineering hypothesis.",
            "direct_comparison": {"primary_question": "", "include": [], "exclude": [], "follow_on_broad_sweep": []},
            "expected_benefit": [],
            "risks": [],
            "needs_mapper_change": False,
            "required_evaluations": [],
            "baseline_refs": [],
            "knowledge_refs": [],
        },
        "evaluation_requests.json": {
            "proposal_id": proposal_id,
            "source_commit": source_commit,
            "requested_items": [],
        },
        "promotion_decision.json": {
            "proposal_id": proposal_id,
            "candidate_id": "",
            "decision": "iterate",
            "reason": "Proposal seeded; awaiting merged evaluation evidence.",
            "evidence_refs": [],
            "next_action": "run first item",
            "requires_human_approval": False,
        },
        "promotion_result.json": {
            "proposal_id": proposal_id,
            "decision": "pending",
            "pr_number": None,
            "merge_commit": "",
            "merged_utc": "",
        },
    }
    for name, payload in builtin_json.items():
        target = proposal_dir / name
        if not target.exists():
            _write_json(target, payload)


def ensure_proposal_scaffold(
    *,
    repo_root: Path,
    proposal_dir: Path,
    proposal_id: str,
    source_commit: str,
    layer: str | None = None,
    kind: str | None = None,
) -> None:
    template_dir = repo_root / "docs" / "proposals" / "_template"

    proposal_dir.mkdir(parents=True, exist_ok=True)
    if template_dir.exists():
        for template_path in sorted(p for p in template_dir.rglob("*") if p.is_file()):
            rel = template_path.relative_to(template_dir)
            target = proposal_dir / rel
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(template_path, target)
    _seed_builtin_template_files(proposal_dir=proposal_dir)
    _seed_builtin_json_files(proposal_dir=proposal_dir, proposal_id=proposal_id, source_commit=source_commit)

    created_utc = utcnow().isoformat().replace("+00:00", "Z")

    proposal_path = proposal_dir / "proposal.json"
    proposal = _load_json(proposal_path)
    proposal["proposal_id"] = proposal_id
    if not str(proposal.get("created_utc", "")).strip() or str(proposal.get("created_utc")) == "2026-03-15T00:00:00Z":
        proposal["created_utc"] = created_utc
    if layer and (not str(proposal.get("layer", "")).strip() or str(proposal.get("layer")) == "layer2"):
        proposal["layer"] = layer
    if kind and (not str(proposal.get("kind", "")).strip() or str(proposal.get("kind")) == "architecture"):
        proposal["kind"] = kind
    _write_json(proposal_path, proposal)

    evaluation_requests_path = proposal_dir / "evaluation_requests.json"
    evaluation_requests = _load_json(evaluation_requests_path)
    evaluation_requests["proposal_id"] = proposal_id
    evaluation_requests["source_commit"] = source_commit
    requested_items = evaluation_requests.get("requested_items")
    if not isinstance(requested_items, list):
        requested_items = []
    requested_items = [entry for entry in requested_items if not _is_placeholder_requested_item(entry)]
    evaluation_requests["requested_items"] = requested_items
    _write_json(evaluation_requests_path, evaluation_requests)

    promotion_decision_path = proposal_dir / "promotion_decision.json"
    promotion_decision = _load_json(promotion_decision_path)
    promotion_decision["proposal_id"] = proposal_id
    if str(promotion_decision.get("candidate_id", "")).strip() == "cand_example_v1_r1":
        promotion_decision["candidate_id"] = ""
    if str(promotion_decision.get("decision", "")).strip() not in {"pending", "iterate", "promote", "reject"}:
        promotion_decision["decision"] = "iterate"
    _write_json(promotion_decision_path, promotion_decision)

    promotion_result_path = proposal_dir / "promotion_result.json"
    promotion_result = _load_json(promotion_result_path)
    promotion_result["proposal_id"] = proposal_id
    decision = str(promotion_result.get("decision", "")).strip() or "pending"
    if decision not in {"pending", "iterate", "promote", "reject", "promoted"}:
        decision = "pending"
    promotion_result["decision"] = decision
    promotion_result.setdefault("pr_number", None)
    promotion_result.setdefault("merge_commit", "")
    promotion_result.setdefault("merged_utc", "")
    _write_json(promotion_result_path, promotion_result)

"""Artifact transport policy for remote worker evidence."""

from __future__ import annotations

from pathlib import PurePosixPath

_RUNS_DENY_SEGMENTS = {"/artifacts/", "/work/", "/comparisons/"}

_ALLOWED_RUNS_FILES = {
    "runs/index.csv",
}

_ALLOWED_RUNS_SUFFIXES = {
    "/metrics.csv",
    "/macro_manifest.json",
    "/campaign.json",
    "/report.md",
    "/results.csv",
    "/summary.csv",
    "/pareto.csv",
    "/best_point.json",
    "/objective_sweep.csv",
    "/objective_sweep.md",
}


def _normalize_rel_path(path_text: str) -> str:
    path = PurePosixPath(path_text.strip())
    if path.is_absolute():
        return ""
    normalized = path.as_posix()
    if normalized.startswith("../") or normalized == "..":
        return ""
    return normalized


def is_transportable_expected_output(path_text: str) -> bool:
    rel_path = _normalize_rel_path(path_text)
    if not rel_path:
        return False
    if rel_path.startswith("control_plane/shadow_exports/"):
        return False
    if not rel_path.startswith("runs/"):
        return False
    if rel_path.startswith("runs/model_cache/"):
        return False
    if any(segment in rel_path for segment in _RUNS_DENY_SEGMENTS):
        return False
    if rel_path in _ALLOWED_RUNS_FILES:
        return True
    if rel_path.startswith("runs/campaigns/"):
        name = PurePosixPath(rel_path).name
        if name == "campaign.json" or (name.startswith("campaign__") and name.endswith(".json")):
            return True
    return any(rel_path.endswith(suffix) for suffix in _ALLOWED_RUNS_SUFFIXES)

"""Artifact collection helpers for the internal worker loop."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from control_plane.workers.command_runner import CommandResult


@dataclass(frozen=True)
class StagedArtifact:
    kind: str
    storage_mode: str
    path: str
    sha256: str | None
    metadata: dict[str, object]


@dataclass(frozen=True)
class QueueResultPayload:
    status: str
    metrics_rows: list[str]
    notes: list[str]


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path.resolve())


def collect_expected_output_artifacts(*, repo_root: str, expected_outputs: list[str]) -> list[StagedArtifact]:
    repo_path = Path(repo_root).resolve()
    artifacts: list[StagedArtifact] = []
    for output in expected_outputs:
        path = (repo_path / output).resolve()
        if not path.exists() or not path.is_file():
            continue
        artifacts.append(
            StagedArtifact(
                kind="expected_output",
                storage_mode="repo",
                path=_relative_path(path, repo_path),
                sha256=_sha256_file(path),
                metadata={
                    "size_bytes": path.stat().st_size,
                },
            )
        )
    return artifacts


def collect_log_artifacts(*, repo_root: str, command_results: list[CommandResult]) -> list[StagedArtifact]:
    repo_path = Path(repo_root).resolve()
    artifacts: list[StagedArtifact] = []
    for result in command_results:
        for kind, log_path in [("stdout_log", result.stdout_log), ("stderr_log", result.stderr_log)]:
            path = Path(log_path).resolve()
            if not path.exists():
                continue
            artifacts.append(
                StagedArtifact(
                    kind=kind,
                    storage_mode="transient",
                    path=_relative_path(path, repo_path),
                    sha256=_sha256_file(path),
                    metadata={
                        "command_name": result.name,
                        "returncode": result.returncode,
                        "timed_out": result.timed_out,
                        "size_bytes": path.stat().st_size,
                    },
                )
            )
    return artifacts


def build_queue_result_payload(
    *,
    repo_root: str,
    expected_outputs: list[str],
    command_results: list[CommandResult],
    success: bool,
) -> QueueResultPayload:
    repo_path = Path(repo_root).resolve()
    metrics_rows: list[str] = []
    for output in expected_outputs:
        path = (repo_path / output).resolve()
        if path.exists() and path.is_file() and path.suffix.lower() == ".csv":
            metrics_rows.append(f"{output}:2")

    notes = [
        f"{result.name}: exit_code={result.returncode}, duration_s={result.duration_seconds:.3f}"
        + (" timed_out" if result.timed_out else "")
        for result in command_results
    ]
    if not success:
        failed = next((result for result in command_results if result.returncode != 0), None)
        if failed is not None:
            notes.append(f"failure_command={failed.name}")

    return QueueResultPayload(
        status="ok" if success else "fail",
        metrics_rows=metrics_rows,
        notes=notes,
    )

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "restart_local_control_plane_daemons.sh"


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _make_service_repo(tmp_path: Path, *, with_venv: bool = True) -> Path:
    repo_root = tmp_path / "service-repo"
    package_root = repo_root / "control_plane" / "control_plane"
    services_root = package_root / "services"
    services_root.mkdir(parents=True)
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    (services_root / "__init__.py").write_text("", encoding="utf-8")
    (services_root / "l2_result_consumer.py").write_text("VALUE = 'ok'\n", encoding="utf-8")

    if with_venv:
        bin_dir = repo_root / "control_plane" / ".venv" / "bin"
        bin_dir.mkdir(parents=True)
        _write_executable(
            bin_dir / "python",
            f"#!/usr/bin/env bash\nexec {sys.executable} \"$@\"\n",
        )
        (bin_dir / "activate").write_text("# test fixture\n", encoding="utf-8")

    return repo_root


def _run_script(repo_root: Path, action: str, **env_overrides: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    for key in (
        "RTLCP_ALLOW_FINITE_WORKER_DAEMON",
        "RTLCP_DATABASE_URL",
        "RTLCP_DB_MODE",
        "RTLCP_MACHINE_KEY",
        "RTLCP_MAX_POLLS",
        "RTLCP_ROLE",
        "RTLCP_STOP_ON_NO_WORK",
        "REPO_ROOT",
        "RTLGEN_SERVICE_REPO",
        "VENV_PATH",
    ):
        env.pop(key, None)
    env["RTLGEN_SERVICE_REPO"] = str(repo_root)
    env.update(env_overrides)
    return subprocess.run(
        [str(SCRIPT_PATH), action],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def test_preflight_requires_database_url(tmp_path: Path) -> None:
    repo_root = _make_service_repo(tmp_path)

    result = _run_script(repo_root, "preflight", RTLCP_MACHINE_KEY="eval-stable-1")

    assert result.returncode == 1
    assert "RTLCP_DATABASE_URL must be exported explicitly for preflight" in result.stderr


def test_check_import_requires_database_url(tmp_path: Path) -> None:
    repo_root = _make_service_repo(tmp_path)

    result = _run_script(repo_root, "check-import")

    assert result.returncode == 1
    assert "RTLCP_DATABASE_URL must be exported explicitly for check-import" in result.stderr


def test_preflight_requires_machine_key(tmp_path: Path) -> None:
    repo_root = _make_service_repo(tmp_path)

    result = _run_script(
        repo_root,
        "preflight",
        RTLCP_DATABASE_URL="postgresql+psycopg://rtlgen:secret@db.example.com:5432/rtlgen_control_plane",
    )

    assert result.returncode == 1
    assert "RTLCP_MACHINE_KEY must be exported explicitly for preflight" in result.stderr


def test_preflight_rejects_remote_localhost_database(tmp_path: Path) -> None:
    repo_root = _make_service_repo(tmp_path)

    result = _run_script(
        repo_root,
        "preflight",
        RTLCP_ROLE="evaluator",
        RTLCP_DB_MODE="remote",
        RTLCP_MACHINE_KEY="eval-stable-1",
        RTLCP_DATABASE_URL="postgresql+psycopg://rtlgen:secret@localhost:5432/rtlgen_control_plane",
    )

    assert result.returncode == 1
    assert "must not target localhost/127.0.0.1/::1" in result.stderr


@pytest.mark.parametrize(
    ("env_overrides", "expected_fragment"),
    [
        (
            {"RTLCP_STOP_ON_NO_WORK": "1"},
            "RTLCP_STOP_ON_NO_WORK=1 is not allowed for a managed daemon",
        ),
        (
            {"RTLCP_MAX_POLLS": "3"},
            "RTLCP_MAX_POLLS=3 is not allowed for a managed daemon",
        ),
    ],
)
def test_preflight_rejects_finite_worker_settings(
    tmp_path: Path, env_overrides: dict[str, str], expected_fragment: str
) -> None:
    repo_root = _make_service_repo(tmp_path)

    result = _run_script(
        repo_root,
        "preflight",
        RTLCP_ROLE="evaluator",
        RTLCP_DB_MODE="remote",
        RTLCP_MACHINE_KEY="eval-stable-1",
        RTLCP_DATABASE_URL="postgresql+psycopg://rtlgen:secret@db.example.com:5432/rtlgen_control_plane",
        **env_overrides,
    )

    assert result.returncode == 1
    assert expected_fragment in result.stderr


def test_preflight_allows_finite_worker_override(tmp_path: Path) -> None:
    repo_root = _make_service_repo(tmp_path)

    result = _run_script(
        repo_root,
        "preflight",
        RTLCP_ROLE="evaluator",
        RTLCP_DB_MODE="remote",
        RTLCP_MACHINE_KEY="eval-stable-1",
        RTLCP_DATABASE_URL="postgresql+psycopg://rtlgen:secret@db.example.com:5432/rtlgen_control_plane",
        RTLCP_STOP_ON_NO_WORK="1",
        RTLCP_MAX_POLLS="3",
        RTLCP_ALLOW_FINITE_WORKER_DAEMON="1",
    )

    assert result.returncode == 0
    assert "preflight OK" in result.stdout
    assert "allow_finite_worker_daemon=1" in result.stdout
    assert "max_polls=3" in result.stdout


def test_preflight_requires_virtualenv_files(tmp_path: Path) -> None:
    repo_root = _make_service_repo(tmp_path, with_venv=False)

    result = _run_script(
        repo_root,
        "preflight",
        RTLCP_ROLE="evaluator",
        RTLCP_DB_MODE="remote",
        RTLCP_MACHINE_KEY="eval-stable-1",
        RTLCP_DATABASE_URL="postgresql+psycopg://rtlgen:secret@db.example.com:5432/rtlgen_control_plane",
    )

    assert result.returncode == 1
    assert "Set VENV_PATH explicitly" in result.stderr
    assert f"{repo_root}/control_plane/.venv/bin/python" in result.stderr


@pytest.mark.parametrize(
    ("role", "db_mode", "database_url", "expected_host"),
    [
        (
            "server",
            "local",
            "postgresql+psycopg://rtlgen:secret@localhost:5432/rtlgen_control_plane",
            "localhost",
        ),
        (
            "evaluator",
            "remote",
            "postgresql+psycopg://rtlgen:secret@db.example.com:5432/rtlgen_control_plane",
            "db.example.com",
        ),
    ],
)
def test_preflight_succeeds_for_explicit_local_and_remote_configs(
    tmp_path: Path, role: str, db_mode: str, database_url: str, expected_host: str
) -> None:
    repo_root = _make_service_repo(tmp_path)

    result = _run_script(
        repo_root,
        "preflight",
        RTLCP_ROLE=role,
        RTLCP_DB_MODE=db_mode,
        RTLCP_MACHINE_KEY="eval-stable-1",
        RTLCP_DATABASE_URL=database_url,
    )

    assert result.returncode == 0
    assert "preflight OK" in result.stdout
    assert f"repo_root={repo_root}" in result.stdout
    assert f"venv_path={repo_root}/control_plane/.venv" in result.stdout
    assert "machine_key=eval-stable-1" in result.stdout
    assert f"role={role}" in result.stdout
    assert f"db_mode={db_mode}" in result.stdout
    assert f"db_host={expected_host}" in result.stdout
    assert "stop_on_no_work=0" in result.stdout
    assert "max_polls=persistent" in result.stdout
    assert "secret" not in result.stdout
    assert "control_plane import path OK:" in result.stdout

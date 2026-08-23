import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEVCONTAINER = REPO_ROOT / ".devcontainer"


def test_devcontainer_runs_as_uid_remapped_non_root_user() -> None:
    config = json.loads((DEVCONTAINER / "devcontainer.json").read_text(encoding="utf-8"))

    assert config["remoteUser"] == "rtlgen"
    assert config["updateRemoteUserUID"] is True
    assert config["workspaceMount"] == (
        "source=${localWorkspaceFolder},target=/workspaces/RTLGen,type=bind"
    )
    assert config["workspaceFolder"] == "/workspaces/RTLGen"
    assert config["containerEnv"]["RTLCP_REPO_SLUG"] == "yhmtmt/RTLGen"
    assert config["containerEnv"]["VENV_PATH"] == "/home/rtlgen/.venvs/rtlgen-control-plane"
    assert config["postCreateCommand"] == (
        "/workspaces/RTLGen/control_plane/scripts/bootstrap_venv.sh "
        "/home/rtlgen/.venvs/rtlgen-control-plane"
    )
    assert config["postStartCommand"] == "/workspaces/RTLGen/.devcontainer/post_start.sh"
    assert config["mounts"] == [
        "source=${localEnv:HOME}/.codex,target=/home/rtlgen/.codex,type=bind"
    ]


def test_dockerfile_grants_only_image_owned_init_helper() -> None:
    dockerfile = (DEVCONTAINER / "Dockerfile").read_text(encoding="utf-8")

    assert "USER ${USERNAME}" in dockerfile
    assert "ENV HOME=/home/${USERNAME}" in dockerfile
    assert 'ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"' in dockerfile
    assert "COPY .devcontainer/rtlgen-container-init /usr/local/sbin/rtlgen-container-init" in dockerfile
    assert "NOPASSWD: /usr/local/sbin/rtlgen-container-init" in dockerfile
    assert "NOPASSWD: ALL" not in dockerfile


def test_privileged_helper_does_not_execute_workspace_scripts() -> None:
    helper = (DEVCONTAINER / "rtlgen-container-init").read_text(encoding="utf-8")

    assert "/workspaces/RTLGen/" not in helper
    assert "source " not in helper
    assert "eval " not in helper
    assert "chown -R" not in helper
    assert '[[ -L "${path}" ]]' in helper
    assert "^[A-Za-z_][A-Za-z0-9_]*$" in helper
    assert "^[0-9A-Fa-f:.]+/[0-9]+$" in helper


def test_privileged_helper_rejects_symlinked_workspaces_parent() -> None:
    helper = (DEVCONTAINER / "rtlgen-container-init").read_text(encoding="utf-8")

    assert "[[ -L /workspaces ]]" in helper
    assert "Refusing symlink at privileged directory: /workspaces" in helper
    assert helper.index("[[ -L /workspaces ]]") < helper.index("install -d")


def test_privileged_helper_owns_workspaces_non_recursively() -> None:
    helper = (DEVCONTAINER / "rtlgen-container-init").read_text(encoding="utf-8")

    assert 'install -d -o "${RTLGEN_USER}" -g "${RTLGEN_GROUP}" -m 0755 /workspaces' in helper
    assert 'chown "${RTLGEN_USER}:${RTLGEN_GROUP}" /workspaces' in helper
    assert 'chown -R' not in helper
    assert 'chown "${RTLGEN_USER}:${RTLGEN_GROUP}" /workspaces/' not in helper


def test_privileged_helper_prepares_only_orfs_runtime_roots() -> None:
    helper = (DEVCONTAINER / "rtlgen-container-init").read_text(encoding="utf-8")
    expected_paths = (
        "/orfs/flow/designs/src",
        "/orfs/flow/designs/nangate45",
        "/orfs/flow/logs",
        "/orfs/flow/objects",
        "/orfs/flow/reports",
        "/orfs/flow/results",
    )

    for path in expected_paths:
        assert path in helper
    assert "/orfs/flow/platforms" not in helper
    assert "/orfs/flow/scripts" not in helper
    assert "chown -R" not in helper


def test_post_start_rejects_root_and_uses_noninteractive_sudo() -> None:
    post_start = (DEVCONTAINER / "post_start.sh").read_text(encoding="utf-8")

    assert '[[ "$(id -u)" == "0" ]]' in post_start
    assert "sudo -n /usr/local/sbin/rtlgen-container-init prepare" in post_start


def test_service_start_failure_prints_the_service_log() -> None:
    service_ctl = (DEVCONTAINER / "control_plane_service_ctl.sh").read_text(
        encoding="utf-8"
    )

    assert 'echo "failed to start ${SERVICE}; see ${LOG_FILE}" >&2' in service_ctl
    assert "_tail_log 40 >&2" in service_ctl


def test_codex_installer_is_unprivileged_and_user_local() -> None:
    installer = (REPO_ROOT / "scripts/install-codex-cli.sh").read_text(
        encoding="utf-8"
    )

    assert "sudo" not in installer
    assert 'INSTALL_DIR="${CODEX_INSTALL_DIR:-${HOME}/.local/bin}"' in installer
    assert 'install -m 0755' in installer
    assert "${HOME}/.codex/plugins/.plugin-appserver/codex-code-mode-host" in installer
    assert 'CODE_MODE_HOST_TARGET="${INSTALL_DIR}/codex-code-mode-host"' in installer


def test_server_starts_api_before_resolver() -> None:
    startup = (DEVCONTAINER / "start_control_plane_services.sh").read_text(
        encoding="utf-8"
    )
    server_case = startup.rsplit("  server)", maxsplit=1)[1].split(
        "    ;;", maxsplit=1
    )[0]

    assert '${AUTOSTART_API:-1}' in server_case
    assert server_case.index("start api") < server_case.index("start resolver")


def test_server_honors_completion_autostart_and_enables_dispatch() -> None:
    startup = (DEVCONTAINER / "start_control_plane_services.sh").read_text(
        encoding="utf-8"
    )
    server_case = startup.rsplit("  server)", maxsplit=1)[1].split(
        "    ;;", maxsplit=1
    )[0]

    assert '${AUTOSTART_COMPLETIONS:-0}' in server_case
    assert 'export RTLCP_AUTODISPATCH_READY="${RTLCP_AUTODISPATCH_READY:-1}"' in server_case
    assert (
        'export RTLCP_PROCESS_COMPLETIONS_IN_LOOP='
        '"${RTLCP_PROCESS_COMPLETIONS_IN_LOOP:-1}"'
    ) in server_case
    assert "start completions" in server_case


def test_maintenance_loop_helpers_are_executable() -> None:
    maintenance = (DEVCONTAINER / "run_maintenance_loop.sh").read_text(
        encoding="utf-8"
    )
    scripts = REPO_ROOT / "control_plane" / "scripts"

    for script_name in (
        "dispatch_ready_items_service.sh",
        "poll_github_service.sh",
        "refresh_blocked_dependents_service.sh",
        "report_failure_issues_service.sh",
    ):
        assert script_name in maintenance
        assert (scripts / script_name).stat().st_mode & 0o111


def test_service_bootstrap_rejects_stale_image_helper_before_starting_daemons() -> None:
    startup = (DEVCONTAINER / "start_control_plane_services.sh").read_text(
        encoding="utf-8"
    )

    assert 'IMAGE_INIT_HELPER="/usr/local/sbin/rtlgen-container-init"' in startup
    assert 'REPO_INIT_HELPER="/workspaces/RTLGen/.devcontainer/rtlgen-container-init"' in startup
    assert 'cmp -s "${IMAGE_INIT_HELPER}" "${REPO_INIT_HELPER}"' in startup
    assert "Rebuild the devcontainer image before starting control-plane services." in startup
    assert startup.index("prepare_runtime_paths") < startup.index('case "${ROLE}" in')


def test_service_bootstrap_prepares_and_checks_orfs_runtime_roots() -> None:
    startup = (DEVCONTAINER / "start_control_plane_services.sh").read_text(
        encoding="utf-8"
    )
    expected_paths = (
        "/orfs/flow/designs/src",
        "/orfs/flow/designs/nangate45",
        "/orfs/flow/logs",
        "/orfs/flow/objects",
        "/orfs/flow/reports",
        "/orfs/flow/results",
    )

    assert 'sudo -n "${IMAGE_INIT_HELPER}" prepare' in startup
    assert '[[ ! -d "${path}" || ! -w "${path}" ]]' in startup
    for path in expected_paths:
        assert path in startup


def test_migration_scripts_honor_external_devcontainer_venv() -> None:
    scripts = REPO_ROOT / "control_plane" / "scripts"

    for script_name in (
        "migrate_smoke.sh",
        "migrate_postgres.sh",
        "ensure_postgres_db.sh",
    ):
        script = (scripts / script_name).read_text(encoding="utf-8")
        assert 'VENV_DIR=${RTLCP_VENV_DIR:-${VENV_PATH:-"$ROOT_DIR/.venv"}}' in script

    bootstrap = (scripts / "bootstrap_venv.sh").read_text(encoding="utf-8")
    assert 'VENV_PATH="$VENV_DIR" "$ROOT_DIR/scripts/migrate_smoke.sh"' in bootstrap

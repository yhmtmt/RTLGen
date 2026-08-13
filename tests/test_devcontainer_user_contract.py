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

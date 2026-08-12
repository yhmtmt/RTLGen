import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEVCONTAINER = REPO_ROOT / ".devcontainer"


def test_devcontainer_runs_as_uid_remapped_non_root_user() -> None:
    config = json.loads((DEVCONTAINER / "devcontainer.json").read_text(encoding="utf-8"))

    assert config["remoteUser"] == "rtlgen"
    assert config["updateRemoteUserUID"] is True
    assert config["postStartCommand"] == "/workspaces/RTLGen/.devcontainer/post_start.sh"
    assert config["mounts"] == [
        "source=${localEnv:HOME}/.codex,target=/home/rtlgen/.codex,type=bind"
    ]


def test_dockerfile_grants_only_image_owned_init_helper() -> None:
    dockerfile = (DEVCONTAINER / "Dockerfile").read_text(encoding="utf-8")

    assert "USER ${USERNAME}" in dockerfile
    assert "ENV HOME=/home/${USERNAME}" in dockerfile
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

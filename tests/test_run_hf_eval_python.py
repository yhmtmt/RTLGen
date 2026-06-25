#!/usr/bin/env python3
"""Tests for the Hugging Face eval launcher."""

from __future__ import annotations

import json
import os
import subprocess
import textwrap
from pathlib import Path


def test_run_hf_eval_python_adds_repo_root_to_pythonpath(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    fake_python = tmp_path / "fake_python"
    marker = tmp_path / "marker.json"
    probe_script = tmp_path / "probe.py"

    fake_python.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail
            if [[ "${1:-}" == "-" ]]; then
              cat >/dev/null
              exit 0
            fi
            if [[ "${1:-}" == "-c" ]]; then
              printf '3.11.0\\n'
              exit 0
            fi
            exec python3 "$@"
            """
        ),
        encoding="utf-8",
    )
    fake_python.chmod(0o755)

    probe_script.write_text(
        textwrap.dedent(
            """\
            import json
            import os
            import sys
            import npu.eval.evaluate_llm_decoder_model_native_mixed_int8_attention

            with open(sys.argv[1], "w", encoding="utf-8") as f:
                json.dump({"pythonpath": os.environ.get("PYTHONPATH", "")}, f)
            """
        ),
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["RTLGEN_HF_MATERIALIZER_PYTHON"] = str(fake_python)
    env.pop("PYTHONPATH", None)

    subprocess.run(
        ["bash", "npu/eval/run_hf_eval_python.sh", str(probe_script), str(marker)],
        cwd=repo_root,
        env=env,
        check=True,
    )

    data = json.loads(marker.read_text(encoding="utf-8"))
    assert data["pythonpath"].split(os.pathsep)[0] == str(repo_root)

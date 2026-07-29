import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_cluster_sram_service_gqa8 import build_default_config, generate


def _prepare_design_dir(tmp_path: Path, *, producers: int) -> Path:
    design_dir = tmp_path / f"design_p{producers}"
    design_dir.mkdir(parents=True, exist_ok=True)
    config = build_default_config(producers=producers)
    (design_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    generate(config, design_dir / "verilog")
    return design_dir


def _run_guard(design_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "npu/eval/check_attention_score32_exact_cluster_sram_service_gqa8_guard.py",
            "--design-dir",
            str(design_dir),
            "--config",
            str(design_dir / "config.json"),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


class ClusterSramServiceGuardTests(unittest.TestCase):
    def test_cluster_sram_service_guard_accepts_generated_designs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cluster_sram_service_guard_") as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            for producers in (53, 54):
                design_dir = _prepare_design_dir(temp_dir, producers=producers)
                result = _run_guard(design_dir)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["producers"], producers)
                self.assertEqual(payload["status"], "ok")

    def test_cluster_sram_service_guard_rejects_drifted_top(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cluster_sram_service_guard_drift_") as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            design_dir = _prepare_design_dir(temp_dir, producers=53)
            top_path = design_dir / "verilog" / "top.v"
            top_path.write_text(top_path.read_text(encoding="utf-8") + "\n// stale drift\n", encoding="utf-8")

            result = _run_guard(design_dir)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("generated RTL artifacts do not match current generator output: top.v", result.stderr)


if __name__ == "__main__":
    unittest.main()

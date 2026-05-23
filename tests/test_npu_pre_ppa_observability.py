#!/usr/bin/env python3
"""Pre-PPA observability checks for generated NPU compute datapaths."""

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_CONFIG = REPO_ROOT / "npu/rtlgen/examples/minimal_gemm_4modules.json"


def _write_config(path: Path, *, num_modules: int) -> None:
    cfg = json.loads(BASE_CONFIG.read_text(encoding="utf-8"))
    cfg["compute"]["gemm"]["num_modules"] = int(num_modules)
    path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")


def _generate_rtl(config: Path, out_dir: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "npu/rtlgen/gen.py"),
            "--config",
            str(config),
            "--out",
            str(out_dir),
        ],
        cwd=str(REPO_ROOT),
        check=True,
        capture_output=True,
        text=True,
    )


def _yosys_stat(top_v: Path) -> str:
    completed = subprocess.run(
        [
            "yosys",
            "-p",
            f"read_verilog -sv {top_v}; hierarchy -check -top npu_top; proc; opt; stat",
        ],
        cwd=str(REPO_ROOT),
        check=True,
        capture_output=True,
        text=True,
        timeout=90,
    )
    return completed.stdout + completed.stderr


def _max_gemm_mac_count(stat_log: str) -> int:
    counts = [
        int(match.group(1))
        for match in re.finditer(r"gemm_mac_int8[ \t]+(\d+)", stat_log)
    ]
    if not counts:
        return 0
    return max(counts)


@unittest.skipIf(shutil.which("yosys") is None, "yosys is required for pre-PPA observability checks")
class NpuPrePpaObservabilityTest(unittest.TestCase):
    def test_gemm_mac_instances_survive_yosys_opt_for_num_modules(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            counts: dict[int, int] = {}
            for num_modules in (1, 4):
                config = tmp / f"nm{num_modules}.json"
                out_dir = tmp / f"nm{num_modules}"
                _write_config(config, num_modules=num_modules)
                _generate_rtl(config, out_dir)
                stat_log = _yosys_stat(out_dir / "top.v")
                counts[num_modules] = _max_gemm_mac_count(stat_log)
                self.assertIn("gemm_compute_array", stat_log)

        self.assertEqual(counts[1], 1)
        self.assertEqual(counts[4], 4)
        self.assertGreater(counts[4], counts[1])


if __name__ == "__main__":
    unittest.main()

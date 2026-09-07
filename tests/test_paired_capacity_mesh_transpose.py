"""Real refill + first three paired K heads through the capacity mesh wrapper."""
from pathlib import Path
import os
import shutil
import subprocess

import pytest

from test_attention_kv_capacity_gather_mesh_ingress_elaboration import RTL_FILES

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("producers", [53, 54])
def test_refill_resident_and_split_heads_through_mesh(tmp_path, producers):
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        pytest.skip("Icarus unavailable")
    tb = tmp_path / "tb.sv"
    tb.write_text((ROOT / "tests/paired_capacity_mesh_transpose_tb.sv").read_text()
                  .replace("PRODUCER_COUNT", str(producers)))
    binary = tmp_path / "simv"
    result = subprocess.run(["iverilog", "-g2012", "-s", "tb", "-o", str(binary), str(tb),
                             *(str(ROOT / p) for p in RTL_FILES),
                             str(ROOT / "npu/sim/rtl/attention_score32_exact_kv_key_pingpong_transpose.sv")],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    assert "expects" not in result.stderr, result.stderr
    try:
        result = subprocess.run(["vvp", str(binary)], cwd=tmp_path, capture_output=True,
                                text=True, timeout=int(os.environ.get("RTLGEN_PAIRED_MESH_TIMEOUT", "1800")))
    except subprocess.TimeoutExpired as error:
        progress = tmp_path / "progress.log"
        tail = "\n".join(progress.read_text().splitlines()[-5:]) if progress.exists() else "no progress log"
        pytest.fail(f"Transport runtime limit reached; latest simulation progress:\n{tail}\n{error}")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS refill=69632 inputs=12288 outputs=12288 descriptors=394" in result.stdout

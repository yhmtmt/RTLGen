"""Real refill + first three paired K heads through the capacity mesh wrapper."""
from pathlib import Path
import os
import shutil
import subprocess

import pytest

from test_attention_kv_capacity_gather_mesh_ingress_elaboration import RTL_FILES
from npu.sim.perf.canonical_attention_fixture import CanonicalAttentionFixture

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("producers", [53, 54])
def test_refill_resident_and_split_heads_through_mesh(tmp_path, producers):
    _run_transport(tmp_path, producers, with_stage=False)


@pytest.mark.parametrize("producers", [53, 54])
def test_refill_through_mesh_transpose_and_kq_stage(tmp_path, producers):
    _run_transport(tmp_path, producers, with_stage=True)


@pytest.mark.parametrize("producers", [53, 54])
def test_continuous_fixture_query_initialization(tmp_path, producers):
    _run_transport(tmp_path, producers, with_stage=True, query_only=True)


@pytest.mark.parametrize("producers", [53, 54])
def test_canonical_refill_mesh_and_kq_stage(tmp_path, producers):
    _run_transport(tmp_path, producers, with_stage=True, canonical=True)


@pytest.mark.parametrize("producers", [53, 54])
def test_canonical_fixture_query_initialization(tmp_path, producers):
    _run_transport(tmp_path, producers, with_stage=True, canonical=True, query_only=True)


def _write_canonical_sidecars(tmp_path, producers):
    fixture = CanonicalAttentionFixture()
    with (tmp_path / "canonical_hbm.hex").open("w") as output:
        for tile in range(3):
            for address in range(0, 1 << 20, 32):
                word = int.from_bytes(fixture.memory_flit(tile=tile, address=address), "little")
                output.write(f"{word:064x}\n")
    (tmp_path / "canonical_query.hex").write_text("".join(
        f"{int.from_bytes(bytes(v & 255 for v in fixture.query(group=0, dimension=d)), 'little'):016x}\n"
        for d in range(128)))
    with (tmp_path / "canonical_producers.hex").open("w") as output:
        for tile in range(3):
            for producer in range(producers):
                words = [0] * 256
                for beat, (q, k, last) in enumerate(fixture.producer_stream(
                        producers=producers, producer=producer, group=0, tile=tile)):
                    qw = int.from_bytes(bytes(v & 255 for v in q), "little")
                    kw = int.from_bytes(bytes(v & 255 for v in k), "little")
                    words[beat] = (qw << 129) | (kw << 1) | int(last)
                output.write("".join(f"{word:065x}\n" for word in words))


def _run_transport(tmp_path, producers, *, with_stage, query_only=False, canonical=False):
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        pytest.skip("Icarus unavailable")
    tb = tmp_path / "tb.sv"
    if canonical:
        _write_canonical_sidecars(tmp_path, producers)
    tb.write_text((ROOT / "tests/paired_capacity_mesh_transpose_tb.sv").read_text()
                  .replace("PRODUCER_COUNT", str(producers))
                  .replace("STAGE_ENABLED", "1" if with_stage else "0")
                  .replace("CANONICAL_ENABLED", "1" if canonical else "0"))
    binary = tmp_path / "simv"
    result = subprocess.run(["iverilog", "-g2012", "-s", "tb", "-o", str(binary), str(tb),
                             *(str(ROOT / p) for p in RTL_FILES),
                             str(ROOT / "npu/sim/rtl/attention_score32_exact_kv_key_pingpong_transpose.sv"),
                             str(ROOT / "npu/sim/rtl/attention_score32_exact_kv_key_stage_wide.sv")],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    assert "expects" not in result.stderr, result.stderr
    try:
        result = subprocess.run(["vvp", str(binary), *(["+QUERY_AUDIT"] if query_only else [])], cwd=tmp_path, capture_output=True,
                                text=True, timeout=int(os.environ.get("RTLGEN_PAIRED_MESH_TIMEOUT", "1800")))
    except subprocess.TimeoutExpired as error:
        progress = tmp_path / "progress.log"
        tail = "\n".join(progress.read_text().splitlines()[-5:]) if progress.exists() else "no progress log"
        pytest.fail(f"Transport runtime limit reached; latest simulation progress:\n{tail}\n{error}")
    assert result.returncode == 0, result.stdout + result.stderr
    if query_only:
        assert "PASS query initialization" in result.stdout
        return
    assert "PASS refill=69632 inputs=12288 outputs=12288 descriptors=394" in result.stdout
    if with_stage:
        assert "PASS staged producer beats=24576" in result.stdout

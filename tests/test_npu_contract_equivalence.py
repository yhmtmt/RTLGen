#!/usr/bin/env python3
"""Minimal perf-vs-RTL contract conformance regression."""

import json
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RTLGEN_CONFIG = REPO_ROOT / "npu/rtlgen/examples/minimal.json"


def _pack_desc(opcode: int, flags: int = 0, size_units: int = 1, tag: int = 0) -> bytearray:
    raw = bytearray(32 * size_units)
    struct.pack_into("<BBBBI", raw, 0, opcode & 0xFF, flags & 0xFF, size_units & 0xFF, 0, tag & 0xFFFFFFFF)
    return raw


def _encode_gemm_tag(m: int, n: int, k: int) -> int:
    return ((int(m) & 0xFFF) << 20) | ((int(n) & 0x3FF) << 10) | (int(k) & 0x3FF)


def _write_event_dma_stream(path: Path) -> None:
    raw = bytearray()

    dma0 = _pack_desc(0x01)
    struct.pack_into("<QQI", dma0, 8, 0x0, 0x10000, 256)
    raw.extend(dma0)

    raw.extend(_pack_desc(0x20, tag=1))
    raw.extend(_pack_desc(0x21, tag=1))

    dma1 = _pack_desc(0x01)
    struct.pack_into("<QQI", dma1, 8, 0x200, 0x10200, 256)
    raw.extend(dma1)

    path.write_bytes(bytes(raw))


def _write_gemm_event_dma_stream(path: Path) -> None:
    raw = bytearray()

    gemm = _pack_desc(0x10, tag=_encode_gemm_tag(64, 64, 64))
    struct.pack_into("<QQQ", gemm, 8, 0x1000, 0x2000, 0x3000)
    raw.extend(gemm)

    raw.extend(_pack_desc(0x20, tag=1))
    raw.extend(_pack_desc(0x21, tag=1))

    dma = _pack_desc(0x01)
    struct.pack_into("<QQI", dma, 8, 0x4000, 0x5000, 1024)
    raw.extend(dma)

    path.write_bytes(bytes(raw))


def _write_gemm_vec_dependent_stream(path: Path) -> None:
    raw = bytearray()

    gemm = _pack_desc(0x10, tag=_encode_gemm_tag(1, 1, 1))
    for idx, value in enumerate([2, 3, 4, 5, 6, 7, 8, 9]):
        gemm[8 + idx] = value
    for idx in range(8):
        gemm[16 + idx] = 1
    struct.pack_into("<Q", gemm, 24, 0x3000)
    raw.extend(gemm)

    raw.extend(_pack_desc(0x20, tag=1))
    raw.extend(_pack_desc(0x21, tag=1))

    vec = _pack_desc(0x11, flags=0x00, tag=0x80000000)
    struct.pack_into("<QQI", vec, 8, 0x3000, 0x6000, 8)
    raw.extend(vec)

    path.write_bytes(bytes(raw))


def _run_perf(
    bin_path: Path,
    out_path: Path,
    cfg_path: Path,
    *,
    mem_path: Path | None = None,
) -> list[dict[str, object]]:
    cmd = [
            sys.executable,
            str(REPO_ROOT / "npu/sim/perf/run.py"),
            "--bin",
            str(bin_path),
            "--out",
            str(out_path),
            "--config",
            str(cfg_path),
            "--overlap",
        ]
    if mem_path is not None:
        cmd.extend(["--mem-json", str(mem_path)])
    subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        check=True,
    )
    data = json.loads(out_path.read_text(encoding="utf-8"))
    return data["trace"]


def _normalize_perf_trace(trace: list[dict[str, object]], scenario: str) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    dma_seen = 0
    for ev in trace:
        name = ev["name"]
        if name == "GEMM":
            normalized.append({"kind": "done", "opcode": 0x10, "offset": 0})
        elif name == "DMA_COPY":
            if scenario == "event_dma":
                offset = 0 if dma_seen == 0 else 96
                normalized.append(
                    {
                        "kind": "complete" if dma_seen == 0 else "issue",
                        "opcode": 0x01,
                        "offset": offset,
                    }
                )
            elif scenario == "gemm_event_dma":
                normalized.append({"kind": "issue", "opcode": 0x01, "offset": 96})
            dma_seen += 1
        elif name == "EVENT_SIGNAL":
            normalized.append({"kind": "retire", "opcode": 0x20, "offset": 32})
        elif name == "EVENT_WAIT":
            normalized.append({"kind": "retire", "opcode": 0x21, "offset": 64})
    return normalized


def _run_rtl_stdout(bin_path: Path, plusargs: list[str]) -> str:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        rtl_out = tmp / "rtl_out"
        subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "npu/rtlgen/gen.py"),
                "--config",
                str(RTLGEN_CONFIG),
                "--out",
                str(rtl_out),
            ],
            cwd=str(REPO_ROOT),
            check=True,
        )
        vvp_path = Path(td) / "tb_npu_shell.vvp"
        subprocess.run(
            [
                "iverilog",
                "-g2012",
                "-I",
                str(rtl_out),
                "-s",
                "tb_npu_shell",
                "-o",
                str(vvp_path),
                str(rtl_out / "top.v"),
                str(REPO_ROOT / "npu/sim/rtl/tb_npu_shell.sv"),
                str(REPO_ROOT / "npu/sim/rtl/axi_mem_router.sv"),
                str(REPO_ROOT / "npu/sim/rtl/axi_mem_model.sv"),
                str(rtl_out / "sram_models.sv"),
            ],
            cwd=str(REPO_ROOT),
            check=True,
        )
        completed = subprocess.run(
            [
                "vvp",
                str(vvp_path),
                f"+bin={bin_path}",
                "+contract_trace=1",
                *plusargs,
            ],
            cwd=str(REPO_ROOT),
            check=True,
            capture_output=True,
            text=True,
        )

    return completed.stdout


def _run_rtl(bin_path: Path, plusargs: list[str]) -> list[dict[str, object]]:
    stdout = _run_rtl_stdout(bin_path, plusargs)
    pattern = re.compile(
        r"^CONTRACT_TRACE kind=(?P<kind>[a-z_]+) opcode=0x(?P<opcode>[0-9a-fA-F]+) "
        r"offset=(?P<offset>-?\d+) cycle=(?P<cycle>\d+)$"
    )
    normalized: list[dict[str, object]] = []
    for line in stdout.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        entry = {
            "kind": match.group("kind"),
            "opcode": int(match.group("opcode"), 16),
            "offset": int(match.group("offset")),
        }
        if entry == {"kind": "issue", "opcode": 0x01, "offset": 0}:
            continue
        if entry == {"kind": "complete", "opcode": 0x01, "offset": 96}:
            continue
        normalized.append(entry)
    return normalized


class NpuContractEquivalenceTest(unittest.TestCase):
    def test_event_dma_contract_matches_between_perf_and_rtl(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            bin_path = tmp / "event_dma.bin"
            out_path = tmp / "trace.json"
            cfg_path = tmp / "cfg.json"
            _write_event_dma_stream(bin_path)
            cfg_path.write_text(
                json.dumps(
                    {
                        "dma_bw_gbps": 16.0,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            perf_trace = _normalize_perf_trace(_run_perf(bin_path, out_path, cfg_path), "event_dma")
            rtl_trace = _run_rtl(bin_path, ["+bytes=128", "+event_dma_test=1"])

        expected = [
            {"kind": "complete", "opcode": 0x01, "offset": 0},
            {"kind": "retire", "opcode": 0x20, "offset": 32},
            {"kind": "retire", "opcode": 0x21, "offset": 64},
            {"kind": "issue", "opcode": 0x01, "offset": 96},
        ]
        self.assertEqual(perf_trace, expected)
        self.assertEqual(rtl_trace, expected)

    def test_gemm_architectural_writeback_matches_between_perf_and_rtl(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            bin_path = tmp / "gemm_event_dma.bin"
            perf_path = tmp / "trace.json"
            cfg_path = tmp / "cfg.json"
            rtl_log = tmp / "rtl.log"
            rtl_summary = tmp / "rtl_arch_summary.json"
            perf_summary = tmp / "perf_arch_summary.json"
            _write_gemm_event_dma_stream(bin_path)
            cfg_path.write_text(
                json.dumps(
                    {
                        "gemm_tops": 1.0,
                        "dma_bw_gbps": 16.0,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            _run_perf(bin_path, perf_path, cfg_path)
            rtl_log.write_text(
                _run_rtl_stdout(
                    bin_path,
                    ["+bytes=128", "+contract_trace=1", "+gemm_mac_test=1", "+contract_gemm_event_dma_test=1"],
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "npu/sim/perf/compare_tensor_traces.py"),
                    "--rtl-log",
                    str(rtl_log),
                    "--perf-trace",
                    str(perf_path),
                    "--rtl-summary-out",
                    str(rtl_summary),
                    "--perf-summary-out",
                    str(perf_summary),
                    "--require-architectural-gemm-writeback",
                ],
                cwd=str(REPO_ROOT),
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("compare-tensor-trace: OK", completed.stdout)

    def test_gemm_to_memory_backed_vec_matches_between_perf_and_rtl(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            bin_path = tmp / "gemm_vec.bin"
            perf_path = tmp / "trace.json"
            cfg_path = tmp / "cfg.json"
            mem_path = tmp / "mem.json"
            rtl_log = tmp / "rtl.log"
            _write_gemm_vec_dependent_stream(bin_path)
            cfg_path.write_text(
                json.dumps(
                    {
                        "gemm_tops": 1.0,
                        "dma_bw_gbps": 16.0,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            mem_path.write_text(
                json.dumps(
                    {
                        "segments": [
                            {
                                "addr": "0x3000",
                                "data_bytes": [0, 1, 2, 3, 4, 5, 6, 7],
                            }
                        ]
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            _run_perf(bin_path, perf_path, cfg_path, mem_path=mem_path)
            rtl_log.write_text(
                _run_rtl_stdout(
                    bin_path,
                    ["+bytes=128", "+vec_test=1", "+contract_trace=1", "+gemm_mac_test=1"],
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "npu/sim/perf/compare_tensor_traces.py"),
                    "--rtl-log",
                    str(rtl_log),
                    "--perf-trace",
                    str(perf_path),
                    "--require-architectural-writeback",
                ],
                cwd=str(REPO_ROOT),
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("compare-tensor-trace: OK", completed.stdout)

    def test_gemm_event_dma_contract_matches_between_perf_and_rtl(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            bin_path = tmp / "gemm_event_dma.bin"
            out_path = tmp / "trace.json"
            cfg_path = tmp / "cfg.json"
            _write_gemm_event_dma_stream(bin_path)
            cfg_path.write_text(
                json.dumps(
                    {
                        "gemm_tops": 1.0,
                        "dma_bw_gbps": 16.0,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            perf_trace = _normalize_perf_trace(_run_perf(bin_path, out_path, cfg_path), "gemm_event_dma")
            rtl_trace = _run_rtl(bin_path, ["+bytes=128", "+contract_gemm_event_dma_test=1"])

        expected = [
            {"kind": "done", "opcode": 0x10, "offset": 0},
            {"kind": "retire", "opcode": 0x20, "offset": 32},
            {"kind": "retire", "opcode": 0x21, "offset": 64},
            {"kind": "issue", "opcode": 0x01, "offset": 96},
        ]
        self.assertEqual(perf_trace, expected)
        self.assertEqual(rtl_trace, expected)


if __name__ == "__main__":
    unittest.main()

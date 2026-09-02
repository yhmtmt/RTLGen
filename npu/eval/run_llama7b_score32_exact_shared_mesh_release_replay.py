#!/usr/bin/env python3
"""Run the exact producer-release-coupled shared-mesh RTL verification gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.prepare_llama7b_score32_exact_shared_mesh_release_replay import (
    REPLAY_MODEL,
    build_replay,
    make_source_ref,
    main as prepare_replay,
)


JsonDict = dict[str, Any]
RESULT_MODEL = "llama7b_score32_exact_shared_mesh_release_coupled_rtl_v1"
SUMMARY_RE = re.compile(
    r"PASS promotion-scale shared-mesh replay "
    r"compile_s=(?P<compile_s>[0-9.]+) "
    r"run_s=(?P<run_s>[0-9.]+) "
    r"arb_decisions=(?P<eager_arb_decisions>\d+) "
    r"envelope_s=(?P<envelope_s>[0-9.]+) "
    r"envelope_cycles=(?P<envelope_cycles>\d+) "
    r"release_coupled_cycles=(?P<release_cycles>\d+) "
    r"release_vc0_done_cycle=(?P<release_vc0_done>\d+) "
    r"release_vc1_done_cycle=(?P<release_vc1_done>\d+) "
    r"release_arb_decisions=(?P<release_arb_decisions>\d+) "
    r"release_source_fires=(?P<release_source_fires>\d+)"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_result(
    *,
    replay: JsonDict,
    cadence_path: Path,
    pytest_stdout: str,
    pytest_stderr: str = "",
) -> JsonDict:
    if replay.get("model") != REPLAY_MODEL:
        raise ValueError("unexpected release replay model")
    match = SUMMARY_RE.search(pytest_stdout)
    if match is None:
        raise ValueError("full RTL replay did not emit its passing release summary")
    values = match.groupdict()
    release_cycles = int(values["release_cycles"])
    vc0_done = int(values["release_vc0_done"])
    vc1_done = int(values["release_vc1_done"])
    if release_cycles != max(vc0_done, vc1_done):
        raise ValueError("release service completion differs from the later producer")

    return {
        "version": 1,
        "model": RESULT_MODEL,
        "passed": True,
        "decision": "exact_cluster_release_coupled_shared_mesh_rtl_verified",
        "source_refs": [
            make_source_ref(cadence_path),
            {
                "path": "npu/eval/prepare_llama7b_score32_exact_shared_mesh_release_replay.py",
                "sha256": _sha256(
                    REPO_ROOT
                    / "npu/eval/prepare_llama7b_score32_exact_shared_mesh_release_replay.py"
                ),
            },
            {
                "path": "npu/eval/run_llama7b_score32_exact_shared_mesh_release_replay.py",
                "sha256": _sha256(
                    REPO_ROOT
                    / "npu/eval/run_llama7b_score32_exact_shared_mesh_release_replay.py"
                ),
            },
            {
                "path": "tests/attention_score32_exact_dual_producer_shared_mesh4x4_full_tb.sv",
                "sha256": _sha256(
                    REPO_ROOT
                    / "tests/attention_score32_exact_dual_producer_shared_mesh4x4_full_tb.sv"
                ),
            },
            {
                "path": "tests/test_attention_score32_exact_dual_producer_shared_mesh4x4_full.py",
                "sha256": _sha256(
                    REPO_ROOT
                    / "tests/test_attention_score32_exact_dual_producer_shared_mesh4x4_full.py"
                ),
            },
        ],
        "release_contract": replay,
        "rtl_observation": {
            "mode": "producer_release_coupled_single_held_beat_stall_dilated",
            "service_cycles": release_cycles,
            "vc0_done_cycle": vc0_done,
            "vc1_done_cycle": vc1_done,
            "standalone_eager_envelope_cycles": int(values["envelope_cycles"]),
            "release_arbiter_decisions_checked": int(values["release_arb_decisions"]),
            "release_source_handshakes_checked": int(values["release_source_fires"]),
            "eager_arbiter_decisions_checked": int(values["eager_arb_decisions"]),
            "exact_traffic": {
                "vc0_contexts": 112,
                "vc0_packets": 7616,
                "vc0_flits": 60928,
                "vc1_groups": 4,
                "vc1_rows": 512,
                "vc1_packets": 1260,
                "vc1_flits": 10020,
            },
            "payload_check": "all_vc0_flits_and_all_512_exact_vc1_rows",
            "perf_rtl_equivalence": (
                "all_release_source_valid_handshakes_and_all_endpoint_vc_arbiter_cycle_decisions"
            ),
            "protocol_errors": 0,
        },
        "host_runtime_seconds": {
            "compile": float(values["compile_s"]),
            "eager_replay": float(values["run_s"]),
            "eager_envelope": float(values["envelope_s"]),
        },
        "test_log": {
            "stdout_sha256": hashlib.sha256(pytest_stdout.encode("utf-8")).hexdigest(),
            "stderr_sha256": hashlib.sha256(pytest_stderr.encode("utf-8")).hexdigest(),
        },
        "interpretation": {
            "proves": [
                "measured p54/p53 output rows are not injected before their source release cycles",
                "downstream stalls retain one beat and dilate later releases without an unbounded replay queue",
                "the full exact VC0 and stats-once VC1 payloads traverse one shared registered-credit mesh",
                "the Python endpoint VC arbiter agrees with every recorded RTL arbitration cycle",
            ],
            "does_not_prove": replay["remaining_abstractions"],
        },
        "next_gate": (
            "Wire VC0 destination SRAM residency into each cluster fill interface, then replay the "
            "producer/reducer/shared-mesh path without trace-derived VC1 sources."
        ),
    }


def render_markdown(result: JsonDict) -> str:
    observation = result["rtl_observation"]
    lines = [
        "# Llama7B Exact Shared-Mesh Release-Coupled RTL",
        "",
        f"- decision: `{result['decision']}`",
        f"- completion: `{observation['service_cycles']}` cycles",
        f"- VC0 completion: `{observation['vc0_done_cycle']}` cycles",
        f"- VC1 completion: `{observation['vc1_done_cycle']}` cycles",
        f"- eager capacity envelope: `{observation['standalone_eager_envelope_cycles']}` cycles",
        "",
        "## Proves",
        "",
        *[f"- {item}" for item in result["interpretation"]["proves"]],
        "",
        "## Does Not Prove",
        "",
        *[f"- {item}" for item in result["interpretation"]["does_not_prove"]],
        "",
        "## Next Gate",
        "",
        result["next_gate"],
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cadence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path)
    parser.add_argument("--timeout-sec", type=int, default=3600)
    args = parser.parse_args(argv)

    cadence_path = args.cadence.resolve()
    cadence = json.loads(cadence_path.read_text(encoding="utf-8"))
    replay = build_replay(cadence, cadence_path=cadence_path)
    with tempfile.TemporaryDirectory(prefix="score32_release_replay_") as temp_name:
        temp = Path(temp_name)
        replay_path = temp / "replay.json"
        p54_memh = temp / "p54.memh"
        p53_memh = temp / "p53.memh"
        prepare_replay(
            [
                "--cadence",
                str(cadence_path),
                "--out",
                str(replay_path),
                "--p54-memh",
                str(p54_memh),
                "--p53-memh",
                str(p53_memh),
            ]
        )
        env = os.environ.copy()
        env["RTLGEN_RUN_SLOW_SHARED_MESH_FULL_REPLAY"] = "1"
        env["RTLGEN_RELEASE_CADENCE_JSON"] = str(cadence_path)
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-s",
                "tests/test_attention_score32_exact_dual_producer_shared_mesh4x4_full.py",
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=args.timeout_sec,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "release-coupled RTL gate failed\n"
                f"stdout:\n{completed.stdout}\n"
                f"stderr:\n{completed.stderr}"
            )
        result = build_result(
            replay=replay,
            cadence_path=cadence_path,
            pytest_stdout=completed.stdout,
            pytest_stderr=completed.stderr,
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.out_md is not None:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(render_markdown(result), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

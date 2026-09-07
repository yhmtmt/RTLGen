#!/usr/bin/env python3
"""Replay all collected cluster numerical payloads through the shared mesh."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from npu.eval.numerical_mesh_sidecars import build_sidecars
from tests import test_attention_score32_exact_dual_producer_shared_mesh4x4_full as gate


def run(collection: Path) -> dict:
    report = json.loads(collection.read_text())
    sidecars = build_sidecars(report)
    sources = [collection.resolve(), Path(__file__).resolve(), gate.TB,
        Path(gate.__file__), ROOT / "npu/eval/numerical_mesh_sidecars.py",
        ROOT / "npu/eval/cluster_numerical_payload.py", *gate.RTL_SOURCES, gate.FAKERAM_MODEL]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    with tempfile.TemporaryDirectory(prefix="numerical_mesh_") as name:
        work = Path(name)
        tree = gate._generate_tree(work)
        binary = work / "simv"
        command = [str(gate._tool("iverilog")), "-g2012", "-s", gate.TOP,
            "-o", str(binary), str(tree / "top.v"),
            *map(str, gate.RTL_SOURCES), str(gate.FAKERAM_MODEL), str(gate.TB)]
        compiled = subprocess.run(command, capture_output=True, text=True, timeout=600)
        if compiled.returncode:
            raise RuntimeError(compiled.stderr)
        args = [str(gate._tool("vvp")), str(binary), "+RELEASE_CADENCE", "+NUMERICAL_PAYLOAD",
            f"+NUMERICAL_COMMAND_BASE={sidecars['command_base']}"]
        for kind in ("leaf", "root", "release"):
            path = work / f"{kind}.memh"
            path.write_text(sidecars[f"{kind}_memh"])
            args.append(f"+NUMERICAL_{kind.upper()}={path}")
        arb, release = work / "arb.trace", work / "release.trace"
        args.extend([f"+ARB_TRACE={arb}", f"+RELEASE_TRACE={release}"])
        result = subprocess.run(args, capture_output=True, text=True, timeout=1800)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        match = gate.PASS_RE.search(result.stdout)
        if match is None:
            raise ValueError("numerical mesh PASS summary absent")
        observation = {key: int(value) for key, value in match.groupdict().items()}
        assert observation["vc1_rows"] == 512 and observation["release_coupled"] == 1
        assert observation["vc0_flits"] == 60928 and observation["vc1_flits"] == 10020
        decisions = gate._assert_arbiter_trace_matches_model(arb)
        cycles = [int(c, 16) for c in sidecars["release_memh"].splitlines()]
        fires = gate._assert_release_trace_matches_model(release, {
            "endpoint_release_cycles": [cycles[i*512:(i+1)*512] for i in range(16)]})
        assert fires == 8192
    for path, digest in hashes.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"source changed during replay: {path}")
    return {"model": "score32_numerical_mesh_replay_v1", "passed": True,
        "source_hashes": hashes, "observation": observation,
        "source_handshakes_checked": fires, "arbitration_decisions_checked": decisions,
        "scope": "collected exact leaf values through mesh; trace-coupled timing, historical VC0, no physical/CDC claim"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.collection)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")

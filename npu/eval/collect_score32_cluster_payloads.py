#!/usr/bin/env python3
"""Collect exact numerical outputs from all sixteen concrete cluster replays."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from npu.eval import probe_llama7b_score32_exact_cluster_release_cadence as cadence
from npu.eval.cluster_numerical_payload import pack_all_endpoints


def collect(config_path: Path, *, compile_timeout: int, run_timeout: int) -> dict:
    config_path = config_path.resolve()
    sources = [Path(__file__).resolve(), config_path,
        ROOT / "npu/eval/cluster_numerical_payload.py",
        ROOT / "npu/eval/probe_llama7b_score32_exact_cluster_release_cadence.py",
        ROOT / "npu/eval/gqa8_compositional_exact.py",
        ROOT / "npu/eval/probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8.py",
        ROOT / "npu/rtlgen/gen_attention_score32_exact_local16_global_tree_cluster_sram_gqa8.py"]
    identities = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    config = json.loads(config_path.read_text())
    observations = []
    with tempfile.TemporaryDirectory(prefix="score32_all_cluster_payloads_") as name:
        work = Path(name)
        rtl = cadence._prepare_guarded_rtl(config, work)
        memories = cadence._write_behavioral_memories(work)
        generated = (rtl / "top.v").read_text()
        names = cadence.probe._hierarchical_module_names(config["top_name"])
        print("Building exact reference for all endpoints", flush=True)
        reference = cadence.probe._reference(logical_head_groups=4)
        for producers in (54, 53):
            kind = f"p{producers}_cluster"
            build = work / kind
            source = build / "rtl"
            source.mkdir(parents=True)
            top = f"cadence_{kind}"
            (source / "top.v").write_text(cadence._alias_module_family(
                cadence.extract_module_family(generated, prefix=names[kind]),
                prefix=names[kind], alias=top))
            tb = build / "tb.sv"
            tb.write_text(cadence.cluster_testbench(top_name=top, producers=producers,
                logical_head_groups=4, output_ready_pattern=(True,)))
            control = build / "cluster.vlt"
            control.write_text(cadence._verilator_control_file_text(top))
            obj = build / "obj"
            print(f"Compiling {kind}", flush=True)
            for index, command in enumerate(cadence._verilator_two_stage_commands(
                rtl_dir=source, fakeram_path=memories, tb_path=tb,
                control_path=control, obj_dir=obj)):
                _, failure = cadence._run_process(command, cwd=build,
                    timeout_sec=compile_timeout, phase=f"compile_{kind}_{index}")
                if failure:
                    raise RuntimeError(cadence._diagnostic(failure))
            for endpoint, count in enumerate(cadence.probe.CLUSTER_PRODUCERS):
                if count != producers:
                    continue
                run = build / f"endpoint_{endpoint}"
                run.mkdir()
                print(f"Replaying endpoint {endpoint}", flush=True)
                cadence._write_cluster_sidecars(run, cluster=endpoint, logical_head_groups=4)
                result, failure = cadence._run_process(
                    [str(obj / cadence.probe.VERILATOR_BINARY_NAME), f"+CLUSTER={endpoint}"],
                    cwd=run, timeout_sec=run_timeout, phase=f"run_cluster_{endpoint}")
                if failure:
                    raise RuntimeError(cadence._diagnostic(failure))
                observations.append(cadence.extract_cluster_cadence(result.stdout,
                    cluster=endpoint, expected_rows=reference["cluster_rows"][endpoint]))
                print(f"Endpoint {endpoint}: exact rows verified", flush=True)
    words = pack_all_endpoints(observations)
    for path, expected in identities.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"source changed during collection: {path}")
    return {"model": "score32_all_cluster_numerical_payloads_v1", "passed": True,
        "source_identities": identities, "clusters": sorted(observations, key=lambda x: x["cluster"]),
        "packed_word_count": len(words), "expected_root_rows": reference["root_rows"],
        "scope": "sixteen separate concrete RTL replays; mesh transport and physical closure pending"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=cadence.DEFAULT_CONFIG)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--compile-timeout", type=int, default=3600)
    parser.add_argument("--run-timeout", type=int, default=1800)
    args = parser.parse_args()
    result = collect(args.config, compile_timeout=args.compile_timeout, run_timeout=args.run_timeout)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()

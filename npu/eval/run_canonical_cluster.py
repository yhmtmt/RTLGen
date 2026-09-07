#!/usr/bin/env python3
"""Concurrent p54/p53 cluster replay using canonical tensor sidecars."""
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
from npu.eval.canonical_attention_cluster_reference import canonical_cluster_rows
from npu.eval.collect_score32_cluster_payloads import loaded_project_sources
from npu.sim.perf.canonical_attention_fixture import CanonicalAttentionFixture


def run():
    fixture = CanonicalAttentionFixture()
    config_path = cadence.DEFAULT_CONFIG
    sources = loaded_project_sources() | {Path(__file__).resolve(), config_path}
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sources)}
    config = json.loads(config_path.read_text())
    observations = []
    generated_hashes = {}
    with tempfile.TemporaryDirectory(prefix="canonical_concurrent_cluster_") as name:
        work = Path(name)
        rtl = cadence._prepare_guarded_rtl(config, work)
        memories = cadence._write_behavioral_memories(work)
        generated = (rtl / "top.v").read_text()
        names = cadence.probe._hierarchical_module_names(config["top_name"])
        for endpoint, producers in ((0,54),(8,53)):
            kind = f"p{producers}_cluster"
            build = work / kind
            source = build / "rtl"
            source.mkdir(parents=True)
            top = f"canonical_{kind}"
            (source / "top.v").write_text(cadence._alias_module_family(
                cadence.extract_module_family(generated, prefix=names[kind]), prefix=names[kind], alias=top))
            tb = build / "tb.sv"
            tb.write_text(cadence.cluster_testbench(top_name=top, producers=producers,
                logical_head_groups=4, output_ready_pattern=(True,)))
            control = build / "cluster.vlt"
            control.write_text(cadence._verilator_control_file_text(top))
            obj = build / "obj"
            for path in (source / "top.v", tb, control, memories):
                generated_hashes[str(path.relative_to(work))] = hashlib.sha256(path.read_bytes()).hexdigest()
            print(f"Compiling canonical {kind}", flush=True)
            for index, command in enumerate(cadence._verilator_two_stage_commands(
                    rtl_dir=source, fakeram_path=memories, tb_path=tb, control_path=control, obj_dir=obj)):
                _, failure = cadence._run_process(command, cwd=build, timeout_sec=3600, phase=f"compile_{kind}_{index}")
                if failure:
                    raise RuntimeError(cadence._diagnostic(failure))
            print(f"Building canonical reference and sidecars for endpoint {endpoint}", flush=True)
            expected = canonical_cluster_rows(cluster=endpoint, fixture=fixture)
            run_dir = build / "run"
            run_dir.mkdir()
            cadence._write_cluster_sidecars(run_dir, cluster=endpoint, logical_head_groups=4, canonical_fixture=fixture)
            for path in sorted(run_dir.glob("*.memh")):
                generated_hashes[str(path.relative_to(work))] = hashlib.sha256(path.read_bytes()).hexdigest()
            print(f"Replaying all {producers} concurrent producers for endpoint {endpoint}", flush=True)
            result, failure = cadence._run_process([str(obj / cadence.probe.VERILATOR_BINARY_NAME), f"+CLUSTER={endpoint}"],
                cwd=run_dir, timeout_sec=1800, phase=f"canonical_cluster_{endpoint}")
            if failure:
                raise RuntimeError(cadence._diagnostic(failure))
            observations.append(cadence.extract_cluster_cadence(result.stdout, cluster=endpoint, expected_rows=expected))
            print(f"Endpoint {endpoint}: 512 canonical numerical rows verified", flush=True)
        for path, digest in generated_hashes.items():
            if hashlib.sha256((work / path).read_bytes()).hexdigest() != digest:
                raise RuntimeError(f"generated input changed during replay: {path}")
    if not loaded_project_sources().issubset(sources):
        raise RuntimeError("new unpinned project dependency loaded during replay")
    for path, digest in hashes.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"source changed during replay: {path}")
    return {"passed": True, "source_hashes": hashes, "generated_hashes": generated_hashes,
        "clusters": observations, "scope": "Two separate concurrent cluster RTL runs with canonical sidecar inputs; not live ingress or shared mesh, technology SRAM, workload recost, or PPA."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.out.write_text(json.dumps(result, indent=2) + "\n")

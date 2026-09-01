#!/usr/bin/env python3
"""Measure exact p54/p53 cluster output cadence for shared-mesh release."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
from typing import Any

from npu.eval import probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 as probe
from npu.eval.check_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_guard import (
    main as strict_guard_main,
)
from npu.eval.gqa8_compositional_exact import (
    _diagnostic,
    _run_process,
    _write_cluster_sidecars,
    cluster_testbench,
    extract_module_family,
)
from npu.rtlgen.gen_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 import (
    generate,
)


JsonDict = dict[str, Any]
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / Path(
    "runs/designs/npu_blocks/"
    "attention_score32_exact_local16_global_tree_cluster_sram_gqa8_p54x8_p53x8_c16_r2_l8_b59/"
    "config.json"
)
REPRESENTATIVE_CLUSTERS = (0, 8)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def extract_cluster_cadence(
    stdout: str,
    *,
    cluster: int,
    logical_head_groups: int = 4,
    expected_rows: list[dict[str, object]] | None = None,
) -> JsonDict:
    """Validate one cluster replay and retain per-group output cycles."""

    _summary, summaries, cluster_rows, _root_rows, timeout_cycle = probe._parse_stdout(stdout)
    if timeout_cycle is not None:
        raise ValueError(f"cluster {cluster} timed out at cycle {timeout_cycle}")
    if len(summaries) != 1 or int(summaries[0]["cluster"]) != cluster:
        raise ValueError(f"cluster {cluster} replay lacks one matching summary")
    rows = cluster_rows[cluster]
    if expected_rows is None:
        reference = probe._reference(logical_head_groups=logical_head_groups)
        expected_rows = reference["cluster_rows"][cluster]
    audit = probe.compare_full_rows(expected_rows, rows)
    if not audit["passed"]:
        raise ValueError(f"cluster {cluster} exact-row mismatch: {audit['first_mismatch']}")

    cycles_by_command: dict[int, list[int]] = {}
    for match in probe._CLUSTER_RESULT_RE.finditer(stdout):
        if int(match.group(1)) != cluster:
            continue
        cycles_by_command.setdefault(int(match.group(2)), []).append(int(match.group(9)))

    commands = probe._logical_commands(logical_head_groups=logical_head_groups)
    groups = []
    for command in commands:
        command_id = int(command["command_id"])
        cycles = cycles_by_command.get(command_id, [])
        if len(cycles) != probe.EXPECTED_PER_CLUSTER["emitted_beat_count"]:
            raise ValueError(
                f"cluster {cluster} command {command_id} has {len(cycles)} output cycles"
            )
        if any(next_cycle <= cycle for cycle, next_cycle in zip(cycles, cycles[1:])):
            raise ValueError(
                f"cluster {cluster} command {command_id} output cycles are not increasing"
            )
        groups.append(
            {
                "logical_group": int(command["logical_index"]),
                "command_id": command_id,
                "head_base": int(command["head_base"]),
                "first_output_cycle": min(cycles),
                "last_output_cycle": max(cycles),
                "output_span_cycles": max(cycles) - min(cycles) + 1,
                "output_rows": len(cycles),
                "output_cycles": cycles,
            }
        )

    summary = summaries[0]
    expected_commands = logical_head_groups * probe.WAVES
    if (
        int(summary["wave_command_accept_count"]) != expected_commands
        or int(summary["completed_command_count"]) != logical_head_groups
        or int(summary["emitted_beat_count"])
        != logical_head_groups * probe.EXPECTED_PER_CLUSTER["emitted_beat_count"]
        or int(summary["errors"]) != 0
    ):
        raise ValueError(f"cluster {cluster} count/error contract failed: {summary}")

    return {
        "cluster": cluster,
        "producer_count": probe.CLUSTER_PRODUCERS[cluster],
        "passed": True,
        "exact_row_audit": audit,
        "summary": summary,
        "groups": groups,
        "last_output_cycle": max(group["last_output_cycle"] for group in groups),
    }


def measure(
    config: JsonDict,
    *,
    config_path: Path,
    backend: str,
    compile_timeout_sec: int,
    simulation_timeout_sec: int,
) -> JsonDict:
    if backend not in {"iverilog", "verilator"}:
        raise ValueError("backend must be iverilog or verilator")
    resolved_config_path = config_path.resolve()
    relative_config_path = resolved_config_path.relative_to(REPO_ROOT)
    logical_head_groups = 4
    top_name = str(config["top_name"])
    modules = probe._hierarchical_module_names(top_name)
    fakeram_path = REPO_ROOT / "npu/sim/rtl/fakeram45_64x32_model.sv"

    with tempfile.TemporaryDirectory(prefix="score32_cluster_release_cadence_") as temp_name:
        work_dir = Path(temp_name)
        rtl_dir = work_dir / "rtl"
        generate(config, rtl_dir)
        with contextlib.redirect_stdout(io.StringIO()):
            strict_guard_main(
                ["--design-dir", str(work_dir), "--config", str(rtl_dir / "config.json")]
            )

        generated_rtl = (rtl_dir / "top.v").read_text(encoding="utf-8")
        reference = probe._reference(logical_head_groups=logical_head_groups)
        observations = []
        phase_records = [{"phase": "strict_generated_top_guard", "returncode": 0}]
        for cluster in REPRESENTATIVE_CLUSTERS:
            producers = probe.CLUSTER_PRODUCERS[cluster]
            kind = "p54_cluster" if producers == 54 else "p53_cluster"
            build_dir = work_dir / kind
            source_dir = build_dir / "rtl"
            run_dir = build_dir / "run"
            source_dir.mkdir(parents=True)
            run_dir.mkdir()
            (source_dir / "top.v").write_text(
                extract_module_family(generated_rtl, prefix=modules[kind]),
                encoding="utf-8",
            )
            tb_path = build_dir / "tb.sv"
            obj_dir = build_dir / "obj_dir"
            sim_path = build_dir / "simv"
            tb_path.write_text(
                cluster_testbench(
                    top_name=modules[kind],
                    producers=producers,
                    logical_head_groups=logical_head_groups,
                    output_ready_pattern=(True,),
                ),
                encoding="ascii",
            )
            _write_cluster_sidecars(
                run_dir,
                cluster=cluster,
                logical_head_groups=logical_head_groups,
            )
            if backend == "verilator":
                control_path = build_dir / "cluster.vlt"
                control_path.write_text(
                    "`verilator_config\n"
                    f'hier_block -module "{modules[kind]}"\n',
                    encoding="ascii",
                )
                command = probe._verilator_hierarchical_compile_command(
                    rtl_dir=source_dir,
                    fakeram_path=fakeram_path,
                    tb_path=tb_path,
                    control_path=control_path,
                    obj_dir=obj_dir,
                )
                run_command = [
                    str(obj_dir / probe.VERILATOR_BINARY_NAME),
                    f"+CLUSTER={cluster}",
                ]
            else:
                command = probe._icarus_compile_command(
                    rtl_dir=source_dir,
                    fakeram_path=fakeram_path,
                    tb_path=tb_path,
                    sim_path=sim_path,
                )
                run_command = [probe._tool("vvp"), str(sim_path), f"+CLUSTER={cluster}"]
            _result, failure = _run_process(
                command,
                cwd=build_dir,
                timeout_sec=compile_timeout_sec,
                phase=f"compile_{kind}",
            )
            phase_records.append(
                {
                    "phase": f"compile_{kind}",
                    "returncode": failure["returncode"] if failure else 0,
                }
            )
            if failure:
                raise RuntimeError(_diagnostic(failure))
            result, failure = _run_process(
                run_command,
                cwd=run_dir,
                timeout_sec=simulation_timeout_sec,
                phase=f"run_cluster_{cluster}",
            )
            phase_records.append(
                {
                    "phase": f"run_cluster_{cluster}",
                    "returncode": failure["returncode"] if failure else 0,
                }
            )
            if failure:
                raise RuntimeError(_diagnostic(failure))
            observations.append(
                extract_cluster_cadence(
                    result.stdout or "",
                    cluster=cluster,
                    logical_head_groups=logical_head_groups,
                    expected_rows=reference["cluster_rows"][cluster],
                )
            )

    source_paths = (
        Path("npu/eval/probe_llama7b_score32_exact_cluster_release_cadence.py"),
        Path("npu/eval/gqa8_compositional_exact.py"),
        Path("npu/eval/probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8.py"),
        Path("npu/rtlgen/gen_attention_score32_exact_local16_global_tree_cluster_sram_gqa8.py"),
    )
    return {
        "version": 1,
        "model": "llama7b_score32_exact_cluster_release_cadence_v1",
        "passed": True,
        "decision": "representative_p54_p53_cluster_release_cadence_measured",
        "precision": "score32_exact_gqa8_full_head_dimension_128",
        "clock_domain": "generated_cluster_single_clock",
        "simulation_backend": backend,
        "logical_head_groups": logical_head_groups,
        "persistent_waves_per_group": probe.WAVES,
        "representative_clusters": observations,
        "conservative_group_ready_cycles": [
            max(row["groups"][group]["first_output_cycle"] for row in observations)
            for group in range(logical_head_groups)
        ],
        "conservative_group_complete_cycles": [
            max(row["groups"][group]["last_output_cycle"] for row in observations)
            for group in range(logical_head_groups)
        ],
        "phase_records": phase_records,
        "source_identities": {
            "config_path": relative_config_path.as_posix(),
            "config_file_sha256": _sha256(resolved_config_path),
            "config_canonical_sha256": hashlib.sha256(
                json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
            "files": {
                path.as_posix(): _sha256(REPO_ROOT / path) for path in source_paths
            },
        },
        "remaining_abstractions": [
            "The p54 and p53 wrappers cover the two distinct cluster structures; all sixteen physical copies are not replayed.",
            "External HBM/DRAM return timing remains outside the cluster and is represented by the explicit fill valid/ready plane.",
            "The measured cluster release cycles must be converted to the independently clocked shared-mesh domain and replayed against the exact dual-producer RTL before throughput promotion.",
        ],
    }


def render_markdown(report: JsonDict) -> str:
    lines = [
        "# Llama7B Score32 Exact Cluster Release Cadence",
        "",
        f"- decision: `{report['decision']}`",
        f"- precision: `{report['precision']}`",
        f"- conservative group ready cycles: `{report['conservative_group_ready_cycles']}`",
        f"- conservative group complete cycles: `{report['conservative_group_complete_cycles']}`",
        "",
        "| Cluster | Producers | Group | Head base | First output | Last output | Rows |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for cluster in report["representative_clusters"]:
        for group in cluster["groups"]:
            lines.append(
                f"| {cluster['cluster']} | {cluster['producer_count']} | "
                f"{group['logical_group']} | {group['head_base']} | "
                f"{group['first_output_cycle']} | {group['last_output_cycle']} | "
                f"{group['output_rows']} |"
            )
    lines.extend(("", "## Remaining Abstractions", ""))
    lines.extend(f"- {item}" for item in report["remaining_abstractions"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path)
    parser.add_argument("--backend", choices=("iverilog", "verilator"), default="verilator")
    parser.add_argument("--compile-timeout-sec", type=int, default=3600)
    parser.add_argument("--simulation-timeout-sec", type=int, default=3600)
    args = parser.parse_args()

    if not args.config.is_file():
        raise FileNotFoundError(f"checked-in config not found: {args.config}")
    config = json.loads(args.config.read_text(encoding="utf-8"))
    report = measure(
        config,
        config_path=args.config,
        backend=str(args.backend),
        compile_timeout_sec=int(args.compile_timeout_sec),
        simulation_timeout_sec=int(args.simulation_timeout_sec),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.out_md is not None:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

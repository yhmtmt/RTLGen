#!/usr/bin/env python3
"""
Proposal-scoped quality precheck for terminal softmax routing changes.

This command is intentionally narrow. It is meant for proposals that do not
change softmax math, only the terminal storage path. It proves that:

1. pre-softmax compute ops are unchanged,
2. the terminal softmax parameters are unchanged,
3. the candidate removes only the final DMA hop, and
4. perf traces reflect exactly that bounded change.
"""

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml  # type: ignore


REPO_ROOT = Path(__file__).resolve().parents[2]


def rel_to_repo(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except Exception:
        return str(path.resolve())


def run_cmd(cmd: List[str]) -> None:
    subprocess.run(cmd, cwd=str(REPO_ROOT), check=True)


def load_yaml(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_op_for_compare(op: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in op.items() if k != "dst"}


def _op_by_id(schedule: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(op.get("id")): op for op in schedule.get("ops", [])}


def _find_terminal_softmax(schedule: Dict[str, Any]) -> Dict[str, Any]:
    softmax_ops = [op for op in schedule.get("ops", []) if str(op.get("type")) == "softmax"]
    if len(softmax_ops) != 1:
        raise ValueError(f"expected exactly one softmax op, found {len(softmax_ops)}")
    return softmax_ops[0]


def _find_dma_y(schedule: Dict[str, Any]) -> Dict[str, Any]:
    for op in schedule.get("ops", []):
        if str(op.get("id")) == "dma_y":
            return op
    raise ValueError("baseline schedule missing dma_y")


def _find_event_target(schedule: Dict[str, Any]) -> str:
    events = schedule.get("events", [])
    if len(events) != 1:
        raise ValueError(f"expected exactly one terminal event, found {len(events)}")
    return str(events[0].get("signal_on", ""))


def _build_artifacts(
    *,
    onnx_path: str,
    arch_path: str,
    perf_config: str,
    batch_override: int | None,
    work_dir: Path,
    label: str,
) -> Tuple[Path, Path, Path]:
    schedule = work_dir / f"{label}_schedule.yml"
    descriptors = work_dir / f"{label}_descriptors.bin"
    trace = work_dir / f"{label}_trace.json"

    mapper_cmd = [
        "python3",
        "npu/mapper/onnx_to_schedule.py",
        "--onnx",
        onnx_path,
        "--arch",
        arch_path,
        "--out",
        str(schedule),
    ]
    if batch_override is not None:
        mapper_cmd.extend(["--batch-override", str(int(batch_override))])
    run_cmd(mapper_cmd)
    run_cmd(
        [
            "python3",
            "npu/mapper/run.py",
            str(schedule),
            "--out-bin",
            str(descriptors),
        ]
    )
    run_cmd(
        [
            "python3",
            "npu/sim/perf/run.py",
            "--bin",
            str(descriptors),
            "--out",
            str(trace),
            "--config",
            perf_config,
            "--summary",
            "--overlap",
        ]
    )
    return schedule, descriptors, trace


def compare_terminal_softmax_quality(
    *,
    onnx_path: str,
    baseline_arch: str,
    candidate_arch: str,
    perf_config: str,
    batch_override: int | None,
    artifact_dir: Path | None = None,
) -> Dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="rtlgen-softmax-quality-") as tmpdir:
        tmp = Path(tmpdir)
        base_schedule_path, base_desc_path, base_trace_path = _build_artifacts(
            onnx_path=onnx_path,
            arch_path=baseline_arch,
            perf_config=perf_config,
            batch_override=batch_override,
            work_dir=tmp,
            label="baseline",
        )
        cand_schedule_path, cand_desc_path, cand_trace_path = _build_artifacts(
            onnx_path=onnx_path,
            arch_path=candidate_arch,
            perf_config=perf_config,
            batch_override=batch_override,
            work_dir=tmp,
            label="candidate",
        )

        base_schedule = load_yaml(base_schedule_path)
        cand_schedule = load_yaml(cand_schedule_path)
        base_trace = load_json(base_trace_path)
        cand_trace = load_json(cand_trace_path)

        persisted: Dict[str, str] = {}
        if artifact_dir is not None:
            artifact_dir.mkdir(parents=True, exist_ok=True)
            for src_path, key in (
                (base_schedule_path, "baseline_schedule"),
                (cand_schedule_path, "candidate_schedule"),
                (base_desc_path, "baseline_descriptors"),
                (cand_desc_path, "candidate_descriptors"),
                (base_trace_path, "baseline_trace"),
                (cand_trace_path, "candidate_trace"),
            ):
                dst_path = artifact_dir / src_path.name
                shutil.copy2(src_path, dst_path)
                persisted[key] = rel_to_repo(dst_path)

    base_softmax = _find_terminal_softmax(base_schedule)
    cand_softmax = _find_terminal_softmax(cand_schedule)
    base_dma_y = _find_dma_y(base_schedule)

    base_ops = _op_by_id(base_schedule)
    cand_ops = _op_by_id(cand_schedule)

    failures: List[str] = []

    for op_id in ("dma_x", "dma_w1", "dma_b1", "gemm1"):
        if base_ops.get(op_id) != cand_ops.get(op_id):
            failures.append(f"op {op_id} differs between baseline and candidate")

    base_softmax_cmp = _normalize_op_for_compare(base_softmax)
    cand_softmax_cmp = _normalize_op_for_compare(cand_softmax)
    if base_softmax_cmp != cand_softmax_cmp:
        failures.append("terminal softmax parameters changed beyond dst routing")

    if str(base_dma_y.get("src")) != str(base_softmax.get("dst")):
        failures.append("baseline dma_y src does not match baseline softmax dst")
    if str(base_dma_y.get("dst")) != "Y_DRAM":
        failures.append("baseline dma_y dst is not Y_DRAM")
    if str(cand_softmax.get("dst")) != "Y_DRAM":
        failures.append("candidate softmax dst is not Y_DRAM")
    if "dma_y" in cand_ops:
        failures.append("candidate still contains dma_y")

    if _find_event_target(base_schedule) != "dma_y":
        failures.append("baseline terminal event is not dma_y")
    if _find_event_target(cand_schedule) != "softmax1":
        failures.append("candidate terminal event is not softmax1")

    base_stats = dict(base_trace.get("stats", {}) or {})
    cand_stats = dict(cand_trace.get("stats", {}) or {})
    if int(base_stats.get("gemm_ops", 0)) != int(cand_stats.get("gemm_ops", 0)):
        failures.append("gemm op count differs in perf trace")
    if int(base_stats.get("softmax_ops", 0)) != int(cand_stats.get("softmax_ops", 0)):
        failures.append("softmax op count differs in perf trace")
    if int(base_stats.get("vec_ops", 0)) != int(cand_stats.get("vec_ops", 0)):
        failures.append("vec op count differs in perf trace")
    if int(base_stats.get("dma_ops", 0)) != int(cand_stats.get("dma_ops", 0)) + 1:
        failures.append("candidate perf trace does not remove exactly one DMA op")

    removed_dma_bytes = int(base_dma_y.get("bytes", 0))
    base_total_bytes = int(base_stats.get("total_bytes", 0))
    cand_total_bytes = int(cand_stats.get("total_bytes", 0))
    if base_total_bytes != cand_total_bytes + removed_dma_bytes:
        failures.append("candidate total_bytes does not match removal of terminal dma_y")

    base_softmax_trace = [ev for ev in base_trace.get("trace", []) if ev.get("name") == "SOFTMAX"]
    cand_softmax_trace = [ev for ev in cand_trace.get("trace", []) if ev.get("name") == "SOFTMAX"]
    if len(base_softmax_trace) != 1 or len(cand_softmax_trace) != 1:
        failures.append("expected exactly one SOFTMAX event in both perf traces")
    else:
        keys = ("row_bytes", "rows", "dtype", "duration_ns")
        for key in keys:
            if base_softmax_trace[0].get(key) != cand_softmax_trace[0].get(key):
                failures.append(f"SOFTMAX trace field differs: {key}")

    return {
        "passed": not failures,
        "proposal_scope": "terminal_softmax_routing_only",
        "inputs": {
            "onnx_path": onnx_path,
            "baseline_arch": baseline_arch,
            "candidate_arch": candidate_arch,
            "perf_config": perf_config,
            "batch_override": batch_override,
        },
        "summary": {
            "baseline_event_target": _find_event_target(base_schedule),
            "candidate_event_target": _find_event_target(cand_schedule),
            "baseline_softmax_dst": str(base_softmax.get("dst")),
            "candidate_softmax_dst": str(cand_softmax.get("dst")),
            "baseline_dma_ops": int(base_stats.get("dma_ops", 0)),
            "candidate_dma_ops": int(cand_stats.get("dma_ops", 0)),
            "baseline_total_bytes": base_total_bytes,
            "candidate_total_bytes": cand_total_bytes,
            "removed_dma_bytes": removed_dma_bytes,
            "baseline_schedule": persisted.get("baseline_schedule", ""),
            "candidate_schedule": persisted.get("candidate_schedule", ""),
            "baseline_descriptors": persisted.get("baseline_descriptors", ""),
            "candidate_descriptors": persisted.get("candidate_descriptors", ""),
            "baseline_trace": persisted.get("baseline_trace", ""),
            "candidate_trace": persisted.get("candidate_trace", ""),
        },
        "checks": {
            "pre_softmax_ops_match": "op dma_x/dma_w1/dma_b1/gemm1 identical",
            "terminal_softmax_params_match": "softmax src/row_bytes/rows/dtype unchanged",
            "routing_only_delta": "candidate routes softmax directly to Y_DRAM and removes dma_y",
            "perf_delta_bounded": "perf trace removes exactly one DMA op and one dma_y byte transfer",
        },
        "failures": failures,
    }


def render_markdown(result: Dict[str, Any]) -> str:
    lines = [
        "# Terminal Softmax Quality Precheck",
        "",
        f"- status: {'pass' if result['passed'] else 'fail'}",
        f"- scope: `{result['proposal_scope']}`",
        "",
        "## Inputs",
    ]
    for key, value in result["inputs"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Summary",
        ]
    )
    for key, value in result["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Checks",
        ]
    )
    for key, value in result["checks"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Failures",
        ]
    )
    if result["failures"]:
        for failure in result["failures"]:
            lines.append(f"- {failure}")
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Compare terminal softmax routing quality for a candidate arch.")
    ap.add_argument("--onnx", required=True, help="Input ONNX model")
    ap.add_argument("--baseline-arch", required=True, help="Accepted baseline architecture YAML")
    ap.add_argument("--candidate-arch", required=True, help="Candidate architecture YAML")
    ap.add_argument("--perf-config", required=True, help="Perf config JSON")
    ap.add_argument("--batch-override", type=int, help="Optional mapper batch override")
    ap.add_argument("--out-json", required=True, help="Output JSON report")
    ap.add_argument("--out-md", help="Optional output markdown report")
    ap.add_argument(
        "--artifact-dir",
        help="Optional durable artifact directory. Defaults to <out-json stem>_artifacts beside out-json.",
    )
    args = ap.parse_args()

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    artifact_dir = Path(args.artifact_dir) if args.artifact_dir else out_json.with_name(
        f"{out_json.stem}_artifacts"
    )

    result = compare_terminal_softmax_quality(
        onnx_path=args.onnx,
        baseline_arch=args.baseline_arch,
        candidate_arch=args.candidate_arch,
        perf_config=args.perf_config,
        batch_override=args.batch_override,
        artifact_dir=artifact_dir,
    )

    out_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    if args.out_md:
        out_md = Path(args.out_md)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(render_markdown(result), encoding="utf-8")

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

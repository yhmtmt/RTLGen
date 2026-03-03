#!/usr/bin/env python3
"""
Campaign runner scaffold for NPU end-to-end evaluation.

Flow (phase-2 scaffold):
  1) ONNX -> schedule.yml
  2) schedule.yml -> descriptors.bin
  3) physical metrics collection (reuse metrics.csv, optionally run sweep)
  4) perf sim trace generation
  5) merged result-row JSON + append-only flattened CSV
"""

import argparse
import csv
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from validate import load_json, validate_campaign, validate_result_row


REPO_ROOT = Path(__file__).resolve().parents[2]
VALID_MACRO_MODES = ("flat_nomacro", "hier_macro")


def die(msg: str) -> None:
    print(f"run_campaign: {msg}", file=sys.stderr)
    sys.exit(1)


def log(msg: str) -> None:
    print(f"[run_campaign] {msg}")


def run_cmd(cmd: List[str], *, dry_run: bool = False) -> None:
    pretty = " ".join(cmd)
    log(f"$ {pretty}")
    if dry_run:
        return
    subprocess.run(cmd, cwd=str(REPO_ROOT), check=True)


def abs_path(path_text: str) -> Path:
    p = Path(path_text)
    if p.is_absolute():
        return p
    return (REPO_ROOT / p).resolve()


def rel_to_repo(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except Exception:
        return str(path.resolve())


def safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def parse_repeat_index(tag: str) -> int:
    m = re.search(r"_r(\d+)$", str(tag or ""))
    if not m:
        return 1
    try:
        return max(1, int(m.group(1)))
    except Exception:
        return 1


def normalize_run_token(text: str, default: str = "na") -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "", str(text or "")).lower()
    return token or default


def make_run_id(
    *,
    campaign_id: str,
    model_id: str,
    arch_id: str,
    macro_mode: str,
    repeat_index: int,
    param_hash: str,
) -> str:
    return (
        f"{campaign_id}__{model_id}__{arch_id}__{macro_mode}"
        f"__r{repeat_index}__p{normalize_run_token(param_hash)}"
    )


def infer_macro_mode(row: Dict[str, Any]) -> str:
    mode_name = str(row.get("mode_name", "")).strip()
    if mode_name in VALID_MACRO_MODES:
        return mode_name

    params_text = str(row.get("params_json", "")).strip()
    if params_text:
        try:
            params = json.loads(params_text)
            if str(params.get("SYNTH_HIERARCHICAL", "0")).strip() in ("1", "true", "True"):
                return "hier_macro"
        except Exception:
            pass

    tag = str(row.get("tag", ""))
    if "hier_macro" in tag:
        return "hier_macro"
    return "flat_nomacro"


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_top_name_from_design(design_dir: Path) -> str:
    cfg = design_dir / "verilog" / "config.json"
    if not cfg.exists():
        return "npu_top"
    doc = load_json(cfg)
    top = str(doc.get("top_name", "")).strip()
    return top or "npu_top"


def parse_physical_row(raw: Dict[str, str]) -> Dict[str, Any]:
    work_result_json = str(raw.get("work_result_json", "")).strip()
    work_result_path = abs_path(work_result_json) if work_result_json else None
    work_doc = load_json(work_result_path) if work_result_path and work_result_path.exists() else {}

    flow_elapsed = safe_float(raw.get("flow_elapsed_seconds"))
    if flow_elapsed is None:
        flow_elapsed = safe_float(work_doc.get("flow_elapsed_seconds"))
    stage_elapsed = safe_float(raw.get("stage_elapsed_seconds"))
    if stage_elapsed is None:
        stage_elapsed = safe_float(work_doc.get("stage_elapsed_seconds"))

    result_path = str(raw.get("result_path", "")).strip()
    if not result_path:
        result_path = str(work_doc.get("result_path", "")).strip()

    status = str(raw.get("status", "")).strip() or str(work_doc.get("status", "")).strip() or "fail"
    tag = str(raw.get("tag", "")).strip() or str(work_doc.get("tag", "")).strip()
    param_hash = str(raw.get("param_hash", "")).strip() or str(work_doc.get("param_hash", "")).strip()
    compare_group = str(raw.get("compare_group", "")).strip() or str(work_doc.get("compare_group", "")).strip()
    params_text = str(raw.get("params_json", "")).strip() or str(work_doc.get("params_json", "")).strip()
    tag_prefix = ""
    if params_text:
        try:
            params = json.loads(params_text)
            tag_prefix = str(params.get("tag_prefix", "")).strip()
        except Exception:
            tag_prefix = ""

    repeat_match = re.search(r"_r(\d+)$", tag)
    return {
        "status": status,
        "tag": tag,
        "param_hash": param_hash,
        "compare_group": compare_group,
        "tag_prefix": tag_prefix,
        "macro_mode": infer_macro_mode(raw),
        "repeat_index": parse_repeat_index(tag),
        "has_repeat_suffix": bool(repeat_match),
        "critical_path_ns": safe_float(raw.get("critical_path_ns")),
        "die_area_um2": safe_float(raw.get("die_area")),
        "total_power_mw": safe_float(raw.get("total_power_mw")),
        "flow_elapsed_s": flow_elapsed,
        "place_gp_elapsed_s": stage_elapsed,
        "work_result_json": rel_to_repo(work_result_path) if work_result_path else "",
        "synth_result_json": result_path,
    }


def collect_physical_candidates(metrics_csv: Path) -> List[Dict[str, Any]]:
    rows = read_csv_rows(metrics_csv)
    out: List[Dict[str, Any]] = []
    for row in rows:
        out.append(parse_physical_row(row))
    return out


def row_matches_physical_select(row: Dict[str, Any], selector: Optional[Dict[str, Any]]) -> bool:
    if not selector:
        return True
    compare_group = str(selector.get("compare_group", "")).strip()
    tag_prefix = str(selector.get("tag_prefix", "")).strip()

    if compare_group:
        if str(row.get("compare_group", "")).strip() != compare_group:
            return False
    if tag_prefix:
        if not str(row.get("tag", "")).startswith(tag_prefix):
            return False
    return True


def select_physical_rows(
    candidates: List[Dict[str, Any]],
    *,
    modes: List[str],
    repeats: int,
    selector: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for mode in modes:
        mode_rows = [
            r
            for r in candidates
            if r.get("macro_mode") == mode
            and r.get("status") == "ok"
            and row_matches_physical_select(r, selector)
        ]
        mode_rows.sort(
            key=lambda r: (
                int(r.get("repeat_index", 1)),
                0 if bool(r.get("has_repeat_suffix")) else 1,
                0 if safe_float(r.get("flow_elapsed_s")) is not None else 1,
                0 if safe_float(r.get("place_gp_elapsed_s")) is not None else 1,
                str(r.get("tag", "")),
            )
        )
        if not mode_rows:
            continue

        by_repeat: Dict[int, Dict[str, Any]] = {}
        for row in mode_rows:
            idx = int(row.get("repeat_index", 1))
            if idx not in by_repeat:
                by_repeat[idx] = row

        picked: List[Dict[str, Any]] = []
        for idx in range(1, repeats + 1):
            if idx in by_repeat:
                picked.append(by_repeat[idx])
        if not picked:
            picked = mode_rows[:repeats]
        out.extend(picked)
    return out


def maybe_run_physical_sweep(
    *,
    campaign: Dict[str, Any],
    arch: Dict[str, Any],
    repeats: int,
    dry_run: bool,
) -> None:
    design_dir = str(arch["synth_design_dir"])
    sweep_file = str(arch["sweep_file"])
    platform = str(campaign["platform"])
    make_target = str(campaign["make_target"])
    top_name = load_top_name_from_design(abs_path(design_dir))

    cmd = [
        "python3",
        "npu/synth/run_block_sweep.py",
        "--design_dir",
        design_dir,
        "--platform",
        platform,
        "--top",
        top_name,
        "--sweep",
        sweep_file,
        "--repeat",
        str(repeats),
        "--skip_existing",
    ]
    if make_target:
        cmd.extend(["--make_target", make_target])
    macro_manifest = str(arch.get("macro_manifest", "")).strip()
    if macro_manifest:
        cmd.extend(["--macro_manifest", macro_manifest])

    run_cmd(cmd, dry_run=dry_run)


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return load_json(path)


def write_json(path: Path, doc: Dict[str, Any]) -> None:
    ensure_parent_dir(path)
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def can_reuse_artifact_set(
    *,
    outputs: List[Path],
    meta_path: Path,
    expected_meta: Dict[str, str],
) -> bool:
    if not all(p.exists() for p in outputs):
        return False
    if not meta_path.exists():
        return False
    meta_doc = read_json(meta_path)
    if not isinstance(meta_doc, dict):
        return False
    for k, v in expected_meta.items():
        if str(meta_doc.get(k, "")) != str(v):
            return False
    return True


def mapper_emit(
    *,
    model_id: str,
    model: Dict[str, Any],
    campaign_dir: Path,
    reuse_existing: bool,
    dry_run: bool,
) -> Tuple[str, str]:
    mapper_dir = campaign_dir / "artifacts" / "mapper" / model_id
    mapper_dir.mkdir(parents=True, exist_ok=True)
    schedule = mapper_dir / "schedule.yml"
    desc_bin = mapper_dir / "descriptors.bin"
    meta_path = mapper_dir / "meta.json"

    onnx_path = str(model.get("onnx_path", "")).strip()
    mapper_arch = str(model.get("mapper_arch", "")).strip()
    if not onnx_path:
        die(f"model {model_id}: missing onnx_path")
    if not mapper_arch:
        die(f"model {model_id}: missing mapper_arch")

    expected_meta = {
        "kind": "mapper",
        "model_id": model_id,
        "onnx_path": onnx_path,
        "mapper_arch": mapper_arch,
    }
    if reuse_existing and can_reuse_artifact_set(
        outputs=[schedule, desc_bin],
        meta_path=meta_path,
        expected_meta=expected_meta,
    ):
        log(
            "reuse mapper artifacts: "
            f"model_id={model_id} schedule={rel_to_repo(schedule)} "
            f"descriptors={rel_to_repo(desc_bin)}"
        )
        return rel_to_repo(schedule), rel_to_repo(desc_bin)

    run_cmd(
        [
            "python3",
            "npu/mapper/onnx_to_schedule.py",
            "--onnx",
            onnx_path,
            "--arch",
            mapper_arch,
            "--out",
            rel_to_repo(schedule),
        ],
        dry_run=dry_run,
    )
    run_cmd(
        [
            "python3",
            "npu/mapper/run.py",
            rel_to_repo(schedule),
            "--out-bin",
            rel_to_repo(desc_bin),
        ],
        dry_run=dry_run,
    )
    if not dry_run:
        write_json(
            meta_path,
            {
                **expected_meta,
                "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "schedule_yml": rel_to_repo(schedule),
                "descriptors_bin": rel_to_repo(desc_bin),
            },
        )
    return rel_to_repo(schedule), rel_to_repo(desc_bin)


def perf_emit(
    *,
    model_id: str,
    descriptors_bin: str,
    perf_config: str,
    campaign_dir: Path,
    reuse_existing: bool,
    dry_run: bool,
) -> Tuple[str, Dict[str, Any]]:
    perf_dir = campaign_dir / "artifacts" / "perf" / model_id
    perf_dir.mkdir(parents=True, exist_ok=True)
    trace_json = perf_dir / "trace.json"
    meta_path = perf_dir / "meta.json"

    expected_meta = {
        "kind": "perf",
        "model_id": model_id,
        "descriptors_bin": descriptors_bin,
        "perf_config": perf_config,
    }
    if reuse_existing and can_reuse_artifact_set(
        outputs=[trace_json],
        meta_path=meta_path,
        expected_meta=expected_meta,
    ):
        log(
            "reuse perf artifacts: "
            f"model_id={model_id} trace={rel_to_repo(trace_json)}"
        )
        trace_doc = read_json(trace_json) if not dry_run else {}
        stats = dict(trace_doc.get("stats", {}) or {})
        return rel_to_repo(trace_json), stats

    cmd = [
        "python3",
        "npu/sim/perf/run.py",
        "--bin",
        descriptors_bin,
        "--out",
        rel_to_repo(trace_json),
        "--overlap",
    ]
    if perf_config:
        cmd.extend(["--config", perf_config])
    run_cmd(cmd, dry_run=dry_run)

    stats: Dict[str, Any] = {}
    if not dry_run:
        trace_doc = read_json(trace_json)
        stats = dict(trace_doc.get("stats", {}) or {})
        write_json(
            meta_path,
            {
                **expected_meta,
                "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "trace_json": rel_to_repo(trace_json),
            },
        )

    return rel_to_repo(trace_json), stats


def build_model_artifacts(
    *,
    model: Dict[str, Any],
    campaign_dir: Path,
    reuse_existing: bool,
    dry_run: bool,
) -> Tuple[str, Dict[str, Any]]:
    model_id = str(model["model_id"])
    perf_config = str(model.get("perf_config", "")).strip()
    schedule_yml, descriptors_bin = mapper_emit(
        model_id=model_id,
        model=model,
        campaign_dir=campaign_dir,
        reuse_existing=reuse_existing,
        dry_run=dry_run,
    )
    perf_trace_json, perf_stats = perf_emit(
        model_id=model_id,
        descriptors_bin=descriptors_bin,
        perf_config=perf_config,
        campaign_dir=campaign_dir,
        reuse_existing=reuse_existing,
        dry_run=dry_run,
    )
    return model_id, {
        "schedule_yml": schedule_yml,
        "descriptors_bin": descriptors_bin,
        "perf_trace_json": perf_trace_json,
        "perf_stats": perf_stats,
    }


def flatten_row(row: Dict[str, Any]) -> Dict[str, Any]:
    physical = row.get("physical", {}) or {}
    performance = row.get("performance", {}) or {}
    artifacts = row.get("artifacts", {}) or {}
    return {
        "version": row.get("version"),
        "campaign_id": row.get("campaign_id"),
        "run_id": row.get("run_id"),
        "timestamp_utc": row.get("timestamp_utc"),
        "status": row.get("status"),
        "platform": row.get("platform"),
        "model_id": row.get("model_id"),
        "arch_id": row.get("arch_id"),
        "macro_mode": row.get("macro_mode"),
        "repeat_index": row.get("repeat_index"),
        "physical_critical_path_ns": physical.get("critical_path_ns"),
        "physical_die_area_um2": physical.get("die_area_um2"),
        "physical_total_power_mw": physical.get("total_power_mw"),
        "physical_flow_elapsed_s": physical.get("flow_elapsed_s"),
        "physical_place_gp_elapsed_s": physical.get("place_gp_elapsed_s"),
        "performance_cycles": performance.get("cycles"),
        "performance_latency_ms": performance.get("latency_ms"),
        "performance_throughput_infer_per_s": performance.get("throughput_infer_per_s"),
        "performance_energy_mj": performance.get("energy_mj"),
        "artifact_synth_result_json": artifacts.get("synth_result_json", ""),
        "artifact_perf_trace_json": artifacts.get("perf_trace_json", ""),
        "artifact_schedule_yml": artifacts.get("schedule_yml", ""),
        "artifact_descriptors_bin": artifacts.get("descriptors_bin", ""),
        "notes": row.get("notes", ""),
    }


def append_results_csv(results_csv: Path, row: Dict[str, Any]) -> None:
    flat = flatten_row(row)
    header = list(flat.keys())
    ensure_parent_dir(results_csv)

    if results_csv.exists():
        with results_csv.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            old_header = list(reader.fieldnames or [])
            old_rows = list(reader)
        if old_header == header:
            with results_csv.open("a", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=header)
                writer.writerow(flat)
            return

        merged_header = list(old_header)
        for key in header:
            if key not in merged_header:
                merged_header.append(key)
        with results_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=merged_header)
            writer.writeheader()
            for old in old_rows:
                writer.writerow({k: old.get(k, "") for k in merged_header})
            writer.writerow({k: flat.get(k, "") for k in merged_header})
        return

    with results_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerow(flat)


def load_existing_run_ids(results_csv: Path) -> set[str]:
    if not results_csv.exists():
        return set()
    with results_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        out = set()
        for row in reader:
            run_id = str(row.get("run_id", "")).strip()
            if run_id:
                out.add(run_id)
        return out


def safe_slug(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(text))
    s = s.strip("_")
    return s or "row"


def write_row_json(campaign_dir: Path, row: Dict[str, Any]) -> str:
    out_dir = campaign_dir / "artifacts" / "result_rows"
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = str(row.get("run_id", "run"))
    out_path = out_dir / f"{safe_slug(run_id)}.json"
    out_path.write_text(json.dumps(row, indent=2), encoding="utf-8")
    return rel_to_repo(out_path)


def build_row(
    *,
    campaign_id: str,
    platform: str,
    model_id: str,
    arch_id: str,
    macro_mode: str,
    repeat_index: int,
    param_hash: str,
    physical_tag: str,
    compare_group: str,
    physical: Dict[str, Any],
    perf_stats: Dict[str, Any],
    artifacts: Dict[str, str],
) -> Dict[str, Any]:
    cp_ns = safe_float(physical.get("critical_path_ns"))
    area = safe_float(physical.get("die_area_um2"))
    power = safe_float(physical.get("total_power_mw"))
    flow_elapsed = safe_float(physical.get("flow_elapsed_s"))
    stage_elapsed = safe_float(physical.get("place_gp_elapsed_s"))

    total_time_ns = safe_float(perf_stats.get("total_time_ns"))
    if total_time_ns is not None:
        latency_ms = total_time_ns * 1e-6
        throughput = (1000.0 / latency_ms) if latency_ms > 0 else None
    else:
        latency_ms = None
        throughput = None

    cycles = (total_time_ns / cp_ns) if (total_time_ns is not None and cp_ns and cp_ns > 0.0) else None
    energy_mj = (power * total_time_ns * 1e-9) if (power is not None and total_time_ns is not None) else None

    physical_ok = (cp_ns is not None and area is not None and power is not None)
    perf_ok = (
        total_time_ns is not None
        and latency_ms is not None
        and throughput is not None
        and energy_mj is not None
    )
    status = "ok" if (physical_ok and perf_ok) else "fail"

    run_id = make_run_id(
        campaign_id=campaign_id,
        model_id=model_id,
        arch_id=arch_id,
        macro_mode=macro_mode,
        repeat_index=repeat_index,
        param_hash=param_hash,
    )
    notes_parts: List[str] = []
    if param_hash:
        notes_parts.append(f"param_hash={param_hash}")
    if physical_tag:
        notes_parts.append(f"tag={physical_tag}")
    if compare_group:
        notes_parts.append(f"compare_group={compare_group}")
    row = {
        "version": 0.1,
        "campaign_id": campaign_id,
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "platform": platform,
        "model_id": model_id,
        "arch_id": arch_id,
        "macro_mode": macro_mode,
        "repeat_index": repeat_index,
        "physical": {
            "critical_path_ns": cp_ns,
            "die_area_um2": area,
            "total_power_mw": power,
            "flow_elapsed_s": flow_elapsed,
            "place_gp_elapsed_s": stage_elapsed,
        },
        "performance": {
            "cycles": cycles,
            "latency_ms": latency_ms,
            "throughput_infer_per_s": throughput,
            "energy_mj": energy_mj,
        },
        "artifacts": {
            "synth_result_json": artifacts.get("synth_result_json", ""),
            "perf_trace_json": artifacts.get("perf_trace_json", ""),
            "schedule_yml": artifacts.get("schedule_yml", ""),
            "descriptors_bin": artifacts.get("descriptors_bin", ""),
        },
        "notes": "; ".join(notes_parts),
    }
    validate_result_row(row, check_paths=False)
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description="Run NPU end-to-end evaluation campaign")
    ap.add_argument("--campaign", required=True, help="Campaign manifest JSON")
    ap.add_argument("--run_physical", action="store_true", help="Run physical sweep if needed")
    ap.add_argument("--repeat", type=int, help="Override campaign repeats")
    ap.add_argument(
        "--modes",
        nargs="+",
        default=list(VALID_MACRO_MODES),
        choices=list(VALID_MACRO_MODES),
        help="Macro modes to evaluate",
    )
    ap.add_argument("--skip_existing", action="store_true", help="Skip run_ids already in results CSV")
    reuse_group = ap.add_mutually_exclusive_group()
    reuse_group.add_argument(
        "--reuse_model_artifacts",
        dest="reuse_model_artifacts",
        action="store_true",
        help="Reuse existing mapper/perf artifacts when input metadata matches (default)",
    )
    reuse_group.add_argument(
        "--no_reuse_model_artifacts",
        dest="reuse_model_artifacts",
        action="store_false",
        help="Force rerun of mapper/perf model artifacts",
    )
    ap.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="Number of parallel jobs for per-model mapper/perf artifact generation (default: 1)",
    )
    ap.add_argument("--max_models", type=int, help="Limit number of models (debug)")
    ap.add_argument("--max_arch", type=int, help="Limit number of architecture points (debug)")
    ap.add_argument("--dry_run", action="store_true", help="Print commands without executing tools")
    ap.set_defaults(reuse_model_artifacts=True)
    args = ap.parse_args()

    os.chdir(REPO_ROOT)
    campaign_path = abs_path(args.campaign)
    campaign = load_json(campaign_path)
    validate_campaign(campaign, check_paths=True)

    campaign_id = str(campaign["campaign_id"])
    platform = str(campaign["platform"])
    repeats = int(args.repeat) if args.repeat is not None else int(campaign["repeats"])
    if repeats < 1:
        die("repeat must be >= 1")
    jobs = int(args.jobs)
    if jobs < 1:
        die("jobs must be >= 1")

    campaign_dir = abs_path(str(campaign["outputs"]["campaign_dir"]))
    results_csv = abs_path(str(campaign["outputs"]["results_csv"]))
    campaign_dir.mkdir(parents=True, exist_ok=True)

    models = list(campaign["models"])
    points = list(campaign["architecture_points"])
    if args.max_models is not None:
        models = models[: max(0, args.max_models)]
    if args.max_arch is not None:
        points = points[: max(0, args.max_arch)]

    existing_run_ids = load_existing_run_ids(results_csv) if args.skip_existing else set()
    generated = 0
    skipped = 0

    # Step 1/2/4: model-level mapper+perf artifacts (independent from physical rows in phase-2 scaffold)
    model_artifacts: Dict[str, Dict[str, Any]] = {}
    for model in models:
        model_id = str(model.get("model_id", "")).strip()
        if not model_id:
            die("model entry missing model_id")
        if not str(model.get("onnx_path", "")).strip():
            die(f"model {model_id}: missing onnx_path")
        if not str(model.get("mapper_arch", "")).strip():
            die(f"model {model_id}: missing mapper_arch")

    use_parallel_models = (jobs > 1 and len(models) > 1)
    if use_parallel_models:
        workers = min(jobs, len(models))
        log(f"parallel model artifact build: jobs={workers} models={len(models)}")
        with ThreadPoolExecutor(max_workers=workers) as ex:
            fut_map = {
                ex.submit(
                    build_model_artifacts,
                    model=model,
                    campaign_dir=campaign_dir,
                    reuse_existing=bool(args.reuse_model_artifacts),
                    dry_run=args.dry_run,
                ): str(model["model_id"])
                for model in models
            }
            for fut in as_completed(fut_map):
                model_id = fut_map[fut]
                try:
                    out_model_id, artifacts = fut.result()
                except BaseException as exc:
                    die(f"model artifact build failed for model_id={model_id}: {exc}")
                model_artifacts[out_model_id] = artifacts
                log(f"model artifacts ready: model_id={out_model_id}")
    else:
        for model in models:
            model_id = str(model["model_id"])
            out_model_id, artifacts = build_model_artifacts(
                model=model,
                campaign_dir=campaign_dir,
                reuse_existing=bool(args.reuse_model_artifacts),
                dry_run=args.dry_run,
            )
            model_artifacts[out_model_id] = artifacts
            log(f"model artifacts ready: model_id={model_id}")

    # Step 3/5: physical + merge rows
    for arch in points:
        arch_id = str(arch["arch_id"])
        metrics_csv = abs_path(str(arch["synth_design_dir"])) / "metrics.csv"
        selector_raw = arch.get("physical_select", {})
        selector: Dict[str, Any] = {}
        if isinstance(selector_raw, dict):
            selector = dict(selector_raw)

        candidates = collect_physical_candidates(metrics_csv)
        selected = select_physical_rows(candidates, modes=args.modes, repeats=repeats, selector=selector)
        if not selected and args.run_physical:
            maybe_run_physical_sweep(
                campaign=campaign,
                arch=arch,
                repeats=repeats,
                dry_run=args.dry_run,
            )
            candidates = collect_physical_candidates(metrics_csv)
            selected = select_physical_rows(candidates, modes=args.modes, repeats=repeats, selector=selector)

        if not selected:
            log(
                f"WARNING: no physical rows selected for arch_id={arch_id} "
                f"(metrics_csv={rel_to_repo(metrics_csv)})"
            )
            continue

        for phys in selected:
            macro_mode = str(phys["macro_mode"])
            repeat_index = int(phys["repeat_index"])
            param_hash = str(phys.get("param_hash", "")).strip()
            physical_tag = str(phys.get("tag", "")).strip()
            compare_group = str(phys.get("compare_group", "")).strip()
            for model in models:
                model_id = str(model["model_id"])
                model_data = model_artifacts[model_id]

                run_id = make_run_id(
                    campaign_id=campaign_id,
                    model_id=model_id,
                    arch_id=arch_id,
                    macro_mode=macro_mode,
                    repeat_index=repeat_index,
                    param_hash=param_hash,
                )
                if run_id in existing_run_ids:
                    skipped += 1
                    continue

                row = build_row(
                    campaign_id=campaign_id,
                    platform=platform,
                    model_id=model_id,
                    arch_id=arch_id,
                    macro_mode=macro_mode,
                    repeat_index=repeat_index,
                    param_hash=param_hash,
                    physical_tag=physical_tag,
                    compare_group=compare_group,
                    physical=phys,
                    perf_stats=dict(model_data["perf_stats"]),
                    artifacts={
                        "synth_result_json": str(phys.get("work_result_json") or phys.get("synth_result_json") or ""),
                        "perf_trace_json": str(model_data["perf_trace_json"]),
                        "schedule_yml": str(model_data["schedule_yml"]),
                        "descriptors_bin": str(model_data["descriptors_bin"]),
                    },
                )

                if not args.dry_run:
                    write_row_json(campaign_dir, row)
                    append_results_csv(results_csv, row)
                generated += 1
                existing_run_ids.add(run_id)

    log(
        f"done: campaign_id={campaign_id} generated_rows={generated} skipped_rows={skipped} "
        f"results_csv={rel_to_repo(results_csv)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

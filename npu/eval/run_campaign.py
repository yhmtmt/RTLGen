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
import hashlib
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml  # type: ignore

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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_path_text(path_text: str) -> str:
    txt = str(path_text or "").strip()
    if not txt:
        return ""
    p = abs_path(txt)
    if not p.exists() or not p.is_file():
        return ""
    return sha256_file(p)


def hash_path_text_with_overrides(path_text: str, overrides: Dict[str, Any]) -> str:
    txt = str(path_text or "").strip()
    payload = {
        "path": txt,
        "file_sha256": hash_path_text(txt),
        "overrides": overrides or {},
    }
    if not txt and not overrides:
        return ""
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


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


def make_default_batch_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def make_sample_id(
    *,
    run_id: str,
    batch_id: str,
    sample_index: int,
    used_sample_ids: set[str],
) -> str:
    base = (
        f"{run_id}__b{normalize_run_token(batch_id, default='batch')}"
        f"__s{max(1, int(sample_index))}"
    )
    sample_id = base
    suffix = 2
    while sample_id in used_sample_ids:
        sample_id = f"{base}__x{suffix}"
        suffix += 1
    return sample_id


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


def load_model_manifest(campaign: Dict[str, Any]) -> Tuple[str, str, Dict[str, Dict[str, Any]]]:
    model_set_id = str(campaign.get("model_set_id", "")).strip()
    model_manifest_txt = str(campaign.get("model_manifest", "")).strip()
    if not model_set_id or not model_manifest_txt:
        die("campaign must define model_set_id and model_manifest")
    model_manifest_path = abs_path(model_manifest_txt)
    manifest = load_json(model_manifest_path)

    by_id: Dict[str, Dict[str, Any]] = {}
    for raw in manifest.get("models", []):
        if not isinstance(raw, dict):
            continue
        model_id = str(raw.get("model_id", "")).strip()
        if not model_id:
            continue
        by_id[model_id] = {
            "model_id": model_id,
            "onnx_path": str(raw.get("onnx_path", "")).strip(),
            "onnx_sha256": str(raw.get("onnx_sha256", "")).strip().lower(),
        }
        fetch = raw.get("fetch")
        if isinstance(fetch, dict):
            by_id[model_id]["fetch"] = fetch
    return model_set_id, rel_to_repo(model_manifest_path), by_id


def layer1_candidate_note(arch: Dict[str, Any]) -> Tuple[str, bool]:
    layer1 = arch.get("layer1_modules")
    if not isinstance(layer1, dict):
        return "", False

    manifest_txt = str(layer1.get("manifest", "")).strip()
    variant_ids_raw = layer1.get("variant_ids", [])
    variant_ids = [
        str(v).strip()
        for v in variant_ids_raw
        if isinstance(v, str) and str(v).strip()
    ]
    allow_wrapped = bool(layer1.get("allow_wrapped_io", False))

    scopes_by_id: Dict[str, str] = {}
    if manifest_txt and variant_ids:
        manifest_doc = load_json(abs_path(manifest_txt))
        candidates = manifest_doc.get("candidates", [])
        if isinstance(candidates, list):
            for cand in candidates:
                if not isinstance(cand, dict):
                    continue
                vid = str(cand.get("variant_id", "")).strip()
                if not vid:
                    continue
                scope = str(cand.get("evaluation_scope", "")).strip()
                scopes_by_id[vid] = scope or "unknown"

    parts: List[str] = []
    if manifest_txt:
        parts.append(f"layer1_manifest={manifest_txt}")
    if variant_ids:
        ids_with_scope = [f"{vid}@{scopes_by_id.get(vid, 'unknown')}" for vid in variant_ids]
        parts.append(f"layer1_candidates={','.join(ids_with_scope)}")
    if allow_wrapped:
        parts.append("layer1_allow_wrapped_io=1")

    has_wrapped = any(scopes_by_id.get(vid, "") == "wrapped_io" for vid in variant_ids)
    return "; ".join(parts), bool(has_wrapped and allow_wrapped)


def mapper_split_note_from_schedule(schedule_yml: str) -> str:
    schedule_path = abs_path(schedule_yml)
    if not schedule_path.exists():
        return ""

    try:
        with schedule_path.open("r", encoding="utf-8") as f:
            doc = yaml.safe_load(f)
    except Exception:
        return "mapper_split_enabled=unknown"

    if not isinstance(doc, dict):
        return "mapper_split_enabled=unknown"

    notes = doc.get("mapper_notes")
    split_enabled: Optional[bool] = None
    chunks: List[int] = []
    row_parallel_enabled: Optional[bool] = None
    row_chunks: List[int] = []
    gemm_num_modules: Optional[int] = None
    if isinstance(notes, dict):
        raw_chunks: Any = []
        if "final_linear_split_enabled" in notes or "final_linear_out_chunks" in notes:
            split_enabled = bool(notes.get("final_linear_split_enabled", False))
            raw_chunks = notes.get("final_linear_out_chunks", [])
        else:
            split_enabled = bool(notes.get("gemm2_split_enabled", False))
            raw_chunks = notes.get("gemm2_out_chunks", [])
        if isinstance(raw_chunks, list):
            for v in raw_chunks:
                try:
                    chunks.append(int(v))
                except Exception:
                    continue
        if "final_linear_row_parallel_enabled" in notes:
            row_parallel_enabled = bool(notes.get("final_linear_row_parallel_enabled", False))
        elif "gemm_row_parallel_enabled" in notes:
            row_parallel_enabled = bool(notes.get("gemm_row_parallel_enabled", False))
        raw_row_chunks = notes.get("final_linear_row_chunks", [])
        if not isinstance(raw_row_chunks, list) or not raw_row_chunks:
            raw_row_chunks = notes.get("gemm_row_chunks", [])
        if isinstance(raw_row_chunks, list):
            for v in raw_row_chunks:
                try:
                    row_chunks.append(int(v))
                except Exception:
                    continue
        if "gemm_num_modules" in notes:
            try:
                gemm_num_modules = max(1, int(notes.get("gemm_num_modules", 1)))
            except Exception:
                gemm_num_modules = None

    # Backward-compatible fallback for schedules without mapper_notes.
    if not chunks:
        gemm2_entries: List[Tuple[int, int]] = []
        for op in doc.get("ops", []) if isinstance(doc.get("ops"), list) else []:
            if not isinstance(op, dict):
                continue
            op_id = str(op.get("id", "")).strip()
            if op_id == "gemm2":
                idx = 0
            elif op_id.startswith("gemm2_c"):
                try:
                    idx = int(op_id[len("gemm2_c") :])
                except Exception:
                    continue
            else:
                continue
            try:
                n_val = int(op.get("n"))
            except Exception:
                continue
            gemm2_entries.append((idx, n_val))
        if gemm2_entries:
            gemm2_entries.sort(key=lambda t: t[0])
            chunks = [n for _, n in gemm2_entries]
            if split_enabled is None:
                split_enabled = len(chunks) > 1

    if split_enabled is None:
        split_enabled = False

    parts = [f"mapper_split_enabled={1 if split_enabled else 0}"]
    if chunks:
        parts.append(f"mapper_split_chunk_count={len(chunks)}")
        parts.append(f"mapper_split_chunks={','.join(str(n) for n in chunks)}")
    if gemm_num_modules is not None:
        parts.append(f"mapper_num_modules={gemm_num_modules}")
    if row_parallel_enabled is not None:
        parts.append(f"mapper_row_parallel_enabled={1 if row_parallel_enabled else 0}")
    if row_chunks:
        parts.append(f"mapper_row_parallel_chunk_count={len(row_chunks)}")
        parts.append(f"mapper_row_parallel_chunks={','.join(str(n) for n in row_chunks)}")
    return "; ".join(parts)


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


def arch_model_hints(arch: Dict[str, Any]) -> Dict[str, int]:
    rtlgen_config_txt = str(arch.get("rtlgen_config", "")).strip()
    gemm_num_modules = 1
    if rtlgen_config_txt:
        rtlgen_doc = read_json(abs_path(rtlgen_config_txt))
        compute = rtlgen_doc.get("compute", {}) if isinstance(rtlgen_doc, dict) else {}
        gemm = compute.get("gemm", {}) if isinstance(compute, dict) else {}
        try:
            gemm_num_modules = max(1, int(gemm.get("num_modules", 1)))
        except Exception:
            gemm_num_modules = 1
    return {
        "gemm_num_modules": gemm_num_modules,
        "gemm_engine_count": gemm_num_modules,
    }


def model_mapper_extra_args(model: Dict[str, Any]) -> List[str]:
    raw = model.get("mapper_extra_args", [])
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for arg in raw:
        if isinstance(arg, str) and str(arg).strip():
            out.append(str(arg))
    return out


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
    arch_id: str,
    model_id: str,
    model: Dict[str, Any],
    campaign_dir: Path,
    reuse_existing: bool,
    dry_run: bool,
    gemm_num_modules: int,
) -> Tuple[str, str]:
    mapper_dir = campaign_dir / "artifacts" / "mapper" / safe_slug(arch_id) / safe_slug(model_id)
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
    mapper_extra_args = model_mapper_extra_args(model)

    expected_meta = {
        "kind": "mapper",
        "arch_id": arch_id,
        "model_id": model_id,
        "onnx_path": onnx_path,
        "mapper_arch": mapper_arch,
        "gemm_num_modules": str(max(1, int(gemm_num_modules))),
        "mapper_extra_args_json": json.dumps(mapper_extra_args, separators=(",", ":")),
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

    cmd = [
        "python3",
        "npu/mapper/onnx_to_schedule.py",
        "--onnx",
        onnx_path,
        "--arch",
        mapper_arch,
        "--out",
        rel_to_repo(schedule),
        "--gemm-num-modules",
        str(max(1, int(gemm_num_modules))),
    ]
    cmd.extend(mapper_extra_args)
    run_cmd(cmd, dry_run=dry_run)
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
    arch_id: str,
    model_id: str,
    descriptors_bin: str,
    perf_config: str,
    campaign_dir: Path,
    reuse_existing: bool,
    dry_run: bool,
    gemm_engine_count: int,
) -> Tuple[str, Dict[str, Any]]:
    perf_dir = campaign_dir / "artifacts" / "perf" / safe_slug(arch_id) / safe_slug(model_id)
    perf_dir.mkdir(parents=True, exist_ok=True)
    trace_json = perf_dir / "trace.json"
    meta_path = perf_dir / "meta.json"

    expected_meta = {
        "kind": "perf",
        "arch_id": arch_id,
        "model_id": model_id,
        "descriptors_bin": descriptors_bin,
        "perf_config": perf_config,
        "gemm_engine_count": str(max(1, int(gemm_engine_count))),
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
    cmd.extend(["--gemm-engine-count", str(max(1, int(gemm_engine_count)))])
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
    arch: Dict[str, Any],
    campaign_dir: Path,
    reuse_existing: bool,
    dry_run: bool,
) -> Tuple[str, str, Dict[str, Any]]:
    arch_id = str(arch["arch_id"])
    model_id = str(model["model_id"])
    perf_config = str(model.get("perf_config", "")).strip()
    hints = arch_model_hints(arch)
    schedule_yml, descriptors_bin = mapper_emit(
        arch_id=arch_id,
        model_id=model_id,
        model=model,
        campaign_dir=campaign_dir,
        reuse_existing=reuse_existing,
        dry_run=dry_run,
        gemm_num_modules=int(hints["gemm_num_modules"]),
    )
    perf_trace_json, perf_stats = perf_emit(
        arch_id=arch_id,
        model_id=model_id,
        descriptors_bin=descriptors_bin,
        perf_config=perf_config,
        campaign_dir=campaign_dir,
        reuse_existing=reuse_existing,
        dry_run=dry_run,
        gemm_engine_count=int(hints["gemm_engine_count"]),
    )
    mapper_split_note = mapper_split_note_from_schedule(schedule_yml)
    return arch_id, model_id, {
        "schedule_yml": schedule_yml,
        "descriptors_bin": descriptors_bin,
        "perf_trace_json": perf_trace_json,
        "perf_stats": perf_stats,
        "mapper_split_note": mapper_split_note,
    }


def flatten_row(row: Dict[str, Any]) -> Dict[str, Any]:
    physical = row.get("physical", {}) or {}
    performance = row.get("performance", {}) or {}
    artifacts = row.get("artifacts", {}) or {}
    return {
        "version": row.get("version"),
        "campaign_id": row.get("campaign_id"),
        "run_id": row.get("run_id"),
        "sample_id": row.get("sample_id", ""),
        "batch_id": row.get("batch_id", ""),
        "sample_index": row.get("sample_index", ""),
        "model_set_id": row.get("model_set_id", ""),
        "model_manifest": row.get("model_manifest", ""),
        "onnx_sha256": row.get("onnx_sha256", ""),
        "mapper_arch_hash": row.get("mapper_arch_hash", ""),
        "perf_config_hash": row.get("perf_config_hash", ""),
        "physical_source_campaign": row.get("physical_source_campaign", ""),
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


def load_existing_sample_index(results_csv: Path) -> Tuple[Dict[str, int], set[str]]:
    run_id_counts: Dict[str, int] = {}
    sample_ids: set[str] = set()
    if not results_csv.exists():
        return run_id_counts, sample_ids
    with results_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            run_id = str(row.get("run_id", "")).strip()
            if run_id:
                run_id_counts[run_id] = int(run_id_counts.get(run_id, 0)) + 1
            sample_id = str(row.get("sample_id", "")).strip()
            if sample_id:
                sample_ids.add(sample_id)
    return run_id_counts, sample_ids


def safe_slug(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(text))
    s = s.strip("_")
    return s or "row"


def write_row_json(campaign_dir: Path, row: Dict[str, Any]) -> str:
    out_dir = campaign_dir / "artifacts" / "result_rows"
    out_dir.mkdir(parents=True, exist_ok=True)
    file_id = str(row.get("sample_id", "")).strip() or str(row.get("run_id", "run")).strip()
    out_path = out_dir / f"{safe_slug(file_id)}.json"
    out_path.write_text(json.dumps(row, indent=2), encoding="utf-8")
    return rel_to_repo(out_path)


def build_row(
    *,
    campaign_id: str,
    model_set_id: str,
    model_manifest: str,
    onnx_sha256: str,
    mapper_arch_hash: str,
    perf_config_hash: str,
    physical_source_campaign: str,
    platform: str,
    model_id: str,
    arch_id: str,
    macro_mode: str,
    repeat_index: int,
    param_hash: str,
    physical_tag: str,
    compare_group: str,
    batch_id: str,
    sample_index: int,
    sample_id: str,
    physical: Dict[str, Any],
    perf_stats: Dict[str, Any],
    artifacts: Dict[str, str],
    layer1_note: str = "",
    mapper_note: str = "",
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
    if mapper_note:
        notes_parts.append(mapper_note)
    if layer1_note:
        notes_parts.append(layer1_note)
    row = {
        "version": 0.1,
        "campaign_id": campaign_id,
        "run_id": run_id,
        "sample_id": sample_id,
        "batch_id": batch_id,
        "sample_index": sample_index,
        "model_set_id": model_set_id,
        "model_manifest": model_manifest,
        "onnx_sha256": onnx_sha256,
        "mapper_arch_hash": mapper_arch_hash,
        "perf_config_hash": perf_config_hash,
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
    if physical_source_campaign:
        row["physical_source_campaign"] = physical_source_campaign
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
    ap.add_argument(
        "--batch_id",
        help=(
            "Optional batch identifier recorded in each sample row "
            "(default: UTC timestamp label)"
        ),
    )
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
    validate_campaign(campaign, check_paths=True, allow_fetch_missing_paths=True)

    campaign_id = str(campaign["campaign_id"])
    model_set_id, model_manifest_rel, model_manifest_by_id = load_model_manifest(campaign)
    physical_source_campaign = str(campaign.get("physical_source_campaign", "")).strip()
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
    existing_run_id_counts, existing_sample_ids = load_existing_sample_index(results_csv)
    pending_run_id_counts: Dict[str, int] = {}
    used_sample_ids = set(existing_sample_ids)
    batch_id = str(args.batch_id).strip() if args.batch_id is not None else ""
    if not batch_id:
        batch_id = make_default_batch_id()
    generated = 0
    skipped = 0

    # Step 1/2/4: architecture-aware mapper+perf artifacts.
    model_artifacts: Dict[Tuple[str, str], Dict[str, Any]] = {}
    model_provenance: Dict[Tuple[str, str], Dict[str, str]] = {}
    for model in models:
        model_id = str(model.get("model_id", "")).strip()
        if not model_id:
            die("model entry missing model_id")
        onnx_path = str(model.get("onnx_path", "")).strip()
        if not onnx_path:
            die(f"model {model_id}: missing onnx_path")
        if not str(model.get("mapper_arch", "")).strip():
            die(f"model {model_id}: missing mapper_arch")
        manifest_model = model_manifest_by_id.get(model_id)
        if manifest_model is None:
            die(f"model {model_id}: not found in campaign.model_manifest")
        manifest_onnx_path = str(manifest_model.get("onnx_path", "")).strip()
        if onnx_path != manifest_onnx_path:
            die(
                f"model {model_id}: campaign onnx_path '{onnx_path}' does not match "
                f"manifest onnx_path '{manifest_onnx_path}'"
            )
        onnx_abs = abs_path(onnx_path)
        if not onnx_abs.exists():
            fetch = manifest_model.get("fetch")
            if isinstance(fetch, dict) and str(fetch.get("url", "")).strip():
                die(
                    f"model {model_id}: missing ONNX file {onnx_path}; "
                    f"run `python3 npu/eval/fetch_models.py --manifest {model_manifest_rel}` first"
                )
            die(f"model {model_id}: missing ONNX file {onnx_path}")
        for arch in points:
            arch_id = str(arch["arch_id"])
            hints = arch_model_hints(arch)
            model_provenance[(arch_id, model_id)] = {
                "model_set_id": model_set_id,
                "model_manifest": model_manifest_rel,
                "onnx_sha256": str(manifest_model.get("onnx_sha256", "")).strip().lower(),
                "mapper_arch_hash": hash_path_text_with_overrides(
                    str(model.get("mapper_arch", "")),
                    {
                        "gemm_num_modules": int(hints["gemm_num_modules"]),
                        "mapper_extra_args": model_mapper_extra_args(model),
                    },
                ),
                "perf_config_hash": hash_path_text_with_overrides(
                    str(model.get("perf_config", "")),
                    {"gemm_engine_count": int(hints["gemm_engine_count"])},
                ),
            }

    artifact_jobs: List[Tuple[Dict[str, Any], Dict[str, Any]]] = [
        (model, arch)
        for arch in points
        for model in models
    ]
    use_parallel_models = (jobs > 1 and len(artifact_jobs) > 1)
    if use_parallel_models:
        workers = min(jobs, len(artifact_jobs))
        log(
            f"parallel model artifact build: jobs={workers} models={len(models)} "
            f"arch_points={len(points)} tasks={len(artifact_jobs)}"
        )
        with ThreadPoolExecutor(max_workers=workers) as ex:
            fut_map = {
                ex.submit(
                    build_model_artifacts,
                    model=model,
                    arch=arch,
                    campaign_dir=campaign_dir,
                    reuse_existing=bool(args.reuse_model_artifacts),
                    dry_run=args.dry_run,
                ): (str(arch["arch_id"]), str(model["model_id"]))
                for model, arch in artifact_jobs
            }
            for fut in as_completed(fut_map):
                arch_id, model_id = fut_map[fut]
                try:
                    out_arch_id, out_model_id, artifacts = fut.result()
                except BaseException as exc:
                    die(
                        f"model artifact build failed for arch_id={arch_id} "
                        f"model_id={model_id}: {exc}"
                    )
                model_artifacts[(out_arch_id, out_model_id)] = artifacts
                log(f"model artifacts ready: arch_id={out_arch_id} model_id={out_model_id}")
    else:
        for model, arch in artifact_jobs:
            model_id = str(model["model_id"])
            arch_id = str(arch["arch_id"])
            out_arch_id, out_model_id, artifacts = build_model_artifacts(
                model=model,
                arch=arch,
                campaign_dir=campaign_dir,
                reuse_existing=bool(args.reuse_model_artifacts),
                dry_run=args.dry_run,
            )
            model_artifacts[(out_arch_id, out_model_id)] = artifacts
            log(f"model artifacts ready: arch_id={arch_id} model_id={model_id}")

    # Step 3/5: physical + merge rows
    for arch in points:
        arch_id = str(arch["arch_id"])
        layer1_note, wrapped_override = layer1_candidate_note(arch)
        if wrapped_override:
            log(
                f"NOTE: arch_id={arch_id} is using Layer1 wrapped_io candidates "
                "(allow_wrapped_io=true)"
            )
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
                model_data = model_artifacts[(arch_id, model_id)]
                model_meta = model_provenance[(arch_id, model_id)]

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
                prior_count = int(existing_run_id_counts.get(run_id, 0)) + int(pending_run_id_counts.get(run_id, 0))
                sample_index = prior_count + 1
                sample_id = make_sample_id(
                    run_id=run_id,
                    batch_id=batch_id,
                    sample_index=sample_index,
                    used_sample_ids=used_sample_ids,
                )

                row = build_row(
                    campaign_id=campaign_id,
                    model_set_id=str(model_meta.get("model_set_id", "")),
                    model_manifest=str(model_meta.get("model_manifest", "")),
                    onnx_sha256=str(model_meta.get("onnx_sha256", "")),
                    mapper_arch_hash=str(model_meta.get("mapper_arch_hash", "")),
                    perf_config_hash=str(model_meta.get("perf_config_hash", "")),
                    physical_source_campaign=physical_source_campaign,
                    platform=platform,
                    model_id=model_id,
                    arch_id=arch_id,
                    macro_mode=macro_mode,
                    repeat_index=repeat_index,
                    param_hash=param_hash,
                    physical_tag=physical_tag,
                    compare_group=compare_group,
                    batch_id=batch_id,
                    sample_index=sample_index,
                    sample_id=sample_id,
                    physical=phys,
                    perf_stats=dict(model_data["perf_stats"]),
                    artifacts={
                        "synth_result_json": str(phys.get("work_result_json") or phys.get("synth_result_json") or ""),
                        "perf_trace_json": str(model_data["perf_trace_json"]),
                        "schedule_yml": str(model_data["schedule_yml"]),
                        "descriptors_bin": str(model_data["descriptors_bin"]),
                    },
                    layer1_note=layer1_note,
                    mapper_note=str(model_data.get("mapper_split_note", "")).strip(),
                )

                if not args.dry_run:
                    write_row_json(campaign_dir, row)
                    append_results_csv(results_csv, row)
                generated += 1
                existing_run_ids.add(run_id)
                pending_run_id_counts[run_id] = int(pending_run_id_counts.get(run_id, 0)) + 1
                used_sample_ids.add(sample_id)

    log(
        f"done: campaign_id={campaign_id} generated_rows={generated} skipped_rows={skipped} "
        f"results_csv={rel_to_repo(results_csv)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

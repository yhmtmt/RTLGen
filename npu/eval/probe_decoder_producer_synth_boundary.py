#!/usr/bin/env python3
"""Bounded synthesis probe for decoder output-projection producer scale."""

from __future__ import annotations

import argparse
import csv
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def load_json_list(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"expected JSON array: {path}")
    entries = [entry for entry in data if isinstance(entry, dict)]
    if len(entries) != len(data):
        raise ValueError(f"expected only JSON objects in {path}")
    return entries


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def portable_log_label(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return path.name


def repo_portable_path_text(raw: Any) -> str:
    text = str(raw or "").strip()
    if not text:
        return ""
    path = Path(text)
    if not path.is_absolute():
        return text
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return ""


def portable_metrics_row(row: dict[str, Any]) -> dict[str, Any]:
    portable = dict(row)
    work_result = repo_portable_path_text(portable.get("work_result_json"))
    if work_result:
        portable["work_result_json"] = work_result
    result_path = repo_portable_path_text(portable.get("result_path"))
    if result_path:
        portable["result_path"] = result_path
    elif work_result:
        portable["result_path"] = work_result
    else:
        portable["result_path"] = ""
    synth_script = repo_portable_path_text(portable.get("synth_script_path"))
    if synth_script:
        portable["synth_script_path"] = synth_script
    elif "synth_script_path" in portable:
        portable["synth_script_path"] = ""
    return portable


def parse_configs(args: argparse.Namespace) -> list[Path]:
    raw: list[str] = []
    for item in args.configs or []:
        raw.extend(part.strip() for part in str(item).split(",") if part.strip())
    raw.extend(args.config or [])
    paths = [(REPO_ROOT / item).resolve() if not Path(item).is_absolute() else Path(item) for item in raw]
    if not paths:
        raise ValueError("provide at least one --config or --configs path")
    return paths


def num_modules(config: dict[str, Any]) -> int:
    compute = config.get("compute")
    if not isinstance(compute, dict):
        raise ValueError("config missing compute object")
    gemm = compute.get("gemm")
    if not isinstance(gemm, dict):
        raise ValueError("config missing compute.gemm object")
    return int(gemm.get("num_modules", 0))


def normalize_repo_path(path: str | Path | None) -> str | None:
    if path is None:
        return None
    raw = str(path).strip()
    if not raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    return rel(candidate)


def load_infeasible_registry(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    entries = load_json_list(path)
    for entry in entries:
        match = entry.get("match")
        if not isinstance(match, dict):
            raise ValueError(f"infeasible registry entry missing match object: {entry.get('id')}")
    return entries


def repo_text_requirements_satisfied(entry: dict[str, Any]) -> bool:
    requirements = entry.get("requires_repo_text") or []
    if not isinstance(requirements, list):
        raise ValueError(f"infeasible registry entry has invalid requires_repo_text: {entry.get('id')}")
    for requirement in requirements:
        if not isinstance(requirement, dict):
            raise ValueError(f"infeasible registry entry has invalid text requirement: {entry.get('id')}")
        raw_path = str(requirement.get("path", "")).strip()
        needle = str(requirement.get("contains", ""))
        if not raw_path or not needle:
            raise ValueError(f"infeasible registry text requirement missing path/contains: {entry.get('id')}")
        path = REPO_ROOT / raw_path
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except FileNotFoundError:
            return False
        if needle not in text:
            return False
    return True


def find_infeasible_match(
    registry: list[dict[str, Any]],
    *,
    config_path: Path,
    config: dict[str, Any],
    platform: str,
    top: str,
    make_target: str,
) -> dict[str, Any] | None:
    normalized_config = rel(config_path)
    modules = num_modules(config)
    for entry in registry:
        match = entry.get("match") or {}
        match_config = normalize_repo_path(match.get("config"))
        if match_config is not None and match_config != normalized_config:
            continue
        if match.get("platform") is not None and str(match.get("platform")) != platform:
            continue
        if match.get("top") is not None and str(match.get("top")) != top:
            continue
        if match.get("make_target") is not None and str(match.get("make_target")) != make_target:
            continue
        if match.get("num_modules") is not None and int(match.get("num_modules")) != modules:
            continue
        if not repo_text_requirements_satisfied(entry):
            continue
        return entry
    return None


def rtlgen_binary_paths(configs: list[Path]) -> list[Path]:
    paths: list[Path] = []
    seen: set[Path] = set()
    for config_path in configs:
        config = load_json(config_path)
        gemm = ((config.get("compute") or {}).get("gemm") or {})
        if not isinstance(gemm, dict):
            continue
        rtlgen_cpp = gemm.get("rtlgen_cpp")
        if not isinstance(rtlgen_cpp, dict):
            continue
        raw_path = str(rtlgen_cpp.get("binary_path", "")).strip()
        if not raw_path:
            continue
        path = Path(raw_path)
        if not path.is_absolute():
            path = REPO_ROOT / path
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            paths.append(resolved)
    return paths


def tail_lines(path: Path, limit: int = 40) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except FileNotFoundError:
        return []
    return lines[-limit:]


def run_logged(
    cmd: list[str],
    *,
    cwd: Path,
    log_path: Path,
    timeout_seconds: int,
    stall_timeout_seconds: int,
) -> dict[str, Any]:
    start = time.monotonic()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            preexec_fn=os.setsid,
        )
        last_size = -1
        last_activity = time.monotonic()
        timed_out = False
        stalled = False
        while proc.poll() is None:
            now = time.monotonic()
            try:
                size = log_path.stat().st_size
            except FileNotFoundError:
                size = 0
            if size != last_size:
                last_size = size
                last_activity = now
            if timeout_seconds > 0 and now - start >= timeout_seconds:
                timed_out = True
                break
            if stall_timeout_seconds > 0 and now - last_activity >= stall_timeout_seconds:
                stalled = True
                break
            time.sleep(2.0)
        if timed_out or stalled:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait()
        rc = proc.returncode
    elapsed = time.monotonic() - start
    if timed_out:
        status = "timeout"
    elif stalled:
        status = "stall_timeout"
    elif rc == 0:
        status = "ok"
    else:
        status = "failed"
    return {
        "status": status,
        "returncode": rc,
        "elapsed_seconds": elapsed,
        "log_path": portable_log_label(log_path),
        "log_tail": tail_lines(log_path),
        "command": " ".join(cmd),
    }


def ensure_rtlgen_binaries(
    configs: list[Path],
    *,
    log_dir: Path,
    build_timeout_seconds: int,
    stall_timeout_seconds: int,
    skip_build: bool,
) -> dict[str, Any]:
    paths = rtlgen_binary_paths(configs)
    missing = [path for path in paths if not path.exists()]
    if not missing:
        return {
            "status": "ok",
            "required_binaries": [rel(path) for path in paths],
            "missing_before_build": [],
            "configure": None,
            "build": None,
        }
    if skip_build:
        return {
            "status": "failed",
            "required_binaries": [rel(path) for path in paths],
            "missing_before_build": [rel(path) for path in missing],
            "configure": None,
            "build": None,
            "error": "rtlgen binary missing and --skip-rtlgen-build was set",
        }

    configure = run_logged(
        ["cmake", "-S", ".", "-B", "build"],
        cwd=REPO_ROOT,
        log_path=log_dir / "rtlgen_cmake_configure.log",
        timeout_seconds=build_timeout_seconds,
        stall_timeout_seconds=stall_timeout_seconds,
    )
    build: dict[str, Any] | None = None
    if configure["status"] == "ok":
        build = run_logged(
            ["cmake", "--build", "build", "--target", "rtlgen", "-j", "2"],
            cwd=REPO_ROOT,
            log_path=log_dir / "rtlgen_cmake_build.log",
            timeout_seconds=build_timeout_seconds,
            stall_timeout_seconds=stall_timeout_seconds,
        )

    missing_after = [path for path in paths if not path.exists()]
    status = "ok" if not missing_after and configure["status"] == "ok" and build and build["status"] == "ok" else "failed"
    result: dict[str, Any] = {
        "status": status,
        "required_binaries": [rel(path) for path in paths],
        "missing_before_build": [rel(path) for path in missing],
        "missing_after_build": [rel(path) for path in missing_after],
        "configure": configure,
        "build": build,
    }
    if status != "ok":
        result["error"] = "failed to prepare rtlgen C++ binary before producer synthesis probe"
    return result


def latest_metrics_row(design_dir: Path) -> dict[str, Any] | None:
    metrics = design_dir / "metrics.csv"
    if not metrics.exists():
        return None
    with metrics.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return dict(rows[-1]) if rows else None


def probe_config(
    config_path: Path,
    *,
    sweep: Path,
    platform: str,
    top: str,
    make_target: str,
    out_root: Path,
    timeout_seconds: int,
    stall_timeout_seconds: int,
    log_dir: Path,
    infeasible_registry: list[dict[str, Any]],
) -> dict[str, Any]:
    config = load_json(config_path)
    modules = num_modules(config)
    design_dir = config_path.parent
    verilog_dir = design_dir / "verilog"
    infeasible = find_infeasible_match(
        infeasible_registry,
        config_path=config_path,
        config=config,
        platform=platform,
        top=top,
        make_target=make_target,
    )
    if infeasible is not None:
        return {
            "config": rel(config_path),
            "design_dir": rel(design_dir),
            "num_modules": modules,
            "rtlgen": None,
            "synthesis": {
                "status": "known_infeasible",
                "returncode": None,
                "elapsed_seconds": 0.0,
                "log_path": "",
                "log_tail": [],
                "command": "",
            },
            "metrics_row": None,
            "status": "known_infeasible",
            "known_infeasible": {
                "id": infeasible.get("id"),
                "reason": infeasible.get("reason"),
                "source_evidence": infeasible.get("source_evidence"),
                "recorded_utc": infeasible.get("recorded_utc"),
            },
        }

    gen_cmd = [
        sys.executable,
        "npu/rtlgen/gen.py",
        "--config",
        rel(config_path),
        "--out",
        rel(verilog_dir),
    ]
    gen_result = run_logged(
        gen_cmd,
        cwd=REPO_ROOT,
        log_path=log_dir / f"nm{modules}_rtlgen.log",
        timeout_seconds=max(300, min(timeout_seconds, 900)),
        stall_timeout_seconds=max(120, min(stall_timeout_seconds, 300)),
    )
    row: dict[str, Any] = {
        "config": rel(config_path),
        "design_dir": rel(design_dir),
        "num_modules": modules,
        "rtlgen": gen_result,
        "synthesis": None,
        "metrics_row": None,
    }
    if gen_result["status"] != "ok":
        row["status"] = f"rtlgen_{gen_result['status']}"
        return row

    synth_cmd = [
        sys.executable,
        "npu/synth/run_block_sweep.py",
        "--design_dir",
        rel(design_dir),
        "--platform",
        platform,
        "--top",
        top,
        "--sweep",
        rel(sweep),
        "--make_target",
        make_target,
        "--out_root",
        rel(out_root),
        "--force_copy",
    ]
    synth_result = run_logged(
        synth_cmd,
        cwd=REPO_ROOT,
        log_path=log_dir / f"nm{modules}_{make_target}.log",
        timeout_seconds=timeout_seconds,
        stall_timeout_seconds=stall_timeout_seconds,
    )
    row["synthesis"] = synth_result
    metrics_row = latest_metrics_row(out_root / design_dir.name)
    if metrics_row is not None:
        row["metrics_row"] = portable_metrics_row(metrics_row)
    if synth_result["status"] != "ok":
        row["status"] = synth_result["status"]
    elif metrics_row and str(metrics_row.get("status", "")).strip():
        row["status"] = str(metrics_row.get("status"))
    else:
        row["status"] = "ok"
    return row


def build_diagnosis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if rows and str(rows[0].get("status")) == "setup_failed":
        return {
            "decision": "producer_synth_boundary_setup_failed",
            "feasible_max_num_modules": None,
            "first_nonviable_num_modules": None,
            "recommended_next_step": "Fix evaluator tool setup before interpreting producer synthesis scale.",
        }
    tool_failures = [row for row in rows if str(row.get("status", "")).startswith("rtlgen_")]
    if tool_failures:
        return {
            "decision": "producer_synth_boundary_setup_failed",
            "feasible_max_num_modules": None,
            "first_nonviable_num_modules": None,
            "recommended_next_step": "Fix RTL generation before interpreting producer synthesis scale.",
        }
    ok_rows = [row for row in rows if str(row.get("status")) == "ok"]
    blocked_rows = [row for row in rows if str(row.get("status")) != "ok"]
    feasible = max((int(row.get("num_modules", 0)) for row in ok_rows), default=None)
    first_blocked = min((int(row.get("num_modules", 0)) for row in blocked_rows), default=None)
    if first_blocked is None:
        decision = "producer_synth_boundary_not_reached"
        next_step = "Extend the probe to the next producer scale before launching full PnR."
    else:
        decision = "producer_synth_boundary_recorded"
        next_step = (
            "Use the largest completed synth point for near-frontier extrapolation and split or macro-harden "
            "larger producers before retrying full physical implementation."
        )
    return {
        "decision": decision,
        "feasible_max_num_modules": feasible,
        "first_nonviable_num_modules": first_blocked,
        "recommended_next_step": next_step,
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Decoder Producer Synthesis Boundary",
        "",
        f"- make_target: `{payload['make_target']}`",
        f"- timeout_seconds: `{payload['timeout_seconds']}`",
        f"- stall_timeout_seconds: `{payload['stall_timeout_seconds']}`",
        "",
        "| num_modules | status | elapsed_s | metrics_status | result_path | log |",
        "|---:|---|---:|---|---|---|",
    ]
    for row in payload["probe_rows"]:
        synth = row.get("synthesis") or {}
        metrics = row.get("metrics_row") or {}
        elapsed = synth.get("elapsed_seconds")
        elapsed_text = f"{float(elapsed):.1f}" if elapsed is not None else ""
        lines.append(
            "| {nm} | {status} | {elapsed} | {metrics_status} | {result_path} | {log} |".format(
                nm=row.get("num_modules"),
                status=row.get("status"),
                elapsed=elapsed_text,
                metrics_status=metrics.get("status", ""),
                result_path=metrics.get("result_path", ""),
                log=synth.get("log_path", ""),
            )
        )
    diagnosis = payload["diagnosis"]
    lines.extend(
        [
            "",
            "## Diagnosis",
            "",
            f"- decision: `{diagnosis.get('decision')}`",
            f"- feasible_max_num_modules: `{diagnosis.get('feasible_max_num_modules')}`",
            f"- first_nonviable_num_modules: `{diagnosis.get('first_nonviable_num_modules')}`",
            f"- recommended_next_step: {diagnosis.get('recommended_next_step')}",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", action="append", default=[], help="Config path; repeatable")
    ap.add_argument("--configs", action="append", default=[], help="Comma-separated config paths")
    ap.add_argument("--sweep", required=True)
    ap.add_argument("--platform", default="nangate45")
    ap.add_argument("--top", default="npu_top")
    ap.add_argument("--make-target", default="1_2_yosys")
    ap.add_argument("--out-root", default="runs/designs/npu_blocks")
    ap.add_argument("--timeout-seconds", type=int, default=1800)
    ap.add_argument("--stall-timeout-seconds", type=int, default=900)
    ap.add_argument("--rtlgen-build-timeout-seconds", type=int, default=900)
    ap.add_argument("--skip-rtlgen-build", action="store_true")
    ap.add_argument("--continue-after-failure", action="store_true")
    ap.add_argument(
        "--infeasible-registry",
        default="runs/knowledge/infeasible_designs.json",
        help="JSON registry of exact synth points to skip before launching long-running tools",
    )
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    configs = sorted(parse_configs(args), key=lambda path: num_modules(load_json(path)))
    sweep = (REPO_ROOT / args.sweep).resolve() if not Path(args.sweep).is_absolute() else Path(args.sweep)
    out = (REPO_ROOT / args.out).resolve() if not Path(args.out).is_absolute() else Path(args.out)
    out_md = (REPO_ROOT / args.out_md).resolve() if not Path(args.out_md).is_absolute() else Path(args.out_md)
    out_root = (
        (REPO_ROOT / args.out_root).resolve()
        if not Path(args.out_root).is_absolute()
        else Path(args.out_root)
    )
    log_root = Path(
        os.environ.get("RTLGEN_PRODUCER_SYNTH_BOUNDARY_LOG_DIR", "/tmp/rtlgen-producer-synth-boundary")
    )
    log_dir = log_root / out.stem
    registry_path = (
        (REPO_ROOT / args.infeasible_registry).resolve()
        if args.infeasible_registry and not Path(args.infeasible_registry).is_absolute()
        else Path(args.infeasible_registry).resolve()
        if args.infeasible_registry
        else None
    )
    infeasible_registry = load_infeasible_registry(registry_path)

    configs_requiring_tools: list[Path] = []
    for config_path in configs:
        config = load_json(config_path)
        if find_infeasible_match(
            infeasible_registry,
            config_path=config_path,
            config=config,
            platform=args.platform,
            top=args.top,
            make_target=args.make_target,
        ) is None:
            configs_requiring_tools.append(config_path)

    setup = ensure_rtlgen_binaries(
        configs_requiring_tools,
        log_dir=log_dir,
        build_timeout_seconds=args.rtlgen_build_timeout_seconds,
        stall_timeout_seconds=max(120, min(args.stall_timeout_seconds, 300)),
        skip_build=args.skip_rtlgen_build,
    ) if configs_requiring_tools else {
        "status": "ok",
        "required_binaries": [],
        "missing_before_build": [],
        "configure": None,
        "build": None,
        "skipped": "all requested configs matched infeasible registry",
    }
    rows: list[dict[str, Any]] = []
    if setup["status"] != "ok":
        rows.append(
            {
                "status": "setup_failed",
                "num_modules": None,
                "config": None,
                "setup": setup,
                "rtlgen": None,
                "synthesis": None,
                "metrics_row": None,
            }
        )
    else:
        for config_path in configs:
            row = probe_config(
                config_path,
                sweep=sweep,
                platform=args.platform,
                top=args.top,
                make_target=args.make_target,
                out_root=out_root,
                timeout_seconds=args.timeout_seconds,
                stall_timeout_seconds=args.stall_timeout_seconds,
                log_dir=log_dir,
                infeasible_registry=infeasible_registry,
            )
            rows.append(row)
            if row.get("status") != "ok" and not args.continue_after_failure:
                break

    payload = {
        "version": 0.1,
        "model": "decoder_output_projection_producer_synth_boundary_v1",
        "platform": args.platform,
        "top": args.top,
        "make_target": args.make_target,
        "timeout_seconds": args.timeout_seconds,
        "stall_timeout_seconds": args.stall_timeout_seconds,
        "infeasible_registry": rel(registry_path) if registry_path is not None else None,
        "rtlgen_setup": setup,
        "sweep": rel(sweep),
        "probe_rows": rows,
        "diagnosis": build_diagnosis(rows),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(out_md, payload)
    return 2 if setup["status"] != "ok" else 0


if __name__ == "__main__":
    raise SystemExit(main())

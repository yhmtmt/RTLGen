#!/usr/bin/env python3
"""
Prepare and run fp16 backend OpenROAD sweeps for NPU top-level blocks.

This script compares:
1) builtin raw16 placeholder fp16 GEMM backend
2) C++ RTLGen IEEE-half fp16 GEMM backend

It materializes RTL under runs/designs/npu_blocks/<design>/verilog and then
invokes npu/synth/run_block_sweep.py for each backend.
"""

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional


REPO_ROOT = Path(__file__).resolve().parents[2]
DESIGN_ROOT_DEFAULT = REPO_ROOT / "runs/designs/npu_blocks"
SWEEP_DEFAULT = REPO_ROOT / "npu/synth/fp16_backend_sweep_nangate45.json"

BACKENDS = (
    {
        "backend": "builtin_raw16",
        "design": "npu_fp16_builtin_l1",
        "rtlgen_config": REPO_ROOT / "npu/rtlgen/examples/minimal_fp16_builtin_l1.json",
        "default_eligible": False,
        "default_note": "non-IEEE placeholder; excluded from default lock",
    },
    {
        "backend": "cpp_ieee",
        "design": "npu_fp16_cpp_l1",
        "rtlgen_config": REPO_ROOT / "npu/rtlgen/examples/minimal_fp16_cpp.json",
        "default_eligible": True,
    },
)


def sha1_file(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_cmd(cmd: List[str], *, cwd: Path, dry_print_only: bool = False) -> None:
    cmd_text = " ".join(str(x) for x in cmd)
    if dry_print_only:
        print(f"[DRY] {cmd_text}")
        return
    subprocess.run(cmd, cwd=str(cwd), check=True)


def ensure_design_dir(design_dir: Path, backend: str, config_path: Path) -> Path:
    design_dir.mkdir(parents=True, exist_ok=True)
    verilog_dir = design_dir / "verilog"
    verilog_dir.mkdir(parents=True, exist_ok=True)
    readme_path = design_dir / "README.md"
    if not readme_path.exists():
        readme_path.write_text(
            "\n".join(
                [
                    f"# {design_dir.name}",
                    "",
                    "Generated NPU fp16 backend block for OpenROAD sweeps.",
                    "",
                    f"- backend: `{backend}`",
                    f"- source config: `{config_path.relative_to(REPO_ROOT)}`",
                    "- top module: `npu_top`",
                    "",
                    "Use `npu/synth/run_fp16_backend_sweep.py` to refresh RTL and run sweeps.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    return verilog_dir


def export_backend_rtl(
    *,
    backend: str,
    config_path: Path,
    design_dir: Path,
    skip_export: bool,
) -> Dict[str, object]:
    verilog_dir = ensure_design_dir(design_dir, backend, config_path)
    config_hash = sha1_file(config_path)
    manifest_path = design_dir / "export_manifest.json"

    if skip_export:
        if not manifest_path.exists():
            raise FileNotFoundError(
                f"skip_export requested but missing manifest: {manifest_path}"
            )
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    top_module_name = design_dir.name

    with tempfile.TemporaryDirectory(prefix=f"rtlgen_{backend}_") as tmpdir:
        tmp_out = Path(tmpdir)
        run_cmd(
            [
                "python3",
                "npu/rtlgen/gen.py",
                "--config",
                str(config_path),
                "--out",
                str(tmp_out),
            ],
            cwd=REPO_ROOT,
        )

        top_src = tmp_out / "top.v"
        if not top_src.exists():
            raise FileNotFoundError(f"RTL export missing top.v: {top_src}")
        top_text = top_src.read_text(encoding="utf-8")
        top_text_renamed = re.sub(
            r"(^\s*module\s+)npu_top(\s*\()",
            rf"\1{top_module_name}\2",
            top_text,
            count=1,
            flags=re.MULTILINE,
        )
        if top_text_renamed == top_text:
            raise ValueError("Failed to rewrite top module name from npu_top")

        include_sources = sorted(tmp_out.glob("*.vh"))

        for stale in verilog_dir.glob("*"):
            if stale.is_file() and stale.suffix in (".v", ".vh"):
                stale.unlink()

        copied = []
        top_dst = verilog_dir / f"{top_module_name}.v"
        top_dst.write_text(top_text_renamed, encoding="utf-8")
        copied.append(top_dst)
        for src in include_sources:
            dst = verilog_dir / src.name
            shutil.copyfile(src, dst)
            copied.append(dst)

    manifest = {
        "backend": backend,
        "rtlgen_config": str(config_path.relative_to(REPO_ROOT)),
        "rtlgen_config_sha1": config_hash,
        "top_module": top_module_name,
        "verilog_files": [
            str(p.relative_to(REPO_ROOT)) for p in copied if p.suffix == ".v"
        ],
        "include_files": [
            str(p.relative_to(REPO_ROOT)) for p in copied if p.suffix == ".vh"
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_backend_sweep(
    *,
    design_dir: Path,
    top_module: str,
    platform: str,
    sweep_path: Path,
    make_target: Optional[str],
    skip_existing: bool,
    force_copy: bool,
    dry_run: bool,
    skip_sweep: bool,
) -> Optional[str]:
    cmd = [
        "python3",
        "npu/synth/run_block_sweep.py",
        "--design_dir",
        str(design_dir),
        "--platform",
        platform,
        "--top",
        top_module,
        "--sweep",
        str(sweep_path),
    ]
    if make_target:
        cmd.extend(["--make_target", make_target])
    if skip_existing:
        cmd.append("--skip_existing")
    if force_copy:
        cmd.append("--force_copy")
    if dry_run:
        cmd.append("--dry_run")
    if skip_sweep:
        run_cmd(cmd, cwd=REPO_ROOT, dry_print_only=True)
        return None
    else:
        try:
            run_cmd(cmd, cwd=REPO_ROOT)
            return None
        except subprocess.CalledProcessError as exc:
            return f"flow failed (exit {exc.returncode})"


def _to_float(value: object) -> Optional[float]:
    if value is None:
        return None
    txt = str(value).strip()
    if not txt:
        return None
    try:
        return float(txt)
    except ValueError:
        return None


def load_latest_metrics(design_dir: Path) -> Optional[Dict[str, object]]:
    work_dir = design_dir / "work"
    if work_dir.is_dir():
        candidates = sorted(
            work_dir.glob("*/result.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for result_path in candidates:
            try:
                row = json.loads(result_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            return {
                "status": row.get("status", ""),
                "tag": row.get("tag", ""),
                "critical_path_ns": _to_float(row.get("critical_path_ns")),
                "die_area": _to_float(row.get("die_area")),
                "total_power_mw": _to_float(row.get("total_power_mw")),
                "result_path": row.get("result_path", ""),
            }

    metrics_csv = design_dir / "metrics.csv"
    if not metrics_csv.exists():
        return None
    with metrics_csv.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None
    row = rows[-1]
    return {
        "status": row.get("status", ""),
        "tag": row.get("tag", ""),
        "critical_path_ns": _to_float(row.get("critical_path_ns")),
        "die_area": _to_float(row.get("die_area")),
        "total_power_mw": _to_float(row.get("total_power_mw")),
        "result_path": row.get("result_path", ""),
    }


def choose_backend(rows: List[Dict[str, object]]) -> Optional[str]:
    best_backend = None
    best_score = None
    for row in rows:
        if row.get("default_eligible") is False:
            continue
        if row.get("status") != "ok":
            continue
        cp = row.get("critical_path_ns")
        area = row.get("die_area")
        pwr = row.get("total_power_mw")
        if cp is None or area is None or pwr is None:
            continue
        score = float(cp) * float(area) * float(pwr)
        if best_score is None or score < best_score:
            best_score = score
            best_backend = str(row.get("backend"))
    return best_backend


def write_report(
    *,
    platform: str,
    sweep_path: Path,
    make_target: Optional[str],
    rows: List[Dict[str, object]],
    report_path: Path,
) -> None:
    recommended = choose_backend(rows)
    make_target_desc = make_target or "full_flow"
    lines = [
        f"# FP16 Backend Sweep ({platform})",
        "",
        "## Inputs",
        f"- sweep: `{sweep_path.relative_to(REPO_ROOT)}`",
        f"- make target: `{make_target_desc}`",
        "- compared backends: `builtin_raw16`, `cpp_ieee`",
        "",
        "## Latest Metrics",
        "| backend | eligible_default | status | tag | critical_path_ns | die_area_um2 | total_power_mw | result_path | notes |",
        "|---|---|---|---|---:|---:|---:|---|---|",
    ]
    for row in rows:
        cp = row.get("critical_path_ns")
        area = row.get("die_area")
        pwr = row.get("total_power_mw")
        lines.append(
            "| {backend} | {eligible} | {status} | {tag} | {cp} | {area} | {pwr} | {result_path} | {notes} |".format(
                backend=row.get("backend", ""),
                eligible="yes" if row.get("default_eligible", True) else "no",
                status=row.get("status", ""),
                tag=row.get("tag", ""),
                cp="" if cp is None else f"{cp:.4f}",
                area="" if area is None else f"{area:.4f}",
                pwr="" if pwr is None else f"{pwr:.4f}",
                result_path=row.get("result_path", ""),
                notes=row.get("notes", ""),
            )
        )

    lines.extend(
        [
            "",
            "## Recommendation",
        ]
    )
    if recommended is None:
        lines.append(
            "- No automatic recommendation yet. Run sweeps with successful metrics for default-eligible backends."
        )
    else:
        lines.append(
            f"- Recommended default backend: `{recommended}` (lowest `critical_path_ns * die_area * total_power_mw` among default-eligible backends)."
        )
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Run fp16 backend OpenROAD sweeps for NPU blocks")
    ap.add_argument("--platform", default="nangate45", help="OpenROAD platform name")
    ap.add_argument("--sweep", default=str(SWEEP_DEFAULT), help="Sweep JSON path")
    ap.add_argument(
        "--design_root",
        default=str(DESIGN_ROOT_DEFAULT),
        help="Design root directory (default: runs/designs/npu_blocks)",
    )
    ap.add_argument(
        "--report_out",
        help="Output markdown report path (default: <design_root>/fp16_backend_decision_<platform>.md)",
    )
    ap.add_argument(
        "--make_target",
        help="Optional OpenROAD make target to run (e.g., 3_5_place_dp, finish).",
    )
    ap.add_argument("--skip_existing", action="store_true", help="Pass through to run_block_sweep.py")
    ap.add_argument("--force_copy", action="store_true", help="Pass through to run_block_sweep.py")
    ap.add_argument("--dry_run", action="store_true", help="Dry-run inside run_block_sweep.py")
    ap.add_argument("--skip_export", action="store_true", help="Reuse existing verilog/ without regenerating RTL")
    ap.add_argument("--skip_sweep", action="store_true", help="Skip OpenROAD execution and only update report")
    args = ap.parse_args()

    sweep_path = Path(args.sweep).resolve()
    if not sweep_path.exists():
        raise FileNotFoundError(sweep_path)
    design_root = Path(args.design_root).resolve()
    design_root.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, object]] = []
    for entry in BACKENDS:
        backend = str(entry["backend"])
        design = str(entry["design"])
        config_path = Path(entry["rtlgen_config"]).resolve()
        default_eligible = bool(entry.get("default_eligible", True))
        default_note = str(entry.get("default_note", ""))
        design_dir = design_root / design
        export_backend_rtl(
            backend=backend,
            config_path=config_path,
            design_dir=design_dir,
            skip_export=args.skip_export,
        )
        sweep_error = run_backend_sweep(
            design_dir=design_dir,
            top_module=design,
            platform=args.platform,
            sweep_path=sweep_path,
            make_target=args.make_target,
            skip_existing=args.skip_existing,
            force_copy=args.force_copy,
            dry_run=args.dry_run,
            skip_sweep=args.skip_sweep,
        )

        latest = load_latest_metrics(design_dir)
        row = {
            "backend": backend,
            "design": design,
            "default_eligible": default_eligible,
            "status": "not_run",
            "tag": "",
            "critical_path_ns": None,
            "die_area": None,
            "total_power_mw": None,
            "result_path": "",
            "notes": default_note,
        }
        if latest is not None:
            row.update(latest)
        elif sweep_error is not None:
            row["status"] = "flow_error"
            row["notes"] = sweep_error
        rows.append(row)

    report_out = (
        Path(args.report_out).resolve()
        if args.report_out
        else (design_root / f"fp16_backend_decision_{args.platform}.md")
    )
    write_report(
        platform=args.platform,
        sweep_path=sweep_path,
        make_target=args.make_target,
        rows=rows,
        report_path=report_out,
    )
    print(f"[INFO] Wrote report: {report_out}")


if __name__ == "__main__":
    main()

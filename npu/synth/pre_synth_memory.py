#!/usr/bin/env python3
"""
Pre-synthesis SRAM modeling/generation stage.

Policy:
- Prefer a real SRAM macro-generation flow when available/configured.
- Fall back to CACTI estimation for early exploration.

Outputs:
- runs/designs/sram/<id>/sram_metrics.json (canonical for downstream use)
- runs/designs/sram/<id>/sram_metrics.pre_synth.json (stage snapshot)
- runs/designs/sram/<id>/pre_synth_memory.json (stage metadata)
"""

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_ROOT = REPO_ROOT / "runs" / "designs" / "sram"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid arch yaml format: {path}")
    return data


def detect_pdk(arch: dict[str, Any]) -> str:
    version = str(arch.get("schema_version", "")).strip()
    if version == "0.2-draft":
        platform = arch.get("platform", {})
        if isinstance(platform, dict):
            return str(platform.get("target_pdk", "")).strip()
        return ""
    sram = arch.get("sram", {})
    if not isinstance(sram, dict):
        return ""
    instances = sram.get("instances", [])
    if not isinstance(instances, list):
        return ""
    for inst in instances:
        if isinstance(inst, dict):
            pdk = str(inst.get("pdk", "")).strip()
            if pdk:
                return pdk
    return ""


def ensure_metrics_shape(metrics_path: Path) -> None:
    data = json.loads(metrics_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("metrics json must be an object")
    instances = data.get("instances")
    if not isinstance(instances, list):
        raise ValueError("metrics json must contain top-level 'instances' list")
    for idx, entry in enumerate(instances):
        if not isinstance(entry, dict):
            raise ValueError(f"instances[{idx}] must be an object")
        if "instance" not in entry or not isinstance(entry.get("instance"), dict):
            raise ValueError(
                f"instances[{idx}] must contain object field 'instance'"
            )


def run_command(
    cmd: list[str],
    *,
    cwd: Path,
    stdout_path: Path | None = None,
    stderr_path: Path | None = None,
) -> int:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if stdout_path is not None:
        stdout_path.write_text(proc.stdout or "", encoding="utf-8")
    if stderr_path is not None:
        stderr_path.write_text(proc.stderr or "", encoding="utf-8")
    return int(proc.returncode)


def run_memgen(
    *,
    arch_path: Path,
    design_id: str,
    design_dir: Path,
    pdk: str,
    memgen_cmd_template: str,
    memgen_metrics_template: str | None,
) -> tuple[bool, str, str]:
    pre_dir = design_dir / "pre_synth"
    memgen_dir = pre_dir / "memgen"
    memgen_dir.mkdir(parents=True, exist_ok=True)
    context = {
        "arch": str(arch_path),
        "id": design_id,
        "out_root": str(design_dir.parent),
        "out_dir": str(design_dir),
        "pre_dir": str(pre_dir),
        "memgen_dir": str(memgen_dir),
        "pdk": pdk,
    }

    try:
        cmd_text = memgen_cmd_template.format(**context)
    except Exception as exc:
        return False, "", f"invalid --memgen-cmd template: {exc}"

    if not cmd_text.strip():
        return False, "", "empty memgen command after template formatting"

    cmd = shlex.split(cmd_text)
    rc = run_command(
        cmd,
        cwd=REPO_ROOT,
        stdout_path=pre_dir / "memgen.stdout.log",
        stderr_path=pre_dir / "memgen.stderr.log",
    )
    if rc != 0:
        return False, cmd_text, f"memgen command failed (exit {rc})"

    if memgen_metrics_template:
        try:
            metrics_path = Path(memgen_metrics_template.format(**context))
        except Exception as exc:
            return False, cmd_text, f"invalid --memgen-metrics template: {exc}"
    else:
        metrics_path = memgen_dir / "sram_metrics.json"

    if not metrics_path.is_absolute():
        metrics_path = REPO_ROOT / metrics_path

    if not metrics_path.exists():
        return (
            False,
            cmd_text,
            f"memgen metrics not found at {metrics_path}",
        )

    try:
        ensure_metrics_shape(metrics_path)
    except Exception as exc:
        return (
            False,
            cmd_text,
            f"invalid memgen metrics format ({metrics_path}): {exc}",
        )

    canonical = design_dir / "sram_metrics.json"
    canonical.write_text(metrics_path.read_text(encoding="utf-8"), encoding="utf-8")
    (design_dir / "sram_metrics.pre_synth.json").write_text(
        canonical.read_text(encoding="utf-8"), encoding="utf-8"
    )
    return True, cmd_text, ""


def run_cacti_fallback(
    *,
    arch_path: Path,
    design_id: str,
    design_dir: Path,
    cacti_bin: str | None,
    cacti_dir: str | None,
    cacti_template: str | None,
) -> tuple[bool, list[str], str]:
    cmd = [
        sys.executable,
        str(REPO_ROOT / "npu" / "synth" / "sram_ppa.py"),
        str(arch_path),
        "--id",
        design_id,
        "--out-root",
        str(design_dir.parent),
    ]
    if cacti_bin:
        cmd.extend(["--cacti-bin", cacti_bin])
    if cacti_dir:
        cmd.extend(["--cacti-dir", cacti_dir])
    if cacti_template:
        cmd.extend(["--cacti-template", cacti_template])

    rc = run_command(
        cmd,
        cwd=REPO_ROOT,
        stdout_path=design_dir / "pre_synth" / "cacti.stdout.log",
        stderr_path=design_dir / "pre_synth" / "cacti.stderr.log",
    )
    if rc != 0:
        return False, cmd, f"cacti fallback failed (exit {rc})"

    canonical = design_dir / "sram_metrics.json"
    if not canonical.exists():
        return False, cmd, f"expected CACTI metrics missing: {canonical}"
    try:
        ensure_metrics_shape(canonical)
    except Exception as exc:
        return False, cmd, f"invalid CACTI metrics format: {exc}"

    (design_dir / "sram_metrics.pre_synth.json").write_text(
        canonical.read_text(encoding="utf-8"), encoding="utf-8"
    )
    return True, cmd, ""


def run_summary(design_id: str, out_root: Path) -> tuple[bool, str]:
    cmd = [
        sys.executable,
        str(REPO_ROOT / "npu" / "synth" / "aggregate_sram_metrics.py"),
        "--id",
        design_id,
        "--root",
        str(out_root),
    ]
    rc = run_command(cmd, cwd=REPO_ROOT)
    if rc != 0:
        return False, f"summary aggregation failed (exit {rc})"
    return True, ""


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Run pre-synthesis SRAM flow (memgen first, CACTI fallback)."
    )
    ap.add_argument("arch", type=Path, help="Architecture YAML")
    ap.add_argument("--id", required=True, help="Design ID under runs/designs/sram/<id>")
    ap.add_argument(
        "--out-root",
        type=Path,
        default=DEFAULT_OUT_ROOT,
        help="SRAM metrics root (default: runs/designs/sram)",
    )
    ap.add_argument(
        "--mode",
        choices=("auto", "memgen_only", "cacti_only"),
        default="auto",
        help="Stage mode: auto (default), memgen_only, or cacti_only.",
    )
    ap.add_argument(
        "--memgen-cmd",
        default="",
        help=(
            "External memory-generator command template. "
            "Placeholders: {arch} {id} {out_root} {out_dir} {pre_dir} {memgen_dir} {pdk}"
        ),
    )
    ap.add_argument(
        "--memgen-metrics",
        default="",
        help=(
            "Metrics JSON path template produced by memgen. "
            "If omitted, defaults to {memgen_dir}/sram_metrics.json."
        ),
    )
    ap.add_argument("--cacti-bin", default="", help="Override path to CACTI binary")
    ap.add_argument("--cacti-dir", default="", help="Override CACTI directory")
    ap.add_argument("--cacti-template", default="", help="Override CACTI template path")
    args = ap.parse_args()

    arch_path = args.arch.resolve()
    if not arch_path.exists():
        print(f"Missing arch config: {arch_path}", file=sys.stderr)
        return 1

    arch = load_yaml(arch_path)
    pdk = detect_pdk(arch)
    design_dir = args.out_root.resolve() / args.id
    pre_dir = design_dir / "pre_synth"
    pre_dir.mkdir(parents=True, exist_ok=True)

    memgen_cmd = str(args.memgen_cmd).strip()
    if not memgen_cmd:
        memgen_cmd = os.environ.get("NPU_SRAM_MEMGEN_CMD", "").strip()
    memgen_metrics = str(args.memgen_metrics).strip() or None

    selected_source = ""
    failure_reason = ""
    memgen_cmd_effective = ""

    if args.mode != "cacti_only":
        if memgen_cmd:
            ok, cmd_text, reason = run_memgen(
                arch_path=arch_path,
                design_id=args.id,
                design_dir=design_dir,
                pdk=pdk,
                memgen_cmd_template=memgen_cmd,
                memgen_metrics_template=memgen_metrics,
            )
            memgen_cmd_effective = cmd_text
            if ok:
                selected_source = "memgen"
                print("pre_synth_memory: selected source = memgen")
            else:
                failure_reason = reason
                print(f"pre_synth_memory: memgen failed: {reason}", file=sys.stderr)
                if args.mode == "memgen_only":
                    return 1
        elif args.mode == "memgen_only":
            print(
                "pre_synth_memory: memgen_only mode requires --memgen-cmd or NPU_SRAM_MEMGEN_CMD",
                file=sys.stderr,
            )
            return 1

    if not selected_source:
        ok, cmd_vec, reason = run_cacti_fallback(
            arch_path=arch_path,
            design_id=args.id,
            design_dir=design_dir,
            cacti_bin=str(args.cacti_bin).strip() or None,
            cacti_dir=str(args.cacti_dir).strip() or None,
            cacti_template=str(args.cacti_template).strip() or None,
        )
        if not ok:
            print(f"pre_synth_memory: {reason}", file=sys.stderr)
            return 1
        selected_source = "cacti_fallback"
        print(f"pre_synth_memory: selected source = cacti_fallback ({' '.join(cmd_vec)})")

    meta = {
        "stage": "pre_synth_memory",
        "source": selected_source,
        "arch": str(arch_path),
        "id": args.id,
        "pdk": pdk,
        "mode": args.mode,
        "memgen_cmd_effective": memgen_cmd_effective,
        "memgen_failure_reason": failure_reason,
        "canonical_metrics": str((design_dir / "sram_metrics.json").resolve()),
        "stage_metrics": str((design_dir / "sram_metrics.pre_synth.json").resolve()),
    }
    (design_dir / "pre_synth_memory.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )

    ok, summary_reason = run_summary(args.id, args.out_root.resolve())
    if not ok:
        print(f"pre_synth_memory: warning: {summary_reason}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

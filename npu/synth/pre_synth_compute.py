#!/usr/bin/env python3
"""
Pre-synthesis compute macro hardening stage.

Goal:
- Harden a C++ RTLGen-generated arithmetic block (adder/multiplier/mac/fp_mac)
  as a macro abstract (LEF/LIB) before top-level NPU floorplanning.
- Emit a manifest consumable by npu/synth/run_block_sweep.py (--macro_manifest).
"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_ROOT = REPO_ROOT / "runs" / "designs" / "npu_macros"


def sha1_file(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid JSON object: {path}")
    return data


def infer_module_name(cfg: dict[str, Any], override: str) -> str:
    if override:
        return override

    ops = cfg.get("operations")
    if isinstance(ops, list):
        op_modules = [
            str(op.get("module_name", "")).strip()
            for op in ops
            if isinstance(op, dict) and str(op.get("module_name", "")).strip()
        ]
        op_modules = list(dict.fromkeys(op_modules))
        if len(op_modules) == 1:
            return op_modules[0]
        if len(op_modules) > 1:
            raise ValueError(
                "Multiple module_name values found in operations[]; "
                "pass --module explicitly."
            )

    for key in (
        "adder",
        "multiplier",
        "multiplier_yosys",
        "mac",
        "fp_mac",
        "fp_mul",
        "fp_add",
        "activation",
        "mcm",
        "cmvm",
    ):
        section = cfg.get(key)
        if isinstance(section, dict):
            name = str(section.get("module_name", "")).strip()
            if name:
                return name

    raise ValueError("Could not infer module name from config; pass --module.")


def rel_or_abs(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def emit_blackbox_stub(module_src: Path, module_name: str, out_path: Path) -> None:
    text = module_src.read_text(encoding="utf-8")
    m = re.search(
        rf"\bmodule\s+{re.escape(module_name)}\b[\s\S]*?\);\s*",
        text,
        flags=re.MULTILINE,
    )
    if not m:
        raise ValueError(f"Could not extract module header for {module_name} from {module_src}")
    header = m.group(0).strip()
    out_path.write_text(f"(* blackbox *)\n{header}\nendmodule\n", encoding="utf-8")


def discover_module_file(candidates: list[Path], module_name: str) -> Path:
    patt = re.compile(rf"\bmodule\s+{re.escape(module_name)}\b", flags=re.MULTILINE)
    for path in candidates:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if patt.search(text):
            return path
    raise FileNotFoundError(
        f"Could not locate module '{module_name}' declaration in candidate files."
    )


def collect_verilog_like_files(src_dir: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in ("*.v", "*.vh", "*.sv", "*.svh"):
        files.extend(sorted(src_dir.glob(pattern)))
    uniq: dict[str, Path] = {}
    for path in files:
        uniq[str(path.resolve())] = path
    return [uniq[k] for k in sorted(uniq.keys())]


def sha1_file_set(paths: list[Path]) -> str:
    digest = hashlib.sha1()
    for path in sorted(paths, key=lambda p: str(p.resolve())):
        digest.update(str(path.resolve()).encode("utf-8"))
        digest.update(sha1_file(path).encode("utf-8"))
    return digest.hexdigest()


def copy_unique_files(src_files: list[Path], dst_dir: Path) -> list[Path]:
    copied: list[Path] = []
    seen_by_hash: dict[str, Path] = {}
    for src in sorted(src_files, key=lambda p: str(p.resolve())):
        file_hash = sha1_file(src)
        if file_hash in seen_by_hash:
            continue
        dst = dst_dir / src.name
        shutil.copy(src, dst)
        seen_by_hash[file_hash] = src
        copied.append(dst)
    return copied


def parse_key_value_list(values: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in values:
        token = str(raw).strip()
        if not token:
            continue
        if "=" not in token:
            raise ValueError(f"Invalid key=value token: {raw}")
        key, value = token.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"Invalid empty key in token: {raw}")
        out[key] = value
    return out


def build_sweep_spec(args: argparse.Namespace) -> dict[str, Any]:
    flow_params: dict[str, Any] = {
        "CLOCK_PERIOD": [float(args.clock_period)],
        "CLOCK_PORT": [args.clock_port],
        "PLACE_DENSITY": [float(args.place_density)],
        "FLOW_VARIANT": [args.flow_variant],
    }

    if args.die_area and args.core_area:
        flow_params["DIE_AREA"] = [args.die_area]
        flow_params["CORE_AREA"] = [args.core_area]
    else:
        flow_params["CORE_UTILIZATION"] = [int(args.core_utilization)]

    return {
        "flow_params": flow_params,
        "tag_prefix": args.tag_prefix,
    }


def run_cmd(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=str(cwd), check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Pre-synthesize compute macro and emit LEF/LIB manifest")
    ap.add_argument(
        "--config",
        help="C++ RTLGen JSON config for a macro block (mode A)",
    )
    ap.add_argument(
        "--src_verilog_dir",
        help=(
            "Existing RTL source directory containing the target module and "
            "dependencies (mode B)"
        ),
    )
    ap.add_argument(
        "--src_module_file",
        default="",
        help=(
            "Optional source file containing --module when using --src_verilog_dir. "
            "Defaults to <src_verilog_dir>/<module>.v or auto-discovery."
        ),
    )
    ap.add_argument("--platform", required=True, help="OpenROAD platform (e.g., nangate45)")
    ap.add_argument("--rtlgen_bin", default="rtlgen", help="Path to C++ rtlgen binary")
    ap.add_argument("--module", default="", help="Override module name to harden")
    ap.add_argument("--id", default="", help="Output design id (default: <module>_<hash8>_<platform>)")
    ap.add_argument("--out_root", default=str(DEFAULT_OUT_ROOT), help="Output root directory")
    ap.add_argument("--flow_variant", default="base", help="OpenROAD FLOW_VARIANT for macro hardening")
    ap.add_argument("--clock_period", type=float, default=10.0, help="Clock period for macro hardening")
    ap.add_argument(
        "--clock_port",
        default="",
        help="Clock port name; leave empty for combinational blocks",
    )
    ap.add_argument("--place_density", type=float, default=0.40, help="PLACE_DENSITY for macro hardening")
    ap.add_argument("--die_area", default="0 0 400 400", help="DIE_AREA rectangle string")
    ap.add_argument("--core_area", default="20 20 380 380", help="CORE_AREA rectangle string")
    ap.add_argument(
        "--core_utilization",
        type=int,
        default=30,
        help="CORE_UTILIZATION when --die_area/--core_area are not used",
    )
    ap.add_argument(
        "--make_target",
        default="generate_abstract",
        help="OpenROAD make target to run (default: generate_abstract)",
    )
    ap.add_argument("--tag_prefix", default="npu_macro", help="Tag prefix for run_block_sweep")
    ap.add_argument(
        "--manifest_param",
        action="append",
        default=[],
        help=(
            "Optional metadata key=value attached to macro_manifest.json "
            "for architecture/sweep matching (repeatable)."
        ),
    )
    ap.add_argument("--skip_existing", action="store_true", help="Skip if macro_manifest.json exists")
    ap.add_argument("--dry_run", action="store_true", help="Dry run (no OpenROAD execution)")
    args = ap.parse_args()

    use_cfg_mode = bool(args.config)
    use_src_mode = bool(args.src_verilog_dir)
    if use_cfg_mode == use_src_mode:
        raise ValueError("Pass exactly one of --config or --src_verilog_dir.")
    manifest_params = parse_key_value_list(args.manifest_param)

    rtlgen_bin: Path | None = None
    config_path: Path | None = None
    source_info: dict[str, Any]
    module_name = ""
    config_hash = ""
    src_verilog_dir: Path | None = None
    src_module_file: Path | None = None

    if use_cfg_mode:
        config_path = Path(str(args.config)).resolve()
        if not config_path.exists():
            raise FileNotFoundError(config_path)
        rtlgen_bin = Path(args.rtlgen_bin)
        if not rtlgen_bin.is_absolute():
            rtlgen_bin = (REPO_ROOT / rtlgen_bin).resolve()
        if not rtlgen_bin.exists():
            raise FileNotFoundError(f"rtlgen binary not found: {rtlgen_bin}")

        cfg = load_json(config_path)
        module_name = infer_module_name(cfg, args.module)
        config_hash = sha1_file(config_path)
        source_info = {
            "mode": "rtlgen_cpp_config",
            "rtlgen_config": rel_or_abs(config_path),
            "rtlgen_config_sha1": config_hash,
            "rtlgen_bin": rel_or_abs(rtlgen_bin),
        }
    else:
        src_verilog_dir = Path(str(args.src_verilog_dir)).resolve()
        if not src_verilog_dir.exists() or not src_verilog_dir.is_dir():
            raise FileNotFoundError(f"Source verilog dir not found: {src_verilog_dir}")
        if not args.module.strip():
            raise ValueError("--module is required when using --src_verilog_dir")
        module_name = args.module.strip()
        src_files = collect_verilog_like_files(src_verilog_dir)
        if not src_files:
            raise FileNotFoundError(f"No Verilog-like sources found in {src_verilog_dir}")
        config_hash = sha1_file_set(src_files)
        if args.src_module_file:
            src_module_file = Path(args.src_module_file)
            if not src_module_file.is_absolute():
                src_module_file = (src_verilog_dir / src_module_file).resolve()
            if not src_module_file.exists():
                raise FileNotFoundError(f"Source module file not found: {src_module_file}")
        else:
            preferred_v = src_verilog_dir / f"{module_name}.v"
            preferred_sv = src_verilog_dir / f"{module_name}.sv"
            if preferred_v.exists():
                src_module_file = preferred_v
            elif preferred_sv.exists():
                src_module_file = preferred_sv
            else:
                src_module_file = discover_module_file(
                    [p for p in src_files if p.suffix.lower() in (".v", ".sv")],
                    module_name,
                )
        source_info = {
            "mode": "existing_verilog",
            "verilog_dir": rel_or_abs(src_verilog_dir),
            "module_file": rel_or_abs(src_module_file),
            "verilog_sha1": config_hash,
        }

    design_id = args.id or f"{module_name}_{config_hash[:8]}_{args.platform}"

    out_root = Path(args.out_root).resolve()
    design_dir = out_root / design_id
    verilog_dir = design_dir / "verilog"
    abstract_dir = design_dir / "abstract"
    manifest_path = design_dir / "macro_manifest.json"
    sweep_path = design_dir / "pre_synth_sweep.json"

    if args.skip_existing and manifest_path.exists():
        print(f"[INFO] Reusing existing manifest: {manifest_path}")
        return 0

    verilog_dir.mkdir(parents=True, exist_ok=True)
    abstract_dir.mkdir(parents=True, exist_ok=True)

    for stale in verilog_dir.glob("*"):
        if stale.is_file():
            stale.unlink()

    if use_cfg_mode:
        assert rtlgen_bin is not None and config_path is not None
        with tempfile.TemporaryDirectory(prefix=f"rtlgen_macro_{design_id}_") as tmp:
            tmp_dir = Path(tmp)
            run_cmd([str(rtlgen_bin), str(config_path)], cwd=tmp_dir)

            generated = sorted(
                list(tmp_dir.glob("*.v"))
                + list(tmp_dir.glob("*.vh"))
                + list(tmp_dir.glob("*.sv"))
                + list(tmp_dir.glob("*.svh"))
            )
            if not generated:
                raise RuntimeError("rtlgen did not emit any .v/.vh/.sv/.svh files")
            module_file = tmp_dir / f"{module_name}.v"
            if not module_file.exists():
                module_file = tmp_dir / f"{module_name}.sv"
            if not module_file.exists():
                module_file = discover_module_file(
                    [p for p in generated if p.suffix.lower() in (".v", ".sv")],
                    module_name,
                )

            copy_unique_files(generated, verilog_dir)

            blackbox_stub = abstract_dir / f"{module_name}_blackbox.v"
            emit_blackbox_stub(module_file, module_name, blackbox_stub)
    else:
        assert src_verilog_dir is not None and src_module_file is not None
        src_files = collect_verilog_like_files(src_verilog_dir)
        copy_unique_files(src_files, verilog_dir)
        blackbox_stub = abstract_dir / f"{module_name}_blackbox.v"
        emit_blackbox_stub(src_module_file, module_name, blackbox_stub)

    sweep_spec = build_sweep_spec(args)
    sweep_path.write_text(json.dumps(sweep_spec, indent=2) + "\n", encoding="utf-8")

    run_block_cmd = [
        "python3",
        "npu/synth/run_block_sweep.py",
        "--design_dir",
        str(design_dir),
        "--platform",
        args.platform,
        "--top",
        module_name,
        "--sweep",
        str(sweep_path),
        "--make_target",
        args.make_target,
        "--force_copy",
    ]
    if args.skip_existing:
        run_block_cmd.append("--skip_existing")
    if args.dry_run:
        run_block_cmd.append("--dry_run")
    run_cmd(run_block_cmd, cwd=REPO_ROOT)

    flow_variant = args.flow_variant
    flow_results = Path("/orfs/flow/results") / args.platform / design_id / flow_variant
    if not flow_results.exists():
        flow_results = Path("/orfs/flow/results") / args.platform / design_id / "base"

    lef_src = flow_results / f"{module_name}.lef"
    lib_src = flow_results / f"{module_name}_typ.lib"
    if not lib_src.exists():
        alt = flow_results / f"{module_name}.lib"
        if alt.exists():
            lib_src = alt

    gds_src = flow_results / "6_final.gds"
    def_src = flow_results / "6_final.def"

    if not args.dry_run:
        if not lef_src.exists():
            raise FileNotFoundError(f"Missing abstract LEF: {lef_src}")
        if not lib_src.exists():
            raise FileNotFoundError(f"Missing abstract LIB: {lib_src}")
        shutil.copy(lef_src, abstract_dir / lef_src.name)
        shutil.copy(lib_src, abstract_dir / lib_src.name)
        if gds_src.exists():
            shutil.copy(gds_src, abstract_dir / gds_src.name)
        if def_src.exists():
            shutil.copy(def_src, abstract_dir / def_src.name)

    manifest = {
        "version": "0.1",
        "design_id": design_id,
        "module": module_name,
        "platform": args.platform,
        "flow_variant": flow_variant,
        "blackboxes": [module_name],
        "additional_lefs": [rel_or_abs((abstract_dir / lef_src.name).resolve())],
        "additional_libs": [rel_or_abs((abstract_dir / lib_src.name).resolve())],
        "additional_gds": (
            [rel_or_abs((abstract_dir / gds_src.name).resolve())]
            if (abstract_dir / gds_src.name).exists()
            else []
        ),
        "blackbox_verilog": [rel_or_abs((abstract_dir / f"{module_name}_blackbox.v").resolve())],
        "source": source_info,
        "manifest_params": manifest_params,
        "sweep": rel_or_abs(sweep_path),
        "make_target": args.make_target,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"[INFO] Hardened macro manifest: {manifest_path}")
    print(
        "[INFO] Use with top-level sweeps:\n"
        f"  python3 npu/synth/run_block_sweep.py ... --macro_manifest {manifest_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

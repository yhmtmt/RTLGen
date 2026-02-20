#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


DEFAULT_TOP_NAME = "npu_top"
DEFAULT_MMIO_ADDR_WIDTH = 12
DEFAULT_DATA_WIDTH = 32

ARCH_DIR = Path(__file__).resolve().parent
SCHEMA_V01 = ARCH_DIR / "schema.yml"
SCHEMA_V02_DRAFT = ARCH_DIR / "schema_v0_2_draft.yml"


SUPPORTED_VEC_OPS = {
    "add",
    "mul",
    "relu",
    "gelu",
    "softmax",
    "layernorm",
    "drelu",
    "dgelu",
    "dsoftmax",
    "dlayernorm",
}


def die(msg: str) -> None:
    print(f"to_rtlgen: {msg}", file=sys.stderr)
    raise SystemExit(1)


def load_yaml(path: Path):
    with path.open() as f:
        return yaml.safe_load(f)


def validate_schema(config: dict, schema: dict):
    missing = []
    for key in schema.get("required", []):
        if key not in config:
            missing.append(key)
    return missing


def as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def nested_get(obj: Any, path: list[str], default: Any = None) -> Any:
    cur = obj
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def normalize_int_list(values: Any, field: str) -> list[int]:
    out = []
    for v in as_list(values):
        try:
            out.append(int(v))
        except Exception as exc:
            die(f"{field} must contain integers: {exc}")
    return out


def normalize_str_list(values: Any) -> list[str]:
    out = []
    for v in as_list(values):
        out.append(str(v).strip())
    return out


def unique_preserve(items: list[Any]) -> list[Any]:
    seen = set()
    out = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def resolve_history_path(raw_path: str, arch_dir: Path) -> Path | None:
    if not raw_path:
        return None
    p = Path(raw_path)
    if p.is_absolute():
        return p
    cwd_path = Path.cwd() / p
    if cwd_path.exists():
        return cwd_path
    arch_rel = arch_dir / p
    if arch_rel.exists():
        return arch_rel
    return cwd_path


def extract_rtlgen_cfg_from_history(record: Any) -> dict | None:
    if not isinstance(record, dict):
        return None
    if isinstance(record.get("rtlgen_config"), dict):
        return record["rtlgen_config"]
    if isinstance(record.get("candidate"), dict):
        cand = record["candidate"]
        if isinstance(cand.get("rtlgen_config"), dict):
            return cand["rtlgen_config"]
        if cand.get("version") == "0.1":
            return cand
    if record.get("version") == "0.1":
        return record
    return None


def load_history_rtlgen_cfgs(history_path: Path | None) -> list[dict]:
    if history_path is None or not history_path.exists():
        return []
    cfgs: list[dict] = []
    try:
        with history_path.open("r", encoding="utf-8") as f:
            for line in f:
                txt = line.strip()
                if not txt:
                    continue
                try:
                    obj = json.loads(txt)
                except json.JSONDecodeError:
                    continue
                cfg = extract_rtlgen_cfg_from_history(obj)
                if isinstance(cfg, dict):
                    cfgs.append(cfg)
    except OSError:
        return []
    return cfgs


def find_history_value(history_cfgs: list[dict], path: list[str]) -> Any:
    for cfg in reversed(history_cfgs):
        value = nested_get(cfg, path, default=None)
        if value is not None:
            return value
    return None


def choose_scalar(
    candidates: list[Any],
    fallback: Any,
    history_value: Any = None,
    predicate=lambda _: True,
) -> Any:
    cands = [c for c in unique_preserve(candidates) if predicate(c)]
    if history_value is not None and predicate(history_value):
        if not cands or history_value in cands:
            return history_value
    if cands:
        return cands[0]
    if fallback is not None and predicate(fallback):
        return fallback
    if history_value is not None and predicate(history_value):
        return history_value
    die("unable to choose a valid value from candidates/fallback/history")


def auto_schema_path(arch_cfg: dict) -> Path:
    version = str(arch_cfg.get("schema_version", "")).strip()
    if version == "0.2-draft":
        return SCHEMA_V02_DRAFT
    return SCHEMA_V01


def build_rtlgen_config_v01(arch: dict, args: argparse.Namespace):
    shell = arch["shell"]
    dma = arch["dma"]
    axi = arch["axi"]
    sram = arch["sram"]
    return {
        "version": "0.1",
        "top_name": args.top_name,
        "mmio_addr_width": args.mmio_addr_width,
        "data_width": args.data_width,
        "queue_depth": int(shell["command_queue_depth"]),
        "enable_irq": bool(shell["supports_interrupts"]),
        "enable_dma_ports": args.enable_dma_ports,
        "enable_cq_mem_ports": args.enable_cq_mem_ports,
        "enable_axi_ports": args.enable_axi_ports,
        "enable_axi_lite_wrapper": args.enable_axi_lite_wrapper,
        "dma_addr_width": int(dma["addr_width"]),
        "dma_data_width": int(dma["data_width"]),
        "axi_addr_width": int(axi["addr_width"]),
        "axi_data_width": int(axi["data_width"]),
        "axi_id_width": int(axi["id_width"]),
        "sram_instances": sram.get("instances", []),
    }


def select_compute_tile(arch: dict, tile_name: str | None) -> dict:
    macros = arch.get("macros", {})
    tiles = as_list(macros.get("compute_tiles", []))
    if not tiles:
        die("v0.2-draft requires macros.compute_tiles")
    if tile_name:
        for tile in tiles:
            if str(tile.get("name")) == tile_name:
                return tile
        die(f"requested tile not found: {tile_name}")
    for tile in tiles:
        if int(tile.get("count", 1)) > 0:
            return tile
    return tiles[0]


def derive_gemm_cfg(
    tile_gemm: dict,
    history_cfgs: list[dict],
    rtlgen_binary_path: str,
) -> dict:
    mac_type_candidates = [x.lower() for x in normalize_str_list(tile_gemm.get("mac_type_candidates", ["int8"]))]
    hist_mac_type = find_history_value(history_cfgs, ["compute", "gemm", "mac_type"])
    mac_type = choose_scalar(
        mac_type_candidates,
        "int8",
        str(hist_mac_type).lower() if hist_mac_type is not None else None,
        predicate=lambda x: str(x).lower() in ("int8", "int16", "fp16"),
    )
    mac_type = str(mac_type).lower()

    backend_candidates = [x.lower() for x in normalize_str_list(tile_gemm.get("mac_backend_candidates", []))]
    if not backend_candidates:
        if mac_type == "int16":
            backend_candidates = ["builtin_int16_dot"]
        elif mac_type == "fp16":
            backend_candidates = ["rtlgen_cpp", "builtin_fp16_dot"]
        else:
            backend_candidates = ["builtin_int8_dot", "rtlgen_cpp"]

    valid_backend_by_type = {
        "int8": {"builtin", "builtin_int8_dot", "rtlgen_cpp"},
        "int16": {"builtin", "builtin_int16_dot"},
        "fp16": {"builtin", "builtin_fp16_dot", "rtlgen_cpp"},
    }
    backend_candidates = [
        b for b in backend_candidates if b in valid_backend_by_type[mac_type]
    ]
    hist_backend = find_history_value(history_cfgs, ["compute", "gemm", "mac_source"])
    default_backend = (
        "builtin_int16_dot"
        if mac_type == "int16"
        else ("rtlgen_cpp" if mac_type == "fp16" else "builtin_int8_dot")
    )
    mac_source = choose_scalar(
        backend_candidates,
        default_backend,
        str(hist_backend).lower() if hist_backend is not None else None,
        predicate=lambda x: str(x).lower() in valid_backend_by_type[mac_type],
    )
    mac_source = str(mac_source).lower()

    lanes_candidates = normalize_int_list(tile_gemm.get("lanes_candidates", []), "macros.compute_tiles[].gemm.lanes_candidates")
    if not lanes_candidates:
        lanes_candidates = [8 if mac_type == "int8" else 4]
    hist_lanes = find_history_value(history_cfgs, ["compute", "gemm", "lanes"])

    def valid_lanes(v: Any) -> bool:
        try:
            n = int(v)
        except Exception:
            return False
        if mac_type in ("int16", "fp16") and not (1 <= n <= 4):
            return False
        if mac_type == "int8" and not (1 <= n <= 8):
            return False
        if mac_source == "rtlgen_cpp" and mac_type in ("int8", "fp16") and n != 1:
            return False
        return True

    lanes_default = 1 if (mac_source == "rtlgen_cpp" and mac_type in ("int8", "fp16")) else (4 if mac_type in ("int16", "fp16") else 8)
    lanes = int(choose_scalar(lanes_candidates, lanes_default, hist_lanes, predicate=valid_lanes))

    accum_candidates = normalize_int_list(tile_gemm.get("accum_width_candidates", []), "macros.compute_tiles[].gemm.accum_width_candidates")
    if not accum_candidates:
        accum_candidates = [16 if (mac_source == "rtlgen_cpp" and mac_type in ("int8", "fp16")) else 32]
    hist_accum = find_history_value(history_cfgs, ["compute", "gemm", "accum_width"])

    def valid_accum(v: Any) -> bool:
        try:
            n = int(v)
        except Exception:
            return False
        if not (16 <= n <= 64):
            return False
        if mac_source == "rtlgen_cpp" and mac_type in ("int8", "fp16") and n != 16:
            return False
        return True

    accum_default = 16 if (mac_source == "rtlgen_cpp" and mac_type in ("int8", "fp16")) else 32
    accum_width = int(choose_scalar(accum_candidates, accum_default, hist_accum, predicate=valid_accum))

    pipeline_candidates = normalize_int_list(tile_gemm.get("pipeline_candidates", []), "macros.compute_tiles[].gemm.pipeline_candidates")
    if not pipeline_candidates:
        pipeline_candidates = [1]
    hist_pipe = find_history_value(history_cfgs, ["compute", "gemm", "pipeline"])
    pipeline = int(choose_scalar(pipeline_candidates, 1, hist_pipe, predicate=lambda x: int(x) >= 1))

    gemm_cfg: dict[str, Any] = {
        "mac_type": mac_type,
        "mac_source": mac_source,
        "lanes": lanes,
        "accum_width": accum_width,
        "pipeline": pipeline,
    }

    # Enforce currently-supported fp16 policy combinations from npu/rtlgen/gen.py.
    if mac_type == "fp16":
        if mac_source == "rtlgen_cpp":
            fp16_policy = {
                "semantics": "ieee_half",
                "accumulation": "fp16",
                "rounding": "rne",
                "subnormals": "preserve",
            }
        else:
            fp16_policy = {
                "semantics": "raw16_placeholder",
                "accumulation": "int32",
                "rounding": "rne",
                "subnormals": "preserve",
            }
        gemm_cfg["fp16"] = fp16_policy

    if mac_source == "rtlgen_cpp":
        rtlgen_cpp_cfg = tile_gemm.get("rtlgen_cpp", {}) or {}
        if not isinstance(rtlgen_cpp_cfg, dict):
            die("macros.compute_tiles[].gemm.rtlgen_cpp must be an object when provided")

        if mac_type == "fp16":
            module_name = "gemm_mac_fp16_ieee"
            gemm_cfg["rtlgen_cpp"] = {
                "binary_path": rtlgen_binary_path,
                "module_name": module_name,
                "total_width": 16,
                "mantissa_width": 10,
            }
        else:
            hist_ppg = find_history_value(history_cfgs, ["compute", "gemm", "rtlgen_cpp", "ppg_algorithm"])
            hist_comp = find_history_value(history_cfgs, ["compute", "gemm", "rtlgen_cpp", "compressor_structure"])
            hist_cpa = find_history_value(history_cfgs, ["compute", "gemm", "rtlgen_cpp", "cpa_structure"])
            ppg = choose_scalar(
                [x for x in normalize_str_list(rtlgen_cpp_cfg.get("ppg_algorithm_candidates", [])) if x],
                "Booth4",
                hist_ppg,
            )
            comp = choose_scalar(
                [x for x in normalize_str_list(rtlgen_cpp_cfg.get("compressor_structure_candidates", [])) if x],
                "AdderTree",
                hist_comp,
            )
            cpa = choose_scalar(
                [x for x in normalize_str_list(rtlgen_cpp_cfg.get("cpa_structure_candidates", [])) if x],
                "BrentKung",
                hist_cpa,
            )
            gemm_cfg["rtlgen_cpp"] = {
                "binary_path": rtlgen_binary_path,
                "module_name": "gemm_mac_int8_pp",
                "ppg_algorithm": ppg,
                "compressor_structure": comp,
                "compressor_library": "fa_ha",
                "compressor_assignment": "legacy_fa_ha",
                "cpa_structure": cpa,
            }

    return gemm_cfg


def derive_vec_cfg(
    tile_vec: dict,
    history_cfgs: list[dict],
    rtlgen_binary_path: str,
) -> dict:
    if not isinstance(tile_vec, dict):
        tile_vec = {}

    hist_activation_source = find_history_value(history_cfgs, ["compute", "vec", "activation_source"])
    hist_fp16_arith_source = find_history_value(history_cfgs, ["compute", "vec", "fp16_arith_source"])

    activation_candidates = [x.lower() for x in normalize_str_list(tile_vec.get("activation_source_candidates", ["builtin"]))]
    fp16_arith_candidates = [x.lower() for x in normalize_str_list(tile_vec.get("fp16_arith_source_candidates", ["builtin"]))]

    activation_source = choose_scalar(
        activation_candidates,
        "builtin",
        str(hist_activation_source).lower() if hist_activation_source is not None else None,
        predicate=lambda x: str(x).lower() in ("builtin", "rtlgen_cpp"),
    )
    activation_source = str(activation_source).lower()

    fp16_arith_source = choose_scalar(
        fp16_arith_candidates,
        "builtin",
        str(hist_fp16_arith_source).lower() if hist_fp16_arith_source is not None else None,
        predicate=lambda x: str(x).lower() in ("builtin", "rtlgen_cpp"),
    )
    fp16_arith_source = str(fp16_arith_source).lower()

    lanes_candidates = normalize_int_list(tile_vec.get("lanes_candidates", []), "macros.compute_tiles[].vec.lanes_candidates")
    if not lanes_candidates:
        lanes_candidates = [8]
    hist_lanes = find_history_value(history_cfgs, ["compute", "vec", "lanes"])

    def valid_vec_lanes(v: Any) -> bool:
        try:
            n = int(v)
        except Exception:
            return False
        if not (1 <= n <= 8):
            return False
        if fp16_arith_source == "rtlgen_cpp":
            return (n >= 2) and ((n % 2) == 0)
        return True

    vec_lanes_default = 4 if fp16_arith_source == "rtlgen_cpp" else 8
    vec_lanes = int(choose_scalar(lanes_candidates, vec_lanes_default, hist_lanes, predicate=valid_vec_lanes))

    ops_supported = [x.lower() for x in normalize_str_list(tile_vec.get("ops_supported", []))]
    if not ops_supported:
        ops_supported = ["add", "mul", "relu"]
    unknown_ops = sorted({op for op in ops_supported if op not in SUPPORTED_VEC_OPS})
    if unknown_ops:
        die(f"unsupported vec ops in arch v0.2 draft: {unknown_ops}")

    hist_ops = find_history_value(history_cfgs, ["compute", "vec", "ops"])
    if isinstance(hist_ops, list):
        hist_ops_norm = [str(x).lower() for x in hist_ops]
        if hist_ops_norm and all(op in SUPPORTED_VEC_OPS for op in hist_ops_norm):
            if set(hist_ops_norm).issubset(set(ops_supported)):
                ops = unique_preserve(hist_ops_norm)
            else:
                ops = unique_preserve(ops_supported)
        else:
            ops = unique_preserve(ops_supported)
    else:
        ops = unique_preserve(ops_supported)

    vec_cfg: dict[str, Any] = {
        "lanes": vec_lanes,
        "ops": ops,
        "activation_source": activation_source,
        "fp16_arith_source": fp16_arith_source,
    }

    if activation_source == "rtlgen_cpp" or fp16_arith_source == "rtlgen_cpp":
        vec_cpp_cfg = {
            "binary_path": rtlgen_binary_path,
            "module_prefix": "vec_act",
        }
        if fp16_arith_source == "rtlgen_cpp":
            vec_cpp_cfg["fp16_total_width"] = 16
            vec_cpp_cfg["fp16_mantissa_width"] = 10
        vec_cfg["rtlgen_cpp"] = vec_cpp_cfg

    return vec_cfg


def normalize_sram_instances_v02(memory: dict, platform: dict) -> list[dict]:
    instances = as_list(memory.get("instances", []))
    pdk = platform.get("target_pdk")
    tech_node_nm = platform.get("tech_node_nm")
    out = []
    for inst in instances:
        if not isinstance(inst, dict):
            die("memory.instances must contain objects")
        name = inst.get("name")
        if name is None:
            die("memory.instances[].name is required")
        out.append(
            {
                "name": str(name),
                "depth": int(inst["depth"]),
                "width": int(inst["width"]),
                "banks": int(inst.get("banks", 1)),
                "read_latency": int(inst.get("read_latency", 1)),
                "byte_en": bool(inst.get("byte_en", True)),
                "port": str(inst.get("port", "1r1w")),
                "pdk": pdk,
                "tech_node_nm": int(tech_node_nm) if tech_node_nm is not None else None,
                "base_addr": inst.get("base_addr"),
                "alignment_bytes": int(inst.get("alignment_bytes", 64)),
            }
        )
    return out


def build_rtlgen_config_v02(
    arch: dict,
    args: argparse.Namespace,
    arch_dir: Path,
) -> dict:
    platform = arch["platform"]
    shell = arch["shell"]
    io = arch["io"]
    memory = arch["memory"]

    dma = io.get("dma", {})
    axi = io.get("axi", {})

    search = arch.get("search", {})
    derive = search.get("derive_to_rtlgen", {}) if isinstance(search, dict) else {}
    use_history = bool(derive.get("use_history", False)) if isinstance(derive, dict) else False
    history_db = str(derive.get("history_db", "")).strip() if isinstance(derive, dict) else ""
    history_path = resolve_history_path(history_db, arch_dir) if use_history else None
    history_cfgs = load_history_rtlgen_cfgs(history_path)

    tile = select_compute_tile(arch, args.tile_name)
    tile_count = int(tile.get("count", 1))
    compute_enabled = tile_count > 0

    gemm_cfg = derive_gemm_cfg(
        tile.get("gemm", {}) if isinstance(tile, dict) else {},
        history_cfgs,
        args.rtlgen_binary_path,
    )
    vec_cfg = derive_vec_cfg(
        tile.get("vec", {}) if isinstance(tile, dict) else {},
        history_cfgs,
        args.rtlgen_binary_path,
    )

    sram_instances = normalize_sram_instances_v02(memory, platform)

    if not isinstance(dma, dict) or not isinstance(axi, dict):
        die("io.dma and io.axi must be objects in v0.2-draft")

    rtl_cfg = {
        "version": "0.1",
        "top_name": args.top_name,
        "mmio_addr_width": int(shell.get("mmio_addr_width", args.mmio_addr_width)),
        "data_width": int(shell.get("control_data_width", args.data_width)),
        "queue_depth": int(shell["command_queue_depth"]),
        "enable_irq": bool(shell["supports_interrupts"]),
        "enable_dma_ports": args.enable_dma_ports and int(dma.get("engines", 1)) > 0,
        "enable_cq_mem_ports": args.enable_cq_mem_ports,
        "enable_axi_ports": args.enable_axi_ports,
        "enable_axi_lite_wrapper": args.enable_axi_lite_wrapper,
        "dma_addr_width": int(dma["addr_width"]),
        "dma_data_width": int(dma["data_width"]),
        "axi_addr_width": int(axi["addr_width"]),
        "axi_data_width": int(axi["data_width"]),
        "axi_id_width": int(axi["id_width"]),
        "sram_instances": sram_instances,
        "compute": {
            "enabled": compute_enabled,
            "gemm": gemm_cfg,
            "vec": vec_cfg,
        },
        "derive_meta": {
            "arch_schema_version": "0.2-draft",
            "selected_compute_tile": str(tile.get("name", "unknown")),
            "history_enabled": use_history,
            "history_db": str(history_path) if history_path is not None else "",
            "history_records_seen": len(history_cfgs),
            "derive_strategy": str(derive.get("strategy", "")) if isinstance(derive, dict) else "",
        },
    }
    return rtl_cfg


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate an RTLGen NPU config JSON from an arch YAML. "
            "Supports v0.1 and v0.2-draft architecture schemas."
        )
    )
    parser.add_argument("arch", type=Path, help="Architecture YAML file")
    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help=(
            "Architecture schema YAML. "
            "Default auto-selects from arch schema_version "
            "(v0.1 -> npu/arch/schema.yml, v0.2-draft -> npu/arch/schema_v0_2_draft.yml)."
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output JSON path (default: stdout)",
    )
    parser.add_argument("--top-name", default=DEFAULT_TOP_NAME)
    parser.add_argument("--mmio-addr-width", type=int, default=DEFAULT_MMIO_ADDR_WIDTH)
    parser.add_argument("--data-width", type=int, default=DEFAULT_DATA_WIDTH)
    parser.add_argument(
        "--tile-name",
        default=None,
        help="For v0.2-draft, choose a specific macros.compute_tiles[] name.",
    )
    parser.add_argument(
        "--rtlgen-binary-path",
        default="build/rtlgen",
        help="Default binary path used when deriving rtlgen_cpp backends.",
    )
    parser.add_argument(
        "--enable-axi-lite-wrapper",
        dest="enable_axi_lite_wrapper",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--disable-axi-lite-wrapper",
        dest="enable_axi_lite_wrapper",
        action="store_false",
    )
    parser.add_argument(
        "--enable-dma-ports", dest="enable_dma_ports", action="store_true", default=True
    )
    parser.add_argument(
        "--disable-dma-ports", dest="enable_dma_ports", action="store_false"
    )
    parser.add_argument(
        "--enable-cq-mem-ports",
        dest="enable_cq_mem_ports",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--disable-cq-mem-ports",
        dest="enable_cq_mem_ports",
        action="store_false",
    )
    parser.add_argument(
        "--enable-axi-ports", dest="enable_axi_ports", action="store_true", default=True
    )
    parser.add_argument(
        "--disable-axi-ports", dest="enable_axi_ports", action="store_false"
    )

    args = parser.parse_args()

    arch = load_yaml(args.arch)
    if not isinstance(arch, dict):
        print("Invalid arch format.", file=sys.stderr)
        return 2

    schema_path = args.schema if args.schema is not None else auto_schema_path(arch)
    schema = load_yaml(schema_path)

    if not isinstance(schema, dict):
        print("Invalid schema format.", file=sys.stderr)
        return 2

    missing = validate_schema(arch, schema)
    if missing:
        print(
            f"Missing required sections: {', '.join(missing)}",
            file=sys.stderr,
        )
        return 1

    schema_version = schema.get("schema_version")
    arch_version = arch.get("schema_version")
    if schema_version and arch_version and schema_version != arch_version:
        print(
            f"Schema version mismatch: schema={schema_version} arch={arch_version}",
            file=sys.stderr,
        )
        return 1

    if str(arch_version) == "0.2-draft":
        rtlgen_config = build_rtlgen_config_v02(arch, args, args.arch.parent.resolve())
    else:
        rtlgen_config = build_rtlgen_config_v01(arch, args)

    payload = json.dumps(rtlgen_config, indent=2, sort_keys=True)

    if args.out is None:
        print(payload)
    else:
        args.out.write_text(payload + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

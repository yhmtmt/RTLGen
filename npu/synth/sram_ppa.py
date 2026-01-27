#!/usr/bin/env python3
import argparse
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


def load_yaml(path: Path):
    with path.open() as f:
        return yaml.safe_load(f)


def is_power_of_two(value: int) -> bool:
    return value > 0 and (value & (value - 1)) == 0


def parse_cacti_csv(csv_path: Path):
    with csv_path.open(newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if len(rows) < 2:
        return {}
    header = rows[0]
    data = rows[-1]
    row = {key: val for key, val in zip(header, data)}

    def find_key(substr):
        for key in header:
            if substr in key.lower():
                return key
        return None

    metrics = {}
    access_key = find_key("access time")
    area_key = find_key("area")
    read_energy_key = find_key("read energy")
    write_energy_key = find_key("write energy")
    if access_key:
        metrics["access_time_ns"] = float(row[access_key])
    if area_key:
        metrics["area_mm2"] = float(row[area_key])
    if read_energy_key:
        metrics["read_energy_nj"] = float(row[read_energy_key])
    if write_energy_key:
        metrics["write_energy_nj"] = float(row[write_energy_key])
    return metrics


def run_cacti(cacti_bin: Path, template: Path, instance: dict, tech_node_nm: int):
    with template.open() as f:
        cfg = f.read()
    cfg = cfg.replace("@SIZE_BYTES@", str(instance["size_bytes"]))
    cfg = cfg.replace("@WORD_SIZE_BYTES@", str(instance["word_size_bytes"]))
    cfg = cfg.replace("@WORD_SIZE_BITS@", str(instance["word_size_bytes"] * 8))
    cfg = cfg.replace("@READ_PORTS@", str(instance["read_ports"]))
    cfg = cfg.replace("@WRITE_PORTS@", str(instance["write_ports"]))
    cfg = cfg.replace("@RW_PORTS@", str(instance["rw_ports"]))
    cfg = cfg.replace("@TECH_NODE_NM@", str(tech_node_nm))
    cfg = cfg.replace("@TECH_NODE_UM@", f"{tech_node_nm / 1000.0:.3f}")

    with tempfile.TemporaryDirectory() as td:
        tmp_dir = Path(td)
        cfg_path = tmp_dir / "sram.cfg"
        cfg_path.write_text(cfg)
        result = subprocess.run(
            [str(cacti_bin), "-infile", str(cfg_path)],
            cwd=tmp_dir,
            capture_output=True,
            text=True,
        )
        csv_path = tmp_dir / "out.csv"
        metrics = {}
        if csv_path.exists():
            metrics = parse_cacti_csv(csv_path)
            csv_text = csv_path.read_text()
        else:
            csv_text = None
        return result.returncode, result.stdout, result.stderr, csv_text, metrics


def main():
    parser = argparse.ArgumentParser(
        description="Estimate SRAM PPA metrics using CACTI (1R1W)."
    )
    parser.add_argument("arch", type=Path, help="Architecture YAML file")
    parser.add_argument("--id", required=True, help="Design ID for output path")
    parser.add_argument(
        "--out-root",
        type=Path,
        default=Path("runs/designs/sram"),
        help="Root directory for SRAM metrics",
    )
    parser.add_argument(
        "--cacti-dir",
        type=Path,
        default=Path("cacti"),
        help="CACTI submodule directory",
    )
    parser.add_argument(
        "--cacti-bin",
        type=Path,
        default=None,
        help="Path to CACTI binary (defaults to <cacti-dir>/cacti)",
    )
    parser.add_argument(
        "--cacti-template",
        type=Path,
        default=Path("npu/synth/cacti_sram.cfg.in"),
        help="CACTI template config with placeholders",
    )
    args = parser.parse_args()

    arch = load_yaml(args.arch)
    sram = arch.get("sram", {})
    instances = sram.get("instances", [])
    if not instances:
        print("No SRAM instances found in arch config.", file=sys.stderr)
        return 1

    out_dir = args.out_root / args.id
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = out_dir / "sram_metrics.json"

    cacti_bin = args.cacti_bin or (args.cacti_dir / "cacti")
    cacti_available = cacti_bin.exists() and cacti_bin.is_file()
    template_available = args.cacti_template is not None and args.cacti_template.exists()

    results = []
    for inst in instances:
        if inst.get("port", "1r1w") != "1r1w":
            print(f"Unsupported port type: {inst.get('port')}", file=sys.stderr)
            return 1
        depth = int(inst["depth"])
        width = int(inst["width"])
        banks = int(inst.get("banks", 1))
        if width % 8 != 0:
            print(f"Invalid width (must be multiple of 8): {width}", file=sys.stderr)
            return 1
        if not is_power_of_two(depth):
            print(f"Invalid depth (must be power of two): {depth}", file=sys.stderr)
            return 1

        pdk = inst.get("pdk")
        tech_node_nm = inst.get("tech_node_nm")
        if pdk is None and tech_node_nm is None:
            print(
                f"Missing pdk/tech_node_nm for SRAM instance {inst['name']}",
                file=sys.stderr,
            )
            return 1
        if tech_node_nm is None and pdk is not None:
            pdk_map = {
                "sky130": 130,
                "nangate45": 45,
                "asap7": 7,
            }
            tech_node_nm = pdk_map.get(str(pdk))
        tech_node_nm = int(tech_node_nm) if tech_node_nm is not None else None

        size_bytes = depth * (width // 8) * banks
        instance_meta = {
            "name": inst["name"],
            "pdk": pdk,
            "tech_node_nm": tech_node_nm,
            "port": "1r1w",
            "depth": depth,
            "width": width,
            "banks": banks,
            "read_latency": int(inst.get("read_latency", 1)),
            "byte_en": bool(inst.get("byte_en", True)),
            "size_bytes": size_bytes,
            "word_size_bytes": width // 8,
            "read_ports": 1,
            "write_ports": 1,
            "rw_ports": 0,
        }

        record = {
            "instance": instance_meta,
            "estimated": False,
            "metrics": {},
            "artifacts": {},
        }

        if cacti_available and template_available and tech_node_nm is not None:
            rc, stdout_text, stderr_text, csv_text, metrics = run_cacti(
                cacti_bin, args.cacti_template, instance_meta, tech_node_nm
            )
            record["artifacts"]["cacti_stdout"] = stdout_text
            record["artifacts"]["cacti_stderr"] = stderr_text
            if csv_text is not None:
                record["artifacts"]["cacti_csv"] = csv_text
            record["metrics"]["raw"] = metrics
            if metrics.get("area_mm2") is not None:
                record["metrics"]["area_um2"] = metrics["area_mm2"] * 1e6
            if metrics.get("access_time_ns") is not None:
                record["metrics"]["access_time_ns"] = metrics["access_time_ns"]
            if metrics.get("read_energy_nj") is not None:
                record["metrics"]["read_energy_pj"] = metrics["read_energy_nj"] * 1e3
            if metrics.get("write_energy_nj") is not None:
                record["metrics"]["write_energy_pj"] = metrics["write_energy_nj"] * 1e3
            record["estimated"] = rc == 0 and bool(metrics)
        else:
            reason = []
            if not cacti_available:
                reason.append("cacti binary not found")
            if not template_available:
                reason.append("cacti template not provided")
            if tech_node_nm is None:
                reason.append("tech_node_nm missing (pdk provided)")
            record["note"] = ", ".join(reason)

        results.append(record)

    for record in results:
        for key, suffix in (
            ("cacti_stdout", "cacti.stdout"),
            ("cacti_stderr", "cacti.stderr"),
            ("cacti_csv", "cacti.out.csv"),
        ):
            if key in record["artifacts"]:
                dst = out_dir / f"{record['instance']['name']}.{suffix}"
                dst.write_text(record["artifacts"][key])
                record["artifacts"][key] = str(dst)

    payload = {
        "arch": str(args.arch),
        "id": args.id,
        "instances": results,
    }
    metrics_path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Wrote SRAM metrics: {metrics_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

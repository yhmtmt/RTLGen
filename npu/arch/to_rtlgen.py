#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

import yaml


DEFAULT_TOP_NAME = "npu_top"
DEFAULT_MMIO_ADDR_WIDTH = 12
DEFAULT_DATA_WIDTH = 32


def load_yaml(path: Path):
    with path.open() as f:
        return yaml.safe_load(f)


def validate_schema(config: dict, schema: dict):
    missing = []
    for key in schema.get("required", []):
        if key not in config:
            missing.append(key)
    return missing


def build_rtlgen_config(arch: dict, args: argparse.Namespace):
    shell = arch["shell"]
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
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate an RTLGen NPU config JSON from an arch YAML."
    )
    parser.add_argument("arch", type=Path, help="Architecture YAML file")
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("npu/arch/schema.yml"),
        help="Architecture schema YAML",
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

    schema = load_yaml(args.schema)
    arch = load_yaml(args.arch)

    if not isinstance(schema, dict) or not isinstance(arch, dict):
        print("Invalid schema or arch format.", file=sys.stderr)
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

    rtlgen_config = build_rtlgen_config(arch, args)
    payload = json.dumps(rtlgen_config, indent=2, sort_keys=True)

    if args.out is None:
        print(payload)
    else:
        args.out.write_text(payload + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

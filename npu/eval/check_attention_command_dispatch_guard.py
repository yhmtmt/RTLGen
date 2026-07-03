#!/usr/bin/env python3
"""Lightweight generated RTL guard for attention command dispatch blocks."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--design-dir", required=True)
    args = ap.parse_args(argv)

    design_dir = Path(args.design_dir)
    config_path = design_dir / "config.json"
    generated_config_path = design_dir / "verilog" / "config.json"
    if not config_path.exists():
        raise SystemExit(f"missing config: {config_path}")
    if not generated_config_path.exists():
        raise SystemExit(f"missing generated config: {generated_config_path}")

    cfg = _load_json(config_path)
    gen_cfg = _load_json(generated_config_path)
    if cfg != gen_cfg:
        raise SystemExit("generated config does not match source config")
    top_name = str(cfg.get("top_name", "")).strip()
    if not top_name:
        raise SystemExit("top_name must not be empty")
    ctrl = cfg.get("attention_command_dispatch")
    if not isinstance(ctrl, dict):
        raise SystemExit("config must contain attention_command_dispatch object")

    verilog_path = design_dir / "verilog" / f"{top_name}.v"
    if not verilog_path.exists():
        raise SystemExit(f"missing generated verilog: {verilog_path}")
    text = verilog_path.read_text(encoding="utf-8", errors="replace")
    if not re.search(rf"^\s*module\s+{re.escape(top_name)}\b", text, re.MULTILINE):
        raise SystemExit(f"generated verilog does not define top module {top_name}")
    for required in [
        "command_valid",
        "command_ready",
        "cluster_ready",
        "dispatch_valid",
        "dispatch_cluster_id",
        "queued_count",
    ]:
        if required not in text:
            raise SystemExit(f"generated verilog missing expected signal: {required}")
    print(f"OK: attention command dispatch guard passed for {design_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

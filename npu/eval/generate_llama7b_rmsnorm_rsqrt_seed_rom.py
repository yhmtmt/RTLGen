#!/usr/bin/env python3
"""Generate or check the Phase-2 Llama-7B RMSNorm rsqrt seed ROM."""

from __future__ import annotations

import argparse
from pathlib import Path

from npu.eval.llama7b_rmsnorm_phase2 import SEED_ROM_PATH, check_seed_rom, seed_rom_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=SEED_ROM_PATH)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        check_seed_rom(args.output)
        print(f"OK: RMSNorm rsqrt seed ROM matches generator: {args.output}")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(seed_rom_text(), encoding="ascii")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

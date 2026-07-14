#!/usr/bin/env python3
"""Run a focused RTL/reference test and emit portable equivalence evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


def _test_count(output: str) -> int:
    matches = re.findall(r"(\d+) passed", output)
    return int(matches[-1]) if matches else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--component", required=True)
    parser.add_argument("--semantic-profile", required=True)
    parser.add_argument("--test-target", required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    command = [sys.executable, "-m", "pytest", "-q", args.test_target]
    run = subprocess.run(command, cwd=repo_root, capture_output=True, text=True)
    combined = (run.stdout + "\n" + run.stderr).strip()
    passed = run.returncode == 0
    payload = {
        "version": 1,
        "model": "rtl_component_reference_equivalence_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "decision": f"{args.component}_equivalence_{'pass' if passed else 'fail'}",
        "component": args.component,
        "semantic_profile": args.semantic_profile,
        "reference": args.reference,
        "test_target": args.test_target,
        "command": command,
        "returncode": run.returncode,
        "equivalence_pass": passed,
        "passed_test_count": _test_count(combined),
        "test_output_sha256": hashlib.sha256(combined.encode("utf-8")).hexdigest(),
        "test_output_tail": combined[-4000:],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(
        "\n".join(
            [
                f"# {args.component} Equivalence",
                "",
                f"- decision: `{payload['decision']}`",
                f"- equivalence pass: `{passed}`",
                f"- semantic profile: `{args.semantic_profile}`",
                f"- reference: `{args.reference}`",
                f"- focused tests passed: `{payload['passed_test_count']}`",
                f"- test target: `{args.test_target}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": passed, "decision": payload["decision"], "out": str(args.out)}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

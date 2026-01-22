#!/usr/bin/env python3
import datetime as dt
import subprocess
import sys
from pathlib import Path


STATUS_PATH = Path("npu/docs/status.md")
START = "<!-- STATUS_META_START -->"
END = "<!-- STATUS_META_END -->"


def git_head() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True)
            .strip()
        )
    except Exception:
        return "unknown"


def main() -> int:
    if not STATUS_PATH.exists():
        print(f"missing: {STATUS_PATH}", file=sys.stderr)
        return 1

    text = STATUS_PATH.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print("status markers not found", file=sys.stderr)
        return 1

    now = dt.date.today().isoformat()
    meta = f"{START}\nLast updated: {now}\nGit: {git_head()}\n{END}"

    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    STATUS_PATH.write_text(before + meta + after, encoding="utf-8")
    print(f"updated {STATUS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

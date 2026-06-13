#!/usr/bin/env python3
"""Summarize OpenROAD timing path reports referenced by block sweep metrics."""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SUMMARY_TOKENS = (
    "critical path",
    "wns",
    "tns",
    "slack",
    "finish critical path delay",
)


@dataclass(frozen=True)
class TimingPath:
    source: Path
    stage: str
    stage_rank: int
    startpoint: str
    endpoint: str
    path_group: str
    path_type: str
    slack: float | None
    arrival: float | None
    required: float | None
    excerpt: list[str]


STAGE_PATTERNS: tuple[tuple[str, str, int], ...] = (
    ("6_finish", "finish", 0),
    ("5_route", "route", 1),
    ("route", "route", 1),
    ("4_cts", "cts", 2),
    ("cts", "cts", 2),
    ("3_resizer", "resizer", 3),
    ("3_detailed_place", "detailed_place", 4),
    ("3_global_place", "global_place", 5),
    ("2_floorplan", "floorplan", 6),
)


def _float_or_none(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _last_number(line: str) -> float | None:
    matches = re.findall(r"[-+]?(?:\d+\.\d+|\d+)", line)
    if not matches:
        return None
    return _float_or_none(matches[-1])


def _field(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    if match is None:
        return ""
    return match.group(1).strip()


def _read_limited(path: Path, *, max_bytes: int) -> str | None:
    try:
        if path.stat().st_size > max_bytes:
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def report_stage(path: Path) -> tuple[str, int]:
    name = path.name.lower()
    for pattern, stage, rank in STAGE_PATTERNS:
        if pattern in name:
            return stage, rank
    return "other", 99


def _trim_timing_block(lines: list[str]) -> list[str]:
    slack_index = None
    for index, line in enumerate(lines):
        if "slack" in line.lower():
            slack_index = index
            break
    if slack_index is None:
        return lines
    for index in range(slack_index + 1, len(lines)):
        if lines[index].startswith("==="):
            return lines[:index]
    return lines


def extract_timing_paths(path: Path, *, max_bytes: int) -> list[TimingPath]:
    text = _read_limited(path, max_bytes=max_bytes)
    if text is None or "Startpoint:" not in text:
        return []

    paths: list[TimingPath] = []
    for raw_block in re.split(r"(?=^Startpoint:)", text, flags=re.MULTILINE):
        if not raw_block.startswith("Startpoint:"):
            continue
        lines = _trim_timing_block(raw_block.strip().splitlines())
        block = "\n".join(lines)
        slack = None
        arrival = None
        required = None
        for line in lines:
            lower = line.lower()
            if slack is None and "slack" in lower:
                slack = _last_number(line)
            elif arrival is None and "data arrival time" in lower:
                arrival = _last_number(line)
            elif required is None and "data required time" in lower:
                required = _last_number(line)
        stage, stage_rank = report_stage(path)
        paths.append(
            TimingPath(
                source=path,
                stage=stage,
                stage_rank=stage_rank,
                startpoint=_field(r"^Startpoint:\s*(.+)$", block),
                endpoint=_field(r"^Endpoint:\s*(.+)$", block),
                path_group=_field(r"^Path Group:\s*(.+)$", block),
                path_type=_field(r"^Path Type:\s*(.+)$", block),
                slack=slack,
                arrival=arrival,
                required=required,
                excerpt=_condense_excerpt(lines),
            )
        )
    return paths


def _dedupe_timing_paths(paths: Iterable[TimingPath]) -> list[TimingPath]:
    seen: set[tuple[Path, str, str, str, float | None, float | None, float | None]] = set()
    result: list[TimingPath] = []
    for path in paths:
        key = (
            path.source,
            path.startpoint,
            path.endpoint,
            path.path_group,
            path.slack,
            path.arrival,
            path.required,
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def _condense_excerpt(lines: list[str]) -> list[str]:
    if len(lines) <= 42:
        return lines
    head = lines[:24]
    tail = lines[-16:]
    return head + ["..."] + tail


def _metric_float(row: dict[str, str], key: str) -> float | None:
    value = str(row.get(key, "")).strip()
    if not value:
        return None
    return _float_or_none(value)


def _load_metrics(design_dir: Path) -> list[dict[str, str]]:
    metrics_path = design_dir / "metrics.csv"
    with metrics_path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _path_from_text(value: str) -> Path | None:
    text = str(value or "").strip()
    if not text:
        return None
    return Path(text)


def _result_paths_from_work_json(row: dict[str, str]) -> list[Path]:
    result_json = _path_from_text(row.get("work_result_json", ""))
    if result_json is None or not result_json.exists():
        return []
    try:
        payload = json.loads(result_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    paths: list[Path] = []
    for key in ("result_path", "report_path"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            paths.append(Path(value))
    reports = payload.get("reports")
    if isinstance(reports, dict):
        for value in reports.values():
            if isinstance(value, str) and value.strip():
                paths.append(Path(value))
    return paths


def _dedupe(paths: Iterable[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def candidate_report_paths(row: dict[str, str]) -> list[Path]:
    anchors: list[Path] = []
    result_path = _path_from_text(row.get("result_path", ""))
    if result_path is not None:
        anchors.append(result_path)
    anchors.extend(_result_paths_from_work_json(row))

    candidates: list[Path] = []
    for anchor in anchors:
        if anchor.exists() and anchor.is_file():
            candidates.append(anchor)
        report_dir = anchor.parent if anchor.suffix else anchor
        if not report_dir.exists() or not report_dir.is_dir():
            continue
        priority_patterns = (
            "*checks*",
            "*timing*",
            "*setup*",
            "*wns*",
            "*.rpt",
            "*.log",
        )
        for pattern in priority_patterns:
            candidates.extend(path for path in report_dir.glob(pattern) if path.is_file())
        candidates.extend(path for path in report_dir.glob("**/*.rpt") if path.is_file())
    return _dedupe(candidates)


def _report_path_sort_key(path: Path) -> tuple[int, str]:
    _, rank = report_stage(path)
    return rank, str(path)


def _summary_lines(path: Path, *, max_bytes: int) -> list[str]:
    text = _read_limited(path, max_bytes=max_bytes)
    if text is None:
        return []
    lines: list[str] = []
    for line in text.splitlines():
        lower = line.lower()
        if any(token in lower for token in SUMMARY_TOKENS):
            stripped = line.strip()
            if stripped:
                lines.append(stripped)
        if len(lines) >= 20:
            break
    return lines


def _format_number(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.4f}"


def _sorted_metric_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    ok_rows = [row for row in rows if str(row.get("status", "")).strip().lower() in {"ok", "pass", ""}]
    return sorted(
        ok_rows,
        key=lambda row: (
            _metric_float(row, "critical_path_ns") is None,
            _metric_float(row, "critical_path_ns") or 0.0,
            str(row.get("param_hash", "")),
        ),
    )


def _timing_path_sort_key(path: TimingPath) -> tuple[bool, float, str, str]:
    return path.slack is None, path.slack or 0.0, str(path.source), path.endpoint


def _preferred_stage_paths(paths: list[TimingPath]) -> tuple[str | None, list[TimingPath]]:
    if not paths:
        return None, []
    best_rank = min(path.stage_rank for path in paths)
    selected = [path for path in paths if path.stage_rank == best_rank]
    stage = selected[0].stage if selected else None
    return stage, sorted(selected, key=_timing_path_sort_key)


def _append_timing_path_section(lines: list[str], paths: list[TimingPath], *, max_paths: int) -> None:
    for index, path in enumerate(paths[:max_paths], start=1):
        lines.extend(
            [
                f"### Path {index}",
                "",
                f"- source: `{path.source}`",
                f"- stage: `{path.stage}`",
                f"- startpoint: `{path.startpoint}`",
                f"- endpoint: `{path.endpoint}`",
                f"- path_group: `{path.path_group}`",
                f"- path_type: `{path.path_type}`",
                f"- slack: `{_format_number(path.slack)}`",
                f"- data_arrival_time: `{_format_number(path.arrival)}`",
                f"- data_required_time: `{_format_number(path.required)}`",
                "",
                "```text",
                *path.excerpt,
                "```",
                "",
            ]
        )


def build_report(
    *,
    design_dir: Path,
    max_rows: int,
    max_paths: int,
    max_bytes: int,
) -> str:
    rows = _sorted_metric_rows(_load_metrics(design_dir))[:max_rows]
    lines: list[str] = [
        "# OpenROAD Timing Debug Summary",
        "",
        f"- design_dir: `{design_dir}`",
        f"- metrics_path: `{design_dir / 'metrics.csv'}`",
        f"- rows_considered: {len(rows)}",
        "",
        "## Metrics Rows",
        "",
        "| param_hash | tag | status | critical_path_ns | density | result_path |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    all_paths: list[TimingPath] = []
    inspected: list[Path] = []
    summary_by_file: dict[str, list[str]] = {}
    for row in rows:
        density = ""
        params_text = str(row.get("params_json", "")).strip()
        if params_text:
            try:
                params = json.loads(params_text)
                density = str(params.get("place_density", params.get("PLACE_DENSITY", "")))
            except json.JSONDecodeError:
                density = ""
        result_path = str(row.get("result_path", "")).strip()
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("param_hash", "")),
                    str(row.get("tag", "")),
                    str(row.get("status", "")),
                    _format_number(_metric_float(row, "critical_path_ns")),
                    density,
                    f"`{result_path}`" if result_path else "",
                ]
            )
            + " |"
        )
        candidates = candidate_report_paths(row)
        inspected.extend(candidates)
        for candidate in sorted(candidates, key=_report_path_sort_key):
            paths = extract_timing_paths(candidate, max_bytes=max_bytes)
            all_paths.extend(paths)
            if not paths:
                summary = _summary_lines(candidate, max_bytes=max_bytes)
                if summary:
                    summary_by_file[str(candidate)] = summary

    unique_paths = _dedupe_timing_paths(all_paths)
    preferred_stage, preferred_paths = _preferred_stage_paths(unique_paths)
    all_stage_paths = sorted(unique_paths, key=_timing_path_sort_key)
    lines.extend(
        [
            "",
            "## Inspected Report Files",
            "",
        ]
    )
    if inspected:
        for path in sorted(_dedupe(inspected), key=_report_path_sort_key):
            lines.append(f"- `{path}`")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Preferred Final-Stage Timing Paths",
            "",
            f"- raw_path_block_count: {len(all_paths)}",
            f"- unique_path_block_count: {len(unique_paths)}",
            f"- preferred_stage: `{preferred_stage or ''}`",
            "",
        ]
    )
    if preferred_paths:
        _append_timing_path_section(lines, preferred_paths, max_paths=max_paths)
    else:
        lines.append("No report_checks-style Startpoint/Endpoint path blocks were found.")
        if summary_by_file:
            lines.extend(["", "## Available Timing Summary Lines", ""])
            for source, summary in sorted(summary_by_file.items()):
                lines.append(f"### `{source}`")
                lines.append("")
                lines.extend(f"- {line}" for line in summary)
                lines.append("")
    if all_stage_paths and all_stage_paths != preferred_paths:
        lines.extend(
            [
                "",
                "## Worst Timing Paths Across All Stages",
                "",
            ]
        )
        _append_timing_path_section(lines, all_stage_paths, max_paths=max_paths)

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--max-rows", type=int, default=4)
    parser.add_argument("--max-paths", type=int, default=8)
    parser.add_argument("--max-bytes", type=int, default=10 * 1024 * 1024)
    args = parser.parse_args()

    report = build_report(
        design_dir=args.design_dir,
        max_rows=args.max_rows,
        max_paths=args.max_paths,
        max_bytes=args.max_bytes,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

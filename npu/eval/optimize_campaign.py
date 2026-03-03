#!/usr/bin/env python3
"""
Run multi-objective profile sweeps on campaign reporting outputs.

For each objective profile:
  - run `report_campaign.py` with profile weights
  - collect `best_point.json`

Then emit:
  - objective_sweep.csv
  - objective_sweep.md
"""

import argparse
import csv
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from validate import load_json, validate_campaign


REPO_ROOT = Path(__file__).resolve().parents[2]


DEFAULT_PROFILES: List[Dict[str, Any]] = [
    {"name": "balanced", "w_latency": 1.0, "w_energy": 1.0, "w_area": 0.0, "w_power": 0.0, "w_runtime": 0.0},
    {"name": "latency", "w_latency": 1.0, "w_energy": 0.0, "w_area": 0.0, "w_power": 0.0, "w_runtime": 0.0},
    {"name": "energy", "w_latency": 0.0, "w_energy": 1.0, "w_area": 0.0, "w_power": 0.0, "w_runtime": 0.0},
    {"name": "runtime_bal", "w_latency": 0.5, "w_energy": 0.5, "w_area": 0.0, "w_power": 0.0, "w_runtime": 1.0},
    {"name": "ppa", "w_latency": 1.0, "w_energy": 1.0, "w_area": 0.25, "w_power": 0.25, "w_runtime": 0.0},
]


def log(msg: str) -> None:
    print(f"[optimize_campaign] {msg}")


def abs_path(path_text: str) -> Path:
    p = Path(path_text)
    if p.is_absolute():
        return p
    return (REPO_ROOT / p).resolve()


def rel_to_repo(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except Exception:
        return str(path.resolve())


def safe_slug(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(text))
    s = s.strip("_")
    return s or "profile"


def validate_profile(profile: Dict[str, Any], idx: int) -> Dict[str, Any]:
    name = str(profile.get("name", "")).strip()
    if not name:
        raise SystemExit(f"optimize_campaign: profile[{idx}] missing non-empty name")
    out = {"name": name}
    for key in ("w_latency", "w_energy", "w_area", "w_power", "w_runtime"):
        try:
            out[key] = float(profile.get(key, 0.0))
        except Exception as exc:
            raise SystemExit(f"optimize_campaign: profile[{idx}].{key} invalid: {exc}") from exc
    if all(abs(float(out[k])) < 1e-12 for k in ("w_latency", "w_energy", "w_area", "w_power", "w_runtime")):
        raise SystemExit(f"optimize_campaign: profile[{idx}] all weights are zero")
    return out


def load_profiles(path: Optional[str]) -> List[Dict[str, Any]]:
    if not path:
        return [dict(p) for p in DEFAULT_PROFILES]
    doc = load_json(abs_path(path))
    raw = doc.get("profiles")
    if not isinstance(raw, list) or not raw:
        raise SystemExit("optimize_campaign: profiles_json must contain non-empty profiles[]")
    out: List[Dict[str, Any]] = []
    seen = set()
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise SystemExit(f"optimize_campaign: profiles[{i}] must be object")
        p = validate_profile(item, i)
        if p["name"] in seen:
            raise SystemExit(f"optimize_campaign: duplicate profile name: {p['name']}")
        seen.add(p["name"])
        out.append(p)
    return out


def run_cmd(cmd: List[str], dry_run: bool) -> None:
    log("$ " + " ".join(cmd))
    if dry_run:
        return
    subprocess.run(cmd, cwd=str(REPO_ROOT), check=True)


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    header: List[str] = []
    for row in rows:
        for k in row.keys():
            if k not in header:
                header.append(k)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in header})


def fmt(x: Any, digits: int = 6) -> str:
    if x is None or x == "":
        return ""
    try:
        return f"{float(x):.{digits}f}"
    except Exception:
        return str(x)


def main() -> int:
    ap = argparse.ArgumentParser(description="Run objective-profile sweep for a campaign")
    ap.add_argument("--campaign", required=True, help="Campaign manifest JSON")
    ap.add_argument("--profiles_json", help="Optional JSON with profiles[]")
    ap.add_argument("--out_csv", help="Optional objective sweep CSV output path")
    ap.add_argument("--out_md", help="Optional objective sweep markdown output path")
    ap.add_argument("--out_dir", help="Optional profile-artifacts root directory")
    ap.add_argument("--dry_run", action="store_true", help="Print commands only")
    args = ap.parse_args()

    os.chdir(REPO_ROOT)
    campaign_path = abs_path(args.campaign)
    campaign = load_json(campaign_path)
    validate_campaign(campaign, check_paths=True)

    campaign_dir = abs_path(str(campaign["outputs"]["campaign_dir"]))
    out_csv = abs_path(args.out_csv) if args.out_csv else (campaign_dir / "objective_sweep.csv")
    out_md = abs_path(args.out_md) if args.out_md else (campaign_dir / "objective_sweep.md")
    out_dir = abs_path(args.out_dir) if args.out_dir else (campaign_dir / "objective_profiles")

    profiles = load_profiles(args.profiles_json)
    rows: List[Dict[str, Any]] = []

    for profile in profiles:
        name = str(profile["name"])
        slug = safe_slug(name)
        profile_dir = out_dir / slug
        report_md = profile_dir / "report.md"
        summary_csv = profile_dir / "summary.csv"
        pareto_csv = profile_dir / "pareto.csv"
        best_json = profile_dir / "best_point.json"

        cmd = [
            "python3",
            "npu/eval/report_campaign.py",
            "--campaign",
            rel_to_repo(campaign_path),
            "--out_md",
            rel_to_repo(report_md),
            "--out_csv",
            rel_to_repo(summary_csv),
            "--pareto_csv",
            rel_to_repo(pareto_csv),
            "--best_json",
            rel_to_repo(best_json),
            "--w_latency",
            str(profile["w_latency"]),
            "--w_energy",
            str(profile["w_energy"]),
            "--w_area",
            str(profile["w_area"]),
            "--w_power",
            str(profile["w_power"]),
            "--w_runtime",
            str(profile["w_runtime"]),
        ]
        run_cmd(cmd, dry_run=args.dry_run)

        if args.dry_run:
            rows.append(
                {
                    "profile": name,
                    "w_latency": profile["w_latency"],
                    "w_energy": profile["w_energy"],
                    "w_area": profile["w_area"],
                    "w_power": profile["w_power"],
                    "w_runtime": profile["w_runtime"],
                    "best_arch_id": "",
                    "best_macro_mode": "",
                    "objective_score": "",
                    "latency_ms_mean": "",
                    "energy_mj_mean": "",
                    "flow_elapsed_s_mean": "",
                    "best_json": rel_to_repo(best_json),
                    "report_md": rel_to_repo(report_md),
                    "pareto_csv": rel_to_repo(pareto_csv),
                }
            )
            continue

        best_doc = load_json(best_json)
        best = dict(best_doc.get("best", {}) or {})
        rows.append(
            {
                "profile": name,
                "w_latency": profile["w_latency"],
                "w_energy": profile["w_energy"],
                "w_area": profile["w_area"],
                "w_power": profile["w_power"],
                "w_runtime": profile["w_runtime"],
                "best_arch_id": best.get("arch_id", ""),
                "best_macro_mode": best.get("macro_mode", ""),
                "objective_score": best.get("objective_score", ""),
                "latency_ms_mean": best.get("latency_ms_mean", ""),
                "energy_mj_mean": best.get("energy_mj_mean", ""),
                "flow_elapsed_s_mean": best.get("flow_elapsed_s_mean", ""),
                "best_json": rel_to_repo(best_json),
                "report_md": rel_to_repo(report_md),
                "pareto_csv": rel_to_repo(pareto_csv),
            }
        )

    write_csv(out_csv, rows)

    lines: List[str] = []
    lines.append(f"# Objective Sweep: {campaign['campaign_id']}")
    lines.append("")
    lines.append(f"- generated_utc: `{datetime.now(timezone.utc).isoformat(timespec='seconds')}`")
    lines.append(f"- source_campaign: `{rel_to_repo(campaign_path)}`")
    lines.append(f"- output_csv: `{rel_to_repo(out_csv)}`")
    lines.append(f"- profile_artifacts_dir: `{rel_to_repo(out_dir)}`")
    lines.append("")
    lines.append(
        "| profile | w_latency | w_energy | w_area | w_power | w_runtime | best_arch_id | best_macro_mode | objective_score | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean | report_md |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---|")
    for row in rows:
        lines.append(
            "| {profile} | {wlat} | {weng} | {warea} | {wpwr} | {wrun} | {arch} | {mode} | {score} | {lat} | {eng} | {flow} | `{report}` |".format(
                profile=row.get("profile", ""),
                wlat=fmt(row.get("w_latency"), 3),
                weng=fmt(row.get("w_energy"), 3),
                warea=fmt(row.get("w_area"), 3),
                wpwr=fmt(row.get("w_power"), 3),
                wrun=fmt(row.get("w_runtime"), 3),
                arch=row.get("best_arch_id", ""),
                mode=row.get("best_macro_mode", ""),
                score=fmt(row.get("objective_score"), 6),
                lat=fmt(row.get("latency_ms_mean"), 6),
                eng=fmt(row.get("energy_mj_mean"), 9),
                flow=fmt(row.get("flow_elapsed_s_mean"), 4),
                report=row.get("report_md", ""),
            )
        )
    lines.append("")

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
    log(f"wrote objective sweep csv: {rel_to_repo(out_csv)}")
    log(f"wrote objective sweep md: {rel_to_repo(out_md)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


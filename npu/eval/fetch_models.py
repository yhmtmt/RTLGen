#!/usr/bin/env python3
"""
Materialize externally hosted ONNX model files declared in a model manifest.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List

from validate import load_json, sha256_file, validate_model_manifest


REPO_ROOT = Path(__file__).resolve().parents[2]


def die(msg: str) -> None:
    print(f"fetch_models: {msg}", file=sys.stderr)
    sys.exit(1)


def log(msg: str) -> None:
    print(f"[fetch_models] {msg}")


def abs_path(path_text: str) -> Path:
    p = Path(path_text)
    if p.is_absolute():
        return p
    return (REPO_ROOT / p).resolve()


def candidate_urls(fetch_meta: Dict[str, Any]) -> List[str]:
    urls = [str(fetch_meta.get("url", "")).strip()]
    mirrors = fetch_meta.get("mirrors", [])
    if isinstance(mirrors, list):
        urls.extend(str(v).strip() for v in mirrors if str(v).strip())
    return [u for u in urls if u]


def download_to_tmp(url: str, tmp_path: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "RTLGen-fetch-models/0.1"})
    with urllib.request.urlopen(req) as resp, tmp_path.open("wb") as out_f:
        shutil.copyfileobj(resp, out_f, length=1024 * 1024)


def fetch_one(
    *,
    model_id: str,
    onnx_path_txt: str,
    onnx_sha256: str,
    fetch_meta: Dict[str, Any],
    force: bool,
    dry_run: bool,
) -> str:
    dst = abs_path(onnx_path_txt)
    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.exists():
        actual_sha = sha256_file(dst)
        if actual_sha == onnx_sha256:
            return "cached"
        if not force:
            die(
                f"model {model_id}: existing file {onnx_path_txt} has sha256={actual_sha}, "
                "expected manifest hash; rerun with --force to replace it"
            )

    urls = candidate_urls(fetch_meta)
    if not urls:
        die(f"model {model_id}: missing fetch url")

    if dry_run:
        log(f"would fetch model_id={model_id} into {onnx_path_txt} from {urls[0]}")
        return "dry_run"

    errors: List[str] = []
    for url in urls:
        log(f"fetch model_id={model_id} url={url}")
        tmp_fd = None
        tmp_path: Path | None = None
        try:
            tmp_fd, tmp_name = tempfile.mkstemp(
                prefix=f"{model_id}.",
                suffix=".download",
                dir=str(dst.parent),
            )
            os.close(tmp_fd)
            tmp_fd = None
            tmp_path = Path(tmp_name)
            download_to_tmp(url, tmp_path)
            actual_sha = sha256_file(tmp_path)
            if actual_sha != onnx_sha256:
                raise RuntimeError(
                    f"sha256 mismatch for downloaded file: expected {onnx_sha256} got {actual_sha}"
                )
            tmp_path.replace(dst)
            return "downloaded"
        except (OSError, urllib.error.URLError, RuntimeError) as exc:
            errors.append(f"{url}: {exc}")
            if tmp_path is not None and tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
        finally:
            if tmp_fd is not None:
                try:
                    os.close(tmp_fd)
                except OSError:
                    pass

    die(f"model {model_id}: all fetch attempts failed: {'; '.join(errors)}")
    return "unreachable"


def iter_selected_models(models: Iterable[Dict[str, Any]], selected_ids: set[str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for model in models:
        model_id = str(model.get("model_id", "")).strip()
        if not model_id:
            continue
        if selected_ids and model_id not in selected_ids:
            continue
        out.append(model)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch external ONNX model files for evaluation manifests.")
    ap.add_argument("--manifest", required=True, help="Path to runs/models/<set>/manifest.json")
    ap.add_argument(
        "--model_id",
        action="append",
        default=[],
        help="Optional model_id filter; may be repeated",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing local file when its sha256 mismatches the manifest",
    )
    ap.add_argument(
        "--dry_run",
        action="store_true",
        help="Print planned fetch operations without downloading",
    )
    args = ap.parse_args()

    manifest_path = abs_path(args.manifest)
    manifest = load_json(manifest_path)
    model_set_id = str(manifest.get("model_set_id", "")).strip()
    if not model_set_id:
        die(f"{args.manifest}: missing model_set_id")

    by_id = validate_model_manifest(
        manifest_path_txt=str(manifest_path),
        model_set_id=model_set_id,
        check_paths=False,
    )

    selected_ids = {str(v).strip() for v in args.model_id if str(v).strip()}
    raw_models = manifest.get("models", [])
    if not isinstance(raw_models, list):
        die(f"{args.manifest}: models must be an array")
    models = iter_selected_models(raw_models, selected_ids)
    if selected_ids:
        missing = sorted(selected_ids - {str(m.get("model_id", "")).strip() for m in models})
        if missing:
            die(f"unknown --model_id values: {missing}")

    fetched = 0
    cached = 0
    skipped = 0
    for raw in models:
        model_id = str(raw.get("model_id", "")).strip()
        meta = by_id.get(model_id)
        if meta is None:
            die(f"model {model_id}: missing validated manifest metadata")
        fetch_meta = meta.get("fetch")
        if not isinstance(fetch_meta, dict):
            skipped += 1
            log(f"skip model_id={model_id}: no fetch metadata; expecting local file at {meta['onnx_path']}")
            continue
        status = fetch_one(
            model_id=model_id,
            onnx_path_txt=str(meta["onnx_path"]),
            onnx_sha256=str(meta["onnx_sha256"]),
            fetch_meta=fetch_meta,
            force=bool(args.force),
            dry_run=bool(args.dry_run),
        )
        if status == "cached":
            cached += 1
        elif status == "downloaded":
            fetched += 1

    log(
        f"done: model_set_id={model_set_id} fetched={fetched} cached={cached} "
        f"skipped={skipped} selected={len(models)}"
    )


if __name__ == "__main__":
    main()

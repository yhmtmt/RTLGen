#!/usr/bin/env python3
"""Compare candidate tensor outputs against deterministic llm reference fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from llm_reference import compare_reference_docs, load_json_doc


def main() -> int:
    ap = argparse.ArgumentParser(description='Compare candidate outputs against llm reference fixtures.')
    ap.add_argument('--reference-json', required=True, help='Reference fixture json path')
    ap.add_argument('--candidate-json', required=True, help='Candidate output json path')
    ap.add_argument('--out', help='Optional metrics json output path')
    args = ap.parse_args()

    metrics = compare_reference_docs(
        load_json_doc(args.reference_json),
        load_json_doc(args.candidate_json),
    )
    text = json.dumps(metrics, indent=2) + '\n'
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
    else:
        print(text, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

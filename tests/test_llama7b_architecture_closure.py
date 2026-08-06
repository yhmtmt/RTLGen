#!/usr/bin/env python3
"""Focused tests for the persistent Llama7B architecture closure matrix."""

from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "npu/eval/report_llama7b_architecture_closure.py"
JSON_PATH = REPO_ROOT / "npu/docs/llama7b_architecture_closure.json"
MARKDOWN_PATH = REPO_ROOT / "npu/docs/generated/llama7b_architecture_closure.md"


def _load_module():
    spec = importlib.util.spec_from_file_location("llama7b_architecture_closure", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Llama7BArchitectureClosureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()
        cls.matrix = cls.module._load_json(JSON_PATH)

    def test_repo_matrix_is_valid_and_markdown_in_sync(self) -> None:
        errors = self.module.validate_matrix(self.matrix, repo_root=REPO_ROOT)
        self.assertEqual(errors, [])
        rendered = self.module.render_markdown(self.matrix, repo_root=REPO_ROOT)
        self.assertEqual(rendered, MARKDOWN_PATH.read_text(encoding="utf-8"))

    def test_closed_status_rejects_unclosed_dimension(self) -> None:
        matrix = copy.deepcopy(self.matrix)
        matrix["components"][2]["status"] = "closed"
        errors = self.module.validate_matrix(matrix, repo_root=REPO_ROOT)
        joined = "\n".join(errors)
        self.assertIn("unsupported closure", joined)
        self.assertIn("component norm", joined)

    def test_missing_evidence_path_is_rejected(self) -> None:
        matrix = copy.deepcopy(self.matrix)
        matrix["components"][0]["evidence"][0]["path"] = "docs/proposals/does_not_exist.md"
        errors = self.module.validate_matrix(matrix, repo_root=REPO_ROOT)
        joined = "\n".join(errors)
        self.assertIn("evidence path does not exist", joined)
        self.assertIn("does_not_exist.md", joined)


if __name__ == "__main__":
    unittest.main()

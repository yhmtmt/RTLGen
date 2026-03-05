#!/usr/bin/env python3
"""Regression tests for mapper split metadata note extraction."""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml  # type: ignore


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_script_module(name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    sys.path.insert(0, str(module_path.parent))
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class RunCampaignMapperNotesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.run_campaign = load_script_module(
            "run_campaign_for_test", "npu/eval/run_campaign.py"
        )

    def _write_schedule(self, path: Path, doc: dict) -> None:
        path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

    def test_mapper_notes_split_enabled(self):
        with tempfile.TemporaryDirectory() as td:
            sched = Path(td) / "sched.yml"
            self._write_schedule(
                sched,
                {
                    "version": 0.1,
                    "ops": [{"id": "gemm2_c0", "type": "gemm", "n": 2047}],
                    "mapper_notes": {
                        "gemm2_split_enabled": True,
                        "gemm2_out_chunks": [2047, 2047, 2],
                    },
                },
            )
            note = self.run_campaign.mapper_split_note_from_schedule(str(sched))
            self.assertIn("mapper_split_enabled=1", note)
            self.assertIn("mapper_split_chunk_count=3", note)
            self.assertIn("mapper_split_chunks=2047,2047,2", note)

    def test_mapper_notes_fallback_from_ops(self):
        with tempfile.TemporaryDirectory() as td:
            sched = Path(td) / "sched.yml"
            self._write_schedule(
                sched,
                {
                    "version": 0.1,
                    "ops": [
                        {"id": "gemm2_c0", "type": "gemm", "n": 64},
                        {"id": "gemm2_c1", "type": "gemm", "n": 32},
                    ],
                },
            )
            note = self.run_campaign.mapper_split_note_from_schedule(str(sched))
            self.assertIn("mapper_split_enabled=1", note)
            self.assertIn("mapper_split_chunk_count=2", note)
            self.assertIn("mapper_split_chunks=64,32", note)

    def test_mapper_notes_single_chunk(self):
        with tempfile.TemporaryDirectory() as td:
            sched = Path(td) / "sched.yml"
            self._write_schedule(
                sched,
                {
                    "version": 0.1,
                    "ops": [{"id": "gemm2", "type": "gemm", "n": 256}],
                },
            )
            note = self.run_campaign.mapper_split_note_from_schedule(str(sched))
            self.assertIn("mapper_split_enabled=0", note)
            self.assertIn("mapper_split_chunk_count=1", note)
            self.assertIn("mapper_split_chunks=256", note)


if __name__ == "__main__":
    unittest.main()

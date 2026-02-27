#!/usr/bin/env python3
"""Regression tests for runs metrics parsing in validation/index scripts."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HEADER = (
    "design,platform,config_hash,param_hash,tag,status,critical_path_ns,"
    "die_area,total_power_mw,params_json,result_path"
)


def load_script_module(name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RunsParserRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validate_runs = load_script_module(
            "validate_runs", "scripts/validate_runs.py"
        )
        cls.build_runs_index = load_script_module(
            "build_runs_index", "scripts/build_runs_index.py"
        )

    def _write_metrics_csv(self, rows):
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        path = Path(tmpdir.name) / "metrics.csv"
        body = "\n".join([HEADER, *rows]) + "\n"
        path.write_text(body, encoding="utf-8")
        return path

    def _assert_parseable_params(self, row):
        params = json.loads(row["params_json"])
        self.assertIsInstance(params, dict)
        self.assertIn("CLOCK_PERIOD", params)
        self.assertTrue(str(row["result_path"]).strip())

    def test_validate_runs_parses_unquoted_and_csv_quoted_params_json(self):
        legacy_row = (
            "adder_koggestone_64u_wrapper,nangate45,7a7b72571aac,ef9c722d,"
            "prefix_adders_nangate45_40523b9d,ok,0.2507,17669.055625,0.00112,"
            '{"CLOCK_PERIOD": 2.5, "CORE_UTILIZATION": 10, "PLACE_DENSITY": 0.55, '
            '"TAG": "prefix_adders_nangate45_40523b9d"},'
            "/workspaces/RTLGen/runs/designs/prefix_adders/adder_koggestone_64u_wrapper/"
            "work/ef9c722d/result.json"
        )
        quoted_row = (
            "npu_fp16_cpp_hiercmp,nangate45,e94cab253974,77d647dd,"
            "npu_fp16_hiercmp_cmp_33_flat_nomacro,ok,5.701286780426342,2250000.0,0.210414,"
            '"{""CLOCK_PERIOD"": 10.0, ""CORE_AREA"": ""50 50 1450 1450"", '
            '""CORE_UTILIZATION"": """", ""DIE_AREA"": ""0 0 1500 1500"", '
            '""FLOW_VARIANT"": ""cmp33_flat_nomacro"", ""PLACE_DENSITY"": 0.4, '
            '""SYNTH_HIERARCHICAL"": 0, ""SYNTH_KEEP_MODULES"": """", '
            '""TAG"": ""npu_fp16_hiercmp_cmp_33_flat_nomacro"", '
            '""tag_prefix"": ""npu_fp16_hiercmp""}",'
            "/orfs/flow/logs/nangate45/npu_fp16_cpp_hiercmp/cmp33_flat_nomacro/3_3_place_gp.json"
        )
        metrics_path = self._write_metrics_csv([legacy_row, quoted_row])

        fields, rows = self.validate_runs.read_metrics_csv(metrics_path)
        self.assertEqual(2, len(rows))
        self.assertIn("params_json", fields)
        self.assertIn("result_path", fields)
        for row in rows:
            self._assert_parseable_params(row)

    def test_build_runs_index_parses_unquoted_and_csv_quoted_params_json(self):
        legacy_row = (
            "adder_brentkung_16u_wrapper,asap7,727a973b283c,67898f3f,"
            "prefix_adders_asap7_relaxed_a96d1e8e,ok,0.4418263,344.510721,0.000133,"
            '{"CLOCK_PERIOD": 1.0, "CORE_UTILIZATION": 8, "PLACE_DENSITY": 0.5, '
            '"TAG": "prefix_adders_asap7_relaxed_a96d1e8e"},'
            "runs/designs/prefix_adders/adder_brentkung_16u_wrapper/work/67898f3f/result.json"
        )
        quoted_row = (
            "npu_fp16_cpp_l1,nangate45,8e017cf47c46,5d34f219,npu_fp16_5d34f219,ok,"
            "5.6462,2250000.0,0.229,"
            '"{""CLOCK_PERIOD"": 10.0, ""CORE_AREA"": ""50 50 1450 1450"", '
            '""CORE_UTILIZATION"": """", ""DIE_AREA"": ""0 0 1500 1500"", '
            '""PLACE_DENSITY"": 0.4, ""tag_prefix"": ""npu_fp16""}",'
            "/orfs/flow/reports/nangate45/npu_fp16_cpp_l1/base/6_finish.rpt"
        )
        metrics_path = self._write_metrics_csv([legacy_row, quoted_row])

        rows = self.build_runs_index.load_metrics(metrics_path)
        self.assertEqual(2, len(rows))
        for row in rows:
            self._assert_parseable_params(row)


if __name__ == "__main__":
    unittest.main()

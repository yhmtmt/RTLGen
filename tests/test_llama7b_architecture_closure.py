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

    def test_norm_records_exact_rtl_and_register_storage_boundary(self) -> None:
        norm = next(item for item in self.matrix["components"] if item["id"] == "norm")
        self.assertEqual(norm["status"], "open")
        self.assertEqual(norm["dimensions"]["rtl"]["status"], "closed")
        self.assertEqual(norm["dimensions"]["equivalence"]["status"], "measured_component")
        self.assertEqual(norm["dimensions"]["routed_ppa"]["status"], "open")
        self.assertIn("failed synthesis", norm["dimensions"]["routed_ppa"]["summary"])
        self.assertIn("10/14/18 ns routed sweep", norm["next_gate"])
        evidence_paths = {entry["path"] for entry in norm["evidence"]}
        self.assertIn("npu/docs/llama7b_rmsnorm_banked_storage_contract.md", evidence_paths)
        self.assertIn("npu/eval/probe_llama7b_rmsnorm_phase3_equivalence.py", evidence_paths)
        self.assertIn(
            "npu/docs/generated/llama7b_rmsnorm_macro_banked_latency_composition.json",
            evidence_paths,
        )
        self.assertIn("65-row/token", norm["dimensions"]["composition"]["summary"])
        self.assertIn("excludes transformer RMSNorm", norm["dimensions"]["composition"]["summary"])

    def test_multivalue_service_activity_is_measured_but_not_signoff(self) -> None:
        component = next(item for item in self.matrix["components"] if item["id"] == "multivalue_service")
        self.assertEqual(component["status"], "routed_with_caveat")
        self.assertEqual(component["dimensions"]["activity"]["status"], "measured_component")
        joined_caveats = "\n".join(component["caveats"])
        self.assertIn("exploratory routed PPA", joined_caveats)
        self.assertIn("service-window component energy", joined_caveats)
        evidence_paths = {entry["path"] for entry in component["evidence"]}
        self.assertIn(
            "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
            "decoder_attention_decode_score_multivalue_service_activity_power__"
            "l2_decoder_attention_decode_score_multivalue_service_c1_activity_power_llama7b_v1_r8.json",
            evidence_paths,
        )

    def test_producer_service_reducer_composition_reflects_four_group_closure(self) -> None:
        component = next(
            item for item in self.matrix["components"] if item["id"] == "producer_service_reducer_composition"
        )
        self.assertEqual(component["status"], "rtl_unmeasured")
        self.assertEqual(component["dimensions"]["equivalence"]["status"], "measured_component")
        self.assertEqual(component["dimensions"]["composition"]["status"], "measured_component")
        self.assertEqual(component["dimensions"]["scale_validation"]["status"], "measured_component")
        summary = component["summary"]
        self.assertIn("four GQA8 groups per representative", summary)
        self.assertIn("66740", summary)
        self.assertIn("Representative routed composition", summary)
        self.assertIn("remain open", summary)
        self.assertNotIn("one-group proof alone", summary)
        evidence_paths = {entry["path"] for entry in component["evidence"]}
        self.assertIn(
            "docs/proposals/"
            "prop_l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_"
            "llama7b_v1/analysis_report.md",
            evidence_paths,
        )
        self.assertIn(
            "docs/proposals/"
            "prop_l2_decoder_attention_score32_exact_reduction_gqa8_full_equivalence_rerank_llama7b_v1/"
            "analysis_report.md",
            evidence_paths,
        )

    def test_paired_ingress_is_not_promoted_as_transport_or_power_closure(self) -> None:
        component = next(item for item in self.matrix["components"] if item["id"] == "noc")
        self.assertEqual(component["status"], "open")
        self.assertEqual(component["dimensions"]["composition"]["status"], "open")
        self.assertEqual(component["dimensions"]["activity"]["status"], "open")
        self.assertIn("2,113,984", component["dimensions"]["composition"]["summary"])
        self.assertIn("diagnostic evaluation", component["dimensions"]["composition"]["summary"])
        self.assertTrue(any("cluster_adapter_contract.md" in entry["path"] for entry in component["evidence"]))

    def test_pending_schedule_wrapper_activity_is_not_claimed_as_promoted(self) -> None:
        for component_id in ("precision", "score_softmax", "scheduler_cdc", "full_llama7b_recost"):
            component = next(item for item in self.matrix["components"] if item["id"] == component_id)
            self.assertEqual(component["dimensions"]["activity"]["status"], "open")
            activity_summary = component["dimensions"]["activity"]["summary"].lower()
            self.assertIn("pending", activity_summary)
            self.assertNotIn("already", activity_summary)
            self.assertNotIn("promoted", activity_summary)

        full = next(item for item in self.matrix["components"] if item["id"] == "full_llama7b_recost")
        self.assertEqual(full["status"], "open")
        self.assertEqual(full["confidence"], "low")
        self.assertIn("RMSNorm", full["summary"])
        self.assertIn("retracted", full["summary"])
        self.assertIn("146.083--172.388 ms", full["summary"])
        self.assertIn("29.361--50.588 ms", full["summary"])
        self.assertIn("30.034--52.694 ms", full["summary"])
        self.assertIn("72.544 ms", full["summary"])
        self.assertIn("score32 membership is unproven", full["summary"])
        evidence_paths = {entry["path"] for entry in full["evidence"]}
        self.assertIn("npu/docs/generated/llama7b_physically_credible_pareto.json", evidence_paths)
        self.assertIn(
            "npu/docs/generated/llama7b_score32_cadence_frontier_consistency.json",
            evidence_paths,
        )

    def test_noc_and_sram_reflect_promoted_post_august_physical_anchors(self) -> None:
        noc = next(item for item in self.matrix["components"] if item["id"] == "noc")
        self.assertEqual(noc["status"], "open")
        self.assertEqual(noc["confidence"], "medium")
        self.assertEqual(noc["dimensions"]["routed_ppa"]["status"], "measured_component")
        self.assertEqual(noc["dimensions"]["equivalence"]["status"], "open")
        self.assertEqual(noc["dimensions"]["activity"]["status"], "open")
        self.assertIn("not activity-backed energy", noc["dimensions"]["activity"]["summary"])
        noc_evidence = {entry["path"] for entry in noc["evidence"]}
        self.assertIn(
            "docs/proposals/prop_l1_segmented_xy_mesh_noc_phase1_v1/analysis_report.md",
            noc_evidence,
        )

        sram = next(item for item in self.matrix["components"] if item["id"] == "sram")
        self.assertEqual(sram["dimensions"]["routed_ppa"]["status"], "measured_component")
        self.assertEqual(sram["dimensions"]["activity"]["status"], "open")
        self.assertIn("macro/proxy pins", sram["dimensions"]["activity"]["summary"])
        self.assertIn("different hierarchy", sram["dimensions"]["activity"]["summary"])
        sram_evidence = {entry["path"] for entry in sram["evidence"]}
        self.assertIn(
            "docs/proposals/prop_l1_attention_shared_sram_read_group_adapter_ppa_v1/analysis_report.md",
            sram_evidence,
        )
        self.assertIn(
            "docs/proposals/prop_l1_attention_shared_sram_k_round_scheduler_ppa_v1/analysis_report.md",
            sram_evidence,
        )
        self.assertIn(
            "docs/proposals/prop_decoder_attention_decode_score_multivalue_cluster_activity_power_llama7b_v1/"
            "evaluation_requests.json",
            sram_evidence,
        )
        self.assertIn("same routed netlist", sram["next_gate"])

    def test_mapper_is_explicitly_open_for_selected_llama7b_hierarchy(self) -> None:
        mapper = next(
            item for item in self.matrix["components"] if item["id"] == "mapper_workload_lowering"
        )
        self.assertEqual(mapper["status"], "open")
        self.assertEqual(mapper["confidence"], "low")
        self.assertEqual(mapper["dimensions"]["equivalence"]["status"], "open")
        self.assertEqual(mapper["dimensions"]["activity"]["status"], "open")
        self.assertIn("not yet unified", mapper["dimensions"]["composition"]["summary"])
        self.assertIn("canonical Llama7B score32 mapper IR", mapper["next_gate"])
        evidence_paths = {entry["path"] for entry in mapper["evidence"]}
        self.assertIn("npu/mapper/onnx_to_schedule.py", evidence_paths)
        self.assertIn(
            "docs/proposals/prop_l2_mapper_memory_aware_split_v1/analysis_report.md",
            evidence_paths,
        )


if __name__ == "__main__":
    unittest.main()

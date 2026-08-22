from __future__ import annotations

import contextlib
import io
import json
import math
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.audit_llama7b_shared_sram_access_energy import (  # noqa: E402
    DEFAULT_SHARED_CAPACITY_BYTES,
    _rank_composed,
    build_audit_report,
    load_selected_macros,
    main,
)


class SharedSramAccessEnergyAuditTest(unittest.TestCase):
    def test_loads_checked_numeric_cacti_values(self) -> None:
        selected, native = load_selected_macros()
        self.assertEqual(selected.name, "local_capacity_chunk_02_256kib")
        self.assertEqual(selected.capacity_bytes, 262144)
        self.assertEqual(selected.width_bits, 1024)
        self.assertEqual(selected.word_size_bytes, 128)
        self.assertAlmostEqual(selected.access_time_ns, 1.22148, places=8)
        self.assertAlmostEqual(selected.read_energy_pj, 177.523, places=6)
        self.assertAlmostEqual(selected.write_energy_pj, 623.1, places=6)
        self.assertAlmostEqual(selected.area_um2, 882595.72388, places=5)
        self.assertEqual(native.name, "kv_tile_read_buffer")
        self.assertEqual(native.width_bits, 256)
        self.assertEqual(native.word_size_bytes, 32)
        self.assertAlmostEqual(native.access_time_ns, 1.4124, places=7)
        self.assertAlmostEqual(native.read_energy_pj, 241.555, places=6)
        self.assertAlmostEqual(native.write_energy_pj, 288.401, places=6)

    def test_four_flit_coalescing_reduces_accesses_by_four(self) -> None:
        report = build_audit_report(scope="one_layer_remote")
        burst = report["profiles"]["selected_1024b_macro_burst4"]
        naive = report["profiles"]["selected_1024b_macro_naive_flit"]
        self.assertEqual(report["traffic"]["payload_bytes"], 112 * 17_408)
        self.assertEqual(report["traffic"]["flit_count"], 112 * 544)
        self.assertEqual(report["total_source_traffic"]["payload_bytes"], 128 * 17_408)
        self.assertEqual(report["total_source_traffic"]["flit_count"], 128 * 544)
        self.assertEqual(burst["access_count"] * 4, naive["access_count"])
        self.assertEqual(burst["access_count"], 128 * 136)
        self.assertEqual(
            burst["coalesced_flit_count"],
            report["total_source_traffic"]["flit_count"],
        )
        self.assertEqual(burst["macro_word_padding_bytes"], 0)
        self.assertEqual(naive["macro_word_padding_bytes"], (4 - 1) * 32 * naive["access_count"])
        self.assertEqual(burst["byte_masked_access_count"], 0)
        self.assertEqual(naive["byte_masked_access_count"], naive["access_count"])

    def test_energy_uses_access_count_not_capacity(self) -> None:
        report = build_audit_report(scope="one_layer_remote")
        burst = report["composed_profiles"][
            "shared1024_burst4_source_local256_destination"
        ]
        source_access_count = 2_228_224 // 128
        remote_source_access_count = 112 * 136
        local_bypass_access_count = 16 * 136
        destination_access_count = 112 * 544
        total_source_bytes = 128 * 17_408
        remote_payload_bytes = 112 * 17_408
        expected_read_pj = source_access_count * 177.523
        expected_write_pj = destination_access_count * 288.401
        self.assertAlmostEqual(burst["source_read"]["energy_pj"], expected_read_pj, places=6)
        self.assertAlmostEqual(burst["destination_write"]["energy_pj"], expected_write_pj, places=6)
        self.assertAlmostEqual(
            burst["total_sram_energy_pj"],
            source_access_count * 177.523 + destination_access_count * 288.401,
            places=6,
        )
        self.assertEqual(burst["source_read"]["access_count"], 17_408)
        self.assertEqual(burst["remote_source_read"]["access_count"], remote_source_access_count)
        self.assertEqual(
            burst["local_bypass_source_read"]["access_count"],
            local_bypass_access_count,
        )
        self.assertEqual(
            burst["remote_source_read"]["access_count"]
            + burst["local_bypass_source_read"]["access_count"],
            burst["source_read"]["access_count"],
        )
        self.assertAlmostEqual(
            burst["source_read"]["energy_per_useful_byte_pj"],
            expected_read_pj / total_source_bytes,
            places=12,
        )
        expected_remote_only_pj = remote_source_access_count * 177.523 + expected_write_pj
        self.assertAlmostEqual(
            burst["remote_only_energy_per_useful_byte_pj"],
            expected_remote_only_pj / remote_payload_bytes,
            places=12,
        )
        wrong_capacity_normalization = (
            burst["source_shared_capacity_pack"]["macro_count"]
            * 177.523
            / DEFAULT_SHARED_CAPACITY_BYTES
        )
        self.assertFalse(
            math.isclose(
                burst["source_read"]["energy_per_useful_byte_pj"],
                wrong_capacity_normalization,
                rel_tol=1e-12,
                abs_tol=1e-12,
            )
        )
        self.assertEqual(burst["source_shared_capacity_pack"]["macro_count"], 272)
        self.assertAlmostEqual(
            burst["source_shared_capacity_pack"]["area_um2"],
            272 * 882595.72388,
            places=4,
        )
        self.assertIsNone(burst["destination_capacity_pack"])
        self.assertEqual(
            burst["destination_write"]["macro"]["name"],
            "kv_tile_read_buffer",
        )
        self.assertEqual(burst["destination_write"]["access_count"], destination_access_count)

    def test_native_256_width_pack_is_reported_separately(self) -> None:
        report = build_audit_report(scope="one_layer_remote")
        native = report["composed_profiles"][
            "native256_shared_source_local256_destination"
        ]
        self.assertEqual(native["source_read"]["macro"]["width_bits"], 256)
        self.assertEqual(native["source_read"]["macro"]["word_size_bytes"], 32)
        self.assertEqual(
            native["source_read"]["access_count"],
            report["total_source_traffic"]["flit_count"],
        )
        self.assertEqual(native["source_read"]["macro_word_padding_bytes"], 0)
        self.assertEqual(native["source_shared_capacity_pack"]["macro_count"], 136)
        self.assertAlmostEqual(
            native["source_shared_capacity_pack"]["area_um2"],
            136 * 2082403.0404,
            places=4,
        )
        self.assertIsNone(native["destination_capacity_pack"])

    def test_unaligned_payload_marks_only_the_final_native_access(self) -> None:
        report = build_audit_report(
            scope="one_layer_remote",
            fractional_tile_bytes=17_407,
        )
        native = report["profiles"]["native_256b_macro"]
        burst = report["profiles"]["selected_1024b_macro_burst4"]
        self.assertEqual(native["byte_masked_access_count"], 128)
        self.assertEqual(native["fully_utilized_access_count"], native["access_count"] - 128)
        self.assertEqual(burst["byte_masked_access_count"], 128)
        self.assertGreater(native["macro_word_padding_bytes"], 0)
        self.assertGreater(burst["macro_word_padding_bytes"], 0)

    def test_source_and_destination_and_persistence_are_explicit(self) -> None:
        transient = build_audit_report(persistence_mode="transient")
        persistent = build_audit_report(persistence_mode="persistent")
        transient_path = transient["composed_profiles"][
            "shared1024_burst4_source_local256_destination"
        ]
        persistent_path = persistent["composed_profiles"][
            "shared1024_burst4_source_local256_destination"
        ]
        self.assertEqual(transient_path["source_read"]["access_count"], 128 * 136)
        self.assertEqual(transient_path["destination_write"]["access_count"], 112 * 544)
        self.assertEqual(
            transient_path["total_sram_energy_pj"],
            persistent_path["total_sram_energy_pj"],
        )
        self.assertEqual(transient["traffic"]["payload_bytes"], persistent["traffic"]["payload_bytes"])
        self.assertEqual(transient["traffic"]["source_read_bytes"], persistent["traffic"]["source_read_bytes"])
        self.assertIn("does not model HBM behavior", persistent["traffic"]["persistence_note"])

    def test_locality_aware_has_local_reads_and_zero_destination_writes(self) -> None:
        report = build_audit_report(scope="one_layer_remote")
        traffic = report["locality_aware_traffic"]
        path = report["locality_aware_composed_profiles"][
            "shared1024_burst4_local_read"
        ]
        self.assertEqual(traffic["placement"], "local")
        self.assertGreater(traffic["source_read_bytes"], 0)
        self.assertEqual(traffic["destination_write_bytes"], 0)
        self.assertEqual(traffic["transport_packet_count"], 0)
        self.assertEqual(traffic["transport_flit_count"], 0)
        self.assertGreater(path["source_read"]["access_count"], 0)
        self.assertEqual(path["destination_write"]["access_count"], 0)
        self.assertEqual(path["destination_write"]["energy_pj"], 0.0)
        self.assertIsNone(path["destination_capacity_pack"])

    def test_historical_local_bypass_completes_total_source_workload(self) -> None:
        report = build_audit_report(scope="one_layer_remote")
        remote = report["traffic"]
        bypass = report["historical_local_bypass_traffic"]
        total = report["total_source_traffic"]
        self.assertEqual(remote["context_count"], 112)
        self.assertEqual(bypass["context_count"], 16)
        self.assertEqual(total["context_count"], 128)
        self.assertEqual(remote["payload_bytes"], 1_949_696)
        self.assertEqual(bypass["payload_bytes"], 278_528)
        self.assertEqual(total["payload_bytes"], 2_228_224)
        self.assertEqual(total["payload_bytes"], remote["payload_bytes"] + bypass["payload_bytes"])
        self.assertEqual(total["destination_write_bytes"], remote["payload_bytes"])
        self.assertEqual(total["transport_flit_count"], 60_928)

    def test_rankings_and_summary_use_only_composed_paths(self) -> None:
        report = build_audit_report(scope="one_layer_remote")
        remote_names = set(report["composed_profiles"])
        local_names = set(report["locality_aware_composed_profiles"])
        self.assertEqual(
            {row["profile"] for row in report["ranking"]["remote"]},
            remote_names,
        )
        self.assertEqual(
            {row["profile"] for row in report["ranking"]["locality_aware"]},
            local_names,
        )
        self.assertEqual(
            report["summary"]["best_remote_profile"],
            "shared1024_burst4_source_local256_destination",
        )
        self.assertEqual(report["summary"]["remote_destination_write_accesses"], 112 * 544)
        self.assertEqual(report["summary"]["historical_burst4_total_source_read_accesses"], 17_408)
        self.assertEqual(report["summary"]["locality_aware_destination_write_accesses"], 0)
        self.assertNotIn("selected_1024b_macro_burst4", remote_names)
        ranked_energies = [row["total_layer_energy_pj"] for row in report["ranking"]["remote"]]
        self.assertEqual(ranked_energies, sorted(ranked_energies))
        self.assertEqual(report["summary"]["ranking_metric"], "total_layer_energy_pj")

    def test_ranking_uses_total_layer_energy_not_per_byte_diagnostic(self) -> None:
        common = {
            "total_layer_energy_nj": 0.0,
            "total_layer_energy_per_total_source_byte_pj": 0.0,
            "remote_only_energy_per_useful_byte_pj": 0.0,
            "total_sram_energy_pj": 0.0,
            "source_capacity_area_mm2": 1.0,
            "endpoint_access_time_bound_ns": 1.0,
        }
        profiles = {
            "lower_total_higher_per_byte": {
                **common,
                "total_layer_energy_pj": 10.0,
                "total_energy_per_useful_byte_pj": 100.0,
            },
            "higher_total_lower_per_byte": {
                **common,
                "total_layer_energy_pj": 20.0,
                "total_energy_per_useful_byte_pj": 1.0,
            },
        }
        self.assertEqual(_rank_composed(profiles)[0]["profile"], "lower_total_higher_per_byte")

    def test_shape_and_kv_heads_are_threaded_through_report_and_cli(self) -> None:
        report = build_audit_report(kv_heads=32, head_dim=64, kv_bits=16)
        self.assertEqual(report["shape"]["kv_heads"], 32)
        self.assertEqual(report["shape"]["head_dim"], 64)
        self.assertEqual(report["shape"]["kv_bits"], 16)
        self.assertEqual(report["shape"], report["total_source_traffic"]["shape"])
        self.assertEqual(report["configuration"]["shape"], report["shape"])
        self.assertEqual(report["configuration"]["clusters"], 16)
        self.assertEqual(report["configuration"]["packet_payload_bytes"], 256)
        self.assertEqual(report["shape"]["full_kv_bytes"], 32 * 1024**3)
        self.assertEqual(
            report["summary"]["historical_burst4_total_source_read_accesses"],
            17_408,
        )

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(
                main(["--kv-heads", "32", "--head-dim", "64", "--kv-bits", "16"]),
                0,
            )
        cli_report = json.loads(stdout.getvalue())
        self.assertEqual(cli_report["shape"]["kv_heads"], 32)
        self.assertEqual(cli_report["shape"]["head_dim"], 64)
        self.assertEqual(cli_report["shape"]["kv_bits"], 16)

    def test_full_model_scope_scales_remote_and_total_source_inputs(self) -> None:
        one_layer = build_audit_report(scope="one_layer_remote")
        full_model = build_audit_report(scope="full_model")
        self.assertEqual(full_model["traffic"]["context_count"], 32 * one_layer["traffic"]["context_count"])
        self.assertEqual(full_model["traffic"]["payload_bytes"], 32 * one_layer["traffic"]["payload_bytes"])
        self.assertEqual(
            full_model["total_source_traffic"]["payload_bytes"],
            32 * one_layer["total_source_traffic"]["payload_bytes"],
        )
        self.assertEqual(
            full_model["composed_profiles"][
                "shared1024_burst4_source_local256_destination"
            ]["source_read"]["access_count"],
            32
            * one_layer["composed_profiles"][
                "shared1024_burst4_source_local256_destination"
            ]["source_read"]["access_count"],
        )


if __name__ == "__main__":
    unittest.main()

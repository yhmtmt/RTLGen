import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.rtlgen.gen_attention_score32_exact_cluster_sram_service_gqa8 import build_default_config, generate
from npu.sim.perf.attention_score32_exact_cluster_sram_service_gqa8 import (
    BUFFER_BYTES,
    ClusterSramServiceModel,
    DOUBLE_BUFFER_BYTES,
    MANIFEST_NAME,
    ROWS_PER_BANK_PER_BUFFER,
    ROWS_PER_BUFFER,
    STREAMS,
    cluster_sram_service_manifest,
    exact_local_cluster_gqa8_command_block_counts,
    exact_local_cluster_gqa8_slot_bases,
)


def _row_data(buffer_sel: int, stream: int, block_slot: int, slice_index: int) -> int:
    return (
        (int(buffer_sel) << 20)
        | (int(stream) << 19)
        | (int(block_slot) << 8)
        | (int(slice_index) << 1)
        | 1
    )


def _fill_model(model: ClusterSramServiceModel, *, buffer_sel: int, command_id: int, head_base: int, wave_index: int) -> None:
    model.load_buffer(
        buffer_sel=buffer_sel,
        command_id=command_id,
        head_base=head_base,
        wave_index=wave_index,
        row_fn=lambda stream, block_slot, slice_index: _row_data(buffer_sel, stream, block_slot, slice_index),
    )


def _activate_model(
    *,
    producers: int,
    buffer_sel: int = 0,
    command_id: int = 9,
    head_base: int = 0,
    wave_index: int = 2,
) -> ClusterSramServiceModel:
    model = ClusterSramServiceModel(producers=producers)
    _fill_model(
        model,
        buffer_sel=buffer_sel,
        command_id=command_id,
        head_base=head_base,
        wave_index=wave_index,
    )
    assert model.accept_command(
        buffer_sel=buffer_sel,
        command_id=command_id,
        head_base=head_base,
        wave_index=wave_index,
    )
    return model


class ClusterSramServiceTests(unittest.TestCase):
    def test_exact_cluster_sram_service_maps_capacity_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cluster_sram_service_manifest_") as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            for producers, first_extra_count in ((53, 11), (54, 10)):
                service_model = cluster_sram_service_manifest(producers=producers)
                self.assertEqual(service_model["rows_per_bank_per_buffer"], ROWS_PER_BANK_PER_BUFFER)
                self.assertEqual(service_model["rows_per_buffer"], ROWS_PER_BUFFER)
                self.assertEqual(service_model["buffer_bytes"], BUFFER_BYTES)
                self.assertEqual(service_model["double_buffer_bytes_per_cluster"], DOUBLE_BUFFER_BYTES)
                self.assertEqual(service_model["response_fifo_depth_per_lane"], 1)
                self.assertEqual(service_model["bank_reads_per_cycle"], 1)
                self.assertEqual(service_model["schedule"]["per_group_total_blocks_per_stream"], [64, 64, 64, 64])
                self.assertIn("blocks_same_cycle_request_grants", service_model["release_contract"])

                counts = exact_local_cluster_gqa8_command_block_counts(producers=producers, group_index=0)
                bases = exact_local_cluster_gqa8_slot_bases(producers=producers, group_index=0)
                self.assertEqual(counts[:first_extra_count], (2,) * first_extra_count)
                self.assertEqual(counts[first_extra_count:], (1,) * (producers - first_extra_count))
                self.assertEqual(bases[0], 0)
                self.assertEqual(bases[first_extra_count - 1], (first_extra_count - 1) * 2)
                self.assertEqual(bases[first_extra_count], first_extra_count * 2)
                self.assertEqual(bases[-1] + counts[-1], 64)

                config = build_default_config(producers=producers)
                out_dir = temp_dir / f"rtl_p{producers}"
                generate(config, out_dir)
                manifest = json.loads((out_dir / MANIFEST_NAME).read_text(encoding="utf-8"))
                self.assertEqual(manifest["service_model"], service_model)
                self.assertIn("not SRAM-macro closed", manifest["synthesizability_note"])

                rtl = (out_dir / "top.v").read_text(encoding="utf-8")
                self.assertIn("reg [ROW_BITS-1:0] bank_mem [0:BANKS-1][0:1][0:ROWS_PER_BANK_PER_BUFFER-1];", rtl)
                self.assertIn("output wire [31:0] bank_conflict_count,", rtl)
                self.assertIn("bank_conflict_count_q <= bank_conflict_count_q + bank_conflict_delta_r;", rtl)

    def test_exact_cluster_sram_service_fill_residency_response_and_tag(self) -> None:
        model = _activate_model(producers=53, command_id=17, head_base=0, wave_index=3)
        self.assertEqual(model.resident[0], (17, 0, 3))
        self.assertEqual(model.buffer_occupancy_rows, (2048, 0))

        lane = 5
        producer = lane // STREAMS
        address = 1
        slice_index = 7
        responses = model.step(requests=[(lane, address, slice_index)])
        self.assertEqual(responses, [])

        pending = model.responses[lane]
        assert pending is not None
        expected_slot = exact_local_cluster_gqa8_slot_bases(producers=53, group_index=0)[producer] + address
        self.assertEqual(pending.data, _row_data(0, lane % STREAMS, expected_slot, slice_index))
        self.assertEqual(pending.tag, model.build_tag(lane=lane, address=address, slice_index=slice_index))

        drained = model.step(response_ready=[lane])
        self.assertEqual(len(drained), 1)
        self.assertEqual(drained[0], pending)
        self.assertEqual(model.counters["request_accept_count"], 1)
        self.assertEqual(model.counters["response_accept_count"], 1)
        self.assertEqual(model.outstanding_response_occupancy, 0)
        self.assertFalse(model.protocol_error)

    def test_exact_cluster_sram_service_backpressure_holds_valid_without_protocol_error(self) -> None:
        idle_model = ClusterSramServiceModel(producers=53)
        idle_model.step(requests=[(0, 0, 0)])
        self.assertFalse(idle_model.protocol_error)
        self.assertEqual(idle_model.counters["request_stall_cycles"], 1)

        model = _activate_model(producers=53)
        model.step(requests=[(0, 0, 0)])
        self.assertIsNotNone(model.responses[0])
        model.step()
        model.step(requests=[(0, 0, 0)])
        self.assertIsNotNone(model.responses[0])
        self.assertEqual(model.counters["response_stall_cycles"], 2)
        self.assertEqual(model.counters["request_stall_cycles"], 1)
        self.assertFalse(model.protocol_error)

    def test_exact_cluster_sram_service_invalid_accepted_request_returns_zero_and_sets_error(self) -> None:
        model = _activate_model(producers=54, head_base=0)
        model.step(requests=[(0, 8, 3)])
        pending = model.responses[0]
        assert pending is not None
        self.assertEqual(pending.data, 0)
        self.assertTrue(model.errors["invalid_address"])
        self.assertEqual(model.counters["request_accept_count"], 1)

    def test_exact_cluster_sram_service_invalid_slice_returns_zero_and_sets_error(self) -> None:
        for slice_index in (-1, 16):
            with self.subTest(slice_index=slice_index):
                model = _activate_model(producers=54, head_base=0)
                model.step(requests=[(0, 0, slice_index)])
                pending = model.responses[0]
                assert pending is not None
                self.assertEqual(pending.data, 0)
                self.assertEqual(pending.slice_index, slice_index)
                self.assertTrue(model.errors["invalid_address"])
                self.assertEqual(model.counters["request_accept_count"], 1)

    def test_exact_cluster_sram_service_duplicate_fill_row_sets_overwrite(self) -> None:
        model = ClusterSramServiceModel(producers=53)
        self.assertTrue(model.accept_fill_target(buffer_sel=0, command_id=1, head_base=0, wave_index=0))
        self.assertTrue(model.fill_row(buffer_sel=0, stream=0, block_slot=0, slice_index=0, data=_row_data(0, 0, 0, 0)))
        self.assertFalse(model.fill_row(buffer_sel=0, stream=0, block_slot=0, slice_index=0, data=_row_data(0, 0, 0, 0)))
        self.assertTrue(model.errors["overwrite"])
        self.assertEqual(model.counters["fill_row_accept_count"], 1)
        self.assertEqual(model.buffer_occupancy_rows, (1, 0))

    def test_exact_cluster_sram_service_counters_track_actual_simultaneous_events(self) -> None:
        model = _activate_model(producers=53)
        model.step(requests=[(0, 0, 0), (1, 0, 1)])
        self.assertEqual(model.counters["request_accept_count"], 2)
        self.assertEqual(model.counters["request_stall_cycles"], 0)
        self.assertEqual(model.counters["bank_conflict_count"], 0)
        self.assertEqual(model.outstanding_response_occupancy, 2)

        model.step(response_ready=[0, 1])
        self.assertEqual(model.counters["response_accept_count"], 2)

    def test_exact_cluster_sram_service_same_bank_contention_serializes_and_counts_conflicts(self) -> None:
        model = _activate_model(producers=53)
        model.step(requests=[(0, 0, 0), (2, 0, 0)])
        self.assertIsNotNone(model.responses[0])
        self.assertIsNone(model.responses[2])
        self.assertEqual(model.counters["request_accept_count"], 1)
        self.assertEqual(model.counters["request_stall_cycles"], 1)
        self.assertEqual(model.counters["bank_conflict_count"], 1)

        drained = model.step(requests=[(2, 0, 0)], response_ready=[0])
        self.assertEqual(len(drained), 1)
        self.assertEqual(drained[0].lane, 0)
        self.assertIsNotNone(model.responses[2])
        self.assertEqual(model.counters["request_accept_count"], 2)

    def test_exact_cluster_sram_service_atomic_release_blocks_same_cycle_requests(self) -> None:
        model = _activate_model(producers=53, buffer_sel=0, command_id=21, head_base=8, wave_index=4)
        held_requests = [(0, 0, 0), (1, 0, 1)]

        released = model.step(
            requests=held_requests,
            release_valid=True,
            release_buffer_sel=0,
        )
        self.assertEqual(released, [])
        self.assertIsNone(model.active)
        self.assertIsNone(model.resident[0])
        self.assertFalse(model.release_ready(buffer_sel=0))
        self.assertEqual(model.buffer_occupancy_rows, (0, 0))
        self.assertEqual(model.outstanding_response_occupancy, 0)
        self.assertEqual(model.counters["command_release_count"], 1)
        self.assertEqual(model.counters["request_accept_count"], 0)
        self.assertEqual(model.counters["request_stall_cycles"], len(held_requests))
        self.assertEqual(model.counters["bank_conflict_count"], 0)
        self.assertFalse(model.protocol_error)
        self.assertFalse(model.command_ready(buffer_sel=0, command_id=21, head_base=8, wave_index=4))

        idle = model.step(requests=held_requests)
        self.assertEqual(idle, [])
        self.assertEqual(model.counters["request_accept_count"], 0)
        self.assertEqual(model.counters["request_stall_cycles"], len(held_requests) * 2)
        self.assertEqual(model.outstanding_response_occupancy, 0)
        self.assertFalse(model.protocol_error)


if __name__ == "__main__":
    unittest.main()

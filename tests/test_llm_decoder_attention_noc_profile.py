import argparse
from pathlib import Path

from npu.eval.measure_llm_decoder_attention_noc_profile import build_profile


def _args(tmp_path: Path) -> argparse.Namespace:
    return argparse.Namespace(
        repo_root=tmp_path,
        sequence_length=131072,
        tile_tokens=512,
        hidden_size=4096,
        attention_heads=32,
        kv_heads=4,
        kv_bits=8,
        active_clusters=8,
        shared_byte_share=0.44005,
        reduction_scalar_bytes=2,
        flit_bits=[128],
        raw_bandwidth_bytes_per_cycle=[8192.0],
        hops=[1],
        virtual_channels=[4],
        arbitration_efficiency=[0.85],
        vc_base_efficiency=0.85,
        vc_increment=0.05,
        router_latency_cycles_per_hop=2,
    )


def test_attention_noc_profile_default_traffic_quantities(tmp_path: Path) -> None:
    profile = build_profile(_args(tmp_path))
    traffic = profile["traffic_quantities"]

    assert traffic["full_tile_kv_bytes"] == 2 * 512 * 4 * 128
    assert traffic["shared_tile_payload_bytes"] == 230713
    assert traffic["partial_reduction_payload_bytes"] == 4096 * 2 + 32 * 2 * 2
    assert traffic["cross_tile_reduction_payload_bytes"] == 8 * (4096 * 2 + 32 * 2 * 2)
    assert traffic["kv_write_payload_bytes"] == 2 * 4 * 128


def test_attention_noc_profile_matches_selected_best_bandwidth(tmp_path: Path) -> None:
    profile = build_profile(_args(tmp_path))
    row = profile["rows"][0]

    assert row["aggregate_effective_payload_bytes_per_cycle"] == 6963.2
    assert row["per_cluster_effective_payload_bytes_per_cycle"] == 870.4
    assert row["shared_tile_flits"] == 14420
    assert row["shared_tile_noc_cycles"] == 268
    assert row["cross_tile_reduction_noc_cycles"] == 12

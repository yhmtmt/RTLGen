from pathlib import Path

from npu.eval import audit_llm_decoder_attention_endpoint_router_sram_composition as audit


def _write_metrics_csv(path: Path, *, design: str, critical_path_ns: float, die_area: float, power_mw: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "status,critical_path_ns,die_area,total_power_mw,design",
                f"ok,{critical_path_ns},{die_area},{power_mw},{design}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _build_payload(
    *,
    repo_root: Path,
    local_sram_capacity: dict | None,
) -> audit.JsonDict:
    endpoint_ready_valid = {
        "decision": "ready_valid_endpoint_policy_passed",
        "derived_rtl_parameters": {
            "data_w": 512,
            "packet_payload_bytes": 64,
            "banks": 16,
            "endpoint_queue_depth": 1024,
            "bank_queue_depth": 1024,
        },
    }
    endpoint_onchip = {
        "best": {
            "active_clusters": 1,
            "latency_us": 3210.0,
            "topology": "mesh2d",
            "scheduler_policy": "locality_aware",
            "reduction_strategy": "cluster_tree",
            "schedule_policy": "prefetch_overlap",
            "bank_arbiter_policy": "locality_first",
            "cluster_count": 16,
            "bank_count": 64,
            "link_width_bits": 2048,
            "packet_payload_bytes": 64,
            "local_sram_fraction": 0.25,
            "sram_area_fraction": 0.35,
            "compute_logic_area_fraction": 0.5,
            "dominant_tile_resource": "shared_path",
            "noc_router_metrics_csv": "runs/designs/test/router_metrics.csv",
            "noc_fifo_metrics_csv": "runs/designs/test/fifo_metrics.csv",
            "onchip_endpoint_metrics_csv": "runs/designs/test/onchip_endpoint_metrics.csv",
            "local_capacity_bytes_per_cluster": 1024,
            "die_area_mm2": 0.8,
        }
    }
    sram_summary = {
        "total_area_um2": 128.0,
        "max_access_time_ns": 3.1,
        "total_read_energy_pj": 44.0,
        "total_write_energy_pj": 52.0,
    }
    sram_metrics = {
        "instances": [
            {"instance": {"size_bytes": 256}},
        ]
    }

    _write_metrics_csv(
        repo_root / "runs/designs/test/router_metrics.csv",
        design="noc_router_w2048",
        critical_path_ns=4.1,
        die_area=120.0,
        power_mw=0.12,
    )
    _write_metrics_csv(
        repo_root / "runs/designs/test/fifo_metrics.csv",
        design="noc_fifo_w2048",
        critical_path_ns=4.2,
        die_area=110.0,
        power_mw=0.11,
    )
    _write_metrics_csv(
        repo_root / "runs/designs/test/onchip_endpoint_metrics.csv",
        design="onchip_endpoint_w512",
        critical_path_ns=3.5,
        die_area=90.0,
        power_mw=0.09,
    )

    return audit._build_payload(
        repo_root=repo_root,
        endpoint_ready_valid=endpoint_ready_valid,
        endpoint_onchip=endpoint_onchip,
        sram_summary=sram_summary,
        sram_metrics=sram_metrics,
        wide_l1_promotion=None,
        local_sram_capacity=local_sram_capacity,
    )


def test_endpoint_router_sram_composition_audit_with_local_sram_capacity_budget_failure(tmp_path: Path) -> None:
    local_sram_capacity = {
        "source_item": "l2_decoder_attention_local_sram_capacity_llama7b_v1",
        "budget_check": {
            "fits_sram_budget": False,
            "total_area_um2": 1306824061.5888963,
            "sram_budget_area_um2": 280000000.0,
            "area_fraction_of_sram_budget": 4.667229,
        },
        "chunking": {
            "allocated_bytes_per_cluster": 2048,
        },
    }
    payload = _build_payload(repo_root=tmp_path, local_sram_capacity=local_sram_capacity)

    assert payload["closure_diagnosis"]["local_sram_capacity"] == "local_capacity_budget_failed"
    assert payload["required_follow_on_ppa"] == ["capacity_rebalance_or_smaller_local_sram_required"]
    assert payload["measured_primitives"]["local_sram_capacity"]["budget_check"]["fits_sram_budget"] is False
    assert payload["source_items"]["local_sram_capacity"] == "l2_decoder_attention_local_sram_capacity_llama7b_v1"
    assert any("exceeds the available shared SRAM budget" in item for item in payload["remaining_abstractions"])


def test_endpoint_router_sram_composition_audit_without_local_sram_capacity_falls_back_to_macro_missing(
    tmp_path: Path,
) -> None:
    payload = _build_payload(repo_root=tmp_path, local_sram_capacity=None)

    assert payload["closure_diagnosis"]["local_sram_capacity"] == "full_local_capacity_sram_macro_profile_missing"
    assert payload["required_follow_on_ppa"] == ["full_local_capacity_sram_macro_profile_missing"]
    assert payload["measured_primitives"]["local_sram_capacity"] is None
    assert payload["source_items"]["local_sram_capacity"] is None

from pathlib import Path

from npu.eval.estimate_llm_decoder_producer_ranker_coupling import build_coupling_report


def test_producer_service_derives_integer_ii_from_compute_and_memory() -> None:
    report = build_coupling_report(
        mode="producer_service",
        rank_ppa_path=None,
        scale_ppa_path=None,
        candidate_merge_ppa_path=None,
        boundary_ppa_path=None,
        producer_control_boundary_path=None,
        producer_physical_boundary_path=None,
        sram_metrics_json_path=None,
        vocab_size_list=[256],
        hidden_size_list=[64],
        producer_lanes_list=[64],
        macs_per_cycle_list=[4096],
        memory_bandwidth_bytes_per_cycle_list=[128.0],
        memory_share_list=[1.0],
        top_k_list=[1],
        weight_bits=16,
        activation_bits=16,
        clock_ns=1.0,
    )

    row = report["producer_service_sweep"][0]
    assert row["compute_cycles_per_tile"] == 1
    assert row["weight_cycles_per_tile"] == 64
    assert row["producer_ii_cycles"] == 64
    assert row["service_limiter"] == "weight_memory"
    assert report["coupled_ranker_sweep"] == []


def test_coupled_noc_reports_ranker_rows(tmp_path: Path) -> None:
    report = build_coupling_report(
        mode="coupled_noc",
        rank_ppa_path=None,
        scale_ppa_path=None,
        candidate_merge_ppa_path=None,
        boundary_ppa_path=None,
        producer_control_boundary_path=None,
        producer_physical_boundary_path=None,
        sram_metrics_json_path=None,
        vocab_size_list=[256],
        hidden_size_list=[64],
        producer_lanes_list=[64],
        macs_per_cycle_list=[4096],
        memory_bandwidth_bytes_per_cycle_list=[128.0],
        memory_share_list=[1.0, 0.5],
        top_k_list=[1],
        weight_bits=16,
        activation_bits=16,
        clock_ns=1.0,
    )

    assert report["coupled_ranker_sweep"]
    row = report["coupled_ranker_sweep"][0]
    assert row["producer_lanes"] == 64
    assert row["top_k"] == 1
    assert row["producer_ii_cycles"] >= 1
    assert "ranker_latency_us_per_token" in row
    assert row["coupled_latency_us_per_token"] >= row["producer_latency_us_per_token"]
    assert report["recommendation"]["coupled_best"] is not None


def test_coupling_report_carries_producer_control_boundary(tmp_path: Path) -> None:
    boundary = tmp_path / "softmax_event.json"
    boundary.write_text(
        """
{
  "diagnosis": {"decision": "softmax_event_guard_synth_ok_under_bound"},
  "probe_rows": [
    {
      "variant": "cq_v1_softmax_event_guard",
      "status": "ok",
      "static_verilog_stats": {
        "verilog_bytes": 57181,
        "reg_bit_count_est": 2634,
        "wire_bit_count_est": 3864
      },
      "synthesis": {"status": "ok", "elapsed_seconds": 196.2},
      "metrics_row": {"flow_elapsed_seconds": "195.14"}
    }
  ]
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    report = build_coupling_report(
        mode="producer_service",
        rank_ppa_path=None,
        scale_ppa_path=None,
        candidate_merge_ppa_path=None,
        boundary_ppa_path=None,
        producer_control_boundary_path=boundary,
        producer_physical_boundary_path=None,
        sram_metrics_json_path=None,
        vocab_size_list=[256],
        hidden_size_list=[64],
        producer_lanes_list=[64],
        macs_per_cycle_list=[4096],
        memory_bandwidth_bytes_per_cycle_list=[128.0],
        memory_share_list=[1.0],
        top_k_list=[1],
        weight_bits=16,
        activation_bits=16,
        clock_ns=1.0,
    )

    control = report["producer_control_boundary"]
    assert control["decision"] == "softmax_event_guard_synth_ok_under_bound"
    assert control["guard_variant"] == "cq_v1_softmax_event_guard"
    assert control["synthesis_status"] == "ok"
    assert control["reg_bits_est"] == 2634


def test_coupling_report_carries_producer_physical_boundary(tmp_path: Path) -> None:
    boundary = tmp_path / "producer_pnr.json"
    boundary.write_text(
        """
{
  "make_target": "3_3_place_gp",
  "boundary_kind": "physical",
  "diagnosis": {
    "decision": "producer_physical_boundary_not_reached",
    "feasible_max_num_modules": 16,
    "first_nonviable_num_modules": null,
    "recommended_next_step": "Use the largest completed physical point."
  },
  "probe_rows": [
    {
      "num_modules": 8,
      "status": "ok",
      "synthesis": {"status": "ok", "elapsed_seconds": 662.7},
      "metrics_row": {
        "critical_path_ns": "5.66",
        "die_area": "4840000.0",
        "total_power_mw": "0.209",
        "flow_elapsed_seconds": "660.0",
        "stage_elapsed_seconds": "300.0",
        "result_path": "runs/designs/nm8/result.json"
      }
    },
    {
      "num_modules": 16,
      "status": "ok",
      "design_dir": "runs/designs/npu_blocks/npu_fp16_cpp_nm16_producer",
      "synthesis": {"status": "ok", "elapsed_seconds": 822.8},
      "metrics_row": {
        "critical_path_ns": "6.104",
        "die_area": "4840000.0",
        "total_power_mw": "0.254",
        "flow_elapsed_seconds": "819.27",
        "stage_elapsed_seconds": "397.0",
        "result_path": "runs/designs/nm16/result.json"
      }
    }
  ]
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    report = build_coupling_report(
        mode="producer_service",
        rank_ppa_path=None,
        scale_ppa_path=None,
        candidate_merge_ppa_path=None,
        boundary_ppa_path=None,
        producer_control_boundary_path=None,
        producer_physical_boundary_path=boundary,
        sram_metrics_json_path=None,
        vocab_size_list=[256],
        hidden_size_list=[64],
        producer_lanes_list=[64],
        macs_per_cycle_list=[4096],
        memory_bandwidth_bytes_per_cycle_list=[128.0],
        memory_share_list=[1.0],
        top_k_list=[1],
        weight_bits=16,
        activation_bits=16,
        clock_ns=1.0,
    )

    physical = report["producer_physical_boundary"]
    assert physical["decision"] == "producer_physical_boundary_not_reached"
    assert physical["num_modules"] == 16
    assert physical["make_target"] == "3_3_place_gp"
    assert physical["critical_path_ns"] == 6.104
    assert physical["die_area_um2"] == 4840000.0
    assert physical["total_power_mw"] == 0.254

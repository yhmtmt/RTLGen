import json
import subprocess
import sys
from pathlib import Path


def _write_config(
    config_path: Path,
    *,
    equivalence_hash: bool | None = None,
    softmax_pipeline_stages: int | None = None,
    softmax_internal_pipeline_stages: int | None = None,
    softmax_impl: str | None = None,
    mac_accum_bits: int | None = None,
    softmax_accum_bits: int | None = None,
    softmax_score_bits: int | None = None,
    softmax_weight_bits: int | None = None,
    reciprocal_bits: int | None = None,
    value_bits: int | None = None,
    softmax_input_frac_bits: int | None = None,
    softmax_reciprocal_lut_bucket_shift: int | None = None,
    softmax_reciprocal_div_cycles: int | None = None,
) -> None:
    comp = {
        "streams": 2,
        "array_m": 2,
        "array_n": 2,
        "k_unroll": 1,
        "softmax_row_elems": 4,
        "softmax_accum_bits": 16,
        "reciprocal_bits": 10,
        "value_bits": 6,
        "value_lanes": 4,
        "partials": 4,
        "partials_per_cycle": 2,
        "stream_buffer_bits": 128,
    }
    if equivalence_hash is not None:
        comp["equivalence_hash"] = equivalence_hash
    if softmax_pipeline_stages is not None:
        comp["softmax_pipeline_stages"] = softmax_pipeline_stages
    if softmax_internal_pipeline_stages is not None:
        comp["softmax_internal_pipeline_stages"] = softmax_internal_pipeline_stages
    if softmax_impl is not None:
        comp["softmax_impl"] = softmax_impl
    if mac_accum_bits is not None:
        comp["mac_accum_bits"] = mac_accum_bits
    if softmax_accum_bits is not None:
        comp["softmax_accum_bits"] = softmax_accum_bits
    if softmax_score_bits is not None:
        comp["softmax_score_bits"] = softmax_score_bits
    if softmax_weight_bits is not None:
        comp["softmax_weight_bits"] = softmax_weight_bits
    if reciprocal_bits is not None:
        comp["reciprocal_bits"] = reciprocal_bits
    if value_bits is not None:
        comp["value_bits"] = value_bits
    if softmax_input_frac_bits is not None:
        comp["softmax_input_frac_bits"] = softmax_input_frac_bits
    if softmax_reciprocal_lut_bucket_shift is not None:
        comp["softmax_reciprocal_lut_bucket_shift"] = softmax_reciprocal_lut_bucket_shift
    if softmax_reciprocal_div_cycles is not None:
        comp["softmax_reciprocal_div_cycles"] = softmax_reciprocal_div_cycles
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "top_name": "attention_dual_stream_composed_smoke",
                "attention_dual_stream_composed": comp,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _generate_and_check(
    design_dir: Path,
    config_path: Path,
    *,
    run_composed_guard: bool = True,
) -> str:
    subprocess.run(
        [
            sys.executable,
            "npu/rtlgen/gen_attention_dual_stream_composed.py",
            "--config",
            str(config_path),
            "--out",
            str(design_dir / "verilog"),
        ],
        check=True,
    )
    if run_composed_guard:
        subprocess.run(
            [
                sys.executable,
                "npu/eval/check_attention_dual_stream_composed_guard.py",
                "--design-dir",
                str(design_dir),
            ],
            check=True,
        )
    subprocess.run(
        [
            "/oss-cad-suite/bin/iverilog",
            "-g2012",
            "-o",
            str(design_dir / "simv"),
            str(design_dir / "verilog" / "top.v"),
        ],
        check=True,
    )
    return (design_dir / "verilog" / "top.v").read_text(encoding="utf-8")


def test_attention_dual_stream_composed_generator_ppa_guard_and_syntax(tmp_path: Path) -> None:
    design_dir = tmp_path / "attention_dual_stream_composed_smoke"
    config_path = design_dir / "config.json"
    _write_config(config_path)
    top_text = _generate_and_check(design_dir, config_path, run_composed_guard=False)

    manifest = json.loads((design_dir / "verilog" / "attention_dual_stream_composed_manifest.json").read_text())
    assert manifest["streams"] == 2
    assert manifest["total_macs"] == 8
    assert manifest["softmax_row_elems"] == 4
    assert manifest["value_lanes_per_stream"] == 4
    assert manifest["equivalence_hash"] is False
    assert manifest["softmax_impl"] == "exact_div"
    assert manifest["softmax_pipeline_stages"] == 0
    assert manifest["softmax_internal_pipeline_stages"] == 0
    assert manifest["softmax_latency_stages"] == 1
    assert manifest["value_alignment_delay_stages"] == 0
    assert "u_softmax" in top_text
    assert "u_value_stream_0" in top_text
    assert "u_value_stream_1" in top_text
    assert "softmax_weights_out" in top_text
    assert "value_accum_0_out" in top_text
    assert "score_mix_0_out" in top_text
    assert "result_hash" not in top_text
    assert "softmax_weight_hash" not in top_text
    assert "softmax_scores_pipe_0" not in top_text


def test_attention_dual_stream_composed_generator_equivalence_hash_mode(tmp_path: Path) -> None:
    design_dir = tmp_path / "attention_dual_stream_composed_equiv"
    config_path = design_dir / "config.json"
    _write_config(config_path, equivalence_hash=True)
    top_text = _generate_and_check(design_dir, config_path, run_composed_guard=False)

    manifest = json.loads((design_dir / "verilog" / "attention_dual_stream_composed_manifest.json").read_text())
    assert manifest["equivalence_hash"] is True
    assert "result_hash <=" in top_text
    assert "softmax_weight_hash" in top_text
    assert "value_hash_0" in top_text
    assert "compute_fold" in top_text
    assert "softmax_weights_out" not in top_text


def test_attention_dual_stream_composed_generator_softmax_pipeline(tmp_path: Path) -> None:
    design_dir = tmp_path / "attention_dual_stream_composed_pipeline"
    config_path = design_dir / "config.json"
    _write_config(config_path, softmax_pipeline_stages=1)
    top_text = _generate_and_check(design_dir, config_path, run_composed_guard=False)

    manifest = json.loads((design_dir / "verilog" / "attention_dual_stream_composed_manifest.json").read_text())
    assert manifest["equivalence_hash"] is False
    assert manifest["softmax_pipeline_stages"] == 1
    assert manifest["softmax_internal_pipeline_stages"] == 0
    assert manifest["softmax_latency_stages"] == 1
    assert manifest["value_alignment_delay_stages"] == 2
    assert "reg [31:0] softmax_scores_pipe_0" in top_text
    assert ".scores(softmax_scores_pipe_0)" in top_text
    assert "stream_buf_0_pipe_1" in top_text
    assert "score_mix_1_pipe_1" in top_text
    assert ".stream_data(stream_buf_0_pipe_1)" in top_text
    assert ".score_mix(score_mix_1_pipe_1)" in top_text


def test_attention_dual_stream_composed_generator_softmax_split_pipeline(tmp_path: Path) -> None:
    design_dir = tmp_path / "attention_dual_stream_composed_split"
    config_path = design_dir / "config.json"
    _write_config(config_path, softmax_pipeline_stages=1, softmax_internal_pipeline_stages=1)
    top_text = _generate_and_check(design_dir, config_path, run_composed_guard=False)

    manifest = json.loads((design_dir / "verilog" / "attention_dual_stream_composed_manifest.json").read_text())
    assert manifest["softmax_impl"] == "exact_div"
    assert manifest["softmax_pipeline_stages"] == 1
    assert manifest["softmax_internal_pipeline_stages"] == 1
    assert manifest["softmax_latency_stages"] == 2
    assert manifest["value_alignment_delay_stages"] == 3
    assert "exp_weight_q" in top_text
    assert "sum_weight_q" in top_text
    assert ".stream_data(stream_buf_0_pipe_2)" in top_text
    assert ".score_mix(score_mix_1_pipe_2)" in top_text
    assert "lane_out = numer / sum_weight_q" in top_text


def test_attention_dual_stream_composed_generator_softmax_divider_operand_pipeline(tmp_path: Path) -> None:
    design_dir = tmp_path / "attention_dual_stream_composed_split2"
    config_path = design_dir / "config.json"
    _write_config(config_path, softmax_pipeline_stages=1, softmax_internal_pipeline_stages=2)
    top_text = _generate_and_check(design_dir, config_path, run_composed_guard=False)

    manifest = json.loads((design_dir / "verilog" / "attention_dual_stream_composed_manifest.json").read_text())
    assert manifest["softmax_impl"] == "exact_div"
    assert manifest["softmax_pipeline_stages"] == 1
    assert manifest["softmax_internal_pipeline_stages"] == 2
    assert manifest["softmax_latency_stages"] == 3
    assert manifest["value_alignment_delay_stages"] == 4
    assert "numer_q" in top_text
    assert "sum_weight_qq" in top_text
    assert "lane_out = numer_q[i] / sum_weight_qq" in top_text
    assert ".stream_data(stream_buf_0_pipe_3)" in top_text
    assert ".score_mix(score_mix_1_pipe_3)" in top_text


def test_attention_dual_stream_composed_generator_softmax_pow2sum_replacement(tmp_path: Path) -> None:
    design_dir = tmp_path / "attention_dual_stream_composed_pow2sum"
    config_path = design_dir / "config.json"
    _write_config(config_path, softmax_pipeline_stages=1, softmax_impl="pow2sum")
    top_text = _generate_and_check(design_dir, config_path)

    manifest = json.loads((design_dir / "verilog" / "attention_dual_stream_composed_manifest.json").read_text())
    assert manifest["softmax_impl"] == "pow2sum"
    assert manifest["softmax_pipeline_stages"] == 1
    assert manifest["softmax_internal_pipeline_stages"] == 0
    assert manifest["softmax_latency_stages"] == 1
    assert manifest["value_alignment_delay_stages"] == 2
    assert "denom_shift" in top_text
    assert "lane_scaled" in top_text
    assert "/ sum_weight" not in top_text
    assert ".stream_data(stream_buf_0_pipe_1)" in top_text


def test_attention_dual_stream_composed_generator_softmax_recip_lut_replacement(tmp_path: Path) -> None:
    design_dir = tmp_path / "attention_dual_stream_composed_recip_lut"
    config_path = design_dir / "config.json"
    _write_config(config_path, softmax_pipeline_stages=1, softmax_impl="recip_lut")
    top_text = _generate_and_check(design_dir, config_path)

    manifest = json.loads((design_dir / "verilog" / "attention_dual_stream_composed_manifest.json").read_text())
    assert manifest["softmax_impl"] == "recip_lut"
    assert manifest["softmax_pipeline_stages"] == 1
    assert manifest["softmax_internal_pipeline_stages"] == 0
    assert manifest["softmax_latency_stages"] == 1
    assert manifest["value_alignment_delay_stages"] == 2
    assert "function [RECIPROCAL_WIDTH-1:0] reciprocal_lut" in top_text
    assert "reciprocal_q = reciprocal_lut(sum_weight)" in top_text
    assert "/ sum_weight" not in top_text
    assert "/ sum_weight_q" not in top_text
    assert "denom_shift" not in top_text
    assert ".stream_data(stream_buf_0_pipe_1)" in top_text


def test_attention_dual_stream_composed_generator_q12_pwl_softmax(tmp_path: Path) -> None:
    design_dir = tmp_path / "attention_dual_stream_composed_q12_pwl"
    config_path = design_dir / "config.json"
    _write_config(
        config_path,
        softmax_pipeline_stages=1,
        softmax_impl="pwl_recip_lut",
        softmax_score_bits=12,
        softmax_weight_bits=12,
        softmax_input_frac_bits=8,
        softmax_reciprocal_lut_bucket_shift=8,
    )
    top_text = _generate_and_check(design_dir, config_path)

    manifest = json.loads((design_dir / "verilog" / "attention_dual_stream_composed_manifest.json").read_text())
    assert manifest["softmax_impl"] == "pwl_recip_lut"
    assert manifest["softmax_score_bits"] == 12
    assert manifest["softmax_weight_bits"] == 12
    assert manifest["softmax_input_frac_bits"] == 8
    assert manifest["softmax_reciprocal_lut_bucket_shift"] == 8
    assert "attention_softmax_weight_q12_pwl_recip_like" in top_text
    assert "function [ACCUM_BITS-1:0] pwl_weight" in top_text
    assert "function [RECIPROCAL_WIDTH-1:0] reciprocal_lut" in top_text
    assert "wire [47:0] softmax_weights" in top_text
    assert "wire [11:0] score_lane_00" in top_text
    assert "wire [11:0] weight_00" in top_text


def test_attention_dual_stream_composed_generator_q20_pwl_v8_softmax(tmp_path: Path) -> None:
    design_dir = tmp_path / "attention_dual_stream_composed_q20_pwl_v8"
    config_path = design_dir / "config.json"
    _write_config(
        config_path,
        softmax_pipeline_stages=1,
        softmax_impl="pwl_recip_lut",
        mac_accum_bits=24,
        softmax_accum_bits=32,
        softmax_score_bits=20,
        softmax_weight_bits=20,
        reciprocal_bits=20,
        value_bits=8,
        softmax_input_frac_bits=8,
        softmax_reciprocal_lut_bucket_shift=8,
    )
    top_text = _generate_and_check(design_dir, config_path)

    manifest = json.loads((design_dir / "verilog" / "attention_dual_stream_composed_manifest.json").read_text())
    assert manifest["softmax_impl"] == "pwl_recip_lut"
    assert manifest["mac_accum_bits"] == 24
    assert manifest["softmax_score_bits"] == 20
    assert manifest["softmax_weight_bits"] == 20
    assert manifest["reciprocal_bits"] == 20
    assert manifest["value_bits"] == 8
    assert manifest["softmax_reciprocal_lut_bucket_shift"] == 8
    assert "module attention_softmax_weight_q12_pwl_recip_like" in top_text
    assert "localparam integer RECIP_BUCKET_SHIFT = 8;" in top_text
    assert "wire [79:0] softmax_weights" in top_text
    assert "wire [19:0] score_lane_00" in top_text
    assert "wire [19:0] weight_00" in top_text
    assert "module attention_full_value_stream_q8v8_p8_ppc2" in top_text


def test_attention_dual_stream_composed_generator_q24_pwl_compact_recip_v8_softmax(
    tmp_path: Path,
) -> None:
    design_dir = tmp_path / "attention_dual_stream_composed_q24_pwl_div_v8"
    config_path = design_dir / "config.json"
    _write_config(
        config_path,
        softmax_pipeline_stages=1,
        softmax_impl="pwl_recip_div",
        mac_accum_bits=24,
        softmax_accum_bits=40,
        softmax_score_bits=24,
        softmax_weight_bits=24,
        reciprocal_bits=24,
        value_bits=8,
        softmax_input_frac_bits=8,
        softmax_reciprocal_lut_bucket_shift=8,
    )
    top_text = _generate_and_check(design_dir, config_path)

    manifest = json.loads((design_dir / "verilog" / "attention_dual_stream_composed_manifest.json").read_text())
    assert manifest["softmax_impl"] == "pwl_recip_div"
    assert manifest["mac_accum_bits"] == 24
    assert manifest["softmax_accum_bits"] == 40
    assert manifest["softmax_score_bits"] == 24
    assert manifest["softmax_weight_bits"] == 24
    assert manifest["reciprocal_bits"] == 24
    assert manifest["value_bits"] == 8
    assert manifest["softmax_reciprocal_lut_bucket_shift"] == 8
    assert "module attention_softmax_weight_q24_pwl_recip_div_like" in top_text
    assert "localparam [RECIPROCAL_WIDTH-1:0] RECIPROCAL_NUMERATOR = 48'd281474959933440;" in top_text
    assert "reciprocal_numer = RECIPROCAL_NUMERATOR + (reciprocal_denominator >> 1);" in top_text
    assert "reciprocal_q = reciprocal_numer / reciprocal_denominator;" in top_text
    assert "function [RECIPROCAL_WIDTH-1:0] reciprocal_lut" not in top_text
    assert "wire [95:0] softmax_weights" in top_text
    assert "wire [23:0] score_lane_00" in top_text
    assert "wire [23:0] weight_00" in top_text
    assert "module attention_full_value_stream_q8v8_p8_ppc2" in top_text


def test_attention_dual_stream_composed_generator_q24_pwl_seqdiv_v8_softmax(
    tmp_path: Path,
) -> None:
    design_dir = tmp_path / "attention_dual_stream_composed_q24_pwl_seqdiv_v8"
    config_path = design_dir / "config.json"
    _write_config(
        config_path,
        softmax_pipeline_stages=1,
        softmax_impl="pwl_recip_seqdiv",
        mac_accum_bits=24,
        softmax_accum_bits=40,
        softmax_score_bits=24,
        softmax_weight_bits=24,
        reciprocal_bits=24,
        value_bits=8,
        softmax_input_frac_bits=8,
        softmax_reciprocal_lut_bucket_shift=8,
        softmax_reciprocal_div_cycles=48,
    )
    top_text = _generate_and_check(design_dir, config_path)

    manifest = json.loads((design_dir / "verilog" / "attention_dual_stream_composed_manifest.json").read_text())
    assert manifest["softmax_impl"] == "pwl_recip_seqdiv"
    assert manifest["softmax_score_bits"] == 24
    assert manifest["softmax_weight_bits"] == 24
    assert manifest["reciprocal_bits"] == 24
    assert manifest["softmax_reciprocal_div_cycles"] == 48
    assert manifest["softmax_latency_stages"] == 48
    assert manifest["value_alignment_delay_stages"] == 49
    assert "module attention_softmax_weight_q24_pwl_recip_seqdiv_like" in top_text
    for token in ("div_busy", "div_bit", "div_quotient", "div_remainder", "softmax_valid"):
        assert token in top_text
    assert ".start(softmax_start_pipe_0)" in top_text
    assert ".softmax_valid(softmax_valid)" in top_text
    assert "done <= softmax_valid" in top_text
    assert "reciprocal_q = reciprocal_numer / reciprocal_denominator" not in top_text
    assert "/ reciprocal_denominator" not in top_text
    assert "function [RECIPROCAL_WIDTH-1:0] reciprocal_lut" not in top_text


def test_attention_dual_stream_composed_generator_score32_exact_softmax(tmp_path: Path) -> None:
    design_dir = tmp_path / "attention_dual_stream_composed_score32"
    config_path = design_dir / "config.json"
    _write_config(
        config_path,
        softmax_pipeline_stages=1,
        softmax_impl="exact_div",
        mac_accum_bits=32,
        softmax_accum_bits=40,
        softmax_score_bits=32,
        softmax_weight_bits=16,
        softmax_internal_pipeline_stages=1,
    )
    top_text = _generate_and_check(design_dir, config_path, run_composed_guard=False)

    manifest = json.loads((design_dir / "verilog" / "attention_dual_stream_composed_manifest.json").read_text())
    assert manifest["mac_accum_bits"] == 32
    assert manifest["mac_module"] == "int8_mac_s8s8_acc32"
    assert manifest["softmax_score_bits"] == 32
    assert manifest["softmax_weight_bits"] == 16
    assert manifest["score_mix_bits"] == 32
    assert manifest["score_bits_source"] == "mac_acc32_native"
    assert "module int8_mac_s8s8_acc32" in top_text
    assert "module attention_softmax_weight_score32_w16_exact_div_like" in top_text
    assert "wire signed [31:0] mac_c_0000" in top_text
    assert "wire signed [31:0] mac_r_0000" in top_text
    assert "wire [31:0] score_lane_00" in top_text
    assert "wire [63:0] softmax_weights" in top_text
    assert "input  wire [31:0] score_mix" in top_text


def test_attention_dual_stream_composed_generator_score24_w16_exact_softmax(tmp_path: Path) -> None:
    design_dir = tmp_path / "attention_dual_stream_composed_score24_w16"
    config_path = design_dir / "config.json"
    _write_config(
        config_path,
        softmax_pipeline_stages=1,
        softmax_impl="exact_div",
        mac_accum_bits=24,
        softmax_accum_bits=32,
        softmax_score_bits=24,
        softmax_weight_bits=16,
        value_bits=8,
        softmax_internal_pipeline_stages=1,
    )
    top_text = _generate_and_check(design_dir, config_path, run_composed_guard=False)

    manifest = json.loads((design_dir / "verilog" / "attention_dual_stream_composed_manifest.json").read_text())
    assert manifest["mac_accum_bits"] == 24
    assert manifest["mac_module"] == "int8_mac_s8s8_acc24"
    assert manifest["softmax_score_bits"] == 24
    assert manifest["softmax_weight_bits"] == 16
    assert manifest["value_bits"] == 8
    assert manifest["score_mix_bits"] == 24
    assert manifest["score_bits_source"] == "mac_acc24_native"
    assert "module int8_mac_s8s8_acc24" in top_text
    assert "module attention_softmax_weight_score24_w16_exact_div_like" in top_text
    assert "module attention_full_value_stream_q8v8_p8_ppc2" in top_text
    assert "wire signed [23:0] mac_c_0000" in top_text
    assert "wire [23:0] score_lane_00" in top_text
    assert "wire [63:0] softmax_weights" in top_text
    assert "input  wire [23:0] score_mix" in top_text


def test_attention_dual_stream_composed_generator_score32_softmax_requires_acc32(tmp_path: Path) -> None:
    design_dir = tmp_path / "attention_dual_stream_composed_score32_requires_acc32"
    config_path = design_dir / "config.json"
    _write_config(config_path, softmax_score_bits=32, softmax_weight_bits=16)
    result = subprocess.run(
        [
            sys.executable,
            "npu/rtlgen/gen_attention_dual_stream_composed.py",
            "--config",
            str(config_path),
            "--out",
            str(design_dir / "verilog"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "requires mac_accum_bits=32" in (result.stderr + result.stdout)


def test_attention_dual_stream_composed_generator_score32_softmax(tmp_path: Path) -> None:
    design_dir = tmp_path / "attention_dual_stream_composed_score32"
    config_path = design_dir / "config.json"
    _write_config(
        config_path,
        softmax_pipeline_stages=1,
        softmax_impl="pwl_recip_lut",
        mac_accum_bits=32,
        softmax_accum_bits=40,
        softmax_score_bits=32,
        softmax_weight_bits=16,
        softmax_input_frac_bits=8,
        softmax_reciprocal_lut_bucket_shift=8,
    )
    top_text = _generate_and_check(design_dir, config_path, run_composed_guard=False)

    manifest = json.loads((design_dir / "verilog" / "attention_dual_stream_composed_manifest.json").read_text())
    assert manifest["softmax_score_bits"] == 32
    assert manifest["softmax_weight_bits"] == 16
    assert manifest["score_mix_bits"] == 32
    assert manifest["score_bits_source"] == "mac_acc32_native"
    assert manifest["mac_module"] == "int8_mac_s8s8_acc32"
    assert manifest["value_bits"] == 6
    assert "wire [63:0] softmax_weights" in top_text
    assert "wire [31:0] score_lane_00" in top_text
    assert "wire [31:0] score_mix_0" in top_text
    assert "wire [31:0] score_mix_1" in top_text
    assert "reg [31:0] score_mix_0_pipe_0" in top_text
    assert "reg [31:0] score_mix_1_pipe_0" in top_text
    assert "output reg  [31:0] score_mix_0_out" in top_text
    assert "output reg  [31:0] score_mix_1_out" in top_text


def test_attention_dual_stream_composed_generator_score32_v8_exact_softmax(tmp_path: Path) -> None:
    design_dir = tmp_path / "attention_dual_stream_composed_score32_v8"
    config_path = design_dir / "config.json"
    _write_config(
        config_path,
        softmax_pipeline_stages=1,
        softmax_impl="exact_div",
        mac_accum_bits=32,
        softmax_accum_bits=40,
        softmax_score_bits=32,
        softmax_weight_bits=16,
        softmax_internal_pipeline_stages=1,
    )
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    cfg["attention_dual_stream_composed"]["value_bits"] = 8
    config_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    top_text = _generate_and_check(design_dir, config_path)

    manifest = json.loads((design_dir / "verilog" / "attention_dual_stream_composed_manifest.json").read_text())
    assert manifest["mac_module"] == "int8_mac_s8s8_acc32"
    assert manifest["value_bits"] == 8
    assert "module attention_full_value_stream_q8v8_p8_ppc2" in top_text
    assert "wire signed [7:0] value_00" in top_text


def test_attention_dual_stream_composed_generator_score32_v8_recip_lut_q16_softmax(
    tmp_path: Path,
) -> None:
    design_dir = tmp_path / "attention_dual_stream_composed_score32_v8_recip_lut_q16"
    config_path = design_dir / "config.json"
    _write_config(
        config_path,
        softmax_pipeline_stages=1,
        softmax_impl="recip_lut",
        mac_accum_bits=32,
        softmax_accum_bits=40,
        softmax_score_bits=32,
        softmax_weight_bits=16,
        reciprocal_bits=16,
    )
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    cfg["attention_dual_stream_composed"]["value_bits"] = 8
    config_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    top_text = _generate_and_check(design_dir, config_path)

    manifest = json.loads((design_dir / "verilog" / "attention_dual_stream_composed_manifest.json").read_text())
    assert manifest["mac_module"] == "int8_mac_s8s8_acc32"
    assert manifest["softmax_impl"] == "recip_lut"
    assert manifest["softmax_score_bits"] == 32
    assert manifest["softmax_weight_bits"] == 16
    assert manifest["reciprocal_bits"] == 16
    assert manifest["value_bits"] == 8
    assert manifest["softmax_latency_stages"] == 1
    assert manifest["value_alignment_delay_stages"] == 2
    assert "module attention_softmax_weight_score32_w16_recip_lut_q16_like" in top_text
    assert "localparam integer RECIPROCAL_BITS = 16" in top_text
    assert "localparam integer RECIPROCAL_WIDTH = 32" in top_text
    assert "function [RECIPROCAL_WIDTH-1:0] reciprocal_lut" in top_text
    assert "reciprocal_q = reciprocal_lut(sum_weight)" in top_text
    assert "/ sum_weight" not in top_text
    assert "/ sum_weight_q" not in top_text
    assert "wire [63:0] softmax_weights" in top_text
    assert "module attention_full_value_stream_q8v8_p8_ppc2" in top_text


def test_attention_dual_stream_composed_generator_score32_v8_exact_softmax_divider_operand_pipeline(
    tmp_path: Path,
) -> None:
    design_dir = tmp_path / "attention_dual_stream_composed_score32_v8_split2"
    config_path = design_dir / "config.json"
    _write_config(
        config_path,
        softmax_pipeline_stages=1,
        softmax_impl="exact_div",
        mac_accum_bits=32,
        softmax_accum_bits=40,
        softmax_score_bits=32,
        softmax_weight_bits=16,
        softmax_internal_pipeline_stages=2,
    )
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    cfg["attention_dual_stream_composed"]["value_bits"] = 8
    config_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    top_text = _generate_and_check(design_dir, config_path)

    manifest = json.loads((design_dir / "verilog" / "attention_dual_stream_composed_manifest.json").read_text())
    assert manifest["mac_module"] == "int8_mac_s8s8_acc32"
    assert manifest["softmax_score_bits"] == 32
    assert manifest["softmax_weight_bits"] == 16
    assert manifest["value_bits"] == 8
    assert manifest["softmax_internal_pipeline_stages"] == 2
    assert manifest["softmax_latency_stages"] == 3
    assert manifest["value_alignment_delay_stages"] == 4
    assert "module attention_full_value_stream_q8v8_p8_ppc2" in top_text
    assert "localparam integer PRODUCT_BITS = 56" in top_text
    assert "reg [PRODUCT_BITS-1:0] numer_q [0:ROW_ELEMS-1]" in top_text
    assert "reg [ACCUM_BITS-1:0] sum_weight_qq" in top_text
    assert "lane_out = numer_q[i] / sum_weight_qq" in top_text
    assert ".stream_data(stream_buf_0_pipe_3)" in top_text

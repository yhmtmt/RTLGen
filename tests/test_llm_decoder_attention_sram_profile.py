from npu.eval.measure_llm_decoder_attention_sram_profile import build_buffer_specs


def test_attention_sram_profile_default_logical_quantities() -> None:
    buffers = build_buffer_specs(
        tile_tokens=512,
        hidden_size=4096,
        attention_heads=32,
        kv_heads=4,
        score_bits=16,
        softmax_weight_bits=16,
        kv_bits=8,
        accumulator_bits=32,
        output_bits=16,
        max_bank_width_bits=256,
    )

    by_name = {buffer.name: buffer for buffer in buffers}

    assert by_name["score_tile_buffer"].logical_bytes == 512 * 32 * 2
    assert by_name["softmax_weight_buffer"].logical_bytes == 512 * 32 * 2
    assert by_name["kv_tile_read_buffer"].logical_bytes == 2 * 512 * 4 * 128
    assert by_name["partial_value_buffer"].logical_bytes == 4096 * 4
    assert by_name["result_writeback_buffer"].logical_bytes == 4096 * 2
    assert by_name["softmax_stats_buffer"].logical_bytes == 32 * 2 * 4


def test_attention_sram_profile_shapes_are_cacti_friendly() -> None:
    buffers = build_buffer_specs(
        tile_tokens=512,
        hidden_size=4096,
        attention_heads=32,
        kv_heads=4,
        score_bits=16,
        softmax_weight_bits=16,
        kv_bits=8,
        accumulator_bits=32,
        output_bits=16,
        max_bank_width_bits=256,
    )

    for buffer in buffers:
        assert buffer.width_bits % 8 == 0
        assert buffer.depth > 0
        assert buffer.depth & (buffer.depth - 1) == 0
        assert buffer.banks >= 1

    total_logical = sum(buffer.logical_bytes for buffer in buffers)
    total_allocated = sum(buffer.banks * buffer.depth * buffer.width_bits // 8 for buffer in buffers)
    assert total_allocated >= total_logical
    assert total_allocated / total_logical < 1.1

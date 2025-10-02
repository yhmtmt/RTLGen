# Configuration File

You can specify multiplier, adder, and operand parameters in the configuration files.

## Adder Configuration

```json
{
    "operand": {
        "bit_width": 8,
        "signed": true
    },
    "adder": {
        "module_name": "adder_koggestone_8s",
        "cpa_structure": "KoggeStone",
        "pipeline_depth": 1
    }
}
```

Specify both "operand" and "adder". The "operand" section configures the bit width and signedness of the integer input. In the "adder" section, you can select the `cpa_structure` from the following four types:

- `Ripple`: Ripple Carry Adder (simple, area-efficient, but slow for large bit-widths)
- `KoggeStone`: Kogge-Stone Adder (parallel prefix, very fast, higher area)
- `BrentKung`: Brent-Kung Adder (parallel prefix, balanced delay and area)
- `Sklansky`: Sklansky Adder (parallel prefix, fast, but can have high fanout)

Pipelining is not yet implemented; only a single stage is supported.

## Multiplier Configuration

```json
{
    "operand": {
        "bit_width": 16,
        "signed": true
    },
    "multiplier": {
        "module_name": "booth_multiplier32s",
        "ppg_algorithm": "Booth4",
        "compressor_structure": "AdderTree",
        "cpa_structure": "KoggeStone",
        "pipeline_depth": 1
    }
}
```

Currently, `compressor_structure` and `pipeline_depth` are fixed to `AdderTree` and `1`. The `AdderTree` is optimized using ILP as described in [UFO-MAC: A Unified Framework for Optimization of High-Performance Multipliers and Multiply-Accumulators](https://arxiv.org/abs/2408.06935). For more details, see [Compressor Tree Memo](doc/compressor_tree/memo_about_compressor_tree.md).

The generator supports two partial product generation (PPG) algorithms: `Normal` and `Booth4`:

- **Normal**: Conventional approach using an array of AND gates to generate partial products.
- **Booth4**: Radix-4 modified Booth algorithm, based on ["High Performance Low-Power Left-to-Right Array Multiplier Design"](https://ieeexplore.ieee.org/document/1388192).

Specify your desired algorithm in the `ppg_algorithm` field. For sign extension, a fast computation technique is used, as described in ["Minimizing Energy Dissipation in High-Speed Multipliers"](https://ieeexplore.ieee.org/document/621285). The `bit_width` should be at least 4.

## Multiplier Configuration for Yosys

```json
{
    "operand": {
        "bit_width": 16,
        "signed": true
    },
    "multiplier_yosys": {
        "module_name": "yosys_multiplier16s",
        "booth_type": "Booth"
    }
}
```

If you have Yosys installed, you can use the multiplier generator in Yosys. Yosys can generate Booth multipliers. Specify `"Booth"` or `"LowpowerBooth"` in the `booth_type` field. Note: `"LowpowerBooth"` cannot be used with unsigned integers.

# RTLGen

RTLGen is a Verilog generator driven by a JSON configuration file. It can emit a mix of arithmetic and activation blocks:
- Integer arithmetic: multipliers (normal/Booth), adders (multiple CPA styles), and constant-multiplier variants (MCM/CMVM).
- Floating point: adders/multipliers/FMA via FloPoCo integration.
- Activations: integer ReLU/ReLU6/leaky ReLU and user-defined symmetric PWL functions; FP path supports ReLU and leaky ReLU (FP PWL is coarse/experimental).

## Building the Project

Dependencies:
- CMake, C++17 compiler
- Google Test (tests/CTests)
- OR-Tools (bundled path configured in CMake)
- FloPoCo (built as an ExternalProject; requires GMP/MPFR/MPFI/LAPACK/Sollya) and PAGSuite submodule
- Yosys + GHDL plugin (for VHDL→Verilog on FloPoCo outputs)

The devcontainer (`.devcontainer/Dockerfile`) provisions these. See [development.md](development.md) for environment details. To build:

```sh
mkdir build
cd build
cmake ..
cmake --build .
```

## Running the Generator

To run the generator, create a JSON configuration file as shown in the `examples/` directory. Supported configuration options are described in [about_config.md](examples/about_config.md). Once your configuration file is ready, run:

```
rtlgen <JSON configuration file>
```

This command generates a Verilog module for your circuit according to the configuration file. The generated module will be placed in the current working directory.

## Notes and References
- Multiplier comparison (Booth vs. normal PPG) with OpenROAD results: see [doc/booth4_vs_normal/booth_vs_normal_multiplier_comparison.md](doc/booth4_vs_normal/booth_vs_normal_multiplier_comparison.md).
- Yosys Booth vs ILP Booth comparison with normalized PPA plots: see [doc/yosys_vs_ilp_booth.md](doc/yosys_vs_ilp_booth.md).
- Constant-multiplier algorithms (MCM/CMVM) and CLIs: see [doc/constant_multiplication.md](doc/constant_multiplication.md).
- Evaluation artifacts (configs, generated Verilog, sweep metrics) live under [runs/](runs/README.md); add configs there to queue new evaluations.

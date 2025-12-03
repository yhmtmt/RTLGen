# RTLGen

RTLGen is a Verilog generator driven by a JSON configuration file. It can emit a mix of arithmetic and activation blocks:
- Integer arithmetic: multipliers (normal/Booth), adders (multiple CPA styles), and constant-multiplier variants (MCM/CMVM).
- Floating point: adders/multipliers/FMA via FloPoCo integration.
- Activations: integer ReLU/ReLU6/leaky ReLU and user-defined symmetric PWL functions; FP path supports ReLU and leaky ReLU (FP PWL is coarse/experimental).

## Building the Project

To build the project, you need CMake and a C++ compiler. You will also need the Google Test and OR-Tools libraries. The development environment is fully defined in the Dockerfile located in `.devcontainer`, making it easy to use Visual Studio Code with a devcontainer for both development and evaluation of generated circuits using OpenROAD. See [development.md](development.md) for details.

Once you have the dependencies installed, build the project with:

```
mkdir build
cd build
cmake ..
make
make install
```

## Running the Generator

To run the generator, create a JSON configuration file as shown in the `examples/` directory. Supported configuration options are described in [about_config.md](examples/about_config.md). Once your configuration file is ready, run:

```
rtlgen <JSON configuration file>
```

This command generates a Verilog module for your circuit according to the configuration file. The generated module will be placed in the current working directory.

## Notes and References
- Multiplier comparison (Booth vs. normal PPG) with OpenROAD results: see [doc/booth4_vs_normal/booth_vs_normal_multiplier_comparison.md](doc/booth4_vs_normal/booth_vs_normal_multiplier_comparison.md).
- Constant-multiplier algorithms (MCM/CMVM) and CLIs: see [doc/constant_multiplication.md](doc/constant_multiplication.md).

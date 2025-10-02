# RTLGen

RTLGen is a Verilog generator that takes a JSON configuration file as input and produces a Verilog module with user-specified parameters. The current version of this tool primarily supports multiplier generation.

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

## Booth vs. Normal Multiplier Comparison

A detailed comparison between the modified Booth algorithm and the normal partial product generator is available in [booth4_vs_normal/booth_vs_normal_multiplier_comparison.md](doc/booth4_vs_normal/booth_vs_normal_multiplier_comparison.md). This document provides an in-depth analysis of the performance and area of both multiplier types, based on evaluations using OpenROAD with the Nangate45 PDK.

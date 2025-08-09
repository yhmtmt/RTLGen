# RTLGen

This project is a Verilog multiplier generator. It takes a JSON configuration file as input and generates a Verilog module for a multiplier with the specified parameters.

## Building the Project

To build the project, you will need to have CMake and a C++ compiler installed. You will also need to have the Google Test and OR-Tools libraries installed.

Once you have the dependencies installed, you can build the project with the following commands:

```
mkdir build
cd build
cmake ..
make
```

## Running the Generator

To run the generator, you will need to create a JSON configuration file. The configuration file should have the following format:

```json
{
  "operand": {
    "bit_width": 8,
    "signed": true
  },
  "multiplier": {
    "module_name": "my_multiplier",
    "ppg_algorithm": "Booth4",
    "compressor_structure": "CSATree",
    "pipeline_depth": 2
  }
}
```

Once you have created the configuration file, you can run the generator with the following command:

```
./bin/mult-gen <config.json>
```

This will generate a Verilog module for a multiplier with the specified parameters. The generated module will be placed in the `build` directory.

## Running the Tests

To run the tests, you can use the following command:

```
ctest
```

## Development Environment (Dev Container)

This project supports development inside a dev container, which provides a consistent Ubuntu-based environment with all necessary dependencies pre-installed. The dev container is configured for use with Visual Studio Code and Docker.

### GPU Support

If you require GPU acceleration (for example, for EDA tools or simulations), you must add the `--gpus` option to the `runArgs` in `.devcontainer/devcontainer.json`. This enables Docker to pass through GPU resources to the container.

### X11 Forwarding and ORFS

Some design flows (such as those using `/orfs/flow`) require graphical applications. To enable X11 forwarding from the container to your host, you must run the following command on your host computer before starting the container:

```
xhost + local:
```

This allows the container to connect to your host's X server for GUI applications. Without this, graphical tools inside the container (such as those in `/orfs`) will not function.

## Design Evaluation Script

The `eval_design.py` script automates the process of preparing, running, and evaluating the generated Verilog designs. It handles configuration file generation, moves design files to the appropriate platform directories, executes the flow (such as invoking `make` in `/orfs/flow`), and extracts results. Make sure to run this script inside the dev container for correct environment setup and dependency resolution.

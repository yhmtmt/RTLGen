# Verilog Multiplier Generator

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
./bin/genwtm <config.json>
```

This will generate a Verilog module for a multiplier with the specified parameters. The generated module will be placed in the `build` directory.

## Running the Tests

To run the tests, you can use the following command:

```
ctest
```

#!/bin/bash

# This script generates a Verilog multiplier and runs a testbench for it.
# It requires 'jq' and 'iverilog' to be installed.

set -e # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
# The generator executable
GENERATOR_EXE="./build/mult-gen"

# --- Script ---

# Check for config file argument
if [ -z "$1" ]; then
  echo "Usage: $0 <config.json>"
  exit 1
fi

CONFIG_FILE=$1

# Check if required tools are installed
if ! command -v jq &> /dev/null; then
    echo "Error: 'jq' is not installed. Please install it to continue."
    exit 1
fi
if ! command -v iverilog &> /dev/null; then
    echo "Error: 'iverilog' is not installed. Please install it to continue."
    exit 1
fi

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file '$CONFIG_FILE' not found."
    exit 1
fi

# Run the multiplier generator
echo "1. Generating Verilog from $CONFIG_FILE..."
$GENERATOR_EXE $CONFIG_FILE

# Extract module name from config file
MODULE_NAME=$(jq -r '.multiplier.module_name' "$CONFIG_FILE")
if [ -z "$MODULE_NAME" ] || [ "$MODULE_NAME" == "null" ]; then
    echo "Error: Could not parse 'module_name' from $CONFIG_FILE."
    exit 1
fi

VERILOG_FILE="${MODULE_NAME}.v"
TESTBENCH_FILE="${MODULE_NAME}_tb.v"
COMPILED_FILE="${MODULE_NAME}.vvp"

# Check if generated files exist
if [ ! -f "$VERILOG_FILE" ] || [ ! -f "$TESTBENCH_FILE" ]; then
    echo "Error: Verilog files not found after running the generator."
    exit 1
fi

# Compile the Verilog files
MG_CPA_FILE="MG_CPA.v"
if [ ! -f "$MG_CPA_FILE" ]; then
    echo "Error: MG_CPA.v not found."
    exit 1
fi

echo "2. Compiling Verilog with iverilog..."
iverilog -o "$COMPILED_FILE" "$VERILOG_FILE" "$TESTBENCH_FILE" "$MG_CPA_FILE"

# Run the simulation
echo "3. Running simulation..."
vvp "$COMPILED_FILE"

echo "Done."

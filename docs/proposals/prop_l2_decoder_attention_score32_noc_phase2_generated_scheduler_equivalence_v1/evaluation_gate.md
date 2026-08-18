# Evaluation Gate

Run the workload-complete eight-wave replay on the remote evaluator with
`--descriptor-scheduler serial_generated`. The result must contain exactly one
JSON and one Markdown report and must not claim payload SRAM bitcells,
workload-activity power, or HBM/DRAM controller closure.

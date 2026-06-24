# Llama7B Mixed/Int8 Score Precision Boundary

This proposal sweeps attention score precision after the native checkpoint
ablation showed QKV8 is acceptable while score8 is not.

The output should identify the lowest score precision that preserves the
7B-class checkpoint attention-shadow ranking gate before a hardware/PPA mapping
job is scheduled.


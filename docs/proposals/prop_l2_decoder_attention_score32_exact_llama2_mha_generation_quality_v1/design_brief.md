# Design Brief

The candidate is the existing score32 q8/k8/v8, weight16, exp-LUT/div attention arithmetic. Reference and candidate runs use the same official Llama-2-7B checkpoint, prompts, dtype, and greedy decode sequence.

The evaluator validates both the requested model ID and loaded structural dimensions before collecting evidence. The job has no hardware dependency so model-quality execution can proceed in parallel with the physical recost chain.

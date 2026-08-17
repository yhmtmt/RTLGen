# Exact Llama-2-7B MHA Generation Quality

This proposal closes the model-identity gap in the native-context score32 attention frontier. It evaluates the score32 exp-LUT/div arithmetic on the official `meta-llama/Llama-2-7b-hf` checkpoint and refuses proxy checkpoints or non-MHA structures. It does not validate the separate 131k-token extrapolation.

The checkpoint is gated. The remote evaluator must already have Hugging Face authorization; authentication failure is a failed prerequisite, not quality evidence.

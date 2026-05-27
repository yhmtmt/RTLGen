# Llama7B Measured Compute Substitution

This proposal rescoring step replaces abstract Llama7B attention/KV compute-throughput points with merged corrected NPU compute PPA. It keeps the deployable model frontier restricted to quality-backed native-GQA KV8 and uses the physical-HBM memory/NoC model as the surrounding service model.


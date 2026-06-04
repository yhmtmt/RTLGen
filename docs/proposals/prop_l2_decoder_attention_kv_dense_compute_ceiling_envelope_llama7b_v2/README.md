# Llama7B Dense Compute Ceiling Envelope V2

This proposal reruns the Llama7B attention/KV compute ceiling envelope after
the dense FP16 GEMM tile result was measured and registered.

The goal is to replace the earlier hypothetical measured-density baseline with
the best registered RTLGen dense-tile density, then decide whether larger dense
tiles and memory/NoC integration are justified.

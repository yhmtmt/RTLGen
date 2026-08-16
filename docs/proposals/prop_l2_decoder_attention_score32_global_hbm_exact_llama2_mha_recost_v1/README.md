# Global-HBM Exact Llama-2-7B MHA Recost

This proposal corrects two model-identity errors before the score32 point can
re-enter the Llama-2-7B frontier. The HBM controller is global, so each wave
must replay the aggregate bytes from all 16 active clusters rather than one
tile. Exact Llama-2-7B also uses 32 KV heads (MHA), not the current four-head
GQA8 proxy.

The evaluator reports a corrected GQA8 baseline and an exact-MHA structural
recost. Neither row is promotable until native Llama-2-7B score32 generation
quality is measured.

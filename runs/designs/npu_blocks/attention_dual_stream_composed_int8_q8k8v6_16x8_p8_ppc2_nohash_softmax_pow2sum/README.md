# Composed Dual-Stream Attention No-Hash Softmax Pow2Sum

This candidate replaces the exact divider-based softmax normalization with a power-of-two denominator selected from the exp-weight sum. It keeps the max-shift exp approximation and one registered softmax input stage, but removes the `numer / sum_weight` divider.

The point is a PPA/architecture probe. If the physical result is attractive, it needs a separate quality/equivalence study before promotion into the Llama7B model path.

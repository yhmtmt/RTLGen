# Decode-shaped M1x8 score tile

Autoregressive Llama7B decode computes one active query row against key blocks.
For an eight-key block, each head-dimension beat multiplies one query scalar by
eight key scalars and accumulates eight signed 32-bit scores.

The measured M16x8 operational tile is functionally valid GEMM RTL, but its 16
rows cannot be shared across attention heads because each head has a different
key matrix. Scaling its full area as useful decode compute is therefore a
conservative, semantically mismatched recost.

This proposal compares an exact M1x8 scalar-drain tile with an exact M1x8 packed
score-row tile. The packed lane order directly matches the two-pass attention
engine and removes a separate scalar-to-row packer.

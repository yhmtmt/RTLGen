# Quality Gate

This change preserves the already quality-qualified signed-int8 Q/K and signed
32-bit score precision. It changes compute shape and result transport only.

Promotion requires exact RTL/reference equality for every score lane, including
negative operands, final-beat inclusion, backpressure, and command reuse. The
later Llama7B recost must retain the existing generation-quality evidence.

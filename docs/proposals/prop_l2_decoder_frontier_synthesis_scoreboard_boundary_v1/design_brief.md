# Decoder Frontier Synthesis With Bounded Producer Control

Refresh the whole-decoder frontier view after the bounded EVENT scoreboard fix.

The producer/ranker model still estimates output-projection service from
compute and memory bandwidth. The new SOFTMAX/EVENT guard result should be
carried as producer-control feasibility evidence, not folded into token
latency as if it measured the full producer.

The expected decision is still `iterate`: choose the next measured RTL frontier
from the updated evidence.

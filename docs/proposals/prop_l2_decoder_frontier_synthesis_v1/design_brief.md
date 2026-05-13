# Decoder Frontier Synthesis

Combine the latest L2 decoder evidence into one ranking view:

- whole-decoder stage breakdown for resident-weight MLP/norm context
- measured attention/KV tile-calibrated memory pressure
- producer/ranker shared NoC coupling

The intent is to choose the next measured RTL frontier from a whole-decoder perspective instead of optimizing standalone datapaths in isolation.

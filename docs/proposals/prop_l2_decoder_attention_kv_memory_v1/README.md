# Decoder Attention/KV Memory Hierarchy Breakdown

This proposal follows the whole-decoder stage breakdown and narrows the next question to attention.

The estimator separates QKV projection, QK score, softmax score movement, value mix, attention output projection, and KV-cache read/write traffic. It sweeps context length, larger model proxy shapes, KV memory tier, NoC hops, KV precision, and MHA/GQA/MQA sharing.

The result is not RTL PPA. It is a low-cost bottleneck map for deciding whether the next measured work should target KV locality, NoC bandwidth, attention compute, or score/softmax movement.

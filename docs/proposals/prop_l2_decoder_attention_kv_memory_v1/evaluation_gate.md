# Evaluation Gate

- Run `l2_decoder_attention_kv_memory_v1`.
- Confirm the report includes QKV projection, QK score, softmax, value mix, output projection, and KV-cache read/write terms.
- Confirm local SRAM, shared SRAM, HBM, and remote-HBM tier rows are present.
- Confirm MHA, GQA, and MQA sharing rows are present.
- Treat the result as an analytical memory hierarchy map, not measured RTL.
- Use the result to choose the next job only after checking whether conclusions are stable across context length, memory tier, and KV sharing.

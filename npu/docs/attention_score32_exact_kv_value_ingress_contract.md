# Exact Score32 V Ingress Composition Contract

## Ownership

`attention_score32_exact_kv_value_ingress` owns one accepted cluster-SRAM fill
target at a time. The target fixes the double-buffer selection, command ID,
query-head base, wave, and corresponding KV head. The buffer must equal the
wave-index low bit and the head base must be one of 0, 8, 16, or 24.

For that target, exactly 128 unique `(stream, block_slot)` blocks cover the
1,024 tokens of one 128-dimensional int8 V head. Each 1 KiB canonical planar
block enters as 32 addressed 256-bit flits and drains as sixteen 512-bit SRAM
rows. Completion is asserted only when the final row of the 128th unique block
is accepted by the SRAM endpoint.

## Composition

The wrapper directly drives the existing exact cluster-SRAM target and fill
ports. Buffer selection is captured at target acceptance and cannot change
during fill. Block metadata must match the resident KV head, duplicate blocks
are rejected, and backpressure propagates from the SRAM row port through the
transposer to canonical ingress.

The end-to-end RTL test fills all 2,048 rows of the real generated 16-bank,
double-buffer endpoint in a permuted block order, checks every output byte,
activates the resident command tuple, and reads data back through the endpoint
request/response path.

With one transpose buffer, the complete V head has a 6,271-cycle no-stall
bound from the first block target through final drain. This is a conservative
functional reference. Ping-pong or multi-lane transpose, SRAM macro
substitution, capacity/HBM gather descriptors, shared-mesh source routing, and
the external HBM controller/PHY remain separate architecture dimensions.

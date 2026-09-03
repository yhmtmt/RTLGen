# Exact Score32 K/Q Producer Staging Contract

## Storage

`attention_score32_exact_kv_key_stage` holds one int8 K head tile and one Q
group:

- K: 64 absolute block banks x 128 dimensions x 128 bits = 128 KiB.
- Q: 128 dimensions x eight int8 query heads = 1 KiB.

The K write interface uses `(kv_head, producer, producer_block, dimension)`.
The stage inverts the same group-specific p53/p54 prefix schedule used by the
producer and maps every write to one of the 64 absolute block banks. It rejects
an invalid second block, wrong head, nonsequential dimension, duplicate
completed block, or inconsistent last marker.

## Producer Schedule

On command acceptance, all producers receive block zero for 128 dimensions.
Only the 10 p54 or 11 p53 group-specific extra producers continue through
block one. Q is duplicated across both streams and broadcast identically to
all active producers, as required for attention on one query token.

Each producer has a pending bit. A ready lane accepts its current beat once
and clears its bit; the global dimension advances only after every active lane
has accepted. This bounds skew to one beat, avoids repeated handshakes, and
does not make valid combinationally dependent on ready.

## Composition

`attention_score32_exact_kv_key_ingress` connects the canonical planar-flit
transposer directly to this staging write interface. The full equivalence test
loads all 4,096 256-bit K flits through 64 transpose targets, checks all 8,192
producer beats, and applies independent per-lane stalls for both p53 and p54.

With one transpose buffer, a complete head tile requires 12,351 no-stall
cycles from the first target through the final drain. Producer input then
requires 256 barrier beats without stalls. Q filling uses an independent port
and can overlap K filling. This is a conservative baseline; transpose-buffer
parallelism and ping-pong fill/drain are follow-on architecture dimensions.

The arrays are inferred storage, not characterized SRAM macros. V fill,
capacity/HBM gather scheduling, cluster command release, and the external HBM
controller/PHY remain outside this block.

# Exact Score32 K/V Ingress Transpose Contract

## Scope

`attention_score32_exact_kv_ingress_transpose` converts addressed 256-bit
flits from the planar int8 tile layout into one existing score32 consumer
shape at a time:

- V: one 1 KiB, eight-token block becomes sixteen 512-bit cluster-fill rows.
- K: matching 1 KiB blocks from both 512-token streams become 128 128-bit
producer beats.

The target identifies the K/V head and six-bit block slot. V also identifies
the stream. For K, the RTL derives the producer and relative block using the
checked group-specific p53/p54 slot schedule. Both output channels retain the
K/V head identifier; no downstream block must infer it from hidden state.

## Addressing

The 1 MiB tile byte order is:

```text
K[kv_head][token][dimension], then V[kv_head][token][dimension]
```

Each accepted flit is 32-byte aligned and carries a 32-bit byte-valid mask.
The block completes only after every byte is present. Disjoint partial writes
may complete a line; overlapping bytes, a zero mask, an unaligned address, or
metadata outside the active target sets the sticky protocol error.

## Reorder

Sequential flits do not directly form consumer beats. A V flit contains four
eight-byte slices for one token, while a fill row contains one slice from
eight tokens. A K producer beat contains one dimension byte from eight tokens
in each stream. The RTL therefore stores 64 256-bit lines and performs the
required transpose during drain.

The one-buffer minimum service is explicit and has no hidden overlap:

| Target | Input flits | Output beats | Transfer cycles | Target II |
|---|---:|---:|---:|---:|
| one V block | 32 | 16 | 48 | 49 |
| one paired-stream K block | 64 | 128 | 192 | 193 |

Transfer cycles exclude the target handshake. The initiation interval includes
the edge required to return to idle before accepting the next target.
Backpressure holds the current output and extends both bounds.

## Boundary

V output directly matches one cluster SRAM fill-row port. K output is a
serial, producer-addressed staging write; it cannot directly supply all 53 or
54 producer inputs in the same cycle. A later composed gate must add a banked
producer-local K store, parallel readout, capacity/HBM gather descriptors,
double buffering, and block-level overlap scheduling.

The module is a functional and area-conservative reference, not the final
Llama7B cluster throughput architecture. HBM controller/PHY and SRAM bitcells
remain outside this contract.

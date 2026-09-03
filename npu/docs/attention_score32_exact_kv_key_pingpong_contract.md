# Exact Score32 Ping-Pong K Ingress Contract

## Architecture

`attention_score32_exact_kv_key_pingpong_transpose` accepts canonical K flits
without a separate block-target cycle. The first addressed flit fixes the KV
head and block slot. Two 2 KiB transpose buffers alternate fill and drain, and
the drain emits two adjacent 128-bit dimensions in one 256-bit beat.

`attention_score32_exact_kv_key_stage_wide` stores the paired dimensions as one
256-bit word in each of 64 explicit K banks. Producer readout still presents
one 128-bit dimension per cycle to every active p53/p54 producer, preserving
the existing score-cluster interface and per-lane ready/valid accounting.

## Service Bounds

For one 128 KiB K head:

- one-buffer serial reference: 12,351 cycles;
- ping-pong serial drain: 8,256 cycles;
- one-buffer 256-bit drain: 8,255 cycles;
- automatic-target ping-pong 256-bit drain: 4,160 cycles.

The selected candidate accepts 4,096 256-bit flits on consecutive cycles and
then drains the final buffer in 64 cycles. A wider drain cannot improve this
head interval without widening canonical ingress. The producer phase remains
256 barrier beats without stalls because producers with a second block run a
second 128-dimension phase.

## Verification And Physical Boundary

The full test covers p53 and p54 group rotations, all 64 K block pairs, all
8,192 producer beats, per-block last markers, and independent producer stalls.
It checks exact byte identity from canonical flits through producer outputs.

The 128 KiB K store and 1 KiB Q store remain inferred arrays. Their generic
asynchronous-read implementation is a functional reference, not SRAM-macro
PPA. Physical evaluation must separately measure the ping-pong transpose and
control slice, then substitute a characterized 64-bank memory organization
that preserves one 256-bit write and parallel producer read semantics.

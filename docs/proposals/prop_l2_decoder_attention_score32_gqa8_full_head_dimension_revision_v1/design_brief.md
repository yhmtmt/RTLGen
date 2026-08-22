# Design Brief

The prior composed GQA8 probes asserted `input_last` on every accepted
query/key beat.  They exercised the structural hierarchy but reduced each
token score to one INT8 product.  Llama7B requires a 128-term dot product, so
the producer accumulation dependency and its release timing were unproven.

The corrected driver emits 128 deterministic dimension beats for every token
block, asserts `input_last` only on dimension 127, and computes reference scores
from the same complete sequence.  Large query, key, last, and value stimuli are
written as sidecar memory files instead of embedded Verilog assignments.  The
one-group run is the bounded first gate; the four-group rotation follows only
after it passes.

The remote tasks use the fine-compositional Icarus backend.  It serially
replays every exact producer stimulus through real producer RTL, then verifies
the concrete p54/p53 SRAM/reducer paths and global tree with complete sidecars.
This avoids an unbounded monolithic 856-producer simulation without replacing
any arithmetic stage by a heuristic result.

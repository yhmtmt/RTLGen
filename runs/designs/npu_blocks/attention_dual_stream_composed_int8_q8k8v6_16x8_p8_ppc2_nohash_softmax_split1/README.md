# Composed Dual-Stream Attention No-Hash Softmax Split1

This candidate keeps the exact divider-based softmax approximation but splits the shared softmax block into an exp/sum register stage followed by the divide/output stage. Value-stream payload and score-mix inputs are delayed by three stages to stay aligned with the registered softmax weights.

The point tests whether the current critical path is dominated by the front half of softmax or by the divider/output half.

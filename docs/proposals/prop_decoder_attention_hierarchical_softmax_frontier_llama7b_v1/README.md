# Hierarchical Softmax Frontier

This proposal removes the assumption that independently normalized 8-token attention blocks can be composed into a Llama7B context row.

The first gate compares one-pass online merges with an exact two-pass global-max/score-replay reference at the full 131072-token target. The selected architecture must then expose real score-buffer, max-reduction, exponent accumulation, weighted-value accumulation, final division, and ready/valid behavior in RTL before full-model recost.

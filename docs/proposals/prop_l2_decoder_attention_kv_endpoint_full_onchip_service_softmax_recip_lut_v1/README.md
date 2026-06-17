# Endpoint Full On-Chip Service With Reciprocal-LUT Softmax

This proposal reruns the explicit endpoint/SRAM/NoC on-chip service schedule
against the corrected q8/q10/q12 reciprocal-LUT endpoint full-search frontier.

The goal is to reduce the current on-chip service abstraction after the softmax
precision frontier was folded into the Llama7B endpoint SRAM/NoC search. HBM and
DRAM service remain inherited unchanged in this item.


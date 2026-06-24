# Llama7B Mixed/Int8 Broad Native Quality

This proposal broadens the native checkpoint attention-shadow gate for the
only mixed/int8 score-boundary point that passed: QKV8 with score24 and
float-quantized softmax.

The result should determine whether the passing high-score point survives the
full default prompt set before it is treated as a precision-valid architecture
candidate for energy/PPA frontier scheduling.

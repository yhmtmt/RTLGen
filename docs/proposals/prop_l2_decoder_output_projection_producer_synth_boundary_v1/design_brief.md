# Decoder Producer Synthesis Boundary

The previous output-projection producer scale job entered a long ABC synthesis phase before producing useful PPA. This job changes the question from "finish nm4/nm8/nm16 PnR" to "where does synth-only compilation stop being practical?"

It probes nm2, nm3, and nm4 in increasing order using `1_2_yosys`, a total timeout, and a quiet-output timeout. The first timeout or failed synthesis stops the probe and records the largest completed point.

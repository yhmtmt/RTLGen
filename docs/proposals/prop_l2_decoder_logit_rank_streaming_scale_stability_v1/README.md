# Decoder Logit-Rank Streaming Scale Stability

This job broadens the SRAM-backed decoder streaming frontier across larger vocabulary sizes and wider producer-lane counts.

The sweep is intentionally still a model-level L2 check. It does not add new RTL or measured NoC PPA; it asks whether the current conclusion remains stable enough to justify either NoC/banking work or larger-model quality confirmation.

The boundary follow-up adds the r128/k1 explicit macro pin-perimeter result as sensitivity evidence. That value is useful for understanding artificial boundary pressure, but the padded macro die area is not charged to the normal integrated-ranker cost ranking.

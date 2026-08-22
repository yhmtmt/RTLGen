# Promotion Gate

Run and merge the one-group full-128D equivalence result first.  Dispatch the
four-group rotation only after that result passes without protocol errors or
resource ambiguity.  Replace the active score32 GQA8 frontier rerank only after
both corrected reports pass and are materialized.  Any timeout or resource
failure leaves the equivalence claim unresolved and must not restore the
retracted ranking.

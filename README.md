# ExcerptGate

Standalone GenLayer Intelligent Contract. No frontend.

bind locks one URL and one excerpt. adjudicate fetches the page live.
AFFIRMED or DENIED only if that excerpt is still on the page. Otherwise UNBOUND.

- Network: Studionet (61999)
- Address: `0xE910a151328e3240DF6477b701499DE38362330b`
- Studio: https://studio.genlayer.com/?import-contract=0xE910a151328e3240DF6477b701499DE38362330b
- Explorer: https://explorer-studio.genlayer.com/address/0xE910a151328e3240DF6477b701499DE38362330b

## Settled cases
1. wrong excerpt (illustrative examples) → UNBOUND
2. documentation examples excerpt → AFFIRMED
3. dead URL → UNBOUND
4. UN homepage question + real excerpt → DENIED

Flow: bind → adjudicate → challenge

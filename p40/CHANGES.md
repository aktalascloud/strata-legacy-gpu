# Current build

Official source `ffa80d73133ea5c548aefe57889a16e8085a938f`.

- Fix Windows inherited log handles (#5175): engine and CPU vision output now appends instead of overwriting earlier log lines.
- Retain qualified AVX1/Pascal classic E4 and locked CPUvision99 bytes; no native rebuild or new generation-speed claim.
- PR5040 streaming tool fix was already included in C5; 1553 exact-byte parser schedules are retained, not rerun.
- Experimental DeepSeek/C7 source is separate; this classic-only release contains no model weights or additional backend runtime.

Measured performance is independently source-pinned in BENCHMARKS.md.

# Vectorized CUDA table staging

**Not selected; the original engine is retained.** Copies opaque32-bit codebook words with aligned128/64-bit loads/stores and scalar alignment/tail fallback. Shared native IQ CUDA consumers use the helper; sign-mask construction, synchronization, weights and floating point expressions stay unchanged. No model-name or one-quant dispatch is introduced. Original HIP loops remain; other backends are not newly qualified.

P40 numerical qualification:72 prototype constant/global, aligned/unaligned and output-bound cases; real IQ MMVQ/grouped regression and EXPDEC grid0/grid1 all passed. The isolated1024-word constant-memory copy median fell9.367 to6.300 microseconds (32.7% lower time). Actual IQ tables use device memory; that constant-memory result is not a model throughput claim.

Two Swift/P40 A/B pairs, same512-token request, equal warmups, reserve150MiB, context262144, stored Q2 MTP/sampling/KV unchanged. Measured candidate rates: `[38.0, 38.4, 38.3, 39.1, 38.2, 38.0, 38.7, 39.0]` tok/s; control: `[37.8, 37.8, 37.9, 38.4, 37.7, 37.0, 37.6, 37.8]`. Pooled median difference: **1.46%**; pair differences: `[1.3210039630118908, 2.1248339973439556]`%; maximum within-arm MAD: `0.910%`. Selection required positive direction in both pairs, pooled gain greater than twice the observed MAD and comparable CPU load. The candidate did not meet all gates; the small initial difference is not a confirmed throughput gain.

CPU/host AVX1 flags stay unchanged. The source-controlled CUDA compiler command retains its inherited device-math flags; no new relaxation is added. Q8 numerical evidence is reused only with the identical native_mmvq object/archive and five critical sources; the changed IQ CUDA object has fresh checks. No new Q8 run is claimed.

Base: upstream`54828c7efbcdf9474697e70922d851f6707f4b32` plus the published legacy aggregate, reconstructed tree`6db1359840eacdc4a900393f645553d45ccda4e8`. Adapt before applying to another tree. MIT licensing retained. Patch SHA256:`671b8dc9204b230a446ca6067664496778ef4bc0b1758bd4d347b975ef451d40`.

MTP response/acceptance variation also exists in controls. Operator checks do not prove identical whole replies. Other model weights were absent and were not downloaded; no other-model or universal speed claim, filled262K quality test or fresh-OS installation claim is made.

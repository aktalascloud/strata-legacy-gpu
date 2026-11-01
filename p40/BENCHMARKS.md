# Source-bound short-workload measurements

| Workload | No MTP, native tok/s | Q2 MTP + suffix3, native tok/s | Gain |
|---|---|---|---|
| short-ru | 30.8342 | 37.9704 | +23.14% |
| code-4k | 34.1319 | 36.7436 | +7.65% |

Measured 2026-11-01: `swift-1.5-iq3-s`, engine 0.1.55, source `c62d5e3a15b4`, native SHA-256 `3B0486521742B5B2A40C5DD8B13014B63FA3090EAF4EF28BD4D305562A342BD7`. Same native bytes as r1. Equal-workload harmonic gain: **15.2705%**. Three selected repeats and four pooled baseline repeats per workload; warmups excluded.

Context capacity262144; KVq4_0, host resident20480. Inputs133 and4128 tokens; output256. Sampling unchanged, seed requested. Other PC/client traffic permitted; native SSE decode timing excludes queue latency. This is short Russian and cached4K/code throughput, not a filled262K benchmark or quality evaluation. Background traffic and short runs limit precision; tuning was not exhaustive. CPU operator improvements are separate and percentages are not additive.

Hardware: Windows; Ivy Bridge AVX1; 256 GiB RAM; Tesla P40 24 GiB. Native rate = 1000 * predicted_n / predicted_ms; thinking tokens count. No frontend benchmark.

[Structured results](results/benchmarks.json). No private configuration, sampler values, payloads, responses or raw logs.

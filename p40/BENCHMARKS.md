# Latest source-bound measurements

| Workload | Baseline native tok/s | Selected native tok/s | Gain |
|---|---|---|---|
| short-ru | 30.8342 | 37.9704 | +23.14% |
| code-4k | 34.1319 | 36.7436 | +7.65% |

Measured 2026-11-01: `swift-1.5-iq3-s`, engine 0.1.55, source `c62d5e3a15b4`, native SHA-256 `3B0486521742B5B2A40C5DD8B13014B63FA3090EAF4EF28BD4D305562A342BD7`. Historical measurement of the explicitly identified source/native. No throughput gain is established for the current build. Equal-workload harmonic gain for that measurement: **15.2705%**.

Context capacity 262144; KV q4_0;host streaming20480resident. Inputs {"code-4k": 4128, "short-ru": 133}; output 256. Mode: Q2 MTP with suffix3; compare pooled no-MTP baseline. Sampling: unchanged; seed requested. Background: Other PC/client traffic permitted; native SSE timings ranked, not queue latency. Warmups included: False. Short Russian and cached4K/code decode only; not a filled262K benchmark, quality evaluation or exhaustive tuning. CPU operator improvements are separate and percentages are not additive.

Hardware: Ivy Bridge AVX1, 256 GiB RAM, Tesla P40 24 GiB, Windows; worker counts are recorded per measurement. Rate = 1000 * predicted_n / predicted_ms. Thinking tokens count. No frontend benchmark.

[Structured evidence](results/benchmarks.json). No private payloads, responses, host identifiers or raw logs.

# Latest source-bound measurements

| Workload | Native tok/s | Whole API tok/s |
|---|---|---|
| short | 34.56 | 31.11 |
| cached38K | 33.51 | 27.22 |

Measured 2026-10-30: Swift1.5 IQ3_S, engine 0.1.54, source `870aedd9e1eb`. YaRN4, KVq4 host/32768, MTPQ2/spec3,14workers; xhigh/T0/seed12345,128output,1warm+2measured per workload. Tested38,912tokens, not a filled1M window. Short measurement noisy. Different from the current0.1.55 profile; no new whole-model speed claim. The recent CPU optimization is operator-only; percentages are not additive.

Hardware: Ivy Bridge AVX1, 256 GiB RAM, Tesla P40 24 GiB, Windows; worker counts are recorded per measurement. Rate = 1000 * predicted_n / predicted_ms. Thinking tokens count. No frontend benchmark.

[Structured evidence](results/benchmarks.json). No private payloads, responses, host identifiers or raw logs.

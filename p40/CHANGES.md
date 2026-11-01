# Current build

Official source `c62d5e3a15b40ea51c96aae9e8d36928965f53ab`.

- Merge official native0.1.55; retain the reviewed Ivy/Pascal/no-pin/FP/owner patches.
- Q2 activation-scale hoist preserves quantization and reduction order; operator-only results are separate from model throughput.
- Bounded MMQ ID reads and explicit unsigned IQ register-byte extraction in the pinned build copy.
- API tool-result ID mapping, declared-tool authority, forced tool choice and correctly framed errors.
- One model-neutral strata.json, explicit UTF8 readers, metadata-driven model paths and public presets.
- Exact native reuse for serving-only changes; no relabelled GPU results, weights or private state.

Measured performance is independently source-pinned in BENCHMARKS.md.

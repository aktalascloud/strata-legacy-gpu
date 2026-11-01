# Current local changes

- AVX1/Ivy strict baseline and guarded wider kernels; no forced CPU pinning or system NUMA changes.
- Pascal J96/unroll; independent register-byte extraction and bounded MMQ ID reads.
- Row-independent Q2 activation scales hoisted without changing quantization or FP reduction order.
- Current-request tool authority, incremental parsing, API ID/display name separation and protocol error/tool-result compatibility.
- Source-bound author capabilities, CPU vision, immutable activation and graceful owner control.

Exact patch/source fingerprints are published in the manifests. CPU-operator results are separate from whole-model throughput. Unverified hardware paths remain experimental.

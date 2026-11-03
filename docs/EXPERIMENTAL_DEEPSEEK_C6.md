# DeepSeek C6/C7: EXPERIMENTAL_SOURCE_ONLY

This draft contains four source changes. It does not ship a newly qualified engine, change model defaults, or claim an end-to-end speed improvement.

| Change | Result |
| --- | --- |
| External CPU vision with RAM-only loading | The native load guard accepts external CPU vision while retaining rejection of the native vision tower and disk-tier options in RAM-only mode. Actual complete-model residency remains to be verified. |
| Profiler sample bounds ([upstream #5127](https://github.com/Niko1221/Strata/pull/5127)) | The sample buffer follows the profiler stage table, stage indices are checked, and chunk accumulation uses the matching stage count. |
| Per-request DeepSeek speculation control | `strata_tune.spec` accepts booleans or integer `0`/`1` for the existing native request switch. Missing or invalid values preserve existing behavior; other engine families are unchanged. |
| AVX1 CPU activation quantization | The CPU fallback uses the existing AVX1 Q8_K quantizer on AVX1 CPUs without AVX2. Other activation formats keep their previous path; the existing presence-based `STRATA_NO_Q8K_AVX1` opt-out is honored. |

For example, `{"strata_tune":{"spec":0}}` suppresses speculation for that request. Draft weights, memory allocations, taps and seeding remain loaded. This is **not** a comparison with an engine started without a drafter. The switch also suppresses optional lookup speculation when that feature is enabled.

Validation so far:

- The exact request-method candidate reuses 68 passing CPU cases; the external-vision guard has eight truth-table cases and source reachability checks. The profiler collector has an instrumented CPU canary/bounds check using simulated CUDA events. These are separate from actual model or GPU validation.
- An inactive C6 AVX1/CUDA 12.9/sm61 candidate compiled and linked the changed native unit while reusing existing components. It was not a complete rebuild. Comparison of its device image found only 12 anonymous-symbol-prefix substitutions; other device-image bytes matched. This is reuse evidence, not a new numerical GPU run.
- C7 recompiled one CPU host unit and reused the other C6 components. Its GPU device image is byte-identical to C6. Eight activation-byte checks and eight integrated CPU fallback checks passed, with all written outputs finite and selected output rows checked against a CPU reference. This is not a full-matrix numerical sweep or a GPU/model result.
- Isolated warm-cache **quantization-only** measurements were **2.18x at K=5120** and **2.09x at K=2304** versus the previous quantization path. These are not token-generation rates or end-to-end expert/model speedups.
- A plan for **148 actual-shape GPU reports is prepared, not executed**. Its CPU numerical reference samples explicit rows and columns; planned GPU scans cover all written outputs and canaries. Earlier bounded tests do not become full-shape passes.

Complete DeepSeek payload verification, actual RAM residency, MTP behavior and image-response checks remain pending. Existing qualified releases and their validation scope are unchanged.
HIP, SYCL and other backend builds were not run for this draft; compatibility is not claimed for them.

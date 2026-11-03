# DeepSeek C6: EXPERIMENTAL_SOURCE_ONLY

This draft contains three source changes. It does not ship a newly qualified engine, change model defaults, or claim a speed improvement.

| Change | Result |
| --- | --- |
| External CPU vision with RAM-only loading | The native load guard accepts external CPU vision while retaining rejection of the native vision tower and disk-tier options in RAM-only mode. Actual complete-model residency remains to be verified. |
| Profiler sample bounds ([upstream #5127](https://github.com/Niko1221/Strata/pull/5127)) | The sample buffer follows the profiler stage table, stage indices are checked, and chunk accumulation uses the matching stage count. |
| Per-request DeepSeek speculation control | `strata_tune.spec` accepts booleans or integer `0`/`1` for the existing native request switch. Missing or invalid values preserve existing behavior; other engine families are unchanged. |

For example, `{"strata_tune":{"spec":0}}` suppresses speculation for that request. Draft weights, memory allocations, taps and seeding remain loaded. This is **not** a comparison with an engine started without a drafter. The switch also suppresses optional lookup speculation when that feature is enabled.

Validation so far:

- The exact request-method candidate reuses 68 passing CPU cases; the external-vision guard has eight truth-table cases and source reachability checks. The profiler collector has an instrumented CPU canary/bounds check using simulated CUDA events. These are separate from actual model or GPU validation.
- An inactive AVX1/CUDA 12.9/sm61 candidate compiled and linked the changed native unit while reusing existing components. It was not a complete rebuild. Comparison of its device image found only 12 anonymous-symbol-prefix substitutions; other device-image bytes matched. This is reuse evidence, not a new numerical GPU run.
- A plan for **148 actual-shape GPU reports is prepared, not executed**. Its CPU numerical reference samples explicit rows and columns; planned GPU scans cover all written outputs and canaries. Earlier bounded tests do not become full-shape passes.

Complete DeepSeek payload verification, actual RAM residency, MTP behavior and image-response checks remain pending. Existing qualified releases and their validation scope are unchanged.
HIP, SYCL and other backend builds were not run for this draft; compatibility is not claimed for them.

# AVX1 / Pascal decode review, 7 November 2026

Official main was fetched again:54828c7e. This pass keeps common engine mechanisms separate from model/quant-specific dispatch. Only Swift weights were available and authorized for measurement.

| Source | Code reviewed and disposition |
|---|---|
| [Strata5099](https://github.com/Niko1221/Strata/pull/5099) | Full relevant refill/native diff. Our single-GPU refill already overlaps; observed host wait0.10ms of46ms/window. No multi-GPU assumption imported. |
| [Strata4604](https://github.com/Niko1221/Strata/pull/4604) | Full relevant canonical-logprobs diff. Fixed read policy costs ordinary decode; not enabled as an acceleration. |
| [Lamina16](https://github.com/eddoursul/Lamina/pull/16) | Fused CPU pool idea already integrated. Current sampled Swift decode had zero CPU expert jobs; no unused-path speed claim. |
| [llama.cpp31831](https://github.com/ggml-org/llama.cpp/pull/31831) | All nine changed files and discussion read. Short-column weight reuse is useful and already present in native MMVQ/grouped experts; no Adreno thresholds copied. |
| [PolyStrata147](https://github.com/simplexai-labs/PolyStrata/pull/147) | All five files and discussion read. Tiled FP32 q8 attention improves HIP prefill, explicitly not decode. Different native q4-KV path; not blindly ported. |
| [llamAmpere90](https://github.com/JakeATX/llamAmpere/pull/90) | Both Windows/large-offset changes read. Separate runtime; native reader already uses wide offsets. |
| [Maya904](https://github.com/mw00/project-maya/pull/904) | Both files/body read. DSpark helper-pool placement requires a second helper GPU; generic lesson is protecting draft residency, already required locally. Author's paired decode is1.5% lower, not a universal speedup. |
| [Strata5458](https://github.com/Niko1221/Strata/pull/5458) | Results-only gfx1100 document. AMD timing/defaults are not P40 qualification. |
| [llama.cpp30247](https://github.com/ggml-org/llama.cpp/pull/30247) | Partial: OpenCL Gemma4 path, host API patch missing. Full semantic review is not claimed. |
| [Sepal-Runner7](https://github.com/bloomifycafe/Sepal-Runner/pull/7) | Partial PR: SIMT GEMM, scan shared-memory guard, decision caller and complete FP32 chunked GDN/contract read. Portable register/vector-load ideas;64-token WY staging is not automatically faster for tiny verify windows. Its input-row decision throughput is not autoregressive LLM decode. Attention/integration/tests/Lean remain pending. |

Standalone matvec-transposed and EXPDEC R2/R2-B4 experiments did not establish a reliable model benefit; their flags were restored. Each own code delta is retained as a separate patch with status and measurements. Existing PCIe overlap/stable-address patches are separately available too. Percentages from unrelated operations, CPUs and GPUs are not additive.

The older frozen PR remainder has applicability decisions. This is not a complete security or semantic audit of every source. Fresh code subset:4 fully reviewed PRs and2 partial PRs; the three older relevant native reviews are counted separately. No false global semantic completion percentage is assigned.

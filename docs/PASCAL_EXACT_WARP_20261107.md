# Pascal exact-warp update, 7 November 2026

This update merges official Strata `146df3c468739147f520ac3816de806f71232571` (engine0.1.58), retaining the existing AVX1/P40 changes. Five merge conflicts were resolved against the qualified implementations: CMake, frontend/server, dense loading and verifier copy scheduling. The separate public C20 DeepSeek source remains intact; it is not a new DeepSeek runtime qualification.

## What changed relative to stock

The new opt-in `STRATA_MMVQ_EXACT_WARP=1` schedules selected dense matrix-vector products on one physical CUDA warp. It keeps the previous four logical accumulation chains and their merge order, removing cross-warp shared partials and their barrier. It retains the original weights, quantization, routing and dot-product expressions.

The idea was investigated from [Strata #5476](https://github.com/Niko1221/Strata/pull/5476). Its original one-warp sum changes floating-point order. This fork's adaptation preserves the old order instead. The selected dispatch covers Q4_K/Q5_K/IQ4_NL, K<=4096, N>=512 and verification widths2–4 or8 in the CUDA sm60 experiment build. Other formats/geometries and the unset path retain their previous dispatch. No model-name dispatch is used. P40 is the measured GPU; other architectures are not qualified by this report.

The existing [selected patch catalogue](../performance/patches/series/README.md) documents the retained AVX1 PLE, Pascal MMQ, PCIe overlap/static-address, RAM-residency, parser/security and startup/control changes. Their historical percentages are not additive.

## Measurements and limits

On Tesla P40, selected dense operations improved about6–40% at the usual2–4 verification columns. The preliminary exact template matched72 comparisons, including odd output sizes. The final production archive passed72 direct/Graph comparison cases against independent single-column calls,130 Q8 cases and all26 required package checks. These include actual-shape and small-shape fallback cases; they are not72 distinct tensor geometries or a full model-quality evaluation.

Same-native Swift IQ3_S A/B used seven requests per arm, two warm-ups and five measured512-token replies, the same prompt, greedy temperature0/seed42 and unchanged model settings. Median system CPU was7.2% in both arms.

| Profile | Median native tok/s | MAD |
|---|---:|---:|
| Exact-warp disabled | 37.6 | 0.27% |
| Exact-warp enabled | 37.8 | 0.53% |

The observed +0.53% is below the measured noise. Outputs and MTP acceptance also vary, so **overall model TPS gain is not established**. The profile retains the confirmed exact operator benefit without a credible model regression. It is not an absolute maximum claim.

The broader template experiment covered140 comparisons with exact outputs. Large Q6_K/IQ4_XS shapes were about10–20% slower at three columns, so those formats are excluded from this dispatch. A separate existing EXPDEC R1 MINB2/MINB4 comparison, three normal rounds and one strided round, found only timing noise; MINB4 remains unchanged. No extra model arm was run for that ineffective parameter.

CPU/host retain the O3/Ivy AVX1 profile with strict FP and no baseline AVX2/FMA/F16C. The native MMVQ unit retains its existing source-controlled CUDA math flags; this patch adds no FP relaxation. CPU vision is reused by identical component bytes and normalized source closure, not relabeled as a fresh compilation.

## Model settings

The checked Swift profile keeps context262144,150MiB reserve,14workers, Q2 MTP, speculation3/confidence0.5, suffix3, PCIe fraction1, q4_0 KV with20480 resident tokens and growth, CPU-only vision and standard xhigh reasoning. Existing user sampling/settings are preserved. First-install defaults should follow the [pinned Swift author's card](https://huggingface.co/SC117/Swift-1.5-Qwen3.8-Flash-Next-GSQ-RCO-abliterated-GGUF): temperature1.0, top_p0.95, top_k20, min_p0, xhigh; benchmark requests override temperature only for repeatability. The Q2 RT head is the qualified compatible base draft, not a newly trained Swift-specific head.

## Review scope

Ten selected fresh PR revisions were assessed; eight relevant code scopes were read and two remain explicitly partial. This is not completion of every tracked PR. Relevant findings include:

- [Strata #4910](https://github.com/Niko1221/Strata/pull/4910): the small-batch PLE allocation avoidance is already integrated; preserve main's large-batch hash fallback.
- [Strata #5474](https://github.com/Niko1221/Strata/pull/5474): unwidened FP16 and grouped SwiGLU fusion are prefill ideas, not demonstrated decode gains here.
- [Strata #5475](https://github.com/Niko1221/Strata/pull/5475): new Q8 copies change HC weights and validation tolerance; not selected.
- [PolyStrata #149](https://github.com/simplexai-labs/PolyStrata/pull/149): size-class MMQ reduces padded prefill work in a separate engine; no direct classic-decode port.
- [Maya #906](https://github.com/mw00/project-maya/pull/906): fixes shared-prefix/slot restoration in the separate DeepSeek scheduler; not a Swift change.
- [Xolotl #115](https://github.com/Indras-Mirror/Xolotl/pull/115): disk-prefix latency policies do not benefit this RAM-only profile.
- [Strata #5471](https://github.com/Niko1221/Strata/pull/5471) and [Sepal #8](https://github.com/bloomifycafe/Sepal-Runner/pull/8): relevant implementation read, full proof/benchmark/safety scopes still incomplete. No unmeasured architecture thresholds were imported.

Review follows exact heads and a two-month activity window. Earlier inventory/applicability closure is not full semantic or security review. No new weights, hardware settings, affinity, system NUMA policy or unrelated services were changed.

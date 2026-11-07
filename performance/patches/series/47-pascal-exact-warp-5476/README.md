# Exact logical-warp dense scheduling on Pascal

Status: selected and enabled in the primary Swift profile. The final native passed72 direct/Graph comparison cases,130 Q8 cases and26 required package checks. Same-binary model A/B observed37.8 vs37.6 tok/s (+0.53%), below noise; overall model TPS gain is not established. No new approximation was introduced.

The one-warp idea comes from [Strata PR5476](https://github.com/Niko1221/Strata/pull/5476), head `ca4a88d6c4b72543ef6d72790ec90a89d15cefbd` (MIT). Its original one-warp reduction changes floating-point order. This adaptation keeps the existing four logical accumulation chains and their ordered merge inside one physical warp, removing cross-warp shared-memory partials and barriers. Weight values, quantization, routing and the individual dot products stay unchanged.

The patch applies to the qualified Strata146df3c native source with the local0.1.58 aggregate55b99414. It is not a standalone patch against arbitrary stock revisions. Exact input/output hashes are recorded in the local preparation and qualification receipts.

Opt-in: `STRATA_MMVQ_EXACT_WARP=1`. The dispatch is compiled only for the CUDA sm60 experiment build, before B6, for Q4_K/Q5_K/IQ4_NL, K<=4096, N>=512 and verification widths2–4 or8. Q6_K, IQ4_XS, other geometries and the unset/default path keep the previous dispatch. No model-name check is used.

On Tesla P40,72 preliminary direct comparisons, including odd output sizes, matched the existing qualified B6 path and independent single-column calls bit for bit. Typical T2–4 operations improved about6–40%; these percentages are operator results, not model token throughput. The original broader one-warp experiment regressed some Q6_K and IQ4_XS shapes and was not selected.

The final production checker bound the new archive, compared direct and CUDA Graph output with independent old single-column arithmetic, and the profile was applied through the existing graceful deployment. HIP/SYCL/Metal execution, other GPUs and other models are not qualified by these measurements.

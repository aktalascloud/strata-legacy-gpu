# Exact singleton fused GU scheduling

Selected. Own scheduling adaptation on the prior qualified H2 path, official base `146df3c468739147f520ac3816de806f71232571`. A generic optional hint receives the verifier's actual token-group size. Under existing sm61/H2/GU21/2560x640/non-strided/cap10..40 guards, hint1 selects NT1; every entry is still processed by the chunk loop even with an inaccurate hint. Other callers and windows retain NT4. No FP expression or reduction tree changes.

ptxas reports NT4=123 registers versus NT1=64, no spills. Six alternating Graph rounds over rotating weight blobs gave singleton-operation throughput+4.45..11.13% (G10:+9.48%,70.50 to64.39us). NT1 on multi-entry groups, broad NT2 and forced occupancy regressed; excluded. This is an operation gain, not a whole-model speedup or additive percentage.

Final native `d8ee83c2`: CPU/ISA guards,130 actual-library Q8 direct/Graph cases (one expected shared-memory decline per mode),56 normal/strided expert pairs,27 package GPU cases including full F32, standard graceful startup and loaded/API verification passed. CPUvision is unchanged. Raw detached expert tests covered360 chunk and240 rejected launch-bound cases. They do not constitute a broad model-quality evaluation.

Both model controls use exact rank0 routing. Greedy request T0/seed42, two warmups plus five512-token measurements: 29.6/29.3tok/s, observed-1.01%, MAD1.69/1.02%, CPU7.4/8.1%. Author-default T1/top_p.95/top_k20, one warmup plus three512-token measurements: 27.9/28.5tok/s, observed+2.15%. Comparable identical text/draft work: greedy=False, author=False. Whole-model TPS gain established:False. Timing differences with different MTP acceptance or inside noise are not attributed to the kernel.

Local STRATA_ROUTE_TAIL_SKIP changed from rank1 to0 for model quality: compute all original selected experts. It was never a Boolean flag. The prior private39–40tok/s H2/expert-table measurements used rank1 and must not be presented as exact-routing measurements. The public first-install preset already used0 and is unchanged. No new routing bias, quantization, sampler, OS policy or model setting is introduced by these code patches.

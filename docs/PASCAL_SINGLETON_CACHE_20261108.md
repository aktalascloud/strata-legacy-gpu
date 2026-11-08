# P40 singleton scheduling and exact routing,8 November2026

# Exact singleton fused GU scheduling

Selected. Own scheduling adaptation on the prior qualified H2 path, official base `146df3c468739147f520ac3816de806f71232571`. A generic optional hint receives the verifier's actual token-group size. Under existing sm61/H2/GU21/2560x640/non-strided/cap10..40 guards, hint1 selects NT1; every entry is still processed by the chunk loop even with an inaccurate hint. Other callers and windows retain NT4. No FP expression or reduction tree changes.

ptxas reports NT4=123 registers versus NT1=64, no spills. Six alternating Graph rounds over rotating weight blobs gave singleton-operation throughput+4.45..11.13% (G10:+9.48%,70.50 to64.39us). NT1 on multi-entry groups, broad NT2 and forced occupancy regressed; excluded. This is an operation gain, not a whole-model speedup or additive percentage.

Final native `d8ee83c2`: CPU/ISA guards,130 actual-library Q8 direct/Graph cases (one expected shared-memory decline per mode),56 normal/strided expert pairs,27 package GPU cases including full F32, standard graceful startup and loaded/API verification passed. CPUvision is unchanged. Raw detached expert tests covered360 chunk and240 rejected launch-bound cases. They do not constitute a broad model-quality evaluation.

Both model controls use exact rank0 routing. Greedy request T0/seed42, two warmups plus five512-token measurements: 29.6/29.3tok/s, observed-1.01%, MAD1.69/1.02%, CPU7.4/8.1%. Author-default T1/top_p.95/top_k20, one warmup plus three512-token measurements: 27.9/28.5tok/s, observed+2.15%. Comparable identical text/draft work: greedy=False, author=False. Whole-model TPS gain established:False. Timing differences with different MTP acceptance or inside noise are not attributed to the kernel.

Local STRATA_ROUTE_TAIL_SKIP changed from rank1 to0 for model quality: compute all original selected experts. It was never a Boolean flag. The prior private39–40tok/s H2/expert-table measurements used rank1 and must not be presented as exact-routing measurements. The public first-install preset already used0 and is unchanged. No new routing bias, quantization, sampler, OS policy or model setting is introduced by these code patches.

# Atomic cache publication under allocation failure

Selected narrow transaction-order adaptation from [Strata#5530](https://github.com/Niko1221/Strata/pull/5530), head827d55ab826b73dc8ce5b13f29220f00bb014528, MIT. Reserve the serial before moving the saved image; undo that serial if image-vector growth throws. Advance identity only after both succeed. A noexcept-move assertion preserves the guarantee. Successful cache state and budget are unchanged. Optional Linux memory locking, allocator policy and resource limits are not imported.

On the actual Windows baseline header:64 offline failure-injection cases/15 allocation failures exposed5 inconsistent cache states. Fixed header:0 inconsistent states, caller image/bytes retained on failure and retry succeeds. The regression executable rebuilt against final source passed64/15/0. The live GPU server was not fault-injected. This is a reliability fix, not a measured generation-TPS speedup. The full48-file upstream PR remains only partially reviewed.

Final native `d8ee83c2`: CPU/ISA guards,130 actual-library Q8 direct/Graph cases (one expected shared-memory decline per mode),56 normal/strided expert pairs,27 package GPU cases including full F32, standard graceful startup and loaded/API verification passed. CPUvision is unchanged. Raw detached expert tests covered360 chunk and240 rejected launch-bound cases. They do not constitute a broad model-quality evaluation.

Both model controls use exact rank0 routing. Greedy request T0/seed42, two warmups plus five512-token measurements: 29.6/29.3tok/s, observed-1.01%, MAD1.69/1.02%, CPU7.4/8.1%. Author-default T1/top_p.95/top_k20, one warmup plus three512-token measurements: 27.9/28.5tok/s, observed+2.15%. Comparable identical text/draft work: greedy=False, author=False. Whole-model TPS gain established:False. Timing differences with different MTP acceptance or inside noise are not attributed to the kernel.

Local STRATA_ROUTE_TAIL_SKIP changed from rank1 to0 for model quality: compute all original selected experts. It was never a Boolean flag. The prior private39–40tok/s H2/expert-table measurements used rank1 and must not be presented as exact-routing measurements. The public first-install preset already used0 and is unchanged. No new routing bias, quantization, sampler, OS policy or model setting is introduced by these code patches.

Settings: context262144/reserve150MiB/14workers/PCIe1/Q2 MTP spec3/confidence.5/suffix3/lookup sizes4,12/q4_0 KVhost20480 cells per QSA layer/CPUvision/standard xhigh. Full required host weights, PLE and embeddings stay in RAM; no hidden HDD fallback. Fresh Windows normal installation/UAC/tasks/model download and full262144 throughput remain untested. Setup is unsigned. Broader semantic source review remains open.

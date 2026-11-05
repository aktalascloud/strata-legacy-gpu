# Exact IQ2_XXS CPU rows on AVX1

STRATA_DS4_IQ2_AVX1=1 enables the optional IQ2_XXS CPU row path for one through eight activations per expert. It shares the grid/sign decode, accumulates the same exact integer sums in two vectors, and retains the actual ggml AVX1 reference's eight F32 lanes, multiplication/addition and horizontal reduction order. The existing exact inline half expansion runs once per weight block. Other counts, quantization types and the Q2_K MTP math keep their original paths. The public default is off; opt-in requires an AVX1/no-AVX2 build and compatible older CPU. No FMA/F16C is introduced.

The CPU fixture links the actual production gg_cpu object and compares the new entry against ggml's active AVX1 IQ2_XXS trait. All 96 cases, 13,824 finite row outputs and 63,488 finite FP16 expansions matched bit for bit. Output canaries were intact. No GPU imports or computations were used by the fixture. Each of the sixteen measured (K2304/K5120, NT1..8) CPU-operation shapes had both new timings faster than both reference timings. These are CPU-operation timings, not a model-speed percentage.

An earlier production object retained repeated external half calls and regressed despite a successful inline prototype. That object was not deployed. Reusing the project's existing inline converter removes those calls. The final revision recompiles one CPU object; the identical model host object and all GPU objects are reused with their original evidence. No old test is relabelled as a fresh run.

## Local model readback

The exact reserve150/context262144/CPU12 profile kept 2041 GPU experts, the full CPU expert arena and Engram resident, Q2 MTP experts in RAM, confidence0.5 and CPU-only vision. Original weights, selected experts and author temperature1/top_p1/high75 are unchanged. The rank-v4 placement candidate is separate and disabled.

The two clean 128-token C20 decode samples were 12.73/14.15 tok/s (median 13.44). Contemporary C17 controls were 11.55/10.66 tok/s; an earlier C17 series had median13.46. Identical request settings and excluded warmups were used. Separate starts, cache history and shared-PC conditions limit causal claims. No universal maximum, full262K throughput or broad perplexity validation is claimed.

The engine-only update requires the unchanged runtime files from the [C17 native component](https://github.com/aktalascloud/strata-legacy-gpu/releases/tag/v0.1.56-deepseek1017-avx1-p40-4f11bf3a). See its manifest for exact prerequisite hashes. No weights, private config or MSVC DLLs are included. This is not a standalone portable installer.

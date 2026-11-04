# Experimental DeepSeek C10 source

This draft contains AVX1/Pascal source changes. The published classic C8 runtime remains a separate release. No qualified portable DeepSeek runtime, model weights or downloader is included here.

## Source changes

- Strict residency loading accepts the external CPU vision bridge. Genuine image-routing biases remain mandatory; no zero filling or ordinary text-bias alias is introduced.
- Optional profiler stage storage uses the bounded full stage table instead of its old six-element array.
- `strata_tune.spec=0|1` controls request compute while retaining loaded Q2 draft/head/tap memory. Spec0 does not free VRAM for more main-model experts.
- The existing AVX1 Q8_K activation quantizer is selected on AVX1-only CPUs. Its isolated K5120/K2304 measurements were 2.18x/2.09x; these are operator numbers, not a model speedup.
- `DS4_ENGRAM_DISK=1` explicitly permits the bounded Engram tier. Absent/off retains full Engram RAM. Other generation weights, embeddings and CPU vision retain strict residency/read-ban requirements.

Current public C8 main is merged with real ancestry, preserving its Windows inherited-log append fix. The four code files match reviewed C10 source after CRLF-to-LF conversion only. Native compilation provenance is retained.

## Actual bounded model results

DeepSeek-V4.1-Flash-1017 IQ2_XXS with Q2 DSpark now loaded successfully with full Engram RAM and reserve 512 MiB. Native reports 110,595,290,400 Engram bytes resident, all 14,050 CPU experts copied and CUDA-registered (120.8 GB), and 1,694 GPU experts (16.04 GB). Embeddings are resident; the external CPU projector locked 972,189,696 weight bytes. The redundant Engram row cache is off. Earlier arithmetic/two synthetic color-image checks and positive Q2 draft acceptance remain bounded functional evidence; the current full-RAM run also generated nonempty text with real accepted drafts.

An earlier partial/cache-mode thinking-off screen used one excluded warmup and two balanced 32-token spec0/spec1 pairs at T1/topP1. Every sample had API 32/native-produced 32 and zero overrun. Medians were 8.10 tok/s for spec0 and 7.53 tok/s for spec1 using API tokens/native decode elapsed. Both pairs favored spec0, but the ranges overlap and both arms improved later; shared-PC/cache/placement effects remain. This compares compute modes on the same build, not patch-versus-stock performance, and establishes no universal maximum or new default. The saved author setting remains high75. Earlier high75/cap32 samples reached a 16-token thinking budget; their original strict cap32 unrankable status is unchanged.

Full-RAM request-only confidence screens retained 0.5: 0.3 was slower; 0.7 had no stable gain. Although 0.9 led by 4.62% in two reversed 64-token pairs, a 128-token confirmation reversed it (-8.43%), so it was rejected. The selected 0.5 produced 11.41/12.56 tok/s (median11.98) at 128 output tokens with request effort=none/T1/topP1. These are bounded shared-PC comparisons, not a universal optimum, stock-versus-patch result or causal RAM speedup. The saved author high75 and sampler are unchanged.

Earlier full-RAM/150 MiB and partial/150 MiB attempts failed during CUDA host registration. Full-RAM/512 MiB now succeeds. Registration headroom is a plausible explanation, but the original exact error code/cause remains unrecorded; no driver-mode or OS change is prescribed. Native full-residency/read-ban guards are active. Current HTTP counters do not measure per-request per-file physical IO, so enforcement is not presented as measured physical zero.

## Qualification and remaining limits

The original 28 GPU processes/148 selected dense/expert reports remain actual passed evidence. References use selected CPU rows/columns; all generated GPU outputs receive finiteness/canary scans. These receipts were not rerun or relabelled as full-model validation. AVX1 quantizer/fallback and Engram host/cache paths have separate CPU evidence. CUDA payload comparison permits only reviewed literal anonymous-symbol-prefix differences, not arbitrary opcode normalization or a claim that compressed fatbins are raw-identical.

The chosen GGUF omitted forty main-layer learned VL routing biases. A separately prepared genuine F32[384] companion from the matching official 1017 checkpoint supplied 61,440 bytes for this local check. This source draft redistributes no such weights or private preparation proofs and supplies no qualified public downloader. CPU projector encoding alone does not prove LLM image-routing correctness.

Local source-specific schema3/S4U controller verification and graceful full-RAM restart succeeded. Portable startup/control export, actual cross-model desktop qualification, wider model/image/tool/MTP quality and long-generation performance remain pending. The private controller correction is not part of these four source files. No public default model/sampler/compute mode is changed here. Keep the PR in draft; original MIT and dependency licenses remain unchanged.

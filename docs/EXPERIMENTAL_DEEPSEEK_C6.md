# Experimental DeepSeek C12 source

This draft contains AVX1/Pascal source changes. The published classic C8 runtime remains a separate release. No qualified portable DeepSeek runtime, model weights or downloader is included here.

## Source changes

- Strict residency loading accepts the external CPU vision bridge. Genuine image-routing biases remain mandatory; no zero filling or ordinary text-bias alias is introduced.
- Optional profiler stage storage uses the bounded full stage table instead of its old six-element array.
- `strata_tune.spec=0|1` controls request compute while retaining loaded Q2 draft/head/tap memory. Spec0 does not free VRAM for more main-model experts.
- The existing AVX1 Q8_K activation quantizer is selected on AVX1-only CPUs. Its isolated K5120/K2304 measurements were 2.18x/2.09x; these are operator numbers, not a model speedup.
- `DS4_ENGRAM_DISK=1` explicitly permits the bounded Engram tier. Absent/off retains full Engram RAM. Other generation weights, embeddings and CPU vision retain strict residency/read-ban requirements.

Current public C8 main is merged with real ancestry, preserving its Windows inherited-log append fix. The native code files retain reviewed C10 bytes after CRLF-to-LF conversion. C12 adds only a Monitor RAM card and a bounded DS4 rounded-pool-size parser with one guarded post-READY call; all pre-existing serving/control AST remains unchanged. Native compilation provenance is retained.

## Actual bounded model results

DeepSeek-V4.1-Flash-1017 IQ2_XXS with Q2 DSpark now loaded successfully with full Engram RAM and reserve 512 MiB. Native reports 110,595,290,400 Engram bytes resident, all 14,050 CPU experts copied and CUDA-registered (120.8 GB), and 1,694 GPU experts (16.04 GB). Embeddings are resident; the external CPU projector locked 972,189,696 weight bytes. The redundant Engram row cache is off. Earlier arithmetic/two synthetic color-image checks and positive Q2 draft acceptance remain bounded functional evidence; the current full-RAM run also generated nonempty text with real accepted drafts.

An earlier partial/cache-mode thinking-off screen used one excluded warmup and two balanced 32-token spec0/spec1 pairs at T1/topP1. Every sample had API 32/native-produced 32 and zero overrun. Medians were 8.10 tok/s for spec0 and 7.53 tok/s for spec1 using API tokens/native decode elapsed. Both pairs favored spec0, but the ranges overlap and both arms improved later; shared-PC/cache/placement effects remain. This compares compute modes on the same build, not patch-versus-stock performance, and establishes no universal maximum or new default. The saved author setting remains high75. Earlier high75/cap32 samples reached a 16-token thinking budget; their original strict cap32 unrankable status is unchanged.

Full-RAM request-only confidence screens retained 0.5: 0.3 was slower; 0.7 had no stable gain. Although 0.9 led by 4.62% in two reversed 64-token pairs, a 128-token confirmation reversed it (-8.43%), so it was rejected. The selected 0.5 produced 11.41/12.56 tok/s (median 11.98) at 128 output tokens with request effort=none/T1/topP1. These are bounded shared-PC comparisons, not a universal optimum, stock-versus-patch result or causal RAM speedup. The saved author high75 and sampler are unchanged.

Earlier full-RAM/150 MiB and partial/150 MiB attempts failed during CUDA host registration. Full-RAM/512 MiB now succeeds. Registration headroom is a plausible explanation, but the original exact error code/cause remains unrecorded; no driver-mode or OS change is prescribed. Native full-residency/read-ban guards are active. Current HTTP counters do not measure per-request per-file physical IO, so enforcement is not presented as measured physical zero.

## Current context 262144 profile and UI

The local context 262144/prefill-chunk0 profile keeps 1,841 GPU experts (17.32 decimalGB /16.13 GiB) and all 13,903 remaining experts pinned in RAM (119.6 GB); full Engram, embeddings and CPU-only projector stay resident. The projector does not consume VRAM. Prefill-chunk0 trades slower long-prompt ingestion for more expert VRAM. A supported86,400-second READY limit avoids premature termination of a cold HDD load; independent startup observation never treats an elapsed deadline as proof that a live owner failed.

The Monitor now has a RAM percentage/used-total/history card. Older DS4 INFO omits expert pool bytes, so the backend reads only the current startup log and accepts a rounded size only when native expert counts match. The UI marks it with approximately rather than inventing exact bytes. Existing native MiB reports win; unknown/mismatched logs stay unknown. The whole serving module remains AST-identical after removing the pure parser and its sole guarded insertion, including admission/drain/shutdown.

Matched request-local none/T1/topP1 128-token screens retained Q2 GPU drafting/confidence0.5. CPU14 spec-on/off medians were11.22/10.38 tok/s; both pairs favored on. A separate CPU12 startup gave clean on samples12.20/11.86 (median 12.03); one off sample was excluded for other-process CPU load. CPU12 is the best observed profile, but differing background load and separate startups do not prove an isolated 7.26% causal gain or a universal maximum. Process CPU accounting separates other applications from System/driver work; raw cautious runs remain preserved. Author high75 and sampler are unchanged.

Optional CPU-resident MTP experts are a separate pending experiment. Full CPU draft attention/head support is not claimed here. There is no new native build or GPU numerical rerun for this C12 UI change.

## Qualification and remaining limits

The original 28 GPU processes/148 selected dense/expert reports remain actual passed evidence. References use selected CPU rows/columns; all generated GPU outputs receive finiteness/canary scans. These receipts were not rerun or relabelled as full-model validation. AVX1 quantizer/fallback and Engram host/cache paths have separate CPU evidence. CUDA payload comparison permits only reviewed literal anonymous-symbol-prefix differences, not arbitrary opcode normalization or a claim that compressed fatbins are raw-identical.

The chosen GGUF omitted forty main-layer learned VL routing biases. A separately prepared genuine F32[384] companion from the matching official 1017 checkpoint supplied 61,440 bytes for this local check. This source draft redistributes no such weights or private preparation proofs and supplies no qualified public downloader. CPU projector encoding alone does not prove LLM image-routing correctness.

Local source-specific schema3/S4U controller verification and graceful full-RAM restart succeeded. Portable startup/control export, actual cross-model desktop qualification, wider model/image/tool/MTP quality and long-generation performance remain pending. The private controller correction is not part of these source changes. No public default model/sampler/compute mode is changed here. Keep the PR in draft; original MIT and dependency licenses remain unchanged.

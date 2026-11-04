# Experimental DeepSeek C10 source

This draft contains source changes for AVX1/Pascal. The published classic C8 runtime remains a separately qualified release. No DeepSeek binary, model weights, private configuration or downloader is included here.

## Changes relative to current public main

- The strict-RAM loader accepts the external CPU vision bridge. Image-specific routing biases remain genuine learned weights; an incomplete pack is refused rather than filled with zeros or ordinary text-routing aliases.
- Optional profiler stage storage uses the full bounded stage table instead of writing past its old six-element array. This path stays opt-in.
- A request may use `strata_tune.spec=0|1` to compare DSpark compute. Spec0 retains the loaded draft/head/tap memory. It does not free VRAM for more main-model experts.
- The existing Q8_K activation quantizer is selected on AVX1-only CPUs, preserving the opt-out and the other CPU/format paths. Isolated quantization measured 2.18x at K5120 and 2.09x at K2304; neither number is an end-to-end generation-speed claim.
- `DS4_ENGRAM_DISK=1` explicitly permits the bounded Engram reader/cache tier. Absent/off retains full Engram RAM. Main/draft weights, embeddings and CPU vision remain subject to their strict residency policy; this adds no automatic general HDD fallback.

The C8 Windows inherited-log append fix is preserved through the real public-main merge. All four code files match the reviewed C10 source after CRLF-to-LF conversion only. Their native compilation provenance is retained rather than described as a new rebuild.

## Evidence and limits

The original 28 GPU processes produced 148 passing reports for the selected dense/expert matrix paths, including the real shapes/strides. CPU references cover selected rows/columns; all generated GPU outputs receive finiteness/canary scans. These are the original results, not repeated runs or full-model qualification. AVX1 quantizer/fallback and Engram host/cache paths have separate CPU evidence. Decoded CUDA payload comparison permits only the explicitly reviewed literal anonymous-symbol prefixes; raw compressed fatbins are not claimed byte-identical across those host compilations.

Full-model loading, actual complete residency/weight IO, real image handling, MTP acceptance and end-to-end generation speed remain pending. Foreign accelerator results do not qualify Pascal. No hardware-wide maximum or fresh whole-model speed gain is claimed.

A GGUF that omits the forty main-layer image-routing biases needs separately prepared genuine F32[384] vectors from the matching official DeepSeek-V4.1-Flash-1017 checkpoint for external CPU vision. They total 61,440 bytes. The native loader supports such a separately pinned model-data companion; this PR neither redistributes those weights nor supplies a qualified public downloader/launcher. A projector's CPU encoding test alone does not qualify the LLM image-routing path.

Original MIT and vendored dependency licenses are unchanged. Please keep this source draft unmerged until its remaining model/runtime evidence is reviewed.

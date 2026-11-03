# CPU vision dependency overlay

The helper uses llama.cpp/ggml under the included MIT license. The retained dependency
origin names `3cf03257f219afbe7334045ff7c6a06ac68c627d`; the local baseline was an extracted
source directory, so this is a declared origin, not a new Git HEAD verification.
The exact base/applied file hashes and the 353 actually compiled source/header inputs
in this directory define the checked dependency used by the helper.

`overlay-files/` contains the nine changed dependency files, including the new
DeepSeek-4.1 projector and the Windows CPU weights-only lock. The two corresponding
helper files are tracked at `tools/vision/gguf_meta.h` and `tools/vision/strata_vision.cpp`.
`overlay.patch` is the same dependency-only delta for code review; do not apply both
the raw-file tool and the patch to different baselines.

Before building, select a separate local dependency tree with the matching checked
baseline. Do not modify a tree used by an active build or model. From the Strata root:

```powershell
python tools/vision/apply_llama_overlay.py --llama-dir <local-llama-source> --check-only
python tools/vision/apply_llama_overlay.py --llama-dir <local-llama-source>
```

The tool rejects unknown changes before writing. It accepts already applied files
and can finish an interrupted application. It changes only the nine listed files;
it does not download a dependency or modify SDKs, credentials or system settings.
No source here is a weight file.

Build `strata-vision` with `LLAMA_DIR` pointing at that source, using the project's
fixed O3/Ivy AVX1 profile, CPU-only backends and at most 12 total build jobs. The
actual Windows recipe uses `STRATA_PORTABLE=OFF` and checks every effective compiler
command for Ivy AVX1 and disabled AVX2/FMA/F16C. The upstream CMake cache can retain
`GGML_NATIVE=ON` in this MSVC branch; the checked commands contain no `march=native`.
Do not call a different host's automatically chosen instructions an Ivy build.

`--require-weight-ram` explicitly locks the existing CPU weight buffer on Windows,
checks every page with `K32QueryWorkingSetEx`, and refuses a pageable fallback. It
uses only the helper's own working-set quota and restores it on cleanup when still
owned. It neither copies the weight buffer nor changes global OS policy. The flag
is off by default and cannot be combined with `--gpu`.

DeepSeek-4.1 uses its own row-major START/NEWLINE/END projector and CPU embedding
transport. Its checked CPU mode uses `--flash-attn off`. Existing Qwen profiles
retain their own automatic attention mode unless explicitly configured otherwise.
Compilation and a CPU image test do not qualify native DeepSeek GPU math, whole-model
RAM fit, model quality, MTP acceptance or generation speed.

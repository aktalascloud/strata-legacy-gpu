# Maintainer route

1. Read README.md, UPSTREAM.md, build-profile.json, source-provenance.json, CHANGES.md and BENCHMARKS.md. Use exact source/pins; do not invent flags.
2. Build from VS2022 x64 Developer PowerShell with Clang23.1.4/CUDA12.9/CMake/Ninja/Git: `powershell -File p40/build.ps1 -Jobs 12`. Dependencies are pinned; weights are unnecessary for compilation.
3. Never overwrite a loaded engine or a pinned check tree. Apply only after source review and the checks required by the actual delta. Reuse unchanged bytes explicitly; do not rename old checks.
4. Preserve user strata.json, supported native model modes and source-bound author capabilities. Model names/paths are data, not application switches.
5. Before a switch prove exact owner/source/config/nonce/time, graceful drain, captured-tree completion and a free port. No kill/cancel. After startup prove loaded/API/settings/owner. Unknown state blocks switching and rollback.
6. Keep current outputs and necessary build/dependency/license inputs. Do not publish weights/pack/MTP, keys, private configs/state, hosts, raw logs or caches.
7. Report actual validation and limits. Operator speed is not model throughput; experimental hardware/models remain experimental.

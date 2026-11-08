# Strata Legacy GPU

[English](README.md) · [Русский](README.ru.md) · [Windows ZIP](https://github.com/aktalascloud/strata-legacy-gpu/releases/latest)

A local OpenAI-compatible server for Windows/Ivy Bridge/P40. One user configuration, `strata.json`; model selection belongs to prepared data and a compatible backend.

**Engine 0.1.58**, official source `146df3c46873`, native `d8ee83c2`. [Full Windows Setup.exe and portable ZIP](https://github.com/aktalascloud/strata-legacy-gpu/releases/tag/v0.1.58-swift-p40-d8ee83c2-setup-r2) include Python, the P40 engine, CPU vision and WebUI. Swift IQ3_S with compatible Q2 MTP is prepared on first setup; weights, private settings and SDKs are not bundled. [Exact-warp changes, measurements and review scope](docs/PASCAL_FUSED_H2_20261108.md).

Current d8ee83c2 additions: exact singleton GU scheduling (operation throughput+4.45–11.13%) and atomic conversation-cache publication under allocation failure (5 inconsistent states before,0 after). Exact0 Swift: greedy29.6/29.3tok/s; author-default T1 27.9/28.5tok/s. Differences remain inside noise with different MTP work; no overall TPS gain is established. AVX1/P40 compatibility, RAM residency/CPUvision, API and reliability changes have [30 retained source/workflow entries](performance/patches/series/README.md); these are not30 speedups. Prior rank1 model measurements used approximate expert skipping and are historical.

1. Check SHA256SUMS and run Setup.exe in a fresh folder, or extract the ZIP and run `INSTALL.cmd`.
2. Select the Swift model folder. Missing pinned files download with resume; existing configuration/runtime state is never overwritten by Setup. Existing installations use their managed updater.
3. `START.cmd` starts serving; `CHECK.cmd` checks the installation; `STOP.cmd` drains it. `AUTOSTART.cmd` enables independent startup.

APIs: `/v1/models`, `/v1/chat/completions`, `/v1/responses`, `/v1/messages`. Configure the address and supported modes locally. Author Auto/Ultra modes require the specific qualified model identity.

Source build: VS2022 x64 Developer PowerShell, Clang23.1.4, CUDA12.9, CMake/Ninja/Git; run `powershell -File p40/build.ps1 -Jobs 12`. CPU vision build: `powershell -File p40/build-vision.ps1 -Jobs 12`, using the checked private-copy dependency overlay. Compiling new bytes does not qualify them.

[Historical measurements](p40/BENCHMARKS.md) identify older source/native versions. Earlier dense-operation receipts improve about 6–40%; their historical Swift37.8/37.6tok/s comparison is below noise, so an overall model TPS gain is not established. Setup extraction/hash/import checks passed; fresh Windows installation was not tested. The installer is unsigned.

[Changes](p40/CHANGES.md) · [Recipe](p40/build-profile.json) · [Validation](p40/INSTALLATION-VERIFICATION.md) · [Licenses](THIRD_PARTY_NOTICES.md) · [Upstream](https://github.com/Niko1221/Strata)

[Expert dispatch patch and measurements](docs/PASCAL_EXPERT_TABLE_20261107.md) · [Follow-up PR dispositions](docs/REVIEW_FOLLOWUP_20261107.md).

[Exact fused experts and graph memory](docs/PASCAL_FUSED_H2_20261108.md) · [Latest PR review](docs/REVIEW_FOLLOWUP_20261108.md).

[Latest exact-routing measurements and cache fix](docs/PASCAL_SINGLETON_CACHE_20261108.md) · [New scoped PR review](docs/REVIEW_SINGLETON_CACHE_20261108.md). Prior private rank1 measurements are historical approximation results; current local/public profiles use rank0.

[JSON completion fix and reused native qualification](docs/JSON_WATCHER_20261108.md). Native/model settings unchanged; no new speed claim.

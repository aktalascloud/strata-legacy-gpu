# Strata Legacy GPU

[English](README.md) · [Русский](README.ru.md) · [Windows ZIP](https://github.com/aktalascloud/strata-legacy-gpu/releases/latest)

A local OpenAI-compatible server for Windows/Ivy Bridge/P40. One user configuration, `strata.json`; model selection belongs to prepared data and a compatible backend.

**Engine 0.1.58**, official source `146df3c46873`, native `62b147b0`. [Full Windows Setup.exe and portable ZIP](https://github.com/aktalascloud/strata-legacy-gpu/releases/tag/v0.1.58-swift-p40-62b147b0-setup-r3) include Python, the P40 engine, CPU vision and WebUI. Swift IQ3_S with compatible Q2 MTP is prepared on first setup; weights, private settings and SDKs are not bundled. [Exact-warp changes, measurements and review scope](docs/PASCAL_EXACT_WARP_20261107.md).

1. Check SHA256SUMS and run Setup.exe in a fresh folder, or extract the ZIP and run `INSTALL.cmd`.
2. Select the Swift model folder. Missing pinned files download with resume; existing configuration/runtime state is never overwritten by Setup. Existing installations use their managed updater.
3. `START.cmd` starts serving; `CHECK.cmd` checks the installation; `STOP.cmd` drains it. `AUTOSTART.cmd` enables independent startup.

APIs: `/v1/models`, `/v1/chat/completions`, `/v1/responses`, `/v1/messages`. Configure the address and supported modes locally. Author Auto/Ultra modes require the specific qualified model identity.

Source build: VS2022 x64 Developer PowerShell, Clang23.1.4, CUDA12.9, CMake/Ninja/Git; run `powershell -File p40/build.ps1 -Jobs 12`. CPU vision build: `powershell -File p40/build-vision.ps1 -Jobs 12`, using the checked private-copy dependency overlay. Compiling new bytes does not qualify them.

[Historical measurements](p40/BENCHMARKS.md) identify older source/native versions. Current selected dense operations improve about 6–40%; same-native Swift 37.8 vs 37.6 tok/s is below noise, so an overall model TPS gain is not established. Setup extraction/hash/import checks passed; fresh Windows installation was not tested. The installer is unsigned.

[Changes](p40/CHANGES.md) · [Recipe](p40/build-profile.json) · [Validation](p40/INSTALLATION-VERIFICATION.md) · [Licenses](THIRD_PARTY_NOTICES.md) · [Upstream](https://github.com/Niko1221/Strata)

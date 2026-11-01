# Strata Legacy GPU

[English](README.md) · [Русский](README.ru.md) · [Windows ZIP](https://github.com/aktalascloud/strata-legacy-gpu/releases/latest)

A local OpenAI-compatible server for Windows/Ivy Bridge/P40. One user configuration, `strata.json`; model selection belongs to prepared data and a compatible backend.

**Engine 0.1.55**, source `c62d5e3a15b4` (`c62d5e3a15b40ea51c96aae9e8d36928965f53ab`). The AVX1/Pascal sm61 profile is qualified; other included backends retain separate experimental limits.

1. Extract the ZIP, check SHA256SUMS, run `INSTALL.cmd`.
2. Select a compatible backend/local model. No weights or personal settings are bundled.
3. `START.cmd` starts serving; `CHECK.cmd` checks the installation; `STOP.cmd` drains it. `AUTOSTART.cmd` enables independent startup.

APIs: `/v1/models`, `/v1/chat/completions`, `/v1/responses`, `/v1/messages`. Configure the address and supported modes locally. Author Auto/Ultra modes require the specific qualified model identity.

Source build: VS2022 x64 Developer PowerShell, Clang23.1.4, CUDA12.9, CMake/Ninja/Git; run `powershell -File p40/build.ps1 -Jobs 12`. Compiling new bytes does not qualify them.

[Latest measurements and scope](p40/BENCHMARKS.md). This build has no new whole-model benchmark.

[Changes](p40/CHANGES.md) · [Recipe](p40/build-profile.json) · [Validation](p40/INSTALLATION-VERIFICATION.md) · [Licenses](THIRD_PARTY_NOTICES.md) · [Upstream](https://github.com/Niko1221/Strata)

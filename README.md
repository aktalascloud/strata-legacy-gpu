# Strata Legacy GPU

[English](README.md) · [Русский](README.ru.md) · [Windows ZIP](https://github.com/aktalascloud/strata-legacy-gpu/releases/latest)

A local OpenAI-compatible server for Windows/Ivy Bridge/P40. One user configuration, `strata.json`; model selection belongs to prepared data and a compatible backend.

**Engine 0.1.56**, source `ffa80d73133e` (`ffa80d73133ea5c548aefe57889a16e8085a938f`). The AVX1/Pascal sm61 profile is qualified; this ZIP contains the classic native E4 engine and the separately qualified CPU vision helper. DeepSeek/MiniMax and other backend source retain explicit experimental limits; no unqualified native runtime is bundled.

1. Extract the ZIP, check SHA256SUMS, run `INSTALL.cmd`.
2. Install the prepared native model; optional generic backends are source-only in this ZIP. No weights or personal settings are bundled.
3. `START.cmd` starts serving; `CHECK.cmd` checks the installation; `STOP.cmd` drains it. `AUTOSTART.cmd` enables independent startup.

APIs: `/v1/models`, `/v1/chat/completions`, `/v1/responses`, `/v1/messages`. Configure the address and supported modes locally. Author Auto/Ultra modes require the specific qualified model identity.

Source build: VS2022 x64 Developer PowerShell, Clang23.1.4, CUDA12.9, CMake/Ninja/Git; run `powershell -File p40/build.ps1 -Jobs 12`. CPU vision build: `powershell -File p40/build-vision.ps1 -Jobs 12`, using the checked private-copy dependency overlay. Compiling new bytes does not qualify them.

[Historical measurements](p40/BENCHMARKS.md) identify a different source/native version; current-build throughput gain has not been measured.

[Changes](p40/CHANGES.md) · [Recipe](p40/build-profile.json) · [Validation](p40/INSTALLATION-VERIFICATION.md) · [Licenses](THIRD_PARTY_NOTICES.md) · [Upstream](https://github.com/Niko1221/Strata)

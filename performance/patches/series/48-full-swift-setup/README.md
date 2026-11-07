# Full Swift Windows installer

Selected installation workflow, based on public commit7b7f60cfd60ab55b0b02e37aa67f147bb4d83c3b. It packages the existing qualified0.1.58 native/Python/CPU-vision/WebUI kit as Setup.exe, uses the pinned Swift IQ3_S and compatible Q2 RT manifest, and sets the documented first-install profile. Existing configurations are retained; Setup requires a fresh folder.

The NSIS bootstrap uses64-bit PowerShell on Windows x64, preserves third-party notices and provides /VERIFYONLY. Its exact flag parser, real EXE extraction into a Unicode/spaced path, bundle/native version checks and isolated runtime imports passed. Configuration, active runtime and scheduled-task definitions stayed unchanged. No weights or SDK are bundled. No fresh-Windows install, real first-use weight download/preparation or administrator task registration was performed in this qualification.

Factory-only defaults do not replace existing user settings. Standard Swift xhigh is used; author Auto/Ultra is disabled. No generation-speed percentage is attributed to the installer. Native performance evidence remains the separate exact-warp report.

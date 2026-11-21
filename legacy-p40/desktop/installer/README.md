# Strata Desktop P40 Setup

The Windows x64 installer bundles Desktop, the Pascal CUDA build of the native engine, CPU Vision, Node.js, Python Control and Harness. It prepares the Swift pack from two existing IQ3_S GGUF shards. Model weights and the optional prepared Q2 MTP pack are supplied separately. The selected configuration starts locally on port 8093. Setup requires an NVIDIA driver, Microsoft Edge WebView2 Runtime and the official [Microsoft Visual C++ x64 runtime](https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist) 14.51.36247 or newer. Setup checks the Microsoft signatures and copies the Vision prerequisites from System32 during installation.

Setup r5 ships engine 0.1.63 and Desktop patches 01–08. The Swift profile uses PLE `mmap`, a 2048-token conversation-cache threshold and a 200 MiB VRAM reserve. [Patch archive](../../patches/)

Choose an empty installation directory. An existing startup entry stays in place, so disable older Strata startup entries before switching to this installation.

Use the release Desktop executable and its matching Host build. Stage the official Node, Control and Harness components with `assemble.ps1`. Pass absolute artifact and notice paths, their recorded hashes, and a fresh `-Stage` directory. Build that directory with `build-installer.ps1 -Stage <directory> -IntegritySha256 <hash> -Nsis <makensis.exe> -Output <Setup.exe> -PrivatePrefix <path-prefixes>`. Keep the distribution notices and MPL source archive together with the payload.

Run `Setup.exe /VERIFYONLY /D=<empty-directory>` to test extraction without an autostart entry or model. The process checks component hashes and runs engine, Control, Node and Harness version or help commands. A `-Qualification` build only supports this mode. Validate real startup and inference separately.

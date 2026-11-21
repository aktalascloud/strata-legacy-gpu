# Active patches

The engine [index](index.json) pins the qualified upstream `3142b66b`. The earlier Swift screen on `c7757280` covered 01, 57 and 58. Upstream carries route-prior protection and AVX1 IQ4_NL PLE support. The 2048-token cache minimum uses a supported engine argument.

[Desktop patches](desktop/) preserve the application features. Patch 05 overlaps CPU and GPU hardware probes on Windows. Median time to App Host HTTP 200 dropped from 5.68 s to 4.03 s across four paired starts.

Patch 06 lets a KoboldCpp LAN helper turn reasoning off when its model list omits reasoning metadata. An explicit model capability still takes precedence.

Patch 07 accepts the self-contained engine introduced in 0.1.62. The receipt still pins the exact engine and Vision files, and supports the MMQ DLL in builds that include it.

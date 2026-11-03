# Validation scope

Engine **0.1.56**, upstream `ffa80d73133e` (`ffa80d73133ea5c548aefe57889a16e8085a938f`).

The native profile has source-pinned CPU/ISA/owner checks and applicable GPU numerical/Graph checks, including the complete DenseF32 sweep. The classic E4 GPU mathematical bytes retain their exact original 27-case qualification, including DenseF32 5201; old GPU runs are not renamed. CPU vision99E1 is a separately built CPU-only component with actual locked-weight and encode checks. A synthetic CPU image was also answered by the live classic model after a graceful upgrade. DeepSeek native whole-model/GPU qualification is incomplete and its binary is not in this ZIP.

The package checks changed installer/control helpers, imports/versions, PowerShell/CMD, source/native fingerprints, licenses, privacy and ZIP contents. These are distinct from trained-model quality, full-context performance and validation on untested hardware.

Use INSTALL.cmd, CHECK.cmd, START.cmd and STOP.cmd. Keep one owner per port and drain accepted requests; do not force-kill a server or overwrite its loaded files.

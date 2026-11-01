# Validation scope

Engine **0.1.55**, upstream `c62d5e3a15b4` (`c62d5e3a15b40ea51c96aae9e8d36928965f53ab`).

The native profile has source-pinned CPU/ISA/owner checks and applicable GPU numerical/Graph checks, including the complete DenseF32 sweep. Serving-only changes retain an explicit identical-native reuse proof; old GPU runs are never renamed to a new run. CPU vision is reused only with exact input/binary evidence.

The package checks changed installer/control helpers, imports/versions, PowerShell/CMD, source/native fingerprints, licenses, privacy and ZIP contents. These are distinct from trained-model quality, full-context performance and validation on untested hardware.

Use INSTALL.cmd, CHECK.cmd, START.cmd and STOP.cmd. Keep one owner per port and drain accepted requests; do not force-kill a server or overwrite its loaded files.
